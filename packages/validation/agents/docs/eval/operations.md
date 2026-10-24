# Operations and boundaries

`/palarran:agent:eval {task or suite} [--plan]` first reads mandatory guides and target memory. --plan writes protocol/rubric/ADR only; no worktree or command execution. Without it, execute only an explicitly authorized local suite; paid model calls require concrete budget/scope. Repository tests are always offline.

CLI from a full palarran checkout (portable skills include guides/templates; runtime is separate):

```sh
python3 -m orchestrator.agent_eval create --suite /path/to/reviewed-suite.json --target /path/to/clean-target --state /path/to/private-state
python3 -m orchestrator.agent_eval work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator.agent_eval report --state /path/to/private-state --run RUN_ID
python3 -m orchestrator.agent_eval compare --state /path/to/private-state --run RUN_ID --other-run OTHER_ID
```

Create calls no models but creates an owned worktree. AI work additionally requires `--allow-model-calls`; a technical gate, not a substitute for human authorization/shared budget. Configure ai_policy/usage_policy and explicitly include historical carry/unknowns. Do not create a new cash allowance for comparison or after failure. Repeated work retains the same ledger/limit. A new suite/run does not itself combine spending across runs: the coordinator must carry previous charges/reserves before new admission. Thus v1 has no automatic repeated trials.

Budget stop responds to observed usage receipts/timeouts; providers may exceed the cap before the first event. This is not a transactional provider spending ceiling. A hard financial cap requires a separately limited provider account/gateway; reconcile invoices separately.

Cancel/resolve/usage-reconcile use the existing `python3 -m orchestrator` lifecycle. Unknown outcomes are not replayed. Runs fail fast; a corrected grader/new trial requires a new revision and reviewed remaining shared budget. No further model measurement before reconciliation. CLI performs no install/auth/account setup/SSH/deploy.

Synthetic `examples/palarran-agent-eval/suite.example.json` requires replacing absolute Python/external check_build.py paths and works only with a disposable trusted clean Git target. It generates structured answers and checks them: a contract smoke test, not real model results. Offline tests also check an actual Python bug fix through an external grader and fake-provider receipts/over-budget stops.

Results/rationale: target `.palarran/palarran-agent-eval/<task>/` with protocol revision, private-run references, sanitized report, decisions and handoff. Never copy private bundle/receipts/raw output into Git. Record chosen fixtures, source applicability, comparison conditions and NOT_RUN checks. Optional fresh Graphify supports navigation; missing graphs never waive AGENTS/ADR reads.
