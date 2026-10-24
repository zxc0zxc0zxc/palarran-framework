# Product Factory: first runtime

Runtime turns a specific SDD workflow into a recoverable engineering run. Separate [product research → MVP-plan](../../../product/research/docs/pipeline.md) and [ML](../../../machine-learning/experiments/docs/pipeline.md) pipelines build on it. A long-lived autonomous market-feedback loop remains the next layer; runtime never invents work merely to continue a cycle.

Read in order: [architecture](architecture.md), [contract](contract.md), [operations](operations.md), [sources](sources.md). Implementation decisions belong to the private target journal, which is not distributed.

Python >=3.9, POSIX, Git and local disk. Runtime needs no pip packages, PostgreSQL or cloud. Products live in separate Git repositories. Skills are read from palarran; product decisions live in its `.palarran/`. Runtime state includes workflow snapshots and is private local data, not a Git artifact.

```sh
python3 -m orchestrator --help
python3 -m orchestrator create --workflow packages/core/orchestration/examples/smoke.json --target /path/to/target --state /path/to/private-state
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator status --state /path/to/private-state --run RUN_ID
```

`create` creates an owned detached Git worktree inside state without editing the source checkout. `work` executes trusted commands: an explicit execution boundary. The demo workflow creates a file and checks its actual content. `codex`/`claude` adapters run installed authorized CLIs; [token/cost accounting](usage-accounting.md) stores actual usage receipts and stops AI stages at stage/run caps. New product runs freeze models/allocations under [budget policy](model-budgets.md); generic workflows without it are explicitly unmanaged. Access/limit errors and clarification stop execution rather than bypass permissions.

Check runtime on a disposable target in one run (without LLM/network):

```sh
python3 scripts/factory_acceptance.py
python3 -m unittest discover -s tests -p 'test_factory_*.py' -v
```

The [backend agent template](../examples/backend-agent.json) requires adapting executable/skill/feature paths and verifiers to actual source DoD; it never runs automatically. For Claude change adapter/executable/allowlists; configure login/allowed environment outside Git. Runtime adds explicit handoff: implemented permits independent checks; needs_input pauses the run. Smoke tests never call provider CLI.

## Product research pipeline

ML experiments use a separate [ML pipeline](../../../machine-learning/experiments/docs/pipeline.md): seven planning skills → concrete approval → supervised local/Modal training → independent benchmark. A private resource ledger complements AI usage accounting; the [Modal adapter](../../../machine-learning/experiments/docs/modal-adapter.md) preserves identity, metrics, cancellation proof and billing reserves.

The [product pipeline](../../../product/research/docs/pipeline.md) connects five product skills/final MVP synthesis in existing bounded runtime; engineering workflow API remains compatible.

## Agent evaluations

[Agent eval](../../../validation/agents/docs/eval/README.md) compiles frozen suites into existing runtime workflows with independent final gates, private usage ledger and safe quality/cost/time reports. CLI: `python3 -m orchestrator.agent_eval --help`.
