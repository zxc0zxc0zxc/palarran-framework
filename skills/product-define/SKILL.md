---
name: product-define
description: "Определить продукт по идее или README: ICP/JTBD, value proposition, business model, MVP и проверяемые критерии успеха на основе startup cases. Использовать для /product:define; исследование и planning, без реализации."
---

# Product define

Вызов `/product:define {описание/объект}` или `$product-define`. Работай только с вопросом этого скилла; остальные product-этапы не запускай автоматически.

## Обязательная база — до исследования

Прочитай [карту](../../docs/product/README.md), [evidence contract](../../docs/product/evidence.md), [workflow и память](../../docs/product/workflow.md), [data/API access](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), **[профильные кейсы](../../docs/product/cases/product-discovery.md)**, **[профильный guide](../../docs/product/define.md)** и [шаблон результата](../../templates/product/brief.md). Нет mandatory docs — сообщи blocker/попроси путь к checkout, не заменяй их общими знаниями. Объясни, какой case применяешь и почему, что из него не переносишь.

## Target и границы

Разреши symlink текущего SKILL.md и определи installed checkout отдельно от target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, product catalog/accepted ADR/revisions/handoffs и README. Нет описания — используй фактический project context; если бизнес/ключевая география неясны, задай один конкретный вопрос, продолжая независимую часть. Не переопределяй выбранный пользователем продукт/аналоги.

Scope — read-only public research, уже разрешённые источники данных, локальная проверка aggregate расчётов и запись planning/research artifacts. Не менять приложение, не запускать runtime/build/deploy, не создавать accounts/подписки/alpha applications, не устанавливать SDK/MCP, не публиковать и не отправлять сообщения, не активировать tracking/рекламу. Paid API/credits только в имеющемся explicit budget; credentials в чат/argv/logs/records не проси. API docs не означают подключённый API. Проверяй current capability/coverage/cost; недоступность сохраняй gap/fallback, без обхода доступа.

## Профильная работа

Определи user/buyer/approver и одну основную job/current workaround. Применяй Superhuman segmentation только при реальной eligible active cohort; pre-product требует problem/intent test, а не fabricated PMF. Amazon PR/FAQ адаптируй в краткий hypothetical customer narrative и FAQ рисков/цены. Сохрани existing business scope; не генерируй новый продукт вместо запроса.

Сформируй value proposition, candidate wedge/switching costs, proposed model/paid unit/price, MVP end-to-end outcome, non-goals и AC. Построй metric tree с cohort/denominator/window и предложенными thresholds, H-IDs/cheap falsifying tests/owner/caps/stop. Existing market/compare/revenue/acquisition reports связывай exact revisions; missing reports — gaps, не выдуманные выводы. Нарисуй business flow с failure/refusal и handoff к UX/SDD planning. Ни стиль, ни стек, ни разработку не выбирай вместо профильных этапов.

## Проверка, решения и передача

Каждый существенный claim/число связывай с E-ID, primary URL, publisher/publication/retrieval/as-of/period/geo/unit/method/limits и confidence rationale. Различай observed/disclosed/estimated/hypothesis/scenario/unknown; self-report/vendor story не causal evidence. Не выдумывай интервью, трафик, выручку, conversion/ROAS или графики данных. Сохраняй contradictory evidence, проверяй одинаковую basis и переносимость успешного кейса.

До зависимых решений записывай concise rationale/evidence/alternatives/consequences в target `.ai-development/product/<task>/decisions/`, обновляй общий INDEX, reuses/supersedes/history. Results в `revisions/vNNN/` с exact source refs; product INDEX каталогизирует reports, не дублирует ADR. Не перезаписывай чужой existing task/историю; при смене source отметь downstream refs needing review.

Проверь профильный DoD. Report status draft/research_complete/needs_input/blocked; experiments not_run до actual evidence. Research complete не PMF/market validated/build-ready. Итог краткий: вывод, основание, unknown/blocker, следующий дешёвый falsifying test и ссылки на report/ledger/ADR/handoff. Никакого автоматического перехода к execution.
