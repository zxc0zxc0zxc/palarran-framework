"""Saved-prefix reuse and inherited budget, without provider calls."""
from contextlib import closing
import copy
import json
from pathlib import Path
import tempfile
import unittest
from orchestrator.accounting import default_usage_policy, usage_exceeded
from orchestrator.engine import status,work
from orchestrator.product_artifacts import canonical_sha
from orchestrator.product_continue import continuation, create_continuation
from orchestrator.context_packet import packet
import test_product_artifacts as fixtures
import test_factory_core as core
from orchestrator.budgets import default_policy


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve()
        self.source,self.context=fixtures.make_target(self.base/'source')
        fixtures.write_stage(self.source,self.context,'define')
        self.pid=self.context['pipeline_id'];self.skills=fixtures.SKILLS_ROOT

    def policy(self):
        tasks=[dict(id='product-'+s,adapter='codex') for s in ('market','compare','revenue','acquisition','mvp')]
        policy=default_usage_policy(tasks)
        policy['carry']=[dict(source='fixture/import',observed_tokens=0,observed_cost_usd='0',reserved_tokens=0,reserved_cost_usd='0',unknown=False)]
        return policy

    def test_saved_define_is_only_command_verification_not_new_model_task(self):
        flow,context,data,digests=continuation(self.source,self.pid,'define',self.skills,'/fake/codex',self.policy(),route='b2b',budget_ceiling='12.00')
        self.assertEqual(context,self.context)
        self.assertEqual([t['id'] for t in flow['tasks'] if t['adapter']=='codex'],['product-market','product-compare','product-revenue','product-acquisition','product-mvp'])
        self.assertEqual(flow['ai_policy']['max_calls'],5)
        prefix='.palarran/product/pipeline-'+self.pid+'/stages/define/stage.json'
        self.assertEqual(data[prefix],(self.source/prefix).read_bytes())
        name,body=packet(self.source,self.pid,'market',canonical_sha(context),self.skills,'b2b')
        self.assertIn(b'Canonical prefix index',body);self.assertLessEqual(len(body),196608)
        again=packet(self.source,self.pid,'market',canonical_sha(context),self.skills,'b2b')
        self.assertEqual((name,body),again)
        (self.source/prefix).write_text('{}')
        with self.assertRaises(ValueError):packet(self.source,self.pid,'market',canonical_sha(context),self.skills,'b2b')

    def test_missing_carry_or_increased_ceiling_rejected(self):
        for mutate in (lambda p:p.pop('carry'), lambda p:p.update(max_cost_usd='13.00')):
            policy=self.policy();mutate(policy)
            with self.assertRaises(ValueError):
                continuation(self.source,self.pid,'define',self.skills,'/fake/codex',policy,route='b2b',budget_ceiling='12.00')

    def test_carry_exhaustion_stops_before_any_model_launch(self):
        # Core synthetic command needs no executable provider to prove admission guard.
        task=dict(id='ai',adapter='codex',executable='/fake/codex',prompt='never run',verify=[core.command('pass')],model_role='planning',model_calls=1)
        flow=core.workflow([task]);flow['policy']['adapters']=['codex'];flow['policy']['executables'].append('/fake/codex')
        flow['ai_policy']=default_policy('codex');flow['usage_policy']=default_usage_policy([task])
        flow['usage_policy']['carry']=[dict(source='old/1',observed_tokens=100,observed_cost_usd='1',reserved_tokens=100,reserved_cost_usd='12',unknown=True)]
        from orchestrator.engine import create
        # Source target is dirty from fixture artifacts: use separately clean baseline.
        clean=self.base/'clean';clean.mkdir()
        import subprocess
        for args in [('init','-q'),('config','user.name','Fixture'),('config','user.email','fixture@example.invalid')]:subprocess.run(['git','-C',str(clean),*args],check=True)
        (clean/'README.md').write_text('Baseline')
        subprocess.run(['git','-C',str(clean),'add','.'],check=True);subprocess.run(['git','-C',str(clean),'commit','-qm','baseline'],check=True)
        state=self.base/'state';run=create(state,flow,clean)
        self.assertEqual(work(state,run),'failed')
        report=status(state,run)
        self.assertEqual(report['reason'],'usage_budget_exhausted');self.assertEqual(report['tasks'][0]['attempts'],0)
        self.assertFalse(report['usage']['complete']);self.assertEqual(report['usage']['available_reserved_cost_usd'],'0.000000000')

    def test_actual_five_stage_continuation_preserves_import_and_receipts(self):
        import subprocess,sys
        from orchestrator.import_guard import check
        target=self.base/'target'
        subprocess.run(['git','clone','-q','--no-hardlinks',str(self.source),str(target)],check=True)
        extra='.palarran/product/pipeline-'+self.pid+'/stages/define/evidence.md'
        (self.source/extra).write_text('Original evidence appendix')
        provider=self.base/'fake-server';calls=self.base/'called-stages.txt'
        provider.write_text('#!'+sys.executable+'\n'+'''import json,sys,re
from pathlib import Path
sys.path.insert(0,'''+repr(str(self.skills))+''')
sys.path.insert(0,'''+repr(str(self.skills/'tests'))+''')
from test_product_artifacts import write_stage
from orchestrator.product_artifacts import pipeline_dir
thread='fixture-thread';turn='fixture-turn'
def emit(v):print(json.dumps(v),flush=True)
for line in sys.stdin:
 r=json.loads(line);method=r['method'];i=r.get('id')
 if method=='initialize':emit({'id':i,'result':{}})
 elif method=='thread/start':emit({'id':i,'result':{'thread':{'id':thread}}})
 elif method=='turn/start':
  prompt=r['params']['input'][0]['text'];meta=json.loads(prompt.splitlines()[0].split(' ',1)[1]);stage=meta['stage'];root=Path.cwd();base=pipeline_dir(root,meta['pipeline_id']);context=json.loads((base/'context.json').read_text())
  with open('''+repr(str(calls))+''','a') as out:out.write(stage+'\\n')
  emit({'id':i,'result':{'turn':{'id':turn}}})
  for n in (100,200):
   emit({'method':'thread/tokenUsage/updated','params':{'threadId':thread,'turnId':turn,'tokenUsage':{'total':{'inputTokens':n,'cachedInputTokens':50,'outputTokens':50,'reasoningOutputTokens':10,'totalTokens':n+50}}}})
  write_stage(root,context,stage)
  handoff=Path(re.search(r'write (.+?/handoff\\.json) as a JSON object',prompt).group(1));handoff.write_text('{"status":"implemented"}')
  emit({'method':'turn/completed','params':{'threadId':thread,'turn':{'id':turn,'status':'completed'}}})
''');provider.chmod(0o700)
        state=self.base/'continued-state'
        run=create_continuation(state,target,self.source,self.pid,'define',self.skills,str(provider),self.policy(),route='b2b',budget_ceiling='12.00')
        self.assertEqual(work(state,run),'verified')
        report=status(state,run);root=Path(report['workspace'])
        self.assertEqual(calls.read_text().splitlines(),['market','compare','revenue','acquisition','mvp'])
        self.assertEqual(report['usage']['observed_tokens'],1250)
        self.assertEqual(report['budget']['charged_calls'],5)
        self.assertEqual(report['product']['recommendation'],'plan')
        self.assertEqual((root/extra).read_bytes(),(self.source/extra).read_bytes())
        receipt='.palarran/product/pipeline-'+self.pid+'/imports/prefix.json'
        import hashlib
        digest=hashlib.sha256((root/receipt).read_bytes()).hexdigest()
        check(root,receipt,digest)
        (root/extra).write_text('Tampered appendix')
        with self.assertRaises(ValueError):check(root,receipt,digest)
