"""Actual Core export acceptance, isolated from checkout and live providers."""
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
SPEC=importlib.util.spec_from_file_location('pi_exports_packager',ROOT/'scripts/package_plugin.py')
PACKAGER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


def node_with_sqlite():
    """Check an existing tool only; never install Node or SDK dependencies."""
    executable=shutil.which('node')
    if executable is None:return None
    script="import {DatabaseSync} from 'node:sqlite';const v=process.versions.node.split('.').map(Number);if(v[0]<22||v[0]===22&&v[1]<13)process.exit(1);new DatabaseSync(':memory:').close();"
    try:
        result=subprocess.run([executable,'--input-type=module','--eval',script],
                              env={'PATH':os.defpath,'NODE_NO_WARNINGS':'1'},
                              stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,timeout=5)
        return executable if result.returncode==0 else None
    except (OSError,subprocess.SubprocessError):return None


NODE=node_with_sqlite()


class PiCoreExportTests(unittest.TestCase):
    @unittest.skipUnless(NODE,'optional existing Node>=22.13 with built-in SQLite required')
    def test_exported_supervisor_plan_is_zero_io_without_source_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();output=PACKAGER.build_package('core',root/'core',root=ROOT)
            supervisor=output/'packages/core/pi/supervisor.mjs'
            self.assertTrue(supervisor.is_file(),'Core must export its actual pi supervisor')
            home=root/'home';home.mkdir();neutral=root/'neutral';neutral.mkdir()
            before={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
            target=home/'not-created/state.sqlite'
            result=subprocess.run([NODE,str(supervisor),'rpc','--state',str(target),'--plan'],
                                  cwd=neutral,env={'PATH':os.defpath,'HOME':str(home),'NODE_NO_WARNINGS':'1'},
                                  stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout);self.assertEqual(value['status'],'PLANNED')
            self.assertEqual(value['writes'],0);self.assertEqual(value['model_calls'],0);self.assertFalse(value['network'])
            self.assertFalse(target.parent.exists());self.assertEqual(list(home.iterdir()),[])
            self.assertEqual(before,{p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()})

    def test_exported_python_integration_imports_canonical_modules_outside_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();output=PACKAGER.build_package('core',root/'core',root=ROOT)
            neutral=root/'neutral';neutral.mkdir();home=root/'home';home.mkdir()
            code='''import json,sys
from pathlib import Path
from packages.core.parallelism import integration
from packages.core.orchestration.runtime import runner,workspaces
from packages.core.pi import bridge as integration_bridge
root=Path(sys.argv[1]).resolve()
for module in (integration,runner,workspaces,integration_bridge):
 assert Path(module.__file__).resolve().is_relative_to(root)
assert integration.IntegrationQueue.__name__=='IntegrationQueue'
print(json.dumps({'status':'CANONICAL_IMPORTS_VERIFIED','modules':4,'model_calls':0}))
'''
            result=subprocess.run([sys.executable,'-c',code,str(output)],cwd=neutral,
                                  env={'PATH':os.defpath,'HOME':str(home),'PYTHONPATH':str(output),
                                       'PYTHONDONTWRITEBYTECODE':'1'},
                                  stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout);self.assertEqual(value['status'],'CANONICAL_IMPORTS_VERIFIED');self.assertEqual(value['modules'],4)
            for helper in ('pi_setup.py','pi_mcp.py'):
                self.assertTrue((output/'packages/core/setup'/helper).is_file())
            self.assertFalse((output/'.palarran').exists());self.assertFalse((output/'.git').exists())
