# Data requirements before training

Following [Karpathy](sources.md), start with the prediction/generation unit, baseline errors and manual inspection of an authorized sample. For changing facts compare retrieval with training; SFT is useful for behavior/format and skills, but is not a reliable store of continually changing facts.

The plan includes goal, task family (pretraining/DAPT/SFT/preference or non-LLM), baseline, supported languages/scripts/geography, target domains and general capabilities that must be preserved. Choose model/tokenizer/context window and actual data constraints first; do not promise equal quality across arbitrarily many languages at fixed capacity.

## Coverage matrix

Each row records requirement ID, domain, language/script or mul, task/answer format, source and rights evidence, unit/group, expected label/rubric, short/medium/long answer, edge/OOD, train/validation/final-test policy, records/unique groups/**actual tokenizer tokens**, confidence and deficits. Include real positives, hard negatives, ambiguous cases and appropriate refusals where part of product behavior. Do not blanket-label controversial/long material as refusal.

Preserve general dialogue/instruction-following, reasoning, reading, code/math/tool use only where claimed capabilities of the base model/product. “General” is an explicit task set, not arbitrary web noise. Domain QA needs verifiable grounds and full answers; extraction needs schema/empty/no-answer/malformed inputs; code needs executable tests; retrieval needs hard negatives without query/answer leakage.

There is no scientific constant “N rows suffice.” Break down budget into unique useful tokens × repetitions × compute, annotator hours, privacy/rights review, storage, tokenization and evaluation. Learning-curve/proxy-pilot sizing requires an authorized experiment; Chinchilla pretraining is not an SFT sizing formula. [LIMA](sources.md) motivates studying example quality, not a magic count.

## Sources and annotation

Start with owned/authorized data, then original dataset publishers and checks of original/redistribution licenses, consent, PII, retention and availability. Unknown rights prohibit use but do not prohibit describing a research candidate. For synthetic data record teacher/model/prompt/license/cost/filters; never feed the teacher final-test answers. Recursive synthetic corpora without human/real-data anchors are a separate hypothesis with an independent real holdout, not a free substitute for diversity.

Annotation rubrics cover boundary cases and disagreement. Double-label/adjudicate with sample sizes by language/domain/length slice rather than one average. Select filtering/thresholds on development, not final test. Preserve discovered candidates/rejection reasons so later agents do not repeat failed collection.

## Output

[Data plan](../../templates/data-plan.md), source register, coverage gaps, minimum readiness gate and proposed mixture hypotheses. Record decisions in target `.palarran/ml/<task>/decisions/` before dependent actions; `--plan` does not read raw datasets or run profiling/tokenization/download/training. Without access, actual counts and quality are unknown, never scenarios disguised as measurements.
