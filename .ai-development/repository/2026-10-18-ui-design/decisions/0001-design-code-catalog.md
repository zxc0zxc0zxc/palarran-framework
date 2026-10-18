---
id: repository/2026-10-18-ui-design/0001
status: accepted
date: 2026-10-18
scope: ui-design-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ux-design/0002]
supersedes: []
superseded_by: []
---

# Десять официальных направлений и выбор пользователя

## Контекст и основание

Пользователь хочет десять популярных design-code вариантов с устойчивыми reference brands и возможность своих references. Native Liquid Glass и web design systems не имеют одной установленной нами метрики adoption.

## Выбор и объяснение

Создать menu из 10 известных named systems с canonical first-party URL, stable IDs, platform/visual traits/caveats; называть curated menu, не measured ranking. Material 3 и Liquid Glass включены явно. Custom references — отдельный полноценный режим, может дополнять canonical system. При незаданном стиле сначала предложить выбор, не считать default/preselected option согласием.

## Альтернативы

Список только трендовых названий без источников нельзя проверить. Несопоставимые npm downloads/native OS adoption не доказывают общий рейтинг. Не создавать 10 полноэкранных вариантов автоматически: все направления доступны в меню, 2–3 relevant candidates можно показать на одном UX sample для выбора.

## Источники и evidence

Прямой запрос пользователя; official Material/Apple/Fluent/Carbon/Atlassian/Polaris/Spectrum/SLDS/Ant/Primer docs, source registry docs/ui/sources.md. Catalog/source claims проверены 2026-10-18.

## Последствия и пересмотр

Catalog можно расширять по явному запросу, но default menu остаётся 10 + custom. Числа в меню не ранжирование. Адаптация Liquid Glass на web не выдаётся за native Apple rendering/API. Пересмотр при изменении source/version и новых preference.

## Применение и проверка

Реализовано. Local validation/package/skill checks PASS; подробная evidence и границы в [handoff](../handoff.md). Реального application UI target здесь нет.
