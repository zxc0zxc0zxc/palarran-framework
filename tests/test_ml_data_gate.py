"""Real optional tokenizer tests. No installation, Hub, cloud, GPU or paid calls."""
from contextlib import closing
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from orchestrator.ml_data_gate import collate, freeze, mixed_ids, packet
from orchestrator.engine import status, work
from orchestrator.ml_resources import rows
from orchestrator.store import Store
from scripts import ml_data as data
from tests import test_ml_pipeline as fixture

ROOT = fixture.ROOT

BACKEND = os.environ.get('AI_TOOLS_TOKENIZER_PYTHON')


class CollatorTest(unittest.TestCase):
    def test_padding_does_not_mask_real_eos_when_pad_equals_eos(self):
        rows = [dict(id='a',input_ids=[4,9],labels=[4,9],attention_mask=[1,1],assistant_mask=[1,1]),
                dict(id='b',input_ids=[5,6,9],labels=[-100,6,9],attention_mask=[1,1,1],assistant_mask=[0,1,1])]
        batch = collate(rows,9)
        self.assertEqual(batch['input_ids'][0],[4,9,9])
        self.assertEqual(batch['labels'][0],[4,9,-100])
        self.assertEqual(batch['attention_mask'][0],[1,1,0])

    def mixture_fixture(self, sizes=(5,4), total=10, weights=('0.6','0.4'), repeat='2'):
        records = {str(i):dict(id=str(i),split='train',domain=d,language=l) for i,(d,l) in enumerate([('general','en'),('code','ru')])}
        encoded = {str(i):dict(input_ids=list(range(n))) for i,n in enumerate(sizes)}
        audit = dict(schema_version=1,artifact_type='ml-token-audit',status='PASS',expected_records=2,observed_records=2,
                     valid_records=2,issues={},dataset_sha256='0'*64,tokenization_verified=True,remaining_gates=[],
                     cells=[dict(split='train',domain=r['domain'],language=r['language'],records=1,input_tokens=sizes[i],target_tokens=sizes[i]) for i,r in enumerate(records.values())])
        audit['report_sha256']=data.digest(audit)
        recipe=dict(version=1,total_tokens=total,seed=1,cells=[dict(domain=r['domain'],language=r['language'],weight=weights[i],max_repeats=repeat) for i,r in enumerate(records.values())],
                    minimum_domain_shares={},minimum_language_shares={})
        return records,encoded,recipe,audit

    def test_actual_language_floor_blocks_rounded_whole_example_mix(self):
        records,encoded,recipe,audit=self.mixture_fixture()
        recipe['minimum_language_shares']={'en':'0.6'}
        with self.assertRaises(ValueError):
            mixed_ids(records,encoded,recipe,{'max_share_deviation':'0.9'},audit)

    def test_actual_domain_floor_blocks_rounded_whole_example_mix(self):
        records,encoded,recipe,audit=self.mixture_fixture()
        recipe['minimum_domain_shares']={'general':'0.6'}
        with self.assertRaises(ValueError):
            mixed_ids(records,encoded,recipe,{'max_share_deviation':'0.9'},audit)

    def test_fractional_repeat_ceiling_never_crops_or_adds_whole_repeat(self):
        records,encoded,recipe,audit=self.mixture_fixture(total=13,weights=('0.538461538','0.461538462'),repeat='1.5')
        chosen,result=mixed_ids(records,encoded,recipe,{'max_share_deviation':'0.5'},audit)
        self.assertEqual(sorted(chosen),['0','1'])
        self.assertEqual(result['actual_input_tokens'],9)

    def test_validation_example_cannot_be_sampled_as_train(self):
        records,encoded,recipe,audit=self.mixture_fixture(total=9,weights=('0.555555556','0.444444444'))
        records['heldout']=dict(records['0'],id='heldout',split='test')
        encoded['heldout']=dict(input_ids=[1])
        chosen,_=mixed_ids(records,encoded,recipe,{'max_share_deviation':'0.2'},audit)
        self.assertNotIn('heldout',chosen)

    def test_rounding_away_positive_cell_is_a_blocker(self):
        records,encoded,recipe,audit=self.mixture_fixture(sizes=(1,1),total=1,weights=('0.5','0.5'))
        with self.assertRaises(ValueError):
            mixed_ids(records,encoded,recipe,{'max_share_deviation':'1'},audit)


