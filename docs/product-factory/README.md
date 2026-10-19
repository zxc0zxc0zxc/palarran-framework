# Product Factory: первый runtime

Цель — превратить конкретный SDD workflow в восстанавливаемый engineering run. Product discovery, маркетинговые гипотезы и feedback loop остаются следующим уровнем; runtime не выдумывает работу ради продолжения цикла.

Читать последовательно: [архитектура](architecture.md), [контракт](contract.md), [эксплуатация](operations.md), [источники](sources.md). План собственной реализации: [SDD v001](../../.ai-development/backend/2026-10-19-product-factory/plan.md).

Python >=3.9, POSIX, Git и локальный диск. Runtime не требует pip-пакетов, PostgreSQL или облака. Продукт живёт в отдельном Git repository. Skills читаются из ai-tools; решения продукта сохраняются в его `.ai-development/`. Runtime state содержит snapshot workflow, поэтому это приватные локальные данные, не Git-артефакт.

```sh
python3 -m orchestrator --help
python3 -m orchestrator create --workflow examples/product-factory/smoke.json --target /path/to/target --state /path/to/private-state
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator status --state /path/to/private-state --run RUN_ID
```

`create` создаёт owned detached Git worktree в state; исходный checkout не редактируется. `work` запускает доверенные команды: это явная граница исполнения. Демонстрационный workflow создаёт файл и проверяет его реальное содержимое. Адаптеры `codex`/`claude` запускают установленные авторизованные CLI; модель не выбирается вместо пользователя. Ошибка доступа/лимита/уточнение приводят к остановке, а не обходу permissions.
