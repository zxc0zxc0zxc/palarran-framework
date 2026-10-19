# /product:define — сам продукт

Сначала [Superhuman/Amazon](cases/product-discovery.md), [evidence](evidence.md), [workflow](workflow.md). Наша рекомендация — начать с customer outcome и узкого сегмента, затем согласовать scope. Это перенос кейсов, не обещание их результата.

Прочитать description или target README, existing product/UX/architecture/constraints и decisions. Existing бизнес не заменять более модным. Уточнить business process, если user/buyer, job или transaction непонятны; не писать всё подряд для B2B и B2C.

Выход по [brief](../../templates/product/brief.md):

- ICP и кто платит/пользуется/принимает решение; job/trigger/current workaround, частота/тяжесть проблемы и evidence.
- Одно ясное value proposition, отличие от ближайшей замены, ограничения/неудобства и switching costs.
- Proposed business model, оплачиваемая единица, free/paid boundary и стоимость обслуживания. Цена — гипотеза без customer validation.
- MVP с одним end-to-end useful outcome, scope/non-goals, assumptions/risks и dependency on market/compare/revenue/acquisition revisions, когда они уже есть. Отсутствующие refs — gaps, не повод создавать фальшивые исследования.
- Metric tree: ценность → activation → повторное использование/retention → оплата; событие, cohort, denominator/window, proposed threshold и его основание. [Google HEART](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/) помогает связать цели и сигналы; не все категории нужны любому продукту.
- Критические H-IDs, cheapest falsifying test, success/stop/pivot criteria, owner/budget/window. Числовые targets помечать proposed, не benchmark из соседней отрасли.

Схема business flow обязательна: actor → trigger → useful outcome → delivery/payment/return path, включая ключевой failure/отказ. UX handoff перечисляет процессы/сущности/ограничения; не навязывает экраны, стиль или стек. Условия инженерного planning handoff: определён пользовательский outcome, scope/AC, договорённости/unknowns и source revision. Это не запуск build.

DoD: brief согласован с actual context, каждый важный вывод traceable, решение build/test/stop аргументировано либо needs_input, риски/эксперименты не названы выполненными.
