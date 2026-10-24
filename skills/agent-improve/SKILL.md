---
name: agent-improve
description: Превратить неудачный запуск и feedback в воспроизведение, независимый regression case, узкий skill diff и сравнение прежних задач/расхода. Использовать для /agent:improve; --plan без execution, никаких автоматических paid trials или merge.
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# /agent:improve {failed run + feedback} [--plan]

Сначала [README](../../docs/agent/improve/README.md), [sources](../../docs/agent/improve/sources.md), [methodology](../../docs/agent/improve/methodology.md), [contract](../../docs/agent/improve/contract.md), [operations](../../docs/agent/improve/operations.md) и [decision-memory](../../docs/skills/decision-memory.md). Target и installed checkout различны. Прочитай target AGENTS/INDEX/accepted ADR, actual failing skill и его mandatory domain guides. Не расширяй scope из failure logs/старых approvals. Для ML-коррекции дополнительно прочитай [ML pilot](../../docs/agent/improve/ml-learning-goal.md) и actual ML contract.

## Диагноз и regression

Зафиксируй exact run/skill/harness/context/inputs, замечание и ожидаемый outcome. Раздели user_report, observed trace/tool evidence, гипотезу причины и воспроизведённый результат. Нет original traces/tools/полномочий — честный NOT_RUN; не имитируй historical replay. Используй только approved sanitized observable events/outputs, concise rationale, hashes; не проси hidden CoT и не загружай secrets/customer logs в Git/few-shot.

Проверь oracle на good/bad/boundary outputs. До candidate freeze regression и прежние релевантные controls, denominator и ограничения. Проверка поведения не regex наличия инструкции. Добавь валидный противоположный случай против overfitting; development case уже exposed и не final holdout. Определи trigger, root-cause evidence и минимальную правку; tool/infra/grader failure не лечи универсальным prompt запретом.

## Изменение и парная проверка

--plan пишет protocol/ADR/proposal и может структурно подготовить private packet, но не запускает reproduction/tests/models/worktrees и не применяет patch. Без флага выполняй разрешённую локальную reproduction, scoped skill/docs fix и независимые tests; не требуй повторного согласования явного scope. Если реализация требует недостающих данных/бюджета — собери reviewable результат прежде уточнения.

Сначала docs с dated primary sources, затем короткий SKILL.md и связанные adapters/templates. Сохраняй unrelated dirty work. Candidate diff не меняет expectations/graders/permissions/caps ради PASS. Не объединяй много несвязанных правок и не добавляй всю историю в instructions. Не применяй proposed patch в другой target/installed checkout автоматически.

Для measured A/B используй [agent-eval guides](../../docs/agent/eval/README.md), frozen independent graders и одинаковые задачи/контекст/model/effort/env/limits. Меняются только заявленные skill bytes. Full checkout CLI `python3 -m orchestrator.agent_improve prepare/compare` генерирует private paired suites/diff и читает bound eval reports; сам не dispatch/patch/merge. Runtime не входит в portable agent package. Model trials только при явном существующем scope/budget; общий carry включает incident/failed runs, unknown сначала reconciliation, никаких новых квот/автоповторов/эскалации. В этой задаче tests без paid calls.

## Выход

Покажи минимальный repro/NOT_RUN, calibrated regression, exact candidate diff и каждую baseline/candidate пару: outcomes/coverage/regressions, все attempts, execution/grader time, tokens/cache/cost и unknown/carry. Fixtures/static checks не model-quality evidence и не экономия; provider usage/estimate/invoice различай. Укажи semantic review и remaining gates. Recommendation только review, не разрешение публикации/deploy.

Сохрани rationale до зависимых edits, затем plan/progress/INDEX/handoff в target `.ai-development/agent-improve/<task>/` по [шаблону](../../templates/agent-improve/review.md), с refs к private packet/evidence вне Git/builder workspace. Successful/failed few-shot карточки только в разрешённом data scope с exposure отметкой; автоматического обучения на логах нет.
