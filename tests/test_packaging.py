"""Offline portability and containment tests against real package contents."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("packaging_tool", ROOT / "scripts/package_plugin.py")
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


class PackagingTest(unittest.TestCase):
    def test_packages_resolve_skill_docs_and_command_paths_without_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            for namespace in packager.PUBLIC_GROUPS:
                expected = len(packager.registry(ROOT).resolve([namespace])["skills"])
                package = packager.build_package(namespace, Path(directory) / namespace, root=ROOT).resolve()
                manifest = json.loads((package / ".claude-plugin/plugin.json").read_text())
                self.assertEqual(manifest["name"], packager.ALIASES[namespace])
                self.assertEqual(len(list((package / "skills").iterdir())), expected)
                for item in manifest["commands"].values():
                    self.assertTrue((package / item["source"]).is_file())
                for source in package.rglob("*.md"):
                    for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", source.read_text()):
                        if target.startswith(("http:", "https:", "#", "mailto:")):
                            continue
                        destination = (source.parent / target.split("#", 1)[0]).resolve()
                        self.assertTrue(destination.is_relative_to(package), (source, target))
                        self.assertTrue(destination.exists(), (source, target))
                self.assertFalse(any(path.is_symlink() for path in package.rglob("*")))
                self.assertFalse((package / ".palarran").exists())
                self.assertFalse((package / ".git").exists())
                self.assertTrue((package / 'docs/skills/global-memory.md').is_file())
                self.assertTrue((package / 'templates/memory/lesson.example.json').is_file())
                checked = subprocess.run([sys.executable, str(package/'scripts/memory_cycle.py'), '--help'], cwd=directory, capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                search_check = subprocess.run([sys.executable, str(package/'scripts/keenable_auth.py'), 'check', '--plan'], cwd=directory, capture_output=True, text=True)
                self.assertEqual(search_check.returncode, 0, search_check.stderr)
                self.assertEqual(json.loads(search_check.stdout)['network'], False)
                if namespace == "core":
                    for helper in ("project_setup.py", "project_update.py"):
                        self.assertTrue((package/"scripts"/helper).is_file())
                    checked = subprocess.run([sys.executable, str(package/"scripts/project_setup.py"), "--help"], cwd=directory, capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertIn("setup", checked.stdout)
                    coordination = subprocess.run([sys.executable, "-m", "packages.core.coordination.client", "check", "--plan"], cwd=package, capture_output=True, text=True)
                    self.assertEqual(coordination.returncode, 0, coordination.stderr)
                    self.assertFalse(json.loads(coordination.stdout)["network"])
                if namespace in {"design", "code"}:
                    catalog = json.loads((package / "docs/ui/catalog.json").read_text())
                    self.assertEqual(len(catalog["systems"]), 10)
                    self.assertIn("custom", catalog["selection_modes"])
                    tokens = json.loads((package / "templates/ui/tokens.example.json").read_text())
                    self.assertEqual(tokens["schema_version"], 1)
                    self.assertEqual((package / "skills/palarran-ux-design/SKILL.md").is_file(), namespace == "design")
                if namespace in {"memory", "infrastructure"}:
                    self.assertTrue((package/'memory/service.py').is_file())
                    for tool in ('memory_ops.py','vps_ops.py'):
                        checked=subprocess.run([sys.executable,str(package/'scripts'/tool),'--help'],cwd=directory,capture_output=True,text=True)
                        self.assertEqual(checked.returncode,0,checked.stderr)
                    private=Path(directory).resolve()/('private-'+namespace+'.env')
                    checked=subprocess.run([sys.executable,str(package/'scripts/memory_ops.py'),'env-init','--env',str(private)],cwd=directory,capture_output=True,text=True)
                    self.assertEqual(checked.returncode,0,checked.stderr)
                    self.assertEqual(private.stat().st_mode & 0o777,0o600)
                    self.assertNotIn('REPLACE_WITH_RANDOM_AGENT_TOKEN',private.read_text())
                if namespace == "core":
                    self.assertTrue((package / "mcp/catalog/server.py").is_file())
                    checked=subprocess.run([sys.executable,str(package/"scripts/mcp_build.py"),"--help"],cwd=directory,capture_output=True,text=True)
                    self.assertEqual(checked.returncode,0,checked.stderr)
                    generated=Path(directory).resolve()/"mcp-reference"
                    for args in (["scaffold","--spec",str(package/"templates/mcp/catalog.example.json"),"--output",str(generated)],["smoke","--project",str(generated)]):
                        checked=subprocess.run([sys.executable,str(package/"scripts/mcp_build.py")]+args,cwd=directory,capture_output=True,text=True,timeout=15)
                        self.assertEqual(checked.returncode,0,checked.stderr)
                    self.assertFalse((package / "orchestrator").exists())
                if namespace == "validation":
                    for name in ('app_verify.py','app_verify_browser.cjs','ml_data.py'):
                        self.assertTrue((package/'scripts'/name).is_file())
                    checked=subprocess.run([sys.executable,str(package/'scripts/app_verify.py'),'--help'],cwd=directory,capture_output=True,text=True)
                    self.assertEqual(checked.returncode,0,checked.stderr)
                    self.assertFalse((package/'orchestrator').exists())
                if namespace == "validation":
                    self.assertTrue((package / "templates/palarran-agent-improve/review.md").is_file())
                    self.assertTrue((package / "templates/palarran-agent-improve/incident.example.json").is_file())
                    self.assertTrue((package / "skills/palarran-agent-improve/SKILL.md").is_file())
                    self.assertTrue((package / "templates/palarran-agent-eval/protocol.md").is_file())
                    self.assertTrue((package / "docs/agent/eval/contract.md").is_file())
                    self.assertFalse((package / "orchestrator").exists())
                if namespace == "machine-learning":
                    self.assertEqual({key for key in manifest["commands"] if key.startswith("ml:")}, {"ml:" + key for key in ("plan", "hypotheses", "model", "data", "cost", "train", "benchmark")})
                    self.assertFalse((package / "orchestrator").exists())
                    self.assertFalse((package / "docs/product").exists())
                    for resource in ("data-plan.md", "data-prepare.example.json", "token-audit.example.json", "data-mixture.example.json", "data-preparation.example.json"):
                        self.assertTrue((package / "templates/ml" / resource).is_file())
                    source = Path(directory).resolve() / 'public-synthetic.jsonl'
                    source.write_text(json.dumps(dict(id='fixture',group_id='fixture',source_id='synthetic-owned',domain='general',language='en',license='CC0-1.0',rights_status='approved',rights_approval='fixture-owner',text='Synthetic public fixture.'))+'\n')
                    output = Path(directory).resolve() / 'packaged-data-profile.json'
                    data_check = subprocess.run([sys.executable,str(package/'scripts/ml_data.py'),'profile','--input',str(source),'--output',str(output)],capture_output=True,text=True)
                    self.assertEqual(data_check.returncode,0,data_check.stderr)
                    self.assertEqual(json.loads(output.read_text())['records'],1)
                    self.assertIsNone(json.loads(output.read_text())['tokens'])
                    checked = subprocess.run([
                        sys.executable, str(package / "scripts/ml_cost.py"),
                        str(package / "templates/ml/cost.example.json"),
                    ], capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    report = json.loads(checked.stdout)
                    self.assertIsNone(report["within_budget"])
                    self.assertFalse(report["launch_authorized"])
                if namespace == "product":
                    self.assertEqual({key for key in manifest["commands"] if key.startswith("product:")}, {"product:" + key for key in ("define", "market", "compare", "revenue", "acquisition", "b2b", "b2c")})
                    self.assertTrue((package / "docs/product/cases/revenue-economics.md").is_file())
                    self.assertTrue((package / "templates/product/channels.md").is_file())
                    self.assertFalse((package / "orchestrator").exists())
                    self.assertFalse((package / "docs/backend").exists())
                if namespace == "code":
                    self.assertTrue({"frontend:plan", "frontend:build", "backend:plan", "backend:build"}.issubset(manifest["commands"]))
                    self.assertTrue((package / "skills/palarran-frontend-plan/SKILL.md").is_file())
                    for resource in ["spec.md", "api-contract.md", "test-matrix.md", "planning-handoff.md"]:
                        self.assertTrue((package / "templates/frontend" / resource).is_file())
                    self.assertFalse((package / "skills/palarran-ui-design/SKILL.md").exists())
                    self.assertTrue((package / "templates/frontend/browser-review.md").is_file())
                    self.assertTrue((package / "docs/backend").is_dir())
                    target = Path(directory) / "palarran-frontend-plan.md"
                    target.write_text((package / "templates/frontend/plan.md").read_text())
                    checked = subprocess.run([
                        sys.executable, str(package / "scripts/execution_progress.py"),
                        str(package / "templates/frontend/progress.example.json"),
                        "--area", "frontend", "--plan", str(target),
                    ], capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertIn("INCOMPLETE", target.read_text())
                    self.assertIn("Requirements and design mapping", target.read_text())
                if namespace == "code":
                    self.assertTrue({"frontend:plan", "frontend:build", "backend:plan", "backend:build"}.issubset(manifest["commands"]))
                    self.assertTrue((package / "templates/backend/reliability.md").is_file())
                    self.assertTrue((package / "templates/backend/agent-task.md").is_file())
                    self.assertTrue((package / "scripts/backend_progress.py").is_file())
                    self.assertTrue((package / "templates/backend/progress.example.json").is_file())
                    self.assertFalse((package / "scripts/infra_inventory.py").exists())
                    self.assertTrue((package / "docs/ui").is_dir())
                    target_plan = Path(directory) / "target-plan.md"
                    target_plan.write_text((package / "templates/backend/plan.md").read_text())
                    checked = subprocess.run([
                        sys.executable, str(package / "scripts/backend_progress.py"),
                        str(package / "templates/backend/progress.example.json"),
                        "--plan", str(target_plan),
                    ], capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertIn("INCOMPLETE", target_plan.read_text())
                    self.assertIn("Architecture and implementation shape", target_plan.read_text())
                self.assertFalse(any(path.name in {".terraform", ".env", "node_modules"} for path in package.rglob("*")))


    def test_core_commands_do_not_expand_from_a_dependency_mention(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()/"source";root.mkdir()
            catalog=json.loads((ROOT/"packages/catalog.json").read_text())
            moves={}
            for package in catalog["packages"]:
                for skill in package["skills"]:
                    path=root/skill["path"];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# '+skill["name"]+'\n')
                    moves[skill["legacy_path"]]=skill["path"]
            resources={"packages/catalog.json":json.dumps(catalog),
                       "packages/layout.json":json.dumps({"version":1,"moves":moves}),
                       "packages/core/packages/registry.py":"# fixture metadata\n",
                       "packages/core/packages/__init__.py":"",
                       "scripts/palarran_paths.py":"# fixture bootstrap\n",
                       "packages/core/coop/docs/README.md":"# fixture\n", "packages/core/coop/daemon.py":"# fixture\n",
                       "plugins/palarran/plugin.json":json.dumps({"name":"palarran","commands":{
                           "backend:plan":{"source":"./commands/backend.md"},"mcp:build":{"source":"./commands/mcp.md"}}}),
                       "commands/backend.md":"Use skills/palarran-backend-plan/SKILL.md; dependency skills/palarran-setup/SKILL.md\n",
                       "commands/mcp.md":"Use skills/palarran-mcp-build/SKILL.md\n"}
            for name,raw in resources.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(raw)
            def minimal_group(namespace,output,source):
                output.mkdir();return output
            with mock.patch.object(packager,"_legacy_package",side_effect=minimal_group):
                package=packager.build_package("core",Path(directory)/"package",root=root)
            manifest=json.loads((package/".claude-plugin/plugin.json").read_text())
            self.assertEqual(set(manifest["commands"]),{"mcp:build"})
            self.assertFalse((package/"skills/palarran-backend-plan").exists())

    def test_public_menu_is_exact_and_legacy_aliases_do_not_select_new_packages(self):
        self.assertEqual(set(packager.ALIASES), {"core", "memory", "product", "design", "code",
                                               "machine-learning", "docs", "science", "validation", "infrastructure", "security"})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                packager.build_package("backend", Path(directory)/"rejected", root=ROOT)
            self.assertFalse((Path(directory)/"rejected").exists())

    def test_reverse_mapping_rebases_links_adapters_and_prefix_boundaries(self):
        moves={"skills/demo":"packages/code/backend/skills/demo", "docs/backend":"packages/code/backend/docs",
               "scripts/tool.py":"packages/code/backend/scripts/tool.py"}
        raw=b"[guide](../../docs/guide.md#part)\n${CLAUDE_PLUGIN_ROOT}/packages/code/backend/skills/demo/SKILL.md\npython3 packages/code/backend/scripts/tool.py --plan\n[remote](https://example.invalid/packages/code/backend/docs/x)\n"
        output=packager.portable_bytes(raw,"packages/code/backend/skills/demo/SKILL.md","skills/demo/SKILL.md",moves).decode()
        self.assertIn('[guide](../../docs/backend/guide.md#part)',output)
        self.assertIn('${CLAUDE_PLUGIN_ROOT}/skills/demo/SKILL.md',output)
        self.assertIn('python3 scripts/tool.py --plan',output)
        self.assertIn('https://example.invalid/packages/code/backend/docs/x',output)
        self.assertEqual(packager.portable_path('packages/code/backend/docs-other/x',moves),'packages/code/backend/docs-other/x')
        for raw in (b'{"version":true,"moves":{}}',b'{"version":1,"moves":{"../x":"packages/x"}}',
                    b'{"version":1,"moves":{"a":"packages/x","b":"packages/x"}}'):
            with self.assertRaises(ValueError):packager.parse_layout(raw)

    def test_refuses_existing_output_preserving_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing"
            output.mkdir()
            marker = output / "user-work.md"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                packager.build_package("infrastructure", output, root=ROOT)
            self.assertEqual(marker.read_text(), "preserve")

    def test_refuses_source_tree_output_before_creating_anything(self):
        target = ROOT / "docs" / "must-not-create-plugin"
        self.assertFalse(target.exists())
        with self.assertRaises(ValueError):
            packager.build_package("infrastructure", target, root=ROOT)
        self.assertFalse(target.exists())

    def test_rejects_external_source_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory).resolve() / "source"
            fixture.mkdir()
            (fixture / "docs/ci-cd").mkdir(parents=True)
            (fixture / "templates").mkdir()
            (fixture / "plugins/palarran-ci-cd").mkdir(parents=True)
            (fixture / "plugins/palarran-ci-cd/plugin.json").write_text(json.dumps({"name": "palarran-ci-cd", "commands": {}}))
            for name in ["palarran-ci-cd"]:
                (fixture / "skills" / name).mkdir(parents=True)
            external = Path(directory) / "private.txt"
            external.write_text("must not be packaged")
            (fixture / "docs/ci-cd/leak.md").symlink_to(external)
            output = Path(directory) / "package"
            with self.assertRaises(ValueError):
                packager.build_package("ci-cd", output, root=fixture)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
