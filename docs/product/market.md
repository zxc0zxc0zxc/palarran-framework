# /palarran:product:market — market and demand

First read [Buffer/Airbnb](cases/market-validation.md), [evidence](evidence.md), [data sources](data-sources.md). Assess whether a problem exists, its nature and the reachable audience, including negative signals.

Freeze scope: customer/buyer, B2B/B2C, language/geography, business category, time window, launch constraints. Query problem/job, alternatives and purchase intent, not only brand names. Inspect reviews/public discussions/marketplace complaints as qualitative signals with selection bias; never invent interviews or contact people without scope.

Triangulate available independent families: search trend/volume, actual use-case complaints/workarounds, spending/disclosures/industry statistics. Missing one API does not mean a market is absent. Preserve missing coverage and confidence; do not add a fictional source to reach a count.

[Google Trends FAQ](https://support.google.com/trends/answer/4365533?hl=en) explains sampling and the UI's 0–100 normalization. A zero index may indicate low volume. Compare terms/topics, geography, window/category/search property and a common scaling basis; do not sum separate UI exports as absolute volumes. The API alpha has a different consistent-scaling contract: do not call its values absolute buyer counts. Separate trends, seasonality, news spikes and brand/problem interest.

For TAM/SAM/SOM first define the customer unit and annual price basis: TAM is potentially eligible buyers; SAM is the serviceable scope/region/constraints; SOM is reachable distribution with capacity/distribution assumptions and a horizon. Prefer bottom-up when data exists. Cross-check estimates with alternative sizing; do not sum overlapping segments. An unknown base requires qualitative segmentation/unknown, not a precise billion-dollar TAM. Ad competition is not the number of product competitors.

Output using [research](../../templates/product/research.md): scope/query log, segments and evidence, dynamics/risks, sizing bounds or unknown, contradictory signals, actionable next validation. Time-series charts require real data with axes/units/sample/source; without a series, diagram segments and the funnel rather than inventing a trend.

DoD: distinguish demand from curiosity; record coverage/limits, case applicability, costs/permissions for subsequent tests and stop criteria. Research completion remains separate from market validation.
