#!/usr/bin/env python3
"""Offline repository contract and local link checks. No third-party imports."""
from pathlib import Path
import re
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
markdown = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts and not set(p.parts).intersection({".agents", ".terraform", "plans", "artifacts", "node_modules", ".venv"}))
for file in markdown:
    body = file.read_text()
    if body.count("```mermaid") and body.count("```") % 2:
        errors.append(f"{file.relative_to(ROOT)}: unbalanced code fences")
    for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", body):
        if target.startswith(("http:", "https:", "#", "mailto:")):
            continue
        dest = target.split("#", 1)[0]
        if dest and not (file.parent / dest).exists():
            errors.append(f"{file.relative_to(ROOT)}: broken link {target}")

required = ["README.md", "workflow.md", "security-network.md", "delivery-iac.md",
            "storage-operations.md", "decisions.md", "plan-template.md", "sources.md"]
for level in ("low", "med", "high"):
    path = ROOT / "skills" / f"infra-plan-{level}" / "SKILL.md"
    body = path.read_text()
    if not body.startswith(f"---\nname: infra-plan-{level}\ndescription: "):
        errors.append(f"Invalid skill frontmatter: {path}")
    for guide in required + [f"{level}.md"]:
        if f"../../docs/infra/plan/{guide}" not in body:
            errors.append(f"{path}: missing mandatory guide {guide}")
    discover = ROOT / ".agents" / "skills" / f"infra-plan-{level}"
    if not discover.is_symlink() or discover.resolve() != path.parent:
        errors.append(f"Invalid project skill discovery link: {discover}")
    adapter = (ROOT / ".claude" / "commands" / "infra-plan" / f"{level}.md").read_text()
    if "$ARGUMENTS" not in adapter or f"skills/infra-plan-{level}/SKILL.md" not in adapter:
        errors.append(f"Invalid command adapter: {level}")
    profile = (ROOT / "docs/infra/plan" / f"{level}.md").read_text()
    if profile.count("```mermaid") < 2:
        errors.append(f"Profile {level} needs data and management/delivery diagrams")

manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
if manifest.get("name") != "infra-plan":
    errors.append("Invalid slash-command plugin namespace")
for level in ("low", "med", "high"):
    source = manifest.get("commands", {}).get(level, {}).get("source", "")
    if not source or not (ROOT / source).is_file():
        errors.append(f"Invalid plugin command source: {level}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
print(f"OK: {len(markdown)} Markdown files, 3 skills/adapters and project discovery links")
