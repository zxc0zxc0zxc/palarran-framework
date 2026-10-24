# /palarran:product:define — the product itself

First read [Superhuman/Amazon](cases/product-discovery.md), [evidence](evidence.md), [workflow](workflow.md). We recommend starting with a customer outcome and narrow segment, then agreeing on scope. This transfers case lessons, not their promised results.

Read the description or target README, existing product/UX/architecture/constraints and decisions. Do not replace an existing business with a fashionable one. Clarify the business process if the user/buyer, job or transaction is unclear; do not indiscriminately cover both B2B and B2C.

Output using the [brief](../../templates/product/brief.md):

- ICP and who pays/uses/decides; job/trigger/current workaround, problem frequency/severity and evidence.
- One clear value proposition, differentiation from the closest substitute, limitations/inconveniences and switching costs.
- Proposed business model, billing unit, free/paid boundary and cost to serve. Price is a hypothesis without customer validation.
- MVP with one useful end-to-end outcome, scope/non-goals, assumptions/risks and dependencies on market/compare/revenue/acquisition revisions when available. Missing references are gaps, not grounds for fabricated research.
- Metric tree: value → activation → reuse/retention → payment; event, cohort, denominator/window, proposed threshold and rationale. [Google HEART](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/) helps connect goals and signals; not every category is needed for every product.
- Critical H-IDs, cheapest falsifying test, success/stop/pivot criteria, owner/budget/window. Label numerical targets proposed, not benchmarks borrowed from another industry.

A business-flow diagram is mandatory: actor → trigger → useful outcome → delivery/payment/return path, including the main failure/rejection. The UX handoff lists processes/entities/constraints; it does not prescribe screens, style or stack. Engineering-planning handoff requires a defined user outcome, scope/AC, agreements/unknowns and source revision. It does not start a build.

DoD: the brief matches actual context, every important conclusion is traceable, the build/test/stop decision is reasoned or needs_input, and risks/experiments are not described as completed.
