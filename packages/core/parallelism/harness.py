"""Registered managed handlers and conservative bounded headless transport.

Neither command allowlisting nor process groups constitute a security sandbox.
Unsupervised headless integrations remain instruction-based and cannot delegate.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import selectors
import re
import signal
import subprocess
import threading
import time

PROTOCOL = 'palarran.managed.v1'


def _receipt(value):
    if type(value) is not dict or value.get('status') not in ('submitted', 'failed', 'cancelled', 'unknown'):
        raise ValueError('Invalid managed result')
    for key in ('tokens', 'cost_micros'):
        if type(value.get(key)) is not int or value[key] < 0:
            raise ValueError('Invalid managed usage')
    if type(value.get('usage_known')) is not bool or type(value.get('stopped')) is not bool:
        raise ValueError('Managed result needs explicit usage and stop evidence')
    if not isinstance(value.get('subject'), str) or len(value['subject']) > 256:
        raise ValueError('Invalid managed subject')
    if value['status'] == 'cancelled' and not value['stopped']:
        raise ValueError('Cancellation needs actual stop evidence')
    return {key: value[key] for key in ('status', 'subject', 'tokens', 'cost_micros', 'usage_known', 'stopped')}


def unknown(*, stopped=False):
    return dict(status='unknown', subject='', tokens=0, cost_micros=0, usage_known=False, stopped=stopped)


class ManagedHarness:
    """Trusted callback boundary; registrations must control their descendants.

    Reviewers attest to each callback's scope. This does not sandbox Python code.
    All children must use the same Dispatcher.add_tasks, never native delegation.
    """
    protocol = PROTOCOL
    integration = 'enforced'
    nested_delegation = False

    def __init__(self, handlers, *, controlled_descendants=False, protocol=PROTOCOL):
        if protocol != PROTOCOL or controlled_descendants is not True or not handlers:
            raise ValueError('Managed callbacks require reviewed controlled descendants')
        if any(not isinstance(key, str) or not callable(value) for key, value in handlers.items()):
            raise ValueError('Invalid managed handler registry')
        self.handlers = dict(handlers)

    def execute(self, task, *, heartbeat, cancel):
        handler = self.handlers.get(task['task_id'])
        if handler is None:
            raise ValueError('Task has no registered managed handler')
        if cancel.is_set():
            return dict(status='cancelled', subject='', tokens=0, cost_micros=0, usage_known=True, stopped=True)
        return _receipt(handler(task, heartbeat=heartbeat, cancel=cancel))


class HeadlessHarness:
    """Exact registered argv, bounded pipes and observed receipt; no shell/models by default."""
    protocol = PROTOCOL
    integration = 'instruction-based'
    nested_delegation = False

    def __init__(self, commands, *, max_output=65536, environment=None):
        if type(max_output) is not int or not 1024 <= max_output <= 1024 * 1024:
            raise ValueError('Invalid headless output bound')
        self.commands = {}
        for key, command in commands.items():
            if (not isinstance(key, str) or not isinstance(command, (tuple, list)) or not command
                    or any(type(arg) is not str or '\x00' in arg for arg in command)
                    or not Path(command[0]).is_absolute() or not Path(command[0]).is_file()):
                raise ValueError('Headless commands require a reviewed absolute exact argv')
            self.commands[key] = tuple(command)
        self.max_output = max_output
        environment = environment or {}
        if any(key not in ('PATH', 'LANG', 'LC_ALL', 'TZ') for key in environment):
            raise ValueError('Headless env must not contain inherited credentials')
        self.environment = dict(environment)
        self._processes = {}
        self._lock = threading.Lock()

    def cancel(self, session_id):
        with self._lock:
            process = self._processes.get(session_id)
        if process is None:
            return {'stopped': False, 'status': 'unknown'}
        return {'stopped': self._stop(process), 'status': 'cancel_requested'}

    @staticmethod
    def _group_absent(group_id):
        try:
            result = subprocess.run(['/bin/ps','-axo','pgid='],stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,timeout=2,check=True,text=True,env={'PATH':'/usr/bin:/bin'})
            rows = result.stdout.splitlines()
            return (bool(rows) and len(result.stdout)<=1048576
                    and all(row.strip().isdigit() for row in rows)
                    and group_id not in {int(row.strip()) for row in rows})
        except (OSError,ValueError,subprocess.SubprocessError):
            return False

    @staticmethod
    def _stop(process):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            if process.poll() is None:
                return False
        try:
            process.wait(timeout=2)
            return HeadlessHarness._group_absent(process.pid)
        except subprocess.TimeoutExpired:
            return False

    def execute(self, task, *, heartbeat, cancel):
        command = self.commands.get(task['task_id'])
        if command is None:
            raise ValueError('Task argv is not registered')
        seconds = task.get('limits', {}).get('seconds')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 86400:
            raise ValueError('Task needs a finite headless timeout')
        packet = json.dumps({'protocol': PROTOCOL, 'task': task, 'nested_delegation': False}, separators=(',', ':')).encode()+b'\n'
        if len(packet) > 65536:
            raise ValueError('Headless input exceeds bound')
        session = task.get('session_id')
        if not isinstance(session,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',session):
            raise ValueError('Headless launch requires an explicit registered session identity')
        with self._lock:
            if session in self._processes:
                raise ValueError('Session already launched; reconcile before retry')
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, cwd=task['worktree'], env=self.environment,
                start_new_session=True, shell=False)
            self._processes[session] = process
        selector = selectors.DefaultSelector()
        observed = {'tokens': 0, 'cost_micros': 0}
        final = None
        def uncertain(stopped=False):
            return dict(unknown(stopped=stopped), **observed)
        def frame(raw):
            nonlocal final
            value = json.loads(raw)
            if value.get('protocol') != PROTOCOL:
                raise ValueError('Invalid headless protocol')
            if value.get('type') == 'usage':
                if final is not None:
                    raise ValueError('Usage after final result')
                for key in observed:
                    if type(value.get(key)) is not int or value[key] < observed[key]:
                        raise ValueError('Usage cannot decrease')
                    observed[key] = value[key]
                if heartbeat(**observed) is False:
                    cancel.set()
            else:
                if final is not None:
                    raise ValueError('Duplicate headless final result')
                final = _receipt(value)
                if any(final[key] < observed[key] for key in observed):
                    raise ValueError('Final usage cannot decrease')
                observed.update({key:final[key] for key in observed})
        total_output = 0
        output = bytearray(); pending = memoryview(packet); start = time.monotonic()
        os.set_blocking(process.stdin.fileno(), False)
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdin, selectors.EVENT_WRITE)
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while selector.get_map():
                if cancel.is_set() or time.monotonic()-start >= seconds:
                    return uncertain(stopped=self._stop(process))
                for key, _ in selector.select(timeout=0.05):
                    if key.fileobj is process.stdin:
                        try:
                            count = os.write(key.fd, pending); pending = pending[count:]
                        except BrokenPipeError:
                            pending = pending[len(pending):]
                        if not pending:
                            selector.unregister(key.fileobj); key.fileobj.close()
                    else:
                        chunk = os.read(key.fd, 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                        else:
                            total_output += len(chunk)
                            output.extend(chunk)
                            if total_output > self.max_output:
                                return uncertain(stopped=self._stop(process))
                            while b'\n' in output:
                                line, _, rest = output.partition(b'\n'); output = bytearray(rest)
                                frame(line)
                # Keep usage unknown until actual provider/callback evidence arrives.
                if heartbeat() is False:
                    cancel.set()
            process.wait(timeout=max(0.01, seconds-(time.monotonic()-start)))
            if process.returncode != 0:
                return uncertain(stopped=self._stop(process))
            try:
                if output.strip():
                    frame(output)
                if not self._group_absent(process.pid):
                    return uncertain(stopped=self._stop(process))
                if final is not None:
                    final['stopped'] = True
                return final if final is not None else uncertain(stopped=True)
            except (ValueError, TypeError, AttributeError):
                return uncertain(stopped=self._stop(process))
        except (ValueError, TypeError, AttributeError, subprocess.TimeoutExpired):
            return uncertain(stopped=self._stop(process))
        except BaseException:
            self._stop(process)
            raise
        finally:
            selector.close()
            for pipe in (process.stdin, process.stdout):
                if pipe is not None and not pipe.closed:
                    pipe.close()
            # Keep terminal process identity for reconciliation; no implicit replay.
