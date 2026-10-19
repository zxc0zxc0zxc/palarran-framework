---
name: product-acquisition
description: "Исследовать каналы аудитории аналогов: paid search, TikTok/Meta, native/creator, organic/SEO, referral и partnerships; составить evidence-backed funnel и тесты. Использовать для /product:acquisition; без запуска рекламы и outreach."
---

# Product acquisition

Вызов `/product:acquisition {описание/объект}` или `$product-acquisition`. Работай только с вопросом этого скилла; остальные product-этапы не запускай автоматически.

## Обязательная база — до исследования

Прочитай [карту](../../docs/product/README.md), [evidence contract](../../docs/product/evidence.md), [workflow и память](../../docs/product/workflow.md), [data/API access](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), **[профильные кейсы](../../docs/product/cases/acquisition-growth.md)**, **[профильный guide](../../docs/product/acquisition.md)** и [шаблон результата](../../templates/product/channels.md). Нет mandatory docs — сообщи blocker/попроси путь к checkout, не заменяй их общими знаниями. Объясни, какой case применяешь и почему, что из него не переносишь.

## Target и границы

Разреши symlink текущего SKILL.md и определи installed checkout отдельно от target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, product catalog/accepted ADR/revisions/handoffs и README. Нет описания — используй фактический project context; если бизнес/ключевая география неясны, задай один конкретный вопрос, продолжая независимую часть. Не переопределяй выбранный пользователем продукт/аналоги.

Scope — read-only public research, уже разрешённые источники данных, локальная проверка aggregate расчётов и запись planning/research artifacts. Не менять приложение, не запускать runtime/build/deploy, не создавать accounts/подписки/alpha applications, не устанавливать SDK/MCP, не публиковать и не отправлять сообщения, не активировать tracking/рекламу. Paid API/credits только в имеющемся explicit budget; credentials в чат/argv/logs/records не проси. API docs не означают подключённый API. Проверяй current capability/coverage/cost; недоступность сохраняй gap/fallback, без обхода доступа.

## Профильная работа

Прочитай Ahrefs/Airbnb/SweetyTreatyCo cases и проверь stage/business-model fit. Собери per-analogue observed signals по paid search/social, organic content, creators/native, referrals/partners/community: advertiser/domain identity, geo/language/date, creative/landing, delivery/sponsorship classification и coverage. Нативный формат не равно organic: creator post может иметь sponsorship и paid amplification; неизвестный payment оставь unknown.

Рекламная библиотека не раскрывает полный P&L; ads count/duration/views/reach не доказывают spend/CAC/ROAS/retained customers. Отсутствие в archive не отсутствие канала. Нарисуй observed/hypothesized acquisition→activation→payment→retention funnel с unknown edges. Составь stage-aware shortlist и future experiment cards: job/offer/creative/channel, eligible unit, primary outcome/denominator, attribution window/dedup, guardrails, sample/time/cost rationale, cap/stop/owner. Учитывай production/founder/creator/ad costs и margin/retention. Не запускай кампании, не ставь pixels, не пиши креаторам.

## Проверка, решения и передача

Каждый существенный claim/число связывай с E-ID, primary URL, publisher/publication/retrieval/as-of/period/geo/unit/method/limits и confidence rationale. Различай observed/disclosed/estimated/hypothesis/scenario/unknown; self-report/vendor story не causal evidence. Не выдумывай интервью, трафик, выручку, conversion/ROAS или графики данных. Сохраняй contradictory evidence, проверяй одинаковую basis и переносимость успешного кейса.

До зависимых решений записывай concise rationale/evidence/alternatives/consequences в target `.ai-development/product/<task>/decisions/`, обновляй общий INDEX, reuses/supersedes/history. Results в `revisions/vNNN/` с exact source refs; product INDEX каталогизирует reports, не дублирует ADR. Не перезаписывай чужой existing task/историю; при смене source отметь downstream refs needing review.

Проверь профильный DoD. Report status draft/research_complete/needs_input/blocked; experiments not_run до actual evidence. Research complete не PMF/market validated/build-ready. Итог краткий: вывод, основание, unknown/blocker, следующий дешёвый falsifying test и ссылки на report/ledger/ADR/handoff. Никакого автоматического перехода к execution.
