# Первичные источники

Проверено **2026-10-18**. Методика содержит наши implementation/acceptance рекомендации; они не являются обещанием, что владельцы источников используют весь этот workflow. Конкретный runtime/framework API перепроверять по installed version целевого проекта.

| Источник | Что взято | Граница |
|---|---|---|
| [React: Thinking in React](https://react.dev/learn/thinking-in-react) | Разбиение на компоненты и минимальный state | Для React проектов, не основание миграции чужого stack |
| [Next.js: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) | Server/client boundary и интерактивные части | App Router; проверить installed version и project routing |
| [Google: Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) | Viewport, fluid layout, content-driven adaptation | Наши 320/390/768/1440 probes не стандарт Google |
| [Google: Web Vitals](https://web.dev/articles/vitals) | LCP/INP/CLS и различие lab/field | Локальный замер не field гарантия |
| [Microsoft Playwright: Best practices](https://playwright.dev/docs/best-practices) | User-visible behavior, isolation, resilient locators, web-first assertions | Browser tool проекта может быть другим; не навязывать runner |
| [Playwright: Visual comparisons](https://playwright.dev/docs/test-snapshots) | Screenshot comparisons и зависимость от окружения | Сгенерированный baseline не автоматическое одобрение UI |
| [W3C: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | 320 CSS px и применимые исключения | Targeted checks не полная WCAG conformance |
| [OWASP: XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) | Context-sensitive encoding и dangerous HTML sinks | Не полный security audit приложения |

Контракты этого репозитория: [UX](../ux/README.md), [UI](../ui/README.md), [UI responsive/accessibility](../ui/responsive.md), [image generation](../ui/visual-output.md), [decision memory](../skills/decision-memory.md). Их source links/версии проверяются при применении. Для Vue/Svelte/Angular/plain web использовать official docs выбранного target stack, не притворяться, что React guidance охватывает их APIs.

## SDD execution update (2026-10-18)

[Git worktree](https://git-scm.com/docs/git-worktree) — source checkout lifecycle, не runtime/DB/browser isolation. [Playwright parallelism](https://playwright.dev/docs/test-parallel) и [browser contexts](https://playwright.dev/docs/browser-contexts) — первичные источники для test workers/context isolation. Наш вывод для agents: separate worktrees/cwd/resources и final integrated browser checks; contexts не изолируют автоматически shared server/account/data. Exact source plan→task→test→DoD/progress protocol — наша методика, не утверждение о внутреннем процессе Microsoft/GitHub.
