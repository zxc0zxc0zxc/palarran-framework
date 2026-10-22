# Первичные источники ML

Дата проверки URL/доступного содержания: **2026-10-20**. `live` означает изменяемую документацию/README, а не интеграцию или проверку работоспособности API. Если публикация/update не указана — unknown, не дата retrieval. Для конкретного эксперимента зафиксировать commit/release/model/data revision и повторно проверить tariffs/SDK/лицензии. Источники ниже — первичные авторские публикации, papers и документация владельцев инструментов. Числа чужих runs не наши measurements.

| E-ID | Автор/владелец, источник | Publication/version basis | Применение и предел |
| --- | --- | --- | --- |
| E-ML-001 | Andrej Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Диагностика/порядок эксперимента; исторические model советы не универсальны |
| E-ML-002 | Karpathy, [nanochat](https://github.com/karpathy/nanochat) | live README, commit для target ещё не выбран | End-to-end research harness; cost/capability авторские и setup-specific |
| E-ML-003 | Karpathy, [llm.c](https://github.com/karpathy/llm.c) | live repo | Training performance reference, не готовый target stack |
| E-ML-004 | Karpathy, [nanoGPT](https://github.com/karpathy/nanoGPT) | live README сообщает deprecation/update Nov 2025 | Исторический читаемый loop; новый default не назначать |
| E-ML-005 | Martin Zinkevich / Google, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | live guide, точная publication unknown | Baselines/pipeline/skew; адаптировать масштаб |
| E-ML-006 | Lilian Weng, [Thinking about High-Quality Human Data](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) | 2024-02-05 | Quality/raters/disagreement; обзор, не dataset audit |
| E-ML-007 | Lilian Weng, [Extrinsic Hallucinations in LLMs](https://lilianweng.github.io/posts/2024-07-07-hallucination/) | 2024-07-07 | Factuality taxonomy; не готовая target metric |
| E-ML-008 | Sebastian Raschka, [Practical Tips for Finetuning LLMs Using LoRA](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms) | 2023-11-19 | Авторские experiments, settings/quality/runtime trade-offs; не универсальные defaults |
| E-ML-009 | Chip Huyen, [Building LLM applications for production](https://huyenchip.com/2023/04/11/llm-engineering.html) | 2023-04-11 | Eval/cost/latency и alternatives; старые prices/models не использовать как current |
| E-ML-010 | Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | live article, publication в register не зафиксирована | Error-driven eval; кейсы автора не наш success |
| E-ML-011 | Hu et al., [LoRA](https://arxiv.org/abs/2106.09685v2) | 2021-10-16 v2; initial 2021-06-17 | Low-rank adaptation; paper scope/benchmarks |
| E-ML-012 | Dettmers et al., [QLoRA](https://arxiv.org/abs/2305.14314) | 2023-05-23 v1 | Quantized backbone/adapters; hardware/data-specific results |
| E-ML-013 | Hoffmann et al., [Training Compute-Optimal LLMs](https://arxiv.org/abs/2203.15556) | initial 2022-03-29, target version pin needed | Pretraining compute/data trade-offs, не SFT sizing law |
| E-ML-014 | Liang et al., [HELM paper](https://arxiv.org/abs/2211.09110) | initial 2022-11-16, target version pin needed | Holistic evaluation/coverage, не универсальный business benchmark |
| E-ML-015 | EleutherAI, [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | live repo | LLM evaluation tool, task configs/commit обязательно pin |
| E-ML-016 | scikit-learn, [Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | stable docs live | Train-only fit/leakage; installed version сверить |
| E-ML-017 | Hugging Face, [Dataset Cards](https://huggingface.co/docs/hub/datasets-cards) | live docs | Provenance/limitations/metadata, не проверка лицензии источника |
| E-ML-018 | Hugging Face, [PEFT LoRA reference](https://huggingface.co/docs/peft/main/package_reference/lora) | main docs live | Config/API, не автоматически стабильная release |
| E-ML-019 | Hugging Face, [Trainer](https://huggingface.co/docs/transformers/main/en/trainer) | main docs live | Training/eval/checkpoint API, pin release для target |
| E-ML-020 | PyTorch, [Reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html) | versioned 2.9 guide | Seed/determinism limitations; не рекомендация downgrade |
| E-ML-021 | MLflow, [ML Experiment Tracking](https://mlflow.org/docs/latest/ml/tracking/) | latest docs live | Params/metrics/artifacts, remote tracking не подключён |
| E-ML-022 | Modal, [Pricing](https://modal.com/pricing) | live tariff retrieved 2026-10-20 | Per-resource rates/product distinction; не invoice/доступный credit |
| E-ML-023 | Modal, [Resources](https://modal.com/docs/guide/resources) | live docs | Physical cores, RAM/disk requests/limits/billing; не только requested usage |
| E-ML-024 | Modal, [Volumes](https://modal.com/docs/guide/volumes) | live docs | Durability/commit/reload, storage charges; API/product version проверить |
| E-ML-025 | Modal, [Timeouts](https://modal.com/docs/guide/timeouts) | live docs | Per-attempt execution/startup limits, не total-run cap |
| E-ML-026 | Modal, [Failures and retries](https://modal.com/docs/guide/retries) | live docs | Exception retry semantics и стоимость attempts |
| E-ML-027 | Modal, [Preemption](https://modal.com/docs/guide/preemption) | live docs | Restart same input/checkpoint tolerance; retries=0 не доказательство отсутствия restart |
| E-ML-028 | Modal, [Budgets](https://modal.com/docs/guide/budgets) | live docs | Workspace/environment controls, account privileges/scope проверить |
| E-ML-029 | Modal, [Billing](https://modal.com/docs/guide/billing) | live docs | Provider billing/account basis; подключение и invoice не проверены |

Retrieval limitations: `/stable/notes/randomness.html` у PyTorch вернул redirect без содержания, использована доступная versioned 2.9 страница; это не pin версии для будущих проектов. У HELM dashboard динамическое содержимое не прочитано — основание берётся из paper. Непроверенные URL не включаются как прочитанная evidence. Перед копированием snippets проверять license/commit/атрибуцию; копия кода не заменяет проверки.

Наши схемы workflow, artifact contracts, risk/stop policies и profile decision tables — архитектурные рекомендации ai-tools по запросу пользователя. Не приписывать их авторам статей/Modal и не выдавать документационную проверку за trained/benchmarked результат.

## Runtime дополнение — 2026-10-22

E-ML-027 (Modal preemption) и E-ML-025 (timeouts) повторно проверены 2026-10-22: restart и per-attempt duration требуют отдельного remote supervisor; local kill не означает remote cancellation. E-ML-030: Amazon Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/), live article, publication unknown, retrieved 2026-10-22. Применение — stable identity/reconciliation, не обещание exactly-once. Local-only backend, approvals и reserve allocation — наше решение по масштабу текущего Python/SQLite runtime.
| E-ML-031 | Modal, [Sandbox SDK](https://modal.com/docs/sdk/py/latest/Sandbox) | live, retrieved 2026-10-22 | Named identity, GPU, hard lifetime, poll/terminate; не live integration |
| E-ML-032 | Modal, [Volume SDK](https://modal.com/docs/sdk/py/latest/Volume) | live, retrieved 2026-10-22 | Streaming read/commit visibility; remote writer отвечает за durability |
| E-ML-033 | Modal, [Billing](https://modal.com/docs/guide/billing) | live, retrieved 2026-10-22 | Provider billing vs estimates/invoice; workspace totals не job attribution |
| E-ML-034 | Modal, [Sandbox filesystem](https://modal.com/docs/guide/sandbox-files) | live, retrieved 2026-10-22 | Background/final commits, explicit sync only Volume v2; no in-sandbox credentials needed |

## Data curation дополнение — 2026-10-23

Отдельный проверенный [реестр E-DATA-001..013](data/sources.md) содержит Karpathy, Lee dedup, RefinedWeb/FineWeb/Dolma/DCLM, DoReMi, XLM-R, LIMA, catastrophic forgetting, Tülu 3 и versioned tokenizer/trainer docs с датами, применимостью и ограничениями. Paper gains не наши observations и не default mixing ratios.

## Training debugging design — 2026-10-23

[Проверенный реестр E-DBG-001..012](debugging/sources.md): Karpathy/fixed examples, Google pipeline practice, HF PPL/GenerationConfig, PyTorch gradient/AMP, sklearn metrics/calibration, code functional evaluation, Hamel error analysis, MLflow и FID limitations. Это основания дизайна, не новые training measurements.
