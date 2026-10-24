# Scientific preprints from experiments

`/palarran:science:preprint {experiment/report paths}` creates a reviewable LaTeX article draft from existing results. Default: analyze authorized local artifacts/write source; no training/reruns/paid judges/uploads/submission. First read [sources](sources.md), [evidence contract](evidence.md), [workflow](workflow.md), target decisions and domain experiment/protocol/benchmark.

Article: real title/author metadata, abstract, question/hypothesis, related work, methods/data/protocol, experimental setup/compute, results including negatives/failures, diagnostics/behavior examples, limitations/threats, reproducibility/data availability, AI-assistance disclosure, references and claim→evidence appendix. Never invent scientific novelty/statistical significance. Partial-run drafts remain partial with unavailable/missing results.

Report export: `python3 scripts/science_preprint.py --report /private/report.json --output /private/preprint-v001 --title 'Experiment report'`. Outputs main.tex + metrics.csv + evidence.json + source manifest; no overwrite/secret upload. This deterministic evidence draft is supplemented with source-grounded scientific explanation by the skill. Optional automatic pipeline generation uses the same helper without model calls.
