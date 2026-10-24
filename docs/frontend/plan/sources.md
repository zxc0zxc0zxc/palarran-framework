# Frontend planning sources

Checked **2026-10-18**. Workflow/DoD/task IDs are our adaptation of user requirements and existing frontend methodology, not source owners' exact processes.

| Source | Use | Boundary |
|---|---|---|
| [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) | HTTP operation/schema contract reference | Specific version, not a latest claim; preserve existing API dialect/format |
| [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | Standard problem details as a possible error format | Only when selected/supported by backend; no automatic API migration |
| [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) | Web operation cancellation | Client abort does not determine server mutation outcome |
| [W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | Responsive acceptance and exceptions | Planning/checks are partial, not full-conformance proof |
| [Existing frontend sources](../sources.md) | React/Next for applicable stacks, Playwright tests/isolation, Google responsive/performance, OWASP | Apply to target versions without imposing a framework/runner |

Internal sources: [UX contract](../../ux/README.md), [UI contract](../../ui/README.md), [SDD](../sdd-agents.md), [execution progress](../../skills/execution-progress.md), [decision memory](../../skills/decision-memory.md). Target source artifacts/revisions take precedence over generic examples. Code/snippets must be small inert original sketches or have verified permalink/license/attribution; do not invent company production code.
