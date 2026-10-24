# Distribution across domains, languages and lengths

[DoReMi](sources.md) demonstrates domain-weight usefulness in its proxy/full-pretraining setup. [XLM-R](sources.md) examines transfer versus multilingual-capacity dilution. Neither establishes universal 70/20/10 for our SFT. Every numerical Palarran recipe is a toy example or experiment hypothesis, not a best-known optimum.

## Joint distribution first

Budget in **actual model input tokens presented** after the real tokenizer/template, excluding padding. Also count loss-bearing assistant/target tokens: equal token mixtures can yield different gradient mixtures. Rows/characters/bytes help storage profiling but do not replace tokens. One long document may outweigh thousands of short ones; distinguish unique tokens from repeated exposure.

Maintain `domain × language × task/capability × answer_length × source × quality`, including sampled group, real/synthetic and split. Not every dimension needs a full Cartesian product: retain sparse support and unknowns. The basic v1 plan supports joint domain/language cells; other slices need separate review/samplers.

`q(d,l) = q(d) * q(l|d)` or an explicitly approved joint matrix; weights sum to 1. Do not multiply independent marginals into nonexistent cells (for example medical/sr without data). Each cell records owned inventory, desired exposure, minimum coverage, maximum effective repeats, source concentration and validation metrics. Missing data means BLOCKED/new collection/scope revision; no silent renormalization or endless copying of rare corpora.

## Patterns

| Scenario | Distribution pattern | Checks |
| --- | --- | --- |
| General assistant SFT | Balanced multi-skill coverage + explicit short and complete long-answer mixture | Instruction-following, promised reasoning/reading/code, length/completeness and refusal on valid questions |
| Specialist adaptation | Specialist + authorized general anchors/replay, several predefined shares | Target gains and general-holdout non-inferiority; replay does not guarantee no forgetting |
| Multilingual | Language floors, joint coverage within domains, confidence/und/mul, balanced evaluation | Per-language quality, tokenizer fertility, low-resource over-repetition, code switching |
| Multiple domains with unequal volume | Capped domain exposure; proxy/adaptive weights as a separate expensive hypothesis | Not just overall loss: worst slice, unique groups and source dominance |
| Long-context / multi-turn | Sufficient complete long responses and coherent dialogues, format-aware buckets | Answer endings, preserved facts/code/structure; packing-boundary tests |
| Continual updates | Mix new information with preserved task anchors in fixed stages | New/old tasks separately, forgetting curve, data/version drift |

Possible smoothing hypothesis: `q(l) ∝ p(l)^alpha`, `0 < alpha <= 1`; alpha=1 reproduces original shares, smaller alpha increases rare-language relative exposure. This neither means equal quality, solves missing data nor mandates XLM-R's alpha. If p(l)=0, smoothing does not create data. Maximum repeats and rights still apply after smoothing.

## Exposure and shuffle

For each cell `target_tokens = total_train_tokens * q(d,l)`, `effective_epochs = target_tokens / unique_available_tokens`. This is a document-sampler planning approximation, not a count of independent samples. Detect capacity overflow, duplicates/repetition and source-specific reuse before launch. Domain/language floors are explicit; averages must not hide incomplete coverage.

Shuffle train at sample/group level with reproducible seeds across all shards/ranks; do not run one English epoch then Russian merely because of file ordering. Intentional curricula need separate hypotheses and forgetting checks. Distributed sampler/resume records global step/RNG/position; bucketing must not systematically drop long answers, tail batches or rare languages. A microbatch need not contain every language; monitor realized rolling token exposure and loss weights.

v1 mix-plan computes joint token quotas/floors/repeat caps; it neither samples nor trains. Check source/length/task composition and actual sampler exposure separately before training-ready. The toy template is deliberately not a default. Select weights on dev only under a separately agreed budget; test is not for mixture search.
