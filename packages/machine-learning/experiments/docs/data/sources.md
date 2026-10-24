# Scientific basis and transfer limits

Checked 2026-10-23; initial and inspected revisions are recorded below. Papers/author reports are not our reproductions. Do not attribute Palarran recommendations/toy recipes to authors.

| E-ID | Primary source | Date/version | Application and limits |
| --- | --- | --- | --- |
| E-DATA-001 | Karpathy, [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/) | 2019-04-25 | Inspect data/errors before scaling; a blog, not a universal modern architecture |
| E-DATA-002 | Lee et al., [Deduplicating Training Data Makes Language Models Better](https://arxiv.org/abs/2107.06499v2) | initial 2021-07-14; v2 2022-03-24 | Duplicates/overlaps and memorization; CLI exact hashing does not reproduce paper substring/near-dedup |
| E-DATA-003 | Penedo et al., [RefinedWeb](https://arxiv.org/abs/2306.01116v1) | 2023-06-01 v1 | Web-corpus filtering/dedup; English heuristics do not transfer to every language/code |
| E-DATA-004 | Xie et al., [DoReMi](https://arxiv.org/abs/2305.10429v4) | initial 2023-05-17; v4 2023-11-21 | Domain reweighting through a trained proxy; our arithmetic planner neither implements DoReMi nor optimizes weights |
| E-DATA-005 | Soldaini et al., [Dolma](https://arxiv.org/abs/2402.00159v2) | initial 2024-01-31; v2 2024-06-06 | Transparent sources/composition/curation tools; web-scale corpora are not prerequisites for small SFT |
| E-DATA-006 | Penedo et al., [FineWeb](https://arxiv.org/abs/2406.17557v2) | initial 2024-06-25; v2 2024-10-31 | Filtering/dedup ablations and FineWeb-Edu; education scores do not universally measure every domain's usefulness |
| E-DATA-007 | Li et al., [DataComp-LM](https://arxiv.org/abs/2406.11794v4) | initial 2024-06-17; v4 2025-04-21 | Controlled data-curation/evaluation comparisons; transfer the experiment method, not another leaderboard |
| E-DATA-008 | Conneau et al., [XLM-R](https://arxiv.org/abs/1911.02116v2) | initial 2019-11-05; v2 2020-04-08 | Multilingual transfer/capacity dilution, smoothed sampling; masked LM is not decoder-only SFT, historical alpha is not default |
| E-DATA-009 | Zhou et al., [LIMA](https://arxiv.org/abs/2305.11206v1) | 2023-05-18 v1 | Quality/diversity of instruction examples; 1000 examples is the authors' setup, not a sizing rule or skill-preservation guarantee |
| E-DATA-010 | Luo et al., [Catastrophic Forgetting During Continual Fine-tuning](https://arxiv.org/abs/2308.08747v5) | initial 2023-08-17; v5 2025-01-05 | Domain, reasoning, reading regressions and general instruction adaptation; neither LoRA nor replay proves zero forgetting |
| E-DATA-011 | Lambert et al., [Tülu 3](https://arxiv.org/abs/2411.15124v5) | initial 2024-11-22; v5 2025-04-14 | Multi-skill post-training, development/unseen evaluation and decontamination; do not copy recipes without model/task compatibility |
| E-DATA-012 | Hugging Face, [TRL SFT Trainer](https://huggingface.co/docs/trl/v0.23.0/en/sft_trainer) | versioned v0.23.0, publication unknown, inspected 2026-10-23 | max_length, assistant loss and packing semantics; a reference version, not a project pin/downgrade recommendation |
| E-DATA-013 | Hugging Face, [Chat templates](https://huggingface.co/docs/transformers/v4.57.1/chat_templating) | versioned v4.57.1, publication unknown, inspected 2026-10-23 | Model-specific control tokens/train versus generation; check installed version and actual template |

Minimum internal E/H/ADR linkage: goal → source-selection reason → preprocessing/sampling hypothesis → independent gate. Do not turn author-reported gains into expected gains for our training. New corpora/LLM judges require separate rights/budgets; links do not authorize downloads or automatically confer licenses.

E-DATA-014: Hugging Face [Tokenizers Python API](https://huggingface.co/docs/tokenizers/python/latest/api/reference.html), publication unknown, inspected 2026-10-23. `from_file`, offsets, explicit special-token/padding/truncation semantics; actual installed-library version pins are mandatory.
