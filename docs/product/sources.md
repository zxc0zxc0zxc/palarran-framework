# Первичные источники и применимость

Проверка 2026-10-19. Историческая дата кейса отделена от даты чтения. Published unknown означает, что дата не подтверждена; её нельзя заменить retrieval date. Ссылки подтверждают конкретный claim, не обещают перенос успеха. Для текущих company metrics заново проверять as-of.

| Источник | Тип / дата | Что берём / границы |
|---|---|---|
| [Superhuman, Rahul Vohra](https://review.firstround.com/how-superhuman-built-an-engine-to-find-product-market-fit/) | Founder-written, 2018-11-12 | Segmentation/survey/roadmap; reported result, sample/cohort bias; не causal profit proof |
| [Buffer first paying customers](https://buffer.com/resources/idea-to-paying-customers-in-7-weeks-how-we-did-it/) | Founder, 2011-02-16 | Ранние intent/pricing/MVP steps, historical outcome; не current conversion benchmark |
| [Airbnb at YC](https://www.ycombinator.com/blog/the-airbnbs/) | Early investor account, 2020-12-10 | Работа с узким ранним рынком; retrospective заинтересованность |
| [Buffer Open](https://buffer.com/open) | Company dynamic disclosure, published unknown | Disclosed metric definitions; as-of dashboard проверить, не audit |
| [Buffer annual 2023](https://buffer.com/shareholders/2023) | Company annual account, report year 2023 | Pricing/segment/economics context; нельзя приписать весь рост одному решению |
| [GitLab competitor evaluations](https://handbook.gitlab.com/handbook/product/ux/competitor-evaluations/) | Maintained handbook, current publish date unknown | JTBD-based solution evaluation; effect on win-rate не раскрыт |
| [Ahrefs product-led content](https://ahrefs.com/blog/product-led-content/) | Company practitioner account, date не зафиксирована | Демонстрация job/product в контенте; CAC/incrementality не раскрыты |
| [SweetyTreatyCo case in TikTok guide](https://ads.tiktok.com/business/library/TikTok_Formula_4_Success.pdf) | Vendor-selected SMB case, publish date unknown, last page | Organic/Spark/payment events mechanism; цифры из графики не воспроизводим; не causal trial |
| [Amazon Working Backwards](https://www.aboutamazon.com/news/workplace/an-insider-look-at-amazons-culture-and-processes) | Company-published founder-executive book excerpt, ©2021 | Customer narrative/constraints before build; процесс, не quantified effect |
| [Google HEART paper](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/) | Google research, 2010 | Связь product goals и user-centered signals; stage/metric fit нужен отдельно |
| [Microsoft trustworthy experiments](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/) | ExP practitioners, 2020-07-31 | Hypothesis, assignment и measurement trust; маленький pilot не всегда A/B |
| [Trends alpha](https://developers.google.com/search/apis/trends), [UI FAQ](https://support.google.com/trends/answer/4365533?hl=en) | Live vendor docs | Availability/scaling contracts разные; search interest не paying demand |
| [Ads keyword planning](https://developers.google.com/google-ads/api/docs/keyword-planning/overview), [access migration](https://developers.google.com/google-ads/api/docs/api-policy/developer-token) | Live docs; token sunset 2026-09-09 | Historical metrics + актуальный OAuth/project admission, не campaign creation |
| [Meta Ad Library API](https://br-fr.facebook.com/ads/library/api/?source=onboarding) | Live vendor docs | API region/type/archive constraints; поля spend не универсальны |
| [TikTok Commercial Content API](https://developers.tiktok.com/products/commercial-content-api), [Top Ads](https://ads.tiktok.com/business/library/NA_Creative_Center_Top_Ads_One_Pager.pdf) | Live docs / PDF date unknown | Approved archive vs curated creatives, не глобальная полная campaign economics |
| [Google Ads Transparency](https://blog.google/innovation-and-ai/technology/ads/announcing-the-launch-of-the-new-Ads-Transparency-Center/) | Google announcement, 2023 | Observed ad/advertiser signals; general public API не подтверждён |
| [Similarweb API](https://docs.similarweb.com/api-v5/similarweb-api/website-analysis-api/batch-api/traffic-and-engagement), [methodology](https://support.similarweb.com/hc/en-us/articles/5083358615313-Similarweb-Data-Methodology-FAQs) | Live provider docs | Traffic estimates/credits/perimeter; не owner analytics или revenue |
| [SEC public data API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [fair access](https://www.sec.gov/filergroup/announcements-old/new-rate-control-limits) | SEC docs, 2024 / 2021 | Filings/XBRL/limits; не весь private market, не homogeneous revenue series |
| [Appfigures estimates](https://docs.appfigures.com/api/reference/v2/estimates) | Live provider docs | Net mobile estimates по supported perimeter; не все revenue sources |

Excluded during research: Duolingo TikTok case URL вернул notfound при прямом открытии; Google Ads Never Fully Dressed case body не удалось надёжно прочитать. Поэтому их рекламные числовые claims не включены как подтверждённые кейсы. Google HEART PDF redirect был недоступен, использована доступная official publication page. Primary Meta canonical URL не открылся, проверена официальная locale-версия. Это access limitations, не доказательство отсутствия кейса/канала.
