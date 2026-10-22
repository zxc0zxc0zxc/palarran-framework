"""Bounded resource telemetry rejects missing/ambiguous money rather than inventing zero."""
import json
import unittest
from orchestrator.ml_resources import CostStream


class ResourceStreamTest(unittest.TestCase):
    def test_chunked_terminal_receipt_and_ordinary_logs(self):
        stream = CostStream()
        self.assertEqual(stream.feed(b'epoch progress\n{"type":"ml.'), [])
        result = stream.feed(b'usage","sequence":1,"cost_usd":"0.1","terminal":true}\n')
        self.assertEqual(result[0]['cost_usd'], '0.1')
        self.assertEqual(stream.finish(), [])

    def test_missing_null_or_duplicate_terminal_is_not_known_zero(self):
        for cost in (None, '0'):
            stream = CostStream()
            stream.feed((json.dumps(dict(type='ml.usage', sequence=1, cost_usd=cost, terminal=cost is None)) + '\n').encode())
            with self.assertRaises(ValueError):
                stream.finish()
        stream = CostStream()
        data = b'{"type":"ml.usage","sequence":1,"cost_usd":"0","terminal":true}\n'
        stream.feed(data)
        with self.assertRaises(ValueError): stream.feed(data)

    def test_invalid_receipts_and_duplicate_fields_fail(self):
        for data in (
            b'{"type":"ml.usage","sequence":true,"cost_usd":"0","terminal":true}\n',
            b'{"type":"ml.usage","sequence":1,"cost_usd":"NaN","terminal":true}\n',
            b'{"type":"ml.usage","sequence":1,"cost_usd":"0","cost_usd":"1","terminal":true}\n',
            b'malformed ml.usage line\n',
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                CostStream().feed(data)

    def test_unbounded_line_is_rejected(self):
        with self.assertRaises(ValueError):
            CostStream().feed(b'x' * 1048577)


if __name__ == '__main__':
    unittest.main()
