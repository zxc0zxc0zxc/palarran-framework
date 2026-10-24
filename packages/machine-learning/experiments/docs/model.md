# Choosing a model and training method

## Select by task and constraints

Preserve the existing stack unless there is a measured reason to change it. Compare at least the current/no-training baseline and an applicable trainable option, rather than only several LLMs. Consider quality on required languages/slices, weight availability, license/commercial restrictions, memory, training/inference cost, batch/online latency, privacy, context/image size and reproducibility. Current leaderboard and model-card figures remain publisher claims until a local benchmark.

| Task | Starting point | When to add complexity |
| --- | --- | --- |
| Tabular classification/regression | Heuristic, linear/logistic, tree boosting in the existing stack | When error analysis identifies feature/model limitations; compare a neural model on the same splits |
| Time series | Last value/seasonal naive, linear/statistical baseline, temporal features | With sustained improvement in rolling backtests; future covariates must be available at prediction time |
| Ranking/retrieval | Lexical/BM25, frozen embeddings, a simple ranking model | Domain encoder/reranker finetuning with relevant positive/hard-negative data |
| CV/audio | Pretrained backbone + frozen features/linear head | Unfreeze/adapter/full transfer if data and compute suffice; split by subject/session |
| LLM structured tasks | Prompt/few-shot/parser baseline, a suitable small pretrained model | SFT/LoRA for a stable task/label quality; forgetting guardrails |
| LLM current knowledge | Retrieval and source-grounding baseline | Finetuning does not replace an up-to-date knowledge store; evaluate retrieval and generation separately |

This is our decision map, not a claim that one type is always best. [Chip Huyen](https://huyenchip.com/2023/04/11/llm-engineering.html) discusses prompting/finetuning/embeddings and cost/latency trade-offs; transfer the comparative approach, not 2023 prices or model recommendations.

## Training methods

**Feature/head training:** an inexpensive test of representation usefulness. **Full finetuning:** all trainable weights, more optimizer state/overfitting risk; justify with data and a baseline. **LoRA:** trainable low-rank updates to a frozen backbone; record rank/alpha/dropout/target modules, trainable count and trainable embeddings/head. [LoRA paper](https://arxiv.org/abs/2106.09685). **QLoRA:** quantized frozen backbone + adapters; lower memory does not guarantee less wall time or full kernel/hardware support. [QLoRA paper](https://arxiv.org/abs/2305.14314), [PEFT reference](https://huggingface.co/docs/peft/main/package_reference/lora).

**Continued pretraining:** justified by a domain corpus/language shift and a separate downstream test, not a wish to “add a few facts.” **Training from scratch:** a research/narrow specialist task or demonstrated absence of a suitable pretrained model, with a full data/compute budget. **Preference optimization/RL:** only with defined preference/reward data, reward-hacking checks and a cheaper SFT baseline; not the default. **Distillation:** separately account for teacher license, generation cost, privacy and an independent held-out real-data test. Success on synthetic teacher labels is not ground truth.

## Resource envelope before GPU use

Break VRAM into weights, gradients, optimizer/master states, activations, temporary workspaces, communication buffers and allocator reserve. `parameters × bits/8` describes weights only. For adapters, the frozen base remains in memory; activations depend on batch/sequence, and quantization metadata also costs memory. Mixed precision, gradient checkpointing, microbatch/accumulation, packing and sharding change speed/quality trade-offs. For sequence models, check attention/kernel behavior on the selected version; do not promise universal quadratic/linear savings without an implementation.

Record effective batch: microbatch × accumulation × data-parallel replicas; do not count tensor/model-parallel GPUs as additional independent examples. The learning-rate schedule depends on actual updates/tokens, not only epochs. Store estimates separately from measured peak memory/throughput; unknown fit needs a bounded pilot, not an automatic upgrade to a more expensive GPU.

## Output and verification

The model report includes owner/repo/revision/license and task applicability, tokenizer/chat template/special tokens/context/truncation policy, preprocessing, method/hyperparameter candidates, serving artifact format, alternatives and rejection reasons. Pin commit/weights/tokenizer/dependency versions; `trust_remote_code`, custom kernels and pickle/checkpoint deserialization require source/code review and isolation before execution. Do not execute arbitrary model code just to read its card.

Karpathy's [nanochat](https://github.com/karpathy/nanochat) and [llm.c](https://github.com/karpathy/llm.c) are useful readable reference harnesses/performance experiments. Their cost/throughput does not automatically transfer to Modal. The author marks [nanoGPT](https://github.com/karpathy/nanoGPT) as outdated: use it historically, not as the default new production stack. DoD: explain the choice, make rights/refs/resource risks explicit, include at least one real baseline; further runs require separate authorization.
