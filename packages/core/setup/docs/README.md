# Connect Palarran to a project

A user asks Codex or Claude to install Palarran, check memory and explain its commands. The agent reads this guide and target AGENTS/INDEX, installs the library, runs doctor and reports observed results. Installation does not start application development, training or deployment.

The unified entry is [`/palarran:setup`](skill.md), backed by `project_setup.py setup`. It selects installation/update from the receipt, checks memory and explains native commands. Explicit install/update operations remain available. [Package and language configuration](configuration.md).

## Primary sources

Rolling official documentation checked2026-10-24: [OpenAI MCP](https://developers.openai.com/codex/mcp/) for user configuration and stdio; [OpenAI skills](https://developers.openai.com/codex/skills/) for repository `.agents/skills`; [Claude skills](https://code.claude.com/docs/en/skills) for `.claude/skills`; [Claude MCP](https://code.claude.com/docs/en/mcp) for project `.mcp.json`, approvals and scope. Local macOS `man launchd.plist` defines RunAtLoad, KeepAlive and ThrottleInterval. A login LaunchAgent starts after user login, not as a pre-login system daemon.

## Installation

From a complete trusted Palarran checkout:

```sh
python3 scripts/project_setup.py install --target /ABSOLUTE/project --client codex \
  --packages backend app --skills-language en --code-language en --docs-language en --plan
# Review the proposal, then repeat without --plan.
python3 scripts/project_setup.py doctor --target /ABSOLUTE/project
```

Choose `codex`, `claude` or explicitly `both`. First setup asks for missing packages and each output-language preference; automation supplies flags or checked config. Source distribution includes public tracked files from the selected HEAD commit, excluding dirty/untracked work, Git history, target journals/state and credentials. The pinned library lives in target `.ai-tools/library`; relative discovery links move with the project. Do not install bare SKILL.md files without shared guides/templates/helpers. The manifest records revision and source hashes. Repeating install is not an upgrade mechanism.

An existing skill/config collision, symlink parent, changed owned bundle or modified managed AGENTS section blocks replacement. Preserve existing AGENTS and add a small managed entry; Claude's CLAUDE.md also receives a usage link without replacing rules. Project `.mcp.json` contains a launch command rather than credentials. Do not bypass client approvals: wire connectivity does not prove a trust dialog was accepted.

Install writes a target decision, receipt and usage guide; it executes no application tests, code or hooks. `--plan` writes nothing and performs no network/global configuration changes. Doctor performs bounded actual stdio initialize/list/search with at most3 cards and reports counts/status rather than memory contents. Missing memory is NOT_READY, never PASS. No model is called. Explain `.ai-tools/USAGE.md`, installed commands and remaining gaps. A new/restarted client may be required; do not invent UI discovery evidence.

## Global memory prerequisites

Global env and project overrides follow [memory operations](../../../memory/knowledge/docs/operations.md). The first global MCP and persistent tunnel setup needs explicit owner scope. Project installation does not rewrite user configuration or start launchd. Explain missing prerequisites, and do not ask again for an action already authorized. Never copy global credentials into projects.

Global MCP runs from a pinned public snapshot under `~/.palarran/runtime/<commit>/`, not the mutable checkout. Codex's `engineering-memory` entry stores command/args with explicit `--global`, without bearer/reviewer values. Project Claude MCP and doctor also use `--global`: an app `.env` cannot redirect shared-memory connectivity. Explicit CLI/project integrations can still select a project env. Back up private configuration before changes and do not replace an unrelated same-name entry. Existing global installations require the [coordinated migration](palarran.md), not a silent path rewrite.

The owned macOS LaunchAgent `io.palarran.memory-tunnel` starts at login and restarts SSH with throttling. It uses global env, trusted known_hosts, no agent forwarding, loopback18791 and ExitOnForwardFailure. The SSH key must work noninteractively after login; passwords never belong in plist/env/argv. A network outage does not authorize replaying memory writes. Verify connectivity after sleep/wake; do not promise uninterrupted availability.

## Verification and removal

Check actual registered commands, pinned source bytes, launchctl state and native MCP initialize/list/search from a fresh project CWD. In an explicitly authorized recovery test, stop only the owned SSH child, observe its new PID and repeat authenticated doctor. Do not run a model task just to test connectivity.

Global removal: `codex mcp remove engineering-memory`, then `launchctl bootout gui/UID/io.palarran.memory-tunnel`; remove only owned plist/runtime files after checking references, keeping backups. Project uninstall remains manual: remove only manifest-owned unchanged links/files/managed sections and preserve user edits. No git reset/clean, secret deletion or remote database removal.

## Automatic experience reuse

New skill bundles include the mandatory global-memory guide and `scripts/memory_cycle.py`. After separate owner authorization, `python3 scripts/memory_cycle.py enable` enables bounded recall and verified publication across the owner's projects. Project installation does not enable that policy. Without policy, use local drafts/deferred publication. See the [cycle contract](../../agents/docs/global-memory.md). Existing pinned bundles need a reviewed upgrade; the current remote API does not require new privileges or server deployment for this cycle.

## Safe updates

Primary references checked2026-10-24: [Git merge](https://git-scm.com/docs/git-merge) for three-way concepts and [Python os.replace](https://docs.python.org/3/library/os.html#os.replace) for atomic replacement of one object. Palarran's multi-file update is not an ACID transaction: private intent, backups and guarded recovery remain necessary. The installer never invokes Git merge/hooks/drivers or changes the target Git index.

From a new trusted checkout with committed HEAD:

```sh
python3 scripts/project_setup.py update --target /ABSOLUTE/project --plan
python3 scripts/project_setup.py update --target /ABSOLUTE/project
```

Inherit client and package scope from the receipt; never silently add a client/package or change credentials, user MCP, SSH or owner policy. Preserve AGENTS.md, CLAUDE.md, .mcp.json, .env and app code byte-for-byte. Preserve custom USAGE; installation.json is the authoritative source pin. Regenerate unchanged USAGE for the new release.

Inside the library compare old upstream hashes, local files and incoming upstream. Preserve independent local edits/deletions; accept identical local/incoming content. Overlapping changes and new-path collisions produce CONFLICT before writes. Keep unowned regular files, but never carry symlinks/special files automatically. A removed upstream skill with local edits requires review. `--plan` writes nothing or connects; same-revision updates leave files unchanged and repeat read-only health.

Stop active clients/agents while swapping the library. After full preflight, write private backup/intent and target ADR, then swap the library, owned discovery links and receipt. Never replace user-owned links. `.ai-tools/backups/` is private/ignored and can contain local data. Doctor uses pristine public files in `.ai-tools/releases/`, never carried scripts or project hooks. A customized working library cannot become an export/install source. Global wire PASS does not verify a customized project launcher or client UI; report CUSTOMIZED_NOT_VERIFIED.

After update, global initialize/list/search from target CWD is mandatory. Health failure gives UPDATED_MEMORY_NOT_READY and exit2 even when file updates completed. Repeat doctor after fixing connectivity; do not replay apply for a network failure. No application execution or paid calls are performed.

For ordinary I/O failure, rollback only when current hashes/links match expected transaction state. Crashes or concurrent changes yield RECOVERY_REQUIRED and block new updates. Guarded explicit recovery:

```sh
python3 scripts/project_setup.py rollback --target /ABSOLUTE/project --plan
python3 scripts/project_setup.py rollback --target /ABSOLUTE/project
python3 scripts/project_setup.py rollback --target /ABSOLUTE/project --backup .ai-tools/backups/update-TRANSACTION_ID
```

Rollback refuses to overwrite new user changes. Keep the backup and review the diff; no force/reset/clean or automatic replay. Retain caches/backups/attempt ADRs for review. Project updates do not update older global runtimes/tunnels.

## Optional shared web search

[Keenable retrieval](../../agents/docs/context-retrieval.md) is separate from memory: a global key/header helper and native remote MCP, without a key in project/TOML. Project setup can inspect an existing integration within explicit scope, but never silently install/repair it or disable built-in search. Content quota/usage and actual host discovery are distinct from metadata connectivity.

## Versioned installation procedures

[Core runbooks](runbooks/README.md) bind install/update commands, preconditions, expected statuses, partial-state recovery and source revisions. Agents choose a supported procedure before applying changes. Missing support produces a concrete runbook extension, not an invented installation sequence.

Optional engine setup and actual native/managed integration levels: [Temporal and harness compatibility](temporal.md). A new install asks whether to enable Temporal; updates inherit the checked answer. Project setup never implicitly changes a user's global env or starts a Worker. Common parallelism instructions apply to ordinary requests and every skill. Managed adapters use the common dispatcher; AGENTS/CLAUDE instructions alone are instruction-based.

## Local installation default (1.2)

New `setup` and CLI `install` requests use `--mode local` by default. In an existing Git project, this creates the private store, selected native skill links and `CLAUDE.local.md` for Claude without changing tracked `CLAUDE.md`, `AGENTS.md`, `.mcp.json` or `.gitignore`. Reviewed Git-local exclude entries protect generated private paths. A tracked private output is a conflict; ignore rules do not untrack it. Review the exact mode/paths with `--plan` before applying.

Use `--mode project` only when the shared project-instruction/MCP edits are intended. The low-level `install()` API retains its prior project-mode default for compatibility. Existing receipts retain their recorded mode, including legacy project receipts; update does not silently migrate them. An explicit conflicting mode blocks update. Global configuration is never changed.

Claude loads local instructions from `CLAUDE.local.md`; restart/trust requirements remain client-specific. Codex native skills are discoverable through `.agents/skills`, but local mode does not claim automatic loading of a new project instruction file or activate a global MCP connection. Read `.ai-tools/USAGE.md` and follow the selected skill's bounded entry. Shared instruction activation requires explicit project mode or a separately reviewed client configuration.

Memory is optional when its package is not selected. Such setup returns success with `memory.status: NOT_SELECTED`, records the gap and runs no memory subprocess. Explicitly selected memory that fails the real health probe remains `*_MEMORY_NOT_READY`/exit2. File installation, memory readiness and native UI discovery are separate outcomes. Legacy receipts without a package selection keep their existing health policy.

Diagnostics are safe JSON `{status, code, field, hint}`. Missing preferences identify the packages/language remedy; doctor reports the failed protocol stage without provider contents. Arbitrary exception text and raw tracebacks are never printed. On Darwin, only the expected system root aliases `/tmp`, `/var` and `/etc` are canonicalized; other symlink components remain rejected.
