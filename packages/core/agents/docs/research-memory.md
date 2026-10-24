# R&D findings in shared memory

This profile is mandatory when a task produces research, experimental, benchmark, ablation, product-discovery or UX/infra measurement results. Applied to all skills through the [shared loop](global-memory.md); [local decisions](decision-memory.md)/complete domain reports remain context sources. Research findings often transfer better than specific patches: when selecting0–3lessons, consider relevant R&D findings first. This prioritizes agent selection, not a new implemented Neo4j ranking algorithm. Shared limits, owner policy and budget never increase.

## Basis

Checked2026-10-24: [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist), rolling guide—reproducibility, experimental settings, limitations, variability/error bars; [Google Model Cards2019](https://research.google/pubs/model-cards-for-model-reporting/)—evaluation across conditions/intended use. These ground reporting principles, not proof of memory quality. Our0–3limit, compatible field mapping and negative-finding selection are project choices. ML/data/product/science retain domain mandatory guides; writing cards starts no experiment.

## Findings to preserve

- `empirical`: completed experiments, benchmarks/ablations, latency/cost/quality measurements, confirmed failures. Record observation; label causal explanations hypotheses unless tested causally.
- `source_review`: verified primary-paper/case reviews. Preserve authorship, URL/DOI, date/version and claim conditions; source conclusions remain `source_claim`, not `observed` or independent replication.
- `discovery`: evidence-backed demand/competitor/UX research with date, segment, geography and sample limitations. Market research alone is not market validation; disclosed revenue/provider estimates are not observed revenue.

Negative findings, no measurable effects and budget stops are useful. Never cherry-pick successful runs or call interrupted/confounded benchmarks proof of method uselessness. Outcome: `supported`, `refuted`, `inconclusive` or `not_tested`. Refuted is conditional; an insensitive null result is usually inconclusive. Source reviews without own tests use not_tested for the local hypothesis and separately state the authors' reported outcome.

## Minimum content

A card must let the next agent assess applicability without the original conversation:

| Section | Record |
| --- | --- |
| Question | Hypothesis/JTBD, prefrozen success criterion; explicitly label post-hoc criteria |
| Subject | Model/method/config/code versions; safe data and split/protocol hashes/IDs, not dataset contents |
| Conditions | Data size/domains/languages, hardware/workload, material parameters, date/market; reasoned N/A |
| Method | Baseline/candidate, measured change, protocol, seeds/repeats/sample size or limits; observational comparison is not controlled experimentation |
| Observation | Baseline/candidate metrics with units, improvement direction/denominators; valid delta; uncertainty/confidence interval or explicit unknown |
| Resources | Observed time/tokens/GPU and cost with estimate/provider_usage/invoice basis, currency/date; unknown is not zero |
| Conclusion | Outcome, evidence level observed/source_claim/hypothesis, supported and unestablished claims |
| Reuse | applies_when, limitations, possible confounders, review conditions/next check |
| Provenance | Source-repo alias+commit+ADR, E-IDs/source URLs, verified report hashes; no credentials |

For non-ML tasks do not invent model/seed/GPU: preserve relevant contextual measurements and explain inapplicability. One attempt is not independent replication; re-recording one finding in another project is not replication either. Brevity must not lose exact subjects/conditions/numbers.

## memory-v001 compatibility

This profile adds no API fields/types. Existing service accepts case types pattern/incident/decision/solution/anti_pattern only. Use `decision` for neutral R&D findings; `anti_pattern` fits justified negative engineering lessons, not every failed training run. Never send `type:research_result` or top-level `metrics`/`experiment`: deployed service rejects them.

Map into existing fields:

- `title`: short question/result. `tags`: research-result, domain, kind/outcome, meaningful retrieval keywords; reserve room for service fingerprint.
- `problem`: hypothesis + exact subject/data/protocol identity + material conditions; retrieval/dedup can distinguish studies.
- `root_cause`: observed effect/uncertainty and explanation status. Unknown causes stay unknown; reviews attribute source_claim.
- `solution`: compact labeled method/baseline/metrics/resources/outcome/conclusion sections. Conclusions may say “do not apply in these conditions,” “next check required,” or “hypothesis untested,” not necessarily a code fix.
- `applies_when`/`limitations`: transfer boundaries, confounders/unknowns; never hide critical conditions only in source evidence.
- `source`: standard repo/commit/adr from current local journal, even for literature reviews. `evidence`: safe primary links/E-IDs/report hashes, original attribution separately.

Compatible card-content example (synthetic, not actual experience):

```text
type: decision
tags: research-result, ml, empirical, inconclusive, cache
problem: H: cache improves p95; subject fixture-v1; data fixture-a;
         protocol fixed-1000-requests; single-worker; workload read-only.
root_cause: Observed sample difference; causal effect and variability unknown.
solution: Method: baseline cache-off vs candidate cache-on, one run each.
          Metrics: p95 100ms vs 90ms on 1000requests each; lower is better.
          Uncertainty: unknown; single run. Outcome: inconclusive.
          Resources: elapsed/cost unknown. Conclusion: insufficient evidence
          to promise improvement; repeat under the same frozen workload.
applies_when: same workload and version; exploratory comparison only
limitations: synthetic fixture; no production SLA; no independent replication
```

JSON follows the existing case/lesson contract; these are example values, not an upload payload. Full card <=8KiB with verification refs; automatic finish adds proof/fingerprint and may reject oversized input. Never silently truncate metrics/conditions/limitations: narrow the finding or retain a local draft. `finish` sends case only, no artifacts. Authorized manual propose may attach a separately anonymized `verification` artifact under existing contract; no new research-report type. Never upload full data/weights/raw generations/logs/personal responses. Hashes bind evidence, not private-original access or truth.

## Verification, writing and search

Before finish verify source/subject identity, measurements/denominators, conclusions/limits, privacy/rights and semantic duplicates. Existing checks PASS means accurate recording/verification, not conversion of refuted/inconclusive outcomes to supported hypotheses. Include all applicable real report hashes in `verification.checks`. Failed/missing mandatory checks mean local draft/DEFERRED, not fictional PASS. Verified stops support only stop facts/conditions, not unmeasured quality metrics.

Automatic finish preserves commit/clean-source/ADR/evidence/privacy/dedup gates, propose→read-back→promotion→read-back and unknown-outcome reconciliation. Do not retroactively auto-publish existing reports. Changes to model/data/protocol/conditions/outcome/numbers enter fingerprinted problem/root_cause/solution: source/evidence/tags alone do not alter semantic fingerprints. Repeated findings mean feedback/reuse; never overwrite or conflate contradictions. Only reviewers can write CONTRADICTS/VALIDATED_BY/SUPERSEDES relations; without rights preserve references/propose links, never expand MCP inventory.

Before another R&D task search hypothesis/method, domain/language and workload, not technology names alone; include negative findings/limits. Start with bounded3cards, then required originals; FTS guarantees neither semantic nor cross-language recall. Check versions/applicability; never transfer effects/numbers to another dataset/market without verification. Existing published bundles receive this profile through normal safe update; instruction-level workflow, not a new host hook/background extractor.
