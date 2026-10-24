# Primary sources

Checked **2026-10-18**. This methodology contains our implementation/acceptance recommendations; it does not claim source owners use this entire workflow. Recheck concrete runtime/framework APIs against the target project's installed version.

| Source | What we use | Boundary |
|---|---|---|
| [React: Thinking in React](https://react.dev/learn/thinking-in-react) | Component decomposition and minimal state | For React projects, not grounds to migrate another stack |
| [Next.js: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) | Server/client boundary and interactive parts | App Router; check installed version and project routing |
| [Google: Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) | Viewport, fluid layout, content-driven adaptation | Our 320/390/768/1440 probes are not a Google standard |
| [Google: Web Vitals](https://web.dev/articles/vitals) | LCP/INP/CLS and lab/field distinction | A local measurement is not a field guarantee |
| [Microsoft Playwright: Best practices](https://playwright.dev/docs/best-practices) | User-visible behavior, isolation, resilient locators, web-first assertions | The project may use another browser tool; do not impose a runner |
| [Playwright: Visual comparisons](https://playwright.dev/docs/test-snapshots) | Screenshot comparisons and environment dependence | A generated baseline is not automatic UI approval |
| [W3C: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | 320 CSS px and applicable exceptions | Targeted checks do not establish full WCAG conformance |
| [OWASP: XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) | Context-sensitive encoding and dangerous HTML sinks | Not a full application security audit |

Repository contracts: [UX](../../../design/ux/docs/README.md), [UI](../../../design/ui/docs/README.md), [UI responsive/accessibility](../../../design/ui/docs/responsive.md), [image generation](../../../design/ui/docs/visual-output.md), [decision memory](../../../core/agents/docs/decision-memory.md). Check their source links/versions when applying them. For Vue/Svelte/Angular/plain web, use official documentation for the selected target stack; do not pretend React guidance covers their APIs.

## SDD execution update (2026-10-18)

[Git worktree](https://git-scm.com/docs/git-worktree) covers source checkout lifecycle, not runtime/DB/browser isolation. [Playwright parallelism](https://playwright.dev/docs/test-parallel) and [browser contexts](https://playwright.dev/docs/browser-contexts) are primary sources for test workers/context isolation. Our inference for agents: separate worktrees/cwd/resources and final integrated browser checks; contexts do not automatically isolate shared servers/accounts/data. The exact source plan→task→test→DoD/progress protocol is our methodology, not a claim about Microsoft's/GitHub's internal process.
