---
name: product-compare
description: "Сравнить продукт с прямыми конкурентами и заменами по customer jobs, pricing, ограничениям и позиционированию. Использовать для /product:compare; опирается на GitLab/Buffer cases и evidence, без редизайна или внедрения."
---

# Product compare

Вызов `/product:compare {описание/объект}` или `$product-compare`. Работай только с вопросом этого скилла; остальные product-этапы не запускай автоматически.

## Обязательная база — до исследования

Прочитай [карту](../../docs/product/README.md), [evidence contract](../../docs/product/evidence.md), [workflow и память](../../docs/product/workflow.md), [data/API access](../../docs/product/data-sources.md), [primary sources](../../docs/product/sources.md), [case map](../../docs/product/cases/README.md), **[профильные кейсы](../../docs/product/cases/competitive-positioning.md)**, **[профильный guide](../../docs/product/compare.md)** и [шаблон результата](../../templates/product/competitors.md). Нет mandatory docs — сообщи blocker/попроси путь к checkout, не заменяй их общими знаниями. Объясни, какой case применяешь и почему, что из него не переносишь.

## Target и границы

Разреши symlink текущего SKILL.md и определи installed checkout отдельно от target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, product catalog/accepted ADR/revisions/handoffs и README. Нет описания — используй фактический project context; если бизнес/ключевая география неясны, задай один конкретный вопрос, продолжая независимую часть. Не переопределяй выбранный пользователем продукт/аналоги.

Scope — read-only public research, уже разрешённые источники данных, локальная проверка aggregate расчётов и запись planning/research artifacts. Не менять приложение, не запускать runtime/build/deploy, не создавать accounts/подписки/alpha applications, не устанавливать SDK/MCP, не публиковать и не отправлять сообщения, не активировать tracking/рекламу. Paid API/credits только в имеющемся explicit budget; credentials в чат/argv/logs/records не проси. API docs не означают подключённый API. Проверяй current capability/coverage/cost; недоступность сохраняй gap/fallback, без обхода доступа.

## Профильная работа

Задай общий JTBD/scenario/ICP и выбери релевантные direct/indirect/manual/no-change alternatives, обычно 3–5 с объяснением coverage. Пользовательский список сохрани. По GitLab сравнивай одинаковую job, по Buffer учитывай segment/paid unit/packaging, не только feature count. Историческую company strategy не выдавай за сегодняшнюю capability.

Для каждого: canonical identity/product/owner, jobs/segment, pricing billing/geo/tax/limits/as-of, flow/capability с evidence state, activation friction, trust/integrations/switching costs. Нет аккаунта — official demos/docs/screenshots с inference label, без выдуманного hands-on. Выведи minimum parity, candidate wedge/non-goals, response/switching risks и falsifying test. Объясни axes/weights positioning map; не суммируй arbitrary scores в гарантированную победу. Revenue/acquisition вопросы связывай с отдельными actual reports или оставляй unknown.

## Проверка, решения и передача

Каждый существенный claim/число связывай с E-ID, primary URL, publisher/publication/retrieval/as-of/period/geo/unit/method/limits и confidence rationale. Различай observed/disclosed/estimated/hypothesis/scenario/unknown; self-report/vendor story не causal evidence. Не выдумывай интервью, трафик, выручку, conversion/ROAS или графики данных. Сохраняй contradictory evidence, проверяй одинаковую basis и переносимость успешного кейса.

До зависимых решений записывай concise rationale/evidence/alternatives/consequences в target `.ai-development/product/<task>/decisions/`, обновляй общий INDEX, reuses/supersedes/history. Results в `revisions/vNNN/` с exact source refs; product INDEX каталогизирует reports, не дублирует ADR. Не перезаписывай чужой existing task/историю; при смене source отметь downstream refs needing review.

Проверь профильный DoD. Report status draft/research_complete/needs_input/blocked; experiments not_run до actual evidence. Research complete не PMF/market validated/build-ready. Итог краткий: вывод, основание, unknown/blocker, следующий дешёвый falsifying test и ссылки на report/ledger/ADR/handoff. Никакого автоматического перехода к execution.
