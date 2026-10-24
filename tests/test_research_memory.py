"""Compatible R&D result cards through the real automatic memory cycle, offline."""
import copy
import json
import unittest
import test_memory_cycle as fixtures


class ResearchMemoryTest(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.MemoryCycleTest();self.fixture.setUp()
    def tearDown(self):self.fixture.tearDown()

    def finding(self,outcome='inconclusive',condition='single-worker'):
        value=copy.deepcopy(self.fixture.value);case=value['case']
        case.update(type='decision',title='Synthetic cache benchmark',problem='H: cache lowers p95; subject fixture-v1; data fixture-a; protocol1000requests; '+condition,root_cause='Observed sample difference; causal effect and variability unknown.',solution='Method: cache-off baseline vs cache-on candidate, one run each. Metrics: p95 100ms vs90ms,1000requests each; lower is better. Uncertainty: unknown. Outcome: '+outcome+'. Resources: cost unknown. Conclusion: no general latency promise.',applies_when=['Same version, dataset and workload; exploratory comparison only'],limitations=['Synthetic fixture; single run; no production SLA or independent replication'],tags=['research-result','empirical',outcome,'cache'])
        return value

    def test_negative_and_inconclusive_results_publish_without_positive_outcome(self):
        for outcome in ('refuted','inconclusive'):
            value=self.finding(outcome);result=self.fixture.finish(value)
            self.assertEqual(result['status'],'PUBLISHED')
            stored=self.fixture.api.rows[result['id']]['case']
            self.assertIn('Outcome: '+outcome,stored['solution'])
            self.assertTrue(any('verified:PASS' in ref for ref in stored['evidence']))
            self.assertIn('cost unknown',stored['solution'])

    def test_distinct_conditions_do_not_deduplicate_and_recall_preserves_limits(self):
        first=self.fixture.finish(self.finding(condition='single-worker'))
        second=self.fixture.finish(self.finding(condition='two-workers'))
        self.assertNotEqual(first['id'],second['id'])
        repeat=self.fixture.finish(self.finding(condition='single-worker'))
        self.assertEqual(repeat['status'],'DUPLICATE');self.assertEqual(first['id'],repeat['id'])
        result=fixtures.cycle.start('project-a','engineering',self.fixture.home,self.fixture.api)
        self.assertEqual(len(result['cards']),2)
        self.assertTrue(all('no production SLA' in str(row) for row in result['cards']))

    def test_source_review_keeps_claim_and_local_not_tested_status(self):
        value=self.finding('not_tested');case=value['case']
        case['tags']=['research-result','source-review','not-tested']
        case['root_cause']='source_claim: primary paper reports a conditional result; not independently reproduced.'
        case['solution']='Attributed source review only. Outcome: not_tested locally; no observed local metrics.'
        case['limitations']=['Source verification is not replication; applicability unknown.']
        result=self.fixture.finish(value)
        stored=self.fixture.api.rows[result['id']]['case']
        self.assertIn('not independently reproduced',stored['root_cause'])
        self.assertIn('not_tested locally',stored['solution'])


if __name__=='__main__':unittest.main()
