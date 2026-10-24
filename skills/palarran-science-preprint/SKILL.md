---
name: palarran-science-preprint
description: Create a LaTeX research report from existing experiments with verifiable results, references, limitations and claim-to-evidence mapping. Use for /palarran:science:preprint; no training/publication.
---

Shared cycle: before work and after checks follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:science:preprint {experiment/report paths}

First read [README](../../docs/science/README.md), [sources](../../docs/science/sources.md), [evidence](../../docs/science/evidence.md), [workflow](../../docs/science/workflow.md) and [decision-memory](../../docs/skills/decision-memory.md). Identify installed checkout separately from target. Read target README/AGENTS, INDEX/accepted decisions, experiment/protocol/data/model/config/benchmark and all-attempt reports. Never automatically run missing results.

Freeze question/hypothesis, baseline, protocol revision, selection policy, seeds/N/splits, units/denominators, compute/cost basis and gaps. Bind each claim to exact artifact/hash/evidence pointers; self-consistency does not prove evaluation independence. Research related work in primary sources; verify metadata/applicability, never invent citations/DOI/novelty/authors/significance/success. Preserve partial/negative/failed runs. Development probes are not heldout benchmarks. Do not include private outputs without disclosure permission.

Create a separate target LaTeX project with main.tex/tables/figures/references/evidence register. For new projects use available create_latex_project tools, otherwise a dedicated no-overwrite folder. With runtime reports start `python3 scripts/science_preprint.py --report /private/report.json --output /private/preprint-v001`; supplement this data-only draft with evidence-based explanations. Use the [neutral template](../../templates/science/main.tex)/[claim register](../../templates/science/claim-evidence.md). Include actual recorded charts, honest baseline comparisons, full limitations/AI-assistance disclosure. Never invent missing points/confidence intervals.

Compile with existing built-in/local compilers without shell escape/automatic installs; fix source errors and inspect PDF with available renderers. Missing compiler/viewer means NOT COMPILED / NOT VISUALLY REVIEWED. Compile success proves no scientific conclusions. Portable packages lack runtime/compiler: use the source helper and explicitly report unavailable checks.

Before dependent edits record rationale/alternatives/sources in target `.palarran/science/<task>/decisions/`; update INDEX/coverage/handoff. Complete samples/state/checkpoints remain private; Git contains authorized editorial artifacts only. Conclude with source/PDF paths, scope/results/limits, scientific checks, compile/visual status and remaining evidence. No submission, artifact publishing or new paid runs.
