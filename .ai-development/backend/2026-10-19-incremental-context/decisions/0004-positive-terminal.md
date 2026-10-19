---
id: backend/2026-10-19-incremental-context/0004
status: accepted
date: 2026-10-19
scope: positive-terminal-probe
supersedes: []
superseded_by: []
---
# Отдельная положительная проверка terminal

## Контекст и основание
Второй probe остановлен штатно по промежуточному token cap: fifth receipt166087 tokens/$0.1404712 при cap150000. Результат и usage_stop сохранены, private metadata подтверждает guard. Это успешная negative compatibility check, а не доказательство terminal completion. Первый missing-outcome случай не имеет доказанной причины.

## Выбор и объяснение
Отдельный минимальный positive probe без web/research: marker/handoff и выход. Максимум100k tokens/$0.20, один запуск. Это отдельная проверка terminal path, не replay и не повтор исследования. Она укладывается в original$12/5m с перенесёнными reserves: первая $0.25/150k; вторая $0.25/166087 (max cap/observed). После неё новых probes нет. Full continuation только при complete usage + independent verification. Это уточняет stop из0003 для штатного budget-stop результата; unexpected failure по-прежнему блокирует продолжение.

## Альтернативы
Пропустить positive terminal проверку — недоказанная интеграция. Снова искать web — лишний контекст/расход. Поднять общий budget запрещено.

## Последствия и пересмотр
Все предыдущие attempts unknown остаются unknown. Только новая точная receipt переносится как known; новый unknown означает stop. Суммарные token/stage ceilings сохраняются; если реально достигается общий cap, дальнейшие этапы останавливаются.

## Источники и evidence
Private incremental-probe2-result.json:5receipts, usage_stop, retained diagnostics. Offline223tests/validator/factory acceptance PASS.

## Применение и проверка
Single minimal model turn through immutable runtime; independent marker gate, receipt terminal, final fingerprint. No market claims.

## Результат и итоговое распределение
Positive probe verified:2receipts/54562tokens/$0.0676438, terminal + independent final fingerprint. Все diagnostic reserves учтены. Before continuation reserved carry:2412596tokens/$7.2274214; available2587404tokens/$4.7725786. Stage allocations уменьшаются до575k tokens для первых четырёх,250k дляmvp (2.55m total); money0.90each (4.50total). Общий original5m/$12 неизменен.
