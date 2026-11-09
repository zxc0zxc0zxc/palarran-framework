"""Independent pi admission and code-ownership regressions; local fixtures only."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(os.environ.get('PALARRAN_PI_TEST_SOURCE',Path(__file__).resolve().parents[1])).resolve()
PI=ROOT/'packages/core/pi'
NODE=shutil.which('node')


@unittest.skipUnless(NODE,'Node.js is optional')
class PiBoundaryTests(unittest.TestCase):
    def js(self,source,timeout=15):
        result=subprocess.run([NODE,'--input-type=module','-e',"import assert from 'node:assert/strict';\n"+source],
                              cwd=ROOT,capture_output=True,text=True,timeout=timeout)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def git(self,root,*args):
        return subprocess.check_output(['/usr/bin/git','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',
          '-c','commit.gpgsign=false','-c','user.name=Fixture','-c','user.email=fixture@localhost','-C',str(root),*args],
          text=True,stderr=subprocess.DEVNULL).strip()

    def repository(self,root):
        self.git(root,'init','-q');(root/'owned.txt').write_text('owned baseline\n');(root/'unowned.txt').write_text('unowned baseline\n')
        self.git(root,'add','--','owned.txt','unowned.txt');self.git(root,'commit','-qm','Baseline')
        return self.git(root,'rev-parse','HEAD')

    def candidate(self,root,base,rejected):
        self.js(f"""
import * as execution from {json.dumps((PI/'execution.mjs').as_uri())};
assert.equal(typeof execution.validateCandidate,'function','candidate ownership must inspect the complete index/tree');
const check=()=>execution.validateCandidate({json.dumps(str(root))},{json.dumps(base)},['owned.txt']);
assert.{'throws' if rejected else 'doesNotThrow'}(check);
""")

    def test_staged_unowned_new_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base=self.repository(root)
            (root/'owned.txt').write_text('valid owned change\n');(root/'private-new.txt').write_text('unowned staged data\n')
            self.git(root,'add','--','owned.txt','private-new.txt')
            # Staged data is absent from the old ls-files --modified/--others check.
            self.assertNotIn('private-new.txt',self.git(root,'ls-files','--modified','--others','--exclude-standard'))
            self.candidate(root,base,True)

    def test_staged_unowned_deletion_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base=self.repository(root)
            (root/'owned.txt').write_text('valid owned change\n');self.git(root,'add','--','owned.txt');self.git(root,'rm','-q','--','unowned.txt')
            self.assertNotIn('unowned.txt',self.git(root,'ls-files','--modified','--others','--exclude-standard'))
            self.candidate(root,base,True)

    def test_owned_staged_change_is_valid_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();base=self.repository(root)
            (root/'owned.txt').write_text('valid owned change\n');self.git(root,'add','--','owned.txt')
            self.candidate(root,base,False)

    @unittest.skipUnless(os.name=='posix','POSIX process groups')
    def test_parent_exit_does_not_prove_same_group_child_stopped(self):
        self.js(f"""
import * as execution from {json.dumps((PI/'execution.mjs').as_uri())};
import {{spawn}} from 'node:child_process';
assert.equal(typeof execution.groupStopped,'function','root PID disappearance is not process-group stop proof');
const script="const {{spawn}}=require('node:child_process');const c=spawn(process.execPath,['-e','setInterval(()=>{{}},10000)'],{{stdio:'ignore'}});c.once('spawn',()=>process.stdout.write(String(c.pid)+'\\\\n',()=>process.exit(0)));";
const child=spawn(process.execPath,['-e',script],{{detached:true,stdio:['ignore','pipe','ignore']}});
try{{
 await Promise.race([new Promise((resolve,reject)=>{{child.once('exit',code=>code===0?resolve():reject(new Error('fixture exit')));child.once('error',reject)}}),new Promise((_,reject)=>setTimeout(()=>reject(new Error('fixture timeout')),3000))]);
 assert.equal(execution.groupStopped(child.pid),false,'a live descendant still owns the process-group slot');
 process.kill(-child.pid,'SIGKILL');
 for(let i=0;i<60&&!execution.groupStopped(child.pid);i++)await new Promise(r=>setTimeout(r,25));
 assert.equal(execution.groupStopped(child.pid),true);
}}finally{{try{{process.kill(-child.pid,'SIGKILL')}}catch{{}}}}
""",timeout=15)

    def store_prefix(self,root):
        return f"""
