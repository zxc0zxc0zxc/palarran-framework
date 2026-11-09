"""Offline selected-memory MCP migration; never starts a server or model."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable if importlib.util.find_spec('tomllib') else shutil.which('python3.11')


@unittest.skipUnless(PYTHON, 'existing Python3.11+ tomllib required; no automatic install')
class PiMemoryMigrationTests(unittest.TestCase):
    def fixture(self,root):
        home=root/'home';agent=home/'.pi/agent';agent.mkdir(parents=True)
        source=home/'.codex/config.toml';source.parent.mkdir()
        wrapper=root/'memory-wrapper';wrapper.write_text('#!/bin/sh\nprintf SHOULD_NOT_EXECUTE > "'+str(root/'executed')+'"\n');wrapper.chmod(0o700)
        self.write_source(source,wrapper)
        return home,agent,source,wrapper

    def write_source(self,source,wrapper,*,env='PRIVATE_SECRET_FIXTURE',extra='',name='engineering-memory'):
        source.write_text('[mcp_servers.'+name+']\ncommand = '+json.dumps(str(wrapper))+'\nargs = ["--global", "--readonly"]\n'+extra+'\n[mcp_servers.'+name+'.env]\nMEMORY_TOKEN = '+json.dumps(env)+'\n\n[mcp_servers.keenable]\nurl = "https://example.invalid/mcp"\nhttp_headers = {"X-API-Key" = "SECRET_KEENABLE_NOT_COPIED"}\n')

    def run_cli(self,home,agent,source,*,server='engineering-memory',plan=False):
        args=[PYTHON,str(ROOT/'packages/core/setup/pi_mcp.py'),'--home',str(home),'--agent-dir',str(agent),'--codex-config',str(source),'--source-server',server]
        if plan:args.append('--plan')
        completed=subprocess.run(args,capture_output=True,text=True,timeout=15)
        self.assertNotIn('PRIVATE_SECRET_FIXTURE',completed.stdout+completed.stderr)
        self.assertNotIn('SECRET_KEENABLE_NOT_COPIED',completed.stdout+completed.stderr)
        self.assertFalse((home.parent/'executed').exists())
        value=json.loads(completed.stdout)
        return completed,value

    def test_plan_is_readonly_and_reports_only_safe_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            before={p.relative_to(home).as_posix():p.read_bytes() for p in home.rglob('*') if p.is_file()}
            checked,result=self.run_cli(home,agent,source,plan=True)
            self.assertEqual(checked.returncode,0);self.assertEqual(result['status'],'PLANNED');self.assertEqual(result['writes'],0)
            self.assertEqual(result['server'],'engineering_memory');self.assertEqual(result['transport'],'stdio')
            self.assertNotIn(str(wrapper),checked.stdout);self.assertNotIn('args',result);self.assertNotIn('env',result)
            self.assertEqual(before,{p.relative_to(home).as_posix():p.read_bytes() for p in home.rglob('*') if p.is_file()})

    def test_install_copies_only_selected_stdio_and_preserves_other_pi_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            old={'mcpServers':{'existing':{'url':'https://existing.invalid/mcp','headers':{'Authorization':'EXISTING_PRIVATE'}}},'autoEnableCodemode':False,'custom':{'untouched':True}}
            target=agent/'mcp.json';target.write_text(json.dumps(old))
            checked,result=self.run_cli(home,agent,source)
            self.assertEqual(checked.returncode,0);self.assertEqual(result['status'],'INSTALLED')
            current=json.loads(target.read_text());entry=current['mcpServers']['engineering_memory']
            self.assertEqual(entry,{'command':str(wrapper),'args':['--global','--readonly'],'env':{'MEMORY_TOKEN':'PRIVATE_SECRET_FIXTURE'}})
            self.assertEqual(current['mcpServers']['existing'],old['mcpServers']['existing']);self.assertEqual(current['custom'],old['custom']);self.assertFalse(current['autoEnableCodemode'])
            self.assertNotIn('keenable',current['mcpServers']);self.assertEqual(target.stat().st_mode&0o777,0o600)
            receipt=home/'.palarran/pi/mcp-installation.json';self.assertEqual(receipt.stat().st_mode&0o777,0o600)
            self.assertNotIn('PRIVATE_SECRET_FIXTURE',receipt.read_text())
            backups=list((home/'.palarran/pi/mcp-backups').rglob('mcp.json'));self.assertEqual(len(backups),1);self.assertEqual(json.loads(backups[0].read_text()),old)

    def test_idempotent_update_keeps_unrelated_changes_and_refuses_local_owned_edits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root);target=agent/'mcp.json'
            self.run_cli(home,agent,source);before=target.read_bytes();_,result=self.run_cli(home,agent,source);self.assertEqual(result['status'],'UNCHANGED');self.assertEqual(target.read_bytes(),before)
            current=json.loads(target.read_text());current['custom']='owner';target.write_text(json.dumps(current))
            self.write_source(source,wrapper,env='NEXT_PRIVATE_VALUE')
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,0);self.assertEqual(result['status'],'UPDATED');self.assertNotIn('NEXT_PRIVATE_VALUE',checked.stdout+checked.stderr)
            current=json.loads(target.read_text());self.assertEqual(current['custom'],'owner');self.assertEqual(current['mcpServers']['engineering_memory']['env']['MEMORY_TOKEN'],'NEXT_PRIVATE_VALUE')
            current['mcpServers']['engineering_memory']['args'].append('--local-edit');target.write_text(json.dumps(current));before=target.read_bytes()
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'owned_entry_modified');self.assertEqual(target.read_bytes(),before)

    def test_unowned_entry_conflicts_and_identical_entry_is_not_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root);target=agent/'mcp.json'
            target.write_text('{"mcpServers":{"engineering-memory":{"command":"DIFFERENT"}}}')
            before=target.read_bytes();checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'server_conflict');self.assertEqual(target.read_bytes(),before)
            target.write_text(json.dumps({'mcpServers':{'engineering_memory':{'command':str(wrapper),'args':['--global','--readonly'],'env':{'MEMORY_TOKEN':'PRIVATE_SECRET_FIXTURE'}}}}));before=target.read_bytes()
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,0);self.assertEqual(result['status'],'ALREADY_CONFIGURED');self.assertFalse(result['owned']);self.assertEqual(target.read_bytes(),before);self.assertFalse((home/'.palarran').exists())

    def test_alias_collision_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root);target=agent/'mcp.json'
            target.write_text('{"mcpServers":{"engineering-memory":{},"engineering_memory":{}}}');before=target.read_bytes()
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'server_name_collision');self.assertEqual(target.read_bytes(),before)

    def test_missing_source_or_memory_is_deferred_without_new_service(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            for raw in (None,'[mcp_servers.other]\ncommand="unrelated"\n'):
                if raw is None:source.unlink()
                else:source.write_text(raw)
                checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,0);self.assertEqual(result['status'],'DEFERRED');self.assertEqual(result['writes'],0);self.assertFalse((agent/'mcp.json').exists());self.assertFalse((home/'.palarran').exists())

    def test_http_unknown_restrictions_and_other_servers_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            cases=[('[mcp_servers.engineering-memory]\nurl="https://example.invalid"\nhttp_headers={Authorization="PRIVATE_SECRET_FIXTURE"}\n','unsupported_transport')]
            for extra in ('disabled_tools=["delete"]\n','env_vars=["PRIVATE_SOURCE_VAR"]\n'):
                self.write_source(source,wrapper,extra=extra);cases.append((source.read_text(),'unsupported_source_fields'))
            for raw,code in cases:
                source.write_text(raw);checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],code);self.assertFalse((agent/'mcp.json').exists())
            checked,result=self.run_cli(home,agent,source,server='keenable');self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'invalid_source_server')

    def test_pi_dynamic_env_shell_commands_symlinks_and_relative_cwd_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            for env in ('!echo PRIVATE_SECRET_FIXTURE','${PRIVATE_SOURCE_VAR}'):
                self.write_source(source,wrapper,env=env);checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'dynamic_env_not_portable')
            self.write_source(source,wrapper,extra='cwd="relative"\n');checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2)
            self.write_source(source,Path('/bin/sh'));checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'unsafe_executable')
            link=root/'alias';link.symlink_to(wrapper);self.write_source(source,link);checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2)
            self.assertFalse((home/'.palarran').exists())

    def test_disabled_source_stays_disabled_and_pending_outcome_blocks_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            self.write_source(source,wrapper,extra='enabled=false\n');checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,0)
            self.assertFalse(json.loads((agent/'mcp.json').read_text())['mcpServers']['engineering_memory']['enabled'])
            (home/'.palarran/pi/mcp-pending.json').write_text('{}');before=(agent/'mcp.json').read_bytes()
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2);self.assertEqual(result['code'],'recovery_required');self.assertEqual((agent/'mcp.json').read_bytes(),before)

    def test_source_symlink_duplicate_json_and_cli_argument_values_never_echo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();home,agent,source,wrapper=self.fixture(root)
            original=root/'original.toml';source.rename(original);source.symlink_to(original)
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2)
            source.unlink();original.rename(source);(agent/'mcp.json').write_text('{"mcpServers":{},"mcpServers":{}}')
            checked,result=self.run_cli(home,agent,source);self.assertEqual(checked.returncode,2)
            checked=subprocess.run([PYTHON,str(ROOT/'packages/core/setup/pi_mcp.py'),'--PRIVATE_SECRET_FIXTURE'],capture_output=True,text=True)
            self.assertEqual(checked.returncode,2);self.assertNotIn('PRIVATE_SECRET_FIXTURE',checked.stdout+checked.stderr);self.assertEqual(json.loads(checked.stdout)['code'],'invalid_arguments')
