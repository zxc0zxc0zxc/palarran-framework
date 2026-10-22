# Выбор модели и способа обучения

## Выбор по задаче и ограничениям

Сохрани существующий стек, если нет измеренной причины менять его. Сравни как минимум текущий/no-training baseline и применимый обучаемый вариант, а не только несколько LLM. Учитывай качество на нужных языках/срезах, availability weights, лицензию/коммерческие ограничения, memory, train/inference cost, batch/online latency, privacy, контекст/размер изображения и воспроизводимость. Текущий leaderboard и параметры из model card — заявления издателя до локального benchmark.

| Задача | С чего начать | Когда усложнять |
| --- | --- | --- |
| Tabular classification/regression | Heuristic, linear/logistic, tree boosting по существующему стеку | Если error analysis показывает ограничение признаков/модели; neural model сравнить на тех же splits |
| Time series | Last value/seasonal naive, linear/statistical baseline, temporal features | При устойчивом выигрыше rolling backtest; future covariates доступны в момент прогноза |
| Ranking/retrieval | Lexical/BM25, frozen embeddings, простая ranking model | Domain encoder/reranker finetune при релевантных positive/hard-negative данных |
| CV/audio | Pretrained backbone + frozen features/linear head | Unfreeze/adapter/full transfer, если данных и compute достаточно; split по субъекту/сессии |
| LLM structured tasks | Prompt/few-shot/parser baseline, небольшая подходящая pretrained model | SFT/LoRA при стабильной задаче/label quality; guardrails на забывание |
| LLM свежие знания | Retrieval и source grounding baseline | Finetune не заменяет актуальность knowledge store; оценить retrieval и generation отдельно |

Это наша decision map, а не утверждение, что один тип всегда лучший. [Chip Huyen](https://huyenchip.com/2023/04/11/llm-engineering.html) рассматривает prompting/finetuning/embeddings и trade-offs стоимости/latency; переносим сравнительный подход, не цены и model recommendations 2023 года.

## Training methods

**Feature/head training:** дешёвый способ проверить полезность представления. **Full finetuning:** все trainable weights, больше optimizer state/риск overfit; обосновать данными и baseline. **LoRA:** обучаемые низкоранговые обновления frozen backbone, фиксировать rank/alpha/dropout/target modules, trainable count и trainable embeddings/head. [LoRA paper](https://arxiv.org/abs/2106.09685). **QLoRA:** quantized frozen backbone + adapters; меньше memory не гарантирует меньше wall time или полную поддержку kernels/hardware. [QLoRA paper](https://arxiv.org/abs/2305.14314), [PEFT reference](https://huggingface.co/docs/peft/main/package_reference/lora).

**Continued pretraining:** оправдывается domain corpus/сдвигом языка и отдельным downstream test, не желанием «добавить пару фактов». **Training from scratch:** исследовательская/узкая специализированная задача либо доказанное отсутствие подходящей pretrained model, с полноценным data/compute budget. **Preference optimization/RL:** только при определённых preference/reward data, проверке reward hacking и более дешёвого SFT baseline; не default. **Distillation:** отдельно учитывать teacher license, generation cost, privacy и удержанный независимый real-data test. Успех на synthetic teacher labels не ground truth.

## Resource envelope до GPU

Разложи VRAM на weights, gradients, optimizer/master states, activations, temporary workspaces, communication buffers и allocator reserve. `parameters × bits/8` описывает только weights. Для adapters frozen base остаётся в памяти, activations зависят от batch/sequence; quantization metadata тоже не бесплатна. Mixed precision, gradient checkpointing, microbatch/accumulation, packing и sharding изменяют speed/quality trade-offs. Для sequence models attention/kernel behaviour проверяется на выбранной версии; не обещать универсальную квадратичную/линейную экономию без реализации.

Запиши эффективный batch: microbatch × accumulation × data-parallel replicas; tensor/model-parallel GPUs не считать дополнительными independent examples. Learning-rate schedule зависит от реального числа updates/tokens, не только epochs. Estimate и measured peak memory/throughput хранятся раздельно; unknown fit требует bounded pilot, не автоматическую замену на GPU дороже.

## Выход и проверка

Model report включает owner/repo/revision/license и применимость к задаче, tokenizer/chat template/special tokens/context/truncation policy, preprocessing, method/hyperparameter candidates, serving artifact format, alternatives и причины отказа. Pin commit/weights/tokenizer/dependency versions; `trust_remote_code`, custom kernels, pickle/checkpoint deserialization требуют проверки источника/кода и изоляции до исполнения. Не выполнять произвольный код модели ради чтения card.

Karpathy [nanochat](https://github.com/karpathy/nanochat) и [llm.c](https://github.com/karpathy/llm.c) полезны как читаемые reference harness/performance experiments. Их cost/throughput не переносится на Modal автоматически. [nanoGPT](https://github.com/karpathy/nanoGPT) помечен автором устаревшим: использовать как исторический пример, не default нового production stack. DoD: выбор объяснён, права/refs/ресурсные риски явны, минимум один реальный baseline, дальнейшие запуски отдельно разрешаются.
