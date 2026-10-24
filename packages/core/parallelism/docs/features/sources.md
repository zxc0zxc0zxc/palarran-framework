# Primary sources and applicability

Reviewed 2026-10-24. These sources justify engineering practices, not claims that a local demo reproduces their production systems.

| Source | Source guidance | Palarran application and limits |
| --- | --- | --- |
| [Google AIP-180: backwards compatibility](https://google.aip.dev/180), created 2019-07-23 | Source, wire and semantic compatibility are distinct; compatible schema changes can still alter expectations. | Pin semantics and producer/consumer checks. A schema validator alone cannot establish a business invariant. |
| [Ian Robinson / Thoughtworks: Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html), 2006-06-12 | Consumer obligations inform service evolution and useful contract validation. | Freeze every affected consumer and owner approval. A generated client or mock is only a limited check. |
| [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/), 2018 | Evaluate a partial, time-limited change against a control and use observed signals to guide rollout. | Explicit version prefixes, stop thresholds and observation windows. A ready plan does not authorize deploy; offline tests do not prove live reliability. |
| [Temporal Python: Workflow message passing](https://docs.temporal.io/develop/python/workflows/message-passing), current documentation | Queries read; Signals and Updates change a durable Workflow under their documented execution semantics. | Keep inherited backend and one existing dispatcher authority. Bus notification and a successful request are not proof that an external action completed. Actual remote Service acceptance requires separate evidence. |
| [Git worktree](https://git-scm.com/docs/git-worktree), current reference | Linked worktrees isolate working directories while sharing Git repository metadata. | Pin each repository base and owned worktree; namespace logical file claims by repository. Worktrees are not process/network sandboxes. |

Passport layout, state machine, pessimistic evidence invalidation, root operation slots, ID format and disclosure bounds are Palarran engineering choices derived from the user specification v0.1. They are not vendor benchmarks. Preserve known spend and unknown liabilities across failures; never invent measured token savings or cross-machine acceptance.
