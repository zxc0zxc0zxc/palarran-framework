# Data discovery, preparation and quality

## Discovery before downloading

Start with owned/authorized project data, then relevant open datasets from original authors, Hugging Face Hub, universities and official competition publishers. Search does not authorize bulk downloads or scraping. For each candidate record owner/original URL/revision, task/languages/geography/period, sample/label unit, size/format, original and redistributor license, use/PII restrictions, access/auth/cost, provenance and fit to the target distribution. Unknown license/consent blocks use; public availability does not establish permission.

[Hugging Face Dataset Cards](https://huggingface.co/docs/hub/datasets-cards) provides useful metadata, limitations and provenance; a card is an author statement, not independent quality/rights verification. Fill in the [data card](../../templates/ml/data-card.md), preserving rejected candidates so the next agent does not repeat discovery.

## Contract and split

Before transformation/augmentation, freeze the split unit and leakage threats. For entity-dependent examples split by user/patient/document/repository/session; for time series use time with horizon/gap and availability timestamp, applying purge/embargo to overlapping windows where justified. Fit scalers/imputers/vocabulary/feature selection on train only. CV/audio augmentation follows splitting; chunks from one source must not cross splits. Grounding corpora and benchmark queries can also leak through duplicates/quotations. [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) grounds train-only fitting/Pipeline; the specific entity/time policy is our adaptation.

Separate train, validation/model selection and final test. A small dataset may require grouped/nested cross-validation rather than arbitrary 80/10/10; fix the method and precision limits in advance. Do not use the final test for prompt selection, HPO, synthetic generation, target thresholds or manual correction of training labels. Hold access and its hash separately; if the agent has seen the answers, it is no longer a hidden holdout.

## Preparation (`--prepare`)

Within the authorized volume: immutable raw snapshot/private refs → schema/type checks → bounded profiling → canonicalization/dedup → split manifest → train-only fitting/augmentation → versioned processed shards. Record counts before/after every filter and exclusion reasons, bytes/checksums, transform commit/seed/config. Do not delete originals automatically. Do not change the source license or publish the cleaned dataset by default.

Check exact/near duplicates within and across splits; the report includes method/threshold and detection limits, rather than declaring “no leakage” after one hash check. Check missingness, invalid ranges, empty/truncated samples, class/domain/language imbalance, label conflicts, temporal coverage, corrupt files and sample inspection in the authorized environment. No sensitive examples in the public journal.

## Annotation and synthetic data

[Lilian Weng, Human Data Quality](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) discusses task design/raters/disagreement. Transfer annotator calibration and investigation of disagreement: it may reflect the task rather than annotator error. Our procedure: a concise rubric with boundary examples, a double-label audit subset, adjudication/versioning, quality-audit size and uncertainty, privacy and annotation cost. Do not collapse subjective labels into an invented single ground truth.

Synthetic generation is a separate experiment: teacher/model/prompt/revision/license, generation/censoring/filter counts, deduplication, failed-call costs, factuality and diversity checks, and an independent real-data holdout. Do not generate from test answers or equate more rows with more independent observations. For preference data retain chosen/rejected provenance and the rubric; do not turn arbitrary LLM-judge scores into human preferences.

## Output and DoD

The data report preserves rights/provenance, split/transform hashes, counts, quality/contamination evidence, slices, retention/access and unknowns. `research_complete` means a strategy was found; `prepared` means files were actually created/checked. For an inaccessible private dataset provide a reproducible preparation recipe and blocked/not_run status, without invented statistics. Heavy downloads/dependencies/cloud uploads are outside default research. Changing the split invalidates prior benchmark comparisons until rechecked.

## Deeper preparation and data mixtures

For LLM/text tasks, reading the [data route](data/README.md), [planning](data/planning.md), [cleaning](data/cleaning.md), [domain/language mixtures](data/mixtures.md), [answer integrity](data/answer-integrity.md), [tool contract](data/tools.md), [evaluation gates](data/evaluation.md) and [dated scientific sources](data/sources.md) is mandatory. `scripts/ml_data.py` supports explicitly authorized local preparation/auditing/arithmetic mixture planning only; it is not training or evidence of model improvement. Other modalities need their own adapters; existing split/rights rules remain in force.
