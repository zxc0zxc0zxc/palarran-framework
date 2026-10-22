# Научная база и пределы переноса

Проверено 2026-10-23; ниже зафиксированы initial и inspected revisions. Paper/author report не наше воспроизведение. Рекомендации ai-tools и toy recipe не приписывать авторам.

| E-ID | Первоисточник | Дата/version | Применение и предел |
| --- | --- | --- | --- |
| E-DATA-001 | Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Осмотреть данные и ошибки до масштабирования; блог, не универсальная современная архитектура |
| E-DATA-002 | Lee et al., [Deduplicating Training Data Makes Language Models Better](https://arxiv.org/abs/2107.06499v2) | initial 2021-07-14; v2 2022-03-24 | Дубликаты/пересечения и memorization; exact hash в нашем CLI не воспроизводит substring/near-dedup paper |
| E-DATA-003 | Penedo et al., [RefinedWeb](https://arxiv.org/abs/2306.01116v1) | 2023-06-01 v1 | Фильтрация/дедуп web corpus; не переносить English heuristics на все языки/код |
| E-DATA-004 | Xie et al., [DoReMi](https://arxiv.org/abs/2305.10429v4) | initial 2023-05-17; v4 2023-11-21 | Domain reweighting через обученный proxy; наш арифметический planner не реализует DoReMi и не оптимизирует веса |
| E-DATA-005 | Soldaini et al., [Dolma](https://arxiv.org/abs/2402.00159v2) | initial 2024-01-31; v2 2024-06-06 | Прозрачные источники/состав/curation tools; web-scale corpus не предпосылка небольшого SFT |
| E-DATA-006 | Penedo et al., [FineWeb](https://arxiv.org/abs/2406.17557v2) | initial 2024-06-25; v2 2024-10-31 | Абляции filtering/dedup и FineWeb-Edu; образовательный score не универсальная мера полезности всех доменов |
| E-DATA-007 | Li et al., [DataComp-LM](https://arxiv.org/abs/2406.11794v4) | initial 2024-06-17; v4 2025-04-21 | Контролируемое сравнение data curation и evaluation; переносить метод эксперимента, не чужой leaderboard |
| E-DATA-008 | Conneau et al., [XLM-R](https://arxiv.org/abs/1911.02116v2) | initial 2019-11-05; v2 2020-04-08 | Multilingual transfer/capacity dilution, smoothed sampling; masked LM не decoder-only SFT, исторический alpha не default |
| E-DATA-009 | Zhou et al., [LIMA](https://arxiv.org/abs/2305.11206v1) | 2023-05-18 v1 | Качество/разнообразие instruction examples; 1000 примеров — setup авторов, не норма объёма и не гарантия сохранения skills |
| E-DATA-010 | Luo et al., [Catastrophic Forgetting During Continual Fine-tuning](https://arxiv.org/abs/2308.08747v5) | initial 2023-08-17; v5 2025-01-05 | Domain, reasoning, reading regression и general instruction adaptation; ни LoRA, ни replay не доказательство нулевого forgetting |
| E-DATA-011 | Lambert et al., [Tülu 3](https://arxiv.org/abs/2411.15124v5) | initial 2024-11-22; v5 2025-04-14 | Multi-skill post-training, development/unseen evaluation и decontamination; не копировать recipe без model/task compatibility |
| E-DATA-012 | Hugging Face, [TRL SFT Trainer](https://huggingface.co/docs/trl/v0.23.0/en/sft_trainer) | versioned v0.23.0, publication unknown, inspected 2026-10-23 | max_length, assistant loss и packing semantics; reference version, не рекомендация pin/downgrade проекта |
| E-DATA-013 | Hugging Face, [Chat templates](https://huggingface.co/docs/transformers/v4.57.1/chat_templating) | versioned v4.57.1, publication unknown, inspected 2026-10-23 | Model-specific control tokens/train vs generation; installed version и actual template нужно сверять |

Минимальные внутренние E/H/ADR связи: цель → почему выбран источник → какой preprocessing/sampling hypothesis → какой independent gate. Не превращать reported gain авторов в ожидаемый gain нашего обучения. Новые corpora/LLM judges требуют отдельных прав/бюджета; ссылки не разрешают скачать данные или использовать лицензии автоматически.

E-DATA-014: Hugging Face [Tokenizers Python API](https://huggingface.co/docs/tokenizers/python/latest/api/reference.html), publication unknown, inspected 2026-10-23. `from_file`, offsets, explicit special-token/padding/truncation semantics; actual installed library version pins обязательны.
