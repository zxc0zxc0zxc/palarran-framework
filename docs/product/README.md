# Продукт: от evidence к решению

Обязательная база product-скиллов: **сначала изучить кейсы и профильную документацию, затем выполнять исследование**. Кейсы стартапов показывают механизмы на близком масштабе; практики бигтехов помогают измерять и проверять решения. Это наша адаптация, не универсальный рецепт успеха.

| Команда | Обязательный профиль | Результат |
|---|---|---|
| `/product:define {идея}` | [Продукт](define.md), [Superhuman/Amazon](cases/product-discovery.md) | ICP/JTBD, value proposition, business model, MVP, success/stop criteria |
| `/product:market {рынок}` | [Рынок](market.md), [Buffer/Airbnb](cases/market-validation.md) | demand evidence, сегменты, scope TAM/SAM/SOM, проверки риска |
| `/product:compare {продукт}` | [Аналоги](compare.md), [GitLab/Buffer](cases/competitive-positioning.md) | одинаковые customer jobs, конкуренты/замены, pricing и defensible wedge |
| `/product:revenue {аналоги}` | [Выручка](revenue.md), [Buffer transparency](cases/revenue-economics.md) | раскрытые метрики и отдельно диапазоны оценок с допущениями |
| `/product:b2b {продукт}` | [B2B](b2b.md), [Yclients/YouGile/Buffer](cases/b2b-first-customers.md) | Малые кандидаты, bounded offer, sales/outreach plan |
| `/product:b2c {продукт}` | [B2C](b2c.md), [Россия и иностранные стартапы](cases/b2c-frugal-growth.md) | Узкая аудитория, дешёвые каналы, цены и growth tests |
| `/product:acquisition {аналоги}` | [Привлечение](acquisition.md), [Ahrefs/Airbnb/TikTok](cases/acquisition-growth.md) | доказанные channel signals, funnel и план ограниченных экспериментов |

Для всех: [evidence](evidence.md), [workflow и handoff](workflow.md), [методы и API](data-sources.md), [реестр кейсов](cases/README.md), [первичные источники](sources.md). Templates: [brief](../../templates/product/brief.md), [research](../../templates/product/research.md), [competitors](../../templates/product/competitors.md), [economics](../../templates/product/economics.md), [channels](../../templates/product/channels.md).

Каждый skill можно вызвать отдельно, с текущими проектными материалами или явным списком аналогов. Не нужно автоматически запускать остальные. Нет description — прочитать target README/product memory; если бизнес/география не ясны, задать один конкретный вопрос, продолжая независимый inventory. Не выбирать другой бизнес вместо пользовательского.

Исследование разрешает read-only public web/доступные authorized data и planning artifacts. Оно не разрешает создавать accounts, покупать subscriptions, подавать alpha applications, писать респондентам/креаторам, публиковать страницы, включать tracking или запускать рекламу. Paid API/credits используют только по имеющемуся явному бюджету; отсутствие доступа → gap/fallback, не секрет в чате и не выдуманный результат.

## Единый runtime pipeline

[Запуск от идеи до MVP-плана](pipeline.md) и [версионированный artifact contract](pipeline-contract.md). Это явный связанный scope; standalone commands не запускают pipeline автоматически.

[Кому/как продавать до build и после polish](go-to-market.md), [проверка цен](pricing.md), [даты и границы новых источников](go-to-market-sources.md). Runtime сохраняет шесть stages; B2B/B2C — ветки внутри acquisition, без дополнительного модельного запуска.
