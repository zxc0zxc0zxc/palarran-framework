# Skills and pipelines

Palarran's engineering overview is in the [root README](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/README.md). This guide collects workflow entrypoints without making a command catalog the framework's front page. Catalog links point to the full source repository; installed packages carry their selected mandatory domain guides locally.

## Choose a bounded workflow

| Work | Entry and authoritative guide |
| --- | --- |
| Product | Define, market, compare, revenue and acquisition; [product pipeline](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/product/research/docs/pipeline.md). |
| Design | UX concepts, then UI from those concepts; [Design](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/design/README.md). |
| Engineering | Frontend/backend plan, then authorized build with owned worktrees; [Code](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/code/README.md). |
| ML | Learning goal, data, model, cost, authorized training, diagnostics and independent benchmark; [ML pipeline](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/machine-learning/experiments/docs/pipeline.md). |
| Delivery | Infrastructure, CI/CD and scoped operations; [Infrastructure](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/infrastructure/README.md). |
| Acceptance | Business scenarios and independent outcomes; [Validation](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/validation/README.md). |
| Reporting | Research reports and portable review artifacts; [Science](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/science/README.md) and [Docs](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/docs/README.md). |

Research preserves sources, uncertainty and open questions. Product work can end in an MVP plan, a validation experiment, a pivot or a stop. Implementation follows the accepted specification; acceptance checks the exact resulting subject. ML workflows preserve learning goals, data/checkpoint lineage, metrics, generations and independent benchmarks.

## Invoke a skill

See the [complete native command catalog](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/skills/README.md) for exact names and arguments. Codex uses names such as `$palarran-backend-plan`; unified Claude commands require the portable plugin. Standalone discovery and namespaced plugin commands are separate interfaces.

Build a self-contained plugin from reviewed public resources:

```sh
python3 scripts/package_plugin.py palarran --output /NEW/palarran-plugin
claude --plugin-dir /NEW/palarran-plugin
```

Individual selectors follow package IDs, such as `palarran-code` and `palarran-machine-learning`. Exports exclude private journals, runtime state and credentials. Installation and updates follow the [versioned runbooks](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/core/setup/docs/runbooks/README.md).

## Connect stages without losing context

Pass bounded typed artifacts, exact source revisions, relevant decisions, acceptance criteria and remaining work. Do not copy the full conversation. All descendants preserve the same root limits; unknown outcomes require reconciliation before replay. A successful model exit is not verified completion.

[Development and research pipeline diagram](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/assets/development-pipeline.png)

```sh
python3 -m orchestrator --help
```

The [bounded runtime](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/core/orchestration/docs/README.md) tracks dependencies, leases, cumulative usage and recovery. [Managed parallel execution](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/core/parallelism/docs/contract.md) and [cross-repository features](https://github.com/zxc0zxc0zxc/palarran-framework/blob/main/packages/core/parallelism/docs/features/README.md) provide engineering coordination. Selecting a package or planning a stage does not authorize model calls, training, deployment, outreach or publication.
