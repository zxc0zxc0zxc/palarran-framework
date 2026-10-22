"""Synthetic CPU-only data checks; no real tokenizer, downloads, models or provider calls."""
import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from scripts import ml_data as data

ROOT = Path(__file__).resolve().parents[1]


def record(name='r1', *, group=None, domain='general', language='en', split='train', content='A complete owned answer.', chat=True):
    value = dict(id=name,group_id=group or name,source_id='synthetic-owned',domain=domain,language=language,
                 license='CC0-1.0',rights_status='approved',rights_approval='fixture-owner-approval')
    if split is not None: value['split']=split
    if chat: value['messages']=[dict(role='user',content='Give the full result.'),dict(role='assistant',content=content)]
    else:value['text']=content
    return value


def config():
    return dict(version=1,seed=73,split_weights=dict(train='0.8',validation='0.1',test='0.1'))


def policy(objective='assistant'):
    return dict(version=1,objective=objective,max_sequence_tokens=100,end_token_ids=[2],
                tokenizer_sha256='a'*64,template_sha256='b'*64,length_bins=[2,8,32])


def tensors(value):
    return dict(id=value['id'],record_sha256=data.digest(value),tokenizer_sha256='a'*64,template_sha256='b'*64,
                complete=True,input_ids=[10,11,12,2,2],labels=[-100,-100,12,2,-100],
                attention_mask=[1,1,1,1,0],assistant_mask=[0,0,1,1,0])


def recipe(cells=None, total=8):
    return dict(version=1,total_tokens=total,seed=73,cells=cells or [dict(domain='general',language='en',weight='1',max_repeats='1')],
                minimum_domain_shares={},minimum_language_shares={})


class DataToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name).resolve();self.serial=0
    def tearDown(self):self.tmp.cleanup()
    def path(self, suffix='data'):
        self.serial+=1;return self.base/(str(self.serial)+'-'+suffix)
    def jsonl(self, values):
        path=self.path('input.jsonl');path.write_text(''.join(data.canonical(v)+'\n' for v in values));return path
    def prepare(self, values, conf=None):
        path=self.jsonl(values);destination=self.path('prepared')
        summary=data.prepare(path,conf or config(),destination)
        return destination,summary
    def audit(self, values=None, change=None, pol=None):
        folder,_=self.prepare(values or [record(),record('r2',content='Different answer.')])
        prepared,_=data.verify_prepared(folder);token_rows=[tensors(v) for v in prepared.values()]
        if change:change(token_rows)
        token_file=self.jsonl(token_rows)
        return data.audit_tokens(folder,token_file,pol or policy()),folder,token_rows

    def test_profile_is_metadata_only_no_tokens_or_raw_content_claim(self):
        sentinel='RAW_PRIVATE_SENTINEL_739'
        path=self.jsonl([record(content=sentinel),record('r2',content=sentinel),{'bad':'schema'}])
        report=data.profile(path)
        self.assertEqual(report['records'],3);self.assertEqual(report['counts']['invalid_schema'],1)
        self.assertEqual(report['exact_duplicate_rows'],1);self.assertIsNone(report['tokens'])
        self.assertNotIn(sentinel,json.dumps(report));self.assertNotIn('r1',json.dumps(report))

    def test_prepare_preserves_long_answers_code_whitespace_and_unicode(self):
        content='  def f():\n\treturn "ёлка e\u0301 عربي"\n'+'Полный ответ. '*5000
        folder,summary=self.prepare([record(content=content)])
        prepared,_=data.verify_prepared(folder)
        self.assertEqual(prepared['r1']['messages'][-1]['content'],content)
        self.assertEqual(summary['accepted_records'],1)
        self.assertEqual(stat.S_IMODE(folder.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((folder/'train.jsonl').stat().st_mode),0o600)
        self.assertFalse(summary['training_ready']);self.assertEqual(summary['audits']['pii'],'NOT_RUN')

    def test_unknown_rights_invalid_rows_and_secret_markers_have_reasons_and_denominator(self):
        unknown=record('r2',content='unknown rights');unknown['rights_status']='unknown'
        unlicensed=record('r3',content='unknown license');unlicensed['license']='unknown'
        secret=record('r4',content='-----BEGIN PRIVATE KEY----- fixture only')
        folder,summary=self.prepare([record(),unknown,unlicensed,secret,{'bad':'schema'}])
        self.assertEqual(summary['input_records'],5);self.assertEqual(summary['accepted_records'],1)
        self.assertEqual(summary['excluded_by_reason'],dict(rights_not_approved=2,secret_marker=1,invalid_schema=1))
        self.assertEqual(sum(s['before'] for s in summary['slices']),5)
        self.assertNotIn('fixture only',json.dumps(data.load(folder/'manifest.json')))
        prepared,_=data.verify_prepared(folder);self.assertEqual(set(prepared),{'r1'})

    def test_empty_train_is_blocked_not_prepared_or_zero_cost_quality(self):
        row=record();row['rights_status']='unknown'
        folder,summary=self.prepare([row]);self.assertEqual(summary['status'],'blocked_no_train_data')
        audit=data.audit_tokens(folder,self.jsonl([]),policy())
        self.assertEqual(audit['status'],'FAIL');self.assertIn('empty_dataset',audit['issues'])

    def test_exact_duplicates_connect_groups_before_assignment_transitively(self):
        values=[record('a1',group='A',split=None,content='shared-one'),record('b1',group='B',split=None,content='shared-one'),
                record('b2',group='B',split=None,content='shared-two'),record('c1',group='C',split=None,content='shared-two'),
                record('c2',group='C',split=None,content='C-unique'),record('a2',group='A',split=None,content='A-unique')]
        folder,summary=self.prepare(values);prepared,_=data.verify_prepared(folder)
        self.assertEqual(summary['accepted_records'],4);self.assertEqual(summary['excluded_by_reason']['exact_duplicate'],2)
        self.assertEqual(len({v['split'] for v in prepared.values()}),1)
        self.assertEqual(len(set(data.load(folder/'manifest.json')['group_components'].values())),1)
        other,_=self.prepare(list(reversed(values)))
        for split in data.SPLITS:self.assertEqual((folder/(split+'.jsonl')).read_bytes(),(other/(split+'.jsonl')).read_bytes())

    def test_fixed_holdout_is_not_moved_or_deduplicated_away(self):
        for values in ([record('a',group='same',split='train'),record('b',group='same',split='test',content='Other')],
                       [record('a',group='A',split='train'),record('b',group='B',split='test')]):
            path=self.jsonl(values);destination=self.path('rejected')
            with self.assertRaises(ValueError):data.prepare(path,config(),destination)
            self.assertFalse(destination.exists())
        folder,_=self.prepare([record(split='test')]);prepared,_=data.verify_prepared(folder)
        self.assertEqual(prepared['r1']['split'],'test')

    def test_grouping_is_preserved_with_different_content_and_nonidentical_unicode_is_not_collapsed(self):
        folder,summary=self.prepare([record('a',group='same',content='é',split=None),record('b',group='same',content='e\u0301',split=None)])
        prepared,_=data.verify_prepared(folder)
        self.assertEqual(summary['accepted_records'],2)
        self.assertEqual(len({v['split'] for v in prepared.values()}),1)

    def test_duplicate_identity_is_fatal_even_if_one_has_unknown_rights(self):
        a=record();b=record(content='Different');b['rights_status']='unknown'
        with self.assertRaises(ValueError):self.prepare([a,b])

    def test_prepared_shard_and_private_ledger_drift_rejected(self):
        for name in ('train.jsonl','decisions.jsonl'):
            folder,_=self.prepare([record()]);(folder/name).write_text('{}\n')
            with self.assertRaises(ValueError):data.verify_prepared(folder)

    def test_chat_roles_and_tool_formats_are_not_flattened_or_guessed(self):
        for messages in ([dict(role='assistant',content='bad first')],
                         [dict(role='user',content='question'),dict(role='tool',content='tool')],
                         [dict(role='user',content='question'),dict(role='assistant',content='')]):
            value=record();value['messages']=messages
            _,summary=self.prepare([value]);self.assertEqual(summary['excluded_by_reason']['invalid_schema'],1)

    def test_successful_tensor_audit_counts_nonpadding_and_supervised_end_even_pad_equals_eos(self):
        audit,_,_=self.audit()
        self.assertEqual(audit['status'],'PASS')
        self.assertEqual(audit['cells'][0]['input_tokens'],8)
        self.assertEqual(audit['cells'][0]['target_tokens'],4)
        self.assertEqual(audit['target_length_histogram'],{'2':2})
        self.assertFalse(audit['tokenization_verified']);self.assertFalse(audit['training_ready'])
        self.assertNotIn('input_ids',json.dumps(audit))

    def test_slice_failures_and_target_lengths_do_not_disappear_in_average(self):
        audit,_,_=self.audit([record(),record('ru',language='ru',content='Русский')],change=lambda rows:rows[1].update(complete=False))
        self.assertEqual(audit['status'],'FAIL')
        self.assertEqual(audit['issues_by_slice'],[dict(split='train',domain='general',language='ru',reason='incomplete_answer',records=1)])
        self.assertEqual(audit['cells'][0]['target_length_histogram'],{'2':1})

    def test_masked_real_end_and_supervised_padding_are_failures(self):
        for mutate in (lambda r:r['labels'].__setitem__(3,-100),lambda r:r['labels'].__setitem__(4,2),
                       lambda r:r['labels'].__setitem__(0,10),lambda r:r['attention_mask'].__setitem__(0,0),
                       lambda r:r['assistant_mask'].__setitem__(2,True)):
            audit,_,_=self.audit(change=lambda rows:mutate(rows[0]))
            self.assertEqual(audit['status'],'FAIL')

    def test_overflow_incomplete_wrong_eos_and_empty_targets_fail_without_truncation(self):
        for mutation in (lambda r:r.update(complete=False),lambda r:r['input_ids'].__setitem__(3,99),
                         lambda r:r.update(labels=[-100]*5,assistant_mask=[0]*5)):
            audit,_,_=self.audit(change=lambda rows:mutation(rows[0]))
            self.assertEqual(audit['status'],'FAIL')
        pol=policy();pol['max_sequence_tokens']=4
        audit,_,_=self.audit(pol=pol);self.assertEqual(audit['status'],'FAIL')
        self.assertEqual(audit['observed_records'],2);self.assertEqual(audit['valid_records'],0)

    def test_training_only_on_eos_is_not_a_complete_supervised_answer(self):
        def only_end(rows):
            rows[0].update(labels=[-100,-100,-100,2,-100],assistant_mask=[0,0,0,1,0])
        audit,_,_=self.audit(change=only_end)
        self.assertEqual(audit['status'],'FAIL')
        self.assertEqual(audit['issues']['no_non_end_targets'],1)

    def test_missing_duplicate_unknown_and_wrong_hash_tensor_rows_are_not_dropped(self):
        mutations=(lambda r:r.pop(),lambda r:r.append(copy.deepcopy(r[0])),lambda r:r[0].update(id='unknown-id'),
                   lambda r:r[0].update(record_sha256='f'*64),lambda r:r[0].update(template_sha256='f'*64))
        for mutation in mutations:
            audit,_,_=self.audit(change=mutation)
            self.assertEqual(audit['status'],'FAIL');self.assertTrue(audit['issues'])

    def test_causal_objective_and_assistant_objective_are_distinct(self):
        folder,_=self.prepare([record(chat=False)])
        records,_=data.verify_prepared(folder);value=tensors(records['r1'])
        value.update(labels=[10,11,12,2,-100],assistant_mask=[0]*5)
        path=self.jsonl([value])
        self.assertEqual(data.audit_tokens(folder,path,policy('causal'))['status'],'PASS')
        self.assertEqual(data.audit_tokens(folder,path,policy())['status'],'FAIL')

    def test_joint_token_plan_is_exact_and_excludes_holdout_inventory(self):
        values=[record(),record('r2',content='second'),record('r3',language='ru',split='test',content='holdout')]
        audit,_,_=self.audit(values)
        planned=data.mix_plan(audit,recipe())
        self.assertEqual(planned['status'],'feasible');self.assertEqual(planned['cells'][0]['available_tokens'],8)
        self.assertFalse(planned['sampler_executed']);self.assertFalse(planned['training_ready'])
        sparse=recipe([dict(domain='general',language='ru',weight='1',max_repeats='100')],4)
        rejected=data.mix_plan(audit,sparse)
        self.assertEqual(rejected['status'],'blocked');self.assertEqual(rejected['cells'][0]['available_tokens'],0)
        self.assertEqual(rejected['cells'][0]['target_tokens'],4)

    def test_no_silent_renormalization_when_joint_support_is_missing(self):
        audit,_,_=self.audit()
        cells=[dict(domain='general',language='en',weight='0.5',max_repeats='1'),dict(domain='specialist',language='ru',weight='0.5',max_repeats='1')]
        result=data.mix_plan(audit,recipe(cells,8))
        self.assertEqual(result['status'],'blocked')
        self.assertEqual([c['target_tokens'] for c in result['cells']],[4,4])
        self.assertEqual(result['cells'][1]['missing_unique_tokens'],4)

    def test_repeat_capacity_and_unique_tokens_have_correct_units(self):
        audit,_,_=self.audit()
        cells=[dict(domain='general',language='en',weight='1',max_repeats='2')]
        result=data.mix_plan(audit,recipe(cells,20))
        self.assertEqual(result['status'],'blocked')
        self.assertEqual(result['cells'][0]['uncovered_exposure_tokens'],4)
        self.assertEqual(result['cells'][0]['missing_unique_tokens'],2)
        self.assertEqual(result['cells'][0]['effective_passes'],'2.5')

    def test_largest_remainder_rounding_and_language_domain_floors(self):
        audit,_,_=self.audit([record(),record('ru',language='ru',content='Русский')])
        cells=[dict(domain='general',language='en',weight='0.5',max_repeats='1'),dict(domain='general',language='ru',weight='0.5',max_repeats='1')]
        result=data.mix_plan(audit,recipe(cells,3))
        self.assertEqual(sum(c['target_tokens'] for c in result['cells']),3)
        req=recipe(cells,3);req['minimum_language_shares']={'ru':'0.5'}
        self.assertIn('language_floor',data.mix_plan(audit,req)['blockers'])
        req=recipe(cells,3);req['minimum_domain_shares']={'specialist':'0.1'}
        self.assertIn('domain_floor',data.mix_plan(audit,req)['blockers'])

    def test_failing_or_mutated_audit_does_not_authorize_mixture(self):
        audit,_,_=self.audit()
        audit['cells'][0]['input_tokens']=999
        with self.assertRaises(ValueError):data.mix_plan(audit,recipe())
        audit,_,_=self.audit(change=lambda rows:rows.pop())
        with self.assertRaises(ValueError):data.mix_plan(audit,recipe())

    def test_invalid_weights_caps_duplicates_and_boolean_budgets_rejected(self):
        audit,_,_=self.audit()
        for mutate in (lambda r:r.update(total_tokens=True),lambda r:r['cells'][0].update(weight=1),
                       lambda r:r['cells'][0].update(weight='0.9'),lambda r:r['cells'][0].update(max_repeats='0'),
                       lambda r:r['cells'].append(copy.deepcopy(r['cells'][0]))):
            r=recipe();mutate(r)
            with self.assertRaises(ValueError):data.mix_plan(audit,r)

    def test_no_overwrite_no_stdout_payload_and_no_following_symlink_fifo(self):
        source=self.jsonl([record(content='RAW_PRIVATE_SENTINEL_739')]);out=self.path('profile.json')
        argv=[sys.executable,str(ROOT/'scripts/ml_data.py'),'profile','--input',str(source),'--output',str(out)]
        result=subprocess.run(argv,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertNotIn('RAW_PRIVATE_SENTINEL',result.stdout+result.stderr)
        original=out.read_bytes();result=subprocess.run(argv,capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(out.read_bytes(),original)
        link=self.path('alias');link.symlink_to(source)
        with self.assertRaises(ValueError):data.profile(link)
        fifo=self.path('fifo');os.mkfifo(fifo)
        with self.assertRaises(ValueError):data.profile(fifo)
        destination=self.path('kept');destination.mkdir();(destination/'keep').write_text('keep')
        with self.assertRaises(ValueError):data.prepare(source,config(),destination)
        self.assertEqual((destination/'keep').read_text(),'keep')

    def test_cli_prepare_audit_mix_end_to_end_and_failed_audit_exit(self):
        source=self.jsonl([record(),record('r2',content='second')]);folder=self.path('cli-prepared')
        cfg=self.path('config.json');cfg.write_text(json.dumps(config()))
        def cli(command,*args):
            return subprocess.run([sys.executable,str(ROOT/'scripts/ml_data.py'),command]+list(args),capture_output=True,text=True)
        prepared=cli('prepare','--input',str(source),'--config',str(cfg),'--output',str(folder))
        self.assertEqual(prepared.returncode,0,prepared.stderr)
        records,_=data.verify_prepared(folder);token_file=self.jsonl([tensors(v) for v in records.values()])
        pol=self.path('policy.json');pol.write_text(json.dumps(policy()));out=self.path('audit.json')
        audited=cli('audit-tokens','--prepared',str(folder),'--tokens',str(token_file),'--policy',str(pol),'--output',str(out))
        self.assertEqual(audited.returncode,0,audited.stderr)
        rec=self.path('recipe.json');rec.write_text(json.dumps(recipe()));plan=self.path('mix.json')
        mixed=cli('mix-plan','--audit',str(out),'--recipe',str(rec),'--output',str(plan))
        self.assertEqual(mixed.returncode,0,mixed.stderr);self.assertEqual(data.load(plan)['status'],'feasible')
        bad_rows=[tensors(v) for v in records.values()];bad_rows[0]['complete']=False
        token_file=self.jsonl(bad_rows);failed=self.path('failed-audit.json')
        result=cli('audit-tokens','--prepared',str(folder),'--tokens',str(token_file),'--policy',str(pol),'--output',str(failed))
        self.assertEqual(result.returncode,2);self.assertEqual(data.load(failed)['status'],'FAIL')

    def test_malformed_nonfinite_duplicate_keys_and_oversized_lines_rejected(self):
        for content in ('{"a":1,"a":2}\n','{"a":NaN}\n','\n'):
            path=self.path('bad');path.write_text(content)
            with self.assertRaises(ValueError):data.profile(path)
        path=self.path('large');path.write_bytes(b'x'*(data.MAX_LINE+1))
        with self.assertRaises(ValueError):data.profile(path)


if __name__=='__main__':unittest.main()
