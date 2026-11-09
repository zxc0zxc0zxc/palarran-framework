"""Offline native pi client contracts; no model/provider request is made."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / 'packages/core/pi/extension'
NODE = shutil.which('node')


@unittest.skipUnless(NODE, 'Node.js is optional')
class PiExtensionTests(unittest.TestCase):
    def js(self, body, timeout=12):
        source = "import assert from 'node:assert/strict';\n" + body
        result = subprocess.run([NODE, '--input-type=module', '-e', source], cwd=ROOT,
                                capture_output=True, text=True, timeout=timeout)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def prefix(self):
        return f"""
import {{ registerPalarran }} from {json.dumps((EXT/'core.mjs').as_uri())};
const tools=new Map(),commands=new Map(),handlers=new Map(),entries=[],timers=[];
let modelMessages=0;
const pi={{registerTool:x=>tools.set(x.name,x),registerCommand:(n,x)=>commands.set(n,x),
 on:(n,f)=>{{handlers.set(n,f);return ()=>{{}}}},appendEntry:(type,data)=>entries.push({{type:'custom',customType:type,data}}),
 sendMessage:()=>modelMessages++,sendUserMessage:()=>modelMessages++}};
const schemas=Object.fromEntries(['spawn','status','wait','result','send','follow_up','cancel'].map(x=>[x,{{type:'object'}}]));
function context(id='parent-a',stored=[]){{const widgets=[];return {{cwd:process.cwd(),mode:'tui',hasUI:true,
 sessionManager:{{getSessionId:()=>id,getEntries:()=>stored}},ui:{{setWidget:(k,x)=>widgets.push(x),notify:()=>{{}}}},widgets}}}}
const dependencies={{schemas,resolveRepository:async p=>p,setInterval:f=>{{timers.push(f);return {{unref(){{}}}}}},clearInterval:()=>{{}}}};
"""

    def test_registers_exactly_seven_tools_without_starting_work(self):
        self.js(self.prefix()+"""
let calls=0;registerPalarran(pi,{...dependencies,rpc:async()=>{calls++;return {status:'OK'}}});
assert.deepEqual([...tools.keys()].sort(),['swarm_cancel','swarm_follow_up','swarm_result','swarm_send','swarm_spawn','swarm_status','swarm_wait']);
assert.ok(commands.has('swarm'));assert.equal(calls,0);assert.equal(timers.length,0);assert.equal(modelMessages,0);
""")

    def test_every_tool_binds_current_parent_and_never_takes_model_authority(self):
        self.js(self.prefix()+"""
const calls=[];registerPalarran(pi,{...dependencies,rpc:async(command,payload)=>{calls.push({command,payload});return {status:'QUEUED',run_id:'run-a'}}});
const ctx=context();await handlers.get('session_start')({},ctx);
await tools.get('swarm_spawn').execute('t',{idempotency_key:'key-a',tasks:[],parent:{session_id:'forged',repository:'/forged'},command:'approve'},undefined,undefined,ctx);
assert.equal(calls[0].command,'spawn');assert.deepEqual(calls[0].payload.parent,{session_id:'parent-a',repository:process.cwd()});
assert.equal(calls[0].payload.command,undefined);assert.equal(modelMessages,0);
""")

    def test_old_session_poll_cannot_update_the_new_parent(self):
        self.js(self.prefix()+"""
let finish;const calls=[];
registerPalarran(pi,{...dependencies,rpc:async(command,payload,options)=>{calls.push({command,payload,options});
 if(command==='spawn')return {status:'QUEUED',run_id:'run-a'};
 if(command==='status')return new Promise(resolve=>{finish=resolve});return {status:'EVENTS',cursor:0,events:[]}}});
const a=context();await handlers.get('session_start')({},a);
await tools.get('swarm_spawn').execute('t',{idempotency_key:'key-a',tasks:[]},undefined,undefined,a);
const pending=timers[0]();await new Promise(r=>setImmediate(r));
const b=context('parent-b');await handlers.get('session_start')({},b);
finish({status:'RUNNING',run_id:'run-a',counts:{running:9,total:9}});await pending;
assert.equal(b.widgets.filter(Boolean).length,0);assert.equal(modelMessages,0);
assert.ok(calls.find(c=>c.command==='status').options.signal.aborted);
""")

    def test_persisted_selection_is_bound_to_parent_and_repository(self):
        self.js(self.prefix()+"""
