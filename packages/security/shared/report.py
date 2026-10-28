"""Validate prepared security audit evidence offline; never scan or certify a target."""
import argparse
from datetime import date, datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

# Direct script entrypoints also work from an installed target directory.
for _root in Path(__file__).resolve().parents:
    if (_root / 'packages/core/security/local_io.py').is_file():
        sys.path.insert(0,str(_root))
        break
from packages.core.security.local_io import safe_path

MAX_BYTES = 256 * 1024
PROFILES = ('infrastructure', 'ingress', 'log', 'egress', 'code', 'cve')
ID = re.compile(r'[A-Z][A-Z0-9_-]{1,63}\Z')
ADVISORY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{1,127}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')


class ReportError(ValueError):
    """Fixed safe validation code, without private report contents."""
    def __init__(self,code,field=None):
        super().__init__(code)
        self.code=code
        self.field=field


def need(value, code='invalid_report', field=None):
    if not value:
        raise ReportError(code,field)


def fields(value, names, optional=()):
    need(type(value) is dict and set(names)<=set(value) and not set(value)-set(names)-set(optional), 'invalid_fields')


def text(value, maximum=4096):
    need(type(value) is str and bool(value.strip()) and len(value.encode('utf-8')) <= maximum, 'invalid_text')
    need(not any(ord(c) < 32 and c not in '\n\t' for c in value), 'invalid_text')
    return value


def rows(value, maximum=1000, minimum=0):
    need(type(value) is list and minimum <= len(value) <= maximum, 'invalid_list')
    return value


def timestamp(value):
    text(value, 64)
    try:
        parsed = datetime.fromisoformat(value.removesuffix('Z') + '+00:00' if value.endswith('Z') else value)
    except ValueError:
        raise ReportError('invalid_timestamp') from None
    need('T' in value and parsed.tzinfo is not None and parsed.utcoffset() is not None, 'invalid_timestamp')
    return parsed


def identifier(value, pattern=ID):
    need(type(value) is str and pattern.fullmatch(value) is not None, 'invalid_identifier')
    return value


def references(value, known, minimum=0):
    rows(value, 100, minimum)
    need(all(type(v) is str and v in known for v in value) and len(set(value)) == len(value), 'broken_reference')
    return value


def index(value, keys, pattern=ID, minimum=0, optional=(), section=None):
    result = {}
    for position,row in enumerate(rows(value, minimum=minimum)):
        try:
            fields(row, keys, optional)
            key = identifier(row['id'], pattern)
            need(key not in result, 'duplicate_identifier')
            result[key] = row
        except ReportError as error:
            if error.field is None and section:
                error.field = f'{section}[{position}]'
            raise
    return result


def public_url(value):
    text(value, 2048)
    try:
        u = urlsplit(value)
        host = u.hostname
        port = u.port
    except ValueError:
        raise ReportError('invalid_source_url') from None
    need(u.scheme == 'https' and bool(host) and u.username is None and u.password is None
         and not u.query and not u.fragment and port in (None, 443), 'invalid_source_url')
    need(not any(c.isspace() for c in value) and '\\' not in value, 'invalid_source_url')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ReportError('invalid_source_url')
    need('.' in host and not host.lower().endswith(('.local', '.internal', '.localhost'))
         and host.lower() != 'localhost', 'invalid_source_url')


def evidence_reference(value):
    text(value, 1024)
    need(not value.startswith(('/', '~')) and re.match(r'^[A-Za-z]:', value) is None
         and not any(ord(c) == 127 for c in value) and '\\' not in value and '://' not in value
         and not any(p in ('', '.', '..') for p in value.split('/'))
         and not any(c in value for c in '\r\n\t?'), 'invalid_evidence_reference')


