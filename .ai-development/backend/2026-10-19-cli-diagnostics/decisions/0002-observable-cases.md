---
id: backend/2026-10-19-cli-diagnostics/0002
status: accepted
date: 2026-10-19
scope: observable-execution-cases
decision_basis: user-request
reuses: [backend/2026-10-19-cli-diagnostics/0001]
supersedes: []
superseded_by: []
---
# Наблюдаемые шаги и curated few-shot

## Контекст и основание
Пользователь спросил о журнале успешных/неуспешных шагов для последующего few-shot использования.

## Выбор и объяснение
В diagnostics сохранять до32 структурных events: event/type tool category/exit code, без текста, аргументов, output и reasoning. Расширять event_count/drop count при переполнении. Для полезного few-shot — отдельная curated case карточка с task summary, проверенными observable steps/result, evidence refs, bounded lesson/applicability и review status. Это не raw transcript и не приватные рассуждения модели. Auto-injection в будущие prompts не включаем: требуются reviewed/deidentified cases с verifiable outcome и небольшим relevance/token budget.

## Альтернативы
Автоматически сохранять commands/tool output/model reasoning нельзя: secrets, private customer data и вредные instructions попадут в следующие prompts. Пустой флаг success недостаточен: нужны actual independent checks, source revision и scope/ограничения. Failed case не становится доказанным fix, пока не выполнены checks.

## Источники и evidence
Пользовательский вопрос; текущий runtime traces/receipt/fingerprint contract. Формат — наша инженерная рекомендация, не экспериментально доказанное улучшение качества.

## Последствия и пересмотр
Пока есть безопасный журнал и шаблон ручной case extraction; нет автоматического обучения, генерации trusted examples из сырых логов или claims об эффективности. Review после нескольких реальных completed runs.

## Применение и проверка
Secret-sentinel, bounded trace и reasoning omission tests. Первый failed run сохраняется как diagnostic case с unknown root cause до получения evidence, не как успешный рецепт.
