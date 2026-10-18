# Handoff: UI design

Созданы documentation-first база `docs/ui/` (10 MD guides + catalog.json), templates, skill `ui-design`, `/ui:design` adapter, отдельный namespace и portable package. Выбор: 10 established systems + custom, canonical/main source + минимум 2 дополнительных visual refs; source UX mapping, responsive visual preview, semantic tokens/components. Нужные картинки обязательно генерируются и включаются в preview с asset records. Accepted rationale: 0001–0005; история target UI сохраняется для следующих задач.

## Проверка

- PASS: `python3 scripts/validate_repo.py` — 92 Markdown files, 7 skills/adapters, namespaces, links, catalog и canonical decisions.
- PASS: offline unit suite — 11 tests; все 4 packages проверяются в изоляции, UI содержит UX dependency/catalog/token assets, без project memory/external symlinks.
- PASS: skill-creator `quick_validate.py skills/ui-design` (temporary PyYAML environment).
- PASS: `python3 scripts/package_plugin.py ui --output artifacts/plugins/ui` и `claude plugin validate artifacts/plugins/ui --strict`.
- PASS: changed Python compilation, `git diff --check`.
- CI: pending publication.
- NOT RUN: application UI generation, user preference session, render/user tests и image generation — здесь authoring capability, application UX target не задан. Offline contracts не доказывают visual quality будущего результата.

## Использование

Codex: `$ui-design` в target с подключённым skill checkout. Claude: собрать namespace `ui` и загрузить plugin; root infra namespace сохранён. Существующий output не перезаписывать: выбрать новый каталог при пересборке. Package содержит UI/UX методику и UX skill dependency; отдельный slash `/ux:design` предоставляется UX namespace.

В application task прочитать source UX revision/index и прежние choices, выбрать направление (если ещё не задано), исследовать refs, создать versioned preview и actual render checks. Все results/decisions/assets пишутся в target `.ai-development/ui/`, не installed plugin. Недоступный обязательный render/image tool означает draft/gap.
