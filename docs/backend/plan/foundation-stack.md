# Foundation сначала, фича потом

## Исследование без live действий

Прочитать target README/product specs, instructions/decision indexes, существующие languages/runtime/lockfiles, routes/contracts/schema/tests, local CI/delivery/infra descriptions. Инфраструктуру оценить по доступным configs/документам, не SSH/cloud inspection. Зафиксировать baseline commit и relevant dirty changes; неизвестные CPU/RAM/network/storage/traffic/on-call отметить assumptions и запросить критичные данные. Не читать `.env`, private keys, customer dumps или secret-bearing state.

Если backend есть — foundation review заканчивается выводом **reuse** с версиями/границами, capabilities/gaps и причинами. Не перепланировать весь продукт ради одной фичи. Если нет backend либо определённого stack — сначала заполнить [foundation](../../../templates/backend/foundation.md): domain/workload, deploy shape, language/runtime/framework, modules, storage, API/event format, auth/tenant boundary, local dev/testing/CI, observability и infra fit. Установку всего этого только запланировать.

## Выбор стека — наша контекстная матрица

| Кандидат | Возможные основания | Что проверить до выбора |
|---|---|---|
| Go | Concurrent I/O/network services, existing team/code, простой deploy artifact | Domain/library fit, memory/GC/latency budget, SQL/tooling |
| PHP | Existing Laravel/Symfony/product expertise, transactional web app | Worker/runtime/concurrency model, queue lifetime, ops support |
| TypeScript | Общие типы/ecosystem с frontend, I/O APIs, existing Node runtime | CPU-bound jobs отдельно при необходимости, runtime validation/async/resource limits |
| Python | Existing domain/data/ML libraries, team productivity, async/sync integration | Runtime/process model и workload; не обещать CPU throughput без benchmark |
| Rust | Обоснованные memory/safety/latency требования и команда | Complexity/time-to-deliver, drivers/toolchain/ops; не назначать только за репутацию скорости |
| Existing JVM/.NET/другой | Реальный backend/team ecosystem | Сохранить при пригодности; список выше не закрытый |

Эта таблица не сравнительный benchmark и не endorsement компаний. Не переносить generic claims о языке в цифры SLA. Сравнить 2–3 **реальные** альтернативы, выбрать минимально достаточную по team skill, ecosystem, constraints, hiring/maintenance, deploy footprint и migration cost. Для конкретных API/runtime versions проверить official docs, если предлагаем новую технологию.

Relational DB — кандидат при relational invariants/transactions/access patterns; document/KV/time-series/search/object storage выбирать по запросам, consistency и объёму, а не тренду. Search index/read model обычно derived, его rebuild/lag указать. Cache/queue/оркестратор **не обязательны по умолчанию**. Обосновать каждый новый stateful component, resource/cost/backup/monitoring owner.

## Gate foundation → feature

Определены module/data ownership, proposed stack с alternatives, API/event style и versioning, auth/data boundary, deployment/resources/test strategy, numerical workload assumptions и critical unknowns. При blocking вопросах foundation остаётся proposed; downstream feature outline возможен условно, но не execution-ready task plan с ложной определённостью. Если язык уже установлен, code sketches/interfaces/queries адаптируются к нему; planning не изменяет build files.
