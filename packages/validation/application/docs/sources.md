# Primary sources

Inspected 2026-10-24. Author experiments/vendor docs are separate from our measurements/project choices.

| ID | Source / publication basis | Use / limitation |
| --- | --- | --- |
| E-APP-001 | Anthropic [Harness design](https://www.anthropic.com/research/harness-design-long-running-apps), 2026-03-24 | Separate evaluator, calibrated criteria, actual Playwright UI/API/DB checks; several long author runs, not universal quality/cost gain |
| E-APP-002 | OpenAI [Improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop), 2026-05-12 | Traces/feedback → reusable evals/reviewable changes; tutorial, no paid-model-grader requirement |
| E-APP-003 | Playwright [Assertions](https://playwright.dev/docs/test-assertions), live / publication unknown | Web-first retried assertions; installed version/environment pin independently |
| E-APP-004 | Playwright [API testing](https://playwright.dev/docs/api-testing), live / publication unknown | Server-side postconditions after UI actions; HTTP200 alone is not business correctness |
| E-APP-005 | Playwright [Browser contexts](https://playwright.dev/docs/browser-contexts), live / publication unknown | Isolated browser state; not OS sandbox/DB cleanup |
| E-APP-006 | Playwright [Trace viewer](https://playwright.dev/docs/trace-viewer), live / publication unknown | Debug artifacts; traces may contain sensitive data, no default public upload |
| E-APP-007 | SQLite [URI filenames](https://www.sqlite.org/uri.html), URI support since 3.7.7 / 2011-06-23 | mode=ro connection; not app-write isolation, cross-surface-read atomicity or proof of the correct DB |

Our one-attempt/fresh-ID/byte-cap/frozen-receipt protocol comprises bounded engineering choices. Never transfer author-example timing/prices to our run. A full security boundary needs separately isolated environments; trusted suite/source/version endpoint are assumptions here.
