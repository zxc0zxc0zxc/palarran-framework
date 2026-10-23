# ML runtime contract v001

## Workflow и inputs

Workflow v1 получает optional `ml_policy` только для `name: ml-pipeline`. Содержит `pipeline_id`, `context_sha256`, `skills_root`, `artifact_root`, `total_usd`, `backend`, `resources` для `ml-fit`/`ml-evaluate`. Каждая resource task — command, `replay_safe=false`, `verify_stable=true`; reserve_usd, rate_usd_per_second, fixed_usd, max_seconds, rate_source, rate_as_of и pinned files. Reserve покрывает fixed + rate × max_seconds; сумма reserves + usage_policy.max_cost_usd не выше total. Backend `local` или `modal`; Modal fields/remote recovery определены в [adapter contract](modal-adapter.md). Executable и operator-declared dependency files pin по SHA-256; изменения отвергаются до dispatch, не после платного старта. Allowlist не sandbox и не проверка всей dependency closure: policy только для доверенного кода.

Context pin: request, baseline, policy и source digest ML docs/skills/runtime. При каждом verifier и перед execution проверяются exact bytes. Artifact prefix: `.ai-development/ml/pipeline-ID/`. Stage order `hypotheses,plan,model,data,cost,train,benchmark`, затем optional approved ml-prepare для text, fit/evaluate. Новые compiler requests обязаны задать data_mode=text|non_text; exact data contract ниже. Все outputs stage-qualified, ничего не перезаписывать; next stage inputs содержит canonical manifest hashes **всех** предшественников. Common INDEX не второй ledger, canonical progress — private SQLite; project progress/plan — derived snapshot.

## Stage manifest

`stage.json`: schema_version=1, pipeline_id, stage, context_sha256, inputs, report `{path,sha256}`, evidence, decisions, hypotheses, lineage, unknowns, status=`planned`. Полная форма — [пример manifest](../../templates/ml/pipeline-stage.example.json); placeholders намеренно невалидны до адаптации. Evidence record: id/claim/source/classification; decision: D-ID/path/sha256 с canonical `ml/...` ADR metadata, шестью shared explanation headings и обоими IDs в target INDEX; unknown: id/critical/disposition/evidence_ids. Cumulative IDs/records/lineage сохраняются; additions разрешены. Только unknown unresolved→resolved может измениться при сохранённой criticality и ссылке на evidence; старый manifest остаётся. Новая revision требует отдельного run. Все refs относительны target, symlinks/FIFO/path traversal запрещены; reports <=256 KiB, manifest <=1 MiB. Sensitive данные/weights не в reports.

С plan появляются lineage `experiment`; model добавляет `model,tokenizer`; data — `data`; train — `config`; benchmark — `protocol`. Все нужны перед execution. Frozen `protocol` — JSON с primary metric `{name,direction:min|max,threshold,minimum_delta}`, guardrails list `{name,direction,threshold}`, required_checks list. Метрики/threshold конечны, minimum_delta неотрицательна. Это acceptance proposals до оператора, не измеренные результаты. Critical unresolved unknown блокирует approval.

## Trusted jobs и telemetry

Execution commands получают JSON stdin с workspace/pipeline/context/lineage, private artifact directory и output paths. Train пишет `checkpoint.bin`; evaluator читает его и protocol, пишет `evaluation.json` в private artifact directory. Никаких secrets в argv/stdin/usage. Large artifacts вне Git; final check streaming-hash проверяет actual checkpoint (bounded file size), не только pointer. Artifacts append-only по этапам, evaluator не меняет checkpoint.

Stdout JSONL usage: `{"type":"ml.usage","sequence":1,"cost_usd":"0.01","terminal":false}`. Cost — cumulative adapter report одного attempt, USD decimal; sequence возрастает на 1, cost не убывает, replay только byte-equivalent. Terminal true ровно один и последний; null cost/нет terminal/ошибка парсинга означает unknown и удержание reserve. Обычные training logs не сохраняются; output ограничен. Supervisor estimate=fixed+elapsed×rate контролируется независимо от telemetry, чтобы молчание не отключало бюджет. Estimate/report/invoice не складываются как три расхода: charged basis=max(estimate,reported), unknown reserve сохраняется отдельно.

Evaluation JSON: schema_version=1, checkpoint_sha256, protocol_sha256, metrics, baseline, sample_count>0, checks (bool values), verdict=`accept|reject|inconclusive`. Independent verifier вычисляет verdict из frozen primary threshold+minimum_delta и guardrails; missing required evidence допускает только inconclusive. Все числа конечны, отсутствие не ноль. Runtime verification означает integrity/protocol acceptance; правдивость labels, operational SLO и market usefulness требуют своей evidence.

## Durable state и recovery

Private tables resource attempts/approvals имеют run/task/attempt/token, reserved/estimated/reported, state и history. Approval exact prepared prefix создаёт CLI operator, AI file не authority. Admission/lease и resource reservation одна SQLite transaction. Active/unknown row не может быть освобождён `resolve`; отдельное reconciliation требует stopped assertion и cumulative cost не ниже уже наблюдённого. Никакого автоматического refund и reset budget. Lost lease, cancel, supervisor error сохраняют unknown. `ml-reconcile` не делает job verified; новый task attempt требует того же valid approval, remaining attempts и reserves.

## CLI

`ml-create --idea-file ... --target ... --state ... --adapter codex|claude --agent /absolute/cli --ai-policy ... --usage-policy ... --execution-policy ...` создаёт run без вызова providers. `work/status/events/cancel` общие. `ml-approve --state ... --run ... --prefix-sha ...` разрешает только exact подготовленный prefix. `ml-reconcile --state ... --run ... --task ml-fit|ml-evaluate --attempt N --cost-usd ... --processes-stopped` сохраняет отдельную receipt/cost и не повышает ceilings. Все live действия — explicit `work` с разрешённым конфигом. Нельзя обходить CLI разрешений или автоматически продолжать нуждающийся в уточнении этап.

## Local text data gate

[Реальный tokenizer/collator и mandatory preparation gate](data/pipeline.md). Explicit data_preparation policy; legacy non-text не получает фиктивный PASS.

## Training diagnostics / reports

Optional frozen `execution_policy.diagnostics` подключает [runtime diagnostics](debugging/runtime.md) (в ML-разделе — `debugging/runtime.md`). Fit/evaluate instrumentation пишет private bounded stream, coordinator отслеживает rules и собирает report/gallery/CSV/SVG. При terminal/stop/failure — immutable report revision; `python3 -m orchestrator ml-report --state /private/state --run RUN` восстанавливает report без training/provider calls. `status` read-only. Optional `preprint=true` экспортирует LaTeX evidence draft без AI call, compile/submission NOT RUN. Legacy без diagnostics получает partial report, не diagnostics PASS.
