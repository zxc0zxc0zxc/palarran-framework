---
name: agent-eval
description: Спланировать или выполнить полигон агентных задач с независимой проверкой результата, учётом токенов, стоимости и времени. Использовать для /agent:eval; --plan без исполнения, тесты harness без платных вызовов.
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# /agent:eval {задача или suite} [--plan]

Сначала прочитай обязательные [README](../../docs/agent/eval/README.md), [sources](../../docs/agent/eval/sources.md), [methodology](../../docs/agent/eval/methodology.md), [contract](../../docs/agent/eval/contract.md), [operations](../../docs/agent/eval/operations.md), затем [decision-memory](../../docs/skills/decision-memory.md). Разреши symlink skill, отдели installed checkout от target. Прочитай target README/AGENTS, INDEX и relevant accepted ADR, прежние failures и реальные условия задачи. Нет mandatory docs — найди полный checkout, не подменяй общей памятью.

## Protocol до запуска

Определи цель измерения: модель, skill revision либо контекст; выбери реальные task classes и наблюдаемые критерии. До попыток зафиксируй cases/prompts/input hashes/graders/environment/time caps/model settings и бюджет с историческим carry. Сообщи точные пути/формат требуемых ответов в prompt. Создай rubric, good/bad calibration fixtures; planning JSON не доказывает семантическую полноту плана. Code tasks проверяй независимыми behavior/edge/regression tests. Не оценивай агента его собственным PASS. Holdout отделён от development/few-shot.

--plan: только protocol/rubric/ADR/handoff, никаких application edits/install/worktrees/model/tests/cloud. Без --plan запускай только конкретно разрешённую trusted suite. Неизвестный денежный budget не даёт права на model call; tests самого полигона всегда command/fake fixtures. AI требует явных ai_policy/usage_policy и существующего разрешения; --allow-model-calls лишь технический gate. Не повышай ceiling, не replay unknown, не делай paid judges/escalation/retries автоматически. Нет runtime в portable package — подготовь suite/инструкции и отметь execution NOT_RUN, не устанавливай инструменты молча.

## Выполнение и review

Из полного checkout используй `python3 -m orchestrator.agent_eval create/work/report/compare` по operations guide. Graders храни вне candidate worktree, явно pin все external test resources. Existing runtime ведёт usage/fencing/final gates. Worktree/process allowlist не sandbox; для hostile agent нужен отдельно согласованный isolated executor. Missing/stale graph означает scoped source fallback, затем оригинальные файлы/AGENTS/ADR.

Сохраняй все outcomes, skipped denominator, requested model/effort, cache/context и все attempts/cost sources. PASS требует независимого final recheck exact subject; unknown/timeouts/drift = INCONCLUSIVE. Fixture pass — проверка harness, не качества модели. Один trial не статистическая гарантия. В model comparison сравнивай одинаковые protocol/baseline/environment и явно перечисляй treatment/confounds. Report различает observed lower bound, complete token receipts, estimate/provider_reported и invoice=null. Missing cost/time — null/NOT_RUN, не ноль.

## Память и результат

Прежде зависимых действий сохраняй основания выбора, альтернативы, применимость sources, protocol/revision и ограничения в target `.ai-development/agent-eval/<task>/decisions/`; обновляй INDEX и handoff по shared memory contract. Используй [protocol template](../../templates/agent-eval/protocol.md). Private state/bundle, secrets, raw logs/prompts/PII и скрытые reasoning traces не коммить. В target сохраняй только reviewable rationale, safe report и private run reference. Следующая задача читает эти решения и повторно проверяет предпосылки.

В конце: verdict, PASS/FAIL/INCONCLUSIVE/NOT_RUN по cases, расходы/время/unknowns, ограничения сравнения, remaining gates и ссылки на protocol/report/решения. Не публикуй benchmark и не меняй model routing автоматически.
