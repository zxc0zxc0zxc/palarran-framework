# Workflow admission and domain pipelines

[Package instructions](../../AGENTS.md) · [Runtime contract](../../orchestration/docs/contract.md)

The [workflow specification parser](../runtime/spec.py) validates the shared execution shape before admission. Orchestration owns durable state and dispatch; domains own their stage semantics and evidence gates.

- [Product pipeline](../../../product/research/docs/pipeline.md): idea, market, alternatives, economics and acquisition to a justified MVP plan.
- [ML pipeline](../../../machine-learning/experiments/docs/pipeline.md): hypotheses, data/model/cost choices, supervised training and independent benchmark.
- [Execution progress](../../agents/docs/execution-progress.md): engineering plan revisions, owned tasks and independent DoD gates.

Shared admission does not authorize model calls, training or deployment. Keep domain-specific code in its package, preserve budgets across restarts and reject unknown outcomes without blind replay. Run the complete offline suite and factory acceptance after parser or stage-contract changes.
