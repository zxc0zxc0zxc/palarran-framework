# Product pipeline v001: идея → обоснованный MVP-план

Сначала [case map](cases/README.md), [общий workflow](workflow.md), [evidence](evidence.md) и [artifact contract](pipeline-contract.md). Pipeline исполняет существующие skills и сохраняет их границы. Методы Superhuman/Buffer/GitLab/Ahrefs остаются обязательными; композиция и hash gates — наша инженерная адаптация, не заявленный workflow этих компаний. [Источники/даты](sources.md).

```mermaid
flowchart LR
    I[Идея + project context] --> D[define: гипотеза]
    D --> M[market: спрос и сегменты]
    M --> C[compare: аналоги и wedge]
    C --> R[revenue: экономика / unknown]
    R --> A[acquisition: каналы / tests]
    A --> S[product-define: synthesis MVP]
    S --> V[Independent artifact gates + final rerun]
    V --> P[plan / validate / pivot / stop]
```

Stages serial, cumulative prefix передаёт actual context/источники/ADR; final mvp использует тот же product-define с synthesis задачей. Не добавляем новый standalone skill. Содержание источников не подменять summaries предыдущего агента: читать pinned reports/manifests/ADR и relevant primary refs. Не нужно заново собирать уже пригодное evidence, но свежесть/противоречия проверяются.

## Запуск

```sh
python3 -m orchestrator product-create --idea-file /path/to/idea.md --target /path/to/product-repo --state /path/to/private-state --adapter codex --agent /absolute/path/to/codex --skills-root /path/to/ai-tools
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator status --state /path/to/private-state --run RUN_ID
```

Idea file regular non-symlink UTF-8, непустой, <=32KiB; без credentials/customer PII. CLI не вызывает модель при create. Explicit adapter codex/claude и installed executable, авторизация вне workflow. Перед work create/status показывает immutable routing: все шесть research/synthesis stages получают planning модель (Codex gpt-6.1-sol/high или Claude opus/high), по одному launch, всего 6 launches / 30 условных units. `--ai-policy` задаёт собственные profiles/caps до create; это budget запусков. Дополнительный `usage_policy` включает реальные token receipts и observed USD stop: defaults 600000 tokens/$12 run, 100000/$2 stage, включая retries; `--usage-policy` заменяет их до create. Codex cost — explicit pinned API rate estimate, Claude — reported CLI cost, оба не равны счёту/подписке. Missing telemetry останавливает pipeline, unknown не считается нулём. Подробный contract: `docs/product-factory/usage-accounting.md` в полном runtime checkout. Generic workflow поддерживает explicit task retry allocations, product default повторов не выделяет. Plain `resolve` не пополняет бюджет и при исчерпании stage останавливает run. Default environment PATH/HOME означает доступ к configured CLI auth/config; это trusted workflow, не sandbox. `--run-seconds` default 7200, `--task-seconds` 900, `--max-attempts` 2; existing runtime maxima действуют. Ожидание clarification расходует wall deadline, attempts не обнуляются. Paid research/API calls не разрешаются автоматически; dollar cap runtime не гарантирует.

Source bundle из семи SKILL.md, docs/product, shared memory guide и templates/product хешируется. Нет обязательного файла, source symlink/изменение bundle, старые dependency hashes, application edits или altered Git HEAD → verifier failure. Параллельно редактировать skills root во время run нельзя; для стабильного запуска использовать отдельный pinned checkout. Источник runtime verifier — trusted local code.

`product-create` создаёт pipeline UUID/context и owned run worktree. Context записывается до pending run admission через initializer; ошибка оставляет рабочие файлы для диагностики, без выполнения model task. Исходный target checkout не меняется. Status/export включает product.pipeline_id, mvp_plan path и после successful gates recommendation; market_validated=false. Results живут в worktree:

```text
.ai-development/product/pipeline-<pipeline_id>/
  context.json                        # immutable idea/baseline/source digest/revision
  decisions/                          # canonical ADR, per-stage unique IDs
  stages/define/stage.json             # versioned envelope
  stages/define/report.md              # краткий narrative + E/ADR refs
  stages/market/...                    # остальные stages
  stages/compare/...
  stages/revenue/...
  stages/acquisition/...
  stages/mvp/stage.json
  stages/mvp/report.md                 # итоговый MVP-план и verdict
```

Общий target INDEX и product INDEX обновляются без стирания existing entries. Каждый stage создаёт собственные E/claim/unknown IDs и ADR; ссылки на prior IDs разрешены, копировать их с новым смыслом нельзя. Private runtime receipt фиксирует canonical manifest hash: финальный stable rerun отклоняет даже согласованную перезапись hash chain. После прошедшего gate stage immutable: downstream только читает. Draft до gate можно исправить после needs_input с сохранением предыдущего attempt в history; accepted ADR не стирать. Observed failure без replay-safe → failed, новая revision/run для пересмотра scope; expired lease → reconciliation existing runtime.

