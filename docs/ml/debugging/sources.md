# Источники диагностики

Inspected: **2026-10-23**. Research papers/blogs — author reports; vendor docs — API/definitions, не evidence нашего запуска. Versioned references не требуют менять installed stack. Publication unknown оставляется unknown, не заменяется датой чтения.

| E-ID | Первичный источник | Дата/version | Что переносим и где граница |
| --- | --- | --- | --- |
| E-DBG-001 | Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Tiny-set/debugging и fixed-example dynamics; historical blog, не готовый современный trainer |
| E-DBG-002 | Google / Zinkevich, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | live guide; original date unknown | Pipeline/baseline/skew checks; наши numeric thresholds из этого не следуют |
| E-DBG-003 | HF, [Perplexity of fixed-length models](https://huggingface.co/docs/transformers/v4.57.1/en/perplexity) | Transformers v4.57.1; publication unknown | Autoregressive PPL, tokenization/context/stride; not DPO/diffusion quality |
| E-DBG-004 | HF, [GenerationConfig](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation) | v4.57.1; publication unknown | Decode parameters/length/stop identity; API не доказывает semantic completeness |
| E-DBG-005 | PyTorch, [clip_grad_norm_](https://docs.pytorch.org/docs/2.9/generated/torch.nn.utils.clip_grad_norm_.html) | 2.9 | Gradient norm/nonfinite semantics; один threshold не универсален |
| E-DBG-006 | PyTorch, [AMP recipe](https://docs.pytorch.org/tutorials/recipes/recipes/amp_recipe.html) | live tutorial; exact publication unknown | Unscale перед inspection/clipping, scaler/skip semantics; установить target-version API отдельно |
| E-DBG-007 | scikit-learn, [Model evaluation](https://scikit-learn.org/1.7/modules/model_evaluation.html) | 1.7 docs (rendered 1.7.2) | Class/regression/ranking scoring, denominators; applicability зависит от prediction unit |
| E-DBG-008 | scikit-learn, [Calibration](https://scikit-learn.org/1.7/modules/calibration.html) | 1.7 docs | Reliability/proper scoring; Brier включает несколько факторов, не чистая calibration error |
| E-DBG-009 | Chen et al., [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374v2) | 2021-07-07 v1; 2021-07-14 v2 | Functional code evaluation/pass@k; sampled setup/isolated execution нужны отдельно |
| E-DBG-010 | Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | 2024-03-29 | Error analysis, task-specific checks, наблюдаемые traces; judge не ground truth |
| E-DBG-011 | MLflow, [Experiment Tracking](https://mlflow.org/docs/latest/ml/tracking/) | live docs; publication unknown | Метрики/параметры/артефакты; внешний tracker опционален, не подключён |
| E-DBG-012 | TorchMetrics, [FID](https://lightning.ai/docs/torchmetrics/stable/image/frechet_inception_distance.html) | live docs (rendered 1.9.0) | Feature/preprocessing/sample basis фиксировать; FID не полная оценка image fidelity/условной корректности |

Продолжение [ML sources](../sources.md) и [data sources](../data/sources.md). Определения формул/метрик опираются на эти источники; threshold calibration, enum состояний, storage policy, budget hierarchy, report lifecycle и task DAG — рекомендации ai-tools. Чужой пример кода/цифры не copied benchmark и не гарантия качества.
