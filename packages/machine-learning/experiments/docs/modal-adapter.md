# Modal adapter: bounded Sandbox execution

First read the [pipeline](pipeline.md), [contract](pipeline-contract.md), [Modal guide](modal.md) and accepted target ADRs. This adapter extends the local backend; `ml-create` still only plans, and `ml-approve` authorizes the exact verified prefix. A request to develop the adapter does not authorize a paid run.

## Why Sandbox

The [Modal Sandbox reference](https://modal.com/docs/sdk/py/latest/Sandbox) describes named GPU sandboxes, lifetime timeout, poll and terminate. This is a vendor API; our choice is a separate Sandbox per phase/attempt so the whole task can be canceled. Functions and Sandbox have different prices. Use existing App, Image ID, Volume and an explicit environment; never deploy/build/create_if_missing. Network is blocked; the operator prepares model/data/dependencies beforehand. Checked 2026-10-22.

## Policy and remote protocol

Execution policy uses `backend: modal`; all other local-policy fields remain. Every train/evaluate block gets `modal`: `app`, `environment`, `image_id`, `volume`, `gpu`, `cpu`, `memory_mb`, `argv`, `poll_seconds`, `rpc_seconds`, `stop_seconds`. Local argv/files pin the trusted adapter entrypoint; remote argv selects an existing image program. CPU and RAM use request=limit. `max_seconds` is remote hard lifetime; reserve must cover fixed + rate × (max_seconds + stop_seconds). Rate is an explicit maximum all-in USD/sec; fixed includes separately estimated transfer/storage/retention. Do not substitute Functions RAM/CPU rates. Unknown pricing means no approval.

The remote program receives `AI_TOOLS_REQUEST_JSON`: phase, pipeline/context IDs, lineage **with content**, output_dir `/artifacts/<unique-name>`, checkpoint_path from the preceding fit. Total request is bounded to 64 KiB; lineage_content contains original UTF-8 text for exact SHA-256 verification. The remote program must verify all model/data/config/protocol hashes before use. Fit produces checkpoint.bin; evaluation produces evaluation.json under the frozen protocol. Weights/data already exist in the image/Volume; the adapter does not download them. No secrets in argv/request/metrics. The SDK reads credentials in the coordinator environment; none are injected remotely.

Metrics: atomic `metrics.json` in output_dir, `{"sequence":1,"step":10,"values":{"loss":0.2}}`. Sequence strictly increases; identical snapshots are allowed, regressions/NaN/oversized payloads forbidden. For an existing Volume v2 the remote program runs `sync /artifacts` after atomic metrics/checkpoint rename and checks the exit code before completion. The [Sandbox filesystem guide](https://modal.com/docs/guide/sandbox-files) describes background/final commits and explicit sync for v2 only: vendor semantics, so our example requires v2. Credentials are not passed inside; no SDK commit inside Sandbox is assumed. Metrics may be absent until the first snapshot. The coordinator downloads final artifacts as bounded streams into temporary private files and publishes them atomically only after terminal exit=0. Existing verifier commands perform independent hash/protocol checks.

## Spending and stopping

Private SQLite stores intent before create, name, ID, terminal exit, intent time, numeric metrics and up to 10 000 snapshots per attempt. Status shows the latest snapshot and sample count. Polling/recovery update the rate estimate, including queue/startup/errors. On an observed cap/deadline, lost lease, transport failure or `cancel`, the adapter calls terminate and polls. Only a provider terminal exit proves stopping; acknowledgement is insufficient. RPC/waits are bounded; remote timeout backs up a lost coordinator. Neither local-client disconnection nor canceled status alone proves remote termination.

Completed execution with delayed billing is awaiting_billing: keep the full reserve, distinguish estimate/provider report/invoice. Other stages use only the previously allocated remainder of the shared budget. Remote unknown blocks replay and downstream work. [Modal billing](https://modal.com/docs/guide/billing) defines provider semantics; our elapsed estimate is neither an invoice nor an actual billing API result. `ml-reconcile --cost-usd ... --processes-stopped` imports operator-verified cost only with preserved remote terminal proof, retaining the lower estimate and audit. Invoice remains null. Automatic matching of delayed workspace billing is not implemented.

## Crash, recovery and cancellation

`python3 -m orchestrator modal-recover --state PRIVATE --run ID` only looks up/polls by durable name (including terminated objects), never creates and never verifies a task. A lost create response/NotFound stays unknown: failure to find an object does not prove absence of charges. `python3 -m orchestrator cancel --state PRIVATE --run ID` revokes the local lease, then cancels discovered remote jobs even without a live worker. Unavailable Modal leaves terminal proof null; repeat cancel/recover when connectivity returns. No command raises the ceiling or deletes remote artifacts/Volumes.

## Verification and limits

Tests use fake providers/SDKs without credentials, installs, live APIs or paid training. Runtime SDK import is lazy and only for explicit work/cancel/recover; a missing SDK fails before launch. Live SDK compatibility, operational SLA, cost and ML quality require a separately authorized canary; the offline suite proves none. Sandbox lifetime and estimated stopping do not guarantee an invoice ceiling with incorrect rates, provider delays or continuing storage retention.

Remote example packages/machine-learning/experiments/examples/modal_job.py is in the full checkout; the image must include it and Linux sync beforehand; the existing Volume must be v2. Policy example packages/machine-learning/experiments/examples/modal.execution.example.json deliberately contains invalid price/path placeholders: it is not ready launch authorization.
