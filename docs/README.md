# Documentation index

For a complete Palarran checkout: [root README](../README.md) → [AGENTS](../AGENTS.md) → target private decision index → [domain contracts](skills/domain-contracts.md) → the relevant profile. Commands are indexed by [package](../skills/README.md). This map helps navigation; the domain guides hold canonical requirements.

## Shared workflows

| Task | Read |
| --- | --- |
| Install or update skills | [Setup](setup/skill.md), [ownership/update](setup/README.md), [packages and languages](setup/configuration.md) |
| Change this library | [Shared contracts](skills/README.md), affected module AGENTS |
| Understand or record decisions | [Decision memory](skills/decision-memory.md), target accepted ADR index |
| Write AGENTS.md | [Authoring guide](skills/agents-authoring.md) |
| Reuse research findings | [Research memory](skills/research-memory.md), [global cycle](skills/global-memory.md) |
| Retrieve current web/documentation sources | [Context retrieval](skills/context-retrieval.md) |
| Navigate code and dependencies | [Graph context](skills/graph-context.md), [runtime context](product-factory/runtime-context.md), then original files |
| Track implementation | [Execution progress](skills/execution-progress.md), relevant SDD guides |

## Engineering profiles

| Area | Entry | Next guides |
| --- | --- | --- |
| Infrastructure | [Planning](infra/plan/README.md) | [Low](infra/plan/low.md), [medium](infra/plan/med.md), [high](infra/plan/high.md), [security/network](infra/plan/security-network.md), [IaC](infra/plan/delivery-iac.md), [sources](infra/plan/sources.md) |
| CI/CD | [Pipelines](ci-cd/README.md) | [GitHub](ci-cd/github.md), [GitLab](ci-cd/gitlab.md), [stacks](ci-cd/stacks), [performance](ci-cd/performance.md), [evidence](ci-cd/evidence.md) |
| UX | [UX design](ux/README.md) | [Research](ux/research.md), [analysis](ux/analysis.md), [diagrams](ux/diagrams.md), [responsive behavior](ux/responsive.md), [review](ux/review.md) |
| UI | [UI design](ui/README.md) | [Design systems](ui/design-codes.md), [references](ui/references.md), [UX binding](ui/ux-binding.md), [responsive behavior](ui/responsive.md), [visual output](ui/visual-output.md) |
| Frontend planning | [SDD planning](frontend/plan/README.md) | [Context](frontend/plan/source-context.md), [API contracts](frontend/plan/api-contracts.md), [edge cases](frontend/plan/edge-cases.md), [workflow](frontend/plan/workflow.md) |
| Frontend implementation | [Build](frontend/README.md) | [Frontend guides](frontend), [progress](skills/execution-progress.md), actual browser evidence |
| Backend planning | [Architecture/SDD](backend/plan/README.md) | [Planning guides](backend/plan), stack, modules, data, caching, SLO and contracts |
| Backend implementation | [Build](backend/build/README.md) | [Worktrees](backend/build/worktrees.md), [build guides](backend/build), edge/invariant tests and exact subject evidence |

## Product, ML and scientific reporting

| Area | Entry | Next guides |
| --- | --- | --- |
| Product | [Research](product/README.md) | [Cases](product/cases/README.md), [sources](product/data-sources.md), [pipeline](product/pipeline.md); MVP planning is separate from application build |
| ML | [Experiment workflow](ml/README.md) | [Contracts](ml/contracts.md), [plan](ml/plan.md), [sources](ml/sources.md), [model](ml/model.md), [training](ml/train.md), [benchmark](ml/benchmark.md) |
| ML data | [Preparation](ml/data/README.md) | [Mixtures](ml/data/mixtures.md), [answer integrity](ml/data/answer-integrity.md), [runtime gate](ml/data/pipeline.md) |
| Training diagnostics | [Debugging](ml/debugging/README.md) | Task-specific metrics, heuristics, fixed generations and terminal reports |
| Scientific reporting | [Preprints](science/README.md) | Evidence-backed LaTeX reports; publication is separate |

## Runtime and operations

| Area | Read |
| --- | --- |
| Bounded orchestrator | [Runtime](product-factory/README.md), [architecture](product-factory/architecture.md), [contract](product-factory/contract.md), [operations](product-factory/operations.md) |
| Model routing and spend | [Model budgets](product-factory/model-budgets.md), [usage accounting](product-factory/usage-accounting.md); unknown usage is not zero |
| Agent context | [Runtime context](product-factory/runtime-context.md): scoped AGENTS, optional graph and source fallback |
| ML execution | [Pipeline](ml/pipeline.md), [artifacts/approval](ml/pipeline-contract.md), [Modal adapter](ml/modal-adapter.md) |
| Agent evaluation | [Eval harness](agent/eval/README.md): independent quality, tokens, cost and elapsed time |
| Application acceptance | [Browser/API/DB verification](app/verify/README.md): frozen scenarios and exact evidence |
| Agent improvement | [Regression-driven improvement](agent/improve/README.md) |
| MCP tools | [Tool design and evaluation](mcp/build/README.md) |
| Cross-project memory and VPS | [Graph/fulltext operations](memory/README.md), [context package](memory/context-package.md) |
| Project and app installation | [Project setup](setup/README.md), [VPS stack workflow](setup/vps-stack.md) |

## Incident coordination

[Infrastructure incident response](infra/incident/README.md) covers parallel investigation, scoped recovery and multi-developer handoff. [Cross-machine coordination](../packages/core/coordination/docs/README.md) is an optional Core capability, separate from long-term Memory.

## Reading order and evidence

Choose scope and mandatory guides, then inspect linked primary sources with dates/versions and assess target applicability. [Templates](../templates) are starting points; [examples](../examples) are not execution permission. Proposed diagrams are not observed topology, and fixtures are not live verification. Resolve profile links within the actual target/installed package rather than an unrelated neighboring checkout.

Domain-only plugins include their selected guide dependency closure, rather than this whole repository index. Their portable shared entry is [docs/skills/README.md](skills/README.md).
