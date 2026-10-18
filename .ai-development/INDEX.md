# Индекс решений ai-tools

Перед следующей задачей читать связанные accepted записи и проверять актуальность предпосылок. Общие правила: [decision-memory](../docs/skills/decision-memory.md). Workspaces задач временные по scope; durable records сохраняются.

| ID | Статус | Scope / тема | Объяснение и пересмотр |
|---|---|---|---|
| repository/2026-10-18-ci-cd-skills/0001 | accepted | Все скиллы: общая память | [Task-local journal + durable context](repository/2026-10-18-ci-cd-skills/decisions/0001-decision-memory.md); пересмотреть при ограничении хранения/видимости проекта |
| repository/2026-10-18-ci-cd-skills/0002 | accepted | CI/CD: инструкции и обязательная база | [Два provider skills, пять stack guides](repository/2026-10-18-ci-cd-skills/decisions/0002-ci-cd-workflow.md); пересмотреть по реальным применениям |
| repository/2026-10-18-ci-cd-skills/0003 | accepted | Упаковка namespace | [Самодостаточные пакеты](repository/2026-10-18-ci-cd-skills/decisions/0003-plugin-packaging.md); пересмотреть при смене host plugin spec |
| repository/2026-10-18-ci-cd-skills/0004 | accepted | Проверки и границы validation | [Offline contracts и sandbox packaging](repository/2026-10-18-ci-cd-skills/decisions/0004-validation.md); live acceptance после конкретной интеграции |
| repository/2026-10-18-ux-design/0001 | accepted | UX / Исследование и evidence референсов | [Объяснение](repository/2026-10-18-ux-design/decisions/0001-research.md); пересмотр после первого application review |
| repository/2026-10-18-ux-design/0002 | accepted | UX / Диаграммы экранов, состояния, адаптация и copy | [Объяснение](repository/2026-10-18-ux-design/decisions/0002-screen-contract.md); пересмотр после первого application review |
| repository/2026-10-18-ux-design/0003 | accepted | UX / UX package, хранение концептов и проверки | [Объяснение](repository/2026-10-18-ux-design/decisions/0003-delivery.md); пересмотр после первого application review |
| repository/2026-10-18-ui-design/0001 | accepted | UI / Десять официальных направлений и выбор пользователя | [Объяснение](repository/2026-10-18-ui-design/decisions/0001-design-code-catalog.md); пересмотр по source UX/реальному review |
| repository/2026-10-18-ui-design/0002 | accepted | UI / UI привязан к UX и даёт видимый результат | [Объяснение](repository/2026-10-18-ui-design/decisions/0002-ux-binding-and-visual-output.md); пересмотр по source UX/реальному review |
| repository/2026-10-18-ui-design/0003 | accepted | UI / Доказуемые материалы и доступный adaptive review | [Объяснение](repository/2026-10-18-ui-design/decisions/0003-references-and-review.md); пересмотр по source UX/реальному review |
| repository/2026-10-18-ui-design/0004 | accepted | UI / Отдельный UI namespace и переносимые контракты | [Объяснение](repository/2026-10-18-ui-design/decisions/0004-delivery-and-validation.md); пересмотр по source UX/реальному review |
| repository/2026-10-18-ui-design/0005 | accepted | Генерация необходимых UI изображений с asset provenance и включением в preview | ui-design-skill | Прямое требование пользователя; без image tool — draft/NOT RUN | [record](repository/2026-10-18-ui-design/decisions/0005-required-generated-images.md) |
| repository/2026-10-18-frontend-build/0001 | accepted | Frontend / Реализация из UX/UI без редизайна | [Объяснение](repository/2026-10-18-frontend-build/decisions/0001-source-contract.md); пересмотр по первому application run |
| repository/2026-10-18-frontend-build/0002 | accepted | Frontend / Адаптивность и фактическая browser проверка | [Объяснение](repository/2026-10-18-frontend-build/decisions/0002-browser-acceptance.md); пересмотр по первому application run |
| repository/2026-10-18-frontend-build/0003 | accepted | Frontend / Память, необходимые картинки и portable package | [Объяснение](repository/2026-10-18-frontend-build/decisions/0003-delivery-and-assets.md); пересмотр по первому application run |
| repository/2026-10-18-backend-plan/0001 | accepted | Backend / Planning-only SDD и foundation | [Объяснение](repository/2026-10-18-backend-plan/decisions/0001-plan-only-sdd.md); пересмотр по application run |
| repository/2026-10-18-backend-plan/0002 | accepted | Backend / Архитектура, данные, performance и SLA | [Объяснение](repository/2026-10-18-backend-plan/decisions/0002-scale-data-reliability.md); пересмотр после измерений |
| repository/2026-10-18-backend-plan/0003 | accepted | Backend / DAG и future worktrees | [Объяснение](repository/2026-10-18-backend-plan/decisions/0003-agent-worktrees.md); пересмотр по application run |
| repository/2026-10-18-backend-plan/0004 | accepted | Backend / Package и проверка | [Объяснение](repository/2026-10-18-backend-plan/decisions/0004-delivery-validation.md); пересмотр по application run |
| repository/2026-10-18-backend-build/0001 | accepted | Backend build / Source и прогресс в плане | [Объяснение](repository/2026-10-18-backend-build/decisions/0001-source-and-progress.md); пересмотр по application run |
| repository/2026-10-18-backend-build/0002 | accepted | Backend build / Actual agents/worktrees | [Объяснение](repository/2026-10-18-backend-build/decisions/0002-worktree-agents.md); пересмотр по application run |
| repository/2026-10-18-backend-build/0003 | accepted | Backend build / Actual tests и SLA evidence | [Объяснение](repository/2026-10-18-backend-build/decisions/0003-testing-reliability.md); пересмотр после измерений |
| repository/2026-10-18-backend-build/0004 | accepted | Backend build / Package и проверки | [Объяснение](repository/2026-10-18-backend-build/decisions/0004-package-and-validation.md); пересмотр по application run |
| repository/2026-10-18-frontend-sdd/0001 | accepted | Frontend / SDD и worktree lanes | [Объяснение](repository/2026-10-18-frontend-sdd/decisions/0001-sdd-worktrees.md); пересмотр по target run |
| repository/2026-10-18-frontend-sdd/0002 | accepted | Shared execution progress / compatibility | [Объяснение](repository/2026-10-18-frontend-sdd/decisions/0002-shared-progress.md); пересмотр по regression |
| repository/2026-10-18-frontend-sdd/0003 | accepted | Frontend / Integrated browser DoD и package | [Объяснение](repository/2026-10-18-frontend-sdd/decisions/0003-dod-packaging.md); пересмотр по target run |
