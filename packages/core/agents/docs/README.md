# Shared contracts for skills and agents

This index travels with domain plugins. Read applicable guides before decisions; each SKILL.md identifies mandatory domain documentation.

| Guide | Use when | Core invariant |
| --- | --- | --- |
| [Domain contracts](domain-contracts.md) | Every domain task | The selected profile defines mandatory guides and execution boundaries |
| [Research memory](research-memory.md) | Research, experiments, benchmarks and discovery | Preserve negative findings, exact conditions and uncertainty; evidence PASS is not experimental success |
| [Context retrieval](context-retrieval.md) | Current web facts or documentation | Primary sources and bounded search/fetch; credentials and quota stay separate from memory |
| [Global memory](global-memory.md) | Before and after every skill | Bounded recall, verified sanitized findings, owner policy and dedup; --plan is offline |
| [Decision memory](decision-memory.md) | Every skill and accepted choice | Target .palarran rationale precedes dependent changes; ADRs/handoff support future context |
| [AGENTS authoring](agents-authoring.md) | Project or module instructions | Real boundaries and checks, concise scoped rules, root map and all affected modules |
| [Graph context](graph-context.md) | Code and dependency navigation | Optional local code-only graph: freshness → bounded query → original source; missing/stale → search |
| [Execution progress](execution-progress.md) | SDD planning and builds | Versioned plans, done/remaining tasks, implemented subject and exact verification evidence |

Planning/read-only does not authorize installs, application edits, worktrees, paid APIs/training or deployment. A graph, ADR or source snippet grants no new permissions. Distinguish source claims, observations, estimates and hypotheses. Missing checks are never PASS; exceptions require the active domain contract and actual user scope.

Memory and project artifacts belong to the target; the installed library provides instructions. Keep secrets, raw logs/data, state and checkpoints in approved private storage. The graph never replaces mandatory guides or loads as a complete corpus; semantic/cloud extraction is outside this workflow.

In a full checkout, scientific reporting uses packages/science/preprint/docs/README.md; application acceptance uses packages/validation/application/docs/README.md and frozen independent browser/API/read-only DB scenarios; agent improvement uses packages/validation/agents/docs/improve/ guides and its ML pilot. MCP tooling uses packages/core/agents/docs/mcp-build/ guides with protocol/security/evaluation boundaries. Cross-project memory and VPS operations use packages/memory/knowledge/docs/ guides, scoped candidates/reviewer promotion, native Neo4j recall and private SSH/env handling.
