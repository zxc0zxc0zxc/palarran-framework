---
name: palarran-code-review
description: Review an existing diff or release for correctness, state lifecycle and test gaps. Use for /palarran:code:review {range}; no automatic fixes or publication.
---

# Review an existing change

Start with [task context](../../../../core/agents/docs/task-context.md) and the [review workflow](../../docs/README.md). Read only relevant target instructions and source guidance; ordinary small reviews do not require the full planning/build contracts. Apply [Code review domain rules](../../../../core/agents/docs/domain-contracts.md#code-review).

`/palarran:code:review {range?}` binds exact base/head commits and diff semantics; with no range, use the clearly identified current change or ask when ambiguous. Preserve dirty work and label it separately. `--plan` returns scope/check suggestions from visible context only: no file reads, writes, Git/tool execution or network.

Inspect changed code and the necessary callers, state owners and tests. Follow input → state → side effect → acknowledgement, including errors, retries, duplicates, concurrency and shutdown where relevant. Findings need concrete location, trigger, impact, counterevidence and safe retest; distinguish source-supported defects, executed reproductions and suspected hypotheses. Avoid style noise and unrelated cleanup. No findings is not proof of correctness.

Use existing project tests only under already authorized commands/fixture scope. A fake-provider PASS does not prove live integration; mark missing checks NOT_RUN. The project-tests adapter is optional and accepts only explicitly reviewed local bindings. No auto repair, dependency install, model call, exploit, commit, MR or deploy.

For a small review, save `summary.md` and `report.json` under target `.palarran/code-review/<task>/`: exact subject/scope, prioritized findings, actual tests/gaps, an MR-ready Testing paragraph and accepted decision reasons inline. Add one task index link; reuse the same task record across related skills instead of producing separate ADR/context/handoff files. Link an existing ADR only when relevant. Prose follows the project documentation locale; public skill identifiers remain English.
