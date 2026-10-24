# Data readiness and independent verification

Before launch: frozen data/model/tokenizer/template/config/transform hashes, rights/consent, train-only preprocessing, group/duplicate separation, actual domain/language/length/source counts, full-response/loss-mask/EOS/collator checks and a feasible mixture plan. Missing cells/unknown rights/tokenization never become zero or “ready.”

| Gate | Minimum evidence | When missing |
| --- | --- | --- |
| Rights/provenance | source register + approval evidence + exclusions | use blocked; research candidates allowed |
| Split/leakage | exact/group assertions, near/translation/benchmark audit scope | exact-only ≠ leakage-free; remaining audit NOT_RUN |
| Content/labels | sampled annotation/quality review by slice, disagreement | schema-valid ≠ factual/correct |
| Privacy | specialized local scan and review; controlled storage | marker scan ≠ PII-free |
| Tokens/answers | actual tokenizer/template/collator tensors, unmasked targets/end tokens, no truncation | inventory token counts unknown; no ready mixture |
| Mix feasibility | joint quotas, floors, repeats, source/length review and realized sampler test | planned, not sampled |
| Regression | base/adapted domain+general frozen suite, per-language metrics, N/uncertainty | training/quality benefit NOT_RUN |

Independent data verification rereads manifests+shards, verifies digests, exact group/duplicate constraints and tokenized-record bindings. Raw/prepared/token/policy changes invalidate downstream audit/plans. A script report is arithmetic/contract checking, not dataset-author self-attestation. Token IDs/producer flags do not prove correspondence to source text without checking the local tokenizer/template pipeline.

Start with inexpensive schema/golden fixtures, then manual audit and only authorized tokenizer/collator smoke tests, followed by an authorized tiny pilot/learning curve; the data skill does not imply expensive datasets/LLM judges/GPUs. CLI unit tests are synthetic CPU fixtures, not scientific paper replication. Final improvement is checked through `/palarran:ml:benchmark`/`/palarran:agent:eval` under a frozen applicable protocol; the existing runtime preserves spending/prior unknowns, and a new data helper does not reset them.

Preserve preparation status, every reason/count and NOT_RUN list; rejected rows stay in the denominator. Target memory contains safe aggregates/private refs only. Data artifacts/IDs/token arrays may reveal raw text and belong in private storage; token IDs are not anonymization.