const calls=[];registerPalarran(pi,{...dependencies,rpc:async(command,payload)=>{calls.push({command,payload});return {status:'RUNNING',run_id:payload.run_id,counts:{total:1}}}});
const records=[{type:'custom',customType:'palarran-swarm-view',data:{version:1,run_id:'foreign',session_id:'parent-a',repository:process.cwd()}}];
await handlers.get('session_start')({},context('parent-b',records));
assert.equal(timers.length,0);assert.equal(calls.length,0);
""")

    def test_human_start_is_separate_from_model_tools(self):
        self.js(self.prefix()+"""
const calls=[];registerPalarran(pi,{...dependencies,rpc:async(command,payload)=>{calls.push({command,payload});return {status:'RUNNING',run_id:'run-a',counts:{total:1},budget:{tokens_used:0}}}});
const ctx=context();await handlers.get('session_start')({},ctx);
await commands.get('swarm').handler('start run-a',ctx);
assert.ok(calls.some(x=>x.command==='start'));assert.ok(!tools.has('swarm_start'));assert.ok(!tools.has('swarm_approve'));
assert.equal(modelMessages,0);
""")

    def test_shutdown_cleans_ui_polling_without_cancelling_durable_work(self):
        self.js(self.prefix()+"""
let clears=0;const calls=[];registerPalarran(pi,{...dependencies,clearInterval:()=>clears++,rpc:async(command,payload)=>{calls.push(command);return {status:'QUEUED',run_id:'run-a'}}});
const ctx=context();await handlers.get('session_start')({},ctx);
await tools.get('swarm_spawn').execute('t',{idempotency_key:'key-a',tasks:[]},undefined,undefined,ctx);
await handlers.get('session_shutdown')({},ctx);await handlers.get('session_shutdown')({},ctx);
assert.equal(clears,1);assert.ok(!calls.includes('cancel'));assert.equal(ctx.widgets.at(-1),undefined);
""")

    def test_result_is_bounded_and_widget_removes_terminal_controls(self):
        self.js(self.prefix()+"""
const huge='x'.repeat(100000);registerPalarran(pi,{...dependencies,rpc:async(command,payload)=>command==='result'?{status:'SUCCEEDED',summary:huge,artifacts:['result.json']}:{status:'RUNNING',run_id:'run-a',counts:{running:1,total:1},tasks:[{task_id:'a',state:'running',goal:'bad\\u001b[31m\\nLABEL'}]}});
const ctx=context();await handlers.get('session_start')({},ctx);
const result=await tools.get('swarm_result').execute('t',{run_id:'run-a',task_id:'a'},undefined,undefined,ctx);
assert.ok(Buffer.byteLength(result.content[0].text)<20000);assert.equal(result.details.truncated,true);
await commands.get('swarm').handler('use run-a',ctx);await timers[0]();
const text=ctx.widgets.filter(Boolean).flat().join('');assert.ok(!text.includes('\\u001b'));assert.equal(modelMessages,0);
""")

    def test_rpc_protocol_scrubs_environment_and_never_echoes_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs'
            script.write_text("let s='';for await(const x of process.stdin)s+=x;const r=JSON.parse(s);console.error('PRIVATE_OPERATOR_VALUE');console.log(JSON.stringify({status:'OK',command:r.command,secretPresent:!!process.env.PRIVATE_TEST_SECRET}));")
            self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
process.env.PRIVATE_TEST_SECRET='PRIVATE_OPERATOR_VALUE';
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))}}});
const result=await rpc('status',{{parent:{{session_id:'a',repository:process.cwd()}}}});
assert.equal(result.status,'OK');assert.equal(result.command,'status');assert.equal(result.secretPresent,false);
""")

    def test_default_rpc_does_not_inherit_provider_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs'
            script.write_text("console.log(JSON.stringify({status:'OK',openai:!!process.env.OPENAI_API_KEY,anthropic:!!process.env.ANTHROPIC_API_KEY}));")
            self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
