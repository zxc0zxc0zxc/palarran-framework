"""Offline preferences, selected discovery and update scope regressions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import palarran_config as config
import project_setup
from scripts.palarran_paths import source_path


class ConfigurationTests(unittest.TestCase):
    def test_precedence_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp).resolve(); target=home/"project"; target.mkdir()
            (home/".palarran").mkdir(); (target/".palarran").mkdir()
            (home/".palarran/config.json").write_text(json.dumps(dict(version=1,packages=["backend"],languages=dict(skills="ru",code="en",docs="en"),extension=dict(enabled=True))))
            (target/".palarran/config.json").write_text(json.dumps(dict(languages=dict(docs="sr-Latn"))))
            result=config.resolve(target,languages=dict(skills="en"),home=home)
            self.assertEqual(result["languages"],dict(skills="en",code="en",docs="sr-Latn"))
            self.assertEqual(result["packages"],["backend"])
            self.assertEqual(result["extension"],dict(enabled=True))

    def test_reject_malformed_duplicate_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/"config.json"
            for raw in ('{"version":1,"version":1}','{"languages":{"docs":"sr"}}','{"packages":[]}','[]'):
                p.write_text(raw)
                with self.assertRaises(ValueError):config.read(p)
            link=p.with_name("link"); link.symlink_to(p)
            with self.assertRaises(ValueError):config.read(link)

    def test_selected_skills_and_management_entrypoint(self):
        root=Path(__file__).resolve().parents[1]
        bundle={"skills/catalog.json":source_path(root,"skills/catalog.json",required=True).read_bytes(),"docs/shared.md":b"support"}
        rows=json.loads(bundle["skills/catalog.json"])["skills"]
        for row in rows:
            reference="skills/"+row["skill"]+"/SKILL.md"
            bundle[reference]=source_path(root,reference,required=True).read_bytes()
        selected=config.selected(bundle,["backend"])
        names={Path(n).parent.name for n in selected if n.endswith("/SKILL.md")}
        self.assertEqual(names,{"palarran-backend-plan","palarran-backend-build","palarran-setup"})
        self.assertIn("docs/shared.md",selected)
        for choices in (["unknown"],["all","backend"]):
            with self.assertRaises(ValueError):config.selected(bundle,choices)

    def test_plan_does_not_write_configuration(self):
        from unittest.mock import patch
        root=Path(__file__).resolve().parents[1]
        bundle={"skills/catalog.json":source_path(root,"skills/catalog.json",required=True).read_bytes(),"skills/palarran-setup/SKILL.md":b"setup","skills/palarran-backend-plan/SKILL.md":b"plan","scripts/memory_ops.py":b"helper"}
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp).resolve()
            with patch.object(project_setup,"library",return_value=("a"*40,bundle)):
                result=project_setup.install(root,target,"codex",True,dict(version=1,packages=["backend"],languages=dict(skills="ru",code="en",docs="sr-Latn")))
            self.assertEqual(result["status"],"PLANNED")
            self.assertEqual(list(target.iterdir()),[])


class ModularConfigurationTests(unittest.TestCase):
    def bundle(self):
        root = Path(__file__).resolve().parents[1]
        raw = (root / "packages/catalog.json").read_bytes()
        value = json.loads(raw)
        return {"packages/catalog.json": raw, "docs/shared.md": b"support",
                **{skill["legacy_path"]: b"synthetic skill" for package in value["packages"] for skill in package["skills"]}}

    def test_exact_public_ids_dependency_closure_and_no_legacy_fresh_selection(self):
        bundle = self.bundle()
        chosen = config.selected(bundle, ["code"])
        names = {Path(name).parent.name for name in chosen if name.endswith("/SKILL.md")}
        catalog=json.loads(bundle["packages/catalog.json"])
        expected={skill["name"] for package in catalog["packages"] if package["id"] in ("core","code") for skill in package["skills"]}
        self.assertEqual(names,expected)
        self.assertIn("docs/shared.md", chosen)
        for invalid in (["backend"], ["palarran-code"], ["all", "code"], ["unknown"]):
            with self.assertRaises(ValueError): config.selected(bundle, invalid)

    def test_legacy_receipts_preserve_overlapping_ids_without_adding_core_skill(self):
        bundle = self.bundle()
        old = config.selected(bundle, ["memory"], legacy_receipt=True)
        modern = config.selected(bundle, ["memory"])
        self.assertNotIn("skills/palarran-mcp-build/SKILL.md", old)
        self.assertIn("skills/palarran-mcp-build/SKILL.md", modern)
        backend = config.selected(bundle, ["backend"], legacy_receipt=True)
        self.assertIn("skills/palarran-backend-build/SKILL.md", backend)
        self.assertNotIn("skills/palarran-frontend-build/SKILL.md", backend)

    def test_missing_declared_skill_cannot_be_claimed_installed(self):
        bundle = self.bundle(); del bundle["skills/palarran-mcp-build/SKILL.md"]
        with self.assertRaises(ValueError): config.selected(bundle, ["code"])
