# Workflow and durable context

## 1. Context and source UX

Separate installed skill root from target project. Read [decision memory](../../../core/agents/docs/decision-memory.md), target shared index, UX/UI catalogs and current concepts/accepted ADRs. Locate source UX revision through request/index, check status and scope; clarify selection between incompatible versions. README explains the business without replacing a missing UX concept.

Without UX, request a path/concept or propose `/palarran:ux:design` first; research/style exploration may proceed while awaiting an answer, but do not declare full UI ready. Do not invent screens. Record task, constraints, source UX IDs/revision and earlier decisions in `context.md`.

## 2. Direction and source material

Start from user-specified/accepted UI decisions. Otherwise offer all ten options from the [catalog](catalog.json) and **“Custom references”**, plus a justified shortlist; ask for a choice through available selection UI or numbered text. Default/preselection and silence are not consent. While selection is pending, continue independent inventory/research. Do not require a fresh choice on every run.

Custom input: links, images, local assets or Figma; clarify likes/prohibitions when unclear. Custom references may replace a system or supplement it. Under the [methodology](references.md), study the selected system's canonical source and at least 2 additional visual references. In custom mode, use an explicit main user reference instead of the canonical source, also with at least 2 additional sources/products; with less material, state the gap and retain draft status without inventing evidence.

## 3. Explained decisions and output

Create coverage/reuse mapping before layout. Explain every accepted choice—direction, additional references, tokens, density, responsive adaptation, components, exceptions—in canonical ADRs before dependent changes. Related choices may share an ADR if each is explained. Do not present agent recommendations as user approval; `decision_basis` identifies authority. For UX conflicts, propose `ux-deltas.md` instead of silently changing flows/roles/copy/actions.

Generate required design images and include them in the preview with asset records under visual-output; missing tools mean draft/gap. Create [foundations](foundations.md), [responsive layouts](responsive.md) and [visual output](visual-output.md), preserving old revisions. All in-scope screens/states are mandatory; scope reduction needs a request basis, otherwise the result is explicitly partial draft. Statuses: draft → review-ready after required checks; approved only after actual user decision, superseded with a successor link.

## 4. Directories and handoff

```text
.palarran/
  INDEX.md
  ux/INDEX.md                         # source; do not overwrite from UI
  ui/
    INDEX.md                         # task/concept, status, UX revision, direction
    <task>/
      context.md
      research/                      # reference cards, authorized image evidence
      decisions/0001-<choice>.md      # canonical explanations
      concepts/v001/
        overview.md                  # brief, style guide, sources, ADR links
        ux-map.md                    # screen/state/block → spec/preview
        ux-deltas.md                 # pending proposals, if any
        tokens.json
        tokens.css
        components.md
        screens/<screen-id>.md
        preview/index.html           # plus local assets/CSS/JS
        assets/                      # generated images + asset records
        review.md                    # PASS/FAIL/NOT RUN + evidence
      handoff.md
```

Paths define the output contract, not a finished application structure. Link decisions/concepts/source UX and earlier versions in target indexes. Handoff: opening the preview, covered screens/states, selected style and rationale, responsive/fallback checks, limitations and unresolved questions. The next task reads these files before changing visual language; source UX updates require mapping checks and a new UI revision, not erased history. Scratch is temporary; accepted decisions and concepts persist.
