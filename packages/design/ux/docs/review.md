# Review and readiness criteria

## Coverage and traceability

| Area | Check | If missing |
|---|---|---|
| Business | Brief from description or target README/docs, clear roles/tasks/outcomes | Name the unknown process and ask a specific question |
| References | Default 4, minimum 3 independent products with relevance and scope explained | Research incomplete; do not present draft as completed comparison |
| Account UX | Account interfaces actually researched or screenshots found/viewed; visible provenance and gaps | Do not make confident claims about hidden UX |
| Evidence | Observation IDs, source/access/publication dates, platform/role and facts versus inference | Remove unsupported claims or label hypotheses |
| Reuse | Existing screens/states/blocks accounted for; each new/change has a reason | Check duplication and unnoticed scope expansion |
| Screen coverage | Every in-scope Screen ID has a card+desktop/mobile layouts+explanation | Concept FAIL, not deferred visual design |
| Flow/state | All targets/actions/guards clear; pending/error/empty/permission and back/recovery covered as applicable | Finish independent work; dependent flow remains draft |
| Responsive | Tablet/content transitions, keyboard/touch, long content/reflow, focus/scroll | Do not promise responsive UX from a desktop flow alone |
| Copy | Concise UI strings, no instructions/documentation in buttons or extra consent clauses | Simplify task/text first without hiding essential meaning |
| UX boundary | No imposed colors/fonts/radii/brand/production CSS | Remove visual scope or separate it into another request |
| Memory | Concepts/revisions/catalog, canonical ADR, INDEX and handoff saved in target project | The next task must not reconstruct everything from chat |

Record exceptions/narrow scope explicitly. For many screens, split by journeys/review sections without silently omitting in-scope screens. Cover key journeys through references with honest gaps; do not require every competitor for each rare edge case or automatically treat such a row as proven.

## Verification types

- **Syntax/local links:** Mermaid parser and file-link checks. Parser success does not prove a readable render.
- **Visual reading of diagrams:** with a renderer, view previews and inspect labels/edges/graph scale. An automatically generated but unviewed SVG is unverified.
- **Expert walkthrough:** exercise concepts using task scripts, back/error/no-data/no-permission, concise copy, role boundaries and context preservation. This is review, not real user behavior.
- **Prototype/implementation validation:** keyboard, touch, reflow, screen reader, real errors and user task testing only if a prototype/application exists and was tested. Otherwise NOT RUN.

Statuses: PASS/FAIL/NOT RUN + evidence. Concept `review-ready` means the review contract is fulfilled, **not** “usability proven” or WCAG compliance. `approved` needs an actual owner decision. Research-source links do not replace actual testing with our audience.

## Skill behavior evaluation scenarios

In subsequent sandbox evaluation, check:

1. Without a description but with a business README, extracts the business without repeating a generic question or analyzing the tools checkout as the application.
2. An unclear process prompts “What does this business process do?”, preserves unknowns and continues independent work.
3. Four products with closed account access: seeks official materials/screenshots without inventing entry/transitions; an image snippet without viewing is not evidence.
4. Existing accepted S02: checks reuse, preserves revision and avoids duplication caused by a new name.
5. Long CTA/extra consent: keeps concise accurate action and necessary independent choices without combining analytics/age/terms.
6. Desktop only: does not declare completion; adds mobile layouts and tablet/reflow/keyboard contract.
7. Fewer than three researchable products or unavailable browser: preserves useful draft with gaps and real sources without fabricating research.
8. Next task: reads target UX/decision indexes, explains choices using stored IDs and preserves history.

These scenarios are an evaluation plan, not a claim that LLM behavioral evaluation ran during authoring. Do not run third-party account mutations or paid research without corresponding scope.
