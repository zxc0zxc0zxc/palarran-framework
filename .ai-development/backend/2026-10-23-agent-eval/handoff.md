# Handoff agent-eval-v001

Решение: backend/2026-10-23-agent-eval/0001. Сначала primary sources/docs/protocol/ADR, затем реализация. Существующие незакоммиченные изменения сохранены; commits/push/deploy отсутствуют.

## Реализовано

- docs/agent/eval/: dated Anthropic eval/noise + SWE-bench sources, методика, контракт, операции и пределы вывода.
- /agent:eval с --plan, mandatory docs, памятью решений, target/skill separation; namespace agent, discovery link, Claude adapter и portable package.
- orchestrator.agent_eval: strict suite admission, frozen private rubric/pinned graders, compilation в existing serial fail-fast runtime, explicit model launch gate, no automatic retries/model escalation.
- Independent JSON/behavior checks, stable final rechecks; stale source/frozen grader/bundle отклоняются. Report заново сверяет JSON artifact receipts, в том числе Git-ignored answers, не исполняя команды.
- Per-case quality, denominator/skips, requested profiles/context, exact subject/harness/bundle/workflow hashes, token/cache/cost ledger, execution/grader/elapsed seconds и guarded descriptive comparison.
- Quality verdict отделён от financial completeness: historical unknown не стирает доказанную quality, но не даёт complete cost/savings. Existing carry/unknown/failure charges сохраняются.

## Проверки

- PASS: 15 focused final-version offline tests (12.318s): good/bad answer, actual code behavior/edges, grader/bundle drift, final regression, ignored-answer drift, launch gate, fake complete/unknown receipts, budget stop/restart, inherited unknown reserves, strict admission и CLI.
- PASS: 4 portable packaging tests (0.453s), 26 registered skills/adapters, 396 Markdown files, local links, py_compile, git diff --check.
- PASS: factory acceptance, 100 control-plane samples, p95 0.877ms при lab threshold 100ms, smoke 0.510s. Это local synthetic evidence, не operational SLA.
- PASS: 298 full offline tests (228.218s). Отдельные 15 focused tests покрывают final-version changes, включая запрет state symlink и freshness ignored JSON answers. Прежний прерванный прогон не считается evidence.
- Standalone skill-creator quick_validate: BLOCKED из-за отсутствия PyYAML в system/Graphify Python; helper запускался, import завершился ошибкой. Dependencies не устанавливались. Repository skill/namespace/link/package validators PASS.

## Пример и ограничения

[Пример отчёта](example-report.json): четыре synthetic fixtures plan/review/context/build, 4/4 independent checks; это harness smoke, не измерение модели. Temporary test repos/state disposable; raw logs/answers/private bundles в Git не сохранены. В report только safe metrics/hashes, invoice=null и model token/cost=null для command fixtures.

Model/API/Modal/GPU/paid judges NOT_RUN; платных вызовов и увеличения прежнего бюджета нет. Реальное качество моделей, статистическая значимость и финансовый invoice не заявляются. v1 trusted local executor не hostile sandbox, fail-fast оставляет downstream NOT_RUN. Нет автоматических multi-run trials: новые запуски требуют явного переноса прежнего расхода/reserves в общий budget/carry. Изменение grader/harness — новая revision с calibration/review. Auto routing/few-shot publication/outreach/deploy вне scope.
