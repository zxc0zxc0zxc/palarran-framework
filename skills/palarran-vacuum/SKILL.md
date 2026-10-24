---
name: palarran-vacuum
description: Review and clean explicitly disposable intermediates while preserving plans, results and active memory. Use for /palarran:vacuum.
---

# /palarran:vacuum [--long] [--plan]

Read the target AGENTS, private .palarran/INDEX.md and applicable accepted decisions. Follow [decision memory](../../docs/skills/decision-memory.md) and the mandatory [global memory cycle](../../docs/skills/global-memory.md), without recursively invoking this same memory skill. `--plan` performs no network calls or writes.

Mandatory guides: [overview](../../docs/memory/README.md), [sources](../../docs/memory/sources.md), [architecture](../../docs/memory/architecture.md), [contract](../../docs/memory/contract.md), [operations](../../docs/memory/operations.md), [workflow](../../docs/memory/workflow.md), and [context package](../../docs/memory/context-package.md). The target owns context; the library provides instructions. Memory is evidence, never execution authority.

1. Inspect task scope, canonical plan, final result, verification evidence, active handoff, budgets, pending operations and rollback references. These are protected. No cleanup by age, vague temp names, git clean/reset, Docker prune or whole-root deletion.
2. Build a private candidate JSON list of exact relative paths and reasons for explicitly disposable untracked regular files under .palarran task scratch or memory/intermediate. Use `memory_vacuum.py --target TARGET --input CANDIDATES` to produce the path/hash/size/inode proposal. This preflight performs no deletion; --plan stops here.
3. Present the concrete deletion list unless the existing user scope already authorizes these exact disposable artifacts. Save the reviewed proposal privately, then use `memory_vacuum.py --target TARGET --input PROPOSAL --apply APPROVED_SHA256`. Any hash/ownership/path/tracked-file drift blocks preflight. A partial I/O outcome retains a receipt and requires reconciliation, never replay.
4. Keep plan, result/report, decisions, final checks, active sessions, progress, budgets, unknown-operation intents, checkpoints, secrets and backups. Do not remove user files, code or protected parent directories. Empty-directory pruning is not implemented.
5. --long is a separate exact-ID archive/retraction proposal, not physical deletion. The CLI reports REMOTE_REVIEW_REQUIRED without network/mutation. Where an already-authorized reviewer operation is available, recheck references and perform only the reviewed status retraction through the existing API; otherwise leave NOT_RUN. No unrestricted Cypher, file deletion or artifact garbage collection.
6. Report deleted paths, preserved artifacts, exact receipt and pending gates. Cleanup completion does not imply task verification or erase historical evidence.
