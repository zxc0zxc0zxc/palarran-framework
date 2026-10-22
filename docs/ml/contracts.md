# Контракты экспериментов и артефактов

Ниже — поля переносимого skill workflow. JSON/Markdown шаблоны помогают заполнению; общий standalone progress template не становится автоматически runtime schema. Для явного ML pipeline уже реализованы отдельные [typed manifests, approvals и accounting gates](pipeline-contract.md); их требования строже свободного standalone отчёта.

| Артефакт | Обязательное содержание |
| --- | --- |
| `context.md` | target, вопрос, modalities, constraints, inspected code, reused decisions, unknowns |
| `revisions/vNNN/experiment.md` | experiment_id/revision/hash, H-IDs, baseline, dataset/model refs, protocol, budgets, stop, tasks/DoD |
| `hypotheses.md` | H-ID, ожидаемый механизм, falsification, evidence refs, ablation, cost cap, disposition |
| `model.md` | owner/model/revision/license, tokenizer/config hashes, method, alternatives, VRAM assumptions, serving constraints |
| `data-card.md` | source revisions/licenses/permissions, provenance, schema/label unit, PII handling, split policy/hashes, quality/leakage evidence |
| `cost.json` и `cost.md` | source/as-of/currency/unit, billed-resource scenarios, attempts/phase allocation, extras/unknowns, reserve, confidence |
| `runs/<run-id>/attempts.jsonl` | append-only safe lifecycle events, provider IDs, parent/retry cause, authorization scope ref, timestamps, receipts |
| `runs/<run-id>/manifest.json` | exact plan/source/image/dependencies/hardware/data/model/tokenizer/config/seeds, checkpoint lineage, status |
| `runs/<run-id>/usage.jsonl` | estimated/accrued/provider_reported/invoiced **раздельно**, currency/period/as-of, lower/upper/reserve, unknown disposition |
| `benchmark.md` | frozen protocol + dataset hash, checkpoint hash, baseline, hardware/config, metrics/CI/slices, failures, independent command evidence, verdict |
| `progress.json`, plan table, `handoff.md` | source revision, task/gate/subject/evidence, remaining work и причины |

Ссылки на inputs имеют artifact ID, revision, relative path либо разрешённый private URI, SHA-256. Model/tokenizer — repo revision и content digest конкретных файлов; dataset fingerprint библиотеки сам по себе не доказывает неизменность всех внешних файлов. Сохраняй file-list hashes и transform commit/parameters. Код с dirty tree требует patch digest/сохранённый безопасный patch; один HEAD не описывает выполненный код.

E-ID задаёт URL/publisher/title, publication/update (unknown если нет), retrieved/as-of, scope, claim, тип `observed/author_report/vendor_claim/hypothesis/scenario/unknown`, limitation. H-ID ссылается на E-ID/ADR; source article не доказательство результата на нашем dataset. Cumulative IDs не перенумеровывать между этапами. Смена upstream отмечает downstream requiring_review.

## Run identity и checkpoint

У каждого attempt собственный ID; logical experiment ID переживает retries. Checkpoint manifest содержит weights/adapter/base revision, optimizer/scheduler/scaler, RNG всех использованных источников, sampler/dataloader position где поддержано, step/epoch, config/data/tokenizer refs. Весов достаточно для inference, но недостаточно для точного training resume. Укажи, если восстановление только приближённое. Каждый rank пишет в собственный путь; общий финальный manifest публикуется после проверки полной записи и durability.

## Evidence и вердикт

Independent check исполняет зафиксированную evaluation command на **финальном** checkpoint, проверяет dataset/protocol digest и формирует exit status + aggregate report. Training worker «всё готово» не этот check. Изменение checkpoint после проверки инвалидирует результат. Если evaluation не был независимым, нет bootstrap/обязательной slice, недоступны данные или часть примеров упала — явно partial/unverified. Числовые нули отличаются от null/unknown; отсутствие метрики не нулевой error rate.

Benchmark verdict `accept/reject/inconclusive/not_run` сопровождается gate-by-gate результатами. Один синтетический пример шаблона не accepted run. Publication/production rollout — отдельная задача.

## Приватность и хранение

В Git/ADR только безопасные metadata, агрегаты и разрешённые примеры. Не сохранять raw prompts/customer datasets, PII, auth URIs, env dumps, полные provider logs, приватные цепочки рассуждений. Объектные пути/хеши тоже могут раскрывать сведения: выбери private storage и access policy при необходимости. Tracker artifacts и retention/delete policy определяются до upload. Сохраняй краткие решения и observable step summaries для будущего контекста, включая неуспешные эксперименты.

## Design extension: диагностика обучения

[Artifact/event envelope](debugging/artifacts.md), [validation metrics](debugging/task-metrics.md), [rule states](debugging/heuristics.md), [generation snapshots](debugging/generations.md) и [terminal reports](debugging/reports.md) задают design-v001. На каждый attempt и logical run: start stub/rolling/terminal report, full permitted outputs и private refs, source/subject/decoding hashes, missing/unknown evidence. Полные samples остаются private. Новые schemas и finalizer ещё не runtime implementation; wire migration и DoD — в [плане](debugging/integration-plan.md).
