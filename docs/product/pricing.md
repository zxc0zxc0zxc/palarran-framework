# Цены: проверить, посчитать, отсеять дорогое

Сначала реальный cash cap/валюта/период и время владельца. Без бюджета cash cap=0. Не подменять анализ цен «средним по рынку» из памяти. [Источники и даты](go-to-market-sources.md).

## Price register

Для каждой позиции сохранить: Q-ID, площадка/author/формат/география, URL и retrieval timestamp, publication/as-of или unknown, currency, unit (пост/видео/1000 impressions/период), list price vs binding quote vs platform floor vs scenario vs unknown, доступность/срок действия, минимальный заказ и длительность, VAT/налоги/fees, production/доставка/права, условия снятия/замены и measurement. Неизвестное явно перечислить; не считать VAT/fees включёнными без источника. FX — отдельный dated source либо оставить исходную валюту и conditional conversion.

Full test cash = inventory/media + production + обязательные fees/taxes/fulfilment. При несовместимых единицах или unknown обязательных расходах результат unknown/диапазон, а не уверенная сумма. Отдельно time budget и бартерная себестоимость. Minimum budget не ожидаемый spend/CAC; не складывать вложенные campaign/ad group limits как независимые расходы.

Статус: eligible / rejected_over_cap / conditional_quote / conditional_eligibility / unavailable. В исполнимый shortlist проходят только известные доступные варианты под cap; отсутствие бесплатного способа фиксируется gap. Публичные 0 ₽, stock=0 или закрытая аналитика могут быть placeholder — **не доказательство бесплатного размещения**.

## Наблюдения 2026-10-19 — примеры отсева, не предложение покупки

| Источник | Что удалось прочитать | Значение для маленького бюджета | Ограничение |
|---|---|---|---|
| [TikTok official daily budgets](https://ads.tiktok.com/resources/help/article/about-daily-budgets) | Campaign budget должен превышать $50, ad group daily — $20; lifetime ad group зависит от дней | Paid Ads Manager часто не подходит нулевому/малому cap; сравнить minimum feasible test с cap | Документ updated February 2025; вложенные уровни не суммировать механически; проверить актуальный UI/account |
| [Telegram Ads](https://ads.telegram.org/getting-started) | Minimum CPM 0.1 TON | Это floor за 1000 показов, не цена Telegram-поста и не полный test budget | Auction/формат/условия/TON FX меняются; нет гарантии фактического CPM |
| [Telega.in TikTok catalog](https://telega.in/catalog_tiktok), @connoralik | List price 461 538 ₽ | При cash cap=0 или синтетическом примере cap=3 000 ₽ — rejected_over_cap без дальнейшей закупочной проработки | Публичная карточка, не персональный binding quote; fees/права/availability неизвестны |
| [Telega.in Telegram catalog](https://telega.in/catalog) | В просмотренных карточках 0 ₽ / stock=0 / недоступные метрики | unavailable или conditional_quote, **не free inventory** | Рендер/placeholder не подтверждает ставку; не регистрируемся ради заполнения отчёта |
| Собственный контент | Cash может быть 0 при уже доступных ресурсах | Кандидат, если действительно есть доступ и время | Производство/модерация/охваты неизвестны, время не бесплатно |

Дешёвый действующий прайс Telegram-поста/микроблогера в этом исследовании **не подтверждён**. Скилл должен искать свежие релевантные публичные условия в контексте конкретного продукта; иначе needs_quote. Историческая статья BuduFood не тариф 2026 года. Прайсы освежать при подготовке целевого плана и после polish; source timestamp не срок действия предложения.

Синтетический пример cap=3 000 ₽/тест и 10 000 ₽/14 дней можно использовать только для демонстрации отсева, обозначив scenario. Эти числа не market benchmark, не default бюджета и не разрешение тратить. При отсутствии маржи/retention любой target CAC остаётся проверяемым предположением.
