#!/usr/bin/env python3
"""Materialize a self-contained Claude plugin without external symlinks or project memory."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root


import argparse
import json
import posixpath
import re
import sys
from pathlib import Path
import shutil
import tempfile

for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts/palarran_paths.py").is_file():
        sys.path.insert(0, str(_parent / "scripts"))
        break
from palarran_paths import repository_root, source_path

ROOT = repository_root(__file__)
LEGACY_PACKAGES = {'palarran-setup': {'manifest': 'plugins/palarran-setup/plugin.json',
                    'skills': ['palarran-setup'],
                    'docs': ['docs/skills', 'docs/setup', 'docs/memory', 'docs/infra', 'docs/app'],
                    'domain': 'skills'},
 'palarran-memory': {'manifest': 'plugins/palarran-memory/plugin.json',
                     'skills': ['palarran-memory-recall', 'palarran-memory-learn', 'palarran-memorize', 'palarran-remember', 'palarran-memorize-session', 'palarran-remember-session', 'palarran-vacuum'],
                     'docs': ['docs/skills', 'docs/memory', 'docs/infra', 'docs/app'],
                     'domain': 'memory'},
 'palarran-vps': {'manifest': 'plugins/palarran-vps/plugin.json',
                  'skills': ['palarran-vps-inspect', 'palarran-vps-manage'],
                  'docs': ['docs/skills', 'docs/memory', 'docs/infra', 'docs/setup', 'docs/app'],
                  'domain': 'vps'},
 'palarran-mcp': {'manifest': 'plugins/palarran-mcp/plugin.json',
                  'skills': ['palarran-mcp-build'],
                  'docs': ['docs/skills', 'docs/mcp'],
                  'domain': 'mcp'},
 'palarran-app': {'manifest': 'plugins/palarran-app/plugin.json',
                  'skills': ['palarran-app-verify'],
                  'docs': ['docs/skills', 'docs/app'],
                  'domain': 'app'},
 'palarran-science': {'manifest': 'plugins/palarran-science/plugin.json',
                      'skills': ['palarran-science-preprint'],
                      'docs': ['docs/skills', 'docs/science'],
                      'domain': 'science'},
 'palarran-agent': {'manifest': 'plugins/palarran-agent/plugin.json',
                    'skills': ['palarran-agent-eval', 'palarran-agent-improve'],
                    'docs': ['docs/skills', 'docs/agent'],
                    'domain': 'agent'},
 'palarran-ml': {'manifest': 'plugins/palarran-ml/plugin.json',
                 'skills': ['palarran-ml-plan',
                            'palarran-ml-hypotheses',
                            'palarran-ml-model',
                            'palarran-ml-data',
                            'palarran-ml-cost',
                            'palarran-ml-train',
                            'palarran-ml-benchmark'],
                 'docs': ['docs/skills', 'docs/ml'],
                 'domain': 'ml'},
 'palarran-product': {'manifest': 'plugins/palarran-product/plugin.json',
                      'skills': ['palarran-product-define',
                                 'palarran-product-market',
                                 'palarran-product-compare',
                                 'palarran-product-revenue',
                                 'palarran-product-acquisition',
                                 'palarran-product-b2b',
                                 'palarran-product-b2c'],
                      'docs': ['docs/skills', 'docs/product'],
                      'domain': 'product'},
 'palarran-backend': {'manifest': 'plugins/palarran-backend/plugin.json',
                      'skills': ['palarran-backend-plan', 'palarran-backend-build'],
                      'docs': ['docs/skills', 'docs/backend'],
                      'domain': 'backend'},
 'palarran-frontend': {'manifest': 'plugins/palarran-frontend/plugin.json',
                       'skills': ['palarran-frontend-plan',
                                  'palarran-frontend-build',
                                  'palarran-ui-design',
                                  'palarran-ux-design'],
                       'docs': ['docs/skills', 'docs/ux', 'docs/ui', 'docs/frontend'],
                       'domain': 'frontend'},
 'palarran-ui': {'manifest': 'plugins/palarran-ui/plugin.json',
                 'skills': ['palarran-ui-design', 'palarran-ux-design'],
                 'docs': ['docs/skills', 'docs/ux', 'docs/ui'],
                 'domain': 'ui'},
 'palarran-ci-cd': {'manifest': 'plugins/palarran-ci-cd/plugin.json',
                    'skills': ['palarran-ci-cd'],
                    'docs': ['docs/skills', 'docs/infra', 'docs/ci-cd'],
                    'domain': 'ci-cd'},
 'palarran-infra': {'manifest': 'plugins/palarran-infra/plugin.json',
                    'skills': ['palarran-infra-plan', 'palarran-infrastructure-incident'],
                    'docs': ['docs/skills', 'docs/infra'],
                    'domain': 'infra-plan'},
 'palarran-ux': {'manifest': 'plugins/palarran-ux/plugin.json',
                 'skills': ['palarran-ux-design'],
                 'docs': ['docs/skills', 'docs/ux'],
                 'domain': 'ux'}}
LEGACY_ALIASES = {'skills': 'palarran-setup',
 'memory': 'palarran-memory',
 'vps': 'palarran-vps',
 'mcp': 'palarran-mcp',
 'app': 'palarran-app',
 'science': 'palarran-science',
 'agent': 'palarran-agent',
 'ml': 'palarran-ml',
 'product': 'palarran-product',
 'backend': 'palarran-backend',
 'frontend': 'palarran-frontend',
 'ui': 'palarran-ui',
 'ci-cd': 'palarran-ci-cd',
 'infra-plan': 'palarran-infra',
 'ux': 'palarran-ux'}


def _legacy_package(namespace, output, root=ROOT):
    namespace = LEGACY_ALIASES.get(namespace, namespace)
    config = dict(LEGACY_PACKAGES[namespace])
    if namespace == "palarran-setup":
        extra = ["palarran-package-" + action for action in
                 ("create", "search", "install", "update", "uninstall", "list")]
        config["skills"] = list(config["skills"]) + [name for name in extra
            if source_path(root, "skills/" + name + "/SKILL.md").is_file()]
    plugin_name = namespace
    namespace = config['domain']
    root = Path(root).absolute()
    source_path(root, "README.md")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Output already exists; choose a new directory (no overwrite)")
    # An output inside these source trees would recursively include its own staging copy.
    sources = [root / "docs", root / "templates", root / "packages"]
    sources += [root / "skills" / name for name in config["skills"]]
    if any(output.resolve().is_relative_to(source.resolve()) for source in sources):
        raise ValueError("Output must not be inside a packaged source tree")
    manifest = json.loads(source_path(root, config["manifest"], required=True).read_text())
    if manifest["name"] != plugin_name:
        raise ValueError("Plugin namespace mismatch")
    # Copy reviewed documentation and explicit template resources only. Never sweep
    # ignored .terraform binaries, .env files or local artifacts into a package.
    moves = layout_moves(root)
    for item in manifest["commands"].values():
        item["source"] = "./" + portable_path(item["source"].removeprefix("./"), moves)
    paths = [root / name for legacy in config["docs"] for name in document_paths(root, legacy, moves)]
    paths += [root / "skills" / name / "SKILL.md" for name in config["skills"]]
    resources = [
        "templates/palarran/decision.md",
        "templates/infra/README.md",
        "templates/infra/low/compose.yaml", "templates/infra/low/Caddyfile",
        "templates/infra/low/.env.example", "templates/infra/low/init-app.sql",
        "templates/infra/kubernetes/app-network.yaml", "templates/infra/kubernetes/appproject.yaml",
        "templates/infra/terraform-hcloud/main.tf",
        "templates/infra/terraform-hcloud/terraform.tfvars.example",
        "templates/infra/terraform-hcloud/.terraform.lock.hcl",
    ]
    infra_resources = list(resources)
    if namespace in {"ux", "ui", "frontend"}:
        resources = [
            "templates/palarran/decision.md",
            "templates/ux/concept.md", "templates/ux/screen.md", "templates/ux/reference.md",
        ]
    if namespace in {"ui", "frontend"}:
        resources += [
            "docs/ui/catalog.json", "templates/ui/concept.md", "templates/ui/screen.md",
            "templates/ui/reference.md", "templates/ui/tokens.example.json",
        ]
    if namespace == "frontend":
        resources += [
            "templates/frontend/coverage.md", "templates/frontend/browser-review.md",
            "templates/frontend/handoff.md", "templates/frontend/plan.md",
            "templates/frontend/agent-task.md", "templates/frontend/progress.example.json",
            "scripts/execution_progress.py", "templates/frontend/spec.md",
            "templates/frontend/api-contract.md", "templates/frontend/test-matrix.md",
            "templates/frontend/planning-handoff.md",
        ]
    if namespace == "backend":
        resources = [
            "templates/palarran/decision.md", "templates/backend/foundation.md",
            "templates/backend/spec.md", "templates/backend/plan.md",
            "templates/backend/reliability.md", "templates/backend/test-matrix.md",
            "templates/backend/agent-task.md", "templates/backend/progress.example.json",
            "templates/backend/execution-agent.md", "templates/backend/build-verification.md",
            "templates/backend/build-handoff.md", "scripts/backend_progress.py",
            "scripts/execution_progress.py",
        ]
    if namespace == "product":
        resources = [
            "templates/palarran/decision.md", "templates/product/brief.md",
            "templates/product/research.md", "templates/product/competitors.md",
            "templates/product/economics.md", "templates/product/channels.md",
            "templates/product/pipeline-mvp.md",
            "templates/product/b2b-sales.md", "templates/product/b2c-growth.md",
        ]
    if namespace == "ml":
        resources = [
            "templates/palarran/decision.md", "templates/ml/experiment.md",
            "templates/ml/data-card.md", "templates/ml/benchmark.md",
            "templates/ml/progress.example.json", "templates/ml/cost.example.json",
            "templates/ml/pipeline-stage.example.json",
            "scripts/ml_cost.py", "scripts/ml_data.py", "templates/ml/data-plan.md",
            "templates/ml/data-prepare.example.json", "templates/ml/token-audit.example.json",
            "templates/ml/data-mixture.example.json", "templates/ml/data-preparation.example.json",
        ]
    if namespace in {"memory", "vps"}:
        resources = ["templates/palarran/decision.md", "templates/memory/.env.example", "templates/memory/compose.yaml", "templates/memory/palarran-memory.service", "templates/memory/client.example.json", "templates/memory/case.example.json", "templates/memory/deployment-plan.md", "scripts/memory_ops.py", "scripts/memory_acceptance.py", "scripts/memory_context.py", "scripts/memory_vacuum.py", "scripts/vps_ops.py", "scripts/infra_inventory.py", "memory/__init__.py", "memory/service.py", "memory/proxy.py", "mcp/catalog/server.py"]
    if namespace in {"memory", "vps"}:
        resources += infra_resources[1:] + ["docs/setup/vps-stack.md"]
    if namespace == "mcp":
        resources = ["templates/palarran/decision.md", "templates/mcp/build-plan.md", "templates/mcp/catalog.example.json", "scripts/mcp_build.py", "mcp/catalog/server.py"]
    if namespace == "app":
        resources = ["templates/palarran/decision.md", "templates/app/verify/scenarios.md", "templates/app/verify/report.md", "scripts/app_verify.py", "scripts/app_verify_browser.cjs", "scripts/ml_data.py"]
    if namespace == "science":
        resources = ["templates/palarran/decision.md", "templates/science/main.tex", "templates/science/claim-evidence.md", "scripts/science_preprint.py", "scripts/ml_data.py"]
    if namespace == "agent":
        resources = ["templates/palarran/decision.md", "templates/palarran-agent-eval/protocol.md", "templates/palarran-agent-improve/review.md", "templates/palarran-agent-improve/incident.example.json"]
    if namespace == "skills":
        resources += ["scripts/project_setup.py", "scripts/project_update.py", "scripts/palarran_config.py", "scripts/package_plugin.py", "templates/memory/compose.yaml", "templates/memory/palarran-memory.service"]
    if namespace == "skills":
        resources += ['packages/core/coordination/__init__.py', 'packages/core/coordination/service.py', 'packages/core/coordination/build_sqlite.py', 'packages/core/coordination/client.py', 'packages/core/coordination/proxy.py', 'packages/core/coordination/AGENTS.md', 'packages/core/coordination/docs/README.md', 'packages/core/coordination/docs/contract.md', 'packages/core/coordination/docs/wire.md', 'packages/core/coordination/docs/operations.md', 'packages/core/coordination/templates/palarran-coordination.service', 'packages/core/coordination/templates/client.env.example', 'packages/core/coordination/templates/tunnel.service.example', 'mcp/catalog/server.py']
    if namespace == "skills":
        resources += ['packages/core/coordination/__init__.py', 'packages/core/coordination/service.py', 'packages/core/coordination/build_sqlite.py', 'packages/core/coordination/deploy.py', 'packages/core/coordination/docs/runbook.md', 'packages/core/coordination/client.py', 'packages/core/coordination/proxy.py', 'packages/core/coordination/AGENTS.md', 'packages/core/coordination/docs/README.md', 'packages/core/coordination/docs/contract.md', 'packages/core/coordination/docs/wire.md', 'packages/core/coordination/docs/operations.md', 'packages/core/coordination/templates/palarran-coordination.service', 'packages/core/coordination/templates/client.env.example', 'packages/core/coordination/templates/tunnel.service.example', 'mcp/catalog/server.py']
    resources += ["scripts/palarran_paths.py", "templates/agents/root.md", "templates/agents/module.md",
                  "scripts/memory_cycle.py", "scripts/memory_ops.py", "scripts/keenable_auth.py", "templates/memory/lesson.example.json",
                  "memory/__init__.py", "memory/service.py"]
    # Shared memory/installation guides link this inert procedure even when
    # the optional Infrastructure runtime was not selected.
    hosting_guides = ["packages/infrastructure/hosting/docs/" + guide
                      for guide in ("README.md", "runbook.md", "sources.md")]
    if source_path(root, hosting_guides[0]).is_file():
        resources += hosting_guides
    resources += ["packages/core/agents/docs/usage-and-pipelines.md"]
    # Keep the canonical import path for portable setup and test bindings.
    local_io = "packages/core/security/local_io.py"
    if source_path(root, local_io).is_file():
        resources.append(local_io)
    # Core parallelism is an installed cross-domain contract. Export its explicit
    # source closure, never task journals, logs or arbitrary package-local files.
    parallel_guides = ["packages/core/parallelism/README.md"] + [
        "packages/core/parallelism/docs/" + name + ".md" for name in
        ("contract", "sources", "authority", "managed-entry", "temporal", "temporal-sources", "integration", "integration-sources", "dashboard", "core-internals", "ledger-contract", "session-pool")]
    parallel_guides += ["packages/core/parallelism/docs/features/" + name + ".md" for name in
                        ("README", "sources", "contract", "workflow", "acceptance", "gates", "validation")]
    resources += [name for name in parallel_guides if source_path(root, name).is_file()]
    temporal_runbook = "packages/infrastructure/hosting/docs/temporal-runbook.md"
    if source_path(root, temporal_runbook).is_file():
        resources.append(temporal_runbook)
    if namespace in {"skills", "core"}:
        helpers = ["packages/core/parallelism/" + name for name in
                   ("primitives.py", "states.py", "ledger.py", "manifest_validation.py", "feature_validation.py", "dispatcher.py", "authority.py", "entry.py", "harness.py", "native.py", "session_teams.py", "session_pool.py", "team_observer.py", "team_journal.py", "temporal.py", "temporal_worker.py", "requirements-temporal.txt", "integration.py", "root_budget.py", "dashboard.py", "feature.py", "feature_gates.py", "feature_demo.py")]
        helpers += ["packages/core/parallelism/fixtures/features/" + name for name in ("service.py", "check.py")]
        helpers += ["packages/core/parallelism/assets/" + name for name in ("dashboard.html", "dashboard.css", "dashboard.js")]
        helpers += ["packages/core/setup/temporal_config.py"]
        helpers += ["packages/core/orchestration/runtime/" + name + ".py" for name in
                    ("__init__", "runner", "usage", "diagnostics", "accounting", "budgets", "workspaces")]
        resources += [name for name in helpers if source_path(root, name).is_file()]
    # Sharing uses the existing bus; its explicit closure excludes private journals.
    resources += ["packages/core/coordination/docs/sharing/" + guide + ".md" for guide in
                  ("README", "contract", "git", "temporal")]
    if namespace in {"skills", "core", "vps"}:
        resources += ["packages/core/coordination/" + name + ".py" for name in
                      ("share", "share_store", "share_git", "share_runtime", "share_temporal", "share_temporal_worker")]
    packaging_base = "packages/core/packaging/"
    if source_path(root, packaging_base + "README.md").is_file():
        resources += [packaging_base + "README.md", packaging_base + "AGENTS.md"]
        resources += [p.relative_to(root).as_posix() for p in
                      sorted((root / packaging_base / "docs").glob("*.md"))]
        if namespace in {"skills", "core"}:
            resources += ["scripts/package_ops.py", packaging_base + "Dockerfile",
                          packaging_base + "Dockerfile.dockerignore"]
            resources += [packaging_base + name + ".py" for name in
                          ("__init__", "contract", "storage", "store", "service", "client", "installer", "cli")
                          if source_path(root, packaging_base + name + ".py").is_file()]
            resources += [p.relative_to(root).as_posix() for p in
                          sorted((root / packaging_base / "templates").glob("*"))
                          if p.is_file() and p.suffix in {".json", ".yaml", ".md"}]
    resources.append("LICENSE")
    paths += [root / resource for resource in resources]
    for command in manifest["commands"].values():
        paths.append(root / command["source"].removeprefix("./"))
    if namespace == "infra-plan":
        paths.append(root / "scripts/infra_inventory.py")
    files = []
    for legacy in paths:
        relative = legacy.relative_to(root)
        path = source_path(root, relative.as_posix(), required=True)
        # Resolve canonical bytes; never export a compatibility shim instead.
        canonical = path.relative_to(root)
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)) or not path.resolve().is_relative_to(root):
            raise ValueError("Package source contains a symlink or escaping path")
        if path.is_file():
            if path.suffix == ".pyc" or "__pycache__" in path.parts:
                continue
            files.append((path, relative))
        elif not path.is_dir():
            raise ValueError("Package source file missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".plugin-stage-", dir=output.parent) as staging:
        stage = Path(staging) / namespace
        stage.mkdir()
        moves = layout_moves(root)
        for source, relative in files:
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), relative.as_posix(), moves))
        target_manifest = stage / ".claude-plugin/plugin.json"
        target_manifest.parent.mkdir(parents=True, exist_ok=True)
        target_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        # Recheck before publishing; never remove an existing checkout or user artifact.
        if output.exists() or output.is_symlink():
            raise FileExistsError("Output appeared during packaging; not overwritten")
        stage.rename(output)
    return output



def document_paths(root, legacy, moves):
    """Collect a legacy docs subtree even when only its child prefixes moved."""
    result = set()
    prefixes = [legacy] + [old for old in moves if old.startswith(legacy + "/")]
    for prefix in prefixes:
        directory = source_path(root, prefix)
        if directory.is_file():
            if directory.suffix == ".md": result.add(portable_path(directory.relative_to(root).as_posix(), moves))
        elif directory.is_dir():
            for path in directory.rglob("*.md"):
                result.add(portable_path(path.relative_to(root).as_posix(), moves))
    if not result: raise ValueError("Missing reviewed documentation subtree")
    return sorted(result)


def parse_layout(raw):
    """Validate committed mapping bytes without filesystem access or execution."""
    if len(raw) > 65536:
        raise ValueError("Layout manifest exceeds its byte bound")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError("Duplicate layout field")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs)
    if (type(value) is not dict or set(value) != {"version", "moves"}
            or type(value["version"]) is not int or value["version"] != 1
            or type(value["moves"]) is not dict):
        raise ValueError("Invalid layout manifest")
    destinations = set()
    for old, new in value["moves"].items():
        for item in (old, new):
            if (not isinstance(item, str) or not item or "\\" in item or ":" in item
                    or any(ord(c) < 32 or ord(c) == 127 for c in item)
                    or any(part in ("", ".", "..") for part in item.split("/"))):
                raise ValueError("Invalid layout path")
        if new in destinations: raise ValueError("Ambiguous inverse layout")
        destinations.add(new)
    return value["moves"]


def layout_moves(root):
    source_path(root, "README.md")  # Validate all map entries and symlink boundaries.
    path = root / "packages/layout.json"
    return parse_layout(path.read_bytes()) if path.exists() else {}


def portable_path(canonical, moves):
    matches = [(new, old) for old, new in moves.items()
               if canonical == new or canonical.startswith(new + "/")]
    if not matches: return canonical
    new, old = max(matches, key=lambda item: len(item[0]))
    return old + canonical[len(new):]


def portable_bytes(raw, canonical, portable, moves):
    """Rebase local Markdown links; code, remote references and anchors stay intact."""
    if not canonical.endswith(".md") or not moves: return raw
    text = raw.decode("utf-8")
    def link(match):
        target = match.group(1)
        angled = target.startswith("<") and target.endswith(">")
        if angled: target = target[1:-1]
        if not target or target.startswith(("#", "/")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
            return match.group(0)
        path, separator, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(canonical), path))
        if resolved == ".." or resolved.startswith("../"):
            raise ValueError("Markdown link escapes source root")
        exported = portable_path(resolved, moves)
        relative = posixpath.relpath(exported, posixpath.dirname(portable) or ".")
        result = relative + (separator + anchor if separator else "")
        return "](" + ("<" + result + ">" if angled else result) + ")"
    text = re.sub(r"\]\((<[^>]+>|[^)\s]+)\)", link, text)
    # Command adapters and fenced CLI examples also name root-relative resources.
    # Rebase those declared canonical references without rewriting Python source.
    inverse = {new: old for old, new in moves.items()}
    pattern = "|".join(re.escape(item) for item in sorted(inverse, key=len, reverse=True))
    if pattern:
        def reference(match):
            prefix = re.split(r'[\s`"<>]', text[:match.start()])[-1]
            return match.group(0) if "://" in prefix else inverse[match.group(0)]
        text = re.sub(r"(?<![A-Za-z0-9_-])(?:" + pattern + r")(?=/|[^A-Za-z0-9_.-]|$)", reference, text)
    return text.encode("utf-8")


def registry_type():
    import importlib.util
    path = source_path(ROOT, "packages/core/packages/registry.py", required=True)
    spec = importlib.util.spec_from_file_location("palarran_package_registry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Registry


def registry(root=ROOT):
    return registry_type().load(source_path(root, "packages/catalog.json", required=True))


PUBLIC_GROUPS = {
    "core": ["skills", "mcp"], "memory": ["memory"], "product": ["product"],
    "design": ["ui"], "code": ["backend", "frontend"], "machine-learning": ["ml"],
    "docs": [], "science": ["science"], "validation": ["agent", "app"],
    "infrastructure": ["infra-plan", "ci-cd", "vps"], "security": [],
}
# Public menu is exact; legacy adapters are consulted only for older fixture roots.
PACKAGES = {"palarran-" + key: {"id": key} for key in PUBLIC_GROUPS}
ALIASES = {key: "palarran-" + key for key in PUBLIC_GROUPS}


def build_package(namespace, output, root=ROOT):
    root = Path(root).absolute()
    if namespace == "palarran": return build_bundle(output, root)
    if not (root / "packages/catalog.json").exists():
        return _legacy_package(namespace, output, root)
    package_id = namespace.removeprefix("palarran-")
    resolved = registry(root).resolve([package_id])
    return _public_package(output, root, resolved, "palarran-" + package_id)


def _public_package(output, root, resolved, name):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink(): raise FileExistsError("Output already exists")
    if any(output.resolve().is_relative_to(root / directory) for directory in ("docs", "skills", "templates", "packages")):
        raise ValueError("Output must not be inside a packaged source tree")
    names = {skill["name"] for skill in resolved["skills"]}
    groups = list(dict.fromkeys(group for package in resolved["packages"] for group in PUBLIC_GROUPS[package]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".palarran-package-", dir=output.parent) as temporary:
        staging = Path(temporary); bundle = staging / "bundle"; bundle.mkdir()
        for group in groups:
            package = _legacy_package(group, staging / group, root)
            for source in package.rglob("*"):
                if not source.is_file(): continue
                relative = source.relative_to(package)
                if relative.parts[0] == ".claude-plugin": continue
                if relative.parts[0] == "skills" and len(relative.parts) > 1 and relative.parts[1] not in names: continue
                destination = bundle / relative; destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists() and destination.read_bytes() != source.read_bytes(): raise ValueError("Conflicting public resource")
                if not destination.exists(): shutil.copyfile(source, destination)
        moves = layout_moves(root)
        if "code" in resolved["packages"]:
            references = ["docs/git/" + guide + ".md" for guide in
                          ("README", "commit", "history", "conflicts", "mr", "sources")]
            references += ["templates/git/mr.md"]
            for reference in references:
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        if "code" in resolved["packages"]:
            for reference in ("packages/code/review/docs/README.md", "packages/code/review/docs/sources.md", "packages/code/review/README.md"):
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        if "validation" in resolved["packages"]:
            reference = "packages/validation/application/project_tests.py"
            source = source_path(root, reference, required=True)
            destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        if "infrastructure" in resolved["packages"]:
            references = ['packages/infrastructure/hosting/compose.yaml', 'packages/infrastructure/hosting/runtime.py', 'packages/infrastructure/hosting/prepare.py', 'packages/infrastructure/hosting/docs/README.md', 'packages/infrastructure/hosting/docs/runbook.md', 'packages/infrastructure/hosting/docs/sources.md', 'packages/memory/knowledge/Dockerfile', 'packages/memory/knowledge/Dockerfile.dockerignore', 'packages/memory/knowledge/runtime/service.py', 'packages/core/coordination/Dockerfile', 'packages/core/coordination/Dockerfile.dockerignore', 'packages/core/coordination/service.py', 'packages/core/coordination/share.py', 'packages/core/coordination/share_store.py', 'packages/core/coordination/build_sqlite.py']
            for reference in references:
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        if "infrastructure" in resolved["packages"]:
            reference = "packages/infrastructure/hosting/temporal.compose.yaml"
            source = source_path(root, reference)
            if source.is_file():
                destination = bundle / reference
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
        if "security" in resolved["packages"]:
            # Explicit reviewed resource set; never sweep ignored audit evidence,
            # customer logs, credentials or arbitrary package-local artifacts.
            references = ["packages/security/shared/docs/contract.md",
                          "packages/security/shared/docs/README.md",
                          "packages/security/shared/report.py",
                          "packages/security/shared/templates/audit.example.json"]
            for profile in ("infrastructure", "ingress", "log", "egress", "code", "cve"):
                references.extend("packages/security/" + profile + "/docs/" + guide
                                  for guide in ("README.md", "sources.md"))
            for reference in references:
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        if "docs" in resolved["packages"]:
            for reference in document_paths(root, "docs/documentation", moves) + ["packages/docs/documentation/render.py", "packages/docs/documentation/__init__.py"]:
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        if "palarran-core-coop" in names:
            for reference in ("packages/core/coop/docs/README.md", "packages/core/coop/daemon.py"):
                source = source_path(root, reference, required=True)
                destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        for reference in ("packages/catalog.json", "packages/core/packages/registry.py", "packages/core/packages/__init__.py", "scripts/palarran_paths.py"):
            source = source_path(root, reference, required=True)
            destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        for skill in resolved["skills"]:
            reference = skill["legacy_path"]
            source = source_path(root, skill["path"], required=True)
            destination = bundle / reference; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), reference, moves))
        manifest = json.loads(source_path(root, "plugins/palarran/plugin.json", required=True).read_text())
        manifest["name"] = name
        # Command adapters carry skill references; use the committed skill closure,
        # never labels inferred from a command's display name.
        commands = {}
        for command, item in manifest["commands"].items():
            item["source"] = "./" + portable_path(item["source"].removeprefix("./"), moves)
            source = source_path(root, item["source"].removeprefix("./"), required=True)
            text = source.read_text()
            owner = re.search(r"(?<![A-Za-z0-9_-])skills/(palarran-[a-z0-9-]+)/SKILL[.]md", text)
            if owner is None:
                raise ValueError("Command adapter has no explicit owning skill")
            if owner.group(1) in names:
                commands[command] = item
                destination = bundle / item["source"].removeprefix("./")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(portable_bytes(source.read_bytes(), source.relative_to(root).as_posix(), str(destination.relative_to(bundle)), moves))
        manifest["commands"] = commands
        target = bundle / ".claude-plugin/plugin.json"; target.parent.mkdir()
        target.write_text(json.dumps(manifest, indent=2) + "\n")
        if output.exists() or output.is_symlink(): raise FileExistsError("Output appeared during packaging")
        bundle.rename(output)
    return output


def build_bundle(output, root=ROOT):
    if (Path(root) / "packages/catalog.json").exists():
        return _public_package(output, Path(root).absolute(), registry(root).resolve(list(PUBLIC_GROUPS)), "palarran")
    # Compatibility for pre-catalog fixture libraries only.
    root = Path(root).resolve(); output = Path(output).absolute()
    if output.exists() or output.is_symlink(): raise FileExistsError("Output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".palarran-bundle-", dir=output.parent) as directory:
        temporary = Path(directory); bundle = temporary / "bundle"; bundle.mkdir()
        for namespace in LEGACY_PACKAGES:
            package = _legacy_package(namespace, temporary / namespace, root)
            for source in package.rglob("*"):
                if not source.is_file() or source.relative_to(package).parts[0] == ".claude-plugin": continue
                relative = source.relative_to(package); destination = bundle / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists() and destination.read_bytes() != source.read_bytes(): raise ValueError("Conflicting resource")
                if not destination.exists(): shutil.copyfile(source, destination)
        target = bundle / ".claude-plugin/plugin.json"; target.parent.mkdir()
        shutil.copyfile(source_path(root, "plugins/palarran/plugin.json", required=True), target)
        if output.exists() or output.is_symlink(): raise FileExistsError("Output appeared during packaging")
        bundle.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", choices=sorted(set(PACKAGES) | set(ALIASES) | {"palarran"}))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try: output = build_package(args.namespace, args.output)
    except (OSError, ValueError, KeyError): parser.exit(2, "Packaging failed: inspect trusted sources and package selection\n")
    print(f"Created self-contained {args.namespace} plugin: {output}")


if __name__ == "__main__": main()
