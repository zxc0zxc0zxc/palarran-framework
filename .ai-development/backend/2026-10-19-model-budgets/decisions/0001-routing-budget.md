---
id: backend/2026-10-19-model-budgets/0001
status: accepted
date: 2026-10-19
scope: runtime-model-governance
decision_basis: user-request
reuses: [backend/2026-10-19-product-factory/0003, backend/2026-10-19-product-factory/0005]
supersedes: []
superseded_by: []
---

# Роли и невозвратные allocations

## Контекст и основание
Пользователь требует сильное планирование, экономную реализацию, дешёвые простые действия и предварительные бюджеты. CLI агент способен сделать несколько внутренних API calls; время и количество запусков не гарантируют токены/доллары/подписку.

## Выбор и объяснение
1. Immutable optional workflow `ai_policy` с тремя profiles planning/implementation/simple. Product-create включает policy всегда: Codex gpt-6.1-sol/high, gpt-6-luna/high, gpt-6-luna/low; Claude opus/high, sonnet/medium, haiku/low. Это наша стартовая конфигурация, availability и качество требуют отдельных evals. Без fallback/escalation. Самая простая работа — command без LLM.
2. Profiles содержат weight (условные units, не цена) и seconds; workflow max_calls/max_units/max_prompt_bytes. Каждая AI task получает model_role и model_calls. Сумма всех allocations обязана укладываться в оба caps, каждый retry заранее распределён по своей task. Claim атомарно списывает один запуск через durable attempts, включая spawn failure, cancel и unknown outcome; resolve не возвращает units. Существующего SQLite counter достаточно, миграция не нужна. Отдельный mutable ledger дублировал бы учёт.
3. Product шесть research/synthesis tasks — planning, по одному запуску. Итого 6 launches / 30 units (weight 5). Автоматический retry не получает чужую долю. Проверки Python — ноль launches. Время planning 600s, implementation 300s, simple 60s, общий run/task caps дополнительно применяются. Prompt UTF-8 <=32768 bytes включая appended handoff. Глубину прочитанного агентом контекста CLI это не ограничивает.
4. Старые generic workflows без policy допустимы, status явно unmanaged. Новые поля нельзя использовать без policy. Режим controlled не означает monetary/token guarantee. Никаких тарифов/телеметрии выдумывать не будем. Custom policy file позволяет заранее заменить модели/caps; task allocations неизменны после create.

## Альтернативы
Astra по умолчанию дороже для повторного research; оставляем для явно настроенного профиля. Скрытое наследование CLI default нарушает маршрутизацию. Dollar estimate как hard cap неверен: Claude CLI прямо допускает overshoot; Codex CLI не предоставляет эквивалентный переносимый hard cap. API gateway/account limits — отдельное будущее расширение.

## Источники и evidence
Прямой запрос пользователя; [OpenAI models](https://developers.openai.com/codex/models), [noninteractive](https://developers.openai.com/codex/noninteractive), [Claude CLI](https://code.claude.com/docs/en/cli-reference), проверены 2026-10-19; installed CLI help подтвердил model/config/effort flags. Выбор weights/time — наша политика, не vendor benchmark.

## Последствия и пересмотр
Сбой может оставить unused allocation сгоревшей — консервативно, зато crash не возвращает бюджет. Сильный агент может исчерпать подписку внутри одного launch; операционный профиль требует внешних account caps, если нужна денежная гарантия. Изменять модели по качественным evals и доступности. План/верификация исследования не подтверждает рынок.

## Применение и проверка
До запуска: schema/allocation validation. В claim: атомарные caps. В execute: explicit model/effort, bounded time/prompt. В status: allocation/spent/remaining, monetary_cap=false, requested model (не provider attestation). Edge/recovery/concurrency/CLI regression, offline suites и acceptance. Live provider quality/cost NOT_RUN.
