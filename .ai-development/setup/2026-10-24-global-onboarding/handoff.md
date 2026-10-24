# Global memory onboarding handoff

## Implemented: setup-v001

- Explicit user-authorized Codex user entry `engineering-memory`, pinned public runtime revision `00be3c8fad8fe6b9dd1896940b6202f45b76332a` under user home. Actual CLI registration resolves from another project. Config backups private; other settings preserved semantically (CLI normalized an empty preexisting node_repl args list).
- Login LaunchAgent `io.zxc0zxc0zxc.memory-tunnel`, RunAtLoad/KeepAlive/throttle, loopback SSH using global env and existing known key. Noninteractive SSH without SSH_AUTH_SOCK works. Owned SSH child termination recovered with new PID in 1.02 seconds; authenticated doctor passed after recovery. Persistent user-requested tunnel remains running.
- Both global and project-declared shared memory launch with explicit --global. Actual registered Codex command initialized/listed/searched successfully from independent project with unrelated ordinary .env. Project env selection remains available for explicit CLI calls; API project scoping is separate.
- Project installer pins committed public files only, native Codex/Claude discovery links (34 skills), preserved target AGENTS/CLAUDE/MCP config, private backups and target decision before dependent writes. Conflicts refuse; repeat is idempotent. No dirty ML/SFT, journals or credentials exported. Usage explains native names and namespace adapter distinction.

## Verification

Eight focused offline installer/doctor tests passed. Actual temporary project installation and six-tool stdio list/search passed; no memory writes or model calls. Validator/factory passed. Full offline suite: 472 tests, 4 optional skips, PASS. Working-tree validator 568 Markdown/34 skills; isolated staged snapshot validator 522 Markdown/34 skills and installer8/packaging4 passed. Factory 100 samples p95 2.489ms/smoke passed; live providers/operational SLA NOT_RUN. Publication receipt in Git; final committed-bundle doctor from its own installed helper PASS (34 skills/six tools/search), existing target AGENTS preserved. Native symlink-parent rejection observed with macOS temp alias; canonical path succeeded.

## Limits and next context

Restart Codex once for client discovery. Current desktop UI tool discovery and Claude UI/trust approval NOT_RUN; wire-level checks do not prove model tool selection. LaunchAgent runs after user login, not before login; sleep/wake/network availability is not a proven SLA. No paid runs, remote deployment, or automatic memory promotion. Runtime remains pinned to verified earlier memory commit until explicit reviewed upgrade. Project upgrade/uninstall is manual and must preserve modified owned files.

Parallel ML/SFT changes predate this scope and remain unstaged/unpublished by this task.
