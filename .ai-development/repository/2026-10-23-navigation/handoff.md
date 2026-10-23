# Handoff — navigation-v001

## Результат

Root [README](../../../README.md) формализован как карта входа с stable section anchors. Каталоги: [documentation](../../../docs/README.md), [26 skills](../../../skills/README.md), [portable shared contracts](../../../docs/skills/README.md). Root AGENTS указывает новые входы, исходные инварианты сохранены.

README содержит проверенный inventory (26 unique SKILL.md, 9 namespaces), реальную карту modules/AGENTS, подключения full checkout/domain packages, runtime contracts и capability status. Text data gate local implemented; Modal text transport unsupported; training-debug runtime pending; MCP servers planned. Product Factory introduction уточнён: research/ML pipelines уже есть, long-lived market feedback loop ещё нет.

Graph rules: instructions/accepted ADR → fresh bounded graph query → original source; missing/stale = scoped search. Code-only exclusions, no full graph dump, no implicit install/reindex/semantic/cloud operations. Design diagrams помечаются revision/proposal/observed evidence; не считаются code graph/live trace. Existing paired comparison приведён как case-specific evidence, без universal savings.

Badges: dynamic GitHub validate.yml/main + static Python>=3.9, skills26 и optional Graphify. Format сверён с official GitHub docs; remote CI result/visibility не подтверждались. License/security/coverage badges не добавлены без оснований.

## Проверка

PASS: repository validator (после финального journal update повторён), 4 portable packaging tests / 0.656s, inventory equality для всех 26 skills, local navigation fragments, root namespace/workflow existence, git diff --check. Common docs index переносится всеми packages и не ссылается на отсутствующие full-checkout indexes. Python/runtime/skill code не менялся; full runtime suite и factory lab не повторялись для documentation-only changes.

Новых model/provider/SSH/graph/paid calls нет; badges только ссылки, workflow не запускался вручную. No install/reindex/semantic extraction, без изменения budget/state. Локальный docs commit; push не выполнялся.

## Сопровождение

При изменении skill/namespace/module обновлять README indices/static badge counts и actual registration. Канонические инструкции остаются в профильных docs, а индексы только маршрутизируют. Decision ID: repository/2026-10-23-navigation/0001.
