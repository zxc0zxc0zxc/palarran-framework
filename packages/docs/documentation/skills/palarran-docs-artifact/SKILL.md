---
name: palarran-docs-artifact
description: Create a portable responsive HTML feature-review handoff from actual plans, decisions and verification evidence. Use for /palarran:docs:artifact; --plan prepares scope only without reading inputs or writing files.
---

# Feature review artifact

Read the [artifact guide](../../docs/artifact.md), [domain contracts](../../../../core/agents/docs/domain-contracts.md), [decision memory](../../../../core/agents/docs/decision-memory.md) and [global memory](../../../../core/agents/docs/global-memory.md) before work. Outside `--plan`, read target AGENTS, locale preferences, private index and relevant accepted decisions. In `--plan`, use visible context only without target/input reads. Skill checkout and target root differ.

Use `/palarran:docs:artifact {description?}`. With no description, select the actual current visible feature, then latest identifiable feature. Ask only if unrelated candidates remain. Never invent context. `--plan` performs no target/input reads, writes, execution or external calls; return the scope, proposed evidence and remaining questions from visible context only.

For rendering, inspect the real source plan/revision/diff and observed tests within authorized local scope. Tell a short connected story: the concrete pain, what changed, the reasons, what evidence shows and what the reviewer should do. Organize it as What/Why/How/Results, with readiness, env **names**, test prerequisites/steps, evidence and remaining risks. Use a concrete example or before/after only when actual source evidence supports it. Avoid sterile labels, canned prose and invented business outcomes. Include meaningful provided flows/metrics, with source, units, denominator and uncertainty; unknown remains null, not zero. Distinguish observed/target/estimate and NOT_RUN. Preserve decision IDs and rationale in target `.palarran/`, with index and handoff updates before dependent choices. Global memory unavailable/offline means DEFERRED.

Resolve the existing `languages.docs` preference from project configuration and the global fallback, following established missing-config handling; do not add a new artifact-language setting. Supply exactly `en`, `ru` or `sr-Latn` in input `language`. Author every narrative field in that language; the renderer localizes all fixed interface text. Produce one artifact in the resolved project language, without a language selector or multilingual bundles. Preserve exact technical identifiers, metric facts, evidence IDs and unknowns. Canonical skill/code remains English. Prepare the guide's structured JSON in private ignored storage, review it for the intended recipient, then set its approval/privacy declarations. Explicitly approved input only:

```sh
python3 <library>/packages/docs/documentation/render.py --approved --input /private/approved.json --target /chosen/project
```

Output is new `artifacts/<feature>/index.html`; never overwrite an earlier artifact. Do not include secrets, private URLs, logs, customer data or raw sessions. The privacy flag is a declaration, not automatic secret detection. No external publication, MR post, deploy, model generation or app edits are authorized.

Open the generated file in a real browser and inspect desktop/mobile, keyboard controls, filters, diagrams, the resolved project language and missing-data states. Record exact source revision/output hash/viewports/checks and NOT_RUN gaps in the target handoff. A generated page or successful static test is not visual acceptance. Return the artifact path, readiness and material gaps concisely; no fabricated metrics or render evidence.
