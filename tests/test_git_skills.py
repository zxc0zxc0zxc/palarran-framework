"""Offline Git procedure simulations, not evidence of LLM skill reliability or live MR publication."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
GIT=shutil.which('git')


@unittest.skipUnless(GIT,'Git unavailable: offline procedure checks NOT_RUN')
class GitProcedureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.area=Path(self.tmp.name);self.repo=self.area/'repo';self.repo.mkdir()
        # Isolate fixture identity/configuration; never touch the user's signing, hooks or identity.
        self.env={key:value for key,value in os.environ.items() if not key.startswith('GIT_')}
        self.env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',GIT_MERGE_AUTOEDIT='no')
        self.git('init','-b','main');self.git('config','user.name','Fixture Author');self.git('config','user.email','fixture@example.invalid')
        for name,body in [('owned.txt','base\n'),('foreign.txt','base\n'),('shared.txt','first=base\nsecond=base\n')]:self.write(name,body)
        self.git('add','--','owned.txt','foreign.txt','shared.txt');self.commit('Initialize synthetic subject')
    def tearDown(self):self.tmp.cleanup()
    def git(self,*args,cwd=None,check=True,input=None,env=None):
        result=subprocess.run([GIT,'--no-pager','--literal-pathspecs',*args],cwd=cwd or self.repo,
            env=dict(self.env,**(env or {})),input=input,text=True,capture_output=True,timeout=15)
        if check and result.returncode:raise AssertionError(result.stderr or result.stdout)
        return result.stdout if check else result
    def write(self,name,body):
        path=self.repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body);return path
    def commit(self,subject,cwd=None):
        message=self.area/'message.txt';message.write_text(subject+'\n\nFeature: TEST-1\nADR: git/fixture/0001\n')
        return self.git('commit','-F',str(message),cwd=cwd)
    def foreign(self):
        return (self.git('diff','--cached','--binary','--','foreign.txt'),self.git('diff','--binary','--','foreign.txt'),
                hashlib.sha256((self.repo/'untracked.txt').read_bytes()).hexdigest())

    def test_whole_owned_path_commit_preserves_other_staged_unstaged_and_untracked_work(self):
        base=self.git('rev-parse','HEAD').strip()
        self.write('foreign.txt','foreign staged\n');self.git('add','--','foreign.txt');self.write('foreign.txt','foreign staged\nforeign unstaged\n')
        self.write('untracked.txt','someone else\n');protected=self.foreign()
        self.write('owned.txt','owned coherent stage\n')
        message=self.area/'owned-message';message.write_text('Preserve the owned stage\n\nRequired fixture check passed.\n\nFeature: TEST-1\nADR: git/fixture/0001\n')
        self.git('commit','--only','-F',str(message),'--','owned.txt')
        self.assertEqual(self.foreign(),protected)
        self.assertEqual(self.git('show','HEAD:foreign.txt'),'base\n')
        self.assertEqual(self.git('show','HEAD:owned.txt'),'owned coherent stage\n')
        self.assertEqual(self.git('diff-tree','--no-commit-id','--name-only','-r','HEAD').strip(),'owned.txt')
        self.assertEqual(self.git('rev-parse','HEAD^').strip(),base)
        trailers=self.git('interpret-trailers','--parse',input=self.git('log','-1','--format=%B'))
        self.assertIn('Feature: TEST-1',trailers);self.assertIn('ADR: git/fixture/0001',trailers)
        repeat=self.git('commit','--only','-F',str(message),'--','owned.txt',check=False)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual(self.foreign(),protected)

    def test_same_file_negative_control_only_would_include_unstaged_foreign_hunk(self):
        self.write('shared.txt','first=owned\nsecond=base\n');self.git('add','--','shared.txt')
        self.write('shared.txt','first=owned\nsecond=foreign\n')
        self.assertEqual(self.git('show',':shared.txt'),'first=owned\nsecond=base\n')
        self.assertIn('+second=foreign',self.git('diff','--','shared.txt'))
        # Deliberately demonstrate the unsafe shortcut only in this disposable negative control.
        message=self.area/'negative';message.write_text('Demonstrate whole-path semantics\n')
        self.git('commit','--only','-F',str(message),'--','shared.txt')
        self.assertIn('second=foreign',self.git('show','HEAD:shared.txt'))
        self.assertNotEqual(self.git('show','HEAD:shared.txt'),'first=owned\nsecond=base\n')

    def test_required_hook_rejection_does_not_create_commit_or_drop_foreign_dirt(self):
        self.write('foreign.txt','foreign staged\n');self.git('add','--','foreign.txt');self.write('untracked.txt','private fixture\n')
        self.write('owned.txt','owned\n');before=self.git('rev-parse','HEAD');protected=self.foreign()
        hook=self.repo/'.git/hooks/pre-commit';hook.write_text('#!/bin/sh\nexit 1\n');hook.chmod(0o700)
        result=self.git('commit','--only','-m','Rejected by required fixture hook','--','owned.txt',check=False)
        self.assertNotEqual(result.returncode,0);self.assertEqual(self.git('rev-parse','HEAD'),before)
        self.assertEqual(self.foreign(),protected);self.assertTrue(hook.exists())

    def test_renamed_file_history_distinguishes_recorded_changes_and_missing_rationale(self):
        self.write('original name.txt','stable record\n');self.git('add','--','original name.txt')
        self.commit('Keep stable record\n\nThe integration contract requires a persistent identifier.')
        initial=self.git('rev-parse','HEAD').strip()
        self.git('mv','--','original name.txt','renamed name.txt');self.commit('Rename record file')
        self.write('renamed name.txt','stable record\nchanged field\n');self.git('add','--','renamed name.txt')
        self.git('commit','-m','fix',env={'GIT_AUTHOR_NAME':'Original Author','GIT_AUTHOR_EMAIL':'author@example.invalid',
            'GIT_COMMITTER_NAME':'Integrator','GIT_COMMITTER_EMAIL':'integrator@example.invalid'})
        latest=self.git('rev-parse','HEAD').strip()
        history=self.git('log','--follow','--max-count=20','--format=%H','--','renamed name.txt').splitlines()
        self.assertIn(initial,history);self.assertEqual(history[0],latest)
        identity=self.git('show','-s','--format=%an%n%cn%n%aI%n%cI',latest).splitlines()
        self.assertEqual(identity[:2],['Original Author','Integrator']);self.assertEqual(len(identity),4)
        message=self.git('show','-s','--format=%B',latest)
        self.assertEqual(message.strip(),'fix');self.assertEqual(self.git('interpret-trailers','--parse',input=message),'')
        # No recorded reason/decision exists for this latest commit. A report must retain unknown.
        evidence={'commit':latest,'observed_change':'Added changed field','stated_rationale':None}
        explanation='rationale unknown' if evidence['stated_rationale'] is None else evidence['stated_rationale']
        self.assertEqual(explanation,'rationale unknown')
        self.assertIn('persistent identifier',self.git('show','-s','--format=%B',initial))

    def test_owned_integration_worktree_preserves_foreign_dirt_and_both_semantic_requirements(self):
        body='def allowed(owner, current, enabled, tenant, actor_tenant):\n    return owner == current\n'
        self.write('policy.py',body);self.git('add','--','policy.py');self.commit('Create synthetic policy')
        base=self.git('rev-parse','HEAD').strip();self.git('switch','-c','target')
        self.write('policy.py',body.replace('owner == current','owner == current and tenant == actor_tenant'))
        self.git('add','--','policy.py');self.commit('Require tenant membership');target=self.git('rev-parse','HEAD').strip()
        self.git('switch','-c','feature',base)
        self.write('policy.py',body.replace('owner == current','owner == current and enabled'))
        self.git('add','--','policy.py');self.commit('Require enabled principal');source=self.git('rev-parse','HEAD').strip()
        self.write('foreign.txt','foreign staged\n');self.git('add','--','foreign.txt');self.write('foreign.txt','foreign staged\nforeign unstaged\n');self.write('untracked.txt','untouched\n')
        protected=self.foreign();integration=self.area/'integration'
        self.git('worktree','add','-b','codex/test-integration',str(integration),source)
        result=self.git('merge','--no-ff','--no-commit',target,cwd=integration,check=False)
        self.assertNotEqual(result.returncode,0)
        stages=self.git('ls-files','--unmerged',cwd=integration)
        for stage in (' 1\t',' 2\t',' 3\t'):self.assertIn(stage,stages)
        self.assertEqual(self.git('merge-base',source,target,cwd=integration).strip(),base)
        self.assertIn('enabled',self.git('show',':2:policy.py',cwd=integration))
        self.assertIn('tenant == actor_tenant',self.git('show',':3:policy.py',cwd=integration))
        resolved=body.replace('owner == current','owner == current and enabled and tenant == actor_tenant')
        (integration/'policy.py').write_text(resolved);self.git('add','--','policy.py',cwd=integration)
        self.assertEqual(self.git('ls-files','--unmerged',cwd=integration),'')
        self.assertNotIn('<<<<<<<',resolved)
        namespace={};exec(compile(resolved,'synthetic-policy','exec'),namespace)
        allowed=namespace['allowed']
        self.assertTrue(allowed('a','a',True,'tenant1','tenant1'))
        self.assertFalse(allowed('a','a',False,'tenant1','tenant1'))
        self.assertFalse(allowed('a','a',True,'tenant1','tenant2'))
        self.assertFalse(allowed('b','a',True,'tenant1','tenant1'))
        # A marker-free base-only resolution would silently lose both requirements.
        bad={};exec(compile(body,'negative-control','exec'),bad)
        self.assertTrue(bad['allowed']('a','a',False,'tenant1','tenant2'))
        self.commit('Integrate both policy requirements',cwd=integration)
        self.assertEqual(self.git('show','-s','--format=%P',cwd=integration).strip().split(),[source,target])
        self.assertEqual(self.foreign(),protected);self.assertEqual(self.git('rev-parse','HEAD').strip(),source)

    def test_mr_template_retains_unavailable_readiness_gates_and_names_only(self):
        template=(ROOT/'packages/code/git/templates/mr.md').read_text()
        for heading in ('Environment','Testing','Production readiness'):self.assertIn('## '+heading,template)
        self.git('switch','-c','codex/review-fixture')
        self.write('.env.example','API_TOKEN=\n');self.git('add','--','.env.example');self.commit('Declare fixture credential name')
        head=self.git('rev-parse','HEAD').strip();base=self.git('rev-parse','main').strip()
        self.assertEqual(self.git('diff','--name-only','main...HEAD').strip(),'.env.example')
        env_names=re.findall(r'^([A-Z_]+)=',self.git('show','HEAD:.env.example'),re.M)
        self.assertEqual(env_names,['API_TOKEN'])
        replacements=iter(['Declare the credential input used by this synthetic integration.', 'TEST-1','git/fixture/0001',head,'main '+base+' (local fixture only)',
            'API_TOKEN: required secret in the proposed production environment; provision through the approved secret store. No values included.',
            'Prerequisite: synthetic credential fixture. Scenario: missing credential is rejected. Local fixture inspection PASS; application execution NOT_RUN; remote CI NOT_RUN.',
            'not ready: credential provisioning and actual application/CI/rollout/rollback checks remain NOT_RUN. No production or SLA evidence.'])
        draft=re.sub(r'\{[^{}\n]+\}',lambda _:next(replacements),template)
        self.assertIn('## Environment',draft);self.assertIn('API_TOKEN',draft);self.assertIn('remote CI NOT_RUN',draft)
        self.assertIn('not ready:',draft);self.assertIn(head,draft);self.assertNotIn('API_TOKEN=',draft)
        self.assertNotIn('https://github.com/',draft);self.assertNotIn('{',draft)

    def test_history_treats_pathspec_characters_as_literal_filename(self):
        self.write('a[1].txt','literal bracket name\n');self.git('add','--','a[1].txt');self.commit('Create literal-path fixture')
        literal=self.git('rev-parse','HEAD').strip()
        self.write('a1.txt','different file\n');self.git('add','--','a1.txt');self.commit('Create wildcard lookalike')
        other=self.git('rev-parse','HEAD').strip()
        history=self.git('log','--follow','--max-count=20','--format=%H','--','a[1].txt').splitlines()
        self.assertEqual(history,[literal]);self.assertNotIn(other,history)


if __name__=='__main__':unittest.main()
