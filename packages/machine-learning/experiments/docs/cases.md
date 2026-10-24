# Research cases: what transfers and what needs checking

This is an applicability map, not a list of authorities replacing experiments. Dates/versions are in [sources](sources.md). A researcher's work is not their employer's official policy; reported results are not our observations.

| Source | Useful mechanism | Our adaptation | Transfer limits |
| --- | --- | --- | --- |
| Karpathy, [Recipe](https://karpathy.github.io/2019/04/25/recipe/) | Data-first diagnostics, simple baseline, tiny-set fit, gradual complexity | Correctness gate before an expensive pilot | Specific 2019 model/unsupervised advice is not a current default |
| Karpathy, [nanochat](https://github.com/karpathy/nanochat) | Compact end-to-end research harness and cost-aware experiments | Explicit stages/tokenizer/config/eval, reproducible resource measurements | Author cost and “GPT-2 capability” apply to stated setup/metrics, not a frontier model or Modal quote |
| Karpathy, [llm.c](https://github.com/karpathy/llm.c) | Transparent training loop and performance engineering | Profile useful throughput, verify optimization correctness | Do not rewrite an existing trainer in C/CUDA without measured need |
| Google, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | Simple pipeline, metrics, training-serving skew | No-training baseline and ML-environment tests | Big-tech data scale is not a small-project prerequisite |
| Lilian Weng, [Human Data Quality](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) | Annotation design, raters, causes of disagreement | Rubric/calibration/quality audit with provenance | Majority vote is not always the only correct label |
| Sebastian Raschka, [LoRA experiments](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms) | Practical adapter-settings/data/memory/runtime trade-offs | Small rank/module ablations and regression checks | Reported savings percentages/runtime do not transfer to another model/GPU |
| Chip Huyen, [LLM engineering](https://huyenchip.com/2023/04/11/llm-engineering.html) | Evaluation, cost/latency, alternatives to finetuning | Select prompt/retrieval/training by task | Historical prices/models need refresh |
| Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | Evaluate real product errors | Error taxonomy + small representative evaluation set | Author cases do not establish our annotation/judge quality |
| Hu et al., [LoRA](https://arxiv.org/abs/2106.09685); Dettmers et al., [QLoRA](https://arxiv.org/abs/2305.14314) | Adaptation/quantized-training methods | Candidate methods under VRAM constraints | Paper benchmarks do not guarantee quality/context fit |
| Hoffmann et al., [Chinchilla](https://arxiv.org/abs/2203.15556) | Data/model/compute relationship in pretraining | Consider data and compute together | A pretraining scaling recipe is not an optimal SFT-token/epoch formula |
| Stanford CRFM, [HELM](https://arxiv.org/abs/2211.09110) | Multiple evaluation axes, explicit coverage | Scenarios/slices/robustness/efficiency | A general leaderboard does not replace a domain holdout |

Each output names 1–3 applied relevant cases, the transfer mechanism and remaining hypotheses. Do not reload every article at each stage: retain E-IDs/dates/concise findings and reuse immutable evidence. Refresh specifically volatile facts before current price/API/model choices. An unused bibliography entry does not justify a decision.
