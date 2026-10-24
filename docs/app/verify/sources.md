# Первичные источники

Inspected 2026-10-24. Авторские experiments и vendor docs отделены от наших измерений/проектных решений.

| ID | Источник / publication basis | Что используем / ограничение |
| --- | --- | --- |
| E-APP-001 | Anthropic [Harness design](https://www.anthropic.com/research/harness-design-long-running-apps), 2026-03-24 | Separate evaluator, calibrated criteria, actual Playwright UI/API/DB checks; несколько длительных авторских runs, не универсальный quality/cost gain |
| E-APP-002 | OpenAI [Improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop), 2026-05-12 | Traces/feedback → reusable evals and reviewable changes; tutorial, не требование использовать paid model grader |
| E-APP-003 | Playwright [Assertions](https://playwright.dev/docs/test-assertions), live / publication unknown | Web-first retried assertions; installed version/environment pin independently |
| E-APP-004 | Playwright [API testing](https://playwright.dev/docs/api-testing), live / publication unknown | Server-side postconditions after UI actions; HTTP200 alone не business correctness |
| E-APP-005 | Playwright [Browser contexts](https://playwright.dev/docs/browser-contexts), live / publication unknown | Isolated browser state; не OS sandbox и не DB cleanup |
| E-APP-006 | Playwright [Trace viewer](https://playwright.dev/docs/trace-viewer), live / publication unknown | Debug artifacts; traces may contain sensitive data, no default public upload |
| E-APP-007 | SQLite [URI filenames](https://www.sqlite.org/uri.html), URI support since 3.7.7 / 2011-06-23 | mode=ro connection; не изоляция app writes, atomicity всех cross-surface reads или proof correct database |

Наши one-attempt/fresh IDs/bytes caps/frozen receipt protocol — собственные bounded engineering choices. Не переносить время/цены авторских examples на наш запуск. Полный security boundary требует отдельно изолированной среды; trusted suite/source/version endpoint здесь предпосылки.
