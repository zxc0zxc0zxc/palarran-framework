# Modal adapter: execution plan

Revision: modal-v001. Основание: accepted 0001. Coordinator-only shared progress; worktrees/implementation agents здесь не запускались.

| ID | Требование / DoD | Прогресс | Evidence |
| --- | --- | --- | --- |
| M1 | Documentation, primary SDK references, decisions before code | done | docs/ml/modal-adapter.md; decisions/0001-adapter.md |
| M2 | Strict additive Modal policy; no calls at create/approve | done | ml_pipeline, ml_resources, fake admission tests |
| M3 | Durable intent/identity, named Sandbox; no blind replay | done | modal_adapter, lost reply tests |
| M4 | Bounded metrics history, rate estimates, retained billing reserves | done | SQLite metrics/resource tables; status; reconciliation tests |
| M5 | Budget/deadline/lease stop and remote terminal proof | done | stop supervisor; fake deadline/unconfirmed stop tests |
| M6 | Cancel/recover without live worker; no provider resource creation | done | CLI and recovery; fake provider/SDK |
| M7 | Frozen protocol + exact checkpoint independent acceptance | done | remote fixture chain + existing stable verifiers |
| M8 | Full offline suite, structural validator, runtime acceptance | done | 259 full tests + 10 focused Modal; handoff |
| M9 | Live Modal integration / GPU invoice / operational SLA | not run | Outside authorization; no paid test launches |

Проверенная revision modal-v001; результаты и ограничения записаны в handoff.md. Commit отсутствует: текущий workspace включает предыдущие незакоммиченные ML changes, они сохранены. Новые examples инертны, target product pipeline и его бюджет не затрагивались.
