# Task context: read only what this task needs

Start with target instructions, locale, the relevant existing task/index entry and the selected skill. Read only its domain section in [domain contracts](domain-contracts.md), not the full router or unrelated domains. Reuse already read unchanged guides during the same task; follow further references only when a decision depends on them. A link is navigation, not an instruction to recursively load a documentation tree.

## Small review

Use this path for a bounded diff/history/security review (normally <=2commits or <=500changed lines), without implementation, deployment or cross-repository delivery. Risk and dependencies override size: a broad authorization/data-boundary change needs the full relevant method.

1. Read the selected profile's scope/method and applicable source rows. Security reviews follow input → identity/policy → state → side effect → response; LLM applications additionally trace failure/fallback and delivery paths. No network, scanner, paid model or mutation follows from a review request alone.
2. Inspect the actual diff and enough surrounding code to check its lifecycle. A small diff does not justify ignoring a called function or state transition. Record confirmed/suspected findings, counterevidence and missing checks separately.
3. Keep `summary.md` (or the requested draft) and, when the selected profile defines a schema, its structured `report.json` in one private task directory. Put accepted decision IDs, reasons, evidence and limits in the summary before dependent choices. Link the task once in `.palarran/INDEX.md`; multiple skills in that task reuse this record. No separate context/ADR/handoff files are required merely because a skill was called.
4. Apply the [short memory entry](global-memory.md#short-entry). A missing/disabled optional service is a deferred recall, not a reason to install infrastructure or run doctor during a code review.
5. Finish with scope, prioritized findings, checks actually run, unknowns and safe retest steps. Unit/fixture PASS, structural report validation and application acceptance remain different results.

For installation, implementation/SDD, incidents, ML/training, broad architecture and releases, use the complete selected domain workflow and progress/authorization gates. Escalate an initially small task when evidence warrants it; preserve its existing record instead of duplicating it. Private state must be Git-ignored; use the installer/local excludes or an explicitly approved private location, never silently untrack existing files.
