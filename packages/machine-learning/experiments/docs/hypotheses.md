# Training hypotheses and ablation design

A hypothesis connects a specific cause of an error to one change and a testable outcome. “Finetune the model and it will improve” provides no falsification condition. Start with authorized error analysis of existing predictions/aggregates and data constraints. If results do not yet exist, identify the proposed mechanism and a test of it.

## H-ID card

- **Observation/E-ID:** the observed error slice/constraint, number of examples and revision; otherwise unknown.
- **Mechanism:** why the change should help and what alternative cause might explain the error.
- **Intervention/control:** one principal factor, frozen split/config/baseline; what stays unchanged.
- **Prediction:** primary metric, direction, practically relevant delta and guardrails with numerical proposals.
- **Falsification:** the outcome that rejects the idea; inconclusive conditions and minimum size/precision.
- **Resources:** cheapest diagnostic, full test budget/attempt cap, wall time, inputs/outputs, priority.
- **Disposition:** proposed/ready/tested/supported/refuted/inconclusive with evidence; supported only within this protocol.

Karpathy recommends adding complexity gradually. Our adaptation: do not change the dataset, tokenizer, loss, LR and architecture simultaneously when the question concerns one factor. Interactions may use a predefined factorial design; the experiment pays for all combinations, not just the winner. Basis: [Recipe](https://karpathy.github.io/2019/04/25/recipe/).

## Examples, not reported results

| H-ID | Hypothesis | Inexpensive causal diagnostic | Main test |
| --- | --- | --- | --- |
| H-001 | Missing rare labels limit recall | Check label quality and frequency on train/validation | Data curation versus unchanged data at equal compute |
| H-002 | The LLM knows the task but violates the format | Prompt/few-shot + parser baseline, error taxonomy | SFT/LoRA versus the original model; format success and quality separately |
| H-003 | The retriever, rather than the generator, is inadequate | Recall@k on a fixed corpus | Improve retrieval versus finetuning the generator; generation guardrails |
| H-004 | Long context causes OOM/low throughput | Length histogram and memory pilot | Packing/bucketing versus the original loader, with the same effective tokens |

All outcome values remain unknown until measured. Set the budget, number of seeds and thresholds in the experiment spec.

## Selection and stopping

Rank hypotheses by evidence strength, expected practical benefit, cost of falsification and dependence on unavailable data. Do not present a subjective score as a probability of success. Plan negative/control tests: shuffled labels, broken input, no retrieval, frozen weights, where they diagnose a specific error rather than mechanically for every model type.

Raschka shows how LoRA results depend on rank/target modules/data and discusses regressions on other tasks. Use this to motivate testing configuration and forgetting on **your own** tasks, not as a universal rank/epoch count. [The author's experiment analysis](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms).

If the budget permits only one seed, record the reliability limitation; do not conclude stability. Search uses validation; keep the final test held out. After viewing the final test, new hypotheses require a new evaluation policy/holdout revision. Preserve negative results, early stops, the number of inspected variants and spending alongside successes; otherwise later agents may repeat expensive dead-end training.

DoD: every selected H-ID is falsifiable and has a control/metric/threshold/data/attempt cap; rejected ideas have reasons. Hypotheses do not launch a sweep themselves.
