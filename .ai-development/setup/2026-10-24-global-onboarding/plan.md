# setup-v001

- [x] Read contracts/source docs, explicit authorization ADR and SSH non-agent check.
- [x] Docs, committed public snapshot/project installer and bounded memory doctor.
- [x] Real global Codex registration and login LaunchAgent, recovery check.
- [x] Temporary project Codex/Claude onboarding, usage and scopes tests.
- [x] Validator, offline suite/factory and handoff.
- [x] Scoped commit and new committed-bundle doctor (34 skills, six tools, authenticated search PASS); publication receipt is verified origin/main SHA.

Real stdio/global configuration and login-job recovery verified; host UI discovery remains NOT_RUN until client restart. No paid model runs. Full offline suite: 472 tests, 4 optional skips, PASS (353.895s). Working-tree validator: 568 Markdown/34 skills PASS; isolated staged validator: 522 Markdown/34 skills PASS. Isolated staged installer8/packaging4 PASS. Factory 100 samples, p95 2.489ms, smoke PASS; live providers/operational SLA NOT_RUN. Final independent temporary project installed the committed bundle, preserved its AGENTS and ran doctor using its own copied helper: PASS, zero writes/model calls. Native symlink-parent rejection also observed for macOS temp alias; canonical target path succeeded.
