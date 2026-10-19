---
id: backend/2026-10-19-cli-diagnostics/0003
status: accepted
date: 2026-10-19
scope: live-recovery-allocation
decision_basis: user-request
reuses: [backend/2026-10-19-cli-diagnostics/0001]
supersedes: []
superseded_by: []
---
# Canary outcome и ограниченный recovery

## Контекст и основание
Первый новый canary bf072dea выполнил marker/handoff и выдал valid turn usage42005 tokens/$0.0494134 estimate. Guard20k остановил run, EOF completeness unknown. Исторический CLI error не сохранён и ретроспективно не восстанавливается. Current provider/model/auth доступны. Small canary context оказался больше исходной token allocation; это observed fact, не причина первого unknown.

## Выбор и объяснение
User явно разрешил исправление и безопасный повтор. Выделить ровно ещё один отдельный compatibility canary с теми же model/permissions, caps80000tokens/$0.25,90s,1attempt; цель проверить полный EOF receipt+independent marker verification. Не повторять initial product task и не обнулять old run/canary unknown. Общий diagnostic envelope: максимум2 launches и $0.50 observed estimate, old original unknown учитывается отдельно как unknown. После successful canary — новый product research run с default caps600k/$12,100k/$2stage и6launches; никаких автоматических повышений/повторов при failure. Historical unknowns явно передать в итог, не выдавать aggregate за complete.

Budget callback уже revokes lease до возврата execute: разрешить single metadata-only outcome write только для точного token в current charged receipt при terminal usage_budget_exhausted и пустом result. Не восстанавливать lease/usage/status, не позволять overwrite; test stale/missing receipt. Это диагностика завершения supervised process, не reconciliation расхода.

## Альтернативы
Повторять20k canary бессмысленно; отключать usage_policy нельзя. Утверждать0токенов первоначальной попытки нельзя. Скрыть unknown в новом cumulative total нельзя. Raising live product caps on failure без review — вне этой allocation.

## Источники и evidence
Private canary-report.json и verified marker/handoff readback. Sanitized daemon log lookup в старом временном окне не нашёл evidence. Независимый marker check не превращает budget-failed run в runtime verified.

## Последствия и пересмотр
Новый product run допустим только после complete canary; старые attempts сохраняются. Если second canary unknown/failed — дальнейших model calls в этом recovery нет до нового evidence/review. Нет точного aggregate billing старого сбоя и нет гарантии hard provider cap.

## Применение и проверка
Offline metadata/fencing/secret tests, complete EOF canary и independent final gate; product run с фактическим status/usage, без обещания успеха.
