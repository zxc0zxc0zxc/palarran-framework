# Parallel agents in actual worktrees

Read planned DAG/touch sets/contract ownership/resource budgets in the [SDD plan](../plan/sdd-agents.md). During builds run independent ready lanes in parallel when host delegation exists. User requests for `/palarran:backend:build` with this workflow authorize parallel subtasks; no repeated permission per agent. Host/system policy takes precedence. Use internal subagents rather than separate user chats.

## Preparation and dispatch

1. Inspect existing worktrees/attachments and reuse suitable owned clean checkouts. With managed worktree APIs use their lifecycle/attach/archive; otherwise standard Git. Set the frozen base/ref explicitly: tools may default to the remote default branch. Verify path/HEAD/branch after creation and wait for pending setup before dispatch.
2. Each writing lane receives a separate checkout/branch from baseline with its dependencies/contracts. Parent dirty/untracked edits are not copied automatically. Never force-checkout the same branch; integration checkouts also have one owner.
3. Contract/schema/migration/lockfile/shared-index changes have one owner and serial gates. Integrate ready contracts before dependent lanes or pass agreed immutable versions; multiple agents must not edit generated files concurrently.
4. [Packet](../../templates/execution-agent.md): absolute workspace path and required CWD for **every** command; source revisions/IDs, allowed/forbidden files, dependencies, deliverables, tests/DoD, namespaces/ports/resource limits, progress reporting and no external mutations beyond scope. Spawning does not itself change CWD: many agent tools share a filesystem.
5. Launch ready tasks only within max agents/CPU/RAM/DB/CI budgets; independent lane commits/checks stay on their branches. Never give every agent the repository root as a shared writable workspace. Agents do not edit canonical progress/spec/index concurrently; return commit hashes, actual checks/evidence and deviations/blockers.

[Git worktree](https://git-scm.com/docs/git-worktree) separates working trees but shares repository/some metadata. Each runtime task needs separate ports, temp/artifacts, DB/schema/test tenant, queue/cache namespaces and sandbox credential refs; total resource pools remain bounded. Worktrees are not container/network/DB sandboxes. If isolation is impossible, work safely in series and record why; never fake parallelism or direct destructive tests at shared databases.

## Integration

The coordinator checks task diffs/commit ownership/actual outcomes, then integrates by DAG/project policy in one integration checkout. [Cherry-pick](https://git-scm.com/docs/git-cherry-pick) is a possible transfer mechanism, not a required replacement for merge policy. Do not pull unrelated commits. Resolve conflicts deliberately with owners and rerun affected checks; lane checks do not verify integrated code.

After every integration update progress commit/state and invalidate affected checks; after each group run full required integrated suites/API+DB/cross-module checks and feature gates. A ready task verified on its revision may become invalid after dependency changes. Dispatch each new ready wave from the correct base, never a stale contract.

With unavailable agents/delegation tools do not claim parallel agent completion. Execute available independent work serially and record the limitation; an explicit parallel-execution requirement remains unmet. Explain max=1 for small source DAGs rather than creating agent-count overhead.

Worktree cleanup: inspect commits/dirty/untracked/needed ignored artifacts, preserve/integrate evidence and code; managed archive uses host APIs, plain worktree removal is only for owned clean checkouts. Never force-remove others' or uncommitted work, or delete branches with unintegrated commits. No automatic reset --hard/clean --force to resolve conflicts.
