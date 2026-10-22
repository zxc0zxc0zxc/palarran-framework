# Контекст

Запрос: добавить Graphify для экономии контекста, AGENTS authoring rules и per-module instructions. Репозиторий — библиотека 25 skills и bounded orchestrator, а не target SaaS с придуманными services. Прочитаны INDEX, существующий root AGENTS, incremental-context ADR и current source. Старые незакоммиченные ML изменения сохранены.

Использована официальная Graphify Labs distribution graphifyy 0.9.93. PyPI metadata и wheel inspected; wheel hash сверён. Изолированный Python 3.12 runtime нужен только инструменту, runtime/tests остаются совместимыми с system Python 3.9. SDK/API ключи не передаются extraction/query process; setup не меняет global agents/hooks/config.

Общие исходные root ограничения сохранены в docs/skills/domain-contracts.md; exact historical snapshot prior-AGENTS.md нужен для review переноса, не новый действующий policy. Root маршрутизирует к нужному разделу/AGENTS. В target приложениях ближайшие инструкции создаются только по реальным boundaries при implementation authorization; планирование пишет proposal, не меняет target instructions.

No LLM calls, cloud Graphify account, MCP/agent installation, training/deploy/outreach/ad spend. Actual query имеет отдельную freshness/size guard; исходники/решения остаются authority. Результаты и limitations — в handoff.
