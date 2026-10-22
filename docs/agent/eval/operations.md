# Операции и границы

`/agent:eval {задача или suite} [--plan]` сначала читает mandatory guides и target memory. --plan пишет только protocol/rubric/ADR; не создаёт worktree и не запускает команды. Без флага выполнять только явно разрешённую локальную suite; платные model calls требуют конкретного budget и scope. В этом репозитории tests всегда offline.

CLI из полного checkout ai-tools (portable skill package содержит guides/templates, runtime отдельно):

```sh
python3 -m orchestrator.agent_eval create --suite /path/to/reviewed-suite.json --target /path/to/clean-target --state /path/to/private-state
python3 -m orchestrator.agent_eval work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator.agent_eval report --state /path/to/private-state --run RUN_ID
python3 -m orchestrator.agent_eval compare --state /path/to/private-state --run RUN_ID --other-run OTHER_ID
```

create не вызывает модели, но создаёт owned worktree. Для AI work нужен дополнительный `--allow-model-calls`; флаг — технический gate, не замена разрешению человека и общему budget. Настроить ai_policy/usage_policy, явно включить historical carry и прежние unknowns. Не создавать новый денежный лимит для сравнения или после failure. Повтор work сохраняет тот же ledger/лимит. Новая suite/run сама по себе не объединяет расход разных runs: координатор обязан перенести прежние charges/reserves в carry до нового admission. Поэтому автоматических повторных trials в v1 нет.

Budget stop срабатывает по наблюдаемым usage receipts/timeout; до первого события provider может превысить cap. Это не транзакционная гарантия денежного потолка провайдера. Для жёсткого финансового cap нужен отдельно ограниченный provider account/gateway; invoice сверяется отдельно.

Cancel/resolve/usage-reconcile — existing `python3 -m orchestrator` lifecycle. Unknown outcome не replay. Run fail-fast; для исправленного grader/нового trial нужна новая revision и пересмотр оставшегося общего бюджета. До reconciliation нельзя продолжать model measurements. CLI не делает install/auth/настройку аккаунтов/SSH/deploy.

Synthetic example `examples/agent-eval/suite.example.json` требует замены абсолютного Python path и пути к external check_build.py и работает только с disposable trusted clean Git target. Он создаёт структурированные ответы и проверяет их; это smoke контракта, не реальные результаты модели. Offline tests также проверяют настоящий Python bug-fix через внешний grader и fake provider receipts/over-budget stops.

Результаты/объяснения: target `.ai-development/agent-eval/<task>/` с protocol revision, references к private run, sanitized report, decisions и handoff. Не копировать private bundle/receipts/raw output в Git. Записывать выбранные fixtures, применимость источников, условия сравнения и NOT_RUN checks. Навигация по исходникам через optional fresh Graphify; отсутствие графа не отменяет чтение AGENTS/ADR.
