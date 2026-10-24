# /palarran:ux:design workflow

## 1. Recover context and business

Locate the target project separately from the installed skill checkout. Read the [shared memory contract](../../../core/agents/docs/decision-memory.md), target `.palarran/INDEX.md`, `.palarran/ux/INDEX.md` and relevant accepted decisions/concepts. Then read **all** `packages/design/ux/docs/` guides and selected templates. If missing, request their location rather than substituting general knowledge for required reading.

Analyze the description; without one, target README/product docs, then existing screen/route inventory. Record business brief and known/proposed screen/process scope under [business.md](business.md). Clarify unclear processes with “What does this business process—…—do?”; do not invent dependent screens, and continue independent work. A skill-authoring request does not request UX for palarran's business.

## 2. Collect and analyze references

Under [research.md](research.md), find current similar established services: default 4, minimum 3 distinct products with explanation; fewer means incomplete research. Open sources/actual screenshots, exercise authorized read-only journeys or use official help/tours. For closed account interfaces, search screenshots instead of presenting a landing page as account research. An unavailable screenshot means unknown, not a fact reconstructed from memory.

Create cards/observation IDs and compare equivalent tasks under [analysis.md](analysis.md). Record platform/role/date/access/confidence. Every proposed pattern links to evidence and our constraints; popularity does not prove usability. Research does not authorize sending, buying or changing third-party accounts.

## 3. Record decisions and screen inventory

Before choosing screens/layouts, record accepted decisions with rationale and alternatives in canonical `decisions/`, and update the shared index. Build `reuse-map.md`: existing/reuse/changed state/new screen with reasons. Label proposed concepts not yet approved by the user accordingly; an agent may accept a working hypothesis within scope without attributing its approval to the user.

Major screen/layout/flow/state/responsive/copy choices have an ADR or individually explained subdecisions within one under the shared contract. Separately describe unresolved business cases, roles/permissions, recovery and potential effects on existing journeys. Do not automatically import another product's paywalls/permissions/registration.

## 4. Design and save the concept

```text
.palarran/
  INDEX.md
  ux/
    INDEX.md
    <YYYY-MM-DD-task>/
      context.md
      research/
        references/R1-product.md
        comparison.md
        evidence/                   # Safe authorized captures only, if needed
      reuse-map.md
      decisions/0001-journey.md
      concepts/
        v001/
          overview.md
          screen-catalog.md
          flows/J01.md
          screens/S01.md
          diagrams/                 # .mmd/preview, if exported
          review.md
      handoff.md
      scratch/
```

`ux/INDEX.md` is a concept/revision catalog: product/scope/task, status (`draft`, `review-ready`, `approved`, `superseded`), link, source commit, related ADR and known gaps. Canonical decision status stays in shared `.palarran/INDEX.md`; do not create another ADR index with conflicting truth. `approved` requires actual approval by the corresponding user/owner.

Preserve every revision; new `v002` references `v001`, affected Screen IDs and reasons. Do not overwrite approved/superseded concepts for the current variant or lose earlier comparison context. Keep a self-contained concise explanation even if remote screenshots become unavailable. Do not publish complete personal data/screenshots/logs.

Fill [concept](../templates/concept.md), [screen](../templates/screen.md) and [reference](../templates/reference.md) templates. For **every** screen: goal/role/entry/exit, concise copy/actions, functional blocks/reading order, desktop/mobile layout diagrams, tablet transition rules, states/guards/error recovery and evidence/ADR links. A global flow without screen cards does not complete the task. Do not add colors/fonts/CSS, application code or polished mockups without a separate request.

## 5. Review, questions and handoff

Check coverage under [review.md](review.md), diagram syntax and available rendering/visual inspection; report verification boundaries honestly. Walk through primary/error/back/permission journeys on narrow/phone/tablet/desktop with keyboard/long content. Without a running prototype, real interaction/browser accessibility testing is NOT RUN.

Do not stop all work for one question: save completed parts, unresolved screens as proposed and required answers. But do not mark a concept review-ready when mandatory screen coverage/adaptation/reference minimum is missing. A useful draft is allowed with explicit gaps.

Update shared and UX indexes, decision evidence and handoff. Give a concise user response: understood business, which 3–4 products were researched and to what extent, concept/screen/diagram links, major accepted decisions/unknowns and actual checks. Do not repeat the entire report in chat. The next task reads saved concepts and decisions before new research/design; refresh reference evidence and product assumptions where needed.
