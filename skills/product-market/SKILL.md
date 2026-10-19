---
name: product-market
description: "Исследовать рынок и спрос по startup cases: сегменты, search trends, альтернативы, TAM/SAM/SOM и проверка гипотез с источниками. Использовать для /product:market; не запускает рекламу или продуктовую разработку."
---

# Product market

Вызов `/product:market {описание/объект}` или `$product-market`. Работай только с вопросом этого скилла; остальные product-этапы не запускай автоматически.

## Обязательная база — до исследования

Прочитай [карту](../../docs/product/README.md), [evidence contract](../../docs/product/evidence.md), [workflow и память](../../docs/product/workflow.md), [data/API access](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), **[профильные кейсы](../../docs/product/cases/market-validation.md)**, **[профильный guide](../../docs/product/market.md)** и [шаблон результата](../../templates/product/research.md). Нет mandatory docs — сообщи blocker/попроси путь к checkout, не заменяй их общими знаниями. Объясни, какой case применяешь и почему, что из него не переносишь.

## Target и границы

Разреши symlink текущего SKILL.md и определи installed checkout отдельно от target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, product catalog/accepted ADR/revisions/handoffs и README. Нет описания — используй фактический project context; если бизнес/ключевая география неясны, задай один конкретный вопрос, продолжая независимую часть. Не переопределяй выбранный пользователем продукт/аналоги.

Scope — read-only public research, уже разрешённые источники данных, локальная проверка aggregate расчётов и запись planning/research artifacts. Не менять приложение, не запускать runtime/build/deploy, не создавать accounts/подписки/alpha applications, не устанавливать SDK/MCP, не публиковать и не отправлять сообщения, не активировать tracking/рекламу. Paid API/credits только в имеющемся explicit budget; credentials в чат/argv/logs/records не проси. API docs не означают подключённый API. Проверяй current capability/coverage/cost; недоступность сохраняй gap/fallback, без обхода доступа.

## Профильная работа

Зафиксируй customer unit, buyer/job, language/region/window и query clusters problem/alternative/purchase intent. Сопоставь доступные независимые семейства evidence: demand/search, реальные complaints/workarounds, spending/disclosures/statistics. Ищи отрицательные сигналы и альтернативные объяснения. Buffer pricing intent не равен оплате; Airbnb early manual work не доказывает масштабируемый рынок.

Trends API и UI имеют разные scaling/access contracts: сохрани term/topic/geo/window/property/basis, seasonality/news effects, не превращай относительный индекс в volume или paying buyers. Недоступный API не означает нулевой спрос. TAM/SAM/SOM считай bottom-up лишь при обоснованных inputs, с scope/dedup/price/horizon/capacity; иначе qualitative/unknown. Реальные time series отображай с units/source, при отсутствии ряда используй diagram сегментов/воронки. Итог — research report и proposed cheapest validation, не утверждение о состоявшемся market validation.

## Проверка, решения и передача

Каждый существенный claim/число связывай с E-ID, primary URL, publisher/publication/retrieval/as-of/period/geo/unit/method/limits и confidence rationale. Различай observed/disclosed/estimated/hypothesis/scenario/unknown; self-report/vendor story не causal evidence. Не выдумывай интервью, трафик, выручку, conversion/ROAS или графики данных. Сохраняй contradictory evidence, проверяй одинаковую basis и переносимость успешного кейса.

До зависимых решений записывай concise rationale/evidence/alternatives/consequences в target `.ai-development/product/<task>/decisions/`, обновляй общий INDEX, reuses/supersedes/history. Results в `revisions/vNNN/` с exact source refs; product INDEX каталогизирует reports, не дублирует ADR. Не перезаписывай чужой existing task/историю; при смене source отметь downstream refs needing review.

Проверь профильный DoD. Report status draft/research_complete/needs_input/blocked; experiments not_run до actual evidence. Research complete не PMF/market validated/build-ready. Итог краткий: вывод, основание, unknown/blocker, следующий дешёвый falsifying test и ссылки на report/ledger/ADR/handoff. Никакого автоматического перехода к execution.
