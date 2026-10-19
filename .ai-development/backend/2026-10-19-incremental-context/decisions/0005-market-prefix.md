---
id: backend/2026-10-19-incremental-context/0005
status: accepted
date: 2026-10-19
scope: verified-market-prefix-reuse
supersedes: []
superseded_by: []
---
# Сохранить проверенный market без повторного вызова

## Контекст и основание
Continuation8068b8e8aaa140b7b942a0f84ee85d31 stopped by stage575k cap at receipt660629tokens/estimated$0.6097868. Artifacts already written. Separate original pinned verifier: PASS128b7252180a277197bd802d53535b13027164d20427fe0977ffe0a727f6b369. Это structural/source-chain acceptance, не истинность внешних claims/market validation.

## Выбор и объяснение
Импортировать byte-exact define+market через existing verified-prefix continuation; следующий model task compare. Не replay market, не менять failed run/unknown receipt. Перенести market reserve max(cap, observed):660629tokens/$0.90. This covers unknown terminal accounting conservatively; no authoritative invoice assertion.

## Альтернативы
Повторить market — расход и риск смены гипотезы. Повысить лимит failed run или сделать unknown complete — запрещено. Выкинуть independently verified material — ненужная потеря результата.

## Последствия и пересмотр
Общий$12/5m неизменен. Carry3073225tokens/$8.1274214. Remaining1926775tokens/$3.8725786. Compare/revenue/acquisition550k each, mvp250k:1.9m total; money$0.90each:3.6total. No stage cap increases, all new allocations fit original envelope. Резерв — не гарантия upstream invoice; unknown остаются видимыми. Непроверенные drafts не импортировать.

## Источники и evidence
Private report/SQLite; independent original verifier digest above; pinned define remains identical. Research report recommends validate, not build.

## Применение и проверка
Existing continuation import guards pin both stages, ADRs and appendices. Run starts command verification; no define/market model tasks. Final verification remains mandatory. No ads/outreach/account/app/deploy.
