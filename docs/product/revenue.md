# /palarran:product:revenue — revenue of alternatives

First read [Buffer economics](cases/revenue-economics.md), [evidence](evidence.md), [data sources](data-sources.md). Understand the business model and economic range while allowing “unknown.”

Hierarchy: regulator filings/audited reports → investor/company disclosures → founder self-report → named provider estimates → our conditional model. Verify exact entity/product, year/quarter/month, currency/exchange date, gross/net, recognized revenue/run rate/GMV/bookings, reporting coverage and ownership/acquisition changes. Do not attribute a parent company's total to one product. Funding/valuation/downloads are not revenue. Each row needs an E-ID and classification.

For public companies, [SEC companyfacts/submissions](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) provide disclosures; verify taxonomy/unit/period/accession against the original filing. Do not sum YTD with quarterly or revised/duplicate facts. Other jurisdictions require their official registry/IR subject to availability; SEC does not cover all private/non-US companies.

Mobile data providers have their own perimeter. For example, [Appfigures estimates](https://docs.appfigures.com/api/reference/v2/estimates) describes net estimates for supported stores/countries and paid downloads/IAP/subscriptions. This is not necessarily total company revenue: check web, advertising and other channels separately. Do not convert net estimates to gross without source fee/tax definitions.

Without disclosures, estimate only from explicit input E-IDs: `MRR = paid_accounts × monthly_ARPA`; for a marketplace, `net revenue ≈ GMV × effective take_rate`, with refunds/discounts/recognition caveats. Traffic→signup→paid is only a hypothetical scenario when conversions are unavailable, not “the competitor earns X.” Low/base/high are sensitivity ranges, not statistical confidence intervals. Unsupported key inputs remain unknown; avoid complex models that merely imply precision.

For the proposed product, separately assess contribution margin, support/infra/payment/refunds, blended/paid CAC definitions, cohort retention and payback. `LTV≈ARPA×gross_margin/churn` applies only to a stable homogeneous subscription cohort with justified stationary churn; until then use cohort cash flow/sensitivity. Do not equate gross revenue with profit or recommend stock purchases.

Output using [economics](../../templates/product/economics.md): source metric table, comparable normalization, disclosures versus estimates versus scenarios, input bounds/formulas, dominant uncertainty, next data needed. DoD: reproducible arithmetic, preserved unknowns, scale-aware conclusions, no false precision.
