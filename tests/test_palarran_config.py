"""Offline preferences, selected discovery and update scope regressions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import palarran_config as config
import project_setup


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
        bundle={"skills/catalog.json":(root/"skills/catalog.json").read_bytes(),"docs/shared.md":b"support"}
        for p in (root/"skills").glob("*/SKILL.md"):
            bundle[str(p.relative_to(root))]=p.read_bytes()
        selected=config.selected(bundle,["backend"])
        names={Path(n).parent.name for n in selected if n.endswith("/SKILL.md")}
        self.assertEqual(names,{"palarran-backend-plan","palarran-backend-build","palarran-setup"})
        self.assertIn("docs/shared.md",selected)
        for choices in (["unknown"],["all","backend"]):
            with self.assertRaises(ValueError):config.selected(bundle,choices)

    def test_plan_does_not_write_configuration(self):
        from unittest.mock import patch
        root=Path(__file__).resolve().parents[1]
        bundle={"skills/catalog.json":(root/"skills/catalog.json").read_bytes(),"skills/palarran-setup/SKILL.md":b"setup","skills/palarran-backend-plan/SKILL.md":b"plan","scripts/memory_ops.py":b"helper"}
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp).resolve()
            with patch.object(project_setup,"library",return_value=("a"*40,bundle)):
                result=project_setup.install(root,target,"codex",True,dict(version=1,packages=["backend"],languages=dict(skills="ru",code="en",docs="sr-Latn")))
            self.assertEqual(result["status"],"PLANNED")
            self.assertEqual(list(target.iterdir()),[])
