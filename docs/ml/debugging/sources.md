# Diagnostic sources

Inspected: **2026-10-23**. Research papers/blogs are author reports; vendor docs provide APIs/definitions, not evidence of our run. Versioned references do not require changing the installed stack. Unknown publication dates stay unknown, never replaced by reading dates.

| E-ID | Primary source | Date/version | Transfer mechanism and boundary |
| --- | --- | --- | --- |
| E-DBG-001 | Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Tiny-set/debugging and fixed-example dynamics; historical blog, not a ready modern trainer |
| E-DBG-002 | Google / Zinkevich, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | live guide; original date unknown | Pipeline/baseline/skew checks; does not imply our numeric thresholds |
| E-DBG-003 | HF, [Perplexity of fixed-length models](https://huggingface.co/docs/transformers/v4.57.1/en/perplexity) | Transformers v4.57.1; publication unknown | Autoregressive PPL, tokenization/context/stride; not DPO/diffusion quality |
| E-DBG-004 | HF, [GenerationConfig](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation) | v4.57.1; publication unknown | Decoding parameters/length/stop identity; API does not prove semantic completeness |
| E-DBG-005 | PyTorch, [clip_grad_norm_](https://docs.pytorch.org/docs/2.9/generated/torch.nn.utils.clip_grad_norm_.html) | 2.9 | Gradient norm/nonfinite semantics; no universal threshold |
| E-DBG-006 | PyTorch, [AMP recipe](https://docs.pytorch.org/tutorials/recipes/recipes/amp_recipe.html) | live tutorial; exact publication unknown | Unscale before inspection/clipping, scaler/skip semantics; separately establish target-version API |
| E-DBG-007 | scikit-learn, [Model evaluation](https://scikit-learn.org/1.7/modules/model_evaluation.html) | 1.7 docs (rendered 1.7.2) | Classification/regression/ranking scoring, denominators; applicability depends on prediction unit |
| E-DBG-008 | scikit-learn, [Calibration](https://scikit-learn.org/1.7/modules/calibration.html) | 1.7 docs | Reliability/proper scoring; Brier mixes factors, not pure calibration error |
| E-DBG-009 | Chen et al., [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374v2) | 2021-07-07 v1; 2021-07-14 v2 | Functional code evaluation/pass@k; sampled setup/isolated execution required separately |
| E-DBG-010 | Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | 2024-03-29 | Error analysis, task-specific checks, observable traces; judges are not ground truth |
| E-DBG-011 | MLflow, [Experiment Tracking](https://mlflow.org/docs/latest/ml/tracking/) | live docs; publication unknown | Metrics/parameters/artifacts; external tracker optional and not connected |
| E-DBG-012 | TorchMetrics, [FID](https://lightning.ai/docs/torchmetrics/stable/image/frechet_inception_distance.html) | live docs (rendered 1.9.0) | Fix features/preprocessing/sample basis; FID does not fully evaluate image fidelity/conditional correctness |

Continues [ML sources](../sources.md) and [data sources](../data/sources.md). Formula/metric definitions rely on these sources; threshold calibration, state enums, storage policy, budget hierarchy, report lifecycle and task DAG are Palarran recommendations. Others' code/figures are not copied benchmarks or quality guarantees.
