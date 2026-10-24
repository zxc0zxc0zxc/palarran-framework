# Install the framework into an existing local project

Stable ID: `palarran.framework.install`; version: `1.1.0`; reviewed: **2026-10-24**. Baseline and shared gates: [runbook index](README.md). Operation: fresh project installation through the existing `setup` dispatcher, followed by read-only health and ownership verification. No installation is performed by reading this document.

## Applicability and required inputs

Use only when the target has no `.ai-tools/installation.json`, no `.ai-tools/library` and no `.ai-tools/backups/active-update.json`. Existing valid receipts select [update](framework-update.md); partial/corrupt states stop. Read the shared preflight first. Source acquisition, global MCP setup, SSH tunnels, memory-server installation, coordination-chat installation, owner-policy enabling, application work and dependency installation are separate runbooks/scopes.

Required non-secret inputs:

| Input | Required resolution |
| --- | --- |
| Source | Existing trusted complete local checkout at an exact commit, or verified pristine public snapshot; never a customized installed library |
| Target | Existing explicit absolute project directory, distinct from the framework checkout; applicable instructions and prior decisions read |
| Client | Exactly `codex`, `claude` or explicitly requested `both`; use the current requested host when known |
| Packages | Explicit supported package list or checked project/global defaults; `all` only when explicitly selected |
| Languages | All three fields resolved independently to `en`, `ru` or `sr-Latn` by explicit options/project/global precedence |
| Authority | Concrete project file changes and the dispatcher's bounded global-memory read check within existing user scope; absent read-check scope permits file-only install with health NOT_RUN |
| Recovery/evidence | Private target evidence location, pre-change instruction/config hashes and ownership inventory; do not copy secrets |

Ask for missing preferences once when they cannot be inferred from checked configuration. Do not silently select all packages or both clients: the low-level CLI defaults an omitted fresh client to `both`, so this runbook always supplies `--client`. Never assume a global memory profile exists merely because the project requests installation. Credentials are not inputs to these commands; keep secret values in their existing private profile.

## Preflight and offline plan

Complete the shared source/path checks. Resolve conflicting instruction sections, existing skill paths or `.mcp.json` entries by preserving them and stopping; no adoption or overwrite. Existing `.palarran/config.json` must agree with the resolved selection: the installer requires equivalent serialized configuration and will not rewrite a conflicting file. Unknown local JSON fields remain preserved. When configuration is absent, a fresh managed configuration can be created from the resolved package/language fields.

Record original hashes/existence of AGENTS.md, CLAUDE.md, `.mcp.json`, project config and existing target index in private evidence. Do not store their full contents in public output. Fresh installation may append managed onboarding sections, update the target index and, for Claude/both, add the exact project `engineering-memory` launch declaration while preserving unrelated settings. An unrelated entry with that name stops installation. It does not edit Codex user configuration or transfer credentials.

Example resolved selection; substitute the actual reviewed values rather than inheriting these examples:

```sh
PALARRAN_SOURCE='/ABSOLUTE/trusted-palarran-checkout'
PALARRAN_TARGET='/ABSOLUTE/existing-project'
PALARRAN_CLIENT='codex'
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" setup \
  --source "$PALARRAN_SOURCE" --target "$PALARRAN_TARGET" --client "$PALARRAN_CLIENT" \
  --packages code validation --skills-language en --code-language en --docs-language en --plan
```

Expected: exit `0`, JSON `status: PLANNED`, `action: install`, selected `revision`, `client`, nonzero `skills`, `writes: 0`, `network: false`, `model_calls: 0`, `memory: NOT_CHECKED`. `--plan` performs local preflight only, with no installation, target journal writes or memory calls. It does not check the remote default branch. Capture the plan/pin privately and verify that all resolved values match the intended target. Recheck target state if it changes before apply.

Any exit `2`, generic `Setup incomplete` stderr, unexpected action or changed revision is a stop condition. Do not remove an existing library, bypass a collision or repeatedly rerun the command. Missing local source/runtime support requires a versioned extension proposal, not installation of tools.

## Apply within existing authorization

When the concrete project mutation and bounded memory read are already authorized, run the same reviewed command without `--plan`:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" setup \
  --source "$PALARRAN_SOURCE" --target "$PALARRAN_TARGET" --client "$PALARRAN_CLIENT" \
  --packages code validation --skills-language en --code-language en --docs-language en
