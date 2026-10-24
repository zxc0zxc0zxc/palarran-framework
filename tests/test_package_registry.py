"""Pure metadata and temporary-path registry checks; never installs packages."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from packages.core.packages.registry import PUBLIC_IDS, PUBLIC_TITLES, Registry, RegistryError, validate


ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return {"version": 1, "packages": [
        {"id": package_id, "title": PUBLIC_TITLES[package_id], "description": "Synthetic package",
         "requires": [] if package_id == "core" else ["core"],
         "capabilities": [{"id": "module", "status": "planned", "description": "Synthetic capability"}],
         "skills": []} for package_id in PUBLIC_IDS]}


def package(value, package_id):
    return next(item for item in value["packages"] if item["id"] == package_id)


def add_skill(value, package_id, name):
    result = {"name": name, "path": "packages/%s/module/skills/%s/SKILL.md" % (package_id, name),
              "legacy_path": "skills/%s/SKILL.md" % name}
    package(value, package_id)["skills"].append(result)
    return result


class PackageRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def assert_error(self, value, code):
        with self.assertRaises(RegistryError) as raised:
            validate(value)
        self.assertEqual(str(raised.exception), code)

    def test_public_inventory_all_eleven_and_51_single_owners(self):
        registry = Registry.load(ROOT / "packages/catalog.json")
        result = registry.resolve(list(PUBLIC_IDS))
        self.assertEqual(result["packages"], list(PUBLIC_IDS))
        self.assertEqual(len(result["skills"]), 51)
        expected = {"palarran-" + name for name in (
            "setup mcp-build memorize remember memorize-session remember-session memory-learn memory-recall vacuum "
            "product-define product-market product-compare product-revenue product-acquisition product-b2b product-b2c "
            "git-commit git-history git-conflicts git-mr ux-design ui-design frontend-plan frontend-build backend-plan backend-build "
            "ml-plan ml-hypotheses ml-model ml-data ml-cost ml-train ml-benchmark science-preprint "
            "agent-eval agent-improve app-verify infra-plan ci-cd vps-inspect vps-manage infrastructure-incident docs-artifact core-coop core-share security-infrastructure security-ingress security-log security-egress security-code security-cve"
        ).split()}
        self.assertEqual({skill["name"] for skill in result["skills"]}, expected)
        docs = package(registry.catalog, "docs")
        self.assertEqual([item["name"] for item in docs["skills"]], ["palarran-docs-artifact"])
        self.assertEqual(docs["capabilities"][0]["status"], "implemented")
        self.assertEqual({item["id"]: item["title"] for item in registry.catalog["packages"]}, PUBLIC_TITLES)

    def test_core_is_the_only_automatic_dependency_no_optional_services(self):
        registry = Registry.load(ROOT / "packages/catalog.json")
        for selected in PUBLIC_IDS:
            expected = ["core"] if selected == "core" else ["core", selected]
            self.assertEqual(registry.resolve([selected])["packages"], expected)
        self.assertEqual(registry.resolve(["science", "code"]), registry.resolve(["code", "science"]))
        self.assertNotIn("memory", registry.resolve(["code", "product", "infrastructure"])["packages"])

    def test_transitive_closure_dependency_order_and_dedup(self):
        value = fixture()
        package(value, "science")["requires"] += ["validation"]
        package(value, "validation")["requires"] += ["code"]
        for owner, name in (("core", "palarran-z"), ("core", "palarran-a"), ("code", "palarran-code")):
            add_skill(value, owner, name)
        result = Registry(value).resolve(["science", "validation"])
        self.assertEqual(result["packages"], ["core", "code", "validation", "science"])
        self.assertEqual([item["name"] for item in result["skills"]], ["palarran-a", "palarran-z", "palarran-code"])
        value["packages"].reverse()
        self.assertEqual(Registry(value).resolve(["validation", "science"]), result)

    def test_unknown_missing_and_duplicate_package_ids_titles(self):
        value = fixture()
        package(value, "code")["id"] = "unknown"
        self.assert_error(value, "unknown_package")
        value = fixture()
        value["packages"].pop()
        self.assert_error(value, "invalid_package_inventory")
        value = fixture()
        value["packages"][-1] = copy.deepcopy(value["packages"][0])
        self.assert_error(value, "duplicate_package")
        value = fixture()
        package(value, "machine-learning")["title"] = "ML"
        self.assert_error(value, "invalid_title")

    def test_dependency_cycles_unknowns_duplicates_and_core_rules(self):
        value = fixture()
        package(value, "code")["requires"] += ["design"]
        package(value, "design")["requires"] += ["code"]
        self.assert_error(value, "dependency_cycle")
        for dependencies, expected in ((["core", "missing"], "unknown_dependency"),
                                       (["core", "core"], "duplicate_dependency"),
                                       ([], "invalid_core_dependency"),
                                       (["core", "code"], "dependency_cycle")):
            value = fixture()
            package(value, "code")["requires"] = dependencies
            self.assert_error(value, expected)
        value = fixture()
        package(value, "core")["requires"] = ["code"]
        self.assert_error(value, "invalid_core_dependency")

    def test_duplicate_skill_owner_rejected_even_with_independent_valid_paths(self):
        value = fixture()
        add_skill(value, "code", "palarran-shared")
        add_skill(value, "design", "palarran-shared")
        self.assert_error(value, "duplicate_skill_owner")

    def test_capability_schema_and_ownership(self):
        value = fixture()
        skill = add_skill(value, "code", "palarran-example")
        skill["path"] = "packages/design/module/skills/palarran-example/SKILL.md"
        self.assert_error(value, "invalid_skill_path")
        skill["path"] = "packages/code/unknown/skills/palarran-example/SKILL.md"
        self.assert_error(value, "invalid_skill_path")
        for change, expected in (({"status": "available"}, "invalid_capability_status"),
                                 ({"id": "../escape"}, "invalid_identifier"),
                                 ({"description": ""}, "invalid_text")):
            value = fixture()
            package(value, "code")["capabilities"][0].update(change)
            self.assert_error(value, expected)
        value = fixture()
        package(value, "code")["capabilities"] *= 2
        self.assert_error(value, "duplicate_capability")

    def test_paths_are_exact_confined_and_never_legacy_fallback(self):
        invalid = ["/packages/code/module/skills/palarran-x/SKILL.md", "../outside/SKILL.md",
                   "packages/code/../module/skills/palarran-x/SKILL.md",
                   "packages/code//module/skills/palarran-x/SKILL.md",
                   "packages/code/./module/skills/palarran-x/SKILL.md",
                   "packages\\code\\module\\skills\\palarran-x\\SKILL.md"]
        for path in invalid:
            with self.subTest(path=path):
                value = fixture()
                add_skill(value, "code", "palarran-x")["path"] = path
                self.assert_error(value, "invalid_path")
        value = fixture()
        skill = add_skill(value, "code", "palarran-x")
        skill["legacy_path"] = "other/palarran-x/SKILL.md"
        self.assert_error(value, "invalid_skill_path")
        value = fixture()
        skill = add_skill(value, "code", "palarran-x")
        legacy = self.root / skill["legacy_path"]
        legacy.parent.mkdir(parents=True)
        legacy.write_text("Legacy source exists")
        registry = Registry(value)
        self.assertEqual(registry.resolve(["code"])["skills"], [skill])
        with self.assertRaisesRegex(RegistryError, "missing_skill_path"):
            registry.check_paths(self.root, ["code"])

    def test_explicit_path_checks_regular_files_and_selected_closure(self):
        value = fixture()
        selected = add_skill(value, "code", "palarran-x")
        add_skill(value, "science", "palarran-unmoved")
        file = self.root / selected["path"]
        file.parent.mkdir(parents=True)
        file.write_text("# Synthetic skill")
        registry = Registry(value)
        self.assertEqual(registry.check_paths(self.root, ["code"]), [selected["path"]])
        with self.assertRaisesRegex(RegistryError, "missing_skill_path"):
            registry.check_paths(self.root)
        file.unlink()
        file.mkdir()
        with self.assertRaisesRegex(RegistryError, "missing_skill_path"):
            registry.check_paths(self.root, ["code"])

    def test_path_symlink_file_directory_and_root_are_rejected(self):
        value = fixture()
        selected = add_skill(value, "code", "palarran-x")
        outside = self.root / "outside.md"
        outside.write_text("# Not inside the package")
        file = self.root / selected["path"]
        file.parent.mkdir(parents=True)
        file.symlink_to(outside)
        registry = Registry(value)
        with self.assertRaisesRegex(RegistryError, "symlink_path"):
            registry.check_paths(self.root, ["code"])
        file.unlink()
        outside_dir = self.root / "outside-dir"
        outside_dir.mkdir()
        file.parent.rmdir()
        file.parent.symlink_to(outside_dir, target_is_directory=True)
        with self.assertRaisesRegex(RegistryError, "symlink_path"):
            registry.check_paths(self.root, ["code"])
        root_link = self.root / "root-link"
        root_link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(RegistryError, "symlink_path"):
            registry.check_paths(root_link, ["docs"])

    def test_load_rejects_duplicate_nonfinite_oversized_and_symlink_catalogs(self):
        catalog = self.root / "catalog.json"
        for raw, expected in ((b'{"version":1,"version":1,"packages":[]}', "duplicate_key"),
                              (b'{"version":NaN,"packages":[]}', "nonfinite_value"),
                              (b'{"version":Infinity,"packages":[]}', "nonfinite_value"),
                              (b'{"version":'+b'1'*100+b',"packages":[]}', "invalid_number"),
                              (b'\xff', "invalid_json"), (b'[]', "invalid_fields"),
                              (b' '* (1024*1024+1), "catalog_too_large")):
            catalog.write_bytes(raw)
            with self.subTest(expected=expected), self.assertRaisesRegex(RegistryError, expected):
                Registry.load(catalog)
        catalog.write_text(json.dumps(fixture()))
        link = self.root / "linked.json"
        link.symlink_to(catalog)
        with self.assertRaisesRegex(RegistryError, "symlink_path"):
            Registry.load(link)

    def test_unknown_fields_hooks_boolean_version_and_selection_rejected(self):
        for value, expected in (({**fixture(), "hooks": ["execute"]}, "invalid_fields"),
                                ({**fixture(), "version": True}, "unsupported_version"),
                                ({**fixture(), "version": 1.0}, "unsupported_version")):
            self.assert_error(value, expected)
        value = fixture()
        package(value, "core")["install"] = "arbitrary command"
        self.assert_error(value, "invalid_fields")
        registry = Registry(fixture())
        for selection, expected in (([], "invalid_selection"), ("code", "invalid_selection"),
                                    (["missing"], "unknown_package"), ([True], "unknown_package"),
                                    (["core", "core"], "duplicate_selection")):
            with self.subTest(selection=selection), self.assertRaisesRegex(RegistryError, expected):
                registry.resolve(selection)

    def test_catalog_and_resolve_results_cannot_mutate_registry(self):
        value = fixture()
        add_skill(value, "code", "palarran-x")
        registry = Registry(value)
        value["packages"].clear()
        detached = registry.catalog
        detached["packages"].clear()
        result = registry.resolve(["code"])
        result["skills"][0]["path"] = "modified"
        self.assertEqual(registry.resolve(["code"])["skills"][0]["path"],
                         "packages/code/module/skills/palarran-x/SKILL.md")

    def test_planned_documentation_is_declaration_only_with_no_fake_skill(self):
        registry = Registry(fixture())
        self.assertEqual(registry.resolve(["docs"]), {"packages": ["core", "docs"], "skills": []})
        self.assertEqual(registry.check_paths(self.root, ["docs"]), [])


if __name__ == "__main__":
    unittest.main()
