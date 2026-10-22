# Runtime context — execution plan

Revision runtime-context-v001, accepted decision 0001. Existing work/old budgets preserved; no implementation subagents/worktrees dispatched. Private disposable measurement worktree создан existing runtime по explicit user comparison scope.

| Task | State | Evidence |
| --- | --- | --- |
| Primary docs/current code/budget inspection | done | runtime-context.md; 0001 |
| Documentation/ADR before implementation | done | docs/product-factory/runtime-context.md |
| Strict task.context + automatic AGENTS/source binding | done | spec, runtime_context, engine, Store tables |
| Scoped Graphify and fallback under original limits | done | dirty snapshot check; 10 focused tests |
| Context receipts + sanitized status | done | hashes/bytes/paths, fenced persistence |
| Measurement bridge: public JSON only, no tools/reasoning | done | app_server fixture tests |
| Two-call shared carry budget, no replay | done | fake pair + semantic snapshot guard |
| Offline regression and lab acceptance | done | 282 tests; targeted follow-up and factory acceptance in handoff |
| Actual matched pair within old budget | done | comparison.json / comparison.md, both verified |
| Repeated/randomized multi-feature quality study | not run | Not authorized; no new spending |

Implemented source is uncommitted workspace revision runtime-context-v001, not a Git release. Remaining operational limitations: graph refresh remains explicit, stale graph falls back; scope quality depends on declared ownership; missing/oversized instructions block or narrow as documented, no invented module layout.