```

The helper records a target setup decision before dependent installation writes, creates the pinned `.ai-tools/library`, source/ownership manifests and `.ai-tools/USAGE.md`, adds selected native discovery links and updates managed instructions/index. Claude/both may update project `.mcp.json`; unrelated configuration is preserved. Shared public support resources remain available, but only selected skills receive discovery links. It runs no project hooks, app tests, models or deployment.

The dispatcher then uses pristine pinned public bytes for bounded stdio `initialize`, `tools/list` and one `knowledge.search` with at most three cards, through `--global`. The helper's current timeout is 20 seconds; output is limited to 262144 bytes after process completion, not a hard memory/disk quota. Do not expose returned cards or claim unlimited resource protection.

If authority covers **file installation only**, use the exact same selection with operation `install` instead of `setup` (plan first, then apply). Expected exit `0`, `PLANNED` then `INSTALLED`, `memory: NOT_CHECKED`; no health call is made and `action`/dispatcher fields are absent. Report health NOT_RUN. This is a documented low-level route, not permission to skip a check already authorized and required. Do not add a doctor call outside the actual read scope.

## Observe outcome before any next action

| Observed outcome | Meaning and deterministic next step |
| --- | --- |
| Exit `0`, `INSTALLED`, `action: install`, nested memory `PASS`/`CONNECTED` | Dispatcher completed file installation and bounded memory wire check; verify ownership and explain native usage |
| Exit `2`, `INSTALLED_MEMORY_NOT_READY`, memory `NOT_READY` | Files may already be installed; retain receipt, investigate only authorized prerequisites and rerun doctor after resolution, never reinstall to repair network |
| Exit `0`, low-level `install` with `INSTALLED`, `memory: NOT_CHECKED` | Files installed, health NOT_RUN; perform doctor only when that read scope is covered |
| Exit `2` with generic incomplete message or lost output | Outcome unknown; inspect receipt, marker, links, managed files and target decision before any retry |
| Dispatcher reports update/unchanged rather than install | Starting state changed or wrong runbook selected; stop and reconcile using update runbook |

Read back `.ai-tools/installation.json` and the pinned library marker. Verify matching exact source revision, selected skills/client/preferences and owned file hashes/relative links. Compare managed instruction/config changes against the recorded plan; preserve unrelated bytes/content. Read `.ai-tools/USAGE.md` and confirm that application files, private env and global MCP/tunnel/policy stayed outside the mutation. File placement is not native UI discovery. If the client needs restart/trust interaction, describe that remaining step without inventing approval or observed discovery.

For an authorized health retry after prerequisite repair, run only:

```sh
python3 "$PALARRAN_SOURCE/scripts/project_setup.py" doctor \
  --source "$PALARRAN_TARGET/.ai-tools/library" --target "$PALARRAN_TARGET"
```

Expected exit `0`, JSON `status: PASS`, `memory: CONNECTED`, `tools: 6`, `returned_cards` at most `3`, `writes: 0`, `model_calls: 0`. Failure exits `2` and remains NOT_READY. The memory service's six-tool inventory does not grant permission to call mutation tools; doctor invokes only the documented read check. A retry needs a changed prerequisite/evidence, not an automatic loop.

## Idempotency, unknown outcomes and rollback

After a successful setup, the same dispatcher command routes to guarded update; at the same source revision it changes no installed files and repeats health. This does not make fresh installation atomic or justify automatic replay. Direct `install` is not an upgrade command. The install writes multiple objects without an update-style active transaction; an interruption can leave a partial library, links or managed sections. A partial state must not be adopted as a completed installation.

For an unknown outcome, stop writers; inspect only installation-owned metadata and compare against the plan, receipt and before-state. If the complete receipt/owned bytes are consistent, continue with read-only verification. Otherwise retain all evidence and propose an explicit recovery extension for the observed state. Do not delete `.ai-tools` or fabricate a receipt to resume. The update rollback subcommand is not a fresh-install undo facility.

Fresh uninstall/rollback remains a reviewed manual operation: list exact manifest-owned unchanged files/links and managed additions, compare hashes and backups, preserve user edits and private history, then remove/restore only within concrete authorized removal scope. No executable generic delete command is provided because it could erase new work. Preserve backups, journals, global configuration and remote state. Never use reset/clean, force overwrite, automatic cleanup or blanket directory removal.

## Evidence and handoff

Record runbook ID/version, selected source revision/integrity basis, target alias/path, client, package/language resolution, initial state, exact redacted command, exit/status and changed paths. Include receipt/marker verification, preserved settings, memory outcome, UI discovery NOT_RUN unless directly observed, recovery references and any incomplete gate. Retain the setup decision link and private before-state evidence; update the target handoff/index within authorized scope. Explain actual Codex `$palarran-setup` or Claude standalone `/palarran-setup` usage from the installed catalog; unified plugin commands require their separate adapter.

Final status must distinguish files installed, memory connected/not ready/not run, and remaining client interaction. No application acceptance, production readiness, paid quota or service SLA is established by this runbook.

## Common parallelism instructions (1.1.0)

Installation appends a separate `palarran:parallelism` block to the recorded client's AGENTS/CLAUDE instruction files, preserving all original bytes. This applies to ordinary requests and subject skills; native clients remain instruction-based. Before apply resolve the optional Temporal question/profile under [Temporal setup](../temporal.md), preserving explicit project disable and existing global settings. An answer does not grant global writes, Worker startup, deployment or models. Follow the reviewed local Worker procedure only within actual scope, and report its missing readiness honestly.
