# Training / validation отчёты и любой исход остановки

## Три представления

1. **Rolling report** — последний durable progress: identity, last observed metric/validation/snapshot/checkpoint, heuristic state и cost refs. Обновлять после committed diagnostic windows/evaluation/checkpoint и перед stop request; показывать freshness/gaps.
2. **Validation report** — immutable receipt для конкретного subject/protocol/dev split: primary/guardrails/slices, sufficient statistics/denominators, coverage/errors, uncertainty, paired baseline и generations refs. Training telemetry не подменяет это измерение.
3. **Terminal training report** — по attempt и cumulative logical run, при completed, early_stop, budget_stop, operator_cancel, data/integrity failure, NaN, OOM, provider termination/preemption, lease/deadline loss, worker/controller crash или blocked preflight. Причина и last observed state обязательны. Success не единственный исход, deserving report.

## Состояния не смешивать

`training_outcome=not_started|completed|stopped|failed|unknown`, отдельный reason; `provider_state/terminal_proof`; `report_status=complete|partial|unavailable`; `verification_status=verified|unverified|stale|not_run`; `benchmark_verdict=accept|reject|inconclusive|not_run`. Даже complete report о cancelled run не делает модель accepted. При stop request без provider terminal proof outcome остаётся unknown/stop_requested и reserve удерживается. После recovery новый report revision обновляет facts, старый сохраняется.

Completed означает заранее установленный training exit criterion, а не любой process exit=0. Early stop завершает разрешённую training policy, но не подтверждает useful model. Сбой финальной validation → report partial и benchmark not_run/inconclusive по фактам; нельзя скрыть это общим success.

## Минимальный terminal report

| Раздел | Обязательное содержание |
| --- | --- |
| Outcome | Outcome/reason, start/end/last observed, stop requester/ack/provider evidence, report completeness и unknowns |
| Subject | Plan/source/dependencies/model/tokenizer/template/data/preparation/config/protocol/probes hashes, attempts/segments и lineage |
| Progress | Completed optimizer updates, unique vs physically reprocessed tokens/examples, skipped/restarted work, planned limits и achieved coverage |
| Train | Objective components/normalizer, valid NLL/PPL при applicable basis, LR/grad/AMP/update/mix summaries и nonfinite/missing counts |
| Validation | Последние и best **реально выполненные** dev measurements, primary/guardrails/slices/support/uncertainty, protocol/basis, expected/evaluable/errors |
| Behavior | Fixed probe gallery/diffs, finish causes/length/completeness/repetition, snapshot hashes, missing samples и their reason |
| Heuristics | Каждая applicable rule: calibrated threshold/window, last state/observation, triggers, action/ack и evidence; disabled/not_applicable reasons |
| Checkpoints | Base, best-by-frozen-selection, last-good, last-written/unsafe и resume capability; hashes/file completeness; не alias разных ролей |
| Compute / cost | Actual elapsed/train/dev/generation/checkpoint overhead, useful throughput/memory, existing receipt IDs; estimate/provider/invoice/unknown reserves отдельно |
| Decision | Какой H-ID подтверждён/опровергнут/неопределён, evidence limitations, missing DoD, cheapest next test и условие разрешения следующего этапа |

Best checkpoint определяется заранее выбранной validation selection rule с tie-break/min_delta/guardrails. Last checkpoint не обязательно best, lower PPL не отменяет primary task regression. Final hidden test не используется для выбора best. Если weights missing/corrupt, report не ссылается на них как пригодный resume artifact. Configuration/subject drift инвалидирует прежнюю verification, не стирает измерения.

## Устойчивый finalizer

**До dispatch** создать durable start stub с policy hashes, owner и private artifact/report refs. Training writer публикует только committed bounded chunks; coordinator поддерживает rolling metadata. Stop controller сначала прекращает compute по существующим leases/budget policy, затем использует bounded cleanup margin для разрешённого checkpoint/export; не пытается любой ценой сохранить невалидные weights.

Terminal finalizer работает на уже durable local/private artifacts, без импорта модели, запуска GPU, оплаты judge или blind remote replay. Формирует machine-readable JSON + Markdown + plots, проверяет refs/hashes, atomic report manifest; `latest` pointer только после записи. Идемпотентный key: `(logical_run, attempt, terminal_event_id, input_manifest_digest)`. Repeated callback создаёт тот же результат либо explicit new revision после новых reconciliation facts, не duplicate spend/events. Financial truth читает existing ledger, не доверяет строке cost внутри training log.

Crash/SIGKILL/OOM может не исполнить finally. Поэтому coordinator recovery по истёкшему lease/observed terminal событию должен восстановить **минимальный partial report** из start stub и last committed chunks; missing metrics/output refs явно перечислить. При потере coordinator/storage сетью, report recovery запускается после восстановления доступа без training resume. Нельзя гарантировать запись в уничтоженное storage: доступный start stub/remote durable refs и recovery status — обязательная evidence, `unavailable` вместо fake report success. Report недоступен сейчас → явный operational diagnostic, next read-only recovery, не новый платный запуск.

Disk-full: stop writer/controller по policy, сохранить minimal safe status в доступном coordinator durable store; не удалять checkpoints/плохие samples для сокрытия сбоя. Corrupt trailing chunks не включать как valid observations. Recovery читает bounded approved artifacts, не raw provider logs/env dumps.

## Расход, stopping и выбор дальнейших действий

Финальная генерация/validation имеют заранее зарезервированное время/стоимость; при exhausted budget они NOT RUN. Report всё равно формируется из уже сохранённой evidence. Provider cancellation неизвестна — report partial + reserve/unknown, не `stopped=true`. Поздняя invoice/reconciliation меняет report revision, но не reset бюджета/attempts.

Handoff в target `.ai-development/ml` — безопасное summary, implemented plan revision, checks/remaining и ссылки private refs без чувствительных prompts. Полная private галерея не переносится в публичный Git. Report должен существовать и для нулевого полезного progress: исключение/стоп — результат эксперимента, а не отсутствие записи.

Шаблоны: [terminal training report](examples/training-report.md), [validation receipt/report](examples/validation-report.md), [design policy](examples/diagnostics-policy.example.md). Все поля пока примеры для реализации, не runtime-accepted JSON schema.
