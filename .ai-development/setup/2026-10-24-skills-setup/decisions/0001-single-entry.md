---
id: setup/2026-10-24-skills-setup/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# One project setup entrypoint

## Контекст и основание

User requests /skills:setup to choose install/update, preserve settings and edits, check global memory and explain usage. Reuses safe-update/0001 and global-onboarding/0001; unrelated ML work stays outside this change.

## Выбор и объяснение

Add a small deterministic setup dispatcher to the existing installer, not a second installer. No receipt and no library/transaction residue selects install; existing receipt selects guarded update, including unchanged revision health check. Malformed receipt/partial state stops before mutation. Fresh install checks its pinned public bundle; updates retain pristine release checks. Health failure preserves completed installation with nonzero exit; never replay writes to repair networking. Plan mode stays offline/read-only. Client scope inherited on update; fresh agent chooses current host unless explicitly both.

## Альтернативы

Model-only classification can confuse broken installs with absent ones. Delete/reinstall loses local changes. Carrying a full library in a bootstrap plugin duplicates inventories; instead the portable setup plugin requires a trusted full checkout/public snapshot as explicit source. Clone into a new dedicated directory when absent, never reset a dirty checkout.

## Источники и evidence

User request, existing ownership/rollback code and docs/setup/README.md; Claude skills and Git merge primary docs rechecked 2026-10-24. Global recall921cacabd6a45f0e9fb9f874a4c639474482ab6b25886e097ad56b54e0bd74e2 applies to explicit global doctor. Memory evidence never authorizes global changes.

## Последствия и пересмотр

New namespace skills, portable skill skills-setup. Installed native names differ from plugin aliases and must be explained. No global MCP/tunnel/policy changes, credential copies, paid/model launches or application execution. Conflicts/recovery require review, not force. Existing local upstream changes use the same three-way rules.

## Применение и проверка

Planned: fresh/update/noop routing, corrupt/partial/pending/conflicting state, client inheritance, health failure/retry, zero-write plan, portable CLI; existing preservation/rollback suite plus validator/full suite/factory. Results in handoff; no live provider or host UI quality claims.
