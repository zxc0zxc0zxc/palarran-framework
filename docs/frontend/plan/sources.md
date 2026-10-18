# Источники frontend planning

Проверено **2026-10-18**. Workflow/DoD/task IDs — наша адаптация пользовательских требований и existing frontend methodology, не exact process владельцев sources.

| Источник | Использование | Граница |
|---|---|---|
| [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) | HTTP operation/schema contract reference | Конкретная версия, не latest claim; existing API dialect/format сохранить |
| [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | Standard problem details как возможный error format | Только если выбран/поддержан backend, не автоматическая API migration |
| [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) | Web operation cancellation | Server mutation outcome не следует из client abort |
| [W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | Responsive acceptance и исключения | Planning/checks частичны, не full conformance proof |
| [Existing frontend sources](../sources.md) | React/Next при соответствующем stack, Playwright tests/isolation, Google responsive/performance, OWASP | Применять к target versions; не навязывать framework/runner |

Internal sources: [UX contract](../../ux/README.md), [UI contract](../../ui/README.md), [SDD](../sdd-agents.md), [execution progress](../../skills/execution-progress.md), [decision memory](../../skills/decision-memory.md). Target source artifacts/revisions важнее generic examples. Код/snippets только небольшие inert own sketches либо с verified permalink/license/attribution, не выдуманный company production code.
