# Data plan / revision draft-v001

Основание: [data guides](../../docs/ml/data/README.md). Toy JSON templates проверяют формат; 80/10/10, 40/30/20/10, end_token_ids=[999] и нулевые hashes — демонстрация, **не training recipe/default/recommended ratios/tokenizer**. Перед использованием заменить по задаче/модели и source evidence.

## Цель и baseline

Task/pretrain/DAPT/SFT/non-LLM, capability requirements, existing model/tokenizer/template/config revisions, no-training baseline, general skills/languages, допустимые regression thresholds и owner.

## Coverage и acquisition

| Requirement | Domain | Language/script | Task/answer length | Source/rights/consent ref | Records/groups/actual tokens | Gaps | Split/eval |
| --- | --- | --- | --- | --- | --- | --- | --- |

Права/PII/лицензии, annotation rubric/disagreement, real/synthetic provenance, search rejected list, private storage/retention, acquisition/prep/eval/compute budgets; unknown counts не estimates disguised as facts.

## Очистка и lineage

Raw input hash → code/config/seed → exclusion counts по slices → exact/near/translation decontamination scope → component/group/fixed splits → immutable shards/ledger manifest hashes. Никакого silent truncation, loss of code whitespace или train/test rebalancing. Schema/PII/LID/quality audits, что сделано/NOT_RUN.

## Tokenizer/collator и ответы

Actual template/tokenizer/collator hashes; exported unpacked IDs/labels/attention/assistant masks; EOS/EOT и padding; input/target length distributions, overflow/incomplete counts; manual decoded span inspection. Semantic completeness не выводить из complete=true. Packing требует собственного boundary test.

## Mixture hypotheses

Joint domain/language weights, preserved general anchors, language/domain floors, source/length/quality slices, total train-token exposure/max effective repeats, exact inventory и missing cells. Proposed alpha/proxy weighting — гипотеза, no free DoReMi. Toy weights не основание выбора. Realized sampler/resume/rank/shuffle checks обязательны до launch.

## Проверки / прогресс

- [ ] Права и source evidence готовы.
- [ ] Independent split/dedup/contamination и privacy/content audit.
- [ ] Actual tokenizer/template/collator, labels/EOS и full-answer checks.
- [ ] Feasible mixture + source/length review + actual sampler exposure.
- [ ] Отдельное разрешение training/budget, preserved historical expenses.
- [ ] Base/adapted general+domain+per-language+full-answer frozen benchmark.

Implementation status и verification раздельны. Решения/альтернативы/источники до зависимых действий в target INDEX/ADR. Data artifacts и token arrays private; journal только safe aggregates/private refs. Training/model benefit по умолчанию NOT_RUN.
