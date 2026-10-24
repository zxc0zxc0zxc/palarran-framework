# Running, recovery and evidence

1. Prepare a separate trusted Git target with committed baseline. `create` rejects dirty targets; no remote calls/source-branch checkout needed. State is a new private local directory outside target/repo, chmod 0700; never publish DB/WAL or store on NFS. Use one state authority per target: independent states cannot share target-resource locks.
2. Copy the [example](../../examples/product-factory/smoke.json); adapt absolute executable paths, plan references/verifier commands. State saves immutable normalized snapshots/SHA-256. Editing original JSON does not alter existing runs. New scope → new run/revision.
3. `create --workflow FILE --target REPO --state DIR` returns run ID. `work --run ID --state DIR` runs until verified/failed/needs_input/cancelled; another worker cannot acquire the same run's active lease. `status` prints safe JSON IDs/status/attempts/reason/metadata, no prompts/argv/stdout. `events` is sanitized audit. `export` prints the same report, not a compatible skill-progress ledger.
4. On timeout/error inspect reason and your own safe diagnostics in target sandbox. Runtime stores no raw subprocess output; CLI tools may keep their own logs/auth caches with separately managed lifetime/access. Output caps bound streams; digests do not replace app logs. Workflows must contain no secrets; runtime cannot reliably detect them all.
5. After crashes run `work`: expired leases become needs_input. AI may also stop explicitly via needs_input handoff. First stop old process tree/review filesystem/external outcomes; then `resolve --run ID --task TASK_ID --reason SAFE_REASON --processes-stopped --state DIR`. Safe reasons enter private reconciliation history/next AI attempt. Replay spends another attempt; exhausted caps never reset. Unreconcilable outcomes require cancel/new reviewed run.
6. `cancel --run ID --state DIR` revokes the lease; a live worker kills its process group on next heartbeat. Without a worker, operators manually terminate orphans. Cancel is not rollback.
7. Preserve verified worktrees for review. Runtime never push/merge/deploys. Before transfer review `git diff`, `.palarran` and current status fingerprint. No auto cleanup: `git worktree remove PATH` only after preserving needed tracked/untracked/ignored data and no active run. SQLite backup uses consistent backup API with stopped workers; never copy just DB without WAL while active. Restore to separate state first, then reconcile unfinished runs.

## Proposed local SLO / SLA

Our v001 targets follow [Google SRE's SLI/SLO/SLA distinction](https://sre.google/sre-book/service-level-objectives/). No commercial SLA agreed; 30-day operational availability NOT_RUN.

- Correctness: 0 duplicate active claims/run, 0 accepted stale-token finishes in concurrency/fault tests.
- Recovery: detect expired leases on the next new-worker poll, within lease_seconds + 1s with a live poller. Detection time, not external-side-effect recovery.
- RPO: 0 lost committed SQLite transitions after process crashes on healthy local disk with FULL sync; disk/host loss excluded. Unknown process outcomes need reconciliation.
- Dispatch control-plane p95 <=100ms across 100 sequential claim/finish pairs for a synthetic no-op DAG on local disk, excluding subprocess startup/model latency. Preserve samples/environment/failures. Investigate FAIL rather than changing targets after measurement.
- Budgets: attempts <= cap; wall timeout plus <=1s cleanup grace; bounded output. Final verifiers also obey run/task deadlines.

Required tests: malformed DAG/policy, real command/file read-back, nonzero verifiers, retries/attempt caps, timeout/output flood/descendant kill, parallel claims/fencing, expired lease/reopen, operator gates, cancellation, immutable workflow, stale fingerprint, final cross-task regression, secret-sentinel absence in status/events/DB output. Final evidence belongs to the private target handoff, not the distributed library.

## Models and budget

Before work inspect create/status/export `budget`: requested model/effort/per-task allocations. The [contract](model-budgets.md) separates launch caps from unknown provider spend. Product CLI accepts `--ai-policy /path/to/policy.json` (regular non-symlink JSON <=64KiB); invalid policies fail before worktree creation. Policy changes require new runs. Allocate retries before create; resolve never refunds launches.

## Actual usage and stopping

The [usage contract](usage-accounting.md) defines caps/pricing sources. New product-run defaults: 600000 tokens/$12/run, 100000/$2/stage including retries. Example: `--usage-policy examples/product-factory/codex-usage-policy.json`. Custom Codex models require matching rate cards. `status`/`export` returns per-attempt/stage/run `usage` counters/cost/completeness; `budget` remains the launch guard. Unknown != zero; observed lower bounds are separate.

On usage_unknown stop the old worker, verify provider receipts/prepare contract-normalized JSON. This command executes nothing:

```sh
python3 -m orchestrator usage-reconcile --state /path/to/private-state --run RUN_ID --task TASK_ID --attempt 1 --usage-file /path/to/checked-usage.json --reason "Provider receipts checked" --processes-stopped
python3 -m orchestrator resolve --state /path/to/private-state --run RUN_ID --task TASK_ID --reason "Scope and prior outcome reconciled" --processes-stopped
```

Reconcile forbids decreasing observed counters/cost and never replenishes launch allocation; exceeded budgets remain terminal. Budgets cannot protect against invisible internal requests before the first event. Claude additionally gets `--max-budget-usd` for remaining stage/run estimates; overshoot stays visible. Financial invoices/subscription quotas remain separate telemetry.

## Context before AI dispatch

For module tasks set context.paths from SDD ownership and short context.query. Root/ancestor AGENTS are automatic; fresh target Graphify cache is used only with matching workspace snapshots, otherwise bounded source fallback. No automatic setup/indexing. Status exposes metadata receipts, not text; [full contract](runtime-context.md).

## Training diagnostics / reports

Optional frozen `execution_policy.diagnostics` enables [runtime diagnostics](../ml/debugging/runtime.md) (`debugging/runtime.md` in the ML section). Fit/evaluate instrumentation writes a private bounded stream; coordinator tracks rules/builds report/gallery/CSV/SVG. Terminal/stop/failure yields immutable report revisions; `python3 -m orchestrator ml-report --state /private/state --run RUN` recovers reports without training/provider calls. `status` is read-only. Optional `preprint=true` exports a LaTeX evidence draft without AI calls; compile/submission NOT RUN. Legacy runs without diagnostics get partial reports, not diagnostics PASS.
