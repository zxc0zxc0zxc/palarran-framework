# Контракт /ci-cd:github и /ci-cd:gitlab

Созданы переносимые `skills/ci-cd-github` и `skills/ci-cd-gitlab` и slash-адаптеры. Это контракт их применения, не обещание уже работающего application pipeline. Credentials, targets и agents ai-tools не подключает автоматически.

## Обязательное чтение

Скилл сначала выполняет [общий контракт памяти решений](../skills/decision-memory.md), затем читает `docs/ci-cd/README.md`, `evidence.md`, `workflow.md`, `architecture.md`, `performance.md`, `security.md`, `environments.md`, `decisions.md`, этот контракт, `sources.md`, guide выбранного provider и все обнаруженные `stacks/*.md`. Если база отсутствует — запросить checkout, не планировать только по общим знаниям. В результате указать реально прочитанные paths/commit и применимые первоисточники; claims компании и нашу адаптацию различать.

## Intake и discovery

1. Read-only repository inventory: manifests/lockfiles/toolchains/workspaces, CI files/Dockerfiles, test scripts/suites и их runtime, dependencies/shared graph, migrations, существующая `.delivery/` registry, ownership и branch policies. Не читать `.env`, credentials, private state или app production data.
2. Определить provider/version/tier, runner pools/arch/capacity/cache storage, registry и deployment backend. Сохранённый config использовать первым; не спрашивать повторно уже известные параметры.
3. Уточнить только существенное: dev/test/prod и их capacity/arch, auto/manual preference, source/ref policy, нужны ли prod approvals, SLO/rollback/migration requirements, бюджет и baseline timings. Пользователь может дать характеристики; отсутствие SSH не мешает проектированию.
4. Live metadata разрешённого control-plane API читать по необходимости и в пределах предоставленного доступа; без credentials готовить draft и список blocker. **SSH-доступ к host не запрашивать**, runtime secrets не собирать через чат.
5. Проверить mismatch между config и actual identity/namespace/revision/capacity; актуализация через reviewed project configuration, не неявное изменение target.

## Результаты применения

- Краткое решение: выбранные provider/stacks/backend, текущие bottlenecks, измеримые цели, ограничения, вопросы и ADR.
- Pipeline graph + traffic/trust boundary graph; список source/events/jobs/gates/identities/cache/artifact boundaries.
- Адаптированные workflow files выбранного provider и stack commands без deploy по SSH; pinned versions/refs и явные prerequisites.
- Schema-validated `.delivery/project.yaml` и per-env registry без secrets; migration существующей конфигурации без потери полезных сведений.
- Release/evidence/deployment manifests и правила promotion/manual buttons/auto events, environment authorization, lock/CAS/stale protection.
- Cache/test-selection/sharding plan с full fallback, budget sheet и способами измерения до/после.
- Secret handling/log/artifact redaction policy и negative tests; runtime secret references отдельно от CI credentials.
- Runbooks bad deploy/rollback/migration failure/identity rotation/cache invalidation/controller unavailable и ownership.

Скиллы создают и проверяют конкретные reviewable изменения, а не только советы. На стадии реализации ранее данное разрешение на соответствующий scope не спрашивается повторно. Включение auto deployment на реальные environments требует настроенного authorization/policy contract; его trusted triggers применяют изменения автоматически без chat approval на каждый run. Optional approval gates задаёт проект, не универсальное требование скилла.

## Приёмка реализации

| Область | Доказательство |
|---|---|
| Документация | Использованные guides/commit, источники возле решений, неизвестное помечено |
| Trigger correctness | PR/MR, merged/protected release, manual и auto events покрыты сценариями |
| Stack correctness | Обнаружены все modules/packages/workspaces, команды и versions совместимы |
| Test scope | Required aggregate не пропускает failed/cancelled/missing tests; impacted closure и full fallback проверены |
| Performance | p50/p95 cold/warm + queue/cost до/после на сопоставимых changes, bottlenecks названы |
| Cache | Cache miss проходит, ключи корректны, untrusted write не отравляет trusted build |
| Artifact | Digest/source/inputs/evidence связаны, packaged candidate прошёл smoke |
| Promotion | Выбор env не rebuild; Next build-time exceptions явно покрыты variants/evidence |
| Permissions | Unknown env/ref/release/actor и invalid OIDC claims rejected |
| Secrets | Synthetic sentinel не найден в logs/reports/cache/layers известных tested failure paths |
| Deployment | Нет SSH/scp/rsync/tunnels, no arbitrary remote scripts; exact observed revision/digest и smoke |
| Concurrency | Нет stale overwrite, lock охватывает rollout/verification, prod change не оборван superseded CI |
| Recovery | Failed rollout и совместимый rollback verified, DB data rollback не обещан без процедуры |
| Project memory | New run воспроизводит config из repo, secret values отсутствуют, drift/verified_at видны |

Результаты помечаются PASS/FAIL/NOT RUN с evidence. Offline validation не доказывает cloud IAM, protected-environment gates, отсутствие утечек при всех ошибках или реальный runtime rollout. Пока эти проверки не запускались — только запланированная проверка, без заявления «всё работает».

## Неймспейсы и упаковка

В checkout доступны project adapters `/ci-cd:github` и `/ci-cd:gitlab`, а portable skill names — `ci-cd-github`, `ci-cd-gitlab`. Для другого проекта собрать отдельный namespace `ci-cd` через `scripts/package_plugin.py` по root README. Пакет включает обязательные docs/templates и не ссылается за пределы plugin root. Корневой `infra-plan` manifest сохранён; production pipelines не активируются самим фактом установки скилла.
