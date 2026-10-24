#!/usr/bin/env python3
"""Materialize a self-contained Claude plugin without external symlinks or project memory."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'palarran-setup': {'manifest': 'plugins/palarran-setup/plugin.json',
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
ALIASES = {'skills': 'palarran-setup',
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


def build_package(namespace, output, root=ROOT):
    namespace = ALIASES.get(namespace, namespace)
    if namespace == 'palarran':return build_bundle(output, root)
    config = PACKAGES[namespace]
    plugin_name = namespace
    namespace = config['domain']
    root = root.resolve()
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Output already exists; choose a new directory (no overwrite)")
    # An output inside these source trees would recursively include its own staging copy.
    sources = [root / "docs", root / "templates", root / "packages"]
    sources += [root / "skills" / name for name in config["skills"]]
    if any(output.resolve().is_relative_to(source.resolve()) for source in sources):
        raise ValueError("Output must not be inside a packaged source tree")
    manifest = json.loads((root / config["manifest"]).read_text())
    if manifest["name"] != plugin_name:
        raise ValueError("Plugin namespace mismatch")
    # Copy reviewed documentation and explicit template resources only. Never sweep
    # ignored .terraform binaries, .env files or local artifacts into a package.
    doc_roots = [root / directory for directory in config["docs"]]
    paths = sorted(path for directory in doc_roots for path in directory.rglob("*.md"))
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
        resources += ['packages/core/coordination/__init__.py', 'packages/core/coordination/service.py', 'packages/core/coordination/client.py', 'packages/core/coordination/proxy.py', 'packages/core/coordination/AGENTS.md', 'packages/core/coordination/docs/README.md', 'packages/core/coordination/docs/contract.md', 'packages/core/coordination/docs/wire.md', 'packages/core/coordination/docs/operations.md', 'packages/core/coordination/templates/palarran-coordination.service', 'packages/core/coordination/templates/client.env.example', 'packages/core/coordination/templates/tunnel.service.example', 'mcp/catalog/server.py']
    resources += ["templates/agents/root.md", "templates/agents/module.md",
                  "scripts/memory_cycle.py", "scripts/memory_ops.py", "scripts/keenable_auth.py", "templates/memory/lesson.example.json",
                  "memory/__init__.py", "memory/service.py"]
    paths += [root / resource for resource in resources]
    for command in manifest["commands"].values():
        paths.append(root / command["source"])
    if namespace == "infra-plan":
        paths.append(root / "scripts/infra_inventory.py")
    files = []
    for path in paths:
        # Reject symlinks rather than shipping targets outside plugin containment.
        relative = path.relative_to(root)
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)) or not path.resolve().is_relative_to(root):
            raise ValueError("Package source contains a symlink or escaping path")
        if path.is_file():
            if path.suffix == ".pyc" or "__pycache__" in path.parts:
                continue
            files.append(path)
        elif not path.is_dir():
            raise ValueError("Package source file missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".plugin-stage-", dir=output.parent) as staging:
        stage = Path(staging) / namespace
        stage.mkdir()
        for source in files:
            destination = stage / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        target_manifest = stage / ".claude-plugin/plugin.json"
        target_manifest.parent.mkdir(parents=True, exist_ok=True)
        target_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        # Recheck before publishing; never remove an existing checkout or user artifact.
        if output.exists() or output.is_symlink():
            raise FileExistsError("Output appeared during packaging; not overwritten")
        stage.rename(output)
    return output


def build_bundle(output, root=ROOT):
    """Union reviewed domain resources; never sweep a repository or private state."""
    root=Path(root).resolve();output=Path(output).absolute()
    if output.exists() or output.is_symlink():raise FileExistsError('Output already exists')
    if any(output.resolve().is_relative_to(root/name) for name in ('skills','docs','templates')):
        raise ValueError('Output must not be inside a packaged source tree')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.palarran-bundle-',dir=output.parent) as directory:
        temporary=Path(directory);bundle=temporary/'bundle';bundle.mkdir()
        for namespace in sorted(PACKAGES):
            package=build_package(namespace,temporary/namespace,root)
            for source in package.rglob('*'):
                if not source.is_file():continue
                relative=source.relative_to(package)
                if str(relative)=='.claude-plugin/plugin.json':continue
                dest=bundle/relative;dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists() and dest.read_bytes()!=source.read_bytes():raise ValueError('Conflicting package resource')
                if not dest.exists():shutil.copyfile(source,dest)
        target=bundle/'.claude-plugin/plugin.json';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/'plugins/palarran/plugin.json',target)
        if output.exists() or output.is_symlink():raise FileExistsError('Output appeared during packaging')
        bundle.rename(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", choices=sorted(set(PACKAGES)|set(ALIASES)|{'palarran'}))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = build_package(args.namespace, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Packaging failed: {error}\n")
    print(f"Created self-contained {args.namespace} plugin: {output}")


if __name__ == "__main__":
    main()
