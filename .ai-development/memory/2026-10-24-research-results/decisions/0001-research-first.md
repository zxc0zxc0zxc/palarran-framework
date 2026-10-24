---
id: memory/2026-10-24-research-results/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Preserve portable research findings

## Контекст и основание

User prioritizes R&D results over code patches as cross-project experience. Existing memory-v001 supports immutable reviewed cases and evidence; no model API/search connector is needed. Global recall for research/evidence returned zero cards; no inferred prior research result. Unpublished ML/SFT work remains untouched.

## Выбор и объяснение

Add a shared research-memory profile to the mandatory global-memory workflow for all skills. Prioritize applicable research findings within the same total0–3lesson budget, retain code lessons when useful. Include negative/inconclusive findings without confusing experiment outcome with evidence validation PASS. Model/data/protocol/baseline/units/uncertainty/conditions/limitations must accompany claims. Source reviews remain attributed source claims, not reproduced experiments.

Reuse deployed memory-v001 unchanged: type decision by default, research-result/domain/kind/outcome tags and compact structured narrative in existing fields. No new type/JSON field/edge, no schema migration/deploy or automatic historical import. Put subject/conditions/outcome in fingerprinted core so changed experiments are not silently deduplicated. Larger sanitized reports may use existing manual verification artifact; auto finish stays card-only. Private datasets, weights, generations and logs never bulk uploaded.

## Альтернативы

Code-only memory misses reusable R&D. Raw report/session ingestion loses privacy and context. New result type would require synchronized service/helper/deployment without adding retrieval capability needed here. A special backend ranking rule would claim priority not implemented by native FTS; priority here is the agent's selection contract, not a new search algorithm.

## Источники и evidence

Primary sources inspected2026-10-24: NeurIPS Paper Checklist (reproducibility, limitations, variability) and Google Model Cards2019 (evaluation conditions/intended use). Links and applicability in docs/skills/research-memory.md. Existing memory/service.py and scripts/memory_cycle.py inspected for schema/dedup/gates; prior automatic-cycle/0001 reused.

## Последствия и пересмотр

No API/GPU/provider calls required to save/read results. Existing pinned skill bundles require normal explicit update to receive the guide. No automatic extraction from previous runs. Structural/hash validation does not judge scientific truth; agent/reviewer validates meaning and scope. Consider typed research schema only after real retrieval/validation limitations appear.

## Применение и проверка

Offline real memory-cycle fixtures: negative/inconclusive claims, source attribution, distinct conditions, compatible schema, publish/dedup/recall. Portable package-contained guides, repo validator and full offline suite. No experiment/training, paid model call or VPS modification. Results recorded in handoff.
