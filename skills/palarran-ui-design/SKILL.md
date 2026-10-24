---
name: palarran-ui-design
description: Create responsive visual design from UX concepts and references, choosing among ten established design systems or custom references. Use for /palarran:ui:design; creates visual previews, tokens and components, generates required images and preserves decision explanations for later tasks.
---

Shared cycle: before work and after checks, perform [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile prohibitions remain. `--plan` uses no network/publication; an outage does not block the primary task.

# UI design

Invoke `/palarran:ui:design {direction/description/references}` or `$palarran-ui-design`. Arguments are optional; source UX is mandatory for complete UI. Authoring the skill does not imply creating palarran's design.

## Mandatory guides

Locate the skill checkout from the resolved real `SKILL.md` (`../../`) separately from the target project. Read [shared decision memory](../../docs/skills/decision-memory.md), target `.palarran/INDEX.md`, UX/UI indexes and related accepted ADR/concepts. Explain every accepted choice (reason, alternatives, evidence, consequences) in canonical target `decisions/` before dependent changes; update indexes/handoff and reuses/supersedes. Old ADRs are context, not new authority. Scratch is temporary; accepted history persists.

Read the entire reference:

- [Contract](../../docs/ui/README.md), [ten directions + custom](../../docs/ui/design-codes.md), [machine-readable catalog](../../docs/ui/catalog.json).
- [Research and custom references](../../docs/ui/references.md), [UX binding](../../docs/ui/ux-binding.md).
- [Foundations/tokens/components](../../docs/ui/foundations.md), [responsiveness and accessibility](../../docs/ui/responsive.md).
- [Visual output and images](../../docs/ui/visual-output.md), [workflow/storage](../../docs/ui/workflow.md), [review](../../docs/ui/review.md), [sources](../../docs/ui/sources.md).
- [Concept](../../templates/ui/concept.md), [screen](../../templates/ui/screen.md), [reference](../../templates/ui/reference.md), [token example](../../templates/ui/tokens.example.json).

If guides are missing, request the checkout path instead of substituting general knowledge. Identify guides/commit actually read. For source UX, use [its contract](../../docs/ux/README.md), [responsiveness](../../docs/ux/responsive.md) and [concise copy](../../docs/ux/microcopy.md).

## Sequence

1. Locate current source UX revision/status/scope through request and target index. Read all in-scope screens/states/blocks, constraints, reference cards and earlier UI choices. README provides business context without replacing UX. With missing source/conflicting versions, clarify path/selection and propose `/palarran:ux:design` first; independent style research is allowed, fabricated complete UI is not.
2. Use an explicit user/accepted choice without re-asking. Without a choice, show **all ten** catalog systems: Material 3, Liquid Glass, Fluent 2, Carbon, Atlassian, Polaris, Spectrum, Lightning, Ant Design, Primer; separately **“Custom references.”** This is a curated menu, not a measured popularity ranking. Recommend 2–3 candidates with reasons. Ask for direction through available selection UI/numbered text; preselection/silence is not consent. Final style stays pending while awaiting the answer; continue independent inventory/research. If helpful, compare 2–3 samples of the same UX screen/state, not ten full applications.
3. Accept user links/images/local files/Figma as main, supplementary or anti-references; open and actually view images with available image/browser tools. Clarify unclear preferences. Research canonical system source (main user reference for custom) and at least 2 additional relevant visual references. Record access/date/platform/version, observation/inference and unknowns. Insufficient material means gap/draft, not fabricated research. Do not generate fake reference screenshots, bypass login or change accounts for research.
4. Create context/research/UX mapping; preserve explanations for every accepted choice before applying it: direction, reference synthesis, tokens, density, components, adaptation, assets and exceptions. Related decisions may share a record with separate reasons. Do not invent user approval. Preserve source UX roles/actions/flow/concise copy; needed changes are proposed `ux-deltas.md` with rationale, not silent implementation.
5. Create coherent semantic JSON/CSS tokens, typography/spacing/color/material/motion and component/state specs, then **actual visual previews of all in-scope screens/states**. Default: local runnable HTML/CSS with synthetic data, local assets and utility gallery/state switcher, without production application mutations/deployment. Text/Mermaid/palettes do not complete UI. Figma/native follows explicit format choice and required host skills/tools. Do not install a library merely because its namesake system was selected.
6. **If design needs an image, generate it** through an available image-generation tool and include the selected asset in preview: illustration, hero/background, cover and other required bitmap assets. Define purpose/composition before generation; read mandatory host image skills when available. Preserve output, prompt without private data, tool/date, selection reason, alt/decorative status and responsive crops. Do not fabricate real logos, product screenshots or factual photos: use authorized originals or explicitly synthetic concept placeholders. Do not rasterize CSS/SVG layouts/icons merely to generate them. Without image generation, state blocker/NOT RUN and draft with labeled placeholder, not “finished asset.” Analyze custom references instead of replacing them with generation without a reason.
7. **Responsiveness is mandatory:** narrow/mobile/tablet/desktop, actual layout boundaries, long/empty/error/pending content, keyboard/touch/focus/zoom and overflow. Semantic tokens do not guarantee post-compositing contrast: test glass on actual backgrounds and supply opaque/unsupported-effects/reduced-motion fallback. Web Liquid Glass is adaptation, not a native-renderer promise. Separate any UX behavior change as a pending delta.
8. Open preview and view renders with available browser/image tools; check coverage/state matrix and applicable contrast/keyboard/focus/targets/overflow/fallback. Save evidence by viewport/screen/state with PASS/FAIL/NOT RUN. Syntax checks are not visual review; screenshots are not user tests. No renderer/mandatory coverage → runnable draft with limitations, not review-ready; approved requires a user decision.
9. Preserve versioned concepts, screens, preview/assets, tokens, research, canonical ADR, shared/UI indexes and handoff in **target `.palarran/ui/`**, not installed package/scratch. Keep old revisions; the next task reads this context. Give a concise summary with an openable preview, selected direction/sources, source UX revision, checks and questions. Do not call a design concept production implementation.
