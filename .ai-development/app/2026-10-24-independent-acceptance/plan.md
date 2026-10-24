# App-verify-v001

- [x] Scope, primary sources, accepted ADR до зависимых изменений.
- [x] Docs: scenario/independence/contract/operations/evidence и templates.
- [x] Skill/adapter/discovery/plugin/index registration.
- [x] Bounded CLI + Playwright bridge + offline fixture/tests.
- [x] Real local browser smoke where available, full checks/acceptance/handoff.

Implemented revision: app-verify-v001 (working tree on a07f007; not committed).

Final focused checks: 17 tests PASS with existing Chrome/Playwright; packaging 4 PASS. Local CLI create/run/report smoke: browser→API→SQLite at 390px and 1280px PASS; both captures viewed. Broad offline suite: 426 tests, 422 PASS / 4 existing optional tensor SKIP. Repo validator and factory acceptance PASS; no paid launches. Details/limits in [handoff](handoff.md).
