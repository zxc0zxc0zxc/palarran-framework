# Where documentation and recall belong

| Material | Canonical location | Recall |
| --- | --- | --- |
| Current architecture, feature behavior and API schema | Project docs/spec files in Git | Read the index, then bounded relevant originals |
| Active task summary and useful pointers | Private .palarran/memory quick context | Small local shortlist, verify freshness |
| Plan, rationale, progress and session handoff | Private .palarran task journal | Stable feature/ADR IDs and exact source references |
| Verified portable findings and research results | Reviewed VPS graph memory | Bounded fulltext/cards, selected neighbors and original evidence |
| Owner notes / unfinished session snapshots | Separate VPS owner-context candidates | Explicit remember/session recall, never treat as verified global knowledge |
| Code relationships | Optional local code-only Graphify index | Freshness check → bounded query → original files |

Keep one canonical document rather than dumping every revision into long-term memory. A remote lesson stores a compact transferable conclusion and commit/feature/ADR/source references; private snapshots retain only what the user explicitly asked to preserve. Do not upload raw docs, credentials, personal data or an entire session by default.

Graphify is useful for code navigation; the current integration is deliberately code-only. Do not promise automatic semantic indexing of documentation or enable a model-powered extraction pass without its own scope/budget. A curated docs index, links, file search and Git history provide cheap reliable first retrieval. FTS finds literal terms, not guaranteed cross-language meaning.

Recalled pointers must be checked against the current commit and document status. Archived or contradicted findings remain traceable but do not override current code/contracts. Vacuum keeps canonical docs, plan/results, evidence and active handoffs; only reviewed disposable drafts are cleanup candidates.
