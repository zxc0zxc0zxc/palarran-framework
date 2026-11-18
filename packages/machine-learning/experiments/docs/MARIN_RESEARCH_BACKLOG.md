# Marin research backlog

Reviewed 2026-11-18; upstream revision is pinned in the [audit](MARIN_ADOPTION_AUDIT.md). Nothing below is implemented or authorized by this document. Cost descriptions are planning estimates, not provider quotes.

| Priority | Research | Prerequisites and expected value | Evaluation and acceptance | Resource needs |
| --- | --- | --- | --- | --- |
| P0 follow-up | Typed full experiment manifest | Existing stage bodies are opaque; agree target-specific model/data/config/runtime/parent fields | Validate metadata against exact pinned stage refs; replay one CPU experiment and reject mismatched parent/config | Stdlib schemas and target adapters; no external tracker |
| P0 follow-up | Mutable upstream revocation/opt-out reconciliation | Authorized source adapters and retention rules; current registry is a reviewed snapshot | Simulate changed license/withdrawal; block new usage and preserve past lineage; explicit deletion policy | Bounded CPU and metadata; no automatic remote ingestion |
| P1 | Substring/n-gram/near-duplicate benchmark audit | Task-specific normalization and labeled overlap/false-positive examples | Fixed exact baseline; measure precision/recall by code/math/tool/prose and preserve near misses | CPU prototype first; scale cost unknown |
| P1 | Independent topic and quality annotations | Domain rubric, scorer revision, manual calibration set | Store scores/labels separately; compare policy on dev, no test-driven thresholds | Human labeling; no default classifier/model API |
| P1 | Rich per-example evaluation and uncertainty | Frozen task IDs and raw result schema | Match baseline/candidate examples; classify all failures; paired uncertainty where justified | Existing local evaluators; paid judges separately authorized |
| P1 | Exact checkpoint resume | Real target trainer exposing optimizer/scheduler/scaler/RNG/sampler state | Interrupted versus continuous run at fixed seed; report approximate resume explicitly | Tiny CPU trainer first, GPU only with budget |
| P2 | Proxy-model mixture optimization and scaling ladder | Repeatable measured training/evaluation, adequate signal and affordable proxy | Change one factor at matched exposure; validate promising outcome at a second scale; retain negatives | Multiple bounded training runs; compute quote required |
| P2 | Muon/Hyperball, routing and MoE balancing | Concrete supported model/workload plus correctness reference | Quality/stability and time-to-quality comparison, not throughput alone | Accelerator pilot, exact dependency/hardware pins |
| P2 | Expert parallelism/FSDP/communication overlap | Proven memory or communication bottleneck and multi-device backend | Profile end-to-end useful tokens/sec, memory and equality/quality guardrails | Multi-device/network capacity; separate scope |

Iris/JAX stack replacement and unconditional Parquet conversion are rejected for this task: they do not solve a demonstrated Palarran problem. No Marin hardware performance result is an expected Palarran speedup.
