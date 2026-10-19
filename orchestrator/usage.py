"""Bounded, stdout-only provider usage extraction without retaining model payloads."""
from decimal import Decimal, DecimalException, ROUND_CEILING, localcontext
import json

MAX_LINE_BYTES = 1048576
MAX_LINES = 10000
MAX_TOKENS = 10 ** 12
MAX_COST_NANO = 10 ** 15
_ERROR = 'Invalid or incomplete provider usage stream'


def _require(condition):
    if not condition:
        raise ValueError(_ERROR)


def _counter(value):
    _require(type(value) is int and 0 <= value <= MAX_TOKENS)
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _integer(value):
    # Bound conversion work even for ignored provider fields and older Python.
    _require(len(value) <= 64)
    return int(value)


def _constant(value):
    raise ValueError(_ERROR)


def _nano(value):
    _require(type(value) is int or isinstance(value, Decimal))
    number = Decimal(value)
    _require(number.is_finite() and 0 <= number <= Decimal(1000000))
    if 0 < number < Decimal('0.000000001'):
        return 1
    with localcontext() as context:
        context.prec = max(32, len(number.as_tuple().digits) + 16)
        result = int((number * Decimal(10 ** 9)).to_integral_value(rounding=ROUND_CEILING))
    _require(0 <= result <= MAX_COST_NANO)
    return result


class UsageStream:
    """Consume JSONL chunks and emit only allowlisted cumulative usage counters."""

    def __init__(self, adapter):
        _require(adapter in ('codex', 'claude'))
        self.adapter = adapter
        self._buffer = bytearray()
        self._lines = 0
        self._sequence = 0
        self._active = False
        self._finished = False
        self._failed = False
        self._input = 0
        self._cached = 0
        self._creation = 0
        self._output = 0
        self._reasoning = 0

    def _snapshot(self, input_tokens, cached, creation, output, reasoning, cost):
        for value in (input_tokens, cached, output):
            _counter(value)
        if creation is None:
            _require(self.adapter == 'codex')
        else:
            _counter(creation)
        _require(cached + (creation or 0) <= input_tokens and input_tokens + output <= MAX_TOKENS)
        if reasoning is not None:
            _counter(reasoning)
            _require(reasoning <= output)
        self._sequence += 1
        _require(self._sequence <= MAX_LINES)
        return dict(sequence=self._sequence, input_tokens=input_tokens,
                    cached_input_tokens=cached, cache_creation_input_tokens=creation,
                    output_tokens=output, reasoning_output_tokens=reasoning,
                    total_tokens=input_tokens + output, reported_cost_nano_usd=cost)

    def _line(self, raw):
        self._lines += 1
        _require(self._lines <= MAX_LINES and 0 < len(raw) <= MAX_LINE_BYTES)
        try:
            record = json.loads(raw.decode('utf-8'), parse_float=Decimal,
                                parse_constant=_constant, parse_int=_integer, object_pairs_hook=_pairs)
        except (ValueError, UnicodeError, RecursionError, OverflowError, DecimalException):
            raise ValueError(_ERROR) from None
        _require(isinstance(record, dict) and isinstance(record.get('type'), str))
        kind = record['type']
        if self.adapter == 'codex':
            if kind == 'turn.started':
                _require(not self._active)
                self._active = True
            elif kind in ('turn.failed', 'error'):
                raise ValueError(_ERROR)
            elif kind == 'turn.completed':
                _require(self._active and isinstance(record.get('usage'), dict))
                usage = record['usage']
                for required in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
                    _require(required in usage)
                incoming = _counter(usage['input_tokens'])
                cached = _counter(usage['cached_input_tokens'])
                creation = usage.get('cache_creation_input_tokens')
                if creation is not None:
                    _counter(creation)
                output = _counter(usage['output_tokens'])
                reasoning = usage.get('reasoning_output_tokens')
                _require(cached + (creation or 0) <= incoming)
                if reasoning is not None:
                    _counter(reasoning)
                    _require(reasoning <= output)
                total_reasoning = None if reasoning is None or self._reasoning is None else self._reasoning + reasoning
                total_creation = None if creation is None or self._creation is None else self._creation + creation
                snapshot = self._snapshot(self._input + incoming, self._cached + cached,
                                          total_creation, self._output + output,
                                          total_reasoning, None)
                self._input, self._cached, self._creation = snapshot['input_tokens'], snapshot['cached_input_tokens'], snapshot['cache_creation_input_tokens']
                self._output, self._reasoning = snapshot['output_tokens'], snapshot['reasoning_output_tokens']
                self._active = False
                return [snapshot]
        elif kind == 'result':
            _require(self._sequence == 0)
            subtype = record.get('subtype', 'success')
            _require(subtype in ('success', 'error_max_budget_usd', 'error_max_turns'))
            _require(type(record.get('is_error', False)) is bool)
            # Documented budget/turn failures still report the crossing request's
            # full modelUsage and cost. Transport exit determines task failure;
            # accounting must preserve that spend before it handles the exit.
            if subtype == 'success':
                _require(not record.get('is_error', False))
            models = record.get('modelUsage')
            _require(isinstance(models, dict) and bool(models))
            incoming = cached = creation = output = 0
            for usage in models.values():
                _require(isinstance(usage, dict))
                for required in ('inputTokens', 'cacheReadInputTokens', 'cacheCreationInputTokens', 'outputTokens'):
                    _require(required in usage)
                uncached = _counter(usage['inputTokens'])
                cache_read = _counter(usage['cacheReadInputTokens'])
                cache_write = _counter(usage['cacheCreationInputTokens'])
                output += _counter(usage['outputTokens'])
                incoming += uncached + cache_read + cache_write
                cached += cache_read
                creation += cache_write
            _require('total_cost_usd' in record)
            return [self._snapshot(incoming, cached, creation, output, None,
                                   _nano(record['total_cost_usd']))]
        elif kind == 'error':
            raise ValueError(_ERROR)
        return []

    def feed(self, chunk):
        _require(not self._finished and not self._failed and isinstance(chunk, bytes))
        snapshots = []
        try:
            # Scan without concatenating an arbitrarily large caller chunk into memory.
            start = 0
            while start < len(chunk):
                end = chunk.find(b'\n', start)
                stop = len(chunk) if end < 0 else end
                _require(len(self._buffer) + stop - start <= MAX_LINE_BYTES)
                self._buffer.extend(chunk[start:stop])
                if end < 0:
                    break
                line = bytes(self._buffer)
                self._buffer.clear()
                snapshots.extend(self._line(line))
                start = end + 1
            return snapshots
        except (ValueError, TypeError, RecursionError, OverflowError, DecimalException):
            self._buffer.clear()
            self._failed = True
            raise ValueError(_ERROR) from None

    def finish(self):
        _require(not self._finished and not self._failed)
        self._finished = True
        try:
            snapshots = self._line(bytes(self._buffer)) if self._buffer else []
            self._buffer.clear()
            _require(self._sequence > 0 and not self._active)
            return snapshots
        except (ValueError, TypeError, RecursionError, OverflowError, DecimalException):
            self._buffer.clear()
            self._failed = True
            raise ValueError(_ERROR) from None
