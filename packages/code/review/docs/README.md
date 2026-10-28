# Review a change without a build ceremony

Use `/palarran:code:review {range}` for an existing change or release. Begin with the [small-task entry](../../../core/agents/docs/task-context.md) and target instructions; read this guide and the relevant source section only. Larger cross-repository changes may need the full planning/integration contract, but a small review does not require a new SDD plan or worktree.

## Bind the subject

Resolve both ends of the supplied range to full commits and record the exact diff semantics. `BASE..HEAD` compares those trees; `BASE...HEAD` starts at the merge base. Do not silently replace a release comparison with the current branch. With no range, inspect visible project context; ask only when multiple plausible subjects remain. Record dirty files separately and preserve all local work.

Use bounded Git reads with external diff/text conversion disabled and explicit arguments. Resolve refs as commit objects before reading the diff; never interpolate supplied refs or paths into shell code. List changed files, then inspect their callers, state owners and relevant tests. A multi-file change is a diff review, not multiple guessed `log --follow` calls. Read further history only to resolve a concrete question; missing ADR trailers mean recorded rationale is unknown.

## Follow the behavior

For each meaningful path, trace input → validation → state change → side effect → acknowledgement. Check failures, retries, duplicate requests, concurrent work, shutdown and stale state where they apply. Distinguish intent, what the code demonstrates and what was actually executed. A unit test passing with a fake provider is useful evidence; it does not establish the live provider or production integration.

Prioritize reproducible defects that change behavior. Each finding needs the exact location, triggering condition, observed or source-supported failure, impact, counterevidence and a safe retest. Label an unexecuted hypothesis as suspected. Do not turn a style preference, unrelated legacy issue or imagined future requirement into a blocker. If no defect was found, state the reviewed scope and the remaining test gaps instead of certifying correctness.

Run existing project tests only within an already authorized test scope and reviewed command binding. The [project-tests adapter](../../../validation/application/docs/project-tests.md) supports server/worker/bot test suites without inventing HTTP, SQLite or a browser. Otherwise record execution as NOT_RUN and propose the precise retest. No automatic fix, install, live model call, commit, MR publication or deployment follows from a review request.

## Small output

Keep `summary.md` and `report.json` under target `.palarran/code-review/<task>/`. Include accepted decision reasons in the summary and add one task-level index reference; do not generate a separate ADR, context and handoff per skill pass. Larger reviews can link existing decisions or add a dedicated ADR when a durable architectural choice warrants it. Preserve earlier accepted revisions.

A useful summary is: subject and scope; findings ordered by impact; tests actually run; limitations; and an MR-ready **Testing** paragraph. Do not claim new environment variables or production readiness unless this review established them. The JSON report may use this small shape:

```json
{
  "version": 1,
  "profile": "code-review",
  "subject": {"base_commit": "FULL_BASE", "head_commit": "FULL_HEAD"},
  "scope": {"paths": ["worker.go"], "excluded": []},
  "findings": [],
  "checks": [{"id": "R7", "status": "NOT_RUN", "scope": "project_test", "evidence": null}],
  "decisions": [{"choice": "Inspect delivery failure before changing retry logic", "reason": "State is committed before acknowledgement"}],
  "limitations": ["Live provider behavior was not exercised"]
}
```

The shape is an authored handoff, not a claim that the project-tests runner validates arbitrary code-review findings. Use real commits, evidence and reasons; placeholders are inert examples.

### Example: a failed delivery

A synthetic worker replaces a recovery code before asking an external provider to compose the reply. One failure branch does not include the new code. Review the state owner and both reply branches, then propose a fake-provider test: first response fails, second response succeeds. Check that the code is either delivered on its own request or safely rolled back; it must not leak into the next unrelated response. If the earlier input gate prevents replacement, record that counterevidence and dismiss the candidate. No external provider call is needed to test this state transition.
