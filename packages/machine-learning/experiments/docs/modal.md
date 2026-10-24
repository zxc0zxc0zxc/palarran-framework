# Modal: resources, launch and recovery

This guide covers Modal Functions training jobs; the runtime Sandbox backend has a separate [contract](modal-adapter.md). Do not treat Modal Training/Dojo, Sandbox and other products as interchangeable: check API maturity, prices and permissions separately. Reading documentation does not connect services, create accounts or install SDKs.

## Pricing reference

Checked 2026-10-20 against the [official page](https://modal.com/pricing); these are selected reference figures, not permanent prices or a promise of GPU availability. USD per GPU-second: T4 `0.000164`, L4 `0.000222`, A10 `0.000306`, A100 80 GB `0.000694`, H100 SXM5 `0.001097`. Functions CPU: `0.0000131` per physical core-second; RAM: `0.00000222` per GiB-second. Sandbox CPU/RAM use different rates on the page. Recheck all values before launch; the [resources guide](https://modal.com/docs/guide/resources) explains billed CPU/RAM/ephemeral disk.

Count storage and egress separately using current inclusion/plan terms; never assume free. [Volumes](https://modal.com/docs/guide/volumes) describes snapshot-based storage billing and charges that may continue after deletion; retention does not end with GPU completion.

## Reviewable launch packet

Before a paid action prepare exact plan/config hashes, source/image/lockfile, model/data/license refs, region/privacy/storage, GPU type/count, CPU/RAM/disk requests+limits, concurrency, wall/step/token caps, exception retry/preemption policy, total reserve, existing secret **names**, outputs, checkpoint and stop/reconciliation commands. Examples such as `app.function(gpu=..., timeout=..., retries=...)` are not themselves training pipelines. Check SDK versions/API signatures against current official references; do not make a trial call to discover the correct API.

First check prepared code/config locally within execution scope, a tiny train-only smoke test, checkpoint loading/saving and data visibility. GPU smoke/pilot runs are paid attempts requiring budget too. Volume creation, image builds, account authentication, upload, deployment/invocation are external actions; explicit plan-only mode performs none. Inspect existing resources read-only only in authorized execution scope; `from_name(..., create_if_missing=True)` may create storage and is unsuitable for read-only inventory.

## Timeouts and retries

[Modal timeouts](https://modal.com/docs/guide/timeouts) apply to individual execution attempts, not an entire logical job; startup is separate. [Retries](https://modal.com/docs/guide/retries) add attempts. Our recommendation: do not enable exception retries without allocated limits/reserves and a resume protocol. For OOM first analyze memory/sequence/batch; no automatic GPU escalation. Connection loss does not prove compute stopped.

Documentation says [preemption](https://modal.com/docs/guide/preemption) can restart the same input. One client invocation therefore does not guarantee one billable execution. A stable logical run ID + per-start attempt ID, durable attempt/restart counter, shared deadline and reserve belong in the process/storage, not only a live client. If the SDK lacks sufficient information/control, record the enforcement gap and do not promise strictly bounded spending.

## Checkpoints and stopping

Use immutable step-specific checkpoint paths; close files, check manifest/hash and explicit durability (`Volume.commit()` for the Volume semantics in use). The [Volumes guide](https://modal.com/docs/guide/volumes) explains commit/reload; a local file's existence does not prove persistence. Prevent multiple writers to one checkpoint; an interrupted write must not publish a completed manifest. A graceful signal handler is supplemental; periodic checkpoints are necessary when it cannot finish.

Abort must stop the specific job and verify its terminal provider outcome; stopping polling, closing a terminal or canceling a local subprocess may not cancel remote compute. Save cancellation acknowledgement/terminal timestamp, last durable checkpoint, estimate and unknown usage. Without confirmation: unknown, retain reserve, prohibit retry until reconciliation. Do not delete volumes/checkpoints or deploy a model as cleanup without separate scope.
