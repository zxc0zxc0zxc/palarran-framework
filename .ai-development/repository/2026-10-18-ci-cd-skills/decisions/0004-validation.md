---
id: repository/2026-10-18-ci-cd-skills/0004
status: accepted
date: 2026-10-18
scope: ai-tools
decision_basis: agent-judgment
reuses: []
supersedes: []
superseded_by: []
---

# Контракты, переносимость и честные границы проверки

## Контекст и основание

Нужно проверить новые entrypoints/общий журнал/packaging; живого application target и deployment credentials нет.

## Выбор и объяснение

Расширить repository validation на все skills/adapters, обязательную memory ссылку и индексы решений; проверить packaged internal links, namespace, отсутствие внешних symlinks и refusal перезаписи existing output в offline unit tests. Выполнить bundled skill validation и Claude plugin manifest validation. Существующий CI запускает offline suite.

## Альтернативы

Не запускать SSH/cloud deploy ради проверки authoring. Не утверждать, что Markdown checker доказывает поведение LLM или end-to-end runtime readiness. Независимые agent evals не запускать без разрешённой delegation; конкретные live scenarios остаются последующему application integration.

## Источники и evidence

AGENTS.md и skill-creator validation guidance; docs/ci-cd/skill-contract.md acceptance PASS/FAIL/NOT RUN; реальные результаты будут в handoff.md.

## Последствия и пересмотр

Статические contracts обнаружат забытые ссылки/непереносимый package, но не все ошибочные рекомендации агента. Performance и no-secret leak acceptance требуют реального sandbox проекта. Пересмотр при первом integration и найденных failures.

## Применение и проверка

Локальные repository/skill/package validators и offline suite выполнены: PASS. Evidence и границы — в [handoff](../handoff.md). GitHub CI для implementation commit `c915764` PASS (run linked in handoff); application/live deployment NOT RUN.
