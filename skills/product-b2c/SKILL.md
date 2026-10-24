---
name: product-b2c
description: "Определить B2C-аудиторию и бесплатные или дешёвые каналы первых клиентов, включая native video, блогеров и Telegram; проверить цены и составить план тестов. Использовать для /product:b2c; без публикаций и закупки рекламы."
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# Product B2C

Вызов `/product:b2c {описание}` или `$product-b2c`. Самостоятельное исследование/планирование первых клиентов; другие команды не запускай автоматически.

## Сначала документация и контекст

До исследования прочитай [карта](../../docs/product/README.md), [evidence](../../docs/product/evidence.md), [workflow](../../docs/product/workflow.md), [данные/API](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), [go-to-market](../../docs/product/go-to-market.md), [цены](../../docs/product/pricing.md), [новые источники/даты](../../docs/product/go-to-market-sources.md), [профиль](../../docs/product/b2c.md), [профильные кейсы](../../docs/product/cases/b2c-frugal-growth.md) и [шаблон результата](../../templates/product/b2c-growth.md). Нет обязательной базы — blocker, не заменяй общими знаниями. Объясни переносимость кейса и что из него не копируешь.

Разреши symlink SKILL.md: installed checkout и target — разные корни. Прочитай [decision memory](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, accepted ADR/product reports/revisions и actual project context. Без описания используй README; если buyer/business/geo неясны, задай один конкретный вопрос и продолжай независимое исследование. Не подменяй продукт. Для B2B2C/marketplace раздели buyer/user/стороны и два плана вместо выдуманного единого ICP.

## Профильная работа

Выдели узкий geo/language/job/trigger сегмент, user/payer, текущую замену и offer по actual product revision. Исследуй российский и иностранный startup mechanism; объясни stage/audience/platform fit и границы self-report. Не обещай канал/дешёвый CAC по чужим охватам.

Порядок: собственный полезный контент и доступные нишевые сообщества/партнёры → релевантные маленькие creators/native TikTok/short video и бартер → конкретные Telegram каналы/посты с публичными media kits → paid platform tests только под cap. Native не обязательно organic; бартер включает себестоимость, доставку, production и время. Проверяй current geography/eligibility; недоступность не обходить.

Покажи максимум 2–3 обоснованных теста с конкретной площадкой/автором/intent group, creative/CTA, price Q-ID/date/currency/unit/quote class, полной стоимостью, доступом и outcome/denominator/window/attribution/cap/stop/owner. Дорогие минимальные тесты исключи сразу; unknown quote или 0-placeholder не free placement. Без платящего/retained outcome не называй views/registrations actual CAC/PMF. Все тесты not_run, никаких публикаций/контактов/покупок.

## Бюджет, сохранение и готовность

До детализации спроси/прочитай actual cash cap/test cap/currency/window и time budget. Бюджет неизвестен → **cash cap=0**; paid кандидаты conditional. Research/model budget отдельно от sales/media. Полные обязательные расходы должны помещаться в cap; missing fee/quote/eligibility → gap. Не выдавай синтетические 3 000/10 000 ₽ примеры из docs за default/тариф/согласие потратить. Read-only public research и уже authorized data; paid API только в explicit budget. Не создавать accounts, не покупать, не отправлять outreach, не публиковать, не ставить tracking, не менять приложение/deploy. API docs не означают подключённый API; секреты не сохраняй.

Связывай существенные claims/цены с E/Q-ID, URL/publisher/date/as-of/geo/unit/method/limits/confidence; observed/disclosed/estimated/hypothesis/scenario/unknown не смешивать. До зависимого выбора запиши rationale/evidence/alternatives/consequences/review trigger в target `.ai-development/product/<task>/decisions/`; INDEX/handoff и `revisions/vNNN/` обновляй без стирания истории. Не хранить результаты в installed skill package. При изменении product/source revisions пометь downstream needing review.

Сначала checkpoint **кому/как продаём до implementation**, после polish — delta actual capabilities/offer/onboarding/quotes. Report status draft/research_complete/needs_input/blocked, отдельно ready_to_test/conditional/needs_input; ready_to_test — полнота предложения, не разрешение запускать и не market validation. Unknowns и недобор не прячь. Финал: сегмент/доступный путь, ограничения/caps, следующий дешёвый falsifying test и ссылки report/evidence/ADR/handoff.

## Если назначен runtime acquisition stage

Прочитай [pipeline](../../docs/product/pipeline.md) и [artifact contract](../../docs/product/pipeline-contract.md). Применяй профиль **внутри текущего acquisition attempt**, с его stage-prefixed E-IDs/report/manifest и pinned upstream refs; не создавай седьмой stage/вложенный CLI run. Standalone эти envelopes не обязательны. MVP synthesis получает sales/growth plan и sellability gaps; independent verifier проверяет integrity, не доказательство спроса/продаж.
