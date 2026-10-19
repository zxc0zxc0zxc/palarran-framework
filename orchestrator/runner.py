"""Bounded POSIX subprocess transport for trusted workflows, not a sandbox."""

import hashlib
import json
import math
import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from .diagnostics import Diagnostics


@dataclass(frozen=True)
class Result:
    returncode: int
    reason: str
    output_sha256: str
    output_bytes: int
    seconds: float
    usage_complete: Optional[bool] = None
    diagnostics: Optional[dict] = None


def invocation(task, workspace, *, profile=None, telemetry=False, max_cost_usd=None):
    """Build a noninteractive argv; prompts travel over stdin, never argv."""
    adapter = task.get("adapter", "command")
    if adapter == "command":
        return list(task["argv"]), ""
    if adapter == "codex":
        argv = [task["executable"], "exec", "--ephemeral", "--sandbox",
                "workspace-write", "-c", 'approval_policy="never"', "-C",
                str(workspace), "-"]
        if profile is not None:
            argv.extend(["--model", profile["model"], "-c",
                         "model_reasoning_effort=" + json.dumps(profile["effort"])])
        if telemetry:
            argv.append("--json")
    elif adapter == "claude":
        argv = [task["executable"], "--print", "--permission-mode", "dontAsk",
                "--allowedTools", "Read,Edit,Write,Bash", "--output-format",
                "stream-json" if telemetry else "json", "--no-session-persistence"]
        if profile is not None:
            argv.extend(["--model", profile["model"], "--effort", profile["effort"]])
        if telemetry:
            argv.append("--verbose")
            if max_cost_usd is not None:
                argv.extend(["--max-budget-usd", str(max_cost_usd)])
    else:
        raise ValueError("unsupported adapter")
    return argv, task["prompt"]


def _kill_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def execute(argv, cwd, *, timeout, output_limit, env, heartbeat, stdin_text="",
            usage_adapter=None, on_usage=None):
    """Drain output to a digest only; fence loss/limits kill the process group.

    Up to output_limit + 1 bytes are read: the extra byte proves overflow.
    Digests cover observed bytes in selector arrival order across both streams.
    Detached descendants that deliberately escape the session need an external
    sandbox/supervisor. The supplied environment is passed without inheritance.
    """
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if isinstance(output_limit, bool) or not isinstance(output_limit, int) or output_limit < 1:
        raise ValueError("output_limit must be a positive integer")
    started = time.monotonic()
    digest = hashlib.sha256()
    output_bytes = 0
    reason = "exited"
    usage_complete = None if usage_adapter is None else False
    usage_stream = None
    diagnostics = Diagnostics() if usage_adapter is not None else None
    if usage_adapter is not None:
        try:
            # Legacy executions neither import nor instantiate telemetry code.
            from .usage import UsageStream
            usage_stream = UsageStream(usage_adapter)
        except Exception:
            return Result(127, "usage_error", digest.hexdigest(), 0,
                          time.monotonic() - started, False)

    def publish(snapshots):
        for snapshot in snapshots:
            if on_usage is not None and not on_usage(snapshot):
                return False
        return True

    try:
        process = subprocess.Popen(
            list(argv), cwd=cwd, env=dict(env), shell=False,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True, bufsize=0,
        )
    except (OSError, ValueError):
        return Result(127, "spawn_error", digest.hexdigest(), 0,
                      time.monotonic() - started, usage_complete,
                      diagnostics.finish() if diagnostics is not None else None)
    selector = selectors.DefaultSelector()
    pending_input = memoryview(stdin_text.encode("utf-8"))
    for stream in (process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
    if pending_input:
        os.set_blocking(process.stdin.fileno(), False)
        selector.register(process.stdin, selectors.EVENT_WRITE)
    else:
        process.stdin.close()
    next_heartbeat = started
    root_exited = False
    try:
        while True:
            now = time.monotonic()
            if now >= next_heartbeat:
                # A broken heartbeat cannot leave an unfenced process running.
                try:
                    alive = heartbeat()
                except Exception:
                    alive = False
                if not alive:
                    reason = "lease_lost"
                    break
                next_heartbeat = time.monotonic() + 0.1
            if process.poll() is not None and not root_exited:
                root_exited = True
                # Descendants may keep inherited stdout open after root exits.
                # Kill the entire remaining group before draining final bytes.
                _kill_group(process)
                if not process.stdin.closed:
                    try:
                        selector.unregister(process.stdin)
                    except KeyError:
                        pass
                    process.stdin.close()
            if not selector.get_map() and root_exited:
                break
            if now - started >= timeout:
                reason = "timeout"
                break
            for key, mask in selector.select(min(0.05, max(0, timeout - (now - started)))):
                stream = key.fileobj
                if mask & selectors.EVENT_WRITE:
                    try:
                        count = os.write(stream.fileno(), pending_input[:65536])
                        pending_input = pending_input[count:]
                    except BrokenPipeError:
                        pending_input = memoryview(b"")
                    except BlockingIOError:
                        continue
                    if not pending_input:
                        selector.unregister(stream)
                        stream.close()
                    continue
                try:
                    chunk = os.read(stream.fileno(), min(65536, output_limit - output_bytes + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if diagnostics is not None:
                    diagnostics.feed("stdout" if stream is process.stdout else "stderr", chunk)
                output_bytes += len(chunk)
                digest.update(chunk)
                if output_bytes > output_limit:
                    reason = "output_limit"
                    break
                if usage_stream is not None and stream is process.stdout:
                    try:
                        # Publish every completed line before parsing the next:
                        # a later malformed line in the same OS read must not
                        # erase an earlier valid receipt from this attempt.
                        segments = chunk.split(b"\n")
                        for index, segment in enumerate(segments):
                            if index < len(segments) - 1:
                                segment += b"\n"
                            if segment and not publish(usage_stream.feed(segment)):
                                reason = "usage_stop"
                                break
                        if reason != "exited":
                            break
                    except Exception:
                        diagnostics.usage_failure(getattr(usage_stream, "failure_code", None))
                        reason = "usage_error"
                        break
            if reason != "exited":
                break
        if reason == "exited" and usage_stream is not None:
            try:
                if publish(usage_stream.finish()):
                    usage_complete = True
                else:
                    reason = "usage_stop"
            except Exception:
                diagnostics.usage_failure(getattr(usage_stream, "failure_code", None))
                reason = "usage_error"
    finally:
        _kill_group(process)
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        process.wait()
    return Result(process.returncode, reason, digest.hexdigest(), output_bytes,
                  time.monotonic() - started, usage_complete,
                  diagnostics.finish() if diagnostics is not None else None)
