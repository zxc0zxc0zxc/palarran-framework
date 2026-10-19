---
id: backend/2026-10-19-model-budgets/0002
status: accepted
date: 2026-10-19
scope: managed-worker-context
decision_basis: agent-judgment
reuses: [backend/2026-10-19-model-budgets/0001]
supersedes: []
superseded_by: []
---

# Scope управляемого worker

## Контекст и основание
Внешний runtime считает CLI launches; агент может сам делегировать или запустить новый CLI и обойти смысл allocation. Provider internally делает несколько requests, их runtime не ограничивает.

## Выбор и объяснение
В managed prompt явно передавать роль и запрет nested model/agent invocations, смены модели и расширения scope. Неподходящая сложность → needs_input. Coordinator раскладывает работу в отдельные заранее budgeted tasks; worker использует обычные разрешённые tools. Это instruction contract trusted worker, не security sandbox.

## Альтернативы
Неограниченная nested delegation делает бюджет непрозрачным. Полная OS/provider isolation сейчас отдельный scope, запрет tools нарушил бы existing execution contract.

## Источники и evidence
User budget request, existing no-bypass/trusted-process boundary; [Claude model configuration](https://code.claude.com/docs/en/model-config), проверено 2026-10-19: profiles/effort/fallback зависят от client/provider. Runtime фиксирует requested model, не attest фактический backend.

## Последствия и пересмотр
No automatic fallback в нашем scheduler не запрещает inherited provider-side routing; доверенные CLI config должны быть проверены оператором. Новые nested tasks требуют нового allocation. Пересмотр при gateway/provider telemetry enforcement.

## Применение и проверка
Managed prompts проверяются реальными fake subprocess fixtures, prompt byte cap после всех appended instructions. Provider quality/cost и соблюдение всех model instructions не доказаны offline tests.
