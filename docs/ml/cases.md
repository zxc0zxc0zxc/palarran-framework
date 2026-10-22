# Исследовательские кейсы: что переносим и что проверяем

Это карта применимости, а не список авторитетов вместо эксперимента. Даты/версии в [sources](sources.md). Работы исследователя не равны официальной политике его работодателя; reported результаты не наши наблюдения.

| Источник | Что в нём полезно | Наша адаптация | Предел переносимости |
| --- | --- | --- | --- |
| Karpathy, [Recipe](https://karpathy.github.io/2019/04/25/recipe/) | Data-first диагностика, simple baseline, tiny-set fit, постепенное усложнение | Correctness gate до дорогого pilot | Советы 2019 о конкретных моделях/unsupervised не современный default |
| Karpathy, [nanochat](https://github.com/karpathy/nanochat) | Компактный end-to-end research harness и cost-aware experiments | Явные стадии/tokenizer/config/eval, воспроизводимые resource measurements | Авторский cost и «GPT-2 capability» относятся к указанным setup/metric, не равны frontier model или Modal quote |
| Karpathy, [llm.c](https://github.com/karpathy/llm.c) | Прозрачность training loop и performance engineering | Профилировать полезный throughput, проверять optimization correctness | Не переписывать существующий trainer в C/CUDA без измеренной нужды |
| Google, [Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | Simple pipeline, metrics, training-serving skew | No-training baseline и tests окружения ML | Bigtech data scale не предпосылка маленького проекта |
| Lilian Weng, [Human Data Quality](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) | Annotation design, raters и причины disagreement | Rubric/calibration/quality audit с provenance | Majority vote не всегда единственно верная label |
| Sebastian Raschka, [LoRA experiments](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms) | Практические trade-offs adapter settings/data/memory/runtime | Небольшие абляции rank/modules и regression checks | Reported проценты экономии и runtime не переносить на другую модель/GPU |
| Chip Huyen, [LLM engineering](https://huyenchip.com/2023/04/11/llm-engineering.html) | Evaluation, cost/latency, альтернативы finetuning | Выбор prompt/retrieval/train по задаче | Исторические цены/модели требуют обновления |
| Hamel Husain, [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) | Evaluation по реальным ошибкам продукта | Error taxonomy + small representative eval set | Авторские кейсы не подтверждают качество нашей разметки/judge |
| Hu et al., [LoRA](https://arxiv.org/abs/2106.09685); Dettmers et al., [QLoRA](https://arxiv.org/abs/2305.14314) | Методы адаптации/quantized training | Метод как кандидат при VRAM constraints | Paper benchmarks не гарантия качества/fit нашего context |
| Hoffmann et al., [Chinchilla](https://arxiv.org/abs/2203.15556) | Связь data/model/compute при pretraining | Учитывать данные и вычисления совместно | Scaling recipe для pretraining не формула оптимальных SFT tokens/epochs |
| Stanford CRFM, [HELM](https://arxiv.org/abs/2211.09110) | Несколько осей оценки, явное coverage | Сценарии/slices/robustness/efficiency | Один общий leaderboard не заменяет domain holdout |

В каждом результате назови применённые 1–3 relevant cases, механизм переноса и что осталось hypothesis. Не нужно загружать все статьи заново на каждом этапе: сохраняй E-IDs/даты/краткие выводы и переиспользуй immutable evidence. Перед current price/API/model choice обновляй именно изменчивые факты. Неиспользованный источник в bibliography не аргумент решения.
