# Data plan / revision draft-v001

Basis: [data guides](../../docs/ml/data/README.md). Toy JSON templates test format; 80/10/10, 40/30/20/10, end_token_ids=[999] and zero hashes are demonstrations, **not training recipes/defaults/recommended ratios/tokenizers**. Replace them by task/model and source evidence before use.

## Goal and baseline

Task/pretrain/DAPT/SFT/non-LLM, capability requirements, existing model/tokenizer/template/config revisions, no-training baseline, general skills/languages, allowed regression thresholds and owner.

## Coverage and acquisition

| Requirement | Domain | Language/script | Task/answer length | Source/rights/consent ref | Records/groups/actual tokens | Gaps | Split/eval |
| --- | --- | --- | --- | --- | --- | --- | --- |

Rights/PII/licenses, annotation rubric/disagreement, real/synthetic provenance, rejected search candidates, private storage/retention, acquisition/preparation/evaluation/compute budgets; unknown counts are not estimates disguised as facts.

## Cleaning and lineage

Raw input hash → code/config/seed → exclusion counts by slice → exact/near/translation decontamination scope → component/group/fixed splits → immutable shard/ledger manifest hashes. No silent truncation, code-whitespace loss or train/test rebalancing. Schema/PII/LID/quality audits, completed/NOT_RUN distinctions.

## Tokenizer/collator and answers

Actual template/tokenizer/collator hashes; exported unpacked IDs/labels/attention/assistant masks; EOS/EOT and padding; input/target length distributions, overflow/incomplete counts; manual decoded-span inspection. Do not infer semantic completeness from complete=true. Packing needs its own boundary test.

## Mixture hypotheses

Joint domain/language weights, preserved general anchors, language/domain floors, source/length/quality slices, total train-token exposure/maximum effective repeats, exact inventory and missing cells. Proposed alpha/proxy weighting is a hypothesis, not free DoReMi. Toy weights do not justify selection. Realized sampler/resume/rank/shuffle checks are mandatory before launch.

## Checks / progress

- [ ] Rights and source evidence ready.
- [ ] Independent split/dedup/contamination and privacy/content audits.
- [ ] Actual tokenizer/template/collator, labels/EOS and full-answer checks.
- [ ] Feasible mixture + source/length review + actual sampler exposure.
- [ ] Separate training/budget authorization, preserved historical expenses.
- [ ] Base/adapted general+domain+per-language+full-answer frozen benchmark.

Separate implementation from verification status. Decisions/alternatives/sources go in target INDEX/ADRs before dependent actions. Data artifacts/token arrays are private; journals contain safe aggregates/private refs only. Training/model benefits default to NOT_RUN.
