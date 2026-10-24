---
name: product-revenue
description: "Исследовать выручку и экономику аналогов: официальные раскрытия, founder reports, provider estimates и отдельные сценарии с диапазонами. Использовать для /product:revenue; неизвестные цифры не выдумывает."
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# Product revenue

Вызов `/product:revenue {описание/объект}` или `$product-revenue`. Работай только с вопросом этого скилла; остальные product-этапы не запускай автоматически.

## Обязательная база — до исследования

Прочитай [карту](../../docs/product/README.md), [evidence contract](../../docs/product/evidence.md), [workflow и память](../../docs/product/workflow.md), [data/API access](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), **[профильные кейсы](../../docs/product/cases/revenue-economics.md)**, **[профильный guide](../../docs/product/revenue.md)** и [шаблон результата](../../templates/product/economics.md). Нет mandatory docs — сообщи blocker/попроси путь к checkout, не заменяй их общими знаниями. Объясни, какой case применяешь и почему, что из него не переносишь.

## Target и границы

Разреши symlink текущего SKILL.md и определи installed checkout отдельно от target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, product catalog/accepted ADR/revisions/handoffs и README. Нет описания — используй фактический project context; если бизнес/ключевая география неясны, задай один конкретный вопрос, продолжая независимую часть. Не переопределяй выбранный пользователем продукт/аналоги.

Scope — read-only public research, уже разрешённые источники данных, локальная проверка aggregate расчётов и запись planning/research artifacts. Не менять приложение, не запускать runtime/build/deploy, не создавать accounts/подписки/alpha applications, не устанавливать SDK/MCP, не публиковать и не отправлять сообщения, не активировать tracking/рекламу. Paid API/credits только в имеющемся explicit budget; credentials в чат/argv/logs/records не проси. API docs не означают подключённый API. Проверяй current capability/coverage/cost; недоступность сохраняй gap/fallback, без обхода доступа.

## Профильная работа

Начни с Buffer transparency/economics case. Ищи regulator/audited filings, затем company/founder disclosures, named provider estimates и только потом conditional models. Разделяй entity vs product, recognized revenue/MRR/ARR/GMV/bookings/funding/valuation, currency/as-of/period/gross-net/perimeter. Company claim не audit. SEC facts сверяй с filing/taxonomy/unit/period/revisions, не складывай quarterly/YTD/duplicate facts.

Mobile net estimates проверь на store/country/paid-download/IAP/subscription coverage; не экстраполируй на весь company revenue. При недоступности public revenue допустим unknown. MRR=paid_accounts×monthly_ARPA требует сопоставимой базы; traffic→signup→paid без observed conversions — scenario, не «аналог зарабатывает». Для low/base/high дай inputs/E-IDs/formulas и dominant sensitivity, не statistical CI. Свою proposed economics/margin/CAC/cohort/payback отдели от конкурентов. Проверь арифметику локально по safe aggregate inputs, никаких paid calls без existing scope/budget.

## Проверка, решения и передача

Каждый существенный claim/число связывай с E-ID, primary URL, publisher/publication/retrieval/as-of/period/geo/unit/method/limits и confidence rationale. Различай observed/disclosed/estimated/hypothesis/scenario/unknown; self-report/vendor story не causal evidence. Не выдумывай интервью, трафик, выручку, conversion/ROAS или графики данных. Сохраняй contradictory evidence, проверяй одинаковую basis и переносимость успешного кейса.

До зависимых решений записывай concise rationale/evidence/alternatives/consequences в target `.ai-development/product/<task>/decisions/`, обновляй общий INDEX, reuses/supersedes/history. Results в `revisions/vNNN/` с exact source refs; product INDEX каталогизирует reports, не дублирует ADR. Не перезаписывай чужой existing task/историю; при смене source отметь downstream refs needing review.

Проверь профильный DoD. Report status draft/research_complete/needs_input/blocked; experiments not_run до actual evidence. Research complete не PMF/market validated/build-ready. Итог краткий: вывод, основание, unknown/blocker, следующий дешёвый falsifying test и ссылки на report/ledger/ADR/handoff. Никакого автоматического перехода к execution.

## Явный runtime pipeline

Если задача явно выдана как product pipeline stage, дополнительно прочитай [pipeline](../../docs/product/pipeline.md) и [artifact contract](../../docs/product/pipeline-contract.md). Выполни только назначенный stage, прочитай pinned cumulative context/reports/E-IDs/ADR и сохрани typed manifest + report; upstream artifacts не переписывай. `mvp` — synthesis mode product-define с [MVP template](../../templates/product/pipeline-mvp.md), не шестой skill. Runtime handoff implemented разрешает только independent checks, не подтверждает рынок. Standalone invocation не запускает pipeline автоматически.
