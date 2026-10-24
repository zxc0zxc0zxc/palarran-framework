# Update the framework while preserving project changes

Stable ID: `palarran.framework.update`; version: `1.0.0`; reviewed: **2026-10-24**. Baseline, supported clients/locales/packages and shared preflight: [runbook index](README.md). Operation: ownership-aware update of an existing project installation, with explicit guarded recovery. Read the [existing update contract](../README.md) before execution.

## Applicability and non-secret inputs

Require an existing valid `.ai-tools/installation.json`, matching library marker, receipt-owned discovery links and an existing trusted local incoming source at an exact revision. Resolve the target, installed revision/client/package preferences, incoming pin, observed local changes, authorized update scope, private evidence directory and recovery contact/owner. Keep client writers stopped during swap/recovery. Use the existing Python/POSIX environment; do not install a replacement toolchain.

The installed receipt defines client/package/language scope. The proposed ten-package regrouping does not replace the current 15-ID installer contract. Do not pass package or locale flags to `update`: current direct-update dispatch does not apply them. Do not use ignored flags as evidence that reselection occurred. An explicit `--client` may only equal the receipt client; omit it to inherit. A requested scope/locale migration needs a reviewed versioned extension rather than reinstall or silent widening. Legacy receipts without preferences retain their legacy selection behavior; document that absence, do not invent a historical package choice.

This runbook does not upgrade global runtimes, user MCP entries, SSH tunnels or owner policy. It does not install coordination chat, dependencies, skills on a VPS, applications or models. Updates preserve AGENTS.md, CLAUDE.md, `.mcp.json`, project/global configuration, private env and application code byte-for-byte; target decision/index records are updated separately. Customized `.ai-tools/USAGE.md` is retained. Unchanged managed USAGE may be regenerated for the new pin.

## Preflight and deterministic merge rules

Complete shared source/path checks, verify receipt/marker linkage and preserve private before-state hashes. If `.ai-tools/backups/active-update.json` exists, skip apply and use recovery below. A corrupt/partial installation or unowned discovery link is not an install candidate. Read current library ownership metadata rather than assuming its files still equal upstream.

The updater compares old upstream hashes, local bytes and incoming upstream hashes. It does not invoke Git merge, project hooks or merge drivers:

| State | Result |
| --- | --- |
| Local equals old upstream | Incoming file/addition/removal may replace the old content |
| Local equals incoming | Accept matching content |
| Incoming equals old upstream, local differs | Preserve local edit or deletion |
| Both changed differently | `CONFLICT`, before replacement |
| New upstream path collides with unowned local file | `CONFLICT`, even without a safe adoption basis |
| Upstream removes a skill with preserved local resources | `CONFLICT`, review required |
| Unknown regular local file not colliding with upstream | Preserve it and mark customization |
| Symlink/special file, unsafe path or changed discovery link | Reject/stop; never carry automatically |

Local modes and file/directory collisions also matter; do not reduce the preflight to text differences. Export/install cannot use a customized carried library as public source. The update keeps a pristine release separately so that health never executes preserved local scripts or customized project MCP declarations.

## Offline plan

Use a trusted complete incoming source rather than an installed/customized launcher. All arguments are reviewed local non-secret paths:

```sh
PALARRAN_SOURCE='/ABSOLUTE/trusted-incoming-palarran-checkout'
PALARRAN_TARGET='/ABSOLUTE/existing-project'
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" update \
  --source "$PALARRAN_SOURCE" --target "$PALARRAN_TARGET" --plan
```

Expected exit `0`, JSON `status: UPDATE_PLANNED`, `from_revision`, incoming `revision`, inherited `client`, selected `skills`, `preserved_local_files`, `conflict_count: 0`, `writes: 0`, `network: false`, `model_calls: 0`. Same-revision plans also say `UPDATE_PLANNED`; they do not perform the later health check. No source fetch, target write, lock-file creation, memory call or global mutation occurs.

Exit `2` with `CONFLICT` means no replacement was performed. The report lists at most 20 conflicts plus the total count; review the full ownership comparison privately rather than assuming the displayed subset is complete. Exit `2` with `RECOVERY_REQUIRED` identifies the pending backup; use recovery. Generic incomplete stderr, a different pin/client or an unexpected result stops execution. Do not bypass conflicts with force, deleting local files or switching to install. Preserve both variants and propose a reviewed resolution/versioned extension.

## Authorized apply and read-back

When the planned mutation and bounded memory read are within existing user authorization, continue without a repeated approval question:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" update \
  --source "$PALARRAN_SOURCE" --target "$PALARRAN_TARGET"
