"""Canonical/legacy localized decision sections retain all semantic gates."""
import unittest
from orchestrator.product_artifacts import HEADINGS, LEGACY_HEADINGS, SERBIAN_HEADINGS, has_decision_sections

class DecisionSectionsTest(unittest.TestCase):
    def test_locales_keep_required_sections(self):
        for headings in (HEADINGS, LEGACY_HEADINGS, SERBIAN_HEADINGS):
            document = '\n'.join('## '+heading+'\nRationale.' for heading in headings)
            self.assertTrue(has_decision_sections(document))
            self.assertFalse(has_decision_sections('\n'.join('## '+h for h in headings[:-1])))
            self.assertFalse(has_decision_sections('Example text says ## '+headings[-1]))

if __name__ == '__main__':
    unittest.main()
