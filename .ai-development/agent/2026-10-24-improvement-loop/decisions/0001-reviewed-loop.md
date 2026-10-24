---
id: agent/2026-10-24-improvement-loop/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Evidence-driven skill improvement

## Контекст и основание

Есть frozen agent eval, но его сравнение запрещает менять prompt. Для изменения skill нужен отдельный controlled treatment: одинаковые задачи/graders/модели/контекст/лимиты, различаются только frozen skill bytes. Failure report не доказанная причина, а fixture не качество модели.

## Выбор и объяснение

Новый /agent:improve и orchestrator.agent_improve prepare/compare. Prepare читает approved sanitized incident/feedback, snapshot baseline/candidate skill, frozen regression+existing control cases, генерирует single-case agent-eval suites и reviewable diff вне target. Не исполняет target/models/worktrees и не применяет patch. Compare читает actual bound agent_eval state/run через existing verifier; проверяет exact generated suite, distinct runs, matching environment/harness/baseline и конечные case outcomes. Single-case runs сохраняют известный FAIL baseline, не теряя все controls из-за fail-fast eval. Различие только skill placeholder; прочие изменения делают comparison ineligible. Все случаи остаются в знаменателе.

Cost/time из existing ledger. Unknown/null не ноль; fixture costs/tokens не model efficiency. Суммировать attempts без двойного учёта carry, сверять общий envelope, не выделять budget и не dispatch автоматически. Допускается только перенос cumulative carry при неизменных остальных caps/rates; unknown/restarts не обнулять. Prepare/compare не model runner: execution и общий carry контролирует existing agent-eval lifecycle/координатор. Paid execution не разрешён этой задачей.

## Альтернативы

Ослабить agent_eval.compare для произвольных изменённых prompts разрушило бы comparability. Regex наличия нужных слов в SKILL.md не проверяет поведение. Автоматически применять feedback/trace instructions или merge/deploy расширило бы полномочия. LLM judge/HALO/Promptfoo — optional отдельные интеграции, не обязательные зависимости.

## Источники и evidence

OpenAI improvement loop 2026-05-12 и repair loop 2026-05-11: traces/feedback→evals→focused changes→revalidation; официальные tutorials, не наш benchmark. Anthropic evals 2026-01-09: outcome, calibrated graders, regression/capability sets. Применимость/границы в docs/agent/improve/sources.md. Никаких hidden chain-of-thought: approved observable events/outputs и concise decision explanations.

## Последствия и пересмотр

Skill 29, agent namespace получает improve рядом с eval, количество namespaces 11. Portable agent package содержит guides/templates; runtime полного checkout отдельно. Нет auto optimizer/paid trials/нового ledger. Первый ML pilot создаёт sanitized regression fixture и diff к уже существующему goal/data contract; исторический training и model behavior NOT_RUN. Candidate publication только по пользовательскому scope, не по факту зелёного fixture.

## Применение и проверка

Offline real local agent-eval runs, bad/good/edge ML plan grader calibration, preserved controls, tamper/protocol drift/missing/unknown/budget/carry tests. Full validator/unit/factory checks. Publication сохраняет чужие ML/SFT dirty изменения.
