# Palarran instructions

Library of skills, documentation and adapters with a bounded Python orchestrator. Canonical public code, identifiers, guides and skill instructions use English. Preserve existing uncommitted work. Project locale preferences control interaction and newly generated artifacts; see .palarran/config.json and global ~/.palarran/config.json.

## Navigation

- [README agent entry](README.md#agent-entry), [documentation index](docs/README.md), [skill catalog](skills/README.md), [shared contracts](packages/core/agents/docs/README.md).
- Graphify navigation: [freshness → bounded query → original source](packages/core/agents/docs/graph-context.md). A diagram or graph never authorizes execution.

## Before a task

- Read `.palarran/INDEX.md`, relevant accepted ADRs and current code to verify assumptions. Record decisions before dependent changes using [decision memory](packages/core/agents/docs/decision-memory.md); update index/handoff and preserve superseded history. In older targets also inspect the legacy .ai-development index.
- Read AGENTS for every affected module in the table below, even when starting from the repository root. Root-to-CWD discovery does not load sibling modules automatically.
- For every domain task or skill, read the relevant [domain contract](packages/core/agents/docs/domain-contracts.md) and its mandatory guides. This applies outside packages/core/agents/docs too.
- Write new AGENTS using the [authoring guide](packages/core/agents/docs/agents-authoring.md): real boundaries/commands, concise testable invariants, no root duplication.

## Core principles

Modularity, parallelism, autonomy and quality guide every task. Prefer concurrent execution for genuinely independent work. Before dispatch, record a bounded task DAG, file/resource ownership and acceptance gates; use owned Git worktrees for parallel implementation and keep shared plan/index/integration under one coordinator. Do not parallelize dependent mutations, approvals or overlapping files. Continue authorized work autonomously without repeated confirmation, preserving budget/scope and unknown-outcome reconciliation. Parallelism must improve elapsed time without weakening independent verification; do not invent worker results or quality evidence.

## Shared invariants

- Documentation and dated primary sources precede implementation. Distinguish vendor claims, observations, estimates and hypotheses.
- Planning/read-only does not authorize application edits, installs, worktrees, cloud/SSH/DB/API execution, training or deployment. Exceptions require the applicable domain contract and actual user scope.
- Keep secrets, credentials, raw logs, customer data, state and checkpoints out of Git. `.delivery/` owns current configuration; target `.palarran/` owns rationale and results. The skill checkout and target are different roots.
- No implied authorization for paid APIs/training, outreach, publication, ad spending or deployment. Preserve cumulative budgets across failures/restarts. Reconcile unknown outcomes before retrying; never increase a budget automatically. Separate estimates, provider usage and invoices.
- Handoff, exit and build are not verification. Independent checks and exact subjects/evidence are mandatory. Missing checks mean partial/NOT_RUN, never PASS. Local tests do not establish an operational SLA or market validation.
- Graphify is optional local code-only navigation under the [graph contract](packages/core/agents/docs/graph-context.md). Query a bounded fresh subset, then original files/AGENTS/ADRs. Use scoped search when missing/stale; never load the whole graph or enable semantic/cloud extraction without separate scope and budget.

## Package ownership

Read [the package map](packages/README.md) and `packages/<package>/AGENTS.md` for every affected package. Domain implementation, skills, docs and templates live in its capability; root module directories are compatibility entrypoints or shared tests.

## Modules and checks

| Directory | Context |
| --- | --- |
| memory | [Cross-project graph memory](packages/memory/knowledge/runtime/AGENTS.md) |
| mcp | [Read-only stdio reference profiles](mcp/AGENTS.md) |
| orchestrator | [Runtime, leases, accounting and providers](packages/core/orchestration/runtime/AGENTS.md) |
| scripts | [CLI, inventory, validators and packaging](scripts/AGENTS.md) |
| tests | [Offline contracts and fixtures](tests/AGENTS.md) |
| skills | [Skill authoring and mandatory guides](skills/AGENTS.md) |
| docs | [Sources and domain contracts](packages/core/agents/docs/AGENTS.md) |
| templates | [Inert examples and target memory](templates/AGENTS.md) |
| plugins | [Portable namespaces](plugins/AGENTS.md) |
| examples | [Local and remote examples](examples/AGENTS.md) |

After code, skill or inventory changes run `python3 scripts/validate_repo.py` and `python3 -m unittest discover -s tests -v`. After runtime changes also run `python3 scripts/factory_acceptance.py`. Never test through live infrastructure apply or paid ML launches. Detailed domain checks remain in domain-contracts.
