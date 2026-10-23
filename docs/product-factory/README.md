# Product Factory: первый runtime

Runtime превращает конкретный SDD workflow в восстанавливаемый engineering run. Поверх него реализованы отдельные [product research → MVP-plan](../product/pipeline.md) и [ML](../ml/pipeline.md) pipelines. Долгоживущий автономный market-feedback loop остаётся следующим уровнем; runtime не выдумывает работу ради продолжения цикла.

Читать последовательно: [архитектура](architecture.md), [контракт](contract.md), [эксплуатация](operations.md), [источники](sources.md). План собственной реализации: [SDD v001](../../.ai-development/backend/2026-10-19-product-factory/plan.md).

Python >=3.9, POSIX, Git и локальный диск. Runtime не требует pip-пакетов, PostgreSQL или облака. Продукт живёт в отдельном Git repository. Skills читаются из ai-tools; решения продукта сохраняются в его `.ai-development/`. Runtime state содержит snapshot workflow, поэтому это приватные локальные данные, не Git-артефакт.

```sh
python3 -m orchestrator --help
python3 -m orchestrator create --workflow examples/product-factory/smoke.json --target /path/to/target --state /path/to/private-state
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator status --state /path/to/private-state --run RUN_ID
```

`create` создаёт owned detached Git worktree в state; исходный checkout не редактируется. `work` запускает доверенные команды: это явная граница исполнения. Демонстрационный workflow создаёт файл и проверяет его реальное содержимое. Адаптеры `codex`/`claude` запускают установленные авторизованные CLI; [Учёт токенов/стоимости](usage-accounting.md) сохраняет реальные usage receipts и останавливает AI stages при stage/run caps. Адаптеры: новые product runs заранее фиксируют модели и allocation по [политике бюджета](model-budgets.md); generic workflows без неё явно unmanaged. Ошибка доступа/лимита/уточнение приводят к остановке, а не обходу permissions.

Проверить runtime на disposable target одним запуском (без LLM и сети):

```sh
python3 scripts/factory_acceptance.py
python3 -m unittest discover -s tests -p 'test_factory_*.py' -v
```

[Шаблон backend agent](../../examples/product-factory/backend-agent.json) требует замены executable/skill/feature paths и verifiers на actual source DoD. Он не запускается автоматически. Для Claude заменить adapter/executable/allowlists; собственный login и разрешённые env настраиваются вне Git. Runtime добавляет explicit handoff: implemented разрешает независимые checks, needs_input приостанавливает run. Provider CLI не вызывается smoke-тестом.

## Product research pipeline

ML эксперименты также поддерживаются отдельным [ML pipeline](../ml/pipeline.md): семь planning skills → конкретный approval → supervised local/Modal training → independent benchmark. Private resource ledger дополняет AI usage accounting; [Modal adapter](../ml/modal-adapter.md) сохраняет identity, metrics, cancellation proof и billing reserves.

[Product pipeline](../product/pipeline.md) связывает пять product skills и итоговый synthesis MVP в существующем bounded runtime; engineering workflow API совместим.

## Agent evaluations

[Agent eval](../agent/eval/README.md) компилирует frozen suite в existing runtime workflow с independent final gates, private usage ledger и safe quality/cost/time report. CLI: `python3 -m orchestrator.agent_eval --help`.
