# Context

Запрос: подключить Modal training adapter, metrics, cost accounting, budget stop и remote cancellation; documentation first, no paid test launches. Прочитаны INDEX, принятый runtime-pipeline/0001, docs/ml и существующие runtime hooks. Прежнее local-only ограничение расширено отдельным trusted Modal Sandbox supervisor, а не обёрткой modal run.

Primary references retrieved 2026-10-22: Modal Sandbox, App.lookup, Image.from_id, Volume.read_file/commit, Workspace.billing report/summary. Billing partial final intervals не включаются, workspace invoice не job invoice. Поэтому автоматически actual cost не выдумывается: delayed billing остаётся зарезервированным до operator reconciliation.

Реальный Modal SDK, аккаунт и cloud не вызывались. Все API-facing tests используют fake objects/async methods; image/data/weights остаются отдельной operator preparation. Target auth/secrets/addresses не добавлены. Существующие ML skills и незакоммиченные файлы сохранены.
