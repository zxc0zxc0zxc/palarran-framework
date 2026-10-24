# UI design: visual language over UX

`/palarran:ui:design` reference for visual design **based on our UX concepts**, source references and user preferences. Input: description/direction/custom materials are optional, but a source UX revision is mandatory for the final screen set. UI does not reinvent business, navigation, roles or CTAs for appearance.

## Contract

- Read [shared decision memory](../skills/decision-memory.md), target UX/UI catalogs, accepted ADRs and source UX screens/states. Record IDs/revision; do not silently use an outdated or first-found concept.
- Offer [10 directions](design-codes.md) with first-party references and a separate **“Custom references”** mode. This is a curated menu of established systems, **not a verified global popularity ranking**. Menu order is not rank.
- Do not re-ask a direction supplied by the user/chosen earlier. Without a selection, show options and ask a preference; do not treat a default/preselection as consent. Continue independent UX inventory/research; final style decision remains pending.
- For the selected direction, study its canonical source and at least 2 additional relevant visual references. User links/images may form the basis or supplement a system. Do not invent evidence to fill coverage/access gaps.
- Output is **visual**: responsive previews of all in-scope screens/states, style guide, semantic tokens, components and handoff. Text alone/a palette/a Mermaid graph does not complete UI work.
- Default medium: local HTML/CSS concept preview with synthetic data, not production application edits. Figma/native/other formats require an explicit request and suitable tools; application code/deployment are separate.
- **If the design needs an image, generate it** and include it in the preview, preserving prompt/tool/date and responsive crops; do not present generated assets as actual reference screenshots. Without a generator, report explicit draft/gap.
- **Responsiveness is mandatory**: narrow/mobile/tablet/desktop, wrapping/density/states, keyboard/touch/focus, contrast and effects fallbacks. Check actual renders when tools are available; otherwise deliver a runnable draft with NOT RUN, not “visually verified.”
- Preserve all revisions in target `.palarran/ui/`, accepted rationale in canonical `decisions/`, UX deltas separately. Read this context before new decisions in the next task.

## Documents

| Document | Purpose |
|---|---|
| [design-codes.md](design-codes.md) and [catalog.json](catalog.json) | Ten-system menu + custom, canonical sources, applicability and selection |
| [references.md](references.md) | Additional/custom references, screenshots, provenance, conflict handling |
| [ux-binding.md](ux-binding.md) | Bind UI to source UX without losing screens/states/concise copy |
| [foundations.md](foundations.md) | Color/type/spacing/shape/elevation/icons/motion, tokens and components |
| [responsive.md](responsive.md) | Responsive layouts, themes, contrast/focus/motion/effects |
| [visual-output.md](visual-output.md) | Style exploration, rendered concepts, preview and handoff |
| [workflow.md](workflow.md) | Workflow, storage, review and subsequent tasks |
| [review.md](review.md) | Definition of done, statuses, behavioral checks |
| [sources.md](sources.md) | Researched primary sources and limitations |

Templates: [concept](../../templates/ui/concept.md), [screen](../../templates/ui/screen.md), [reference](../../templates/ui/reference.md), [token-example](../../templates/ui/tokens.example.json). Fill them for the application; their existence does not mean a finished palarran visual design. Methods/source UX: [docs/ux](../ux/README.md).
