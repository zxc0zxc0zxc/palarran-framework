# Матрица acceptance

| Requirement | Cases | Evidence |
|---|---|---|
| R1 | unknown fields, bool/NaN/negative numbers, duplicate/cyclic/missing deps, invalid argv/env/policy | test_factory_contract |
| R2 | two claimers, stale fencing, DB reopen, expired unknown, attempts cap, dependencies | test_factory_core |
| R3 | actual exit, nonzero, timeout, flood, subprocess descendant cleanup, heartbeat lost, stdin/env, CLI argv | test_factory_runner |
| R4 | real file read-back, final gate regression, changed subject stale | test_factory_core |
| R5 | create target worktree isolation, CLI status/cancel/reconcile, snapshot unchanged, secret output absent | test_factory_core |
| R6 | 100 claims p95 <=100ms, validator, full offline suite | verification.md |

Faults only in disposable local targets/DB. Live provider execution NOT_RUN until actual evidence. Operational 30-day SLA NOT_RUN, не v001 lab DoD.
