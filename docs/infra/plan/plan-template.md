# Шаблон результата infra-plan

Скопировать структуру в `plans/<target>/<date>/plan.md`, заполнить под конкретную машину. Не оставлять её универсальным чеклистом. Артефакты вне Git по умолчанию; публиковать только обезличенные после проверки.

## 1. Саммари для решения

Режим `inventory`/`--plan`, профиль low/med/high, цель, выбранный стек, ресурсы, estimated monthly cost/источник/дата, главные SPOF и unresolved blockers. В конце — вариант исправить либо начать deploy конкретной ревизии.

## 2. Основания и состояние

Repo commit базы знаний, перечень прочитанных `docs/infra/plan/*.md`, дата source verification. Таблица: параметр / значение / наблюдали или сообщил пользователь / evidence / уверенность. Неизвестные OS/arch/disk/CIDR/нагрузка — явно. Existing workloads и ограничения миграции.

## 3. Требования и sizing

SLI/SLO/error budget, RPO/RTO и почему; бюджет с compute/storage/backups/LB/NAT/traffic/telemetry/ops. Capacity worksheet с peak и headroom, отказным сценарием, surge capacity; owners, maintenance window и acceptance targets.

## 4. Схемы взаимодействий

Обязательны две Mermaid-схемы: data plane и management/delivery plane. Указать фактические Internet → firewall/LB → ingress → container/Kubernetes service/pods → DB и app → egress → внешние системы. Отдельно SSH/VPN, GitHub Actions → registry/GitOps → Argo → API, если эти компоненты выбраны; для low объяснить отсутствие Kubernetes/Argo.

Обозначить trust boundaries, направление/ports/TLS, узлы/зоны, storage и backup вне отказного домена. Mermaid сохранять в Markdown. Если renderer недоступен, дать рядом текстовое описание и отметить, что визуальный render не проверен. Не выдавать красивую схему за доказательство работающих правил.

## 5. Безопасность и flow matrix

Таблица source/identity → destination/identity → protocol/port → purpose → enforcement layer → IPv4/IPv6 → allow/deny verification → owner. Host, pod и management egress отдельно. SSH rescue, RBAC, secret storage/rotation, image provenance, audit, threat model и исключения с expiry.

## 6. Конфигурации

`config/` содержит адаптированные IaC/OS/runtime/network/GitOps/CI/storage/observability файлы по выбранной архитектуре. Список exact versions и откуда взяты. Для каждого файла — назначение, prerequisite, способ безопасной передачи секретов, dependency/order. Незавершённые параметры — draft/blocker; не заявлять deploy-ready.

## 7. Data и recovery

Data inventory: store / объём / рост / access mode / consistency / encryption / owner / RPO/RTO / backup mechanism / retention / restore drill. Секреты, ключи, IaC state и cluster datastore отдельно. План миграции и rollback для существующих данных.

## 8. ADR и открытые вопросы

Применимые кейсы из `decisions.md`, альтернативы, первоисточник рядом с утверждением, наша адаптация, стоимость/риск, owner, trigger пересмотра и blocker. Не приписывать компаниям наши конкретные конфигурации или sizing.

## 9. План развёртывания и отката

Этап / предполагаемый diff / предварительные условия / change owner / потенциальный простой / verify / rollback / abort condition. Разрешение пользователя на конкретный план/ревизию; отдельно replacement/destruction и расширение scope. Для default пока не получено разрешение — только план, не применение.

## 10. Проверки готовности

Каждая строка: criterion / численный target / команда или воспроизводимая процедура / expected result / observed result / evidence / статус PASS, FAIL, NOT RUN. Включить positive/negative ingress/egress, TLS, независимый SSH, rollout/rollback, alert delivery, DB restore и RPO/RTO, ресурсы; high — node/zone failure в разрешённом окне.

В `--plan` live tests пометить NOT RUN, данные — user-provided, deploy status — NOT DEPLOYED. Отдельно перечислить local validation и её ограничения.

## 11. Runbooks и handoff

Владелец и канал incidents, инструкции bad deploy/disk full/host lost/DB restore/secret rotation/upgrades. Ссылка на все локальные артефакты и короткое саммари: что готово, что остаётся неизвестным, что блокирует deploy. Пользователь должен иметь возможность исправить план или дать команду на выполнение без восстановления контекста из чата.