## Финальное решение

[MVP template](../../templates/product/pipeline-mvp.md) задаёт структуру narrative, artifact schema остаётся в contract. MVP report включает target/ICP/JTBD, competitor wedge, value proposition/model, scope/non-goals, requirements/AC/priorities, metric/validation plan, economics/channel assumptions, risks/open questions и UX/engineering planning handoff. Каждая requirement и experiment имеет E/ADR refs. Все inherited unknowns перечислить в final disposition: resolved с evidence/ADR либо unresolved. Нельзя тихо потерять неудобную цифру/источник.

`plan` — обоснованная рекомендация следующего planning scope, без критичных unresolved; `validate` — сначала рыночный тест; `pivot`/`stop` — аргументированная смена/остановка. Любой verdict завершает bounded pipeline и может быть artifact-verified. `market_validated=false` всегда: план не выполняет исследования пользователей/оплату/рекламные эксперименты сам. Critical ambiguity о бизнесе/полномочиях → needs_input/question.md; ответ через existing resolve с сохранённой причиной.

Machine gates проверяют структуру/целостность/traceability и allowed changes, а не правдивость источников, достаточность выборки, качество стратегии или реальную готовность рынка. Перед engineering start нужен содержательный review report/primary refs/решений. Runtime не запускает UX/build/ads/deploy автоматически.

Fingerprint включает product artifacts/decision INDEX даже при target gitignore для .ai-development; статус станет stale после изменения таких deliverables. Остальные ignored cache/runtime paths остаются вне identity.

## B2B/B2C внутри acquisition

Runtime сохраняет define → market → compare → revenue → acquisition → mvp: шесть CLI attempts при одном успешном attempt/stage. Acquisition читает и применяет `/product:b2b` или `/product:b2c` внутри своего report по buyer/user; mixed модель разделяет стороны. Дополнительного task/агента/CLI run нет; model budgets не увеличиваются. Семь skill entrypoints, включая оба sales/growth профиля, pinned source digest.

Перед engineering synthesis требует содержательный [sellability review](go-to-market.md): small-fit candidates или конкретная B2C аудитория/каналы, supported offer, full costs/caps и доступный дешёвый тест. Unknown cash cap=0, дорогие/неизвестные размещения не проходят paid shortlist. После polish обновить revision/claims/quotes отдельной research задачей, без автоматического запуска outreach.

Verifier доказывает artifact integrity/traceability, не полноту sales narrative, реальную боль/выручку/цену или рыночную валидацию. Человек/агент-review обязан оценить содержание; эти поля не добавляют ложный machine-verifiable market gate.

## Продолжение сохранённого prefix

`product-continue --state STATE --target ORIGINAL_CLEAN_TARGET --source SAVED_WORKTREE --pipeline ID --through define --skills-root PINNED_ORIGINAL_SKILLS --agent /absolute/codex --route b2b --usage-policy REVIEWED_JSON --budget-ceiling ORIGINAL_USD` создаёт отдельный owned run, не выполняя модель. Original target HEAD обязан совпасть с original context.baseline. Define/context/ADR/report/evidence копируются byte-exact; workflow-pinned import receipt и независимый original verifier выполняются до model stage и повторяются в final checks. Прежний failed state не редактируется/не называется verified.

Выполняются только оставшиеся этапы. Перед каждым — deterministic command materializes полный пакет обязательных pinned guides и компактный upstream index с source IDs/classifications/URLs/manifest hashes. Идентичные guide файлы читаются один раз, исходные полные records доступны по необходимости перед дальнейшими claims. Пакет не является LLM summary и не повышает confidence. Само новое продолжение и его prompts фиксируются отдельным workflow digest; исходный product context/prefix не переписываются. Prefix artifacts защищены pinned import map; indexes расширяются с сохранением истории.

Codex stages используют `transport: app-server` с промежуточными cumulative usage receipts. Укажите reviewed carry entries для старых known/reserved unknown расходов; денежный max включает перенос. Token cap можно изменить только по явному review, не при retry. Carry reserve — scheduling allocation, не authoritative старый invoice/usage reconciliation. `complete=false` остаётся видимым для actual aggregate с historical unknown, даже если все новые attempts complete. Caps остановят дальнейшие model launches, но один выполняющийся response может перейти threshold.

Для новых Codex pipelines промежуточный канал выбирается явно `product-create --transport app-server`; старые snapshots сохраняют прежний terminal-only transport. `product-continue` включает App Server для remaining stages, требует reviewed nonempty carry и явный original monetary ceiling через --budget-ceiling. Сохраняйте исходный source skill snapshot: продолжение не пересчитывает context/define по новой версии библиотеки.
