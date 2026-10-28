# Review sources

Primary pages read2026-10-28. Retrieval dates describe this documentation work, not a new retrieval by every later offline reviewer. Page modification dates were not captured unless stated.

| Source | Applied guidance and limit |
| --- | --- |
| [Google Engineering Practices: what to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Review design, intended behavior, edge/concurrency cases, test usefulness and surrounding context. Avoid speculative overengineering. This is Google guidance, not proof that a particular change is correct. |
| [Git diff manual](https://git-scm.com/docs/git-diff) | Resolve explicit comparison semantics and disable external diff/text conversion when reading untrusted project history. Current manual identifies version2.56.0, updated2026-09-28; match flags to installed Git. |
| [Google Testing Blog: Just Say No to More End-to-End Tests](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Published2015-04-22. Use focused unit/integration checks to localize failures rather than requiring end-to-end infrastructure for every state regression. It does not eliminate the need for independent acceptance of real integrations. |

The compact two-file small-task journal, exact-subject evidence and separate fixture/acceptance statuses are Palarran requirements motivated by the production feedback, not universal vendor mandates.
