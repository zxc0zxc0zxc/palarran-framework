# Case C-cli-web-001 / v001

Review: reviewed 2026-10-19, coordinator verified sources/checks. Scope: Codex CLI0.163.0 JSONL, gpt-6.1-sol/high, runtime source d29cc4e. Это curated few-shot candidate; автоматическое включение в prompts/обучение выключено. Нет raw logs, персональных данных или chain-of-thought.

## Задача и наблюдаемый сбой

Нужно учитывать токены CLI без сохранения tool output. Обычный marker canary завершался, а web-probe доходил до item.started/web_search и локально останавливался usage_error. После safe instrumentation категория ошибки — usage_duplicate_key; terminal usage receipt не получен. Failure examples: probe b23e5457 и product recovery e2479d49; failed usage остаётся unknown.

## Краткое объяснение выбора

Duplicate validation применялась рекурсивно к содержимому tool events, которое не является accounting. Отделить строгую оболочку события и authoritative usage от ignored item payload. Вложенные дубликаты разрешены лишь внутри Codex item.started/item.updated/item.completed; верхний уровень, остальные события и все counters остаются strict. Это не повод игнорировать malformed JSON, неизвестные суммы или missing terminal usage.

## Ошибочный подход

Глобальный last-key-wins либо отключение usage guard скроют неоднозначные счётчики. Автоматический повтор с нулевым расходом выдумывает данные. Успех простой команды без web не доказывает совместимость web events. По uninstrumented first run нельзя ретроспективно утверждать конкретную причину.

## Проверенный результат

Offline regression разрешает duplicate nested tool payload и всё ещё отклоняет duplicate envelope/usage/unknown-event keys; без terminal receipt не выдаётся complete. Full suite213tests PASS62.186s. Post-fix live web-probe3783f3e6: search completed,marker/final fingerprint independent PASS,usage complete89817tokens,rate-card estimate$0.1097686,18.782s. Это проверка adapter compatibility, не production SLA/качество исследования/счёт подписки.

## Переносимость и запреты

Применять к аналогичному non-accounting tool payload только после event/schema review. Не переносить послабление на turn.completed usage или Claude modelUsage. Не считать этот case доказательством причины каждого usage_unknown. Не копировать исторические token/cost значения как новый бюджет или прогноз. Перед few-shot проверить provider version/контракт, выбрать релевантный короткий фрагмент и ограничить token budget.

Evidence: [decision0004](../decisions/0004-web-event-parsing.md), [verification](../verification.md), `tests/test_factory_usage.py::test_codex_ignored_tool_duplicates_do_not_weaken_accounting`; private snapshots web-probe-report.json/web-fixed-report.json в внешнем run root, не публикуются как raw logs.
