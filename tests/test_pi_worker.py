"""Offline transport/lifecycle regressions; never calls a model or installs pi."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PiWorkerTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node runtime not installed')
    def test_transport_lifecycle_and_owned_file_boundaries(self):
        environment = {'PATH': os.environ.get('PATH','/usr/bin:/bin'), 'HOME': '/nonexistent', 'NO_COLOR':'1'}
        sdk = Path.home()/'.pi/agent/install/releases/1.0.0/node_modules/@earendil-works/pi-coding-agent'
        if sdk.is_dir():
            environment['PALARRAN_PI_SDK_TEST'] = str(sdk.resolve())
        result = subprocess.run([shutil.which('node'), '--test', str(ROOT/'packages/core/pi/worker/tests/worker.test.mjs')],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=50)
        self.assertEqual(result.returncode,0,result.stdout[-16000:]+result.stderr[-4000:])
