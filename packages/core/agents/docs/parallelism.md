# Parallel work is the default when tasks are independent

Palarran's core principles are modularity, parallelism, autonomy and quality. Use concurrent agents and batched independent reads where they improve progress. A difficult task is not a reason to run every step serially; a dependency or shared mutation is.

Before dispatch, identify the dependency DAG, bounded inputs, files/resources owned by each worker, source/spec revision, expected artifacts and acceptance gates. Parallel implementation uses isolated owned Git worktrees; research/translation workers also need clear non-overlapping outputs. One coordinator owns shared plan/index/progress, sequential integration and final checks. Workers report actual commits/files/checks and unresolved questions. Never assume completion from an agent exit.

Keep dependent edits, approval decisions, irreversible mutations and shared-file integration sequential. Batch independent searches/reads rather than emitting unnecessary tool rounds. Do not create agents merely to fill slots or ask for permission already supplied by the active scope. Preserve model/provider budgets across every worker, failure and continuation. More parallel calls do not create a larger budget.

Autonomy means carrying out already-authorized work and routine implementation decisions without repeated confirmation. It does not imply paid calls, deployment, outreach, new credentials or replay of unknown operations. When a worker is blocked, continue independent ready tasks; retain the blocked dependency and evidence rather than silently skipping it.

Quality gates bind the final integrated source, not isolated worker claims. Run focused checks per stage and integrated regression/DoD checks afterward. Missing checks remain NOT_RUN. Measure elapsed time, usage and quality on comparable tasks before claiming a parallelism speedup or token saving. Use source-grounded handoffs to keep worker context small without dropping constraints.

## Developers on different machines

Native subagent messaging coordinates one host/session. For optional cross-machine collaboration, use the installed Core coordination capability with distinct participant credentials, a shared project alias and task/incident room. Read the actual versioned coordination contract; discover tools rather than inventing callable routes. Keep secrets in private env profiles, never task packets. Check bounded message pages at assignment/result boundaries and when shared facts change. Receipt ACK and explicit assignment acceptance are different.

Claims are project-wide per canonical environment/target/resource across rooms. The service coordinates complying participants; an external editor/deployer that ignores claims is not fenced. A stale receipt cannot authorize a new action. On expiry/disconnection, stop overlapping mutations and reconcile actual state before transfer. With no shared service, agree one integration/mutation operator and preserve an explicit handoff; do not pretend different developer sessions share locks. The bounded orchestrator does not automatically dispatch remote peers or register this optional MCP server.

## Automatic dispatcher and optional Temporal

The [v001 parallel dispatcher](../../parallelism/docs/contract.md) evaluates ordinary requests and skill stages through the same admission interface. Check ready work again after a completion, block or newly discovered independent task. Continue an active run rather than spawning a fresh budget for each user message. Use a small first wave, then increase assignments only with useful independent work, observed capacity and remaining budget. Record scheduling rationale; a heuristic is not an optimum guarantee.

A configured backend is bound at run creation. Native Codex/Claude conversations remain instruction-based; only an explicitly managed entrypoint controls its registered execution lifecycle. AGENTS alone never establishes enforced interception. If Temporal is selected but unavailable, report waiting/unavailable and reconcile its workflow ID; do not silently launch locally. Installation asks whether to enable Temporal and shows real compatibility/integration status. Workers and harness credentials stay on approved developer machines.
