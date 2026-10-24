"""Offline schema/privacy regressions; fixtures do not establish target security."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'packages/security/shared/report.py'
SPEC = importlib.util.spec_from_file_location('security_report_under_test', SOURCE)
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def fixture():
    return json.loads((SOURCE.parent / 'templates/audit.example.json').read_bytes())


def cve_fixture():
    value = fixture()
    value['profile'] = 'cve'
    value['advisories'] = [{
        'id': 'CVE-2026-12345', 'aliases': ['GHSA-abcd-efgh-ijkl'],
        'component': 'synthetic-library', 'ecosystem': 'synthetic',
        'observed_version': '1.2.3', 'match_status': 'affected',
        'applicability': 'Synthetic inventory comparison, no live target.',
        'fixed_version': '1.2.4', 'source_ids': ['S-001'], 'evidence_ids': ['E-001'],
        'last_checked_at': '2026-10-24T11:30:00Z',
        'advisory_modified_at': '2026-10-23T00:00:00Z'}]
    return value


class SecurityReportTests(unittest.TestCase):
    def rejected(self, value, code=None):
        with self.assertRaises(report.ReportError) as caught:
            report.validate_report(value)
        if code:
            self.assertEqual(str(caught.exception), code)

    def test_example_remains_incomplete_synthetic_and_never_certifies(self):
        result = report.validate_report(fixture())
        self.assertEqual(result['evidence_mode'], 'synthetic')
        self.assertFalse(result['coverage_complete'])
        self.assertEqual(result['conclusion'], 'REVIEW_REQUIRED')
        self.assertEqual(result['security_certification'], 'NOT_PROVIDED')
        self.assertFalse(result['network'])
        self.assertEqual(result['writes'], 0)

    def test_synthetic_evidence_cannot_be_relabelled_as_live(self):
        for environment in ('production', 'staging', 'live'):
            with self.subTest(environment=environment):
                value = fixture(); value['subject']['environment'] = environment
                self.rejected(value, 'synthetic_subject_mismatch')

    def test_not_run_or_na_only_is_not_complete(self):
        for status in ('NOT_RUN', 'NA'):
            with self.subTest(status=status):
                value = fixture(); value['findings'] = []
                for control in value['coverage']:
                    control.update(status=status, evidence_ids=[])
                result = report.validate_report(value)
                self.assertFalse(result['coverage_complete'])
                self.assertEqual(result['checked_controls'], 0)
                self.assertEqual(result['conclusion'], 'INCOMPLETE')

    def test_fail_and_confirmed_findings_must_agree(self):
        value = fixture(); value['findings'] = []
        self.rejected(value, 'unexplained_failed_control')
        value = fixture(); value['coverage'][0]['status'] = 'PASS'
        value['findings'][0]['confidence'] = 'confirmed'
        self.rejected(value, 'contradictory_confirmed_finding')
        value = fixture(); value['findings'][0]['confidence'] = 'confirmed'
        self.assertEqual(report.validate_report(value)['evidence_mode'], 'synthetic')

    def test_unknown_fields_rejected_at_every_object_boundary(self):
        for section in ('root', 'subject', 'sources', 'evidence', 'coverage', 'findings', 'advisories'):
            with self.subTest(section=section):
                value = cve_fixture()
                target = value if section == 'root' else value[section]
                if isinstance(target, list): target = target[0]
                target['unexpected'] = 'private fixture'
                self.rejected(value, 'invalid_fields')

    def test_json_duplicate_fields_and_nonfinite_numbers_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'report.json'
            for raw, code in ((b'{"version":1,"version":1}', 'duplicate_field'),
                              (b'{"x":{"id":1,"id":2}}', 'duplicate_field'),
                              (b'{"x":NaN}', 'nonfinite_number')):
                with self.subTest(raw=raw):
                    path.write_bytes(raw)
                    with self.assertRaisesRegex(report.ReportError, code): report.read_report(path)

    def test_evidence_references_are_bounded_relative_or_opaque(self):
        invalid = ('/private/report.json', '~/report', '../report', 'a/../report', './report',
                   'a//report', 'a/', 'C:/private/report.json', 'C:private.json',
                   r'folder\report', 'https://example.org/evidence', 'item?token=x',
                   'item\nsecret', 'item\tsecret', 'item\x7fsecret', 'x' * 1025)
        for reference in invalid:
            with self.subTest(reference=reference):
                with self.assertRaises(report.ReportError): report.evidence_reference(reference)
        for reference in ('evidence/module.py:42', 'E-001', 'fixtures/report.json'):
            report.evidence_reference(reference)

    def test_reference_integrity_and_list_bounds(self):
        for refs in (['MISSING'], ['E-001', 'E-001'], ['E-001'] * 101):
            value = fixture(); value['coverage'][0]['evidence_ids'] = refs
            self.rejected(value)
        value = fixture(); value['coverage'][0]['evidence_ids'] = []
        self.rejected(value)
        value = fixture(); value['evidence'] *= 1001
        self.rejected(value, 'invalid_list')
        value = fixture(); value['evidence'][0]['summary'] = 'é' * 2049
        self.rejected(value, 'invalid_text')

    def test_input_files_reject_symlinks_nonregular_and_oversize(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / 'report.json'
            path.write_text('{}')
            link = root / 'link'; link.symlink_to(path)
            directory_link = root / 'linked'; directory_link.symlink_to(root, target_is_directory=True)
            for unsafe in (link, directory_link / path.name, root):
                with self.subTest(path=unsafe):
                    with self.assertRaises((report.ReportError, OSError)): report.read_report(unsafe)
            path.write_bytes(b' ' * (report.MAX_BYTES + 1))
            with self.assertRaisesRegex(report.ReportError, 'invalid_input_file'): report.read_report(path)

    def test_advisory_aliases_deduplicate_case_insensitively(self):
        value = cve_fixture(); value['advisories'][0]['aliases'].append('cve-2026-12345')
        self.rejected(value, 'duplicate_advisory_alias')
        value = cve_fixture(); other = copy.deepcopy(value['advisories'][0])
        other.update(id='CVE-2026-54321', aliases=['ghsa-ABCD-efgh-ijkl'])
        value['advisories'].append(other)
        self.rejected(value, 'duplicate_advisory_alias')

    def test_unknown_version_and_inventory_requirements(self):
        for state in ('affected', 'not_affected', 'fixed'):
            with self.subTest(state=state):
                value = cve_fixture(); value['advisories'][0].update(match_status=state, observed_version=None)
                self.rejected(value, 'missing_observed_version')
        value = cve_fixture(); value['advisories'][0].update(match_status='unknown', observed_version=None)
        result = report.validate_report(value)
        self.assertFalse(result['coverage_complete'])
        self.assertEqual(result['advisories']['unknown'], 1)
        value = cve_fixture(); value['evidence'][0]['kind'] = 'code'
        self.rejected(value, 'missing_version_inventory')

    def test_advisory_freshness_and_profile_boundaries(self):
        value = cve_fixture(); value['advisories'][0]['advisory_modified_at'] = '2026-10-24T11:31:00Z'
        self.rejected(value, 'stale_advisory_observation')
        value = cve_fixture(); value['advisories'][0]['last_checked_at'] = '2026-10-24T12:01:00Z'
        self.rejected(value, 'future_advisory_check')
        value = cve_fixture(); value['profile'] = 'code'
        self.rejected(value, 'advisory_profile_mismatch')

    def test_sources_are_public_https_metadata_not_endpoints(self):
        for url in ('http://example.org/doc', 'https://127.0.0.1/doc', 'https://example.local/doc',
                    'https://user:password@example.org/doc', 'https://example.org/doc?token=x',
                    'https://example.org/doc#secret', 'https://example.org:8443/doc'):
            value = fixture(); value['sources'][0]['url'] = url
            self.rejected(value, 'invalid_source_url')

    def test_plan_performs_no_input_io_even_with_validate_flag(self):
        with mock.patch.object(report, 'read_report', side_effect=AssertionError('input read')), \
             mock.patch.object(report, 'validate_report', side_effect=AssertionError('validation')), \
             mock.patch.object(report.os, 'open', side_effect=AssertionError('file open')), \
             mock.patch.object(Path, 'open', side_effect=AssertionError('path open')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            result = report.main(['--plan', '--validate', '--input', '/private/never-open'])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue()), {'status': 'PLANNED', 'network': False, 'writes': 0})

    def test_validation_has_no_network_process_or_evidence_reads(self):
        value = cve_fixture()
        with mock.patch('socket.socket', side_effect=AssertionError('network')), \
             mock.patch('socket.getaddrinfo', side_effect=AssertionError('DNS')), \
             mock.patch('urllib.request.urlopen', side_effect=AssertionError('HTTP')), \
             mock.patch('subprocess.Popen', side_effect=AssertionError('process')), \
             mock.patch.object(report.os, 'open', side_effect=AssertionError('evidence open')), \
             mock.patch.object(Path, 'open', side_effect=AssertionError('evidence read')):
            self.assertEqual(report.validate_report(value)['status'], 'VALIDATED_REPORT')

    def test_cli_outputs_counts_or_fixed_error_never_private_narratives(self):
        secret = 'PRIVATE_FIXTURE_MUST_NOT_ECHO'
        for invalid in (False, True):
            value = fixture(); value['limitations'].append(secret)
            if invalid: value['unknown_private_field'] = secret
            with mock.patch.object(report, 'read_report', return_value=value), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                code = report.main(['--validate', '--input', 'private-fixture.json'])
            self.assertEqual(code, 2 if invalid else 0)
            self.assertNotIn(secret, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())['status'], 'REJECTED' if invalid else 'VALIDATED_REPORT')


if __name__ == '__main__':
    unittest.main()
