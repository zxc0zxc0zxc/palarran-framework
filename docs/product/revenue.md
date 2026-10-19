# /product:revenue — выручка аналогов

Сначала [Buffer economics](cases/revenue-economics.md), [evidence](evidence.md), [data sources](data-sources.md). Цель — понять business model и экономический диапазон, сохраняя возможность «неизвестно».

Иерархия: regulator filings/audited reports → investor/company disclosures → founder self-report → named provider estimates → наша conditional model. Проверять exact entity/product, year/quarter/month, currency/exchange date, gross/net, recognized revenue/run rate/GMV/bookings, reporting coverage и ownership/acquisition changes. Parent company total нельзя назначить одному продукту. Funding/valuation/downloads не revenue. На каждой строке — E-ID и classification.

Для public companies [SEC companyfacts/submissions](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) дают disclosures; сверять taxonomy/unit/period/accession и исходный filing. Не суммировать YTD с quarterly или revised/duplicate facts. Для иных юрисдикций — официальный registry/IR с учётом доступности; SEC не покрывает все частные/неамериканские фирмы.

Provider mobile data имеет свой perimeter. Например, [Appfigures estimates](https://docs.appfigures.com/api/reference/v2/estimates) описывает net estimates для supported stores/countries и paid downloads/IAP/subscriptions. Это не гарантированно весь revenue компании: web, advertising и другие каналы проверять отдельно. Не превращать net estimate в gross без source fee/tax definitions.

При отсутствии disclosures оценивать только с явными input E-IDs: `MRR = paid_accounts × monthly_ARPA`; marketplace `net revenue ≈ GMV × effective take_rate` с refunds/discounts/recognition caveats. Traffic→signup→paid допустим лишь как hypothetical scenario при недоступных конверсиях, не «конкурент зарабатывает X». Low/base/high — sensitivity ranges, не статистический confidence interval. Нет обоснования ключевых входов — unknown; избегать сложной модели ради видимости точности.

Для своего proposed продукта отдельно оценить contribution margin, support/infra/payment/refunds, blended/paid CAC definitions, cohort retention и payback. `LTV≈ARPA×gross_margin/churn` применим только к устойчивой однородной подписочной cohort с аргументированным stationary churn; до этого cohort cashflow/sensitivity. Не считать gross revenue прибылью и не советовать покупать акции.

Выход [economics](../../templates/product/economics.md): source metric table, comparable normalization, disclosed vs estimated vs scenarios, input bounds/formulas, dominant uncertainty, next data needed. DoD: воспроизводимая арифметика, unknown сохранены, conclusions scale-aware, никакой false precision.
