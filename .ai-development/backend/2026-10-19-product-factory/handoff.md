# Handoff: Product Factory v001

Реализована revision v001 по [плану](plan.md) и [spec](spec.md), включая clarification explicit AI handoff ADR 0006. Integration subject `e0b526cb73d48aafaf46f9eb9afbeeb2a93462e3`. 4/4 tasks verified; [canonical progress](progress.json), [actual verification](verification.md), [ADR index](../../INDEX.md).

Готово: строгий DAG/policy admission, immutable workflow snapshot, SQLite WAL/FULL и fenced queue, owned detached Git worktree, bounded command/Codex/Claude transports, retry/attempt/deadline/output limits, unknown-outcome pause/reconciliation, explicit AI needs_input/handoff, task + final independent gates, subject fingerprint/stale report, CLI status/events/export/cancel/resolve. Private reconciliation history сохраняет безопасную причину оператора. Runtime state не подменяет skill progress; source skills отвечают за свои SDD ledgers/ADR.

Проверки: 104 offline tests PASS; repo validation PASS; actual smoke и lab SLO PASS (p95 0.726ms на 100 claim+finish pairs, threshold 100ms). Live CLI providers NOT_RUN, account/cost/network integration не подтверждена. Operational SLA NOT_RUN. CI implementation run [39190418028](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39190418028) — PASS (offline + Terraform schema checks).

Запуск: [README](../../../docs/product-factory/README.md), `python3 scripts/factory_acceptance.py` для безопасного disposable smoke. Для продукта адаптировать [agent example](../../../examples/product-factory/backend-agent.json), source plan и feature-specific DoD; auth вне Git. Target repo должен иметь clean committed baseline, state отдельный приватный local root.

Остатки будущих этапов: parallel task worktrees/merge queue; PG/multi-host HA; market discovery/opportunity/product loop; разрешённый GitOps deploy/observation. Это за пределами v001, а не тайно выполненные функции. Никаких auto push/deploy, bypass permissions или бесконечного task discovery.

Следующая сессия: читать общий INDEX и accepted ADR 0001..0006, source plan/progress, сверить current code/fingerprint/evidence. Для расширений новая revision и impact/test matrix; не выдавать local lab proof за operational readiness.
