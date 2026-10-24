# Git workflow sources

Primary documentation retrieved 2026-10-24. These rolling manuals/provider guides were actually read for this capability; their page modification dates were not captured. Match syntax to the installed Git/host version. Feature IDs, per-stage commits, ownership boundaries and MR Environment/Testing/Production readiness are owner requirements, not universal vendor mandates.

| Source | Relevant basis and limit |
| --- | --- |
| [Git commit manual](https://git-scm.com/docs/git-commit) | Selected-path/--only behavior, message files and hooks. Whole working-tree paths differ from staged-hunk selection; the skill checks ownership rather than assuming --only isolates hunks. |
| [Git log manual](https://git-scm.com/docs/git-log) | Bounded commit/patch history and one-file --follow. Rename detection and shallow history do not establish complete identity or recorded rationale. |
| [Git merge manual](https://git-scm.com/docs/git-merge) | Merge checks, conflicts and abort limitations. No claim that a generic abort restores unrelated pre-existing dirt. |
| [Git interpret-trailers manual](https://git-scm.com/docs/git-interpret-trailers) | Structured commit trailers. The specific Feature/ADR keys and private rationale lookup are our convention. |
| [GitHub CLI conflict guide](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/resolving-a-merge-conflict-using-the-command-line) | Inspect competing line/delete changes and commit their resolution. Examples are not permission to run broad stage/merge/push commands in a dirty target. |
| [GitLab description templates](https://docs.gitlab.com/user/project/description_templates/) | Project/host review layouts. Templates do not establish evidence or authorize publication/notifications. |
| [Git contribution guide](https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project) | Baseline owner guide's coherent-change/message reference. Reused as historical baseline context; not freshly fetched in this capability's source check. |

Actual local Git simulations validate procedure invariants in disposable repositories, not the reliability of an LLM following these skills, live host publication or production readiness. No network push, MR creation or destructive operation on a real checkout is part of the authoring check. Local private decisions and actual version/check evidence remain in the target journal.
