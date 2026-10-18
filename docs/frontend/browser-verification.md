# Browser acceptance: обязательная проверка результата

Успешная компиляция не завершает `/frontend:build`. Запустить приложение штатной командой, определить **фактический** URL/port, открыть его доступным browser tool и пройти [coverage matrix](../../templates/frontend/coverage.md). Не проверять вместо приложения старый UI preview или другой процесс на занятом порту. Сохранять ownership dev process; не останавливать чужой сервер.

Использовать доступный purpose-built browser/UI tool; при необходимости локальный Playwright по conventions target. Если инструмент даёт ограничения доступа, соблюдать их. При отсутствии browser/runtime доступа закончить доступный код и отметить acceptance NOT RUN с конкретным blocker, не подменять проверку HTTP 200. Browser acceptance обязательна для статуса **verified**.

## Что пройти

1. Routes/deep links/reload/back и роль из source UX; проверить, что реально грузятся новые компоненты/assets, нет crash/hydration errors.
2. Основные действия через настоящие controls: menu/navigation, form inputs/validation/submit, dialogs close/focus return, retry/pagination — где они есть. Проверить observable outcome. Доступность disabled/loading не должна маскировать неработающее действие.
3. Loading/empty/error/forbidden/long content воспроизвести детерминированными test fixtures или mock layer, явно пометив источник. При доступном API отдельно проверить реальный request/response и ожидаемое server-side состояние; reload/read-back, если действие должно сохраняться. Не утверждать end-to-end persistence по mock success.
4. Narrow/mobile/tablet/desktop и boundaries из [responsive](responsive.md); проверить keyboard/focus/zoom, scroll, touch targets и source UI fallbacks в поддерживаемых условиях.
5. Снять **и посмотреть** реальные renders; сопоставить с исходным UI при одинаковых размерах/данных: hierarchy/type/spacing/color/assets/states. Записать substantive differences и причину. Наличие PNG не означает просмотр, DOM snapshot не является screenshot.
6. Console, failed network/asset requests и server errors: устранить вызванные изменением дефекты, отличить existing issues с evidence. Фильтрация не должна скрывать crash. Auth/PII не сохранять в report/trace.

После исправления повторить затронутые сценарии и shared component consumers, затем критический smoke flow. Не прекращать после первой сломанной кнопки; исправлять в scope до прохождения. Внешний недоступный backend/tool — конкретная граница проверки, не повод объявить полный success.

## Автоматизация и visual regression

[Playwright best practices](https://playwright.dev/docs/best-practices): проверять наблюдаемое пользователем поведение, изолировать tests, применять устойчивые locators и web-first assertions. Не добавлять произвольные sleeps вместо ожидания состояния. Не привязывать test к CSS nesting, если доступен role/label locator. Использовать штатный framework проекта, не требовать установки нового browser runner при уже доступном подходящем tool.

[Visual comparisons](https://playwright.dev/docs/test-snapshots) чувствительны к environment/fonts/browser. Зафиксировать окружение и deterministic data; сравнивать эквивалентные screens/states. Первый автоматически созданный snapshot ещё не approved baseline. Не принимать массовый `update-snapshots` или расширенный diff threshold как исправление регрессии: сначала посмотреть diff и связать осознанную смену UI с decision/source revision.

Cross-browser scope брать из product requirements/существующей поддержки. При отсутствии списка проверить доступный browser и указать его, не писать «все браузеры». Для поддерживаемых critical engines выполнить доступные проверки или честно перечислить непроверенные. Emulation не доказывает реальную camera/native controls/keyboard интеграцию.

## Evidence

В [browser review](../../templates/frontend/browser-review.md): commit/dirty diff identity, command и environment, browser/version, viewport/role/fixture mode, UX/UI IDs, выполненные шаги и **фактический** результат, screenshot/trace paths, PASS/FAIL/NOT RUN, bugs/recheck. Сохранить sanitized screenshots; traces/HAR могут содержать secrets — не публиковать raw recordings. Обязательные gaps означают partial/unverified, не verified. User acceptance/production deployment отдельно.

## SDD integrated gates и статус задач

Каждый случай связан с plan ID/revision, source UX/UI и TASK/T/AC/screen/state IDs; evidence указывает actual integration commit. Lane screenshots/tests возвращаются в agent reports и не подменяют required browser checks общего приложения. При shared component/router/style change перепроверить затронутые consumers/flows и инвалидировать stale evidence.

Coordinator обновляет [ledger и section source plan](progress.md) после actual проверки: code-ready не verified. Required browser/responsive/visual/flow/DoD gates остаются NOT_RUN/FAIL при недоступном tool/источнике/API или дефекте. Не делить одну управляемую browser surface между одновременно кликающими агентами; isolated contexts/test data/ports либо serial final review.
