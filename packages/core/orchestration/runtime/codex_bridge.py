"""One ephemeral App Server turn, emitting only cumulative counters and safe events."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
import json
import os
import selectors
import subprocess
import sys
from pathlib import Path

MAX_LINE = 1048576


class Object(dict):
    def __init__(self, pairs):
        super().__init__(pairs)
        self.duplicate = len(pairs) != len(self)


def strict(value):
    if isinstance(value, Object):
        if value.duplicate:
            raise ValueError('Duplicate RPC accounting key')
        for item in value.values(): strict(item)
    elif isinstance(value, list):
        for item in value: strict(item)


def integer(value):
    if len(value) > 64: raise ValueError('Integer bound')
    return int(value)


def constant(value):
    raise ValueError('Nonfinite value')


def emit(value):
    print(json.dumps(value, separators=(',', ':')), flush=True)


def run(executable, cwd, model, effort, prompt, stream_limit=1048576, answer_file=None):
    # Inherit the supervisor's process group so cancellation kills the server too.
    process = subprocess.Popen([executable, 'app-server', '--listen', 'stdio://'],
                               cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, bufsize=0)
    selector = selectors.DefaultSelector()
    for stream in (process.stdout, process.stderr):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
    buffer = bytearray()
    thread = turn = None
    latest = None
    started = False
    completed = False
    public_answer = None
    events = raw_bytes = 0

    def send(method, params, ident=None):
        value = dict(method=method, params=params)
        if ident is not None:
            value['id'] = ident
        data = memoryview((json.dumps(value) + '\n').encode())
        while data:
            count = os.write(process.stdin.fileno(), data)
            data = data[count:]

    send('initialize', dict(clientInfo=dict(name='ai_tools_factory', title='AI Tools Factory', version='0.2.0'),
        capabilities=dict(optOutNotificationMethods=['item/commandExecution/outputDelta','item/reasoning/textDelta','item/reasoning/summaryTextDelta','item/agentMessage/delta'])), 1)
    try:
        while not completed:
            if process.poll() is not None and not selector.get_map():
                raise ValueError('Server closed')
            for key, _ in selector.select(.1):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                raw_bytes += len(chunk)
                if raw_bytes > stream_limit:
                    raise ValueError('Server output bound')
                if key.fileobj is process.stderr:
                    # Parent hashes/classifies transient stderr, never persists it.
                    os.write(sys.stderr.fileno(), chunk)
                    continue
                parts = chunk.split(b'\n')
                for part_index, part in enumerate(parts):
                    if len(buffer) + len(part) > MAX_LINE:
                        raise ValueError('Server line bound')
                    buffer.extend(part)
                    if part_index == len(parts) - 1:
                        continue
                    raw = bytes(buffer); buffer.clear()
                    events += 1
                    if events > 10000:
                        raise ValueError('Server event bound')
                    message = json.loads(raw, object_pairs_hook=Object, parse_int=integer, parse_constant=constant)
                    if not isinstance(message, Object) or message.duplicate:
                        raise ValueError('Server envelope')
                    if message.get('method') not in ('item/started', 'item/completed'):
                        strict(message)
                    if 'id' in message and 'method' in message:
                        # Never invent approval/user-input consent.
                        emit(dict(type='error', message='Server request requires explicit authorization'))
                        return 2
                    if 'error' in message:
                        emit(dict(type='error', message='App server protocol error'))
                        return 2
                    if 'id' in message:
                        response = message.get('result')
                        if not isinstance(response, dict):
                            raise ValueError('Server response')
                        if message['id'] == 1:
                            send('initialized', {})
                            send('thread/start', dict(model=model, cwd=cwd, ephemeral=True,
                                approvalPolicy='never', sandbox='read-only' if answer_file else 'workspace-write',
                                config={'model_reasoning_effort': effort, 'tool_output_token_limit': 100000}), 2)
                        elif message['id'] == 2:
                            thread = response['thread']['id']
                            if not isinstance(thread, str) or not thread:
                                raise ValueError('Thread identity')
                            emit(dict(type='turn.started')); started = True
                            send('turn/start', dict(threadId=thread, effort=effort,
                                input=[dict(type='text', text=prompt)], summary='none'), 3)
                        elif message['id'] == 3:
                            incoming_turn = response['turn']['id']
                            if turn is not None and turn != incoming_turn:
                                raise ValueError('Turn response mismatch')
                            turn = incoming_turn
                            if not isinstance(turn, str) or not turn:
                                raise ValueError('Turn identity')
                        continue
                    method = message.get('method')
                    params = message.get('params', {})
                    if method == 'turn/started':
                        if params.get('threadId') != thread:
                            raise ValueError('Turn thread mismatch')
                        incoming_turn = params['turn']['id']
                        if not isinstance(incoming_turn, str) or (turn is not None and turn != incoming_turn):
                            raise ValueError('Turn start mismatch')
                        turn = incoming_turn
                    if method in ('thread/tokenUsage/updated', 'turn/completed'):
                        if not started or not isinstance(params, dict) or params.get('threadId') != thread:
                            raise ValueError('Usage thread mismatch')
                        if method == 'thread/tokenUsage/updated':
                            if not turn or params.get('turnId') != turn:
                                raise ValueError('Usage turn mismatch')
                            total = params['tokenUsage']['total']
                            if not isinstance(total, dict):
                                raise ValueError('Usage shape')
                            # Preserve absent write breakdown as unknown, never zero.
                            receipt = dict(input_tokens=total['inputTokens'], cached_input_tokens=total['cachedInputTokens'],
                                cache_creation_input_tokens=total.get('cacheWriteInputTokens'), output_tokens=total['outputTokens'],
                                reasoning_output_tokens=total['reasoningOutputTokens'], total_tokens=total['totalTokens'])
                            if receipt != latest:
                                emit(dict(type='usage.updated', usage=receipt)); latest = receipt
                        else:
                            result = params['turn']
                            if not turn or result.get('id') != turn or result.get('status') != 'completed' or latest is None:
                                raise ValueError('Incomplete turn')
                            if answer_file is not None:
                                if public_answer is None or len(public_answer.encode()) > 4096:
                                    raise ValueError('Invalid benchmark answer')
                                answer = json.loads(public_answer, object_pairs_hook=Object, parse_constant=constant)
                                strict(answer)
                                if not isinstance(answer, dict):
                                    raise ValueError('Benchmark JSON object required')
                                fd = os.open(answer_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                                with os.fdopen(fd, 'w') as output:
                                    output.write(json.dumps(answer, ensure_ascii=False) + '\n')
                            emit(dict(type='turn.completed')); completed = True
                            break
                    elif method == 'error':
                        emit(dict(type='error', message='App server turn error'))
                        return 2
                    elif method in ('item/started', 'item/completed'):
                        item = params.get('item', {})
                        categories = {'commandExecution':'command_execution','webSearch':'web_search',
                                      'fileChange':'file_change','agentMessage':'agent_message','mcpToolCall':'mcp_tool_call'}
                        kind = categories.get(item.get('type')) if isinstance(item, dict) else None
                        if answer_file is not None:
                            if kind in ('command_execution', 'web_search', 'file_change', 'mcp_tool_call'):
                                raise ValueError('Benchmark tool call forbidden')
                            if item.get('type') == 'agentMessage' and method == 'item/completed' and item.get('phase') in (None, 'final_answer'):
                                strict(item)
                                message_text = item.get('text')
                                if not isinstance(message_text, str) or len(message_text.encode()) > 4096:
                                    raise ValueError('Benchmark answer bound')
                                public_answer = message_text
                        if kind:
                            safe = {'type':kind}
                            code = item.get('exitCode')
                            if type(code) is int and -255 <= code <= 255:
                                safe['exit_code'] = code
                            emit(dict(type='item.started' if method == 'item/started' else 'item.completed', item=safe))
        return 0
    finally:
        selector.close()
        # No shutdown request or extra model turn. Parent additionally kills group.
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('executable', 'cwd', 'model', 'effort'):
        parser.add_argument('--' + key, required=True)
    parser.add_argument('--answer-file', help='Private JSON-only read-only/no-tools measurement result, never reasoning')
    parser.add_argument('--stream-limit', type=int, default=1048576)
    args = parser.parse_args()
    prompt = sys.stdin.buffer.read(1048577)
    if not 1024 <= args.stream_limit <= 10485760 or len(prompt) > 1048576 or not os.path.isabs(args.executable) or not Path(args.cwd).is_absolute():
        return 2
    if args.answer_file is not None and not Path(args.answer_file).is_absolute():
        return 2
    try:
        return run(args.executable, args.cwd, args.model, args.effort, prompt.decode('utf-8'), args.stream_limit, args.answer_file)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        codes = {'Server line bound':'bridge_line_limit', 'Server output bound':'bridge_output_limit',
                 'Usage thread mismatch':'bridge_thread_mismatch', 'Usage turn mismatch':'bridge_turn_mismatch',
                 'Incomplete turn':'bridge_incomplete_turn', 'Duplicate RPC accounting key':'bridge_duplicate_key'}
        emit(dict(type='error', message='App server bridge protocol failure',
                  code=codes.get(str(error), 'bridge_protocol_error')))
        return 2


if __name__ == '__main__':
    sys.exit(main())
