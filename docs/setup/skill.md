# /palarran:setup: one entrypoint

Mandatory alongside [installation/safe updates](README.md), [decision memory](../skills/decision-memory.md) and [global loop](../skills/global-memory.md). Documentation precedes implementation; primary sources/dates are in README. Also checked 2026-10-24: [Claude skills](https://code.claude.com/docs/en/skills)—standalone skill names differ from plugin namespaces; [Git merge](https://git-scm.com/docs/git-merge)—preserving local changes and three-way basis. Dispatcher/ownership rules are our engineering choices, not vendor guarantees.

## Resolve context

Arguments: `/palarran:setup {target?} [--client codex|claude|both] [--plan]`. Target is an explicit directory or current project root; clarify only target if ambiguous. Do not select the library checkout instead of the app. Read target AGENTS/INDEX/accepted ADRs. New installs choose the current Codex/Claude agent; both clients only if requested. Updates inherit client from receipt without expanding scope.

Source is a complete trusted palarran checkout with committed HEAD or verified public snapshot. Customized installed libraries are not update sources. Bootstrap-only plugins need full source: use an existing trusted checkout; otherwise clone the known repository into a new dedicated directory and verify origin/HEAD. Never reset/stash/pull others' changes or run remote-shell pipes. Under --plan no clone/fetch/install: missing source is a blocker. For ordinary unpinned updates the agent checks known-origin default-branch HEAD readonly (`git ls-remote --symref URL HEAD`). If trusted checkout is behind, obtain a new separate checkout/verify origin/exact commit without changing the old one. Explicit user pins win; inaccessible remotes cannot be called latest. CLI itself does not fetch/update source; record selected revision, never distribute dirty/untracked content.

## Automatic selection

| Target state | Action |
| --- | --- |
| No receipt, no library/incomplete transaction | Install after collision preflight |
| Existing valid receipt | Guarded update, receipt-defined scope |
| Matching revision | Replace nothing, readonly memory check |
| Corrupt receipt, library without receipt, pending transaction | Stop, preserve everything, show recovery/review |
| Overlapping local/upstream edits | CONFLICT; no force/reset/reinstall |

```sh
python3 /TRUSTED/palarran/scripts/project_setup.py setup --source /TRUSTED/palarran --target /ABSOLUTE/project --plan
python3 /TRUSTED/palarran/scripts/project_setup.py setup --source /TRUSTED/palarran --target /ABSOLUTE/project
```

First install adds `--client codex` or `--client claude`; updates without client inherit. `--plan` uses local preflight only, writes no ADR/policy and connects no memory. Normal execution records decisions before dependent writes. README holds detailed merge/backup/rollback guarantees; do not duplicate implementation in skills.

## Memory and outcome

Fresh installs check only the fresh pinned bundle; updates check pristine release, never preserved project scripts/hooks. Bounded initialize/list/search with --global, without models/service writes. Missing memory yields INSTALLED_MEMORY_NOT_READY / UPDATED_MEMORY_NOT_READY / UNCHANGED_MEMORY_NOT_READY and exit2; files may already be installed successfully. Fix prerequisites within existing authorization, rerun doctor, never reinstall. Project setup excludes user MCP/tunnel/policy and transfers no credentials. Unknown update outcome means recovery, not retry.

Response: action/status, source revision/client, preserved content/conflicts, memory CONNECTED or exact gap, `.ai-tools/USAGE.md` path, 2–3 examples. Codex standalone: `$palarran-setup`, `$palarran-backend-plan`, `$palarran-frontend-build`; Claude standalone: `/palarran-setup`, `/palarran-backend-plan`. `/palarran:setup` is a namespace adapter/plugin; do not promise it after ordinary discovery install. Natural-language requests can ask “connect or update palarran and check memory.” Updates preserve custom USAGE; still report current commands from the installed skills index. Setup starts no frontend/backend/ML work. Discovery needs a new session/trust approval; wire PASS does not prove host UI integration.

DoD: receipt-confirmed route, target config/edits preserved under ownership contract, actual health or honest blocker, decision/handoff/usage explanation. Tests are offline/fake; live memory checks are separate, with no paid launches.
