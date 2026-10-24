#!/usr/bin/env python3
"""Offline skill, adapter, documentation and decision-memory contracts."""
from pathlib import Path
import json
import re
import sys
from functools import lru_cache

# The implementation may live below packages; the stable root helper is the sentinel.
ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "scripts/palarran_paths.py").is_file()
            and ((parent / "packages/catalog.json").is_file() or (parent / "skills/catalog.json").is_file()))
sys.path.insert(0, str(ROOT / "scripts"))
from palarran_paths import source_path, source_resolver


def _json(path, maximum=1024 * 1024):
    def pairs(entries):
        value = {}
        for key, item in entries:
            if key in value:
                raise ValueError("Duplicate JSON field")
            value[key] = item
        return value
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Catalog exceeds byte bound")
    def nonfinite(_):
        raise ValueError("Nonfinite catalog number")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def _inventory(root):
    """Load each target's registry and optional authoritative canonical skill ownership."""
    registry = _json(source_path(root, "skills/catalog.json", required=True))
    if not isinstance(registry, dict) or not isinstance(registry.get("skills"), list):
        raise ValueError("Invalid skill registry")
    skills, adapters = {}, {}
    for row in registry["skills"]:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k] for k in ("skill", "domain", "action", "adapter")):
            raise ValueError("Invalid skill registration")
        name = row["skill"]
        if not re.fullmatch(r"palarran-[a-z0-9-]+", name) or name in skills:
            raise ValueError("Duplicate or invalid skill registration")
        source_path(root, row["adapter"])
        skills[name] = (row["domain"], row["action"])
        adapters[name] = row["adapter"]
    catalog_path = source_path(root, "packages/catalog.json")
    if not catalog_path.exists():
        return skills, adapters, {name: source_path(root, "skills/"+name+"/SKILL.md") for name in skills}, None
    catalog = _json(catalog_path)
    if (type(catalog) is not dict or set(catalog) != {"version", "packages"}
            or type(catalog["version"]) is not int or catalog["version"] != 1
            or type(catalog["packages"]) is not list or not 1 <= len(catalog["packages"]) <= 100):
        raise ValueError("Invalid package catalog")
    paths, package_ids = {}, set()
    for package in catalog["packages"]:
        if (type(package) is not dict or set(package) != {"id", "title", "description", "requires", "capabilities", "skills"}
                or not isinstance(package["id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", package["id"])
                or package["id"] in package_ids or type(package["skills"]) is not list
                or type(package["capabilities"]) is not list):
            raise ValueError("Invalid package declaration")
        package_ids.add(package["id"])
        capabilities = {entry["id"] for entry in package["capabilities"] if isinstance(entry, dict) and isinstance(entry.get("id"), str)}
        for skill in package["skills"]:
            if type(skill) is not dict or set(skill) != {"name", "path", "legacy_path"}:
                raise ValueError("Invalid package skill declaration")
            name = skill["name"]
            if not isinstance(name, str) or name not in skills or name in paths:
                raise ValueError("Package skill coverage differs from registry")
            canonical = source_path(root, skill["path"])
            parts = canonical.relative_to(root).parts
            if (canonical.relative_to(root).as_posix() != skill["path"]
                    or len(parts) != 6 or parts[:2] != ("packages", package["id"])
                    or parts[2] not in capabilities or parts[3:] != ("skills", name, "SKILL.md")
                    or skill["legacy_path"] != "skills/"+name+"/SKILL.md"):
                raise ValueError("Invalid canonical skill path")
            if (root / "packages/layout.json").exists() and source_path(root, skill["legacy_path"]) != canonical:
                raise ValueError("Package catalog and layout disagree")
            paths[name] = canonical
    if set(paths) != set(skills):
        raise ValueError("Package skill coverage differs from registry")
    return skills, adapters, paths, package_ids


def _links(file, body, root, resolver=source_path):
    """Resolve original Markdown links; a stale relative link is never silently remapped."""
    from urllib.parse import unquote
    for match in re.finditer(r"(?<!!)\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[\"'][^\"']*[\"'])?\)", body):
        target = match.group(1) or match.group(2)
        if target.startswith(("https:", "http:", "#", "mailto:")):
            continue
        relative = unquote(target.split("#", 1)[0])
        if not relative:
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", relative) or relative.startswith("/") or "\\" in relative:
            yield target, None
            continue
        import os
        path = Path(os.path.abspath(file.parent / relative))
        try:
            local = path.relative_to(root).as_posix()
            # Canonical metadata check, including symlink rejection, without remapping stale links.
            checked = resolver(root, local)
            if checked != path:
                yield target, None
            else:
                yield target, path
        except (ValueError, OSError):
            yield target, None


def _has_guide(root, path, body, reference, resolver=source_path):
    try:
        expected = resolver(root, reference)
    except (ValueError, OSError):
        return False
    return any(dest == expected and dest.is_file() for _, dest in _links(path, body, root, resolver) if dest is not None)


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
IGNORED = {".git", ".agents", ".palarran", ".ai-development", ".codex", ".claude", ".claude-plugin", ".ai-tools", ".etc", ".terraform", "plans", "artifacts", "node_modules", ".venv", "scratch", ".graphify", "graphify-out"}


MANIFEST_SPECS = [('palarran', 'plugins/palarran/plugin.json', ['agent:eval', 'agent:improve', 'app:verify', 'backend:build', 'backend:plan', 'ci-cd', 'frontend:build', 'frontend:plan', 'infra:plan', 'mcp:build', 'memory:learn', 'memory:recall', 'memorize', 'remember', 'memorize:session', 'remember:session', 'vacuum', 'ml:benchmark', 'ml:cost', 'ml:data', 'ml:hypotheses', 'ml:model', 'ml:plan', 'ml:train', 'product:acquisition', 'product:b2b', 'product:b2c', 'product:compare', 'product:define', 'product:market', 'product:revenue', 'science:preprint', 'setup', 'ui:design', 'ux:design', 'vps:inspect', 'vps:manage']), ('palarran-setup', 'plugins/palarran-setup/plugin.json', ['setup']), ('palarran-memory', 'plugins/palarran-memory/plugin.json', ['learn', 'recall', 'memorize', 'remember', 'memorize:session', 'remember:session', 'vacuum']), ('palarran-vps', 'plugins/palarran-vps/plugin.json', ['inspect', 'manage']), ('palarran-mcp', 'plugins/palarran-mcp/plugin.json', ['build']), ('palarran-app', 'plugins/palarran-app/plugin.json', ['verify']), ('palarran-science', 'plugins/palarran-science/plugin.json', ['preprint']), ('palarran-agent', 'plugins/palarran-agent/plugin.json', ['eval', 'improve']), ('palarran-ml', 'plugins/palarran-ml/plugin.json', ['benchmark', 'cost', 'data', 'hypotheses', 'model', 'plan', 'train']), ('palarran-product', 'plugins/palarran-product/plugin.json', ['acquisition', 'b2b', 'b2c', 'compare', 'define', 'market', 'revenue']), ('palarran-backend', 'plugins/palarran-backend/plugin.json', ['build', 'plan']), ('palarran-frontend', 'plugins/palarran-frontend/plugin.json', ['build', 'plan']), ('palarran-ui', 'plugins/palarran-ui/plugin.json', ['design']), ('palarran-ci-cd', 'plugins/palarran-ci-cd/plugin.json', ['configure']), ('palarran-infra', 'plugins/palarran-infra/plugin.json', ['plan']), ('palarran-ux', 'plugins/palarran-ux/plugin.json', ['design'])]


def validate(root=ROOT):
    root = Path(root).absolute()
    errors = []
    try:
        skills, adapters, skill_paths, package_ids = _inventory(root)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        return ["Invalid skill registry, package catalog or source layout"], 0
    # A bounded map snapshot is private to this validation operation.
    resolve_snapshot = source_resolver(root)
    # Snapshot-local cache bounds repeated target checks; every validate() starts fresh.
    @lru_cache(maxsize=8192)
    def cached_source(source_root, reference):
        return resolve_snapshot(reference) if Path(source_root) == root else source_path(source_root, reference)
    def resolve(reference):
        try:
            return cached_source(root, reference)
        except (ValueError, OSError):
            errors.append("Unsafe source reference: " + reference)
            return root / ".invalid-source-reference"
    module_roots = ('memory', 'mcp', 'orchestrator', 'scripts', 'tests', 'skills', 'docs', 'templates', 'plugins', 'examples')
    instructions = {root / "AGENTS.md"}
    if package_ids is None:
        instructions.update(resolve(area + "/AGENTS.md") for area in module_roots)
    else:
        instructions.update(root / "packages" / area / "AGENTS.md" for area in package_ids)
    instructions.update(path for path in root.rglob("AGENTS.md") if not set(path.relative_to(root).parts).intersection(IGNORED))
    for path in sorted(instructions):
        name = path.relative_to(root).as_posix()
        limit = 6144 if name == "AGENTS.md" else 4096
        if not path.is_file() or path.is_symlink():
            errors.append('Missing regular instruction file: ' + name)
        elif path.stat().st_size > limit:
            errors.append('Instruction budget exceeded or empty: ' + name)
        else:
            try:
                if not path.read_text(encoding='utf-8').strip():
                    errors.append('Instruction budget exceeded or empty: ' + name)
            except (OSError, UnicodeError):
                errors.append('Invalid instruction text: ' + name)
    for name in ('docs/skills/agents-authoring.md', 'docs/skills/graph-context.md', 'docs/skills/domain-contracts.md',
                 'templates/agents/root.md', 'templates/agents/module.md'):
        if not resolve(name).is_file():
            errors.append('Missing context contract: ' + name)
    markdown = sorted(path for path in root.rglob("*.md") if not set(path.relative_to(root).parts).intersection(IGNORED))
    for file in markdown:
        if file.is_symlink():
            errors.append(f"{file.relative_to(root)}: symlink Markdown source")
            continue
        try:
            body = file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(f"{file.relative_to(root)}: invalid Markdown source")
            continue
        if body.count("```") % 2:
            errors.append(f"{file.relative_to(root)}: unbalanced code fences")
        for target, dest in _links(file, body, root, cached_source):
            if dest is None or not dest.exists():
                errors.append(f"{file.relative_to(root)}: broken or unsafe link {target}")
    if package_ids is None:
        actual_skills = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
        if actual_skills != set(skills):
            errors.append("Update validator registration and memory contract for added/removed skills")
    else:
        actual_paths = {path.relative_to(root).as_posix() for path in (root / "packages").rglob("*") if path.name == "SKILL.md" and path.is_file() and not set(path.relative_to(root).parts).intersection(IGNORED)}
        expected_paths = {path.relative_to(root).as_posix() for path in skill_paths.values()}
        legacy_paths = list((root / "skills").glob("*/SKILL.md"))
        if actual_paths != expected_paths or legacy_paths:
            errors.append("Package catalog must cover every canonical skill exactly; no legacy skill shadows")
    for name, (namespace, command) in skills.items():
        path = skill_paths[name]
        if not path.is_file():
            errors.append(f"Missing skill: {name}")
            continue
        body = path.read_text()
        if not body.startswith(f"---\nname: {name}\ndescription: "):
            errors.append(f"Invalid skill frontmatter: {name}")
        if not _has_guide(root, path, body, "docs/skills/global-memory.md", cached_source):
            errors.append(f"{name}: missing automatic global-memory cycle")
        if not _has_guide(root, path, body, "docs/skills/decision-memory.md", cached_source):
            errors.append(f"{name}: missing shared decision-memory contract")
        if namespace == "docs" and command == "artifact":
            base, guides = "documentation", []
            if not _has_guide(root, path, body, "packages/docs/documentation/docs/artifact.md", cached_source):
                errors.append(f"{name}: missing mandatory artifact guide")
        elif namespace == "infrastructure" and command == "incident":
            base, guides = "infra/incident", ["README.md", "coordination.md", "sources.md", "../plan/security-network.md", "../plan/storage-operations.md", "../plan/workflow.md"]
        elif namespace == "core" and command == "share":
            base, guides = None, []
            if not _has_guide(root, path, body, "packages/core/coordination/docs/sharing/README.md", cached_source):
                errors.append(f"{name}: missing task sharing guide")
        elif namespace == "core" and command == "coop":
            base, guides = None, []
            if not _has_guide(root, path, body, "packages/core/coop/docs/README.md", cached_source):
                errors.append(f"{name}: missing repository cooperation guide")
        elif namespace == "git":
            base, guides = "git", ["README.md", "sources.md", command + ".md"]
        elif namespace == "security":
            base, guides = None, []
            for reference in ("packages/security/shared/docs/contract.md",
                              "packages/security/" + command + "/docs/README.md",
                              "packages/security/" + command + "/docs/sources.md"):
                if not _has_guide(root, path, body, reference, cached_source):
                    errors.append(f"{name}: missing mandatory security guide {reference}")
        elif namespace == "skills":
            base, guides = "setup", ["README.md", "skill.md"]
        elif namespace in {"memory", "vps"}:
            base, guides = "memory", ["README.md", "sources.md", "architecture.md", "contract.md", "operations.md", "workflow.md"]
        elif namespace == "mcp":
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
            base, guides = "infra/plan", INFRA_GUIDES + ["low.md", "med.md", "high.md"]
        elif namespace == "ci-cd":
            base, guides = "ci-cd", CI_GUIDES + ["github.md", "gitlab.md"]
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
            reference = str(Path("docs") / base / guide)
            if "/../" in reference:
                import os
                reference = os.path.normpath(reference)
            if not _has_guide(root, path, body, reference, cached_source):
                errors.append(f"{name}: missing mandatory guide {guide}")
        discover = root / ".agents" / "skills" / name
        if (discover.exists() or discover.is_symlink()) and (not discover.is_symlink() or discover.resolve() != path.parent):
            errors.append(f"Invalid discovery link: {name}")
        adapter_path = resolve(adapters[name])
        adapter = adapter_path.read_text() if adapter_path.is_file() else ""
        if "$ARGUMENTS" not in adapter or not (path.relative_to(root).as_posix() in adapter or _has_guide(root, adapter_path, adapter, path.relative_to(root).as_posix(), cached_source)):
            errors.append(f"Invalid command adapter: {name}")
        if not (resolve("docs/skills/global-memory.md").relative_to(root).as_posix() in adapter or _has_guide(root, adapter_path, adapter, "docs/skills/global-memory.md", cached_source)):
            errors.append(f"Adapter omits automatic global memory: {name}")
        if not (resolve("docs/skills/decision-memory.md").relative_to(root).as_posix() in adapter or _has_guide(root, adapter_path, adapter, "docs/skills/decision-memory.md", cached_source)):
            errors.append(f"Adapter omits memory: {name}")

    for level in ("low", "med", "high"):
        profile_path = resolve(f"docs/infra/plan/{level}.md")
        profile = profile_path.read_text() if profile_path.is_file() else ""
        if profile.count("```mermaid") < 2:
            errors.append(f"Profile {level} needs data and delivery diagrams")
    manifest_specs = [(name, path, list(commands)) for name, path, commands in MANIFEST_SPECS]
    for action in ("commit", "history", "conflicts", "mr"):
        if "palarran-git-" + action in skills:
            manifest_specs[0][2].append("git:" + action)
    for profile in ("infrastructure", "ingress", "log", "egress", "code", "cve"):
        if "palarran-security-" + profile in skills:
            manifest_specs[0][2].append("security:" + profile)
    if "palarran-core-share" in skills:
        manifest_specs[0][2].append("core:share")
    if "palarran-core-coop" in skills:
        manifest_specs[0][2].append("core:coop")
    if "palarran-docs-artifact" in skills:
        manifest_specs[0][2].append("docs:artifact")

    if "palarran-infrastructure-incident" in skills:
        manifest_specs[0][2].append("infrastructure:incident")
        for namespace, _, commands in manifest_specs:
            if namespace == "palarran-infra":
                commands.append("incident")
    for namespace, relative, commands in manifest_specs:
        try:
            manifest = _json(resolve(relative))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("commands"), dict):
                raise ValueError("Invalid plugin declaration")
        except (OSError, ValueError, TypeError):
            errors.append(f"Missing or invalid plugin manifest: {namespace}")
            continue
        if manifest.get("name") != namespace or set(manifest.get("commands", {})) != set(commands):
            errors.append(f"Invalid plugin namespace or commands: {namespace}")
        for command in manifest.get("commands", {}).values():
            if not isinstance(command, dict):
                errors.append(f"Invalid plugin command source: {namespace}")
                continue
            source = command.get("source", "")
            if isinstance(source, str) and source.startswith("./"):
                source = source[2:]
            if not isinstance(source, str) or not source or not resolve(source).is_file():
                errors.append(f"Invalid plugin command source: {namespace}")

    catalog_path = resolve("docs/ui/catalog.json")
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

    return errors, len(markdown)


def main():
    errors, count = validate()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {count} Markdown files, {len(_inventory(ROOT)[0])} skills/adapters, namespaces and decision memory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
