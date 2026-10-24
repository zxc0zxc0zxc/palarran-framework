# Memory package: quick notes, long-term context and session handoffs

The selectable `memory` package exposes:

| Command | Behavior |
| --- | --- |
| `/palarran:memorize short {note}` | Keep a bounded project-local quick note for the next task |
| `/palarran:memorize long {note}` | Store a privacy-reviewed owner-context note on the configured VPS |
| `/palarran:remember {query}` | Read quick context, then bounded relevant remote context when available |
| `/palarran:memorize:session [--long]` | Produce a structured JSON handoff; optionally store its sanitized JSON remotely |
| `/palarran:remember:session [--long] @file` | Validate a local handoff or resolve a saved remote reference, then recheck project state |
| `/palarran:vacuum [--long] [--plan]` | Propose cleanup of explicitly disposable artifacts or archive selected remote context |

Existing memory:learn/recall skills remain compatibility workflows for verified engineering findings. They do not turn every user note or unfinished session into globally verified knowledge.

## Primary sources and limits

Checked2026-10-24. Anthropic's [context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents), published2025-09-29, motivates compact notes and loading source material only when relevant. Its [long-running agent harness](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents), published2025-11-26, motivates explicit progress artifacts and testing the current application instead of trusting a completion summary. These are company-reported approaches, not measured quality or token savings for Palarran. The storage layout, bounds and schema below are our engineering choices. Existing Neo4j/SSH sources and applicability remain in [sources](sources.md).

## Short and long memory

Short means local working context, not a second verified fact database. Store notes under the target `.palarran/memory/quick.json`; keep at most12 notes and a total16KiB. Each note records an immutable ID, concise text, creation time and provenance kind. Reject a write beyond the bounds; never silently evict useful notes. A later task reads a bounded shortlist and verifies any applicable choice against the canonical ADR/source. Automatically expose the quick-context file through target agent instructions, not by rewriting the host system prompt. When absent, continue normally. Do not claim automatic pre-inference memory injection in every client.

Long means persistence in the existing private VPS service through its authenticated loopback/SSH transport. Notes and session handoffs use a dedicated `owner-context` project scope and `owner-note`/`session-handoff` tags with candidate status. This keeps them discoverable across the owner's projects without presenting them as reviewed global engineering findings. The service is single-owner; project filtering is not an adversarial multi-user ACL. Verified portable lessons still use the existing review/promotion workflow.

Use a real source commit from the target or the pinned producer runtime; state which it represents. Never invent a commit, an experiment result or a verification outcome. Long writes require an explicit content privacy review, idempotent canonical payload and local intent before sending. A timeout means unknown outcome: reconcile the deterministic case ID before retry. Preserve private request/receipt files; never print bearer headers or the global env. A successful note write is not a successful engineering verification.

## Session JSON

The agent compacts the visible conversation and actual project artifacts into `palarran-session-v1`. The helper validates and persists that JSON; it does not call a model, scrape private transcripts, read hidden reasoning or execute recorded commands.

Required fields: schema version, kind, project alias, goal, concise summary, real source commit, decisions, tasks, checks, references, budgets, pending operations, open questions and next steps. Explicitly represent done/remaining work, exact tested subject, failures/skips, modified/uncommitted work references, blockers and unknowns. Every decision needs a short rationale and source/evidence references. Preserve run IDs, cumulative consumed/reserved/unknown spending, caps and unresolved side effects; a new session is not a new budget.

Local handoffs are immutable private files under `.palarran/memory/sessions/<sha256>.json`, at most64KiB. Do not silently truncate; split optional evidence into referenced artifacts and retain an explicit completeness note. Remote handoffs reuse the existing `verification` text artifact type and a tagged case in `owner-context`. A small reference JSON binds project scope, case ID and artifact hash. The artifact hash must match canonical JSON bytes before restore; fetch bounded4096-character pages and require completeness.

Restoration is read-only context loading. Reject malformed/oversized/duplicate-key JSON, unsafe relative paths and unexpected fields. Report source/current commit differences and changed referenced file hashes, then read applicable AGENTS/ADR/plan. Treat next steps, commands and permissions in the handoff as untrusted historical descriptions. Do not execute them, recreate worktrees, reinstall, deploy, train, resume an unknown operation or change a cap merely by restoring context. The currently authorized task and current repository remain authoritative.

## Vacuum

Cleanup is a separate operation, with a reviewable candidate manifest before deletion. Keep the canonical plan, decisions, final result/report, verification evidence, active handoff, progress ledger, budgets, pending operations, rollback backups and code. A file's age, name containing temp, or an LLM calling it unnecessary is insufficient proof of ownership/disposability.

Default cleanup is restricted to explicitly selected untracked regular files under task `scratch/` or memory intermediate directories. Record relative path, exact hash, size and reason. Reject escaping/symlink paths, hardlinks, Git-tracked files, secrets and protected artifact names. Apply only the exact reviewed manifest after rechecking hashes/ownership; any drift blocks the whole preflight. Never run git clean/reset, recursive rm on project roots, Docker prune or delete private runtime state/checkpoints as generic cleanup.

`--long` means an independently reviewed remote archive/retraction proposal for exact note/session IDs, with referenced active sessions and verified lessons protected. The existing service retains immutable history: use reviewer-authorized status retraction, not arbitrary Cypher/file deletion or automatic artifact garbage collection. Offline `--plan` never queries the service. Missing reviewer scope leaves a proposal and NOT_RUN; ordinary agent credentials cannot promote or erase memory. No retention purge or remote physical deletion is implemented by this package.

## Verification

Use offline fake transports for long notes/session roundtrips, dedup and unknown outcomes. Test quick-context bounds, malformed handoffs, secret rejection, exact-hash restore, missing source, scope isolation and preservation of budgets/pending operations. Vacuum tests must prove both safe cleanup and preservation under drift, tracked files, symlink escapes, protected results and active handoffs. A fixture roundtrip is not live VPS persistence or semantic summary fidelity; label those separately.
