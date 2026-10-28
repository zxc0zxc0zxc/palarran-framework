"""Sanitized regressions from production feedback, frozen before implementation."""
import contextlib
import copy
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_security_report import fixture, report


class SecurityFeedbackTests(unittest.TestCase):
    def test_report_cli_returns_safe_specific_code_without_input_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'audit.json';value=fixture();value['profile']='PRIVATE_INVALID_PROFILE'
            path.write_text(json.dumps(value));output=io.StringIO()
            with contextlib.redirect_stdout(output):code=report.main(['--validate','--input',str(path)])
            result=json.loads(output.getvalue());self.assertEqual(code,2)
            self.assertEqual(result['code'],'invalid_profile')
            self.assertIn('field',result);self.assertTrue(result['hint'])
            self.assertNotIn('PRIVATE_INVALID_PROFILE',output.getvalue())

    def test_cli_argument_errors_never_echo_unknown_operator_values(self):
        renderer=importlib.import_module('packages.docs.documentation.render')
        for module in (report,renderer,importlib.import_module('packages.validation.application.project_tests')):
            with self.subTest(module=module.__name__):
                output=io.StringIO();errors=io.StringIO()
                with contextlib.redirect_stdout(output),contextlib.redirect_stderr(errors):
                    code=module.main(['--PRIVATE_OPERATOR_VALUE'])
                self.assertEqual(code,2)
                value=json.loads(output.getvalue())
                self.assertEqual(value['code'],'invalid_arguments')
                self.assertEqual(value['field'],'arguments')
                self.assertNotIn('PRIVATE_OPERATOR_VALUE',output.getvalue()+errors.getvalue())

    def test_unknown_access_time_requires_concrete_note_and_remains_incomplete(self):
        value=fixture();value['sources'][0]['accessed_at']=None
        value['sources'][0]['access_note']='Unavailable in this offline review; original reference retained.'
        value['limitations'].append('S-001: no current source fetch performed.')
        result=report.validate_report(value)
        self.assertEqual(result['source_retrieval_unknown'],1)
        self.assertFalse(result['coverage_complete'])
        del value['sources'][0]['access_note']
        with self.assertRaises(report.ReportError):report.validate_report(value)

    def test_opaque_reference_is_explicitly_valid_not_a_retroactive_vulnerability(self):
        for value in ('scratch:zz_probe','EVIDENCE-001','reports/audit.json:12'):
            report.evidence_reference(value)
        for value in ('https://example.invalid/private','../escape','/private/file','C:\\private','a\nb'):
            with self.assertRaises(report.ReportError):report.evidence_reference(value)


class LocalPathFeedbackTests(unittest.TestCase):
    def helper(self):return importlib.import_module('packages.core.security.local_io')

    def git(self,root,*args):
        return subprocess.check_output(['/usr/bin/git','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL)

    def test_arbitrary_file_and_ancestor_symlinks_remain_forbidden(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'real').mkdir();(root/'real'/'x').write_text('fixture')
            (root/'alias').symlink_to(root/'real',target_is_directory=True)
            (root/'file').symlink_to(root/'real'/'x')
            for path in (root/'alias'/'x',root/'file'):
                with self.assertRaises(ValueError):helper.safe_path(path)
            self.assertEqual(helper.safe_path(root/'missing'/'file'),root/'missing'/'file')

    @unittest.skipUnless(sys.platform=='darwin' and Path('/tmp').is_symlink(),'Darwin system alias fixture')
    def test_standard_tmp_alias_is_accepted_without_accepting_nested_alias(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory(dir='/private/tmp') as tmp:
            root=Path(tmp).resolve();(root/'file').write_text('fixture')
            alias=Path('/tmp')/root.name/'file'
            self.assertEqual(helper.safe_path(alias),root/'file')
            (root/'nested').symlink_to(root/'file')
            with self.assertRaises(ValueError):helper.safe_path(Path('/tmp')/root.name/'nested')

    def test_git_local_excludes_are_idempotent_preserve_bytes_and_leave_tracked_clean(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q')
            (root/'source').write_text('source');self.git(root,'add','source')
            before=self.git(root,'status','--porcelain')
            exclude=root/'.git/info/exclude';exclude.write_text('# user rules\ncache/\n')
            for _ in range(2):helper.ensure_private_excludes(root,('.palarran/',))
            raw=exclude.read_text();self.assertTrue(raw.startswith('# user rules\ncache/\n'));self.assertEqual(raw.count('/.palarran/'),1)
            (root/'.palarran').mkdir();(root/'.palarran/report.json').write_text('fixture')
            self.assertEqual(before,self.git(root,'status','--porcelain'))
            self.assertTrue(helper.is_git_target(root))

    def test_tracked_private_state_is_conflict_not_untracked_or_overwritten(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q');(root/'.palarran').mkdir();p=root/'.palarran/report.json';p.write_text('fixture');self.git(root,'add','--','.palarran/report.json')
            before=self.git(root,'status','--porcelain')
            with self.assertRaisesRegex(ValueError,'tracked_private_path'):helper.ensure_private_excludes(root,('.palarran/',))
            self.assertEqual(before,self.git(root,'status','--porcelain'));self.assertEqual(p.read_text(),'fixture')

    def test_owned_leaf_link_excludes_are_idempotent_without_following_the_link(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q')
            folder=root/'.agents/skills';folder.mkdir(parents=True)
            (folder/'user.md').write_text('tracked user skill');self.git(root,'add','--','.agents/skills/user.md')
            destination=root/'outside';destination.mkdir()
            (folder/'owned').symlink_to(destination,target_is_directory=True)
            for _ in range(2):helper.ensure_private_excludes(root,('.agents/skills/owned',))
            self.assertTrue((folder/'owned').is_symlink())
            self.assertEqual((root/'.git/info/exclude').read_text().count('/.agents/skills/owned'),1)
            self.assertIn('.agents/skills/user.md',self.git(root,'ls-files'))

    def test_higher_priority_unignore_blocks_and_preserves_exclude_bytes(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q')
            (root/'.gitignore').write_text('!/.palarran/\n');self.git(root,'add','.gitignore')
            exclude=root/'.git/info/exclude';before=exclude.read_bytes()
            with self.assertRaisesRegex(ValueError,'private_ignore_overridden'):
                helper.ensure_private_excludes(root,('.palarran/',))
            self.assertEqual(exclude.read_bytes(),before)
            self.assertFalse((root/'.palarran').exists())

    def test_selective_unignore_cannot_hide_behind_an_ignored_probe(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q')
            (root/'.gitignore').write_text('!/.palarran/\n/.palarran/*\n!/.palarran/docs/\n')
            before=(root/'.git/info/exclude').read_bytes()
            with self.assertRaisesRegex(ValueError,'private_ignore_overridden'):
                helper.ensure_private_excludes(root,('.palarran/',))
            self.assertEqual((root/'.git/info/exclude').read_bytes(),before)

    def test_nested_target_uses_absolute_git_metadata_and_anchored_relative_scope(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.git(root,'init','-q');target=root/'nested/target';target.mkdir(parents=True)
            path=helper.ensure_private_excludes(target,('.palarran/',))
            self.assertEqual(path,root/'.git/info/exclude')
            self.assertIn('/nested/target/.palarran/',path.read_text())

    def test_non_git_detection_has_no_initialization_side_effect(self):
        helper=self.helper()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.assertFalse(helper.is_git_target(root))
            with self.assertRaises(ValueError):helper.ensure_private_excludes(root,('.palarran/',))
            self.assertFalse((root/'.git').exists())
