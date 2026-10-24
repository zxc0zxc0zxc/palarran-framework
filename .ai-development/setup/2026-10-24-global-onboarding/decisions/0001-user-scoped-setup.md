---
id: setup/2026-10-24-global-onboarding/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Stable global MCP and explicit project setup

## Контекст и основание

Direct user request overrides repository no-global-config default for this task only. Global env already exists owner0600. Codex official MCP/skills, Claude Code skills/MCP and local launchd.plist inspected2026-10-24. No paid agent run needed to prove JSON-RPC connectivity.

## Выбор и объяснение

Export a committed public library snapshot, excluding journals/state/secrets and dirty work, into versioned private global runtime. Codex MCP config uses stable Python path without tokens in argv/config; backups before mutation. macOS user LaunchAgent RunAtLoad/KeepAlive/ThrottleInterval manages strict-key loopback SSH tunnel using global env, no login-shell environment assumptions. No before-login or post-suspend uninterrupted availability promise.

Project installer supports Codex .agents/skills and Claude .claude/skills, relative links into project-local public bundle, preserved user configs/AGENTS, private local journal, complete usage and bounded real MCP doctor. Plan mode writes nothing/calls no server. Project install alone does not authorize global config/launchd, secret creation or remote deploy. Claude project MCP may require client approval; no permissions bypass.

## Альтернативы

Pointing global MCP at mutable working checkout breaks on move/delete and can include unrelated work. Copying SKILL.md alone loses shared docs/templates/helpers. Raw session import and global reviewer tool access are not onboarding. Global config operations separate from project install.

## Источники и evidence

Primary dated verification links in docs/setup/README.md; macOS man launchd.plist: KeepAlive, RunAtLoad and throttling. Actual CLI mcp add/get help and credential-free SSH test. Host/config/user approval from this task.

## Последствия и пересмотр

Pinned library snapshots need explicit upgrade, not silent remote main execution. LaunchAgent logs private and no secret values; failure/backoff visible. MCP config change may need client restart for discovery. Artifact validation and real wire are distinct from observed host UI integration.

## Применение и проверка

Docs before scripts. Offline conflicts/symlink/repeat/plan/env/doctor tests, temp target end-to-end. Actual macOS launchctl/Codex config and memory JSON-RPC, tunnel restart recovery. No model/API paid trials, no app code changes or global Claude installation implied.
