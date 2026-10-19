"""Product artifact fixture builders and offline integrity regression tests."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from orchestrator.product_artifacts import (HEADINGS, STAGES, canonical_sha, pipeline_dir,
                                            source_digest, validate_stage)

SKILLS_ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


def make_target(directory, skills_root=SKILLS_ROOT, pipeline_id='1' * 32):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root)] + list(args), stderr=subprocess.DEVNULL).decode().strip()
    git('init', '-q')
    git('config', 'user.name', 'Fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    (root / 'README.md').write_text('Disposable fixture\n', encoding='utf-8')
    (root / '.gitignore').write_text('ignored/\n', encoding='utf-8')
    git('add', '.')
    git('commit', '-qm', 'Fixture baseline')
    context = dict(schema_version=1, pipeline_id=pipeline_id, idea='Research fixture idea',
                   source_digest=source_digest(skills_root), plan_revision='product-v001',
                   baseline=git('rev-parse', 'HEAD'))
    write_json(pipeline_dir(root, pipeline_id) / 'context.json', context)
    (root / '.ai-development/INDEX.md').write_text('# Decision index\n', encoding='utf-8')
    (root / '.ai-development/product/INDEX.md').write_text(pipeline_id + '\n', encoding='utf-8')
    return root, context


def write_stage(root, context, stage, *, unknown=False, critical=False, recommendation='plan'):
    root = Path(root)
    base = pipeline_dir(root, context['pipeline_id'])
    relative = base.relative_to(root).as_posix()
    report = base / 'stages' / stage / 'report.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('# Fixture research\nE-' + stage + '-1\n', encoding='utf-8')
    decision_id = 'product/pipeline-' + context['pipeline_id'] + '/' + stage
    decision = base / 'decisions' / (stage + '.md')
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_text('---\nid: ' + decision_id + '\nstatus: accepted\n---\n' +
                        '\n'.join('## ' + heading + '\nFixture rationale.\n' for heading in HEADINGS), encoding='utf-8')
    with (root / '.ai-development/INDEX.md').open('a', encoding='utf-8') as stream:
        stream.write(decision_id + '\n')
    inputs = {}
    unknown_ids = []
    for previous in STAGES[:STAGES.index(stage)]:
        prior = json.loads((base / 'stages' / previous / 'stage.json').read_text(encoding='utf-8'))
        inputs[previous] = canonical_sha(prior)
        unknown_ids += [record['id'] for record in prior['unknowns']]
    e_id = 'E-' + stage + '-1'
    evidence = {key: 'Fixture not a live research finding' for key in
                'claim publisher published_at metric_as_of period geography entity_product unit method value_or_range limitations confidence_reason formula'.split()}
    evidence.update(id=e_id, classification='observed', source_url='https://example.com/fixture',
                    retrieved_at='2026-10-19', confidence='low', input_ids=[])
    unknowns = []
    if unknown:
        unknowns = [dict(id='U-' + stage + '-1', question='Unknown fixture fact', critical=critical)]
        unknown_ids.append(unknowns[0]['id'])
    manifest = dict(schema_version=1, pipeline_id=context['pipeline_id'], stage=stage,
                    revision='v001', status='research_complete', context_sha256=canonical_sha(context), inputs=inputs,
                    report=dict(path=report.relative_to(root).as_posix(), sha256=hashlib.sha256(report.read_bytes()).hexdigest()),
                    evidence=[evidence], decisions=[dict(id=decision_id, path=decision.relative_to(root).as_posix(),
                                                       sha256=hashlib.sha256(decision.read_bytes()).hexdigest(), status='accepted')],
                    claims=[dict(id='C-' + stage + '-1', text='Fixture finding', evidence_ids=[e_id], decision_ids=[decision_id])],
                    unknowns=unknowns, verdict=None, requirements=[], experiments=[])
    if stage == 'mvp':
        manifest.update(verdict=dict(recommendation=recommendation, market_validated=False, unresolved=unknown_ids, resolutions=[]),
                        requirements=[dict(id='R-mvp-1', description='Fixture scoped requirement', acceptance='Fixture measurable AC',
                                           priority='must', evidence_ids=[e_id], decision_ids=[decision_id])],
                        experiments=[dict(id='T-mvp-1', hypothesis='Fixture hypothesis', metric='Fixture metric', threshold='1 response',
                                          window='1 week', budget='0 USD proposed', stop='Stop at budget', evidence_ids=[e_id], decision_ids=[decision_id])])
    write_json(base / 'stages' / stage / 'stage.json', manifest)
    return manifest


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root, self.context = make_target(self.temp.name)
        self.base = pipeline_dir(self.root, self.context['pipeline_id'])

    def check(self, stage='define'):
        return validate_stage(self.root, self.context['pipeline_id'], stage, canonical_sha(self.context), SKILLS_ROOT)

    def save(self, manifest):
        write_json(self.base / 'stages' / manifest['stage'] / 'stage.json', manifest)

    def fail(self, stage='define'):
        with self.assertRaises((ValueError, OSError)):
            self.check(stage)

    def test_valid_prefix_and_final(self):
        for stage in STAGES:
            expected = write_stage(self.root, self.context, stage)
            self.assertEqual(self.check(stage), expected)

    def test_context_digest_and_source_drift(self):
        write_stage(self.root, self.context, 'define')
        self.context['idea'] = 'Changed'
        write_json(self.base / 'context.json', self.context)
        self.fail()
        self.context['source_digest'] = '0' * 64
        write_json(self.base / 'context.json', self.context)
        self.fail()

    def test_report_and_decision_digest(self):
        manifest = write_stage(self.root, self.context, 'define')
        report = self.root / manifest['report']['path']
        report.write_text('Corrupted', encoding='utf-8')
        self.fail()
        manifest = write_stage(self.root, self.context, 'define')
        (self.root / manifest['decisions'][0]['path']).write_text('Corrupted', encoding='utf-8')
        self.fail()

    def test_wrong_fields_and_bool_schema(self):
        for change in ({'extra': 'field'}, {'schema_version': True}, {'status': 'verified'}, {'inputs': {'market': '0' * 64}}):
            manifest = write_stage(self.root, self.context, 'define')
            manifest.update(change)
            self.save(manifest)
            self.fail()

    def test_local_context_and_decision_evidence_are_pinned(self):
        manifest = write_stage(self.root, self.context, 'define')
        for uri in ('artifact:context', 'artifact:decision/' + manifest['decisions'][0]['id']):
            manifest['evidence'][0]['source_url'] = uri
            self.save(manifest)
            self.check()
        for uri in ('artifact:decision/missing', 'artifact:/private/key', 'artifact:context?secret=x'):
            manifest['evidence'][0]['source_url'] = uri
            self.save(manifest)
            self.fail()

    def test_evidence_urls_and_unknown_value(self):
        for url in ('https://user:secret@example.com/x', 'https://example.com/?token=secret',
                    'https://example.com/#x', 'https://@example.com/', 'https://example.com/?',
                    'https://example.com:invalid/', 'file:///tmp/x', None, 'https://exa mple.com'):
            manifest = write_stage(self.root, self.context, 'define')
            manifest['evidence'][0]['source_url'] = url
            self.save(manifest)
            self.fail()
        manifest = write_stage(self.root, self.context, 'define')
        manifest['evidence'][0].update(classification='unknown', value_or_range='0', source_url=None)
        self.save(manifest)
        self.fail()

    def test_reference_graph_and_cycles(self):
        for inputs in (['E-missing-1'], ['E-define-1'], ['E-define-2']):
            manifest = write_stage(self.root, self.context, 'define')
            manifest['evidence'][0]['input_ids'] = inputs
            if inputs == ['E-define-2']:
                other = copy.deepcopy(manifest['evidence'][0])
                other.update(id='E-define-2', input_ids=['E-define-1'])
                manifest['evidence'].append(other)
            self.save(manifest)
            self.fail()

    def test_claim_and_mvp_orphan_refs(self):
        manifest = write_stage(self.root, self.context, 'define')
        manifest['claims'][0]['decision_ids'] = ['missing']
        self.save(manifest)
        self.fail()
        write_stage(self.root, self.context, 'define')
        for stage in STAGES[1:]:
            manifest = write_stage(self.root, self.context, stage)
        manifest['requirements'][0]['evidence_ids'] = []
        self.save(manifest)
        self.fail('mvp')

    def test_prefix_tampering(self):
        manifest = write_stage(self.root, self.context, 'define')
        write_stage(self.root, self.context, 'market')
        manifest['claims'][0]['text'] = 'Altered interpretation'
        self.save(manifest)
        self.fail('market')

    def test_unknown_disposition_and_critical_gate(self):
        for stage in STAGES:
            manifest = write_stage(self.root, self.context, stage, unknown=(stage == 'define'), critical=True,
                                   recommendation='validate')
        self.check('mvp')
        manifest['verdict']['recommendation'] = 'plan'
        self.save(manifest)
        self.fail('mvp')
        manifest['verdict'].update(recommendation='validate', unresolved=[])
        self.save(manifest)
        self.fail('mvp')

    def test_resolutions_require_observation_and_accepted_adr(self):
        for stage in STAGES:
            manifest = write_stage(self.root, self.context, stage, unknown=(stage == 'define'), critical=True,
                                   recommendation='validate')
        resolution = dict(id='U-define-1', evidence_ids=['E-mvp-1'], decision_ids=[manifest['decisions'][0]['id']])
        manifest['verdict'].update(recommendation='plan', unresolved=[], resolutions=[resolution])
        self.save(manifest)
        self.check('mvp')
        manifest['evidence'][0].update(classification='hypothesis', input_ids=['E-define-1'])
        self.save(manifest)
        self.fail('mvp')

    def test_scope_app_ignored_and_head_changes(self):
        write_stage(self.root, self.context, 'define')
        for relative in ('README.md', 'app.py', 'ignored/secret.txt'):
            path = self.root / relative
            old = path.read_bytes() if path.exists() else None
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Changed', encoding='utf-8')
            self.fail()
            if old is None:
                path.unlink()
            else:
                path.write_bytes(old)
        subprocess.check_call(['git', '-C', str(self.root), 'commit', '--allow-empty', '-qm', 'Changed HEAD'])
        self.fail()

    def test_symlink_escape_and_invalid_pipeline(self):
        manifest = write_stage(self.root, self.context, 'define')
        report = self.root / manifest['report']['path']
        report.unlink()
        report.symlink_to(self.root / 'README.md')
        self.fail()
        with self.assertRaises(ValueError):
            pipeline_dir(self.root, '../escape')

    def test_duplicate_json_keys_and_oversize(self):
        write_stage(self.root, self.context, 'define')
        path = self.base / 'stages/define/stage.json'
        path.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
        self.fail()
        path.write_bytes(b' ' * 1048577)
        self.fail()

    def test_index_and_metadata_required(self):
        write_stage(self.root, self.context, 'define')
        (self.root / '.ai-development/INDEX.md').write_text('No decision', encoding='utf-8')
        self.fail()

    def test_adr_path_traversal_and_duplicate_evidence(self):
        manifest = write_stage(self.root, self.context, 'define')
        manifest['decisions'][0]['path'] = '../escape.md'
        self.save(manifest)
        self.fail()
        manifest = write_stage(self.root, self.context, 'define')
        manifest['evidence'].append(copy.deepcopy(manifest['evidence'][0]))
        self.save(manifest)
        self.fail()

    def test_non_regular_report_rejected_without_blocking(self):
        import os
        manifest = write_stage(self.root, self.context, 'define')
        report = self.root / manifest['report']['path']
        report.unlink()
        os.mkfifo(str(report))
        self.fail()

    def test_source_missing_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises((ValueError, OSError)):
                source_digest(temp)

    def test_cli_safe_receipt(self):
        manifest = write_stage(self.root, self.context, 'define')
        argv = ['python3', str(SKILLS_ROOT / 'orchestrator/product_artifacts.py'), '--root', str(self.root),
                '--pipeline', self.context['pipeline_id'], '--stage', 'define', '--context-sha', canonical_sha(self.context),
                '--skills-root', str(SKILLS_ROOT)]
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.decode(), 'PASS ' + canonical_sha(manifest) + '\n')
        manifest['evidence'][0]['source_url'] = 'https://user:DO-NOT-LEAK@example.com/'
        self.save(manifest)
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn(b'DO-NOT-LEAK', proc.stdout + proc.stderr)


if __name__ == '__main__':
    unittest.main()
