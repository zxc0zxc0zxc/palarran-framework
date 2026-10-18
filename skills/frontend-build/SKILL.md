---
name: frontend-build
description: Реализовать интерфейс в проекте по нашим UX/UI-концептам с обязательной адаптивностью, проверкой в браузере и сохранением причин решений. Использовать для /frontend:build и переноса согласованных экранов/состояний в код приложения.
---

# Frontend build

Вызов `/frontend:build {scope/пути к UX/UI}` или `$frontend-build`. Работай в target application, сохраняя existing stack и source concepts; создание самого скилла не означает frontend реализацию ai-tools.

## Источники и память

Определи installed checkout по реальному `SKILL.md` с разрешением symlink (`../../`), отдельно target root. Прочитай [общую память](../../docs/skills/decision-memory.md), target общий/UX/UI/frontend indexes и связанные accepted ADR/handoffs. Каждый принятый implementation choice объясни **до** зависимого изменения: основание, альтернативы, evidence, последствия; обновляй canonical decisions/index/handoff, reuses/supersedes, сохраняй историю для следующих задач. Старое полномочие не разрешает новый scope.

Обязательная база:

- [Контракт](../../docs/frontend/README.md), [source UX/UI mapping](../../docs/frontend/source-contract.md).
- [Реализация/data/assets](../../docs/frontend/implementation.md), [адаптивность](../../docs/frontend/responsive.md).
- [Browser acceptance](../../docs/frontend/browser-verification.md), [quality/performance](../../docs/frontend/quality.md).
- [Workflow/контекст](../../docs/frontend/workflow.md), [источники](../../docs/frontend/sources.md).
- [Coverage](../../templates/frontend/coverage.md), [browser review](../../templates/frontend/browser-review.md), [handoff](../../templates/frontend/handoff.md).

База UX/UI: [UX contract](../../docs/ux/README.md), [UI contract](../../docs/ui/README.md); source concepts/screens/tokens/assets читай по target mapping, не заменяй общими знаниями. Если обязательных файлов skill базы нет, запроси checkout; source refs/API docs проверяй по версии target.

## Реализация

1. Прочитай target repo instructions, текущие изменения, product docs, package/lockfile/scripts, components/routes/tests/API clients. Зафиксируй source **UX и UI revisions**, статусы, scope и все in-scope screens/states/blocks в coverage. Если source отсутствует/конфликтует — уточни путь/версию или предложи соответствующий UX/UI этап; независимую работу продолжай, недостающий дизайн не выдумывай. Явный запрос реализовать draft уважай, не требуй нового approval рутинных решений.
2. Сохрани stack/package manager и переиспользуй tokens/assets/components/data contracts. Не начинай повторный выбор из десяти design codes и не мигрируй framework ради привычки. Объясни implementation decisions; proposed UX/UI deltas отдели от accepted choices, не меняй молча роли/flow/copy/style. Покрой весь запрошенный scope, не только landing/happy path.
3. Реализуй реальные app routes/components/states/actions: responsive layouts, semantic controls, short copy, focus/keyboard, loading/empty/error/validation/success по source. Интегрируй существующие APIs в scope; не имитируй успех неработающего backend. Missing API — изолированные явно отмеченные fixtures/adapter и integration NOT RUN, не ложный end-to-end. Secrets не в client bundle/logs/evidence; untrusted HTML не вставлять небезопасным sink.
4. Готовые UI images переиспользуй. Если дизайну нужна отсутствующая картинка — **сгенерируй** доступным image tool, прочитав обязательный host image skill, и включи в app. Сохрани asset provenance/prompt без private data/tool/date/выбор/alt/crops; реальные screenshots/товарные фото/логотипы не подделывай. Нет tool/required asset — partial/gap. CSS/SVG primitives не превращать в растр.
5. **Адаптивность обязательна**: narrow/mobile/tablet/desktop, boundaries/intermediate widths, long content/zoom/overflow и все source states. Не скрывай необходимые actions. Glass/unsupported effects/reduced-motion fallbacks, semantic labels/visible focus и применимые contrast/targets проверь по базе. Device emulation не выдавай за физическое устройство.

## Проверка и завершение

Запусти применимые target lint/typecheck/build/tests; добавь targeted regression checks, где они нужны. Затем **обязательно открой фактическое работающее приложение в браузере** доступным tool, проверь actual URL/версию, routes/deep links/back/reload, actions/state transitions, narrow/tablet/desktop, keyboard/focus, console/network/assets. Сними **и посмотри** реальные renders, сравни с source UI при эквивалентных данных/размерах. Build/HTTP 200/DOM snapshot/непросмотренный PNG не заменяют browser acceptance.

Проверь data outcome реальным API/read-back, если это входит в scope и доступно; mocked tests пометь отдельно. Live payments/email/account mutations требуют соответствующего явного scope/sandbox, сам build их не разрешает. Исправь вызванные изменением defects и повтори затронутые проверки; snapshots не обновляй ради скрытия регрессии. Нужные host-specific навыки применяй при реальном срабатывании условий (например, Figma implementation); не навязывай новый browser runner при уже доступном tool.

Запиши command/environment/commit/browser/viewport, UX/UI case IDs, actual outcome и safe screenshot paths со статусами PASS/FAIL/NOT RUN. Нет browser/runtime/source/API для обязательной проверки — **partial/unverified** с конкретным blocker и сохранённой независимой частью, не объявляй verified. Не утверждай all-browser support, user testing, WCAG certification или deploy без evidence.

Код/tests/assets сохраняй в штатных app directories; canonical rationale, coverage, browser review/evidence и handoff — в **target `.ai-development/frontend/<task>/`** плюс общий/frontend indexes. Свяжи реализацию с source catalogs без перезаписи concepts. В конце дай рабочий URL/команды, ссылки на изменения/решения/проверки и оставшиеся gaps. Следующая задача читает этот контекст и сверяет source revisions до новых изменений.
