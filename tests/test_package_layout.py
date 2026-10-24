"""Offline package migration coverage, with physically moved synthetic source trees."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
# The root shim remains the stable CLI entrypoint after physical migration.
sys.path.insert(0,str(REPO/'scripts'))
from palarran_paths import source_path
spec=importlib.util.spec_from_file_location('layout_validator', source_path(REPO,'scripts/validate_repo.py'))
validator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write(root, relative, text):
    path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8');return path


def dump(root, relative, data):
    return write(root,relative,json.dumps(data))


def fixture(root, modular=False):
    name='palarran-setup'
    row={'skill':name,'domain':'skills','action':'setup','adapter':'commands/palarran/setup.md'}
    dump(root,'skills/catalog.json',{'version':1,'skills':[row]})
    write(root,'AGENTS.md','# Root instructions\n')
    for area in ('memory','mcp','orchestrator','scripts','tests','skills','docs','templates','plugins','examples'):
        write(root,area+'/AGENTS.md','# Module instructions\n')
    for relative in ('docs/skills/agents-authoring.md','docs/skills/graph-context.md','docs/skills/domain-contracts.md',
                     'docs/skills/global-memory.md','docs/skills/decision-memory.md','docs/setup/README.md','docs/setup/skill.md',
                     'templates/agents/root.md','templates/agents/module.md','templates/ml/learning-contract.md','templates/ml/data-goal-audit.md'):
        write(root,relative,'# Synthetic contract\n')
    skill_body='---\nname: '+name+'\ndescription: Synthetic setup skill.\n---\n'
    for guide in ('skills/global-memory.md','skills/decision-memory.md','setup/README.md','setup/skill.md'):
        skill_body+='[Guide](../../docs/'+guide+')\n'
    write(root,'skills/'+name+'/SKILL.md',skill_body)
    # Existing portable namespace contract is intentionally independent of this minimal skill registry.
    for namespace,relative,commands in validator.MANIFEST_SPECS:
        command_rows={}
        for command in commands:
            source=row['adapter'] if command=='setup' else 'commands/synthetic/'+namespace+'/'+command.replace(':','-')+'.md'
            command_rows[command]={'source':'./'+source}
            write(root,source,'# Synthetic adapter\n')
        dump(root,relative,{'name':namespace,'commands':command_rows})
    write(root,row['adapter'],'$ARGUMENTS\n[Skill](../../skills/'+name+'/SKILL.md)\n[Memory](../../docs/skills/global-memory.md)\n[Decisions](../../docs/skills/decision-memory.md)\n')
    # Adapter is two levels below root, matching its actual lexical location.
    for level in ('low','med','high'):
        write(root,'docs/infra/plan/'+level+'.md','```mermaid\nflowchart TD\n A --> B\n```\n'*2)
    ui=validator.source_path(REPO,'docs/ui/catalog.json')
    dump(root,'docs/ui/catalog.json',json.loads(ui.read_text()))
    if not modular:return
    moves={'skills/catalog.json':'packages/core/packages/catalog/skills.json',
           'skills/'+name:'packages/core/setup/skills/'+name,
           'docs/skills':'packages/core/agents/docs', 'docs/setup':'packages/core/setup/docs',
           'docs/infra/plan':'packages/infrastructure/planning/docs',
           'docs/ui':'packages/design/ui/docs', 'templates/agents':'packages/core/agents/templates',
           'templates/ml':'packages/machine-learning/experiments/templates',
           row['adapter']:'packages/core/setup/commands/setup.md'}
    for legacy,canonical in moves.items():
        source=root/legacy;target=root/canonical;target.parent.mkdir(parents=True,exist_ok=True);shutil.move(source,target)
    # Plugin declarations may themselves be relocated and retain legacy source refs.
    plug='plugins/palarran-setup'
    target='packages/core/setup/plugins/palarran-setup'
    (root/target).parent.mkdir(parents=True,exist_ok=True);shutil.move(root/plug,root/target);moves[plug]=target
    dump(root,'packages/layout.json',{'version':1,'moves':moves})
    catalog={'version':1,'packages':[{'id':'core','title':'Core','description':'Synthetic package',
        'requires':[],'capabilities':[{'id':'setup','status':'implemented','description':'Synthetic setup'}],
        'skills':[{'name':name,'path':'packages/core/setup/skills/'+name+'/SKILL.md','legacy_path':'skills/'+name+'/SKILL.md'}]}]}
    dump(root,'packages/catalog.json',catalog);write(root,'packages/core/AGENTS.md','# Package instructions\n')
    write(root,'packages/core/setup/skills/'+name+'/SKILL.md','---\nname: '+name+'\ndescription: Synthetic setup skill.\n---\n'+
          '[Global](../../../agents/docs/global-memory.md)\n[Decisions](../../../agents/docs/decision-memory.md)\n[Readme](../../docs/README.md)\n[Workflow](../../docs/skill.md)\n')
    write(root,'packages/core/setup/commands/setup.md','$ARGUMENTS\n[Skill](../skills/'+name+'/SKILL.md)\n[Global](../../agents/docs/global-memory.md)\n[Decisions](../../agents/docs/decision-memory.md)\n')


class PackageLayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def errors(self):return validator.validate(self.root)[0]

    def test_legacy_no_catalog_or_layout_still_validates(self):
        fixture(self.root)
        self.assertEqual(self.errors(),[])
        self.assertEqual(validator._inventory(self.root)[2]['palarran-setup'],self.root/'skills/palarran-setup/SKILL.md')

    def test_physical_moves_catalog_guides_templates_adapter_plugin_and_package_links(self):
        fixture(self.root,True)
        self.assertFalse((self.root/'skills/palarran-setup').exists())
        self.assertFalse((self.root/'docs/skills').exists())
        self.assertTrue((self.root/'packages/core/setup/docs/skill.md').is_file())
        self.assertEqual(self.errors(),[])
        write(self.root,'packages/core/setup/docs/extra.md','[Missing](missing.md)\n')
        self.assertTrue(any('packages/core/setup/docs/extra.md' in error and 'missing.md' in error for error in self.errors()))

    def test_catalog_coverage_rejects_unlisted_nested_skill_and_legacy_shadow(self):
        fixture(self.root,True)
        write(self.root,'packages/core/setup/skills/palarran-surprise/SKILL.md','# Unregistered\n')
        self.assertTrue(any('cover every canonical skill' in error for error in self.errors()))
        shutil.rmtree(self.root/'packages/core/setup/skills/palarran-surprise')
        write(self.root,'skills/palarran-setup/SKILL.md','# Shadow\n')
        self.assertTrue(any('legacy skill shadows' in error for error in self.errors()))

    def test_missing_canonical_never_uses_existing_legacy(self):
        fixture(self.root,True)
        (self.root/'packages/core/setup/skills/palarran-setup/SKILL.md').unlink()
        write(self.root,'skills/palarran-setup/SKILL.md','# Shadow\n')
        self.assertIn('Missing skill: palarran-setup',self.errors())

    def test_catalog_and_layout_must_agree_and_owners_cannot_duplicate(self):
        fixture(self.root,True)
        path=self.root/'packages/catalog.json';value=json.loads(path.read_text())
        value['packages'][0]['skills'][0]['path']='packages/core/setup/skills/palarran-setup-other/SKILL.md'
        path.write_text(json.dumps(value));self.assertIn('Invalid skill registry, package catalog or source layout',self.errors())
        fixture_root=self.root/'second';fixture_root.mkdir();fixture(fixture_root,True)
        path=fixture_root/'packages/catalog.json';value=json.loads(path.read_text())
        value['packages'][0]['skills']*=2;path.write_text(json.dumps(value))
        self.assertIn('Invalid skill registry, package catalog or source layout',validator.validate(fixture_root)[0])

    def test_dynamic_instruction_budgets_and_missing_package_boundary(self):
        fixture(self.root,True)
        write(self.root,'packages/core/setup/AGENTS.md','x'*4097)
        self.assertIn('Instruction budget exceeded or empty: packages/core/setup/AGENTS.md',self.errors())
        (self.root/'packages/core/AGENTS.md').unlink()
        self.assertIn('Missing regular instruction file: packages/core/AGENTS.md',self.errors())

    def test_stale_relative_guides_and_plugin_source_fail_after_move(self):
        fixture(self.root,True)
        path=self.root/'packages/core/setup/skills/palarran-setup/SKILL.md'
        path.write_text(path.read_text().replace('../../../agents/docs/global-memory.md','../../../../../../docs/skills/global-memory.md'))
        self.assertIn('palarran-setup: missing automatic global-memory cycle',self.errors())
        plug=self.root/'packages/core/setup/plugins/palarran-setup/plugin.json';value=json.loads(plug.read_text())
        value['commands']['setup']['source']='./commands/missing.md';plug.write_text(json.dumps(value))
        self.assertIn('Invalid plugin command source: palarran-setup',self.errors())

    def test_malformed_duplicate_and_unsafe_layout_are_explicit_errors(self):
        fixture(self.root,True)
        for raw in ('{"version":1,"version":1,"packages":[]}', '{invalid', '{"version":1,"packages":[]}'):
            (self.root/'packages/catalog.json').write_text(raw)
            self.assertIn('Invalid skill registry, package catalog or source layout',self.errors())
        (self.root/'packages/layout.json').write_text('{"version":1,"moves":{"docs":"../escape"}}')
        self.assertIn('Invalid skill registry, package catalog or source layout',self.errors())

    def test_canonical_symlinks_and_escaping_markdown_links_fail(self):
        fixture(self.root,True)
        path=self.root/'packages/core/setup/skills/palarran-setup/SKILL.md';original=path.read_text();path.unlink()
        outside=write(self.root,'elsewhere.md',original);path.symlink_to(outside)
        self.assertIn('Invalid skill registry, package catalog or source layout',self.errors())
        path.unlink();path.write_text(original)
        write(self.root,'packages/core/setup/docs/escape.md','[Escape](../../../../../../outside.md)\n')
        self.assertTrue(any('escape.md: broken or unsafe link' in error for error in self.errors()))


if __name__=='__main__':unittest.main()
