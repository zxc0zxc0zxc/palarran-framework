"""Observable CLI failures without exporting raw payloads or private reasoning."""
import json
import unittest
from orchestrator.diagnostics import Diagnostics


class DiagnosticsTests(unittest.TestCase):
    def test_split_error_and_stderr_are_classified_without_private_text(self):
        d = Diagnostics()
        raw = (json.dumps({'type': 'turn.failed', 'error': {'message':
               'stream disconnected: error sending request https://secret.invalid/private?token=SENTINEL'}}) + '\n').encode()
        for byte in raw:
            d.feed('stdout', bytes([byte]))
        d.feed('stderr', b'401 Unauthorized Bearer SENTINEL\n')
        result = d.finish()
        self.assertEqual(result['codes'], ['authentication_failed', 'connection_failed', 'provider_error'])
        self.assertEqual(result['terminal_event'], 'turn.failed')
        self.assertNotIn('SENTINEL', json.dumps(result))
        self.assertNotIn('secret.invalid', json.dumps(result))

    def test_trace_is_bounded_and_ignores_reasoning_and_arguments(self):
        d = Diagnostics()
        for kind in ['reasoning', 'command_execution'] * 50:
            d.feed('stdout', (json.dumps({'type': 'item.completed', 'item': {
                'type': kind, 'text': 'PRIVATE_REASONING', 'command': 'SECRET_COMMAND', 'exit_code': 7}}) + '\n').encode())
        result = d.finish()
        self.assertEqual(len(result['steps']), 32)
        self.assertEqual(result['steps_dropped'], 18)
        self.assertEqual(result['event_count'], 100)
        self.assertTrue(all(s['kind'] == 'command_execution' and s['exit_code'] == 7 for s in result['steps']))
        self.assertNotIn('PRIVATE_REASONING', json.dumps(result))
        self.assertNotIn('SECRET_COMMAND', json.dumps(result))

    def test_oversized_lines_and_unknown_types_cannot_escape(self):
        d = Diagnostics()
        d.feed('stderr', b'SECRET' * 10000)
        self.assertLessEqual(sum(map(len, d.buffers.values())), 32768)
        d.feed('stderr', b'\ninvalid configuration\n')
        d.feed('stdout', b'{"type": [], "private": "SECRET"}\n')
        result = d.finish()
        self.assertIn('diagnostic_line_dropped', result['codes'])
        self.assertIn('configuration_invalid', result['codes'])
        self.assertNotIn('SECRET', json.dumps(result))