```

After full preflight the updater acquires a nonblocking single-host lock, repeats state checks, creates a private transaction backup/candidate and pristine release, writes durable intent and a target decision, then swaps the library, owned discovery links, receipt and unchanged managed USAGE. It commits the transaction marker before bounded global-memory health. This multi-file operation is not ACID or a cross-machine lock. Do not run another writer against the same target.

| Exit/status | File result | Next step |
| --- | --- | --- |
| `0` / `UPDATED` with nested memory `PASS` | New pin installed | Verify receipt, links and preservation; report memory separately |
| `0` / `UNCHANGED` with memory `PASS` | Same pin, no update writes | Report unchanged plus observed wire connectivity |
| `2` / `UPDATED_MEMORY_NOT_READY` | Update completed, health failed | Keep new receipt/backup; fix only authorized prerequisites, then doctor; no replay |
| `2` / `UNCHANGED_MEMORY_NOT_READY` | Same pin, health failed | No update needed; investigate authorized connectivity and doctor |
| `2` / `CONFLICT` | Replacement not begun | Preserve local variants; review exact conflicts |
| `2` / `ROLLED_BACK` from update | Apply failed and guarded restore completed | Verify restored pin; report failed update and preserve evidence |
| `2` / `RECOVERY_REQUIRED` | Current state needs reconciliation | Stop and use guarded recovery |
| Any `journal: WRITE_FAILED` | File/health result may already be complete | Reconcile actual state and preserve external evidence; do not replay to repair a journal |
| Generic incomplete stderr, lost output or interrupted process | Unknown | Read back transaction/receipt/current bytes before another mutation |

A top-level `network: true` means the helper attempted health; it is not proof of connectivity. Health uses pristine public release bytes and `--global`, with no application/model execution. `CUSTOMIZED_NOT_VERIFIED` reports a carried library or project launcher customization; global wire PASS does not verify that customization. `DECLARED_NOT_UI_VERIFIED` is also not client UI proof. Same-revision status may omit this integration field; absence does not establish verification.

Independently read back the new receipt/revision, source marker, selected discovery links and library state against the reported source/local overrides. Compare protected settings/app hashes to before-state. Confirm pending intent is absent for a completed update and preserve the backup reference returned by the helper. Keep `.ai-tools/releases/` pristine and private backups out of exports/Git. Do not run customized project scripts to obtain a health result.

After a changed connectivity prerequisite, run only the authorized read check:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" doctor \
  --source "$PALARRAN_TARGET/.ai-tools/library" --target "$PALARRAN_TARGET"
```

For update-version markers this resolves the cached pristine release. Expected exit `0`, `PASS`, `CONNECTED`, six declared tools, at most three cards, zero writes/model calls. Exit `2` leaves health NOT_READY. Never dump cards or run a paid/model task as a connection test. If health is outside current scope, stop before normal update because it includes that read; return the already prepared offline proposal and identify only the missing read scope.

## Unknown outcomes and guarded recovery

Stop installation writers and reconcile receipt, library marker/current hashes, links, `.ai-tools/backups/active-update.json` and the referenced transaction's phase/before/after signatures. Do not clear locks/intents or delete failed candidates to force a rerun. A timeout or missing response is not proof that the swap failed. A completed matching new state with no pending intent needs verification/doctor, not a second update. A pending intent blocks update until guarded recovery.

Plan recovery without writes/network:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" rollback \
  --target "$PALARRAN_TARGET" --plan
```

Expected exit `0`, `ROLLBACK_PLANNED`, exact owned `backup`, `writes: 0`, `network: false`; or `NO_PENDING_UPDATE`, `writes: 0` when no active marker exists. The latter does not prove all current files are healthy. A completed update rollback requires its explicit retained backup because its active marker was removed. Set `PALARRAN_BACKUP` only to the reviewed reference returned by the update/transaction, not an arbitrary external directory:

```sh
PALARRAN_BACKUP='.ai-tools/backups/update-REPLACE_WITH_RECORDED_32_HEX_ID'
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" rollback \
  --target "$PALARRAN_TARGET" --backup "$PALARRAN_BACKUP" --plan
```

The implementation accepts only `.ai-tools/backups/update-` followed by exactly 32 lowercase hexadecimal characters and validates all owned before/after trees, links, receipt and USAGE. The placeholder above must be replaced; it is deliberately invalid as written. A failed guard stops before restore. Preserve concurrent user edits and backups; never alter expected hashes, force overwrite or use Git reset/clean.

When the exact restore is already authorized and its plan passed, execute the same rollback command without `--plan`:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" rollback \
  --target "$PALARRAN_TARGET" --backup "$PALARRAN_BACKUP"
```

Expected exit `0`, `ROLLED_BACK`, prior `revision`, exact `backup`, `memory: NOT_CHECKED`. This differs from an update operation reporting `ROLLED_BACK` with exit `2`. Verify restored ownership and protected file hashes independently; run doctor only within the existing read scope. Recovery restores library, links, receipt and USAGE, retaining transaction/journal history and any rolled-forward directory. It does not reverse global changes, app/data migrations or automatically clean retained files. A second rollback is not an assumed idempotent operation; reconcile current state first.

If recovery guards fail, retain current/old/candidate variants and draft a versioned recovery extension with exact observed signatures and preservation gates. No automated retries, dependency installs, source replacement or budget increase are permitted by this runbook. Backup deletion requires separately scoped reviewed cleanup.

## Evidence and handoff

Record runbook ID/version, incoming implementation/pin, old/new revisions, target alias/path, inherited client/preferences, preserved local file count/list, conflicts/count, exact redacted command/exit/status, receipt and protected-file read-back evidence, transaction/backup reference and journal result. Report file result, memory result and client discovery separately, with remaining gates marked NOT_RUN/NOT_READY. Preserve `.palarran/setup/update-...` decision/handoff and append the target index only within the coordinator's ownership.

Explain the next already authorized action: finish read-back, retry doctor after an observed prerequisite change, or guarded recovery. For unsupported cases supply the extension proposal defined in the [runbook structure](README.md). Do not present a versioned document, passing offline plan or successful file swap as production/chat-service acceptance.
