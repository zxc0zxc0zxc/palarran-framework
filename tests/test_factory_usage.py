"""Synthetic JSONL usage receipts; no provider calls or source payload retention."""
import json
import unittest

from orchestrator.usage import MAX_LINE_BYTES, MAX_LINES, UsageStream


def encoded(value):
    return json.dumps(value, separators=(',', ':')).encode('utf-8') + b'\n'


def codex(input_tokens=10, cached=3, output=4, **fields):
    usage = dict(input_tokens=input_tokens, cached_input_tokens=cached, output_tokens=output)
    usage.update(fields)
    return encoded(dict(type='turn.started')) + encoded(dict(type='turn.completed', usage=usage))


def claude(cost=0.0001, **fields):
    value = dict(type='result', subtype='success', is_error=False, total_cost_usd=cost,
                 modelUsage={'synthetic-model': dict(inputTokens=10, cacheReadInputTokens=3,
                                                     cacheCreationInputTokens=2, outputTokens=4)})
    value.update(fields)
    return encoded(value)


class UsageStreamTests(unittest.TestCase):
    def parse(self, adapter, data):
        parser = UsageStream(adapter)
        return parser.feed(data) + parser.finish()

    def test_codex_cumulative_cache_and_reasoning_not_double_counted(self):
        snapshots = self.parse('codex', codex(cache_creation_input_tokens=2, reasoning_output_tokens=3) +
                               codex(20, 5, 8, cache_creation_input_tokens=1, reasoning_output_tokens=4))
        self.assertEqual(snapshots[-1], dict(sequence=2, input_tokens=30, cached_input_tokens=8,
                                           cache_creation_input_tokens=3, output_tokens=12,
                                           reasoning_output_tokens=7, total_tokens=42, reported_cost_nano_usd=None))

    def test_arbitrary_byte_boundaries_including_utf8(self):
        data = encoded(dict(type='item.completed', item={'text':'секрет'})) + codex()
        parser = UsageStream('codex')
        receipts = []
        for byte in data:
            receipts += parser.feed(bytes([byte]))
        receipts += parser.finish()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]['total_tokens'], 14)
        self.assertNotIn('секрет', repr(vars(parser)))

    def test_final_line_without_newline(self):
        parser = UsageStream('codex')
        self.assertEqual(parser.feed(codex().rstrip(b'\n')), [])
        self.assertEqual(parser.finish()[0]['total_tokens'], 14)
        with self.assertRaises(ValueError):
            parser.feed(b'')
        with self.assertRaises(ValueError):
            parser.finish()

    def test_claude_sum_models_and_ignore_assistant_usage(self):
        models = {'m1':dict(inputTokens=10, cacheReadInputTokens=3, cacheCreationInputTokens=2, outputTokens=4),
                  'm2':dict(inputTokens=20, cacheReadInputTokens=7, cacheCreationInputTokens=5, outputTokens=8)}
        ignored = encoded(dict(type='assistant', message={'usage':{'input_tokens':999999}, 'content':'SECRET-KEY'}))
        snapshots = self.parse('claude', ignored + claude(modelUsage=models))
        self.assertEqual(len(snapshots), 1)
        receipt = snapshots[0]
        self.assertEqual((receipt['input_tokens'], receipt['cached_input_tokens'], receipt['cache_creation_input_tokens'],
                          receipt['output_tokens'], receipt['total_tokens']), (47, 10, 7, 12, 59))
        self.assertIsNone(receipt['reasoning_output_tokens'])
        self.assertEqual(receipt['reported_cost_nano_usd'], 100000)
        self.assertNotIn('SECRET', repr(receipt))
        self.assertNotIn('m1', repr(receipt))

    def test_cost_decimal_precision_and_ceil(self):
        data = claude().replace(b'0.0001', b'0.0000000001')
        self.assertEqual(self.parse('claude', data)[0]['reported_cost_nano_usd'], 1)
        data = claude().replace(b'0.0001', b'0.1234567890000000000000001')
        self.assertEqual(self.parse('claude', data)[0]['reported_cost_nano_usd'], 123456790)
        self.assertEqual(self.parse('claude', claude(cost=0))[0]['reported_cost_nano_usd'], 0)
        data = claude().replace(b'0.0001', b'1e-10000000')
        self.assertEqual(self.parse('claude', data)[0]['reported_cost_nano_usd'], 1)

    def test_missing_terminal_and_unfinished_turn(self):
        for adapter, data in (('codex', b''), ('claude', b''), ('codex', encoded(dict(type='turn.started'))),
                              ('claude', encoded(dict(type='assistant', usage={'input_tokens':1}))),
                              ('codex', codex() + encoded(dict(type='turn.started')))):
            with self.subTest(adapter=adapter, data=data), self.assertRaises(ValueError):
                self.parse(adapter, data)

    def test_duplicate_terminals_and_starts(self):
        for adapter, data in (('claude', claude() + claude()), ('codex', codex() + codex().split(b'\n',1)[1]),
                              ('codex', encoded(dict(type='turn.started')) + codex())):
            with self.subTest(adapter=adapter), self.assertRaises(ValueError):
                self.parse(adapter, data)

    def test_known_errors_fail_closed(self):
        for data in (claude(subtype='error_during_execution'), claude(is_error=True),
                     claude(subtype='error_max_budget_usd'), encoded(dict(type='error', error='SECRET'))):
            with self.assertRaises(ValueError) as caught:
                self.parse('claude', data)
            self.assertNotIn('SECRET', str(caught.exception))
        with self.assertRaises(ValueError):
            self.parse('codex', encoded(dict(type='turn.failed', error='SECRET')))

    def test_missing_claude_counters_model_map_and_cost(self):
        for fields in ({'modelUsage':{}}, {'modelUsage':None}, {'modelUsage':{'m':{'inputTokens':1}}},
                       {'total_cost_usd':None}, {'total_cost_usd':'0.1'}, {'total_cost_usd':True}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.parse('claude', claude(**fields))

    def test_invalid_counters_booleans_negative_fraction_and_bound(self):
        for value in (True, -1, 0.2, '3', None, 10**12+1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse('codex', codex(input_tokens=value))
        for fields in ({'cache_creation_input_tokens':8}, {'reasoning_output_tokens':5}):
            with self.assertRaises(ValueError):
                self.parse('codex', codex(**fields))
        with self.assertRaises(ValueError):
            self.parse('codex', codex(10**12, 0, 1))
        with self.assertRaises(ValueError):
            self.parse('codex', codex(10**12,0,0) + codex())

    def test_claude_aggregate_overflow_and_cost_bounds(self):
        for data in (claude(cost=-1), claude(cost=1000001), claude(cost=float('inf')),
                     claude(modelUsage={'m':dict(inputTokens=10**12, cacheReadInputTokens=1,
                                                cacheCreationInputTokens=0, outputTokens=0)})):
            with self.assertRaises(ValueError):
                self.parse('claude', data)

    def test_unknown_reasoning_propagates_without_invention(self):
        receipts = self.parse('codex', codex(reasoning_output_tokens=2) + codex() + codex(reasoning_output_tokens=1))
        self.assertEqual([item['reasoning_output_tokens'] for item in receipts], [2, None, None])

    def test_malformed_duplicate_json_nonobject_and_utf8(self):
        for data in (b'not json\n', b'[]\n', b'{}\n', b'\xff\n', b'\n', b'{"type":"x","type":"y"}\n',
                     b'{"type":"x","usage":NaN}\n', b'{"type":"x","x":1e99999999999999999999999}\n'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.parse('codex', data)

    def test_line_and_count_bounds_and_failed_parser_clears_buffer(self):
        parser = UsageStream('codex')
        parser.feed(b'x' * MAX_LINE_BYTES)
        with self.assertRaises(ValueError):
            parser.feed(b'x')
        self.assertEqual(parser._buffer, b'')
        with self.assertRaises(ValueError):
            parser.finish()
        parser = UsageStream('codex')
        parser.feed(encoded(dict(type='ignored')) * MAX_LINES)
        with self.assertRaises(ValueError):
            parser.feed(encoded(dict(type='ignored')))

    def test_depth_and_huge_integer_fail_safely(self):
        for data in (b'{"type":"ignored","x":' + b'[' * 2000 + b'0' + b']' * 2000 + b'}\n',
                     b'{"type":"ignored","x":' + b'9' * 10000 + b'}\n'):
            with self.assertRaises(ValueError) as caught:
                self.parse('codex', data)
            self.assertEqual(str(caught.exception), 'Invalid or incomplete provider usage stream')

    def test_unrecognized_messages_cannot_spoof_usage(self):
        data = encoded(dict(type='item.completed', usage={'input_tokens':900000})) + codex()
        self.assertEqual(self.parse('codex', data)[0]['total_tokens'], 14)

    def test_invalid_adapter_and_input_type(self):
        with self.assertRaises(ValueError):
            UsageStream('command')
        with self.assertRaises(ValueError):
            UsageStream('codex').feed('text')


if __name__ == '__main__':
    unittest.main()
