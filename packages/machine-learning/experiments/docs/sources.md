# Primary ML sources

URL/available-content check date: **2026-10-20**. `live` means mutable documentation/README, not an integration or verified API operation. An absent publication/update date is unknown, not retrieval date. For a concrete experiment pin commit/release/model/data revision and recheck tariffs/SDKs/licenses. These are primary author publications, papers and tool-owner documentation. Other runs' figures are not our measurements.

| E-ID | Author/owner, source | Publication/version basis | Application and limits |
| --- | --- | --- | --- |
| E-ML-001 | Andrej Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Diagnostics/experiment sequence; historical model advice is not universal |
| E-ML-002 | Karpathy, [nanochat](https://github.com/karpathy/nanochat) | live README, target commit not yet selected | End-to-end research harness; author cost/capability is setup-specific |
| E-ML-003 | Karpathy, [llm.c](https://github.com/karpathy/llm.c) | live repo | Training-performance reference, not a ready target stack |
| E-ML-004 | Karpathy, [nanoGPT](https://github.com/karpathy/nanoGPT) | live README reports deprecation/update Nov 2025 | Readable historical loop; not a new default |
| E-ML-005 | Martin Zinkevich / Google, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | live guide, exact publication unknown | Baselines/pipeline/skew; adapt scale |
| E-ML-006 | Lilian Weng, [Thinking about High-Quality Human Data](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) | 2024-02-05 | Quality/raters/disagreement; review, not a dataset audit |
| E-ML-007 | Lilian Weng, [Extrinsic Hallucinations in LLMs](https://lilianweng.github.io/posts/2024-07-07-hallucination/) | 2024-07-07 | Factuality taxonomy, not a ready target metric |
| E-ML-008 | Sebastian Raschka, [Practical Tips for Finetuning LLMs Using LoRA](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms) | 2023-11-19 | Author experiments, settings/quality/runtime trade-offs; not universal defaults |
| E-ML-009 | Chip Huyen, [Building LLM applications for production](https://huyenchip.com/2023/04/11/llm-engineering.html) | 2023-04-11 | Eval/cost/latency and alternatives; old prices/models are not current |
| E-ML-010 | Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | live article, publication not recorded in register | Error-driven evaluation; author cases are not our success |
| E-ML-011 | Hu et al., [LoRA](https://arxiv.org/abs/2106.09685v2) | 2021-10-16 v2; initial 2021-06-17 | Low-rank adaptation; paper scope/benchmarks |
| E-ML-012 | Dettmers et al., [QLoRA](https://arxiv.org/abs/2305.14314) | 2023-05-23 v1 | Quantized backbone/adapters; hardware/data-specific results |
| E-ML-013 | Hoffmann et al., [Training Compute-Optimal LLMs](https://arxiv.org/abs/2203.15556) | initial 2022-03-29, target version pin needed | Pretraining compute/data trade-offs, not an SFT sizing law |
| E-ML-014 | Liang et al., [HELM paper](https://arxiv.org/abs/2211.09110) | initial 2022-11-16, target version pin needed | Holistic evaluation/coverage, not a universal business benchmark |
| E-ML-015 | EleutherAI, [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | live repo | LLM evaluation tool; pin task configs/commit |
| E-ML-016 | scikit-learn, [Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | stable docs live | Train-only fit/leakage; check installed version |
| E-ML-017 | Hugging Face, [Dataset Cards](https://huggingface.co/docs/hub/datasets-cards) | live docs | Provenance/limitations/metadata, not source-license verification |
| E-ML-018 | Hugging Face, [PEFT LoRA reference](https://huggingface.co/docs/peft/main/package_reference/lora) | main docs live | Config/API, not automatically a stable release |
| E-ML-019 | Hugging Face, [Trainer](https://huggingface.co/docs/transformers/main/en/trainer) | main docs live | Training/eval/checkpoint API; pin a release for the target |
| E-ML-020 | PyTorch, [Reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html) | versioned 2.9 guide | Seed/determinism limitations; not a downgrade recommendation |
| E-ML-021 | MLflow, [ML Experiment Tracking](https://mlflow.org/docs/latest/ml/tracking/) | latest docs live | Parameters/metrics/artifacts; remote tracking is not connected |
| E-ML-022 | Modal, [Pricing](https://modal.com/pricing) | live tariff retrieved 2026-10-20 | Per-resource rates/product distinctions; not an invoice/available credit |
| E-ML-023 | Modal, [Resources](https://modal.com/docs/guide/resources) | live docs | Physical cores, RAM/disk requests/limits/billing; not requested usage alone |
| E-ML-024 | Modal, [Volumes](https://modal.com/docs/guide/volumes) | live docs | Durability/commit/reload, storage charges; verify API/product version |
| E-ML-025 | Modal, [Timeouts](https://modal.com/docs/guide/timeouts) | live docs | Per-attempt execution/startup limits, not a total-run cap |
| E-ML-026 | Modal, [Failures and retries](https://modal.com/docs/guide/retries) | live docs | Exception-retry semantics and attempt costs |
| E-ML-027 | Modal, [Preemption](https://modal.com/docs/guide/preemption) | live docs | Same-input restart/checkpoint tolerance; retries=0 does not prove no restart |
| E-ML-028 | Modal, [Budgets](https://modal.com/docs/guide/budgets) | live docs | Workspace/environment controls; verify account privileges/scope |
| E-ML-029 | Modal, [Billing](https://modal.com/docs/guide/billing) | live docs | Provider billing/account basis; connection and invoices not verified |

Retrieval limitations: PyTorch `/stable/notes/randomness.html` redirected without content; the available versioned 2.9 page was used, not a future-project version pin. The HELM dashboard's dynamic content was not read; the basis is the paper. Unchecked URLs are not inspected evidence. Before copying snippets verify license/commit/attribution; copied code does not replace checks.

Our workflow schemas, artifact contracts, risk/stop policies and profile decision tables are Palarran architectural recommendations requested by the user. Do not attribute them to article authors/Modal or present documentation checks as trained/benchmarked results.

## Runtime addition — 2026-10-22

E-ML-027 (Modal preemption) and E-ML-025 (timeouts) rechecked 2026-10-22: restarts and per-attempt duration require a separate remote supervisor; local kill does not mean remote cancellation. E-ML-030: Amazon Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), live article, publication unknown, retrieved 2026-10-22. Application: stable identity/reconciliation, not an exactly-once promise. Local-only backend, approvals and reserve allocation are our scale-aware choices for the current Python/SQLite runtime.
| E-ML-031 | Modal, [Sandbox SDK](https://modal.com/docs/sdk/py/latest/Sandbox) | live, retrieved 2026-10-22 | Named identity, GPU, hard lifetime, poll/terminate; not live integration |
| E-ML-032 | Modal, [Volume SDK](https://modal.com/docs/sdk/py/latest/Volume) | live, retrieved 2026-10-22 | Streaming read/commit visibility; remote writer owns durability |
| E-ML-033 | Modal, [Billing](https://modal.com/docs/guide/billing) | live, retrieved 2026-10-22 | Provider billing versus estimates/invoices; workspace totals are not job attribution |
| E-ML-034 | Modal, [Sandbox filesystem](https://modal.com/docs/guide/sandbox-files) | live, retrieved 2026-10-22 | Background/final commits, explicit sync only Volume v2; no in-sandbox credentials needed |

## Data curation addition — 2026-10-23

The separately verified [E-DATA-001..013 register](data/sources.md) includes Karpathy, Lee dedup, RefinedWeb/FineWeb/Dolma/DCLM, DoReMi, XLM-R, LIMA, catastrophic forgetting, Tülu 3 and versioned tokenizer/trainer docs with dates, applicability and limitations. Paper gains are not our observations or default mixing ratios.

## Training debugging design — 2026-10-23

[Verified E-DBG-001..012 register](debugging/sources.md): Karpathy/fixed examples, Google pipeline practice, HF PPL/GenerationConfig, PyTorch gradients/AMP, sklearn metrics/calibration, functional code evaluation, Hamel error analysis, MLflow and FID limitations. These justify the design, not new training measurements.
