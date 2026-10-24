# Source UX/UI contract

Before changing code, read target product docs and `.palarran/INDEX.md`, UX/UI catalogs, relevant accepted ADRs and previous frontend handoffs. Select **both specific** revisions, their statuses and in-scope screens/states/blocks, UI tokens/components/assets and responsive specs. Do not assume any `v001` is the latest agreed version or invent approved status. An explicit request to implement a draft permits it as source with the limitation stated.

Build [coverage](../templates/coverage.md): source UX ID/state → source UI spec → application route/component/data adapter → browser scenario → evidence/status. The UI preview is a visual reference; its gallery/state switcher does not become application navigation. Cover the entire requested scope by default, not merely a landing page/happy path. Partial implementation requires agreed scope or an explicitly unfinished result.

| Ambiguity | Action |
|---|---|
| Missing concepts | Find target catalogs/requested path; if absent, request the location or propose the UX/UI stage. README does not replace screen specs |
| UX/UI conflict | Clarify the conflict; do not change the UX business scenario/role for UI convenience. Record a proposed delta and continue independent work |
| UI omits a technical detail | Choose within existing conventions and explain through an ADR; do not require approval for every size/component |
| Missing asset/token | Check source, existing assets and [asset workflow](implementation.md); do not invent a user-approved replacement |
| Source revision changes during work | Record the diff, affected IDs, new mapping revision and repeat checks |

Preserve concise UI copy, action ordering/availability, roles/permissions, entry/back/deep links and loading/empty/error/validation/success from UX. Visual density/material/type/color come from UI. Implementation may improve internals without changing behavior when the choice is explained. Propose required behavior/style changes with reasons and concrete impact; do not mark them accepted through silence.

No repeat selection among ten design systems is required: that choice was made at the UI stage. Do not start new competitor research instead of implementing unless source is actually unclear or the user requests rework.

## SDD source and execution revision

The [SDD plan](sdd-agents.md) additionally records plan/spec/API revision and both UX/UI revisions. Without an execution plan, first derive one from these source concepts without inventing new UX. R/AC/screen/state/block/C IDs → TASK/T IDs → application route/component → browser gate/DoD. [Progress](progress.md) appears directly in this source plan; a semantic scope change has a new revision/impact/ADR, while completion metadata does not change the design revision. Missing critical source remains a blocker, not a silently accepted requirement.
