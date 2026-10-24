# Skills and pipelines

Palarran's engineering overview is in the [root README](../../../../README.md). This guide collects workflow entrypoints without making a command catalog the framework's front page.

## Choose a bounded workflow

| Work | Entry and authoritative guide |
| --- | --- |
| Product | Define, market, compare, revenue and acquisition; [product pipeline](../../../product/research/docs/pipeline.md). |
| Design | UX concepts, then UI from those concepts; [Design](../../../design/README.md). |
| Engineering | Frontend/backend plan, then authorized build with owned worktrees; [Code](../../../code/README.md). |
| ML | Learning goal, data, model, cost, authorized training, diagnostics and independent benchmark; [ML pipeline](../../../machine-learning/experiments/docs/pipeline.md). |
| Delivery | Infrastructure, CI/CD and scoped operations; [Infrastructure](../../../infrastructure/README.md). |
| Acceptance | Business scenarios and independent outcomes; [Validation](../../../validation/README.md). |
| Reporting | Research reports and portable review artifacts; [Science](../../../science/README.md) and [Docs](../../../docs/README.md). |

Research preserves sources, uncertainty and open questions. Product work can end in an MVP plan, a validation experiment, a pivot or a stop. Implementation follows the accepted specification; acceptance checks the exact resulting subject. ML workflows preserve learning goals, data/checkpoint lineage, metrics, generations and independent benchmarks.

## Invoke a skill

See the [complete native command catalog](../../../../skills/README.md) for exact names and arguments. Codex uses names such as `$palarran-backend-plan`; unified Claude commands require the portable plugin. Standalone discovery and namespaced plugin commands are separate interfaces.

Build a self-contained plugin from reviewed public resources:

```sh
python3 scripts/package_plugin.py palarran --output /NEW/palarran-plugin
claude --plugin-dir /NEW/palarran-plugin
```

Individual selectors follow package IDs, such as `palarran-code` and `palarran-machine-learning`. Exports exclude private journals, runtime state and credentials. Installation and updates follow the [versioned runbooks](../../setup/docs/runbooks/README.md).

## Connect stages without losing context

Pass bounded typed artifacts, exact source revisions, relevant decisions, acceptance criteria and remaining work. Do not copy the full conversation. All descendants preserve the same root limits; unknown outcomes require reconciliation before replay. A successful model exit is not verified completion.

![Development and research pipeline](../../../../assets/development-pipeline.png)

```sh
python3 -m orchestrator --help
```

The [bounded runtime](../../orchestration/docs/README.md) tracks dependencies, leases, cumulative usage and recovery. [Managed parallel execution](../../parallelism/docs/contract.md) and [cross-repository features](../../parallelism/docs/features/README.md) provide engineering coordination. Selecting a package or planning a stage does not authorize model calls, training, deployment, outreach or publication.
