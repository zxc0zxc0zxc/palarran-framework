# Source UX/UI contract

До изменения кода прочитать target product docs и `.ai-development/INDEX.md`, UX/UI catalogs, связанные accepted ADR и предыдущие frontend handoffs. Выбрать конкретные **обе** revisions, их статусы и in-scope screens/states/blocks, UI tokens/components/assets и responsive specs. Не считать любой `v001` последней согласованной версией; approved status не придумывать. Явный запрос реализовать draft допускает draft как source с указанным ограничением.

Составить [coverage](../../templates/frontend/coverage.md): source UX ID/state → source UI spec → app route/component/data adapter → browser scenario → evidence/status. UI preview служит visual reference, но его gallery/state switcher не переносится в app navigation. По умолчанию охватить весь запрошенный scope, не только landing/happy path. Частичная реализация — только согласованный scope или явно незавершённый результат.

| Неясность | Действие |
|---|---|
| Нет концептов | Найти target catalogs/путь из запроса; если нет — запросить расположение или предложить UX/UI этап. README не заменяет screen specs |
| UX и UI расходятся | Уточнить конфликт; бизнес-сценарий/роль из UX не менять ради UI. Записать proposed delta, продолжать независимые части |
| UI не задаёт техническую мелочь | Выбрать в рамках existing conventions, объяснить ADR; не требовать согласия на каждый размер/компонент |
| Asset/token отсутствует | Проверить источник, existing assets, [asset workflow](implementation.md); не выдумывать user-approved replacement |
| Source revision обновилась во время работы | Зафиксировать diff, затронутые IDs, новую mapping revision и повторные проверки |

Сохранять короткий UI copy, порядок/доступность actions, roles/permissions, entry/back/deep links, loading/empty/error/validation/success из UX. Визуальные density/material/type/color из UI. Реализация может улучшить внутреннее устройство без смены поведения, если choice объяснён. Требуемую смену поведения/стиля вынести в proposal с причиной и конкретным impact; не записывать её accepted по молчанию.

Не нужен повторный выбор из 10 дизайн-систем: выбор уже сделан на UI этапе. Не начинать новое competitor research вместо реализации, если только источник действительно неясен или пользователь просит переработку.

## SDD source и execution revision

[SDD plan](sdd-agents.md) дополнительно фиксирует plan/spec/API revision и обе UX/UI revisions. При отсутствии execution plan сначала составить его из этих source concepts, не придумывая новый UX. R/AC/screen/state/block/C IDs → TASK/T IDs → app route/component → browser gate/DoD. [Прогресс](progress.md) отражается прямо в этом source plan; semantic scope change имеет новую revision/impact/ADR, metadata completion не меняет design revision. Missing critical source остаётся blocker, а не silently accepted requirement.
