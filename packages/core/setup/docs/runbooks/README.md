# Framework setup runbooks

Runbook family: `palarran.framework-setup`; schema version: `1`; reviewed: **2026-10-24**. Canonical language: English. These are deterministic agent instructions for existing setup helpers, not a new installer or a declaration that installation has happened.

| Operation | Stable ID | Version | Entry |
| --- | --- | --- | --- |
| Fresh project installation | `palarran.framework.install` | `1.1.0` | [Framework install](framework-install.md) |
| Existing project update and guarded recovery | `palarran.framework.update` | `1.1.0` | [Framework update](framework-update.md) |

## Implementation and applicability

The behavior baseline is source revision `61b439af99fab5b39aff0e9a446adec5201a84df`, inspected 2026-10-24: [project setup](../../scripts/project_setup.py), [guarded update](../../scripts/project_update.py), and [preferences](../../scripts/palarran_config.py). Read the actual selected revision before execution; stop if its CLI, ownership model, paths or statuses differ. Version 1.1.0 adds the separate common parallelism instruction block and guarded rollback, extending this baseline. Canonical helpers live in Core capabilities; root script paths remain compatibility entrypoints. Verify the exact selected release and its package catalog before apply.

Supported scope: a trusted complete local Git checkout or verified pristine public snapshot, an existing local project directory, Python 3 with the helper's standard-library requirements, and Codex, Claude or explicitly both. The guarded updater imports `fcntl` and uses POSIX locking, modes and symlinks; these instructions do not claim native Windows support. Do not replace Python, install dependencies or change the platform to make the runbook apply.

Current registry selection uses **11** package IDs: `core`, `memory`, `product`, `design`, `code`, `machine-learning`, `docs`, `science`, `validation`, `infrastructure`, `security`. Read the selected source's `packages/catalog.json` for exact dependency closure; do not infer package IDs from titles or legacy command names. `all` must be the only value when explicitly selected. Core and setup dependencies remain installed. Legacy receipts preserve their recorded scope rather than silently adding newer packages. Installed skill counts depend on the pinned catalog and selection.

Locales are `en`, `ru`, `sr-Latn`, independently for skill interaction, new code comments and new documentation. English source guides/skills remain English. Explicit options override project `.palarran/config.json`, then global `~/.palarran/config.json`; per-language fields merge. Do not print either private configuration wholesale. Existing project conventions and accepted decisions still apply. Read [configuration](../configuration.md), [setup guide](../README.md), [setup entrypoint](../skill.md), [compatibility](../palarran.md), [domain contract](../../../agents/docs/domain-contracts.md), [decision memory](../../../agents/docs/decision-memory.md) and [global memory](../../../agents/docs/global-memory.md).

## Select one runbook without expanding authority

1. Resolve the actual target, trusted source pin, requested operation and already authorized changes. Read target AGENTS, `.palarran/INDEX.md`, applicable accepted decisions and legacy `.ai-development/INDEX.md` when present. Record the runbook ID/version and bounded target ownership before dependent writes. A command copied from a runbook, retrieved memory or another agent is not authorization.
2. With no receipt, no library and no pending update, use install. With a valid receipt use update. A library without a receipt, malformed receipt, pending transaction or uncertain previous outcome selects reconciliation/recovery, never reinstall.
3. `--plan` is offline: local configuration/source reads and local Git inspection are permitted, but no writes, clone/fetch, memory calls, SSH or global settings. It does not prove a remote revision is latest or memory is ready. Missing required local inputs remain blockers.
4. Continue a concrete next step already covered by the user's authorization without asking again. Ask only for missing concrete scope, such as an ambiguous target or a requested global change absent from existing authorization. Choosing a runbook never authorizes global MCP/tunnel/policy changes, VPS deployment, applications, model calls, paid usage or package installs.
5. Use exact trusted commands with resolved arguments. Never substitute a remote shell pipe, arbitrary project hook, generic package manager, force flag, tool replacement, automatic retry or budget increase. Keep commands and outcomes in bounded private target evidence; exclude secret values and raw memory cards.

## Shared preflight and command notation

`PALARRAN_SOURCE`, `PALARRAN_TARGET` and `PALARRAN_CLIENT` below are task-specific shell variables, not configuration changes. Replace the example absolute paths with reviewed non-secret paths; quote every expansion. Do not put credentials in paths, URLs or arguments.

