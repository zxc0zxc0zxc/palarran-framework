# Source UX → UI: what to preserve and what may change

## Source concept selection

Read target `.palarran/ux/INDEX.md`, accepted decisions, source concepts/revisions and user intent. Use an explicitly supplied source; otherwise select an unambiguously current suitable concept and explain why. With conflicting approved/draft revisions, clarify instead of automatically taking the newest filename.

Without UX, research visual preference/brand/references, but full screen design remains draft. Propose a concept path or UX stage; do not start substantial new UX scope or invent screens for the user. Draft UX may be used with explicit status/gap list without calling it approved.

## Mapping

`ux-map.md`: UX concept/revision/commit → UI revision/direction → every Screen/State/Block ID → preview/spec → ADR and coverage status. UI covers all in-scope UX screens and mandatory states by default, including mobile/desktop. Partial scope must be explicitly requested or labeled incomplete draft; two attractive hero screens do not replace an entire application.

Preserve:

- user goals/roles/permissions and navigation/back/recovery;
- primary/secondary action priority, data ordering and mandatory information;
- concise accurate UX copy, field labels and errors;
- loading/empty/error/validation/pending/success/permission behavior;
- responsive functional alternatives and accessibility intent.

UI adds typography/scale/weights, role-based colors, spacing/grid/density, borders/shapes, elevation/materials, imagery/icons, visual component states, motion and coherent responsive styling. This does not authorize changing action outcomes/data models or adding onboarding/paywalls/consent.

## Style conflicts with UX

First adapt style to UX. For example, weaken/replace glass with an opaque surface if it harms form readability; glass does not justify moving the primary CTA to an unclear floating area. Denser tables must not lose data/actions on mobile.

When a new screen/layout structure or changed flow is needed, create `ux-deltas.md` with source ID, reasons, alternatives, impact and proposed UX change. Do not silently edit approved UX or present UI preference as business approval. Continue independent visual choices; mark dependent screens pending. Technical preview controls must not appear in application UI.

## Updates and handoff

With a new UX revision, check mapping, obsolete screens/states and effects on tokens/components; do not overwrite earlier UI revisions. Reuse previous UI systems only after checking source UX/brand/style assumptions. In review, distinguish UX-preserved from UX-delta; a new developer must find the original screen intent without reconstructing all correspondence.
