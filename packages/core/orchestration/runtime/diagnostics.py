"""Bounded enum-only CLI observations. Never retain provider messages or identifiers."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import json
import re

RULES = (
    ('authentication_failed', r'\b401\b|unauthorized|invalid api key|authentication failed|not logged in|token.*expired'),
    ('rate_limited', r'\b429\b|rate.limit|usage limit|quota exceeded'),
    ('model_unavailable', r'model.{0,150}(not supported|not found|does not exist|unavailable|not available)|unsupported model'),
    ('configuration_invalid', r'error (parsing|loading) config|invalid configuration|unrecognized (argument|option)|unexpected argument'),
    ('sandbox_denied', r'sandbox.{0,100}(denied|not permitted|failed)|sandbox-exec'),
    ('connection_failed', r'error sending request|failed to connect|connection refused|network is unreachable|stream disconnected|dns error|tls.{0,50}(error|failed)|certificate verify'),
)
TERMINALS = {'turn.failed', 'error', 'turn.completed', 'result'}


class Diagnostics:
    """At most two 16KiB buffers and fixed codes; oversized lines are dropped."""
    def __init__(self):
        self.buffers = {'stdout': b'', 'stderr': b''}
        self.dropping = {'stdout': False, 'stderr': False}
        self.codes = set()
        self.events = 0
        self.started = False
        self.terminal = 'none'
        self.steps = []
        self.steps_dropped = 0

    def _classify(self, message):
        if not isinstance(message, str):
            return
        # Pattern matching never exports the matched source text.
        for code, pattern in RULES:
            if re.search(pattern, message[:16384], re.IGNORECASE):
                self.codes.add(code)

    def _line(self, source, raw):
        if source == 'stderr':
            self._classify(raw.decode('utf-8', errors='replace'))
            return
        try:
            record = json.loads(raw)
        except (ValueError, UnicodeError, RecursionError):
            return
        if not isinstance(record, dict):
            return
        self.events = min(10000, self.events + 1)
        kind = record.get('type')
        item = record.get('item')
        category = item.get('type') if isinstance(item, dict) else None
        allowed = {'command_execution', 'web_search', 'mcp_tool_call', 'file_change', 'agent_message', 'todo_list'}
        if kind in ('turn.started', 'turn.completed', 'turn.failed', 'error', 'result') or (kind in ('item.started', 'item.completed') and isinstance(category, str) and category in allowed):
            step = {'event': kind}
            if isinstance(category, str) and category in allowed:
                step['kind'] = category
                exit_code = item.get('exit_code')
                if type(exit_code) is int and -255 <= exit_code <= 255:
                    step['exit_code'] = exit_code
            if len(self.steps) < 32:
                self.steps.append(step)
            else:
                self.steps_dropped += 1
        if kind == 'turn.started':
            self.started = True
        if isinstance(kind, str) and kind in TERMINALS:
            self.terminal = kind
        if kind in ('error', 'turn.failed'):
            self.codes.add('provider_error')
            code = record.get('code')
            if isinstance(code, str) and code in {'bridge_line_limit','bridge_output_limit','bridge_thread_mismatch','bridge_turn_mismatch','bridge_incomplete_turn','bridge_duplicate_key','bridge_protocol_error'}:
                self.codes.add(code)
            self._classify(record.get('message'))
            error = record.get('error')
            if isinstance(error, dict):
                self._classify(error.get('message'))
            elif isinstance(error, str):
                self._classify(error)

    def feed(self, source, chunk):
        parts = chunk.split(b'\n')
        for index, part in enumerate(parts):
            ended = index < len(parts) - 1
            if not self.dropping[source]:
                if len(self.buffers[source]) + len(part) > 16384:
                    self.buffers[source] = b''
                    self.dropping[source] = True
                    self.codes.add('diagnostic_line_dropped')
                else:
                    self.buffers[source] += part
            if ended:
                if not self.dropping[source]:
                    self._line(source, self.buffers[source])
                self.buffers[source] = b''
                self.dropping[source] = False

    def usage_failure(self, code):
        allowed = {'usage_line_invalid', 'usage_json_invalid', 'usage_event_invalid',
                   'usage_invariant', 'usage_provider_error', 'usage_line_limit',
                   'usage_incomplete', 'usage_duplicate_key', 'usage_integer_limit',
                   'usage_nonfinite_value'}
        self.codes.add(code if isinstance(code, str) and code in allowed else 'usage_invalid')

    def finish(self):
        for source in self.buffers:
            if self.buffers[source] and not self.dropping[source]:
                self._line(source, self.buffers[source])
            self.buffers[source] = b''
        return {'codes': sorted(self.codes), 'event_count': self.events,
                'turn_started': self.started, 'terminal_event': self.terminal,
                'steps': self.steps, 'steps_dropped': self.steps_dropped}
