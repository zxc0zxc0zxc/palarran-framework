---
name: palarran-git-commit
description: Commit one coherent owned stage with required checks, preserved unrelated dirt and Feature/ADR traceability. Use for /palarran:git:commit; no automatic push, amend or history rewrite.
---

# Commit an owned stage

Read [Git contract](../../docs/README.md), [commit guide](../../docs/commit.md), [sources](../../docs/sources.md), [domain contracts](../../../../core/agents/docs/domain-contracts.md), [feature lifecycle](../../../../core/agents/docs/feature-lifecycle.md), [decision memory](../../../../core/agents/docs/decision-memory.md) and [global memory](../../../../core/agents/docs/global-memory.md). Resolve target AGENTS, locale/conventions, private INDEX/ADRs and stable Feature ID. Apply bounded memory recall; unavailable/offline is DEFERRED, not authority to change scope.

`/palarran:git:commit {stage?}` commits the actual coherent owned stage; a standing feature-build stage policy already grants that local scope. `--plan` only inspects locally and writes inert private planning artifacts: no stage/commit/branch/worktree, hooks/app checks or remote calls. Do not re-ask permission already granted.

1. Inspect worktree/branch/HEAD, in-progress Git operations and staged/unstaged/untracked ownership. Pin the stage diff and protect foreign changes. Mixed ownership in one path blocks whole-path committing; do not hide it with stash/reset or a broad add. Use existing authorized isolation for that patch.
2. Run required stage checks; retain exact subject and PASS/FAIL/NOT_RUN. Record accepted choices before dependent changes. A permitted checkpoint states failed/missing gates explicitly and remains unverified. End coherent implementation stages with reviewable commits, not empty read checkpoints.
3. Inspect the exact selected tree. Use explicit staging when the index is fully owned; fully owned paths may use the guide's --only procedure while preserving unrelated other-file staging. --only includes whole working-tree files, not just staged hunks. Keep hooks/signing and user identity/config; re-inspect after hook changes/failures.
4. Write a concrete repo-convention subject/body with actual problem/result/checks, Feature and relevant real ADR trailers. Use a private message file/structured arguments. Verify new commit/parent/tree/trailers and foreign staged/unstaged/untracked preservation before declaring completion; reconcile HEAD after uncertain command exit before retrying.
5. Update source-plan stage progress and target `.palarran/git/<task>/` decisions/index/handoff with commit and remaining checks. Prose follows `languages.docs`; public commit text follows project conventions. Global learning is separately privacy/evidence-policy bound. Do not push, amend, sweep unrelated files, publish journals/secrets or create an MR automatically.
