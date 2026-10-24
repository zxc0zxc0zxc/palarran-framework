# Использование

`/agent:improve {failed run + feedback} [--plan]` определяет target и skill checkout, читает applicable AGENTS/INDEX/contracts. --plan не исполняет reproduction/tests/модели/worktrees и не применяет application/skill patch; пишет protocol/ADR/proposal. Без флага можно выполнить конкретно разрешённые локальные reproduction/checks и scoped skill/docs fix. Не требовать нового согласования уже разрешённого; недостающие данные/цель уточнять только по существу. Paid APIs, training, установки, deploy/outreach не следуют из вызова.

Runtime полного checkout; portable agent plugin содержит guides/templates, runtime ставится отдельно оператором, ничего автоматически не скачивается:

```sh
python3 -m orchestrator.agent_improve prepare --input /private/improvement.json --target /absolute/target --output /private/new-packet
python3 -m orchestrator.agent_improve compare --packet /private/new-packet --proofs /private/proofs.json
```

Prepare read/write private local artifacts only, поэтому допустим как структурная подготовка в --plan; не вызывает agent_eval.create. Для исполнения сгенерированных suites отдельно existing `python3 -m orchestrator.agent_eval create/work/report` по [operations](../eval/operations.md). Сначала все baseline cases, затем candidate; один case на run. Никакого paid execution в tests. Модели одинаковые в паре; не эскалировать после FAIL. Shared budget один на все runs, включая incident/failed trials. При новом model admission перенести прошлые charges/reserves в carry, unknown сначала reconcile. Runtime reports исключают carry из current observed usage, поэтому cumulative evidence не суммирует carry дважды.

Proofs JSON: `{"baseline":{"case_id":{"state":"/private/state","run":"RUN_ID"}},"candidate":{"case_id":{"state":"/private/other-state","run":"OTHER_ID"}}}`. Case IDs должны совпадать frozen set, отсутствующая запись остаётся missing, не PASS. State/packet вне target. Report печатается как sanitized JSON; сохранение/Markdown handoff может сделать skill в target memory по [шаблону](../../../templates/agent-improve/review.md). Private packet содержит instructions/rubric; его не коммитить.

Публиковать только scoped reviewed diff + источники/decisions + sanitized comparison. Чужие dirty файлы не включать; rollback не reset --hard. Successful/failed few-shot examples хранить отдельно от private final evaluation holdout. Не создавать recurring optimizer/automation без запроса пользователя.

[Инертный example input](../../../templates/agent-improve/incident.example.json) показывает command-only fixture protocol. Все /absolute paths и synthetic fixture executor требуют замены/review; это не реальные skill/model результаты. Для model trials нужны separately approved native AI/usage policies с существующим общим budget/carry, никакая денежная квота примером не выделяется.
