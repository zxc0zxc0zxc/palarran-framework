# Commit one coherent owned stage

`/palarran:git:commit {stage?}` creates a local stage commit when invoked or already authorized by the feature workflow. Read the [shared Git contract](README.md), current project convention and relevant accepted decisions. Do not turn all currently visible changes into one commit. Inspect both index and working tree; identify every owned path/hunk and the concrete purpose of this stage.

## Before committing

Record branch and exact HEAD, in-progress operation, staged/unstaged diff and untracked ownership. Reconcile a pre-existing merge/rebase/cherry-pick with its owner rather than finishing it implicitly. If the branch/index is shared with another active actor, coordinate or use the already authorized owned worktree; a new worktree is not an excuse to transplant unrelated dirt.

Run required checks appropriate to the owned change and its dependency/integration scope. Capture the actual checked revision/diff, commands/tool versions and PASS/FAIL/NOT_RUN. If checks fail, fix within existing implementation scope or leave the stage incomplete. A user-requested or project-supported checkpoint may commit unresolved gates only with an explicit checkpoint description and remaining failures; it is not accepted/production-ready. Do not silently relabel skipped checks as successful.

## Select the actual tree

When all staged changes belong to this stage and relevant working-tree changes have been reviewed, stage explicit paths/hunks and inspect the cached diff before a normal commit. Never use a repository-wide add or `commit -a` as a shortcut.

When unrelated **other files** are staged, a fully owned-path commit can use Git's `--only` path mode after reviewing the **whole current working-tree contents** of those owned paths. As documented in [git-commit](https://git-scm.com/docs/git-commit), this selects named working-tree paths rather than restricting the commit to previously staged hunks. New owned files need their explicit index registration before using this mode. Capture the protected foreign staged diff and unstaged/untracked content identities before and after; ownership includes renames/deletions and both sides of a rename.

If foreign and owned edits share one file, `--only` is unsafe: it includes both even if only the owned hunk was staged. Do not solve this with an index reset, stash or whole-file replacement. Prefer completing the owned patch in an already authorized isolated worktree and coordinate how it will be integrated. A carefully reviewed alternate-index/hunk procedure is possible only when its exact tree, original index preservation and post-commit reconciliation are understood; this skill does not prescribe an unverified generic command for it. Continue independent owned files while the mixed path's ownership is unresolved.

## Message and postconditions

Use a concrete imperative subject following the repo's format, usually within 72 characters. Conventional Commits is optional unless required locally. A short body explains the actual problem, resulting behavior, meaningful validation and material unresolved gates. Do not invent user impact or paste command logs. Read the staged/selected tree so the message describes what will be committed. Feature and relevant ADR trailers bind traceability; avoid invented decisions, hidden reasoning and private paths.

Write multiline text to a private temporary message file and pass it as a file argument. Keep hooks/signing enabled and respect failures; do not amend or disable them automatically. If a hook modifies files or the index, re-inspect ownership and rerun affected checks before retrying; never sweep a hook's unowned side effects into the commit.

Verify the resulting commit exists, parent SHA is the expected pre-commit subject, committed paths/tree match the reviewed stage, trailers/message are correct, and protected foreign staged/unstaged/untracked changes are preserved. A commit command that exits unsuccessfully may still need HEAD/index inspection before retrying. Record the stage commit and remaining checks directly in the source plan when applicable. A later identical invocation should report no owned changes, not create an empty commit. Push and MR publication are separate actions.
