# Контекст и source-driven SDD

Сначала прочитать target agent instructions, общий/frontend/UX/UI indexes и relevant accepted ADR. Найти конкретные spec/UX/UI revisions, status/scope/screens/states/blocks, tokens/components/assets и связанный API schema. README/product docs дают бизнес-контекст, не заменяют missing UX/UI. Draft source допустим по явному запросу с указанным ограничением; approval не изобретать.

Read-only project inventory: baseline commit/relevant dirty changes, framework/runtime/package/lockfile/scripts, routes/layout/global styles/UI library, API clients/auth/cache/forms/test tools, local delivery/infra constraints. Existing stack/reuse — default, не framework migration ради новой фичи. Нет frontend foundation — спланировать минимальную основу с alternatives: rendering/routing/client-server boundaries, component/token strategy, API integration, local dev/test/CI/resource fit. Ничего не устанавливать. Version-specific official docs проверить при выборе нового механизма.

## Spec

[Шаблон](../../../templates/frontend/spec.md): outcome/actors/roles, scope/non-goals, R/AC IDs, screen/state/block/invariant и C-ID, source UI spec/assets/tokens, affected routes/components/data, TASK/T mapping, constraints/unknowns. По умолчанию охватить всю запрошенную фичу, не только success screen. Planned delivered plan revision связывает **обе UX/UI revisions** и API version; accepted source deltas отдельные ADR, не скрытая правка concepts.

Разделить наш frontend implementation choice (component composition/local state) и business/design/API change (новая роль/обязательный шаг/неподдерживаемый endpoint). Первое решать с rationale, второе — explicit proposal/owner/dependency. Новые фичи без нужных source screens оформить как UX/UI gap с конкретным недостающим flow, не нарисовать «согласованный» UI автоматически.

Схемы по необходимости: route/state transitions, component/data ownership, API request/failure sequence и task DAG. Сохранить source diagrams; Mermaid не visual design или evidence actual browser behavior. Для простой фичи достаточно небольших схем/таблиц вместо архитектуры всего приложения.

Performance/accessibility/SEO/offline/browser/device requirements брать из source/платформы. Если предлагается numerical budget, показать assumptions и будущую процедуру измерения, не придумывать benchmark/SLA. No sensitive data в planning examples/evidence.
