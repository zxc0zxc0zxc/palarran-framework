#!/usr/bin/env python3
"""Validate an implementation execution ledger and sync its marked plan section; never run tests."""

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
import os
from pathlib import Path
import re
import tempfile

START = "<!-- backend-progress:start -->"
END = "<!-- backend-progress:end -->"
STATES = {"pending", "in_progress", "implemented", "integrated", "verified", "blocked", "deferred"}
ACTIVE = {"in_progress", "implemented", "integrated", "verified"}


def commit(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{7,64}", value) is not None


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["Ledger must be an object"]
    if data.get("schema_version") != 1:
        errors.append("Unsupported schema_version")
    for key in ("plan_id", "plan_revision", "execution_id"):
        if not nonempty(data.get(key)):
            errors.append(f"Missing {key}")
    if not commit(data.get("source_commit")):
        errors.append("source_commit must identify the source baseline")
    head = data.get("integration_commit")
    if head is not None and not commit(head):
        errors.append("Invalid integration_commit")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a nonempty list"]
    if not all(isinstance(task, dict) and nonempty(task.get("id")) for task in tasks):
        return errors + ["Every task needs an id"]
    by_id = {task["id"]: task for task in tasks}
    if len(by_id) != len(tasks):
        errors.append("Duplicate task IDs")

    def checks(items, label, subject):
        if not isinstance(items, list):
            errors.append(f"{label}: checks must be a list")
            return []
        seen, required = set(), []
        for item in items:
            if not isinstance(item, dict) or not nonempty(item.get("id")):
                errors.append(f"{label}: invalid check id")
                continue
            cid = item["id"]
            if cid in seen:
                errors.append(f"{label}: duplicate check {cid}")
            seen.add(cid)
            if not isinstance(item.get("required"), bool):
                errors.append(f"{label}/{cid}: required must be boolean")
            if item.get("required") is True:
                required.append(item)
            status = item.get("status")
            if status not in {"PASS", "FAIL", "NOT_RUN"}:
                errors.append(f"{label}/{cid}: invalid status")
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not all(nonempty(v) for v in evidence):
                errors.append(f"{label}/{cid}: evidence must be a list of safe references")
            if status in {"PASS", "FAIL"} and (not evidence or not commit(item.get("subject_commit"))):
                errors.append(f"{label}/{cid}: observed result needs evidence and subject_commit")
            if status in {"FAIL", "NOT_RUN"} and not nonempty(item.get("reason")):
                errors.append(f"{label}/{cid}: missing reason")
            if status == "PASS" and (not commit(subject) or item.get("subject_commit") != subject):
                errors.append(f"{label}/{cid}: PASS is stale for the integration commit")
        return required

    for task in tasks:
        label, state = task["id"], task.get("status")
        if state not in STATES:
            errors.append(f"{label}: invalid task status")
        if task.get("plan_revision") != data.get("plan_revision"):
            errors.append(f"{label}: stale plan_revision")
        if not nonempty(task.get("owner")):
            errors.append(f"{label}: missing owner")
        deps = task.get("depends_on")
        if not isinstance(deps, list) or not all(nonempty(v) for v in deps):
            errors.append(f"{label}: invalid depends_on")
            deps = []
        for dep in deps:
            if dep not in by_id or dep == label:
                errors.append(f"{label}: unknown/self dependency {dep}")
            elif state in ACTIVE and by_id[dep].get("status") not in {"integrated", "verified"}:
                errors.append(f"{label}: dependency {dep} is not integrated")
        commits = task.get("code_commits")
        if not isinstance(commits, list) or not all(commit(v) for v in commits):
            errors.append(f"{label}: invalid code_commits")
        if state in {"implemented", "integrated", "verified"} and not commits:
            errors.append(f"{label}: missing code commits")
        integrated = task.get("integration_commit")
        if integrated is not None and not commit(integrated):
            errors.append(f"{label}: invalid integration_commit")
        if state in {"integrated", "verified"} and not commit(integrated):
            errors.append(f"{label}: missing integration commit")
        if state in {"blocked", "deferred"} and not nonempty(task.get("reason")):
            errors.append(f"{label}: missing blocker/deferral reason")
        required = checks(task.get("checks"), label, integrated)
        if state == "verified" and (not required or any(c.get("status") != "PASS" for c in required)):
            errors.append(f"{label}: verified requires passing required checks")

    visiting, visited = set(), set()

    def visit(tid):
        if tid in visiting:
            errors.append("Dependency cycle")
            return
        if tid in visited:
            return
        visiting.add(tid)
        deps = by_id[tid].get("depends_on")
        if isinstance(deps, list):
            for dep in deps:
                if isinstance(dep, str) and dep in by_id:
                    visit(dep)
        visiting.remove(tid)
        visited.add(tid)

    for tid in by_id:
        visit(tid)
    required = checks(data.get("gates"), "feature gates", head)
    if not required:
        errors.append("At least one required feature gate is needed")
    return errors


def complete(data):
    if validate(data):
        return False
    required = [gate for gate in data["gates"] if gate["required"]]
    return (bool(data["tasks"]) and all(t["status"] == "verified" for t in data["tasks"])
            and bool(required) and commit(data.get("integration_commit"))
            and all(g["status"] == "PASS" and g["subject_commit"] == data["integration_commit"] for g in required))


def cell(value):
    return str(value or "-").replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")


def render(data):
    tasks = data["tasks"]
    total = len(tasks)
    coded = sum(t["status"] in {"implemented", "integrated", "verified"} for t in tasks)
    integrated = sum(t["status"] in {"integrated", "verified"} for t in tasks)
    verified = sum(t["status"] == "verified" for t in tasks)
    verdict = "VERIFIED" if complete(data) else "INCOMPLETE"
    lines = [f"Plan: {cell(data['plan_id'])} / {cell(data['plan_revision'])}; execution: {cell(data['execution_id'])}.",
             f"Integration commit: {cell(data.get('integration_commit'))}. Status: **{verdict}**.",
             f"Implemented {coded}/{total}; integrated {integrated}/{total}; verified {verified}/{total}.",
             "", "| Task | State | Owner | Integration commit | Remaining / reason |", "|---|---|---|---|---|"]
    for task in tasks:
        mark = "[x]" if task["status"] == "verified" else "[ ]"
        lines.append("| " + " | ".join([f"{mark} {cell(task['id'])}", cell(task["status"]), cell(task["owner"]),
                     cell(task.get("integration_commit")), cell(task.get("reason"))]) + " |")
    lines += ["", "| Gate | Required | Status | Subject commit | Evidence / remaining |", "|---|---|---|---|---|"]
    for gate in data["gates"]:
        detail = "; ".join(gate["evidence"]) if gate["status"] == "PASS" else gate.get("reason")
        lines.append("| " + " | ".join(map(cell, [gate["id"], str(gate["required"]), gate["status"], gate.get("subject_commit"), detail])) + " |")
    lines += ["", "Structural validation is not proof of test execution, Git ancestry or operational SLA."]
    return "\n".join(lines) + "\n"


def sync_plan(path, summary, area="backend"):
    if area not in {"backend", "frontend"}:
        raise ValueError("Unknown progress area")
    start = f"<!-- {area}-progress:start -->"
    end = f"<!-- {area}-progress:end -->"
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Refusing a symlink destination")
    body = path.read_text()
    if body.count(start) != 1 or body.count(end) != 1 or body.index(start) >= body.index(end):
        raise ValueError("Plan needs exactly one ordered pair of progress markers")
    new_body = body[:body.index(start) + len(start)] + "\n\n" + summary + "\n" + body[body.index(end):]
    mode = path.stat().st_mode & 0o777
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temp:
            temp_name = temp.name
            temp.write(new_body)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--area", choices=["backend", "frontend"], default="backend",
                        help="Marker namespace; backend default preserves the legacy CLI")
    parser.add_argument("--plan", type=Path, help="Sync only the marked progress section of this existing plan")
    args = parser.parse_args()
    try:
        data = json.loads(args.ledger.read_text())
        errors = validate(data)
        if errors:
            raise ValueError("; ".join(errors))
        summary = render(data)
        if args.plan:
            if args.plan.resolve() == args.ledger.resolve():
                raise ValueError("Plan and ledger must be different files")
            sync_plan(args.plan, summary, area=args.area)
        print(summary)
    except (OSError, ValueError, TypeError, RecursionError) as error:
        parser.exit(2, f"Progress validation failed: {error}\n")


if __name__ == "__main__":
    main()
