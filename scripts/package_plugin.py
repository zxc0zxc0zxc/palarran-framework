#!/usr/bin/env python3
"""Materialize a self-contained Claude plugin without external symlinks or project memory."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "memory": {"manifest": "plugins/memory/plugin.json", "skills": ["memory-recall", "memory-learn"], "docs": ["docs/skills", "docs/memory", "docs/infra"]},
    "vps": {"manifest": "plugins/vps/plugin.json", "skills": ["vps-inspect", "vps-manage"], "docs": ["docs/skills", "docs/memory", "docs/infra"]},
    "mcp": {"manifest": "plugins/mcp/plugin.json", "skills": ["mcp-build"], "docs": ["docs/skills", "docs/mcp"]},
    "app": {"manifest": "plugins/app/plugin.json", "skills": ["app-verify"], "docs": ["docs/skills", "docs/app"]},
    "science": {"manifest": "plugins/science/plugin.json", "skills": ["science-preprint"], "docs": ["docs/skills", "docs/science"]},
    "agent": {
        "manifest": "plugins/agent/plugin.json",
        "skills": ["agent-eval", "agent-improve"],
        "docs": ["docs/skills", "docs/agent"],
    },
    "ml": {
        "manifest": "plugins/ml/plugin.json",
        "skills": ["ml-plan", "ml-hypotheses", "ml-model", "ml-data", "ml-cost", "ml-train", "ml-benchmark"],
        "docs": ["docs/skills", "docs/ml"],
    },
    "product": {
        "manifest": "plugins/product/plugin.json",
        "skills": ["product-define", "product-market", "product-compare", "product-revenue", "product-acquisition", "product-b2b", "product-b2c"],
        "docs": ["docs/skills", "docs/product"],
    },
    "backend": {
        "manifest": "plugins/backend/plugin.json",
        "skills": ["backend-plan", "backend-build"],
        "docs": ["docs/skills", "docs/backend"],
    },
    "frontend": {
        "manifest": "plugins/frontend/plugin.json",
        "skills": ["frontend-plan", "frontend-build", "ui-design", "ux-design"],
        "docs": ["docs/skills", "docs/ux", "docs/ui", "docs/frontend"],
    },
    "ui": {
        "manifest": "plugins/ui/plugin.json",
        "skills": ["ui-design", "ux-design"],
        "docs": ["docs/skills", "docs/ux", "docs/ui"],
    },
    "ci-cd": {
        "manifest": "plugins/ci-cd/plugin.json",
        "skills": ["ci-cd-github", "ci-cd-gitlab"],
        "docs": ["docs/skills", "docs/infra", "docs/ci-cd"],
    },
    "infra-plan": {
        "manifest": ".claude-plugin/plugin.json",
        "skills": ["infra-plan-low", "infra-plan-med", "infra-plan-high"],
        "docs": ["docs/skills", "docs/infra"],
    },
    "ux": {
        "manifest": "plugins/ux/plugin.json",
        "skills": ["ux-design"],
        "docs": ["docs/skills", "docs/ux"],
    },
}


def build_package(namespace, output, root=ROOT):
    config = PACKAGES[namespace]
    root = root.resolve()
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Output already exists; choose a new directory (no overwrite)")
    # An output inside these source trees would recursively include its own staging copy.
    sources = [root / "docs", root / "templates"]
    sources += [root / "skills" / name for name in config["skills"]]
    if any(output.resolve().is_relative_to(source.resolve()) for source in sources):
        raise ValueError("Output must not be inside a packaged source tree")
    manifest = json.loads((root / config["manifest"]).read_text())
    if manifest["name"] != namespace:
        raise ValueError("Plugin namespace mismatch")
    # Copy reviewed documentation and explicit template resources only. Never sweep
    # ignored .terraform binaries, .env files or local artifacts into a package.
    doc_roots = [root / directory for directory in config["docs"]]
    paths = sorted(path for directory in doc_roots for path in directory.rglob("*.md"))
    paths += [root / "skills" / name / "SKILL.md" for name in config["skills"]]
    resources = [
        "templates/ai-development/decision.md",
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
            "templates/ai-development/decision.md",
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
            "templates/ai-development/decision.md", "templates/backend/foundation.md",
            "templates/backend/spec.md", "templates/backend/plan.md",
            "templates/backend/reliability.md", "templates/backend/test-matrix.md",
            "templates/backend/agent-task.md", "templates/backend/progress.example.json",
            "templates/backend/execution-agent.md", "templates/backend/build-verification.md",
            "templates/backend/build-handoff.md", "scripts/backend_progress.py",
            "scripts/execution_progress.py",
        ]
    if namespace == "product":
        resources = [
            "templates/ai-development/decision.md", "templates/product/brief.md",
            "templates/product/research.md", "templates/product/competitors.md",
            "templates/product/economics.md", "templates/product/channels.md",
            "templates/product/pipeline-mvp.md",
            "templates/product/b2b-sales.md", "templates/product/b2c-growth.md",
        ]
    if namespace == "ml":
        resources = [
            "templates/ai-development/decision.md", "templates/ml/experiment.md",
            "templates/ml/data-card.md", "templates/ml/benchmark.md",
            "templates/ml/progress.example.json", "templates/ml/cost.example.json",
            "templates/ml/pipeline-stage.example.json",
            "scripts/ml_cost.py", "scripts/ml_data.py", "templates/ml/data-plan.md",
            "templates/ml/data-prepare.example.json", "templates/ml/token-audit.example.json",
            "templates/ml/data-mixture.example.json", "templates/ml/data-preparation.example.json",
        ]
    if namespace in {"memory", "vps"}:
        resources = ["templates/ai-development/decision.md", "templates/memory/.env.example", "templates/memory/compose.yaml", "templates/memory/ai-tools-memory.service", "templates/memory/client.example.json", "templates/memory/case.example.json", "templates/memory/deployment-plan.md", "scripts/memory_ops.py", "scripts/memory_acceptance.py", "scripts/vps_ops.py", "scripts/infra_inventory.py", "memory/__init__.py", "memory/service.py", "memory/proxy.py", "mcp/catalog/server.py"]
    if namespace in {"memory", "vps"}:
        resources += infra_resources[1:]
    if namespace == "mcp":
        resources = ["templates/ai-development/decision.md", "templates/mcp/build-plan.md", "templates/mcp/catalog.example.json", "scripts/mcp_build.py", "mcp/catalog/server.py"]
    if namespace == "app":
        resources = ["templates/ai-development/decision.md", "templates/app/verify/scenarios.md", "templates/app/verify/report.md", "scripts/app_verify.py", "scripts/app_verify_browser.cjs", "scripts/ml_data.py"]
    if namespace == "science":
        resources = ["templates/ai-development/decision.md", "templates/science/main.tex", "templates/science/claim-evidence.md", "scripts/science_preprint.py", "scripts/ml_data.py"]
    if namespace == "agent":
        resources = ["templates/ai-development/decision.md", "templates/agent-eval/protocol.md", "templates/agent-improve/review.md", "templates/agent-improve/incident.example.json"]
    resources += ["templates/agents/root.md", "templates/agents/module.md"]
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("namespace", choices=sorted(PACKAGES))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = build_package(args.namespace, args.output)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Packaging failed: {error}\n")
    print(f"Created self-contained {args.namespace} plugin: {output}")


if __name__ == "__main__":
    main()