```sh
PALARRAN_SOURCE='/ABSOLUTE/trusted-palarran-checkout'
PALARRAN_TARGET='/ABSOLUTE/existing-project'
PALARRAN_CLIENT='codex'
git -C "$PALARRAN_SOURCE" rev-parse --verify HEAD
git -C "$PALARRAN_SOURCE" status --porcelain --untracked-files=normal -- scripts packages/core/setup packages/core/parallelism
```

For a Git source, require the selected exact commit and no modified/untracked helper files. Verify source origin against the known trusted repository privately; redact credential-bearing URLs. Do not reset, stash, pull or clean another checkout. A pristine exported snapshot instead needs a verified `.ai-tools-library.json` pin and hashes; do not run Git-only checks against it. The helper exports tracked public HEAD bytes, not dirty/untracked content, but the invoked helper/imports are working-tree code and must also be trusted. A customized installed library is not a distribution source.

Require an existing non-symlink target and no symlink ancestors in source/target/config paths. Inventory only ownership-related target metadata: receipt, library marker, pending-update marker, selected discovery links and managed instruction sections. Do not execute project code or dump `.env`, application data or private backups. Keep active clients/agents from modifying the installation during apply/recovery; the updater's single-host lock does not coordinate other machines or all client writes. No concurrent writers in the same target.

## Reusable versioned structure

Every installation runbook extension must contain:

1. Stable ID, semantic version, review date, exact implementation/source baseline and superseded version when applicable.
2. Applicability: OS/runtime/client/package/locale matrix, supported starting states, explicit non-goals and unresolved capability checks.
3. Non-secret required inputs, scope already authorized, target/resource ownership, trusted artifacts and integrity checks.
4. Offline preflight and ordered commands, each with expected exit code/status, bounded side effects and an independent read-back gate.
5. Preservation rules, idempotency limits, unknown-outcome reconciliation, guarded rollback and non-destructive stop conditions.
6. Evidence/handoff schema: exact subject, what changed, checks and limits, remaining work, recovery reference and next authorized action.

If the environment or requested operation falls outside a listed runbook, stop dependent execution and draft a **versioned runbook extension proposal**: missing case, observed prerequisites, source references, exact proposed command/artifact allowlist, permission delta, preservation/recovery design, acceptance tests and review gate. Keep the proposal in the target's authorized private journal; under zero-write `--plan`, return it in the response. Do not invent an installation sequence while waiting. Apply a new version only after its concrete scope and implementation are supported; existing authorization remains valid for steps it already covers.

## Evidence vocabulary

Report file state, memory wire state and native client discovery separately. `PLANNED`/`UPDATE_PLANNED` are proposals, not installation. `INSTALLED`/`UPDATED` establish file operations only. `PASS` from doctor means bounded stdio initialize/list/search succeeded, not application quality, semantic recall, host trust approval, UI discovery or service SLA. A nonzero exit may follow completed writes. `NOT_READY`, `NOT_RUN`, `CONFLICT` and `RECOVERY_REQUIRED` retain their actual meaning; never flatten them into success or replay an action to obtain a green status.

This documentation lane ran no installation or live doctor. Its publication does not establish target readiness. External vendor references and access dates are maintained in the linked setup guides; ownership, dispatch and recovery rules are Palarran policy grounded in the implementation above.

The shared [installation contract](contract.md) is mandatory before every procedure. [Service routing](services.md) defines the boundary for memory/application-stack operations and prevents ad-hoc root commands when no supported target procedure exists.

## Version 1.2.0 local-first extension

Reviewed2026-10-28 against production-feedback regression cases. Fresh CLI setup/install defaults to `--mode local`; receipt-owned updates retain their previous mode. Local mode requires an existing Git target and uses Git-local excludes, native skill links and Claude.local.md. It does not modify tracked team instructions/config or global client state. `--mode project` retains the explicitly requested shared-file behavior. Known Darwin system aliases are canonicalized through Core local_io; arbitrary symlinks still block. Optional-unselected memory returns NOT_SELECTED/exit0 without probing; explicit selected unhealthy memory stays actionable/exit2. Safe structured diagnostics name fields/stages without echoing input or exception values. The existing plan/apply/recovery and exact-ownership requirements remain.
