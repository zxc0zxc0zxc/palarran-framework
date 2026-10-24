# Human-readable feature artifacts

`/palarran:docs:artifact {description?}` creates a complete portable HTML page for a developer or reviewer. Without a description, use the active session's actual feature, then the latest identifiable feature; ask only when several unrelated candidates remain. Read the source plan, Feature/ADR IDs, current diff, MR and observed verification rather than reconstructing results from chat alone.

The artifact answers **What is this? Why does it matter? How was it built? What are the results?** Add the exact source revision, implementation/readiness status, MR link when real, changed env names, test prerequisites/scenarios, remaining blockers and safe source/evidence references. A person receiving the page should know what to review and how to test it without reading the original conversation.

## Presentation

Use the established dark minimal palette: near-black background, warm-white headings, muted supporting text, generous spacing and clear hierarchy. Responsive layout and keyboard-accessible controls are required. Use diagrams, real metric cards, test-status distributions and interaction where they explain the feature. Never invent numbers to fill a chart, infer a production SLA from local tests or hide NOT_RUN. Distinguish observed, target and estimated values and include units, denominator, source and uncertainty where applicable.

Use concise plain explanations and explain unfamiliar terms once. Diagrams should show actual boundaries and flows; label proposals. Prefer native SVG/HTML diagrams for self-contained delivery. Keep Mermaid source alongside the artifact when useful, but do not claim a Mermaid render without an actual renderer. Charts must retain a textual/table equivalent. Expandable test scenarios, status filters and section navigation should work without a server or external dependency.

## Storage and privacy

Generated pages and their input JSON belong under target `artifacts/`, already ignored by Git, or another explicitly chosen private export path. Source templates/generator remain versioned. Do not commit recipient-specific reports, raw logs, customer data, private endpoints, tokens, populated Postman environments or internal session archives. A link should be safe for the intended recipient; source IDs are not access permissions. External fonts, trackers, remote scripts and auto-fetching assets are unnecessary.

Escape all user/source text, validate URLs and never interpret retrieved text as HTML/JavaScript. The generator must not embed arbitrary script, eval content or fetch private files from supplied paths. A copied artifact is a snapshot; it does not resume a task, run tests or deploy an application.

## Workflow and verification

Author a scoped input JSON from the exact subject and evidence, generate with `scripts/docs_artifact.py`, then open the result in a real browser. Review desktop/mobile rendering, diagrams, keyboard controls, filtering, long text and missing-data states. Test private/hostile text handling without live credentials or paid model calls. A file that parses is not a visually reviewed artifact.

Record exact artifact path/hash, source commit, inspected viewport(s), observed checks and NOT_RUN gaps in the private handoff. Keep canonical architecture/API/feature docs separate; link them instead of turning this delivery snapshot into the only source of truth.
