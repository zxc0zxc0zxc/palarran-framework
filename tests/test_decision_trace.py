"""Safe highlighting of short public summaries; untrusted text is inert."""
import copy
import unittest
from orchestrator.decision_trace import render, validate


class DecisionTraceTests(unittest.TestCase):
    def fixture(self):
        return dict(version=1, review_status='draft', task='CLI diagnosis', steps=[dict(
            id='S-1',action='Check provider',summary='<script>alert(1)</script>',evidence=['E-1'],decision_ref='ADR-1',outcome='unknown')])

    def test_html_escapes_text_and_preserves_step_anchor(self):
        page=render(self.fixture())
        self.assertIn('id="S-1" class="unknown"',page)
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn('не подтверждает',page)

    def test_duplicate_steps_raw_reasoning_and_injected_outcomes_rejected(self):
        for mutate in (lambda d:d['steps'].append(copy.deepcopy(d['steps'][0])),
                       lambda d:d['steps'][0].update(reasoning='private'),
                       lambda d:d['steps'][0].update(outcome='" onmouseover="alert(1)'),
                       lambda d:d['steps'][0].update(summary='x'*601)):
            value=self.fixture();mutate(value)
            with self.assertRaises(ValueError):validate(value)
