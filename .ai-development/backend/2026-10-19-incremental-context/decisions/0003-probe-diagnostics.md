---
id: backend/2026-10-19-incremental-context/0003
status: accepted
date: 2026-10-19
scope: supervisor-fault-diagnostics
supersedes: []
superseded_by: []
---
# Сохранение диагностики надзора

## Контекст и основание
Реальный probe получил четыре receipts (121653 tokens, estimated $0.1094558), записал marker/handoff, но остановился с usage_unknown без outcome. Это не доказывает terminal completion и не позволяет reconciliate старый ledger. Причина исключения из имеющихся данных неизвестна.

## Выбор и объяснение
Принято: ожидаемые I/O/ValueError сбои supervisor превращать в безопасный outcome с последним счётчиком, а не терять метаданные. Добавить fault-injection test. На exception пути координатор сохраняет только тип и место собственного кода, без текста ошибки/аргументов. Сырые traces/ключи не сохраняются.

## Последствия и пересмотр
Один дополнительный диагностический probe допускается координатором после офлайн-проверок исправления, как отдельная попытка, без replay предыдущей. Первый probe остаётся unknown с резервом $0.25/150000 tokens; дополнительный также ограничен $0.25/150000 и включён в тот же original $12/5m. Это уточнение правила одного probe: автоматических повторов по-прежнему нет. Continuation только после complete terminal + independent gate. При новом сбое остановиться, сохранить результаты и handoff. Не повышать бюджет.

## Альтернативы
Продолжение без terminal receipt отклонено. Повтор предыдущего run запрещён.

## Источники и evidence
Read-only private probe state, four usage_observed events, fixture tests.

## Применение и проверка
Fault injection, offline suite, factory acceptance, затем один ограниченный probe.
