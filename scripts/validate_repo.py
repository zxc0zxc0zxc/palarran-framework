#!/usr/bin/env python3
"""Offline skill, adapter, documentation and decision-memory contracts."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    **{f"infra-plan-{level}": ("infra-plan", level) for level in ("low", "med", "high")},
    **{f"ci-cd-{provider}": ("ci-cd", provider) for provider in ("github", "gitlab")},
}
INFRA_GUIDES = ["README.md", "workflow.md", "security-network.md", "delivery-iac.md",
                "storage-operations.md", "decisions.md", "plan-template.md", "sources.md"]
CI_GUIDES = ["README.md", "workflow.md", "evidence.md", "architecture.md", "performance.md",
             "security.md", "environments.md", "decisions.md", "skill-contract.md", "sources.md"]
IGNORED = {".git", ".agents", ".terraform", "plans", "artifacts", "node_modules", ".venv", "scratch"}


def validate(root=ROOT):
    errors = []
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
        base = "infra/plan" if namespace == "infra-plan" else "ci-cd"
        guides = INFRA_GUIDES + [f"{command}.md"] if namespace == "infra-plan" else CI_GUIDES + [f"{command}.md"]
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
    for namespace, relative in [("infra-plan", ".claude-plugin/plugin.json"), ("ci-cd", "plugins/ci-cd/plugin.json")]:
        manifest = json.loads((root / relative).read_text())
        expected = {command for ns, command in SKILLS.values() if ns == namespace}
        if manifest.get("name") != namespace or set(manifest.get("commands", {})) != expected:
            errors.append(f"Invalid plugin namespace or commands: {namespace}")
        for command in manifest.get("commands", {}).values():
            source = command.get("source", "")
            if not source or not (root / source).is_file():
                errors.append(f"Invalid plugin command source: {namespace}")

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
