# Общий workflow CI/CD скиллов

Применяется к `ci-cd-github` и `ci-cd-gitlab`. Это workflow подготовки/изменения реального проекта; не разрешение активировать deploy любого найденного production environment.

## 1. Контекст до выбора

Прочитать [обязательный журнал решений](../skills/decision-memory.md): target `.ai-development/INDEX.md` → связанные accepted ADR/context → сверка предпосылок. Определить target project отдельно от checkout скилла. При первом запуске создать task context/index; каждый новый принятый выбор объяснить до зависимого изменения, в handoff сослаться на использованные IDs.

Далее прочитать все common guides, provider guide и обнаруженные stack guides по [контракту](skill-contract.md). Эти локальные документы обязательны; проверять актуальную version-specific документацию для применяемых инструментов и функций. Недоступная база — blocker архитектурных рекомендаций, а не повод подменить её памятью.

## 2. Discovery и intent

Проверить manifests/lockfiles/workspaces/test scripts, существующие CI и Dockerfiles, `.delivery/` и принятые решения. Не открывать credentials, `.env`, state или private app data. Найти все Go modules, Composer packages, JS packages, Python projects, Cargo members и shared dependencies. Не навязывать новый framework/package manager/host ради шаблона.

Уточнить только отсутствующие существенные сведения: provider version/tier, runner architecture/capacity, registry/backend, envs, policy auto/manual и prod approvals, target identities/ресурсы и владельцы, migrations/rollback, timings и budget. Уже сохранённое не спрашивать повторно; stale metadata отметить и по разрешению сверить control-plane API. SSH/scp/rsync/Ansible-over-SSH/туннели не запрашивать и не использовать даже для bootstrap.

Следовать объёму запроса. Если пользователь просит только план, создать reviewable plan/ADR/config drafts и не менять активные workflows/settings. Если просит реализовать — автономно подготовить рабочие изменения выбранного проекта и необходимые проверки. Наличие API credentials не разрешает сменить unrelated environments/permissions. Права на конкретный scope, уже данные пользователем, не переспрашивать.

## 3. Решения и reviewable результат

Записать выбор backend, CI graph, test scope/selection, caches/shards, runner resources, artifact trust, env selection, config/schema, identity, logging, concurrency/stale protection и rollback в `.ai-development/ci-cd/<task>/decisions/`. Подтверждённый прежний выбор использовать через `reuses`, новый заменяющий — через `supersedes`. Рекомендации из источника и собственную адаптацию различать.

Артефакты task: `context.md`, `plan.md` с pipeline/trust Mermaid, `acceptance.md`, `handoff.md`; scratch отдельно. Actual workflows/config/scripts создаются в штатных путях проекта, не в папке установленного скилла:

- GitHub: адаптированные `.github/workflows/` и versioned reusable blocks; GitLab: `.gitlab-ci.yml`/versioned includes/components.
- `.delivery/project.yaml`, environments, JSON Schema(s) **под фактически выбранный контракт**, semantic validation и безопасные identity/secret references. Ни docs example, ни YAML parse не являются готовой schema validation. Проверить unknown fields/env/ref/backend/registry и связь service/env/image/target identity; bootstrap status `unverified` блокирует активный deploy.
- Общие test/build commands проекта, Docker/package changes только по нужде. Toolchain/actions/includes/base images pinned и проверены; placeholders означают draft. Не создавать фиктивный success deploy job, если backend/API/agent отсутствует.
- Release/build evidence: exact source+inputs+digest, required test/scans/provenance; deploy record exact env/desired/observed identity. Одноразовая сборка и packaged-candidate smoke до продвижения, исключения Next build-time config явно оформлены.
- Test/cache/performance budget и измерения; security/log/artifact policy; runbooks rollback/migrations/controller unavailable/identity rotation.

Короткое саммари должно объяснять что меняется, почему (ADR IDs + первоисточники), ожидаемый performance эффект/стоимость, ограничения и blockers. Credentials не включать даже в examples. При secrets prerequisite использовать штатный protected input/secret manager, не чат и не command argv.

## 4. Проверки до активации

Проверить с доступными инструментами: workflow/provider lint под нужную версию, shell/static analysis, schemas+semantic negative tests, stack test commands и packaged artifact smoke, зависимости graph/required gates, cache miss/cold/warm, controlled synthetic secret-leak harness по [security](security.md). Не исполнять неизвестные repository scripts с privileges/secrets без проверки их trust и effects.

Изолированный test repo/runtime — для реальных trigger/identity/env lock/stale tests, затем разрешённые environments. Недостающие credentials/tools/targets отметить NOT RUN; сохранять все остальные полезные результаты и blockers. Не отключать security gate/полный fallback, чтобы «прошло». Speedup — только observed timings на сопоставимом workload, отдельно queue и rollout observation.

## 5. Автоматический deploy и handoff

Когда включение входит в уже разрешённый scope и prerequisites проверены, активировать именно утверждённые events/env policy. Далее эти triggers работают автоматически без chat prompt на каждый run. Manual button — настроенная опция того же contract, не единственная форма prod authorization.

Зелёный статус только после exact desired/observed revision+digest, readiness/smoke и policy observation; Git push/PR merge не являются deployment success. При failure — stop/совместимый rollback через desired state/API, без SSH и arbitrary root commands. Active prod migration/rollout не отменять как устаревший PR CI. Для нового destructive scope показать конкретные последствия и остановить зависимую операцию до разрешения.

Обновить decision verification, INDEX и handoff: paths/IDs, что implemented/activated/verified, PASS/FAIL/NOT RUN, timings, pending blockers, следующий шаг. `.delivery/` — действующая конфигурация, `.ai-development/` — rationale/context, raw logs/секреты не сохраняются ни в одном из них.
