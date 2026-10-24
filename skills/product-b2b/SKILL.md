---
name: product-b2b
description: "Планировать продажи первым небольшим B2B-клиентам: квалификация компаний, проверка боли, оффер и outreach plan. Использовать для /product:b2b до разработки и после polish; только исследование, без отправки сообщений."
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# Product B2B

Вызов `/product:b2b {описание}` или `$product-b2b`. Самостоятельное исследование/планирование первых клиентов; другие команды не запускай автоматически.

## Сначала документация и контекст

До исследования прочитай [карта](../../docs/product/README.md), [evidence](../../docs/product/evidence.md), [workflow](../../docs/product/workflow.md), [данные/API](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), [go-to-market](../../docs/product/go-to-market.md), [цены](../../docs/product/pricing.md), [новые источники/даты](../../docs/product/go-to-market-sources.md), [профиль](../../docs/product/b2b.md), [профильные кейсы](../../docs/product/cases/b2b-first-customers.md) и [шаблон результата](../../templates/product/b2b-sales.md). Нет обязательной базы — blocker, не заменяй общими знаниями. Объясни переносимость кейса и что из него не копируешь.

Разреши symlink SKILL.md: installed checkout и target — разные корни. Прочитай [decision memory](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, accepted ADR/product reports/revisions и actual project context. Без описания используй README; если buyer/business/geo неясны, задай один конкретный вопрос и продолжай независимое исследование. Не подменяй продукт. Для B2B2C/marketplace раздели buyer/user/стороны и два плана вместо выдуманного единого ICP.

## Профильная работа

Применяй small-fit: независимая команда 1–30 человек или 1–3 точки и доступный buyer. Это операционный default, не правовая классификация. Корпоративный parent/enterprise procurement исключают; неизвестный размер/ownership — conditional, не qualified. Не расширяй сегмент ради количества.

Найди до 10 кандидатов через actual public company pages/каталоги/реестры/отзывы/вакансии. При недоборе покажи меньше. Для каждого: source/date size и ownership, buyer role/public business contact URL, observed trigger → pain hypothesis → вопрос, existing substitute, product-fit/ограничения. Не выдумывай контакты/бюджет/готовность купить. Similarweb — optional estimate; N/A не zero, не фильтр размера или отсутствия спроса. Без платного доступа используй публичные источники.

Составь bounded offer/pilot/support с actual capabilities и прозрачной value/cost hypothesis. План: 1–2 доступных пути к buyer, короткие черновики первого обращения/follow-up, маленький batch/cadence, owner, cash/time cap, stop и funnel до paid/retained с denominator/window. Все будущие контакты not_run; список кандидатов не согласие на outreach и не подтверждённые продажи.

## Бюджет, сохранение и готовность

До детализации спроси/прочитай actual cash cap/test cap/currency/window и time budget. Бюджет неизвестен → **cash cap=0**; paid кандидаты conditional. Research/model budget отдельно от sales/media. Полные обязательные расходы должны помещаться в cap; missing fee/quote/eligibility → gap. Не выдавай синтетические 3 000/10 000 ₽ примеры из docs за default/тариф/согласие потратить. Read-only public research и уже authorized data; paid API только в explicit budget. Не создавать accounts, не покупать, не отправлять outreach, не публиковать, не ставить tracking, не менять приложение/deploy. API docs не означают подключённый API; секреты не сохраняй.

Связывай существенные claims/цены с E/Q-ID, URL/publisher/date/as-of/geo/unit/method/limits/confidence; observed/disclosed/estimated/hypothesis/scenario/unknown не смешивать. До зависимого выбора запиши rationale/evidence/alternatives/consequences/review trigger в target `.ai-development/product/<task>/decisions/`; INDEX/handoff и `revisions/vNNN/` обновляй без стирания истории. Не хранить результаты в installed skill package. При изменении product/source revisions пометь downstream needing review.

Сначала checkpoint **кому/как продаём до implementation**, после polish — delta actual capabilities/offer/onboarding/quotes. Report status draft/research_complete/needs_input/blocked, отдельно ready_to_test/conditional/needs_input; ready_to_test — полнота предложения, не разрешение запускать и не market validation. Unknowns и недобор не прячь. Финал: сегмент/доступный путь, ограничения/caps, следующий дешёвый falsifying test и ссылки report/evidence/ADR/handoff.

## Если назначен runtime acquisition stage

Прочитай [pipeline](../../docs/product/pipeline.md) и [artifact contract](../../docs/product/pipeline-contract.md). Применяй профиль **внутри текущего acquisition attempt**, с его stage-prefixed E-IDs/report/manifest и pinned upstream refs; не создавай седьмой stage/вложенный CLI run. Standalone эти envelopes не обязательны. MVP synthesis получает sales/growth plan и sellability gaps; independent verifier проверяет integrity, не доказательство спроса/продаж.