process.env.OPENAI_API_KEY='PRIVATE_OPERATOR_VALUE';process.env.ANTHROPIC_API_KEY='PRIVATE_OPERATOR_VALUE';delete process.env.PALARRAN_PI_CREDENTIAL_ENV;
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))}}});
const r=await rpc('status',{{}});assert.equal(r.openai,false);assert.equal(r.anthropic,false);
""")

    def test_reviewed_credential_selection_is_child_environment_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs'
            script.write_text("let s='';for await(const x of process.stdin)s+=x;console.log(JSON.stringify({status:'OK',openai:!!process.env.OPENAI_API_KEY,anthropic:!!process.env.ANTHROPIC_API_KEY,other:!!process.env.PRIVATE_TEST_SECRET,requestHasKey:s.includes('PRIVATE_OPERATOR_VALUE')}));")
            self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
process.env.OPENAI_API_KEY='PRIVATE_OPERATOR_VALUE';process.env.ANTHROPIC_API_KEY='PRIVATE_OPERATOR_VALUE';process.env.PRIVATE_TEST_SECRET='PRIVATE_OPERATOR_VALUE';
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))},credentialEnv:['OPENAI_API_KEY']}});
const r=await rpc('status',{{}});assert.equal(r.openai,true);assert.equal(r.anthropic,false);assert.equal(r.other,false);assert.equal(r.requestHasKey,false);
process.env.PALARRAN_PI_CREDENTIAL_ENV='ANTHROPIC_API_KEY';
const fromEnv=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))}});
const e=await fromEnv('status',{{}});assert.equal(e.openai,false);assert.equal(e.anthropic,true);assert.equal(e.requestHasKey,false);
""")

    def test_arbitrary_credential_names_fail_before_starting_a_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs';marker=root/'calls'
            script.write_text(f"import fs from 'node:fs';fs.writeFileSync({json.dumps(str(marker))},'launched');console.log(JSON.stringify({{status:'OK'}}));")
            self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))},credentialEnv:['PRIVATE_TEST_SECRET']}});
const r=await rpc('spawn',{{}});assert.equal(r.status,'REJECTED');assert.equal(r.code,'invalid_credential_selection');assert.ok(!JSON.stringify(r).includes('PRIVATE_TEST_SECRET'));
""")
            self.assertFalse(marker.exists())

    def test_rpc_timeout_reports_unknown_mutation_without_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs';marker=root/'calls'
            script.write_text(f"import fs from 'node:fs';fs.appendFileSync({json.dumps(str(marker))},'1');console.error('PRIVATE_OPERATOR_VALUE');setTimeout(()=>{{}},60000);")
            output=self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))},timeoutMs:80}});
const result=await rpc('spawn',{{idempotency_key:'same'}});
assert.equal(result.status,'UNKNOWN');assert.equal(result.code,'supervisor_timeout');console.log(JSON.stringify(result));
""")
            self.assertNotIn('PRIVATE_OPERATOR_VALUE',output)
            self.assertEqual(marker.read_text(),'1')

    def test_rpc_oversized_output_is_safe_and_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);script=root/'supervisor.mjs';script.write_text("process.stdout.write('PRIVATE_OPERATOR_VALUE'.repeat(30000));")
            self.js(f"""
import {{ createRpcClient }} from {json.dumps((EXT/'rpc.mjs').as_uri())};
const rpc=createRpcClient({{supervisorPath:{json.dumps(str(script))},statePath:{json.dumps(str(root/'state.sqlite'))},outputLimit:1024}});
const value=await rpc('status',{{}});assert.equal(value.code,'supervisor_output_limit');assert.ok(!JSON.stringify(value).includes('PRIVATE_OPERATOR_VALUE'));
""")

    def test_installed_pi_loads_extension_without_a_session_or_model_call(self):
        base=Path.home()/'.pi/agent/install'
        try:
            version=(base/'current-version').read_text().strip()
            sdk=base/'releases'/version/'node_modules/@earendil-works/pi-coding-agent'
            loader=sdk/'dist/core/extensions/loader.js'
            if not loader.is_file():self.skipTest('installed pi SDK unavailable')
        except OSError:self.skipTest('installed pi SDK unavailable')
        self.js(f"""
const {{loadExtensions}}=await import({json.dumps(loader.as_uri())});
const result=await loadExtensions([{json.dumps(str(EXT/'index.ts'))}],process.cwd());
assert.deepEqual(result.errors,[]);assert.equal(result.extensions.length,1);
assert.equal(result.extensions[0].tools.size,7);assert.ok(result.extensions[0].commands.has('swarm'));
""",timeout=25)
