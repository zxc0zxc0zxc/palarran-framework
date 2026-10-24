---
name: palarran-git-conflicts
description: Resolve semantic Git conflicts against an explicit target branch while preserving owned scope, both requirements and exact integration evidence. Use for /palarran:git:conflicts; no automatic MR merge, push or shared-history rewrite.
---

# Resolve an explicit integration

Read [Git contract](../../docs/README.md), [conflict guide](../../docs/conflicts.md), [commit guide](../../docs/commit.md), [sources](../../docs/sources.md), [domain contracts](../../../../core/agents/docs/domain-contracts.md), [feature lifecycle](../../../../core/agents/docs/feature-lifecycle.md), [decision memory](../../../../core/agents/docs/decision-memory.md) and [global memory](../../../../core/agents/docs/global-memory.md). Resolve target AGENTS/spec/contracts, private INDEX/ADRs, locale, stable Feature and actual merge/rebase policy; bounded memory recall is evidence only, unavailable/offline is DEFERRED.

`/palarran:git:conflicts {target-branch}` integrates only the explicit target into the owned feature under existing authorization. `--plan` is offline local inspection/inert planning: no fetch, worktrees, merge/rebase, staging/commit or application checks. Do not invent a target or restart an active feature from a new default branch.

1. Inspect branch/worktree, source SHA, existing operation/owner and unrelated staged/unstaged/untracked work. Preserve it; use already authorized clean isolation rather than stash/reset/clean. Resolve/fetch only the intended remote ref when authorized, or use an explicitly requested local ref. Record target and merge-base SHAs plus actual freshness gaps.
2. Choose project-policy merge/rebase; shared/published history cannot be rewritten merely for convenience. Read unmerged stages and both commits/contracts/decisions, accounting for rebase ours/theirs semantics. Handle rename/delete/binary/submodule/generated/lockfile cases explicitly; no blanket ours/theirs or unapproved regeneration.
3. Record semantic resolution rationale before edits. Preserve both compatible requirements and test their combined behavior; unresolved business ambiguity needs a precise question, not a guessed rule. Continue independent nonconflicting work while that dependency remains open.
4. Inspect exact combined diff, no unmerged index entries and contextual marker checks. Run required regression/contract/integration gates on the combined subject; absent/failed checks stay NOT_RUN/FAIL. Clean markers alone are insufficient. Finish only this known owned local operation with stage traceability, or preserve an explicit partial handoff; do not abort/reset someone else's operation.
5. Update target plan/private `.palarran/git/<task>/` decisions/index/handoff with before/target/base/result SHAs, actual checks and gaps, in `languages.docs`. Preserve foreign changes and separately policy-bound global learning. Do not push/force-push, merge the MR, deploy, publish private rationale or claim permanent conflict freedom after target movement.
