---
id: backend/2026-10-19-product-factory/0006
status: accepted
date: 2026-10-19
scope: product-factory-v001-agent-protocol
decision_basis: agent-judgment
reuses: [backend/2026-10-19-product-factory/0004, backend/2026-10-19-product-factory/0005]
supersedes: []
superseded_by: []
---
# Явный AI handoff

## Контекст и основание

CLI exit 0 не различает реализацию и вопрос модели. Требуется не выдумывать пользовательское согласие; это уточнение протокола до завершения v001.

## Выбор и объяснение

Runtime добавляет к prompt обязательный JSON handoff в target `.ai-development/factory/<run>/<task>/attempt-N/handoff.json`. Только `{"status":"implemented"}` разрешает independent gates; `needs_input` блокирует run, отсутствие/ошибка — failure. Повтор получает безопасный operator context из resolve. Handoff не принимает результат проверок от агента.

## Альтернативы

Поиск слов в prose хрупок; exit code недостаточен; provider output JSON не имеет единого envelope. Отдельный минимальный файл переносим между CLI и не сохраняет raw output.

## Источники и evidence

[Contract](../../../../docs/product-factory/contract.md), user scope и review реализации. Это наша protocol adaptation, не vendor claim.

## Последствия и пересмотр

В target появляется маленький durable handoff. Agent обязан следовать дописанному протоколу; untrusted agent по-прежнему требует sandbox. Новые artifact fields требуют новой schema revision.

## Применение и проверка

До изменения кода NOT_RUN; acceptance через controlled CLI fixture с реальными процессами, не live provider.
