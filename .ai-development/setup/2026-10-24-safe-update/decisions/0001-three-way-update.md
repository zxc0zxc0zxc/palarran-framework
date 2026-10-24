---
id: setup/2026-10-24-safe-update/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Ownership-aware project skill updates

## Контекст и основание

User requests safe upgrades of already connected skills, preserving project settings/local modifications and checking global memory afterwards. Existing installer intentionally refuses replacement; global Codex MCP/SSH policy already configured. Parallel ML/SFT work remains excluded.

## Выбор и объяснение

Explicit update command from trusted committed public source, three-way hash comparison (old upstream/local/new upstream), no textual auto-merge. Keep local edits/deletions when upstream unchanged; reject overlapping edits, unknown collisions and unsafe paths before writes. Preserve AGENTS/CLAUDE/.env/.mcp.json/app code exactly, inherit installed client scope. Record target ADR before dependent changes. Candidate directory and original backup plus durable pending intent; serialized updates, rollback with exact state guards, no forced overwrite after concurrent user edits. Private backups may contain local files, never export them.

Health check uses pristine public release, not carried project scripts. Local customization and global connectivity have distinct status. Offline memory does not undo a successful filesystem update; report NOT_READY and nonzero CLI exit, retry doctor without replay. --plan writes/connects nothing. No paid runs or user-global config changes.

## Альтернативы

Deleting/reinstalling loses local context. Blind copy or reset overwrites local work. Full Git merge can execute configured helpers and has broader repository scope. Refusing all edits prevents safe independent updates. Filesystem rename is atomic for one directory, not a multi-file transaction; intent/backup/guarded recovery cover intermediate states without claiming ACID/power-loss guarantees.

## Источники и evidence

Git merge pre-merge checks/three-way concepts and Python os.replace official rolling docs inspected2026-10-24; docs/setup/README.md links. Existing ownership manifests and memory contracts inspected. Global recall returned credential-scope lesson921cacabd6a45f0e9fb9f874a4c639474482ab6b25886e097ad56b54e0bd74e2; applies to explicit --global doctor, not authority to change configuration.

## Последствия и пересмотр

Single-owner Unix/macOS lock, stop active clients while swapping. Semantic merges, changing client scope, global runtime/tunnel upgrades and installs are separate scope. Cache public clean releases for safe health checks; local forks must not become public distribution sources. Unknown interruption blocks further update until explicit guarded rollback/reconciliation. Keep backups until reviewed cleanup; no automatic deletion of user data.

## Применение и проверка

Offline update matrix, plan/noop, configuration byte preservation, add/remove skills, conflicts, local modifications, path/manifest attacks, failed memory, injected I/O/interruption and recovery/concurrent edits. Validator, complete offline suite and factory. Actual temporary project upgrade then authenticated global-memory doctor; no application/paid launches.
