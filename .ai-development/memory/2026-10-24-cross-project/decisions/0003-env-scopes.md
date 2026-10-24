---
id: memory/2026-10-24-cross-project/0003
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Global and project environment scopes

## Контекст и основание

User explicitly requested global credentials at ~/.zxc0zxc0zxc/.env and per-project .env so new projects reuse access. Global directory/env absent at inspection; known provided target and generated memory credentials already in private local .env. Global env authorization does not authorize Codex/Claude client config edits.

## Выбор и объяснение

Explicit --env wins (missing path fails); --global selects global; otherwise Git project-root .env then global fallback. Unknown unrelated app keys ignored without evaluation. If project has no relevant profile keys, use global; a partial profile is used as a whole and missing required settings fail rather than mixing a new target with old credentials. No per-key merge between destinations. Non-Git uses CWD, no arbitrary parent env discovery. Private envs regular owned0600, parent no symlinks, global dir0700. MCP reads only agent URL/token view and never sends reviewer/DB credentials to gateway. A shared env is not an OS sandbox between processes of the same trusted owner.

## Альтернативы

Always mandatory --env repeats per-project setup. Blind per-key merge can pair target from project with credentials from global. Existing unrelated project .env should not disable global memory. No shell source/interpolation or process-wide dumping.

## Источники и evidence

Direct user storage/precedence request and existing memory/VPS private env contracts. Tests cover explicit/global/project/nested Git/non-Git/unknown app keys/no partial merge/unsafe files.

## Последствия и пересмотр

Global file contains operator credentials, protected at filesystem boundary; ordinary MCP inventory still agent-only. Project override deliberately changes context; invalid or incomplete profile must be fixed explicitly. Password-only SSH remains protected prompt/operator task, not plaintext password env.

## Применение и проверка

Update scripts/memory_ops.py, vps_ops.py, acceptance CLI, docs/client template and offline tests. Copy known private values once to new global file without logging, preserve future unrelated values. Verify source keys/permissions/redacted equality; final runtime manifest changes only helper behavior, endpoint identity preserved.
