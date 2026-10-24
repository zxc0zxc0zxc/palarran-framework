"""Offline onboarding, provenance, conflict and protocol tests."""
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import project_setup as setup
import memory_global_setup as global_setup


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.source=self.root/'source';self.source.mkdir()
        subprocess.run(['git','init','-q',str(self.source)],check=True)
        files={
            'scripts/memory_ops.py':'''import json,sys
for line in sys.stdin:
 m=json.loads(line)
 if 'id' not in m:continue
 if m['method']=='initialize':r={'protocolVersion':'2025-11-25'}
 elif m['method']=='tools/list':r={'tools':[{'name':'knowledge.'+n} for n in ('search','get','neighbors','artifact','propose','feedback')]}
 else:
  v={'ok':True,'data':{'items':[]},'error':None}
  r={'isError':False,'structuredContent':v,'content':[{'type':'text','text':json.dumps(v)}]}
 print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':r}),flush=True)
''',
            'skills/README.md':'# Synthetic skill catalog\n',
            'skills/demo/SKILL.md':'---\nname: demo\ndescription: Synthetic fixture\n---\n',
            'docs/skills/decision-memory.md':'# Fixture shared guide\n',
            '.palarran/private.md':'Do not distribute project journal',
            '.env':'private-fixture-do-not-distribute',
        }
        for name,body in files.items():
            p=self.source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
        subprocess.run(['git','-C',str(self.source),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.source),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        self.target=self.root/'target';self.target.mkdir()

    def tearDown(self):self.temp.cleanup()

    def test_plan_is_readonly_and_source_is_committed_public(self):
        (self.source/'skills/demo/SKILL.md').write_text('DIRTY UNREVIEWED')
        (self.source/'scripts/untracked.py').write_text('NEVER DISTRIBUTE')
        result=setup.install(self.source,self.target,'both',True)
        self.assertEqual(result['status'],'PLANNED');self.assertEqual(list(self.target.iterdir()),[])
        setup.install(self.source,self.target,'both')
        lib=self.target/'.ai-tools/library'
        self.assertNotIn('DIRTY', (lib/'skills/demo/SKILL.md').read_text())
        for name in ('.env','.palarran/private.md','scripts/untracked.py'):
            self.assertFalse((lib/name).exists())
        self.assertEqual(setup.library(lib)[0],result['revision'])

    def test_install_repeat_preserves_instructions_configs_and_relative_links(self):
        (self.target/'AGENTS.md').write_text('# Existing rules\nPreserve this.\n')
        (self.target/'.mcp.json').write_text(json.dumps({'mcpServers':{'other':{'command':'existing'}}}))
        first=setup.install(self.source,self.target,'both')
        before={str(p.relative_to(self.target)):p.read_bytes() for p in self.target.rglob('*') if p.is_file() and not p.is_symlink()}
        second=setup.install(self.source,self.target,'both')
        self.assertEqual(first,second)
        after={str(p.relative_to(self.target)):p.read_bytes() for p in self.target.rglob('*') if p.is_file() and not p.is_symlink()}
        self.assertEqual(before,after)
        for parent in ('.agents','.claude'):
            link=self.target/parent/'skills/demo';self.assertTrue(link.is_symlink());self.assertTrue((link/'SKILL.md').is_file())
            self.assertFalse(__import__('os').readlink(link).startswith('/'))
        self.assertIn('Preserve this.',(self.target/'AGENTS.md').read_text())
        config=json.loads((self.target/'.mcp.json').read_text())
        self.assertEqual(config['mcpServers']['other'],{'command':'existing'})
        self.assertNotIn('env',config['mcpServers']['engineering-memory'])
        self.assertEqual(config['mcpServers']['engineering-memory']['args'][-1],'--global')
        self.assertTrue(list((self.target/'.ai-tools/backups').iterdir()))

    def test_collision_has_no_partial_writes(self):
        p=self.target/'.agents/skills/demo';p.mkdir(parents=True);(p/'SKILL.md').write_text('USER CONTENT')
        with self.assertRaises(ValueError):setup.install(self.source,self.target,'codex')
        self.assertFalse((self.target/'.ai-tools').exists())
        self.assertEqual((p/'SKILL.md').read_text(),'USER CONTENT')
        self.assertFalse((self.target/'AGENTS.md').exists())

    def test_unsafe_parent_and_changed_bundle_block(self):
        outside=self.root/'outside';outside.mkdir();(self.target/'.agents').symlink_to(outside)
        with self.assertRaises(ValueError):setup.install(self.source,self.target,'codex')
        self.assertEqual(list(outside.iterdir()),[])
        (self.target/'.agents').unlink()
        setup.install(self.source,self.target,'codex')
        (self.target/'.ai-tools/library/skills/demo/SKILL.md').write_text('Changed owned resource')
        with self.assertRaises(ValueError):setup.install(self.source,self.target,'codex')

    def test_managed_section_conflict_preserves_user_edit(self):
        setup.install(self.source,self.target,'codex')
        p=self.target/'AGENTS.md';p.write_text(p.read_text().replace('Skill docs live','User edited docs live'))
        with self.assertRaises(ValueError):setup.install(self.source,self.target,'codex')
        self.assertIn('User edited',p.read_text())

    def test_existing_mcp_collision_and_unsafe_snapshot_are_rejected(self):
        p=self.target/'.mcp.json'
        p.write_text(json.dumps({'mcpServers':{'engineering-memory':{'command':'user-owned'}}}))
        with self.assertRaises(ValueError):setup.install(self.source,self.target,'both')
        self.assertFalse((self.target/'.ai-tools').exists())
        self.assertEqual(json.loads(p.read_text())['mcpServers']['engineering-memory']['command'],'user-owned')
        out=setup.export(self.source,self.root/'snapshot')
        marker=out/'.ai-tools-library.json';value=json.loads(marker.read_text());value['files']['../../private']='0'*64;marker.write_text(json.dumps(value))
        with self.assertRaises(ValueError):setup.library(out)

    def test_export_and_global_launch_spec_contain_no_credentials(self):
        out=setup.export(self.source,self.root/'snapshot')
        self.assertEqual(setup.library(out)[0],setup.library(self.source)[0])
        with self.assertRaises(ValueError):setup.export(self.source,out)
        spec=global_setup.launch_spec(out,self.root)
        self.assertEqual(spec['ThrottleInterval'],30);self.assertTrue(spec['RunAtLoad']);self.assertTrue(spec['KeepAlive'])
        self.assertIn('--global',spec['ProgramArguments']);self.assertNotIn('TOKEN',str(spec))
        self.assertEqual(plistlib.loads(plistlib.dumps(spec)),spec)

    def test_doctor_real_jsonl_process_and_failure(self):
        result=setup.doctor(self.source,self.target)
        self.assertEqual(result['status'],'PASS');self.assertEqual(result['writes'],0);self.assertEqual(result['tools'],6)
        (self.source/'scripts/memory_ops.py').write_text('raise SystemExit(2)')
        with self.assertRaises(ValueError):setup.doctor(self.source,self.target)


if __name__=='__main__':unittest.main()
