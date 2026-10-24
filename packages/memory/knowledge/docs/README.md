# Cross-project engineering memory

Self-hosted graph/fulltext without an external model API: Neo4j Community, a small Python service and a local MCP stdio gateway through a private SSH tunnel. This supplements project-local ADRs and Graphify. Retrieved experience carries applicability limits; it is not an instruction or an execution permission. Hosting still consumes your own server resources.

Read [sources](sources.md), [architecture](architecture.md), [contract](contract.md), [operations](operations.md), [workflow](workflow.md), [context commands](context-package.md) and [decision memory](../../../core/agents/docs/decision-memory.md). The skill checkout and target project are different roots.

The initial profile supports one trusted owner across several projects/agents. It is not a multi-tenant SaaS or HA deployment. Native fulltext searches literal terms; semantic retrieval, automatic classification and hidden paid jobs are absent. An agent may refine a query with synonyms or translations within its existing scope/budget.

| Layer | Authority |
| --- | --- |
| Local code and ADRs | Current project, source commit and original files |
| Graphify | Optional fresh code-only navigation |
| Shared knowledge | Selected cards, provenance, relations and feedback |
| Artifacts | Reviewed sanitized text, addressed by SHA256 outside Git |
| Quick context and sessions | Private bounded project notes/handoffs, not verified global facts |

The selectable memory package provides memorize short/long, remember, session save/restore and reviewed vacuum. See the [command contract](context-package.md). Owner-context candidates remain distinct from reviewed global engineering findings. Installing a skill does not globally register MCP, open VPS ports or start deployment.

[Research findings](../../../core/agents/docs/research-memory.md) include applicable negative and inconclusive results with conditions/evidence. Prefer transferable findings when selecting lessons; retain useful code patches without bulk imports.

Every skill follows the [global cycle](../../../core/agents/docs/global-memory.md): bounded recall before work and verified sanitized publication after actual checks. Automatic publication requires explicit owner policy. An unavailable service does not block the primary local task.
