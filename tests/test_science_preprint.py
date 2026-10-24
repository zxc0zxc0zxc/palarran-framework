"""Offline scientific export integrity/privacy; no TeX shell, training or model calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import ml_data as data
from scripts.science_preprint import build


class SciencePreprintTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.report=dict(artifact_type='ml-training-report',schema_version=1,training_outcome='failed',report_status='partial',
            context_sha256='a'*64,diagnostics_sha256='b'*64,run_status='failed',reason='budget_exhausted',benchmark_verdict='not_run',verification_status='not_run',
            metrics=[dict(metric=r'quality_%\input{private}',split='validation',step=1,value=.5,support=2,subject='c'*64)],
            generations=[dict(payload=dict(output='PRIVATE_SENTINEL'))],missing=['final_evaluation'],errors=[],limitations=['Synthetic observations only.'])
        self.source=self.root/'report.json';self.save()
    def save(self):
        self.report.pop('report_sha256',None);self.report['report_sha256']=data.digest(self.report)
        self.source.write_text(data.canonical(self.report))
    def test_export_is_escaped_traceable_private_and_source_only(self):
        out=self.root/'paper';result=build(self.source,out,title=r'Cost $5 & \input{secret}')
        source=(out/'main.tex').read_text()
        self.assertNotIn('PRIVATE_SENTINEL',source)
        self.assertIn(r'\textbackslash{}input\{secret\}',source)
        self.assertIn('budget',source)
        self.assertIn('final',source)
        self.assertEqual(result['compiled'],'NOT_RUN')
        claims=json.loads((out/'evidence.json').read_text())['claims']
        self.assertEqual(claims[0]['source_pointer'],'/metrics/0')
        manifest=json.loads((out/'source-manifest.json').read_text())
        for name,digest in manifest['files'].items():self.assertEqual(data.sha((out/name).read_bytes()),digest)
        with self.assertRaises(ValueError):build(self.source,out)
    def test_changed_evidence_cannot_export(self):
        altered=dict(self.report,training_outcome='completed')
        self.source.write_text(json.dumps(altered))
        with self.assertRaises(ValueError):build(self.source,self.root/'paper')
        self.assertFalse((self.root/'paper').exists())
    def test_cli_does_not_print_sensitive_results_on_failure(self):
        self.source.write_text('PRIVATE_SENTINEL')
        script=Path(__file__).resolve().parents[1]/'scripts/science_preprint.py'
        result=subprocess.run([sys.executable,str(script),'--report',str(self.source),'--output',str(self.root/'paper')],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertNotIn('PRIVATE_SENTINEL',result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
