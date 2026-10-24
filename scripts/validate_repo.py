#!/usr/bin/env python3
"""Offline skill, adapter, documentation and decision-memory contracts."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "mcp-build": ("mcp", "build"),
    "agent-improve": ("agent", "improve"),
    "app-verify": ("app", "verify"),
    "science-preprint": ("science", "preprint"),
    "agent-eval": ("agent", "eval"),
    **{f"ml-{command}": ("ml", command) for command in ("plan", "hypotheses", "model", "data", "cost", "train", "benchmark")},
    **{f"product-{command}": ("product", command) for command in ("define", "market", "compare", "revenue", "acquisition", "b2b", "b2c")},
    **{f"infra-plan-{level}": ("infra-plan", level) for level in ("low", "med", "high")},
    **{f"ci-cd-{provider}": ("ci-cd", provider) for provider in ("github", "gitlab")},
    "ux-design": ("ux", "design"),
    "ui-design": ("ui", "design"),
    "frontend-build": ("frontend", "build"),
    "frontend-plan": ("frontend", "plan"),
    "backend-plan": ("backend", "plan"),
    "backend-build": ("backend", "build"),
}
INFRA_GUIDES = ["README.md", "workflow.md", "security-network.md", "delivery-iac.md",
                "storage-operations.md", "decisions.md", "plan-template.md", "sources.md"]
CI_GUIDES = ["README.md", "workflow.md", "evidence.md", "architecture.md", "performance.md",
             "security.md", "environments.md", "decisions.md", "skill-contract.md", "sources.md"]
UX_GUIDES = ["README.md", "business.md", "research.md", "analysis.md", "diagrams.md",
             "responsive.md", "microcopy.md", "workflow.md", "review.md", "sources.md"]
UI_GUIDES = ["README.md", "design-codes.md", "references.md", "ux-binding.md", "foundations.md",
             "responsive.md", "visual-output.md", "workflow.md", "review.md", "sources.md", "catalog.json"]
FRONTEND_GUIDES = ["README.md", "source-contract.md", "implementation.md", "responsive.md",
                   "browser-verification.md", "quality.md", "workflow.md", "sources.md",
                   "sdd-agents.md", "progress.md"]
FRONTEND_PLAN_GUIDES = ["README.md", "source-context.md", "api-contracts.md", "edge-cases.md",
                        "workflow.md", "sources.md"]
BACKEND_GUIDES = ["README.md", "architecture.md", "foundation-stack.md", "contracts.md", "data.md",
                  "caching.md", "performance.md", "reliability.md", "testing.md", "delivery.md",
                  "sdd-agents.md", "workflow.md", "sources.md"]
BACKEND_BUILD_GUIDES = ["README.md", "source-progress.md", "worktrees.md", "implementation.md",
                        "verification.md", "reliability.md", "workflow.md", "sources.md"]
PRODUCT_GUIDES = ["README.md", "evidence.md", "workflow.md", "data-sources.md", "sources.md", "cases/README.md", "pipeline.md", "pipeline-contract.md"]
PRODUCT_CASES = {'define': 'product-discovery.md', 'market': 'market-validation.md', 'compare': 'competitive-positioning.md', 'revenue': 'revenue-economics.md', 'acquisition': 'acquisition-growth.md', 'b2b': 'b2b-first-customers.md', 'b2c': 'b2c-frugal-growth.md'}
ML_GUIDES = ["README.md", "workflow.md", "contracts.md", "cases.md", "sources.md", "pipeline.md", "pipeline-contract.md"]
ML_PROFILES = {
    "plan": ["plan.md", "hypotheses.md"], "hypotheses": ["hypotheses.md"],
    "model": ["model.md"], "data": ["data.md"] + ["data/"+name+".md" for name in ("README", "planning", "cleaning", "mixtures", "answer-integrity", "tools", "evaluation", "sources", "pipeline")], "cost": ["cost.md", "modal.md"],
    "train": ["train.md", "metrics.md", "cost.md", "modal.md", "data/pipeline.md"],
    "benchmark": ["benchmark.md", "metrics.md"],
}
IGNORED = {".git", ".agents", ".terraform", "plans", "artifacts", "node_modules", ".venv", "scratch", ".graphify", "graphify-out"}


def validate(root=ROOT):
    errors = []
    module_roots = ('mcp', 'orchestrator', 'scripts', 'tests', 'skills', 'docs', 'templates', 'plugins', 'examples')
    for name, limit in [('AGENTS.md', 6144)] + [(area + '/AGENTS.md', 4096) for area in module_roots]:
        path = root / name
        if not path.is_file() or path.is_symlink():
            errors.append('Missing regular instruction file: ' + name)
        elif not path.read_text().strip() or path.stat().st_size > limit:
            errors.append('Instruction budget exceeded or empty: ' + name)
    for name in ('docs/skills/agents-authoring.md', 'docs/skills/graph-context.md', 'docs/skills/domain-contracts.md',
                 'templates/agents/root.md', 'templates/agents/module.md'):
        if not (root / name).is_file():
            errors.append('Missing context contract: ' + name)
    markdown = sorted(path for path in root.rglob("*.md") if not set(path.relative_to(root).parts).intersection(IGNORED))
    for file in markdown:
        body = file.read_text()
        if body.count("```") % 2:
            errors.append(f"{file.relative_to(root)}: unbalanced code fences")
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", body):
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            dest = target.split("#", 1)[0]
            if dest and not (file.parent / dest).exists():
                errors.append(f"{file.relative_to(root)}: broken link {target}")

    actual_skills = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    if actual_skills != set(SKILLS):
        errors.append("Update validator registration and memory contract for added/removed skills")
    for name, (namespace, command) in SKILLS.items():
        path = root / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"Missing skill: {name}")
            continue
        body = path.read_text()
        if not body.startswith(f"---\nname: {name}\ndescription: "):
            errors.append(f"Invalid skill frontmatter: {name}")
        if "../../docs/skills/decision-memory.md" not in body:
            errors.append(f"{name}: missing shared decision-memory contract")
        if namespace == "mcp":
            base, guides = "mcp/build", ["README.md", "sources.md", "tool-design.md", "context-efficiency.md", "protocol-security.md", "evaluation.md", "workflow.md"]
        elif namespace == "app":
            base, guides = "app/verify", ["README.md", "sources.md", "methodology.md", "contract.md", "operations.md", "evidence.md"]
        elif namespace == "science":
            base, guides = "science", ["README.md", "sources.md", "evidence.md", "workflow.md"]
        elif namespace == "agent" and command == "improve":
            base, guides = "agent/improve", ["README.md", "sources.md", "methodology.md", "contract.md", "operations.md", "ml-learning-goal.md"]
        elif namespace == "agent":
            base, guides = "agent/eval", ["README.md", "sources.md", "methodology.md", "contract.md", "operations.md"]
        elif namespace == "ml":
            base, guides = "ml", ML_GUIDES + ML_PROFILES[command]
        elif namespace == "product":
            base, guides = "product", PRODUCT_GUIDES + [f"{command}.md", "cases/" + PRODUCT_CASES[command]]
            if command in {"b2b", "b2c", "acquisition"}:
                guides += ["go-to-market.md", "pricing.md", "go-to-market-sources.md"]
        elif namespace == "infra-plan":
            base, guides = "infra/plan", INFRA_GUIDES + [f"{command}.md"]
        elif namespace == "ci-cd":
            base, guides = "ci-cd", CI_GUIDES + [f"{command}.md"]
        elif namespace == "ux":
            base, guides = "ux", UX_GUIDES
        elif namespace == "ui":
            base, guides = "ui", UI_GUIDES
        elif namespace == "frontend":
            if command == "plan":
                base, guides = "frontend/plan", FRONTEND_PLAN_GUIDES
            else:
                base, guides = "frontend", FRONTEND_GUIDES
        elif command == "plan":
            base, guides = "backend/plan", BACKEND_GUIDES
        else:
            base, guides = "backend/build", BACKEND_BUILD_GUIDES
        if namespace == "ci-cd":
            guides += [f"stacks/{stack}.md" for stack in ("go", "php", "typescript-nextjs", "python", "rust")]
        for guide in guides:
            if f"../../docs/{base}/{guide}" not in body:
                errors.append(f"{name}: missing mandatory guide {guide}")
        discover = root / ".agents" / "skills" / name
        if not discover.is_symlink() or discover.resolve() != path.parent:
            errors.append(f"Invalid discovery link: {name}")
        adapter_path = root / ".claude" / "commands" / namespace / f"{command}.md"
        adapter = adapter_path.read_text() if adapter_path.is_file() else ""
        if "$ARGUMENTS" not in adapter or f"skills/{name}/SKILL.md" not in adapter:
            errors.append(f"Invalid command adapter: {name}")
        if "docs/skills/decision-memory.md" not in adapter:
            errors.append(f"Adapter omits memory: {name}")

    for level in ("low", "med", "high"):
        profile = (root / "docs/infra/plan" / f"{level}.md").read_text()
        if profile.count("```mermaid") < 2:
            errors.append(f"Profile {level} needs data and delivery diagrams")
    for namespace, relative in [("mcp", "plugins/mcp/plugin.json"), ("app", "plugins/app/plugin.json"), ("science", "plugins/science/plugin.json"), ("agent", "plugins/agent/plugin.json"), ("ml", "plugins/ml/plugin.json"), ("product", "plugins/product/plugin.json"), ("infra-plan", ".claude-plugin/plugin.json"), ("ci-cd", "plugins/ci-cd/plugin.json"), ("ux", "plugins/ux/plugin.json"), ("ui", "plugins/ui/plugin.json"), ("frontend", "plugins/frontend/plugin.json"), ("backend", "plugins/backend/plugin.json")]:
        manifest = json.loads((root / relative).read_text())
        expected = {command for ns, command in SKILLS.values() if ns == namespace}
        if manifest.get("name") != namespace or set(manifest.get("commands", {})) != expected:
            errors.append(f"Invalid plugin namespace or commands: {namespace}")
        for command in manifest.get("commands", {}).values():
            source = command.get("source", "")
            if not source or not (root / source).is_file():
                errors.append(f"Invalid plugin command source: {namespace}")

    catalog_path = root / "docs/ui/catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text())
        systems = catalog["systems"]
        ids = [item["id"] for item in systems]
        if len(systems) != 10 or len(set(ids)) != 10:
            errors.append("UI catalog needs exactly 10 distinct system choices")
        if set(catalog["selection_modes"]) != {"system", "custom", "system+custom"}:
            errors.append("UI catalog must support standalone custom references")
        if catalog.get("ordering") != "menu-not-popularity-rank":
            errors.append("UI menu must not invent a popularity ranking")
        for item in systems:
            if not all(isinstance(item.get(field), str) and item[field].strip()
                       for field in ("id", "label", "owner", "primary_url", "visual_start", "caveat")):
                errors.append("UI system needs identity, provenance, visual starting point and limitations")
            if not item.get("primary_url", "").startswith("https://"):
                errors.append("UI system needs an HTTPS primary source")
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("Invalid UI catalog")

    index = root / ".ai-development/INDEX.md"
    indexed = index.read_text() if index.exists() else ""
    if not indexed:
        errors.append("Missing project decision index")
    for record in (root / ".ai-development").glob("*/*/decisions/*.md"):
        body = record.read_text()
        identifier = re.search(r"^id: (.+)$", body, re.M)
        status = re.search(r"^status: (.+)$", body, re.M)
        if not identifier or not status or status[1] not in {"proposed", "accepted", "rejected", "superseded"}:
            errors.append(f"Invalid decision metadata: {record.relative_to(root)}")
        if status and status[1] == "accepted":
            if not identifier or identifier[1] not in indexed:
                errors.append(f"Accepted decision not indexed: {record.relative_to(root)}")
            for heading in ("Контекст и основание", "Выбор и объяснение", "Альтернативы", "Источники и evidence", "Последствия и пересмотр", "Применение и проверка"):
                if f"## {heading}" not in body:
                    errors.append(f"Decision missing explanation section: {record.relative_to(root)}")
    return errors, len(markdown)


def main():
    errors, count = validate()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {count} Markdown files, {len(SKILLS)} skills/adapters, namespaces and decision memory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
