# Scientific preprints по экспериментам

`/science:preprint {experiment/report paths}` создаёт reviewable LaTeX draft статьи по существующим результатам. Default — анализ разрешённых локальных artifacts и написание source; нет training/rerun/paid judge/upload/submission. Сначала [sources](sources.md), [evidence contract](evidence.md), [workflow](workflow.md), target decisions и профильные experiment/protocol/benchmark.

Статья: title/authors с реальными metadata, abstract, question/hypothesis, related work, methods/data/protocol, experimental setup/compute, results incl negative/failures, diagnostics/behavior examples, limitations/threats, reproducibility/data availability, AI assistance disclosure, references и appendix claim→evidence. Scientific novelty/статистическая значимость не выдумываются. Draft по partial run остаётся partial и содержит unavailable/missing results.

Report export: `python3 scripts/science_preprint.py --report /private/report.json --output /private/preprint-v001 --title 'Experiment report'`. Выход main.tex + metrics.csv + evidence.json + source manifest; no overwrite, no secret upload. Это deterministic evidence draft; skill затем дополняет научное объяснение только на основании sources. Автоматическая генерация pipeline опциональна и использует тот же helper без model call.
