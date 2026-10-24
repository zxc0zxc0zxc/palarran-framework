---
name: palarran-product-b2b
description: "Plan sales to the first small B2B customers: qualification, pain hypotheses, offer and outreach plan. Use for /palarran:product:b2b before development and after polish; research only, no messages sent."
---

Shared cycle: before work and after checks follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# Product B2B

Invoke `/palarran:product:b2b {description}` or `$palarran-product-b2b`. Independent first-customer research/planning; never automatically start other commands.

## Documentation and context first

Before research read [map](../../docs/README.md), [evidence](../../docs/evidence.md), [workflow](../../docs/workflow.md), [data/API](../../docs/data-sources.md), [primary sources](../../docs/sources.md), [case map](../../docs/cases/README.md), [go-to-market](../../docs/go-to-market.md), [pricing](../../docs/pricing.md), [new sources/dates](../../docs/go-to-market-sources.md), [profile](../../docs/b2b.md), [domain cases](../../docs/cases/b2b-first-customers.md) and [output template](../../templates/b2b-sales.md). Missing mandatory material is a blocker, not grounds to substitute general knowledge. Explain case applicability and what not to copy.

Resolve the SKILL.md symlink: installed checkout and target are different roots. Read [decision memory](../../../../core/agents/docs/decision-memory.md), target README, `.palarran/INDEX.md`, accepted ADRs/product reports/revisions and actual context. Without description use README; if buyer/business/geography is unclear, ask one specific question while continuing independent research. Never substitute another product. For B2B2C/marketplaces split buyer/user/sides and two plans instead of inventing one ICP.

## Domain work

Apply small-fit: independent teams of 1–30 people or 1–3 locations with accessible buyers. Operational default, not legal classification. Corporate parents/enterprise procurement exclude; unknown size/ownership is conditional, not qualified. Never widen segments just to fill counts.

Find up to 10 candidates using actual public company pages/directories/registries/reviews/vacancies. Report fewer when coverage is limited. Each requires source/date size/ownership, buyer role/public business-contact URL, observed trigger→pain hypothesis→question, existing substitute, product fit/limits. Never invent contacts/budget/willingness to buy. Similarweb is optional estimate; N/A is not zero, a size filter or proof of absent demand. Without paid access use public sources.

Produce bounded offer/pilot/support matching actual capabilities and transparent value/cost hypotheses. Plan 1–2 accessible buyer paths, short first-message/follow-up drafts, small batch/cadence, owner, cash/time cap, stop and paid/retained funnel with denominator/window. Future contacts are not_run; prospect lists grant neither outreach consent nor confirmed sales.

## Budget, persistence and readiness

Before detailing, ask/read actual cash cap/test cap/currency/window and time budget. Unknown budget → **cash cap=0**; paid candidates conditional. Research/model budget differs from sales/media. Full mandatory costs must fit cap; missing fees/quotes/eligibility → gap. Synthetic RUB 3,000/10,000 doc examples are not defaults/rates/spending consent. Read-only public research/previously authorized data; paid APIs only within explicit budget. No accounts/purchases/outreach/publications/tracking/app edits/deploy. API documentation is not connected access; never store secrets.

Link material claims/prices to E/Q-ID, URL/publisher/date/as-of/geography/unit/method/limits/confidence; separate observed/disclosed/estimated/hypothesis/scenario/unknown. Before dependent choices record rationale/evidence/alternatives/consequences/review trigger in target `.palarran/product/<task>/decisions/`; update INDEX/handoff/`revisions/vNNN/` without erasing history. Never save results inside installed skills. Product/source-revision changes flag downstream artifacts for review.

First checkpoint **who/how to sell before implementation**; after polish record actual capabilities/offer/onboarding/quote deltas. Report draft/research_complete/needs_input/blocked; separately ready_to_test/conditional/needs_input. ready_to_test means proposal completeness, not launch permission/market validation. Expose unknowns/shortfalls. Conclude with segment/accessible path, constraints/caps, next cheap falsifying test and report/evidence/ADR/handoff links.

## When assigned the runtime acquisition stage

Read [pipeline](../../docs/pipeline.md)/[artifact contract](../../docs/pipeline-contract.md). Apply this profile **inside the current acquisition attempt**, using its stage-prefixed E-IDs/report/manifest and pinned upstream references; never add a seventh stage/nested CLI run. Standalone use needs no envelopes. MVP synthesis receives sales/growth plans/sellability gaps; independent verification checks integrity, not demand/sales proof.