def validate_report(value):
    fields(value, ('version', 'profile', 'subject', 'inspected_at', 'sources', 'evidence',
                   'coverage', 'findings', 'advisories', 'limitations', 'privacy_reviewed'))
    need(type(value['version']) is int and value['version'] == 1, 'unsupported_version')
    need(value['profile'] in PROFILES and type(value['profile']) is str, 'invalid_profile','profile')
    need(value['privacy_reviewed'] is True, 'privacy_review_required')
    inspected = timestamp(value['inspected_at'])
    subject = value['subject']
    fields(subject, ('project', 'revision', 'snapshot_sha256', 'environment'))
    for key in ('project', 'environment'):
        need(type(subject[key]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', subject[key]), 'invalid_subject')
    revision, snapshot = subject['revision'], subject['snapshot_sha256']
    need(revision is None or type(revision) is str and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', revision), 'invalid_subject')
    need(snapshot is None or type(snapshot) is str and SHA.fullmatch(snapshot), 'invalid_subject')
    need(revision is not None or snapshot is not None, 'missing_subject_identity')
    sources = index(value['sources'], ('id', 'title', 'publisher', 'url', 'published_at', 'accessed_at'), minimum=1,optional=('access_note',),section='sources')
    source_retrieval_unknown=0
    for position,source in enumerate(sources.values()):
        text(source['title'], 1024); text(source['publisher'], 256); public_url(source['url'])
        if source['accessed_at'] is None:
            need(type(source.get('access_note')) is str and bool(source['access_note'].strip()),
                 'source_access_note_required',f'sources[{position}].access_note')
            text(source['access_note'],1024)
            need(type(value['limitations']) is list and bool(value['limitations']),
                 'source_retrieval_limitation_required','limitations')
            source_retrieval_unknown+=1
        else:
            try:
                need(timestamp(source['accessed_at']) <= inspected, 'future_source')
            except ReportError as error:
                error.field=f'sources[{position}].accessed_at'
                raise
            if 'access_note' in source:text(source['access_note'],1024)
        if source['published_at'] is not None:
            published = source['published_at']
            if type(published) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}', published):
                try:
                    need(date.fromisoformat(published) <= inspected.date(), 'future_source')
                except ValueError:
                    raise ReportError('invalid_timestamp') from None
            else:
                need(timestamp(published) <= inspected, 'future_source')
    evidence = index(value['evidence'], ('id', 'kind', 'reference', 'sha256', 'summary'))
    kinds = ('code', 'configuration', 'test', 'observation', 'inventory', 'advisory', 'synthetic')
    for item in evidence.values():
        need(type(item['kind']) is str and item['kind'] in kinds, 'invalid_evidence_kind')
        evidence_reference(item['reference']); text(item['summary'])
        need(type(item['sha256']) is str and SHA.fullmatch(item['sha256']), 'invalid_evidence_hash')
        need(item['kind'] != 'synthetic' or subject['environment'] == 'synthetic', 'synthetic_subject_mismatch')
    coverage = index(value['coverage'], ('id', 'area', 'status', 'evidence_ids', 'rationale'), minimum=1)
    statuses = {'PASS': 0, 'FAIL': 0, 'NOT_RUN': 0, 'NA': 0}
    for control in coverage.values():
        text(control['area'], 512); text(control['rationale'])
        need(type(control['status']) is str and control['status'] in statuses, 'invalid_coverage_status')
        statuses[control['status']] += 1
        references(control['evidence_ids'], evidence, int(control['status'] in ('PASS', 'FAIL')))
    findings = index(value['findings'], ('id', 'title', 'severity', 'confidence', 'coverage_ids',
                                        'evidence_ids', 'source_ids', 'impact', 'remediation', 'verification'))
    severities = {name: 0 for name in ('critical', 'high', 'medium', 'low', 'info')}
    linked = set()
    suspected = 0
    for finding in findings.values():
        for key in ('title', 'impact', 'remediation', 'verification'):
            text(finding[key])
        need(type(finding['severity']) is str and finding['severity'] in severities, 'invalid_severity')
        need(finding['confidence'] in ('confirmed', 'suspected'), 'invalid_confidence')
        severities[finding['severity']] += 1
        suspected += int(finding['confidence'] == 'suspected')
        references(finding['coverage_ids'], coverage, 1)
        references(finding['evidence_ids'], evidence, 1); references(finding['source_ids'], sources, 1)
        linked.update(finding['coverage_ids'])
        need(finding['confidence'] != 'confirmed' or any(coverage[k]['status'] == 'FAIL' for k in finding['coverage_ids']), 'contradictory_confirmed_finding')
    need(all(k in linked for k, c in coverage.items() if c['status'] == 'FAIL'), 'unexplained_failed_control')
    advisories = index(value['advisories'], ('id', 'aliases', 'component', 'ecosystem', 'observed_version',
                                            'match_status', 'applicability', 'fixed_version', 'source_ids',
                                            'evidence_ids', 'last_checked_at', 'advisory_modified_at'), ADVISORY)
    need(value['profile'] == 'cve' or not advisories, 'advisory_profile_mismatch')
    aliases = set(); advisory_states = {name: 0 for name in ('affected', 'not_affected', 'fixed', 'unknown', 'not_checked')}
    for advisory in advisories.values():
        identities = [advisory['id']] + rows(advisory['aliases'], 100)
        for alias in identities:
            key = identifier(alias, ADVISORY).casefold()
            need(key not in aliases, 'duplicate_advisory_alias'); aliases.add(key)
        for key in ('component', 'ecosystem', 'applicability'):
            text(advisory[key])
        state = advisory['match_status']
        need(type(state) is str and state in advisory_states, 'invalid_advisory_status')
        advisory_states[state] += 1
        determinate = state in ('affected', 'not_affected', 'fixed')
        references(advisory['source_ids'], sources, int(determinate))
        refs = references(advisory['evidence_ids'], evidence, int(determinate))
        if determinate:
            need(any(evidence[k]['kind'] in ('inventory', 'synthetic') for k in refs), 'missing_version_inventory')
        for key in ('observed_version', 'fixed_version'):
            need(advisory[key] is None or type(advisory[key]) is str, 'invalid_version')
            if advisory[key] is not None:
                text(advisory[key], 256)
        need(not determinate or advisory['observed_version'] is not None, 'missing_observed_version')
        checked = timestamp(advisory['last_checked_at'])
        need(checked <= inspected, 'future_advisory_check')
        if advisory['advisory_modified_at'] is not None:
            need(timestamp(advisory['advisory_modified_at']) <= checked, 'stale_advisory_observation')
    for limitation in rows(value['limitations'], 100):
        text(limitation)
    unknown = advisory_states['unknown'] + advisory_states['not_checked']
    checked = statuses['PASS'] + statuses['FAIL']
    complete = not statuses['NOT_RUN'] and not unknown and not suspected and not source_retrieval_unknown and checked > 0
    conclusion = 'REVIEW_REQUIRED' if findings or advisory_states['affected'] else ('NO_FINDINGS_WITHIN_CHECKED_SCOPE' if complete else 'INCOMPLETE')
    return {'status': 'VALIDATED_REPORT', 'profile': value['profile'], 'coverage': statuses,
            'checked_controls': checked, 'findings': len(findings), 'severity': severities,
            'advisories': advisory_states, 'coverage_complete': complete, 'conclusion': conclusion,
            'evidence_mode': 'synthetic' if any(e['kind'] == 'synthetic' for e in evidence.values()) else 'declared_evidence',
            'security_certification': 'NOT_PROVIDED', 'source_retrieval_unknown':source_retrieval_unknown, 'network': False, 'writes': 0}


def read_report(path):
    try:
        path=safe_path(path)
    except ValueError:
        raise ReportError('unsafe_input_path','input') from None
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_BYTES, 'invalid_input_file')
        raw = stream.read(MAX_BYTES + 1)
    need(len(raw) <= MAX_BYTES, 'input_too_large')
    def pairs(entries):
        result = {}
        for key, value in entries:
            need(key not in result, 'duplicate_field'); result[key] = value
        return result
    def nonfinite(_):
        raise ReportError('nonfinite_number')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true'); parser.add_argument('--validate', action='store_true')
    parser.add_argument('--input')
    args = parser.parse_args(argv)
    if args.plan:
        print('{"status":"PLANNED","network":false,"writes":0}'); return 0
    try:
        need(args.validate and args.input is not None, 'explicit_input_required')
        result = validate_report(read_report(args.input))
        print(json.dumps(result, sort_keys=True)); return 0
    except ReportError as error:
        hints={'explicit_input_required':'Pass --validate --input with a prepared report.',
               'invalid_profile':'Choose a documented security profile.',
               'unsafe_input_path':'Use a regular file without arbitrary symlink components.',
               'source_access_note_required':'Describe unavailable source retrieval without inventing a timestamp.',
               'source_retrieval_limitation_required':'Record unavailable retrieval in limitations.'}
        print(json.dumps(dict(status='REJECTED',code=error.code,field=error.field,
              hint=hints.get(error.code,'Check the security report schema and declared evidence references.'),network=False,writes=0)))
        return 2
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        print(json.dumps(dict(status='REJECTED',code='invalid_or_unavailable_report',field='input',
              hint='Provide an available bounded UTF-8 JSON report matching the documented schema.',network=False,writes=0)))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