class DataModePolicyTest(unittest.TestCase):
    new = fixture.MLPipelineTest.new

    def setUp(self):
        fixture.MLPipelineTest.setUp(self)

    def test_new_request_must_declare_data_mode(self):
        self.execution.pop('data_mode')
        with self.assertRaises(ValueError):
            self.new()

    def test_text_mode_cannot_omit_preparation(self):
        self.execution['data_mode']='text'
        with self.assertRaises(ValueError):
            self.new()

    def test_non_text_cannot_smuggle_text_config(self):
        self.execution['data_preparation']={}
        with self.assertRaises(ValueError):
            self.new()


@unittest.skipUnless(BACKEND,'NOT RUN: set AI_TOOLS_TOKENIZER_PYTHON to an existing optional tokenizers environment')
class RealDataGateTest(unittest.TestCase):
    new = fixture.MLPipelineTest.new
    ready = fixture.MLPipelineTest.ready
    allow = fixture.MLPipelineTest.allow

    def setUp(self):
        fixture.MLPipelineTest.setUp(self)
        self.raw = self.base/'raw.jsonl'
        records = []
        for i,split in enumerate(['train','train','train','validation','test']):
            records.append(dict(id=str(i),group_id=str(i),source_id='owned',domain='general',language='en',
                                license='owned',rights_status='approved',rights_approval='fixture',split=split,
                                completion=dict(complete=True,finish_reason='authored'),
                                messages=[dict(role='user',content='question '+str(i)),dict(role='assistant',content='complete answer '+str(i))]))
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in records))
        self.tk = self.base/'tokenizer.json'
        result = self.backend("from tokenizers import Tokenizer,models,pre_tokenizers,trainers; "
            "t=Tokenizer(models.BPE(unk_token='[UNK]')); t.pre_tokenizer=pre_tokenizers.ByteLevel(add_prefix_space=False); "
            "trainer=trainers.BpeTrainer(vocab_size=300,initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),"
            "special_tokens=['[UNK]','<e>','<u>','<a>','<s>']); "
            "t.train_from_iterator(['question complete answer 0123456789'],trainer); t.save(__import__('sys').argv[1])",str(self.tk))
        self.assertEqual(result.returncode,0,result.stderr)
        self.template = self.base/'template.json'
        self.template.write_text(data.canonical(dict(version=1,bos='',text_suffix='<e>',roles={
            role:dict(prefix=prefix,suffix='<e>') for role,prefix in [('system','<s>'),('user','<u>'),('assistant','<a>')]})))
        self.split = self.base/'split.json'; self.split.write_text(data.canonical(dict(version=1,seed=42,split_weights=dict(train='0.8',validation='0.1',test='0.1'))))
        self.recipe = self.base/'mixture.json'; self.recipe.write_text(data.canonical(dict(version=1,total_tokens=16,seed=42,
            cells=[dict(domain='general',language='en',weight='1',max_repeats='2')],minimum_domain_shares={'general':'1'},minimum_language_shares={'en':'1'})))
        result = self.backend("from tokenizers import Tokenizer; import sys; t=Tokenizer.from_file(sys.argv[1]); print(t.token_to_id('<e>'))",str(self.tk))
        eos = int(result.stdout.strip())
        self.config = dict(python=BACKEND,source=str(self.raw),tokenizer=str(self.tk),template=str(self.template),split=str(self.split),
            mixture=str(self.recipe),tokenizers_version='0.22.1',objective='assistant',max_sequence_tokens=128,end_token_ids=[eos],
            pad_token_id=eos,batch_size=2,length_bins=[16,128],max_share_deviation='0.9',max_output_bytes=1024*1024)
        self.execution['data_preparation'] = self.config
        self.execution['data_mode'] = 'text'
        self.job = ROOT/'examples/ml-pipeline/text_job.py'
        for name in ('train','evaluate'):
            self.execution[name]['argv'][1] = str(self.job)
            self.execution[name]['files'][1] = str(self.job)

    def backend(self, code, *args):
        env = dict(os.environ,PYTHONPATH=str(ROOT))
        return subprocess.run([BACKEND,'-c',code,*args],capture_output=True,text=True,env=env,timeout=20)

    def generated(self, config=None):
        config = freeze(config or self.config)
        output = self.base/'prepared'
        result = self.backend('import sys,json; from orchestrator.ml_data_gate import generate; generate(json.loads(sys.argv[1]),sys.argv[2])',data.canonical(config),str(output))
        return result,config,output

    def test_real_encode_collate_and_independent_regeneration(self):
        result,config,output = self.generated()
        self.assertEqual(result.returncode,0,result.stderr)
        receipt = data.load(output/'receipt.json')
        self.assertTrue(receipt['tokenization_verified'] and receipt['collator_verified'])
        policy = dict(data_preparation=config,artifact_root=str(self.base))
        output.rename(self.base/'prepared-data')
        result = self.backend('import sys,json; from orchestrator.ml_data_gate import verify; verify(json.loads(sys.argv[1]))',data.canonical(policy))
        self.assertEqual(result.returncode,0,result.stderr)
        tokens,_,_ = data.rows(self.base/'prepared-data/tokens.jsonl')
        self.assertTrue(any(-100 in t['labels'] for t in tokens))
        self.assertTrue(all(t['labels'][sum(t['attention_mask'])-1] == self.config['end_token_ids'][0] for t in tokens))

    def test_causal_text_uses_all_active_targets(self):
        records,_,_=data.rows(self.raw)
        for record in records:
            record['text']=record.pop('messages')[-1]['content']
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in records))
        self.config['objective']='causal'
        result,_,output=self.generated()
        self.assertEqual(result.returncode,0,result.stderr)
        tokens,_,_=data.rows(output/'tokens.jsonl')
        for row in tokens:
            self.assertTrue(all(label==token if active else label==-100 for token,label,active in zip(row['input_ids'],row['labels'],row['attention_mask'])))

    def test_output_budget_is_a_blocker(self):
        self.config['max_output_bytes']=1024
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_end_to_end_consumes_actual_batches_and_retains_budget(self):
        run,flow = self.ready()
        self.assertEqual(status(self.state,run)['ml']['data_gate'],'needs_input')
        self.assertEqual(status(self.state,run)['ml']['attempts'],[])
        self.allow(run)
        self.assertEqual(work(self.state,run),'verified',status(self.state,run))
        report = status(self.state,run)
        self.assertEqual(report['ml']['data_gate'],'PASS')
        self.assertEqual(report['ml']['total_usd'],'3')
        self.assertEqual(report['ml']['ai_envelope_usd'],'1')
        self.assertEqual(report['ml']['evaluation']['verdict'],'accept')
        prepared = packet(flow['ml_policy'])
        model = data.load(Path(flow['ml_policy']['artifact_root'])/'checkpoint.bin')
        self.assertEqual(model['prepared_sha256'],prepared['receipt_sha256'])
        (Path(prepared['directory'])/'tokens.jsonl').write_text('{}\n')
        self.assertEqual(status(self.state,run)['status'],'stale')

    def test_overflow_blocks_training_without_resource_attempts(self):
        self.config['max_sequence_tokens'] = 2
        run,_ = self.ready(); self.allow(run)
        self.assertNotEqual(work(self.state,run),'verified')
        with closing(Store(self.state)) as store:
            self.assertEqual(rows(store,run),[])
            self.assertEqual(next(t for t in store.tasks(run) if t['id']=='ml-fit')['attempts'],0)

    def test_impossible_mixture_blocks_training(self):
        recipe = data.load(self.recipe); recipe['cells'][0]['language']='ru'
        self.recipe.write_text(data.canonical(recipe))
        run,_ = self.ready(); self.allow(run)
        self.assertNotEqual(work(self.state,run),'verified')
        with closing(Store(self.state)) as store:
            self.assertEqual(rows(store,run),[])

    def test_quarantined_incomplete_record_blocks_preparation(self):
        rows_,_,_ = data.rows(self.raw); rows_[0]['messages'][-1]['content']=''
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in rows_))
        result,_,output = self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_wrong_end_token_and_missing_substantive_target_fail(self):
        self.template.write_text(self.template.read_text().replace('"suffix":"<e>"','"suffix":""'))
        result,_,_ = self.generated()
        self.assertNotEqual(result.returncode,0)

    def test_eos_only_raw_answer_cannot_pass_as_complete(self):
        records,_,_=data.rows(self.raw)
        records[0]['messages'][-1]['content']='<e>'
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in records))
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_incompatible_backend_version_fails_without_receipt(self):
        self.config['tokenizers_version']='0.0.0'
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(output.exists())

    def test_known_length_stop_cannot_be_fixed_by_appending_eos(self):
        records,_,_=data.rows(self.raw)
        records[0]['completion']=dict(complete=True,finish_reason='length')
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in records))
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_missing_completion_claim_blocks_messages(self):
        records,_,_=data.rows(self.raw); records[0].pop('completion')
        self.raw.write_text(''.join(data.canonical(r)+'\n' for r in records))
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_source_symlink_is_rejected_before_run(self):
        alias=self.base/'alias.jsonl'; alias.symlink_to(self.raw)
        self.config['source']=str(alias)
        with self.assertRaises(ValueError):
            self.new()

    def test_missing_data_mode_rejected_before_run(self):
        execution=copy.deepcopy(self.execution); execution.pop('data_mode')
        with self.assertRaises(ValueError):
            self.new(execution)

    def test_text_without_preparation_rejected_before_run(self):
        execution=copy.deepcopy(self.execution); execution.pop('data_preparation')
        with self.assertRaises(ValueError):
            self.new(execution)

    def test_lineage_mismatch_blocks_preparation_and_resources(self):
        run,flow=self.ready()
        from orchestrator.ml_data_gate import bind
        from orchestrator.ml_artifacts import validate_prefix
        with closing(Store(self.state)) as store:
            root=store.get(run)['workspace']
            prefix=validate_prefix(root,flow['ml_policy'])
            wrong=copy.deepcopy(flow['ml_policy']); wrong['data_preparation']['max_sequence_tokens']=8
            with self.assertRaises(ValueError):
                bind(root,wrong,prefix)
            self.assertEqual(rows(store,run),[])

    def test_source_drift_rejects_approval(self):
        run,_ = self.ready()
        self.raw.write_text(self.raw.read_text()+'\n')
        with self.assertRaises(ValueError):
            self.allow(run)
        with closing(Store(self.state)) as store:
            self.assertEqual(rows(store,run),[])

    def test_strict_mixture_does_not_crop_examples(self):
        self.config['max_share_deviation']='0'
        recipe=data.load(self.recipe); recipe['total_tokens']=1; self.recipe.write_text(data.canonical(recipe))
        result,_,output=self.generated()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((output/'receipt.json').exists())

    def test_mutated_tensor_fails_even_with_rewritten_receipt(self):
        result,config,output=self.generated(); self.assertEqual(result.returncode,0,result.stderr)
        output.rename(self.base/'prepared-data'); output=self.base/'prepared-data'
        tokens,_,_=data.rows(output/'tokens.jsonl'); tokens[0]['labels']=[-100]*len(tokens[0]['labels'])
        (output/'tokens.jsonl').write_text(''.join(data.canonical(r)+'\n' for r in tokens))
        receipt=data.load(output/'receipt.json'); receipt['files']['tokens.jsonl']=data.sha(data.read_bytes(output/'tokens.jsonl'))
        (output/'receipt.json').write_text(data.canonical(receipt)+'\n')
        policy=dict(data_preparation=config,artifact_root=str(self.base))
        result=self.backend('import sys,json; from orchestrator.ml_data_gate import verify; verify(json.loads(sys.argv[1]))',data.canonical(policy))
        self.assertNotEqual(result.returncode,0)

    def test_mutation_during_verification_cannot_receive_fresh_attestation(self):
        result,config,output=self.generated(); self.assertEqual(result.returncode,0,result.stderr)
        output.rename(self.base/'prepared-data')
        policy=dict(data_preparation=config,artifact_root=str(self.base))
        code='''import sys,json
from pathlib import Path
from unittest.mock import patch
from orchestrator import ml_data_gate as gate
from scripts import ml_data as data
policy=json.loads(sys.argv[1]); original=gate.generate
def concurrent_mutation(config,out):
    result=original(config,out)
    root=Path(policy['artifact_root'])/'prepared-data'
    (root/'tokens.jsonl').write_text('{}\\n')
    receipt=data.load(root/'receipt.json')
    receipt['files']['tokens.jsonl']=data.sha(data.read_bytes(root/'tokens.jsonl'))
    (root/'receipt.json').write_text(data.canonical(receipt)+'\\n')
    return result
with patch.object(gate,'generate',side_effect=concurrent_mutation):
    gate.verify(policy)
'''
        result=self.backend(code,data.canonical(policy))
        self.assertNotEqual(result.returncode,0)

    def test_modal_text_policy_rejected_before_run(self):
        config=copy.deepcopy(self.execution); config['backend']='modal'
        from orchestrator.ml_pipeline import build
        with self.assertRaises(ValueError):
            build('fixture',ROOT,'codex',str(self.agent),config,self.ai,self.usage,artifact_root=self.base/'artifacts',baseline='0'*40)


if __name__ == '__main__':
    unittest.main()
