---
id: product/2026-10-19-product-skills/0006
status: accepted
date: 2026-10-19
scope: product-plugin-delivery
decision_basis: existing-policy
reuses: [repository/2026-10-18-ci-cd-skills/0003, product/2026-10-19-product-skills/0001]
supersedes: []
superseded_by: []
---
# Самодостаточный product namespace

## Контекст и основание

Пять product skills должны обнаруживаться Codex и вызываться через Claude commands без потери mandatory docs/cases. Применяем existing portable packaging policy.

## Выбор и объяснение

Namespace product с define/market/compare/revenue/acquisition; source skills — repo skills/, Codex symlinks в .agents/skills, Claude adapters и manifest. Package materializes только reviewed docs/skills + docs/product, пять templates и shared decision template; target memory, runtime state и credentials не включаются.

## Альтернативы

Копия SKILL.md без обязательной базы нарушает doc-first контракт. Расширение infra-plan namespace смешало бы обязанности. Отдельный runtime/API connector сейчас не запрошен.

## Источники и evidence

[Product guide](../../../../docs/product/README.md), existing scripts/package_plugin.py и tests/test_packaging.py. Docs baseline 07af290 создан до новых skills.

## Последствия и пересмотр

Обновляем allowlisted packaging/validator вместе. Реальная доступность API и результат исследования отдельно от installability. Пересмотр при новом host manifest contract.

## Применение и проверка

Пять quick_validate PASS, repository validation PASS; actual materialized packages проверяет offline suite. Sanitized handoff содержит финальный subject и CI.
