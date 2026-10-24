# Usage

`/palarran:agent:improve {failed run + feedback} [--plan]` identifies target/skill checkout and reads applicable AGENTS/INDEX/contracts. --plan runs no reproduction/tests/models/worktrees and applies no application/skill patch; it writes protocol/ADR/proposal. Without it, perform specifically authorized local reproduction/checks and scoped skill/docs fixes. Do not reconfirm existing authorization; clarify missing data/goals only where substantive. Invocation implies no paid APIs, training, installs, deploy/outreach.

Runtime needs the full checkout; the portable agent plugin includes guides/templates; the operator installs runtime separately, with no automatic downloads:

```sh
python3 -m orchestrator.agent_improve prepare --input /private/improvement.json --target /absolute/target --output /private/new-packet
python3 -m orchestrator.agent_improve compare --packet /private/new-packet --proofs /private/proofs.json
```

Prepare reads/writes private local artifacts only, so it is allowed as structural preparation under --plan; it does not call agent_eval.create. Execute generated suites separately through existing `python3 -m orchestrator.agent_eval create/work/report` under [operations](../eval/operations.md). Run all baseline cases, then candidates; one case per run. No paid execution in tests. Use matching models within pairs; do not escalate after FAIL. One shared budget covers all runs, including incident/failed trials. Before new model admission, carry prior charges/reserves and reconcile unknowns first. Runtime reports exclude carry from current observed usage, avoiding double-counted carry in cumulative evidence.

Proofs JSON: `{"baseline":{"case_id":{"state":"/private/state","run":"RUN_ID"}},"candidate":{"case_id":{"state":"/private/other-state","run":"OTHER_ID"}}}`. Case IDs must match the frozen set; absent entries remain missing, not PASS. State/packet stay outside target. Reports print sanitized JSON; the skill may save/produce Markdown handoff in target memory using the [template](../../../templates/palarran-agent-improve/review.md). Private packets contain instructions/rubric and must not be committed.

Publish only a scoped reviewed diff + sources/decisions + sanitized comparison. Exclude others' dirty files; rollback is not reset --hard. Keep successful/failed few-shot examples separate from private final holdout. No recurring optimizer/automation without a user request.

The [inert example input](../../../templates/palarran-agent-improve/incident.example.json) illustrates a command-only fixture protocol. All /absolute paths and synthetic fixture executors require replacement/review; these are not real skill/model results. Model trials need separately approved native AI/usage policies with the existing shared budget/carry; the example allocates no money.
