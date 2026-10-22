# Data preparation v001

Status: complete. Source revision: data-tools-v001. Implemented revision: data-tools-v001.

- [x] D1: dated scientific sources, planning/cleaning/mixture/answer-integrity/tools/evaluation docs; ADR before code.
- [x] T1: bounded profile/prepare, exact dedup/group/fixed split and private manifests.
- [x] T2: independent tensor integrity/lineage checks, token exposure and mixture feasibility.
- [x] S1: extend /ml:data, mandatory docs/validator/portable resources/templates.
- [x] V1: adversarial offline fixtures, full offline suite, packaging/validator/compile, safe handoff.

DoD: no truncation/secret logs, no implicit downloads/training/paid calls; data readiness distinct from schema/tensor integrity. Existing ML runtime approvals and budgets unchanged. Domain/language weights explicit hypotheses; missing data never silently renormalized. Semantic quality, LID/PII/near-dedup coverage, actual tokenizer/collator, training and general/length regression NOT_RUN until applicable checks.

Evidence: 323 full offline tests PASS (230.254s), 26 final focused data tests PASS (0.429s), 4 portable packaging tests PASS (0.501s), repo validator/compile/diff PASS. Training/real tokenizer/data quality NOT_RUN. See handoff.md and example-report.json.