import {{Store}} from {json.dumps((PI/'store.mjs').as_uri())};
import {{handle}} from {json.dumps((PI/'control.mjs').as_uri())};
import {{GLOBAL_LIMITS}} from {json.dumps((PI/'validation.mjs').as_uri())};
const store=new Store({json.dumps(str(root/'state.sqlite'))});
function makeRun(n,heavy=1){{const parent={{session_id:'parent-'+n,repository:{json.dumps(str(root))}}},run_id='run-'+n;
 handle(store,'spawn',{{parent,run_id,idempotency_key:'spawn-'+n,tasks:[{{task_id:'one',goal:'Read fixture',acceptance:['Only fixture work'],repository:parent.repository,profile:{{kind:'fake'}}}}],limits:{{heavy}}}});
 handle(store,'approve',{{parent,run_id}});return {{parent,run_id}};}}
"""

    def test_verification_phase_respects_per_run_heavy_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            self.js(self.store_prefix(root)+"""
try{const scope=makeRun('one',1);const first=handle(store,'phase_admit',{...scope,kind:'verification'});
 assert.equal(first.status,'ADMITTED');assert.equal(handle(store,'phase_admit',{...scope,kind:'verification'}).status,'WAIT');
}finally{store.close()}
""")

    def test_unknown_phases_keep_host_slots_until_reconciled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            self.js(self.store_prefix(root)+"""
try{for(let n=0;n<GLOBAL_LIMITS.heavy;n++){const scope=makeRun(String(n),1);const ticket=handle(store,'phase_admit',{...scope,kind:'verification'});
 assert.equal(ticket.status,'ADMITTED');handle(store,'phase_complete',{...scope,ticket:ticket.ticket,outcome:'unknown'});}
 const later=makeRun('later',1);assert.equal(handle(store,'phase_admit',{...later,kind:'verification'}).status,'WAIT');
}finally{store.close()}
""")

    def test_live_supervisor_is_not_replaced_only_because_lease_expired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            self.js(self.store_prefix(root)+f"""
import {{Scheduler}} from {json.dumps((PI/'execution.mjs').as_uri())};
try{{const first=new Scheduler(store),second=new Scheduler(store);assert.equal(first.lease(),true);
 store.tx(()=>store.run('UPDATE supervisor SET lease_until=0 WHERE id=1'));
 assert.equal(second.lease(),false,'a slow live supervisor must not lose ownership solely to TTL expiry');
 assert.equal(store.get('SELECT identity FROM supervisor WHERE id=1').identity,first.identity);
}}finally{{store.close()}}
""")

    def test_unknown_integration_stays_attention_after_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            self.js(self.store_prefix(root)+"""
try{const scope=makeRun('unknown');store.tx(()=>{store.run("UPDATE tasks SET state='SUBMITTED' WHERE run_id=?",scope.run_id);store.run('INSERT INTO integration_operations VALUES(?,?,?,?,?)','op',scope.run_id,'UNKNOWN','{}',Date.now());store.settleRun(scope.run_id);});
 assert.equal(handle(store,'status',scope).status,'ATTENTION');handle(store,'cancel',scope);assert.equal(handle(store,'status',scope).status,'ATTENTION');
}finally{store.close()}
""")

    def test_task_cancel_fences_queued_composition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            self.js(self.store_prefix(root)+"""
try{const scope=makeRun('composition');store.tx(()=>{store.run("UPDATE tasks SET state='SUBMITTED' WHERE run_id=?",scope.run_id);store.run('INSERT INTO integration_operations VALUES(?,?,?,?,?)','op',scope.run_id,'QUEUED',JSON.stringify({items:[{task_id:'one'}]}),Date.now());store.settleRun(scope.run_id);});
 handle(store,'cancel',{...scope,task_id:'one'});assert.equal(store.get('SELECT state FROM tasks WHERE run_id=?',scope.run_id).state,'CANCELLED');assert.equal(store.get('SELECT status FROM integration_operations WHERE id=?','op').status,'CANCELLED');
}finally{store.close()}
""")
