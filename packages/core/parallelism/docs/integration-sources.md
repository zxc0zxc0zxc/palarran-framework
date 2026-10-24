# Integration queue sources

Reviewed 2026-10-24. Vendor behavior and Palarran choices are distinct.

- [GitHub merge queues](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue): required checks run on the change combined with the target and earlier queued changes. Palarran adopts combined-subject verification locally; it does not create or claim GitHub's hosted merge queue.
- [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick) and [Git worktree](https://git-scm.com/docs/git-worktree): commit application, sequencer state, abort and separate working trees. Palarran serializes mutations in one exclusively owned candidate worktree; no reset of shared branches, automatic push or publication.
- [Google SRE release engineering](https://sre.google/workbook/canarying-releases/): reproducible inputs and automated checks support controlled releases. Local integration checks do not prove deployment health or an operational SLA.
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html): transactional state changes support a private durable queue. A committed mutation intent cannot make an external Git process transactional; interrupted operations remain unknown pending explicit reconciliation.

Semantic compatibility is an explicit project contract, not something Git's textual merge algorithm proves. API shapes, migration ordering and business invariants need independent checks. The queue requires a declared impact matrix and repeats all mandatory gates on the final combined subject. Tests use disposable Git repositories and frozen external gate scripts without paid models or deployed infrastructure.
