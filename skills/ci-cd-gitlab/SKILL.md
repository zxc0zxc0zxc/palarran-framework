---
name: ci-cd-gitlab
description: Спроектировать, внедрить или ускорить GitLab CI/CD для Go, PHP, TypeScript/Next.js, Python и Rust с тестами, автоматическим deploy без SSH и памятью решений. Использовать для /ci-cd:gitlab; планирование инфраструктуры выполняется отдельными infra скиллами.
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# CI/CD — GitLab CI/CD

Обрабатывай `/ci-cd:gitlab` и `$ci-cd-gitlab`. Создавай конкретные проверяемые изменения выбранного проекта в рамках запроса; при запросе только плана не активируй workflows/deploy. Не запускай этот скилл как разрешение менять application pipelines при одной лишь разработке самого скилла.

## Обязательная память всех решений

До выбора прочитай [общий контракт](../../docs/skills/decision-memory.md), затем `.ai-development/INDEX.md` **целевого проекта** и связанные accepted решения прошлых задач. Создай task context до первого нового решения. Любой принятый выбор — включая конфигурацию, оптимизацию и способ проверки — сохрани с объяснением, альтернативами, evidence, последствиями и trigger пересмотра **до зависимого изменения**. Обновляй индекс; старые решения не стирай, связывай reuses/supersedes. В конце оставь handoff и ссылки на IDs. Журнал используется в следующих задачах; scratch временный, accepted records сохраняются. Не записывай секреты и не считай старую запись новым разрешением.

## Обязательная база знаний

Найди checkout по реальному `SKILL.md`, разрешив symlink: `../../`. Не путай его с корнем целевого проекта, где лежат результаты. До проектирования прочитай:

- [Навигацию](../../docs/ci-cd/README.md) и [фактуру компаний](../../docs/ci-cd/evidence.md).
- [Общий workflow](../../docs/ci-cd/workflow.md) и [контракт результата](../../docs/ci-cd/skill-contract.md).
- [Архитектуру](../../docs/ci-cd/architecture.md), [оптимизацию](../../docs/ci-cd/performance.md), [security](../../docs/ci-cd/security.md).
- [Память окружений/promotion](../../docs/ci-cd/environments.md), [ADR-кейсы](../../docs/ci-cd/decisions.md), [источники](../../docs/ci-cd/sources.md).
- [Provider guide gitlab](../../docs/ci-cd/gitlab.md).
- Все обнаруженные стеки: [Go](../../docs/ci-cd/stacks/go.md), [PHP](../../docs/ci-cd/stacks/php.md), [TypeScript/Next.js](../../docs/ci-cd/stacks/typescript-nextjs.md), [Python](../../docs/ci-cd/stacks/python.md), [Rust](../../docs/ci-cd/stacks/rust.md). Для monorepo один стек не заменяет остальные; неприменимые не загружай.

Если базы нет, запроси её расположение и не подменяй обязательное чтение общими знаниями. Укажи в результате прочитанные paths/commit и используемые ADR. Актуальные версии/функции провайдера и toolchain сверяй с официальной документацией; historical bigtech evidence не доказывает наш sizing или speedup.

## Порядок работы

1. Выполни repository discovery и восстановление `.delivery/`/решений по workflow. Раздели факты, допущения и неизвестное; не открывай `.env`/state/private keys/production data. Уточни только отсутствующие существенные параметры.
2. Спроектируй DAG с tests/quality/security → immutable candidate → packaged smoke/evidence → authorized promotion → observed rollout. Выбери GitOps/managed API/уже настроенный pull-controller. **Никаких SSH/scp/rsync/туннелей/Ansible over SSH**, даже как fallback bootstrap. Нет готового controller/API — зафиксируй blocker, а не dummy success.
3. Сохрани объяснения каждого выбора и создай plan/две Mermaid-схемы, adapted provider workflow files, schemas/semantic validation для `.delivery/`, stack scripts/package config по нужде, release/deployment contract, performance budget и runbooks. Полный список — workflow/skill-contract; не копируй docs example как готовый deploy.
4. Оптимизируй measured critical path: независимые jobs, safe caches/keys/trust boundaries, balanced shards, resource budget, validated dependency closure/full fallback. Нельзя ускоряться пропуском обязательных тестов. Nightly suite не заменяет release gate; baseline неизвестен — это план измерения, не достигнутое ускорение.
5. Поддержи auto deploy policy и optional кнопку dev/test/prod одного eligible digest. Env/ref/release — проверенный allowlist, роль scoped, lock+stale guard обязательны. Для Next build-time env либо runtime-compatible design, либо отдельные variants с evidence.
6. Пройди доступные local checks и sandbox acceptance по workflow. Secret values не печатай и не сохраняй в logs/reports/cache/layers; synthetic leak tests не используют production credentials. Отметь PASS/FAIL/NOT RUN и не выдавай syntax validation за live success.
7. Если активация разрешена для конкретного проекта/env и prerequisites готовы — заверши её и проверь точный observed digest/revision+smoke; уже данное разрешение не переспрашивай. Смена scope/destructive migration требует отдельного понятного решения. При plan-only остановись на reviewable файлах. Обнови handoff/decision evidence/INDEX и дай краткое саммари с путями.

## GitLab CI/CD: обязательные ограничения

- Проверить GitLab version/tier/executor; `workflow: rules` устраняет дубли branch/MR pipelines. `needs` ускоряет DAG, но не обходит gates; optional jobs допускаются только при доказанной неприменимости.
- Versioned includes/components pinned; protected/unprotected caches и runner pools изолированы. ID tokens/OIDC audience и project/ref/env claims ограничены; masking/hidden/protected variables не заменяют trust review.
- Manual mode: поддерживаемые typed inputs с env options и release ID либо отдельные manual jobs; `allow_failure` явно отличает optional selection от blocking gate. Protected environments/approvals должны существовать на выбранном tier.
- `resource_group` + outdated protection + release intent/CAS, lock до observed verification; active deploy/migration не interruptible. При downstream pipeline проверить wait/lock semantics, не создавать deadlock.

В обоих провайдерах отсутствующие secrets/права не обходятся SSH или расширением credentials. App runtime secrets извлекает runtime provider; build/deploy identities отделены. `.delivery/` хранит текущую конфигурацию, `.ai-development/` — объяснения и контекст следующих задач.
