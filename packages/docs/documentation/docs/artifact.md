# Portable feature review artifact

`/palarran:docs:artifact {description?}` prepares a self-contained responsive HTML handoff answering **What, Why, How, Results**. Use the explicit subject, otherwise the current visible session's actual feature, otherwise its latest identifiable feature. If several unrelated subjects remain, ask one scoped question. Never invent hidden session context, implementation or verification.

Read the actual plan, accepted decisions, diff, source revision and observed checks. The artifact is a delivery snapshot; canonical architecture/API docs remain authoritative. Separate observed results, targets and estimates. Local tests never establish production SLA. Source IDs and links do not grant access.

## Quick start

For a small review, read this section, [input contract](#input-contract-version-1) when authoring the JSON, and [render and verify](#render-and-verify). Reuse the current task's summary and report; keep decision rationale inline there. One task-level index entry is enough. Separate context/ADR/handoff files are for a material architectural choice, handoff or a long-running task, not each render attempt. Read the bounded [task context entry](../../../core/agents/docs/task-context.md) and only the [review-artifact domain section](../../../core/agents/docs/domain-contracts.md#review-artifacts); do not load unrelated domains.

From the installed target project, validate input before rendering:

```sh
python3 .ai-tools/library/packages/docs/documentation/render.py --check --input /PRIVATE/approved.json
python3 .ai-tools/library/packages/docs/documentation/render.py --approved --input /PRIVATE/approved.json --target /ABSOLUTE/project
```

`--check` reads only its explicit JSON input, returns `VALIDATED_INPUT` with `writes: 0` and `network: false`, and never reads a target or changes ignores. It validates the same schema and approval/privacy declarations as rendering; it does not verify the claims. `--plan` remains zero input/target I/O. Default rendering creates a new `.palarran/docs/artifacts/<feature>/index.html`. In a Git target, rendering protects `.palarran/` with Git-local `info/exclude`; it never changes tracked `.gitignore`, untracks files or publishes the page. Inspect the scope before an authorized render. Non-Git target directories remain supported without Git initialization.

## Write a short human story

Start with the concrete difficulty the reviewer or user faced, then say what changed and how that helps. Explain the reason for the chosen approach, what the evidence actually shows and what the reviewer should do next. Use short connected paragraphs and everyday words; define technical terms once. The four sections organize that story, rather than inviting a list of sterile labels.

A before/after example is useful only when the source actually establishes both states. For example, if the diff shows an added export, explain what the exported page contains and how a reviewer opens it; do not claim it saves time without a measurement. A proposed feature remains proposed. Synthetic examples, unavailable production results, uncertain metrics and tests not run must stay explicit in every translation. Avoid invented business impact, canned enthusiasm and repeating the heading in the first sentence.

## One artifact in the project document language

Supported artifact locales are exactly `en`, `ru` and `sr-Latn`. The agent resolves the existing `languages.docs` preference from target project configuration and the global fallback, using established setup/missing-config handling, and puts that resolved locale in input `language`. Do not introduce a separate artifact-language setting. Renderer input is already approved and resolved: the renderer does not read configuration, translate text or call a model/service. Canonical source and this guide remain English.

Author the title, readiness, narrative, risks, test names/environments/steps/prerequisites/notes, metric names/units/sources/denominators/uncertainty, evidence descriptions and flow labels in the resolved document language. The renderer localizes every fixed interface label, including headings, statuses, unknown values, diagram/table captions, accessibility text, filters, reminders and footer. Technical identifiers, source revisions, evidence IDs and standard units remain exact. Preserve the same facts and unknowns; localization never authorizes invented results or translated identifiers.

An artifact has one language and no language selector or multilingual bundles. Existing version 1 input without `language` keeps the `en` default; the skill should always supply the resolved project locale. Unsupported locale tags and any bundle/translation fields are rejected. Validation checks schema and supported locale, not linguistic truth: the author reviews all supplied prose for the correct language, meaning, units and evidence. Do not silently insert English narrative into a localized artifact.

## Input contract (version 1)

The standard-library renderer `packages/docs/documentation/render.py` accepts a UTF-8 JSON object up to 128 KiB. Duplicate keys, unknown fields, invalid Unicode, control characters (except text newlines/tabs), nonfinite numbers and excessive collections/text are rejected. All fields below are required unless marked optional:

| Field | Meaning |
| --- | --- |
| `version` | Integer `1` |
| `language` (optional) | Exactly `en`, `ru` or `sr-Latn`; default `en` |
| `approved_for_render`, `privacy_reviewed` | Both literal `true`, set only after actual scoped review |
| `feature` | Lowercase slug, 1–64 ASCII letters/digits/hyphens, starting with a letter/digit |
| `title`, `revision`, `readiness` | Concise title, exact source revision or explicit unknown, honest readiness |
| `what`, `why`, `how`, `results` | Nonempty plain explanations, up to 8,000 characters each |
| `environment_names` | Up to 40 variable names, never their values |
| `risks` | Up to 40 remaining risks/blockers; empty means explicitly no recorded risks, not proven absence |
| `evidence` | Up to 60 objects: unique `id`, `description`, optional safe public `url` |
| `tests` | Up to 80 objects: `name`, `status` (`PASS`, `FAIL`, `NOT_RUN`, `INCONCLUSIVE`, `NA`), `environment`, nonempty `steps` list, `prerequisites` list, `evidence_ids` list; optional `note` (required rationale for `NA`) |
| `metrics` | Up to 40 objects: `name`, `value` (finite number or null), `unit`, `source`, `kind` (`observed`, `target`, `estimate`), `denominator`, `uncertainty` |
| `flow` | Object with `nodes` (up to 12 unique `{id,label}`) and `edges` (up to 24 `{from,to,label}` referring to existing nodes); both may be empty |

Every text is plain text, never HTML, JavaScript, Markdown execution or a file include. Node labels and edge labels are required nonempty text of at most120characters; an unlabeled relationship must be given a concise meaningful label, not an empty string. Long diagram labels wrap without silent truncation and have complete SVG titles and table equivalents. Most text fields allow 2,000 characters; IDs allow 64. At most 20 steps/prerequisites per test. Numeric values require supplied source and unit; denominator/uncertainty must be explicit, such as `n=12 requests` / `not measured`, or `not applicable: configuration limit`. Missing measurements use `null` and render as **Unknown**, never zero. Test distribution counts listed scenarios, not executions or an inferred coverage percentage. Independent metric cards avoid comparing incompatible units. A flow shows provided directed edges; it is not runtime tracing. Label proposed topology in its labels or How text.

Public links allow HTTPS DNS hosts only, without credentials, IP literals, local/private suffixes, query strings or nonstandard ports. This deliberately excludes private MR links; retain a safe textual evidence ID instead. An allowed domain is not proof that its contents are public or safe. Review recipient access and sanitization yourself. The privacy flag is a declaration, **not a DLP guarantee**: no tokens, private endpoints, raw logs, customer information or session archives in any field. The renderer reads no referenced files and performs no network requests.

Example shape (fixture data, not a claim about a real feature):

```json
{
  "version": 1, "approved_for_render": true, "privacy_reviewed": true,
  "feature": "review-export", "title": "Review export", "revision": "unknown: not supplied",
  "readiness": "Partial: browser review NOT_RUN",
  "what": "Export a review snapshot.", "why": "Give reviewers a portable handoff.",
  "how": "Render approved structured evidence locally.", "results": "No execution evidence supplied.",
  "environment_names": [], "risks": ["Browser verification remains NOT_RUN."],
  "evidence": [{"id": "E1", "description": "Approved specification"}],
  "tests": [{"name": "Open export", "status": "NOT_RUN", "environment": "local browser",
    "steps": ["Open index.html and use the section controls."], "prerequisites": ["Generated page"], "evidence_ids": ["E1"]}],
  "metrics": [{"name": "Load time", "value": null, "unit": "ms", "source": "No measurement supplied",
    "kind": "observed", "denominator": "unknown", "uncertainty": "not measured"}],
  "flow": {"nodes": [], "edges": []}
}
```

## Render and verify

Plan mode reads no input/target files, writes nothing and executes no external commands:

```sh
python3 packages/docs/documentation/render.py --plan
```

After authorized local artifact preparation and review:

```sh
python3 packages/docs/documentation/render.py --approved --input /private/approved.json --target /chosen/project
```

The existing target directory owns `.palarran/docs/artifacts/<feature>/index.html`; input JSON also belongs in private task storage. During an authorized render in Git, reviewed target-relative `.palarran/` exclusions are appended idempotently to Git-local `info/exclude`, preserving its previous bytes and tracked files. This is a documented local side effect of rendering, not part of `--check` or `--plan`. A pre-existing tracked private destination yields `tracked_private_output`; inspect it separately instead of automatically untracking or overwriting it. Non-Git targets need no ignore edit and are not initialized as repositories.

The renderer refuses existing output, arbitrary symlink components, non-directory parents and inputs outside the explicit input file. On macOS the verified system aliases `/tmp`, `/var` and `/etc` are supported; other symlinks remain rejected. A new revision needs a new feature slug. To hand off the page, explicitly copy the reviewed standalone HTML to the chosen recipient destination; rendering itself does not publish or create a second public export. Metadata checks do not protect against a hostile concurrent filesystem actor; use a trusted local directory.

### Diagnostics

Failures return safe structured JSON with `status`, `code`, schema `field` (or null) and a fixed `hint`. For example, an empty edge label reports `{"status":"REJECTED","code":"invalid_text","field":"flow.edges[0].label","hint":"Provide nonempty text within the documented length limit."}`. Input contents, URL credentials, paths from arbitrary exceptions and raw tracebacks are never echoed. CLI missing-argument errors identify the missing option; unreadable input is `input_unavailable`. A successful render retains the `Rendered: <path>` line for existing callers.

The page uses local CSS, native SVG and a fixed script for navigation, status filtering and a review checklist. Localized text is escaped as HTML; no input text is interpolated into JavaScript. No CDN, fonts, fetch, input JavaScript or external assets. Text/table equivalents remain available for diagrams and charts; all content is readable without JavaScript. A reviewer checklist is local page state, never test evidence or durable acceptance.

Open the file in a real browser. Check desktop/mobile, long Unicode text, focus/keyboard navigation, section controls, filters, checklist, the resolved project language (including narrative, captions and accessibility labels), missing-data states and diagram/table equivalence. Record exact output path/hash, source revision, viewport sizes, observed checks and remaining NOT_RUN in the target private handoff. File generation and static tests alone are not visual verification. No MR posting, deployment, app edits, model calls or external actions are implied.

Before accepted choices, follow target decision memory and applicable AGENTS. Reuse prior source/decision IDs, preserve superseded history, update the target index/handoff; do not save recipient data in the skill checkout. Use locale preferences for new artifact text while canonical skill/code remains English. Global recall/learning is separately policy-bound; offline/disabled is DEFERRED, not invented evidence.

Basis: the user-approved [artifact design](artifacts.md) (2026-10-24); shared [decision memory](../../../core/agents/docs/decision-memory.md) and [domain contracts](../../../core/agents/docs/domain-contracts.md). These are product requirements and engineering choices, not external benchmark claims.
