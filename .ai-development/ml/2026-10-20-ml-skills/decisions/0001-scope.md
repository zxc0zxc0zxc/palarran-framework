---
id: ml/2026-10-20-ml-skills/0001
status: accepted
date: 2026-10-20
decision_basis: user-request
---

## Контекст и основание

Пользователь запросил полный ML цикл с обильной документацией прежде скиллов. Общая память решений обязательна.

## Выбор и объяснение

1. Семь commands: plan, hypotheses, model, data, cost, train, benchmark. У каждого отдельный результат и входные revisions; plan связывает этапы, но не запускает их автоматически. Так можно менять модель/данные без повторения исследования.
2. docs/ml — mandatory source, сначала исследования/блоги, затем skills. Рекомендации отделяются от результатов авторов и vendor claims.
3. Offline cost calculator с явными rates/units и неизвестными extras, без Modal SDK/network. Оценка не invoice/hard spending guarantee. Training требует конкретного разрешённого experiment/config/budget, checkpoints и stop conditions; неизвестный исход не повторяется автоматически.
4. ML память в target .ai-development/ml; code/data/weights в штатных project/private artifact stores, не installed package. Existing orchestrator не расширяется автоматически: portable skills отдельно от runtime integration.

## Альтернативы

Один огромный skill усложняет выбор этапа и контекст. Автоматический training расширяет запрос на создание скиллов до платного запуска. Только LLM finetuning исключил бы tabular/CV/time series: suite покрывает их профильными рекомендациями.

## Источники и evidence

Прямой запрос; docs/skills/decision-memory.md; existing product skills и scripts/package_plugin.py. Первичные ML sources будут датированы в docs/ml/sources.md.

## Последствия и пересмотр

Семь discoverable skills и namespace ml; packaging/validation обновляются. Live Modal integration останется NOT RUN. Пересмотр после первого разрешённого pilot и измеренного расхода.

## Применение и проверка

Planned: repo validator, offline unit suite, skill frontmatter validator, packaged dependency/link containment. No live paid tests.
