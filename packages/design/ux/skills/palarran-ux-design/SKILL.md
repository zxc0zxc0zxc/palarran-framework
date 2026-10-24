---
name: palarran-ux-design
description: Design responsive application UX from a business description or README with research into 3–4 analogs, diagrams for every screen and states. Use for /palarran:ux:design; preserves concepts and decision rationale for later tasks. Does not define visual style or implement the interface without a separate request.
---

Shared cycle: before work and after checks, perform [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile prohibitions remain. `--plan` uses no network/publication; an outage does not block the primary task.

# UX design

Invoke `/palarran:ux:design {description}` or `$palarran-ux-design {description}`. Description is optional: without one, read the **target project's** README and related product docs. Authoring the skill does not mean designing palarran UX.

## Mandatory guides and memory

Find the checkout from the real `SKILL.md`, resolving symlinks: `../../`. The target project for outputs is a separate root from request/workspace. Before choices, read [shared decision memory](../../../../core/agents/docs/decision-memory.md), target `.palarran/INDEX.md`, `.palarran/ux/INDEX.md` and related accepted ADR/concepts. Create task context before a new decision; explain every accepted choice with alternatives/evidence/consequences before dependent changes. Update index/handoff, reuses/supersedes; history remains context for later tasks. Store no secrets/personal data and treat no old ADR as new authority.

Then read:

- [Navigation and rules](../../docs/README.md), [business and reuse](../../docs/business.md).
- [Reference research](../../docs/research.md), [UX analysis](../../docs/analysis.md).
- [Diagrams](../../docs/diagrams.md), [responsiveness](../../docs/responsive.md), [concise UI copy](../../docs/microcopy.md).
- [Workflow and concept storage](../../docs/workflow.md), [review/acceptance](../../docs/review.md), [sources](../../docs/sources.md).
- [Concept template](../../templates/concept.md), [screen template](../../templates/screen.md), [reference template](../../templates/reference.md).

If mandatory guides are missing, request the checkout path instead of substituting general knowledge. Sources in the methodological reference are not application business references. Identify guides/commit actually read and reused ADR/concepts.

## Sequence

1. From description, otherwise target README/product docs, extract roles/tasks/outcomes, market/platform and constraints. Reconcile existing screens/routes/previous concepts. Do not invent monetization, auth, consent, chat or payment without a business basis.
2. If a process/screen's meaning is unclear, ask **“What does this business process—<name>—do?”**, specifying the needed input/outcome. Do not accept dependent decisions before the answer; continue independent work. After the answer, first choose existing screen/block reuse, a new state or a new screen and explain why.
3. Find current similar established businesses through web search, open sources and research matching journeys. Default 4 independent products, minimum 3 with an explained limitation; fewer means incomplete research and draft only. Google/Yandex or Tinder/Mamba are candidate examples, not a universal list or completed research. Popularity does not prove usability.
4. Study actual websites/account interfaces with available browser/UI tools within authorized read-only scope. Without access, **search screenshots**, official help/tours/store images, then dated third-party walkthroughs; open source and view the image itself. Record platform/role/date/access/confidence and observation IDs. Do not infer hidden transitions as facts from a frame; label unknown/inference. Without tools/live access, fabricate no observations. Do not bypass login/paywall or send/buy/change accounts for research.
5. Create brief/research cards/comparison/reuse-map, then explain each accepted UX choice in target `.palarran/ux/<task>/decisions/`. Separate observation, our interpretation and proposal; do not attribute approval to the user. New variants do not erase earlier decisions.
6. Cover the entire application from brief/product docs by default without reducing it to examples; partial scope only by request or as an explicitly unfinished draft. Create versioned concepts under the workflow: overview, screen catalog, journey flows and a card for **every in-scope screen**. For each: desktop/mobile functional-block layouts, ordering/action explanations, tablet/content adaptation, state graph or justified N/A, entry/exit/back/guards/errors/permissions and concise UI copy. A sitemap/global flow does not replace screen diagrams. Preserve Mermaid source; export/view previews when a renderer is available.
7. **UX must be responsive:** tasks/actions remain accessible on narrow/mobile/tablet/desktop, accounting for keyboard/touch/long content/focus/scroll. Do not stop at a scaled-down desktop image. Screen explanations stay separate from UI; add no colors/fonts/radii/branding/CSS or implementation/Figma scope without a request. CTA is concise and accurate: do not combine terms, analytics and age. Do not hide essential price/irreversibility/data for brevity.
8. Run coverage/syntax/link checks, expert walkthrough and available render review. Do not call static concepts user-tested, responsive implementation verified or WCAG compliant. Record PASS/FAIL/NOT RUN; preserve explicit unresolved business questions and reference gaps. Review-ready requires mandatory coverage; approved requires an actual owner decision.
9. Save concepts/revisions, evidence links, decisions, shared and UX indexes and handoff in **target** `.palarran/`, not plugin cache/scratch. Give a short summary: understood business, researched products/boundaries, screen/diagram links, key ADRs and questions. The next task must reuse this context rather than start over.
