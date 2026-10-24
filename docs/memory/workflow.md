# Workflow скиллов

`/memory:recall {task} [--plan]`: читать target INDEX/accepted ADR/applicable AGENTS, затем optional fresh Graphify и bounded memory query. Сначала3карточки, затем нужные originals/соседи/артефакты. Цитировать ID/source/status/date/limitations и applicability к current target. При отсутствии сервиса — local source fallback с явным NOT_RUN, не выдумывать память. `--plan` пишет только query plan, без service/SSH calls.

`/memory:learn {result} [--plan]`: после проверки задачи извлечь максимум3portablelessons. Проверить diff/evidence/privacy/rights; не загружать весь repo/session. Записать rationale в local target journal до propose. Show candidate/dedup/conflicts; reviewer-only promotion после проверки sources. Не выдавать agent token как право promote. После reuse feedback связывает exact source/subject/проверки. `--plan` только draft, без uploads.

`/vps:inspect [target] [--plan]`: строгий readonly inventory без sudo/install/логов/env/dbdump. Использовать verified SSH alias или explicit host/user/port с trusted known_hosts. Неизвестный host key — остановить подключение и получить fingerprint из доверенного канала; не accept-new/no. В env держать references к ключам, не private key/password. Inventory private, sanitized summary в target memory.

`/vps:manage {operation} [--plan]`: сначала inspect и согласованный конкретный change plan с affectedservices/ports/rollback/backup/checks. Подготовить всё локально и показать результат перед approval если фактического deploy authorization ещё нет. Операции deploy/restart/backup/restore/upgrade/firewall не разрешены одним наличием credentials. Default создаёт reviewable config; apply только в уже разрешённом scope. Unknown SSH outcome — reconcile status, не replay. Не совмещать с app CI/CD SSH deploy.

Memory runtime выполняет только явные API/MCP operations. Подключение ко всем агентам/automatic hooks/global config требует отдельной настройки после review; v001 даёт инертный пример. Существующие навыки наследуют общую памятку: optional cross-project recall полезен перед решением, но local ADR/AGENTS authoritative; каждый reuse/result сохраняется локально.
