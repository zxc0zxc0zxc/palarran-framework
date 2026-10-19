"""A denied cleanup signal is safe only after independently proved group absence."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
from orchestrator.runner import _kill_group,_group_absent,execute


class TerminationTests(unittest.TestCase):
    def test_denial_requires_exited_root_and_absent_group(self):
        for exited,absent in ((False,True),(True,False),(True,True)):
            process=Mock(pid=123);process.poll.return_value=0 if exited else None
            with patch('orchestrator.runner.os.killpg',side_effect=PermissionError), patch('orchestrator.runner._group_absent',return_value=absent) as inventory:
                if exited and absent:_kill_group(process)
                else:
                    with self.assertRaises(PermissionError):_kill_group(process)
                self.assertEqual(inventory.called,exited)

    def test_inventory_must_be_numeric_complete_and_available(self):
        for text,absent in [(' 123\n 456\n',False),('456\n789\n',True),('',False),('garbage\n',False)]:
            with patch('orchestrator.runner.subprocess.run',return_value=Mock(stdout=text)):
                self.assertEqual(_group_absent(123),absent)
        with patch('orchestrator.runner.subprocess.run',side_effect=subprocess.TimeoutExpired('ps',2)):
            self.assertFalse(_group_absent(123))

    def test_completed_real_child_drains_receipt_after_denied_group_cleanup(self):
        code='''import json
for value in [dict(type='turn.started'),dict(type='usage.updated',usage=dict(input_tokens=100,cached_input_tokens=50,cache_creation_input_tokens=0,output_tokens=10,reasoning_output_tokens=0,total_tokens=110)),dict(type='turn.completed')]:print(json.dumps(value),flush=True)
'''
        with tempfile.TemporaryDirectory() as root, patch('orchestrator.runner.os.killpg',side_effect=PermissionError):
            result=execute([sys.executable,'-c',code],root,timeout=5,output_limit=10000,env={},heartbeat=lambda:True,usage_adapter='codex-app-server')
        self.assertEqual(result.reason,'exited');self.assertTrue(result.usage_complete)
        self.assertEqual(result.diagnostics['terminal_event'],'turn.completed')
