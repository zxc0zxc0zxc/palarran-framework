# CI/CD: база знаний github/gitlab скиллов

Статус: база знаний и [GitHub](../../skills/ci-cd-github/SKILL.md)/[GitLab](../../skills/ci-cd-gitlab/SKILL.md) скиллы реализованы. Вызовы: `/ci-cd:github`, `/ci-cd:gitlab`. Application pipelines, credentials, runners и deployment agents создаются/подключаются только при применении к конкретному разрешённому проекту.

## Контракт

- Быстрый проверяемый CI для Go, PHP, TypeScript/Next.js, Python и Rust, с измерением времени и обязательной оптимизацией.
- Автоматическое применение через GitOps, managed deployment API или ограниченный pull-controller. **Никакого SSH-доступа к target из скилла или pipeline**, включая `scp`, `rsync`, Ansible over SSH и SSH-туннели. Инфраструктурный bootstrap — отдельный заранее согласованный процесс.
- Опциональная кнопка выбора `dev`, `test`, `prod` запускает автоматизацию для уже проверенного release. Автодеплой по политике тоже поддерживается. Ручной запуск не означает ручное применение.
- Память проекта — версионированные конфигурации environments и deployment contract в `.delivery/`; секреты там запрещены. Не использовать историю чата как источник сведений о production.
- Отсутствие секретов в logs, reports, images и caches — критерий приёмки. Masking полезен, но не считается доказательством отсутствия утечек.
- Скилл обязан читать эту базу, выбранный provider guide и **все обнаруженные stack guides** до проектирования; источники и отклонения показывать в результате.

## Навигация

| Документ | Назначение |
|---|---|
| [evidence.md](evidence.md) | Что взято у Google, Meta, Netflix, Microsoft, AWS и что адаптируем сами |
| [architecture.md](architecture.md) | DAG pipeline, trust boundaries и deployment без SSH |
| [performance.md](performance.md) | Critical path, cache, sharding, affected tests, измерение скорости |
| [security.md](security.md) | Secrets/logs, identities, runners, supply chain и negative tests |
| [environments.md](environments.md) | Память проекта, кнопки стендов, promotion и защита от stale deploy |
| [github.md](github.md) | GitHub Actions jobs/events/permissions/environments |
| [gitlab.md](gitlab.md) | GitLab DAG, rules, inputs/manual jobs, защищённые environments |
| [stacks/go.md](stacks/go.md) | Go modules, build/test cache, race, binaries |
| [stacks/php.md](stacks/php.md) | Composer, PHPUnit/ParaTest, PHPStan, PHP-FPM/workers |
| [stacks/typescript-nextjs.md](stacks/typescript-nextjs.md) | Lockfile, Next cache, E2E и build-time/runtime конфиг |
| [stacks/python.md](stacks/python.md) | uv/pip, pytest/xdist, wheel/container compatibility |
| [stacks/rust.md](stacks/rust.md) | Cargo, sccache, nextest/doctests, release builds |
| [decisions.md](decisions.md) | Открытые решения и аргументы |
| [workflow.md](workflow.md) | Пошаговая работа скилла от контекста до реализации и handoff |
| [../skills/decision-memory.md](../skills/decision-memory.md) | Обязательное объяснение каждого выбора и контекст следующих задач |
| [skill-contract.md](skill-contract.md) | Входы, результаты и acceptance скилла |
| [sources.md](sources.md) | Проверенные первоисточники, даты, ограничения |

## Как применять

Сначала выбрать stack(s) по repository manifests и реальным test commands, затем CI provider и deployment backend из сохранённой конфигурации. Размер VPS не определяет язык/тестовую стратегию. В monorepo строить dependency graph, учитывать shared libraries, lockfiles, Dockerfile/base image, schema, tooling и workflow changes; неполная карта означает full validation.

Первый пригодный baseline: весь обязательный release suite проходит на release commit; артефакт traceable до source/toolchain/lockfile; deploy только разрешённого digest; окончательный статус после rollout и smoke/SLI checks. Ускорение нельзя получать обходом обязательных тестов. Численные latency budgets — наши цели для согласования, не обещания бигтехов.

Для подготовки самой инфраструктуры существует [отдельная база](../infra/plan/README.md). Её SSH workflow не распространяется на эти скиллы: здесь действует явное требование пользователя о deploy без SSH. При отсутствии API/controller доступа скилл фиксирует blocker и готовит bootstrap requirements.
