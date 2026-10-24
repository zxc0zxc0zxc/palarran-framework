"""Offline canonical-source integrity and legacy-fixture compatibility."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from scripts.palarran_paths import repository_root, source_path
from orchestrator import context_packet, product_pipeline
from orchestrator.product_artifacts import source_digest as product_digest
from orchestrator.ml_artifacts import source_digest as ml_digest

ROOT=repository_root(__file__)


def fixture_moves():
    moves={'docs/product':'packages/product/research/docs','templates/product':'packages/product/research/templates',
           'docs/ml':'packages/machine-learning/experiments/docs','templates/ml':'packages/machine-learning/experiments/templates',
           'docs/skills':'packages/core/agents/docs'}
    for profile in ('define','market','compare','revenue','acquisition','b2b','b2c'):
        name='palarran-product-'+profile;moves['skills/'+name]='packages/product/research/skills/'+name
    for profile in ('hypotheses','plan','model','data','cost','train','benchmark'):
        name='palarran-ml-'+profile;moves['skills/'+name]='packages/machine-learning/experiments/skills/'+name
    for name in ('ml_artifacts.py','ml_pipeline.py','ml_resources.py','modal_adapter.py','ml_data_gate.py','ml_diagnostics.py'):
        moves['orchestrator/'+name]='packages/machine-learning/experiments/runtime/'+name
    for name in ('product_artifacts.py','context_packet.py'):
        moves['orchestrator/'+name]='packages/product/research/runtime/'+name
    for name in ('ml_data.py','science_preprint.py'):
        moves['scripts/'+name]='packages/test/scripts/'+name
    return moves


class LayoutRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.moves=fixture_moves()
        # Copy only public pinned sources; no code is launched from these fixtures.
        for legacy in self.moves:
            selected=source_path(ROOT,legacy)
            target=self.root/legacy;target.parent.mkdir(parents=True,exist_ok=True)
            if selected.is_dir():shutil.copytree(selected,target)
            else:shutil.copyfile(selected,target)

    def canonicalize(self):
        (self.root/'packages').mkdir(exist_ok=True)
        (self.root/'packages/layout.json').write_text(json.dumps({'version':1,'moves':self.moves}))
        for old,new in self.moves.items():
            target=self.root/new;target.parent.mkdir(parents=True,exist_ok=True)
            source=self.root/old
            if source.is_dir():shutil.copytree(source,target)
            else:shutil.copyfile(source,target)

    def test_legacy_fixture_hashes_still_track_legacy_sources(self):
        for digest,path in ((product_digest,'docs/product/README.md'),(ml_digest,'docs/ml/README.md')):
            before=digest(self.root)
            source=self.root/path;source.write_bytes(source.read_bytes()+b'\nfixture change\n')
            self.assertNotEqual(before,digest(self.root))

    def test_canonical_digests_ignore_redirect_shims_and_track_real_sources(self):
        self.canonicalize()
        for digest,legacy in ((product_digest,'docs/product/README.md'),(ml_digest,'docs/ml/README.md'),
                              (ml_digest,'orchestrator/ml_data_gate.py')):
            before=digest(self.root)
            old=self.root/legacy;old.write_bytes(b'legacy redirect changed\n')
            self.assertEqual(before,digest(self.root))
            canonical=source_path(self.root,legacy)
            canonical.write_bytes(canonical.read_bytes()+b'\ncanonical changed\n')
            self.assertNotEqual(before,digest(self.root))

    def test_missing_selected_source_never_falls_back_to_legacy(self):
        self.canonicalize();canonical=source_path(self.root,'skills/palarran-product-define/SKILL.md')
        canonical.unlink()
        self.assertTrue((self.root/'skills/palarran-product-define/SKILL.md').exists())
        with self.assertRaises((ValueError,OSError)):product_digest(self.root)

    def test_canonical_symlink_is_rejected(self):
        self.canonicalize();canonical=source_path(self.root,'docs/product/README.md')
        canonical.unlink();canonical.symlink_to(self.root/'docs/product/README.md')
        with self.assertRaises(ValueError):product_digest(self.root)

    def test_product_prompts_and_verifier_reference_canonical_sources(self):
        self.canonicalize()
        flow,context=product_pipeline.build('Fixture idea',self.root,'codex','/fake/codex',baseline='a'*40)
        first=flow['tasks'][0]
        verifier=str(source_path(self.root,'orchestrator/product_artifacts.py'))
        self.assertEqual(first['verify'][0][1],verifier)
        self.assertIn(str(source_path(self.root,'skills/palarran-product-define/SKILL.md')),first['prompt'])
        self.assertIn(str(source_path(self.root,'docs/product/pipeline-contract.md')),first['prompt'])
        self.assertEqual(context['source_digest'],product_digest(self.root))

    def test_packet_materializes_canonical_guide_not_redirect(self):
        self.canonicalize();pipeline='1'*32
        skill=source_path(self.root,'skills/palarran-product-market/SKILL.md')
        guide=source_path(self.root,'docs/product/market.md')
        skill.write_text('[Guide]('+os.path.relpath(guide,skill.parent)+')\n')
        guide.write_text('Canonical full guide fixture\n')
        (self.root/'docs/product/market.md').write_text('Wrong redirect fixture\n')
        relative='.palarran/product/pipeline-'+pipeline
        report=self.root/relative/'stages/define/report.md';report.parent.mkdir(parents=True);report.write_text('Saved brief')
        manifest={'report':{},'claims':[],'unknowns':[],'decisions':[],'evidence':[]}
        with mock.patch.object(context_packet,'validate_stage'),mock.patch.object(context_packet,'load_json',return_value=manifest):
            name,data=context_packet.packet(self.root,pipeline,'market','a'*64,self.root,'b2b')
        self.assertIn(b'Canonical full guide fixture',data)
        self.assertNotIn(b'Wrong redirect fixture',data)
        self.assertIn(guide.relative_to(self.root).as_posix().encode(),data)

    def test_actual_canonical_checkout_sources(self):
        root=Path(os.environ.get('PALARRAN_LAYOUT_CHECK_ROOT',ROOT)).resolve()
        if not (root/'packages/layout.json').is_file():self.skipTest('Canonical layout not present in legacy fixture checkout')
        selected=source_path(root,'docs/product/README.md',required=True)
        self.assertTrue(selected.relative_to(root).as_posix().startswith('packages/'))
        self.assertEqual(len(product_digest(root)),64)
        self.assertEqual(len(ml_digest(root)),64)


if __name__=='__main__':unittest.main()
