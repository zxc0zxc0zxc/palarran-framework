# Frontend build handoff

Созданы documentation-first `docs/frontend/` (8 guides), 3 templates, `frontend-build` skill, `/frontend:build` adapter и frontend manifest. Source UX/UI revisions → app routes/components/states → browser evidence. Existing stack/reuse, short copy, responsive layouts, required image generation/reuse, honest mock vs real API checks и durable context обязательны. Решения: 0001–0003.

## Проверки

- PASS: `python3 scripts/validate_repo.py` — 110 MD, 8 skills/adapters, 5 namespaces, links/catalog/decision-memory contracts.
- PASS: `python3 -m unittest discover -s tests -v` — 11 tests, включая изолированную упаковку всех пяти namespaces. Frontend содержит 3 skills и замыкание UI/UX docs/templates, без project memory/secrets/external symlinks.
- PASS: skill-creator quick_validate (temporary PyYAML environment).
- PASS: `python3 scripts/package_plugin.py frontend --output artifacts/plugins/frontend` и `claude plugin validate artifacts/plugins/frontend --strict`.
- PASS: Python compilation и `git diff --check`.
- CI: pending publication.
- NOT RUN: browser acceptance конкретного приложения, real backend integration, rendering/image generation — application target не задан, здесь authoring capability. Offline tests не доказывают корректность будущей frontend реализации.

## Использование и следующий контекст

Codex `$frontend-build`, Claude отдельный namespace `/frontend:build`. Package содержит frontend/UI/UX skills как dependency closure; upstream slash namespaces подключаются отдельно. При пересборке выбрать новый output, старый не перезаписывается. Root infra plugin сохранён.

При запуске на target читать его UX/UI/frontend indexes и accepted rationale, выбрать обе source revisions, реализовать requested scope в штатном app code и обязательно открыть actual app в браузере. Проверить interactions/states/visual fidelity/responsive layouts, исправить свои defects и записать actual evidence. Mandatory missing browser/API/source/assets означают partial/unverified, не verified. Results/decisions пишутся в target `.ai-development/frontend/`; старый PASS перепроверяется в новой задаче.
