# Handoff — training debugging design-v001

## Создано

[Маршрут](../../../docs/ml/debugging/README.md), source register E-DBG-001..012, contracts хранения/metrics/heuristics/generations/reports, pending implementation DAG и четыре portable examples (training/validation report, fenced JSON diagnostics policy/generation snapshot). Existing ML metrics/train/plan/benchmark/contracts guides и experiment template направляют к дизайну. Root domain contract уточнён.

PPL = exp(actual target NLL), sums/counts after causal shift, без averaging batch perplexities. Нужны task metrics/guardrails и slices; PPL не independent quality. Для DPO/diffusion/classical задач metrics выбираются по objective/task, а не автоматически PPL. Rule registry хранит inputs/basis/applicability/calibration/window/support/state/action/evidence; hard predicates/budget выше soft review.

Fixed dev probes с frozen decoding и exact subject: baseline/intermediate/best/last, полные private observable outputs, errors/length-stop/missing evidence не скрываются. Restore train RNG/mode/state, no hidden-test selection и no silent truncation. Full nontext media artifacts вместо fake token IDs.

Report обязателен при завершении, early/budget/operator stop, NaN/OOM/crash/lost lease/unknown provider outcome, включая blocked preflight. Start stub + rolling durable state + coordinator recovery; partial/unavailable честно при катастрофической потере storage. Budget stop не откладывается ради eval/generation. Training outcome, provider proof, report completeness и benchmark verdict независимы.

## Проверки и границы

PASS: repository validator (links, mandatory docs, portable refs), portable packaging 4 tests / 0.463s. Два fenced JSON templates разобраны strict parser без duplicate keys/NaN; status NOT RUN. Initial packaging FAIL выявил missing JSON resources из docs; исправлено переносом design JSON в Markdown code blocks без code/packager changes. После финального journal update validator повторён.

Runtime code/skills/CLI не менялись. Collectors/scorers/heuristic controller/generation hooks/finalizer/recovery пока NOT IMPLEMENTED; все DBG-01..06 pending. Полный runtime suite не запускался повторно ради documentation-only changes; предыдущие 354 tests относятся к data-gate задаче, не evidence нового diagnostics runtime. Нет paid APIs/GPU/training/model/data downloads/provider execution или изменения бюджета/state.

Следующий scope: строгие versioned schemas/preflight, durable stream collector и normalizers, затем tracked rules/probes, report finalizer/recovery и offline failure injections. Переиспользовать существующие leases/financial ledger, bounded Modal channel мигрировать версионно; нынешний finite metrics snapshot не final report. Подробности [implementation DAG](../../../docs/ml/debugging/integration-plan.md).

## Последующее исполнение

Исторический documentation-only результат выше сохранён. Текущий implemented scope и ограничения: [diagnostics-runtime handoff](../2026-10-23-diagnostics-runtime/handoff.md).
