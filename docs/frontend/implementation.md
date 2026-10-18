# Реализация и интеграции

## Existing stack прежде нового шаблона

Проверить target instructions, Git diff, package manifests/lockfile, runtime versions, scripts, routing, CSS/tokens, UI library и data clients. Сохранять чужие незавершённые изменения. Использовать существующий package manager и version-compatible API. Новый project foundation выбирается по constraints при отсутствии основы, с причиной; не назначать Next/React всем проектам, не обновлять все зависимости попутно.

Разложить UI по смысловым reusable components и source blocks, сохранить semantic tokens и shared states. [React Thinking in React](https://react.dev/learn/thinking-in-react) полезен для React-проектов: component hierarchy и минимально необходимый state. Не дублировать derived values в state без причины. Для [Next Server/Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) учитывать границу server/client; интерактивность локализовать, server secrets не передавать в client props/bundle. Для других frameworks читать их version-specific official docs.

## Data и поведение

Подключать существующие API contracts: loading, empty, validation, forbidden, not-found, timeout/error/retry там, где они предусмотрены. Проверить response shapes, pagination, cancellation/stale requests, pending/double-submit и корректность ошибок по target поведению. Не создавать фиктивные endpoints/success alerts для имитации завершённого действия. Если API нет — изолированный явно обозначенный adapter/fixtures, интеграция **NOT RUN**; backend/migrations не делать без соответствующего scope.

Client-side скрытие кнопки не заменяет server authorization. Credentials остаются в предусмотренном server/env механизме, не в bundle, URL, screenshots или logs. Не печатать auth payload/response с personal data ради debug. [OWASP XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html): не вставлять untrusted HTML через опасные sinks, использовать context-appropriate escaping/sanitization при реальной необходимости rich text. Это targeted security review, не полный аудит.

Реальные payment/email/account mutations не использовать как безобидные smoke tests. Проверять через local/test fixtures или явно разрешённый sandbox; полномочия на build не означают отправку сообщений/платежей. Existing test credentials вводятся безопасным механизмом, не копируются в durable context.

## Assets и fidelity

Перенести source UI tokens и разрешённые assets в app-native структуру, с source mapping; preview CSS не копировать слепо вместе с demo navigation. Проверить font availability/licensing/fallback, icon family, contrast, crops и responsive sizing. CSS/SVG primitives сохранять кодом. Нужные готовые generated assets **переиспользовать**, не генерировать заново при каждом build.

Если UI требует отсутствующее bitmap изображение — **сгенерировать его** доступным image tool, прочитав обязательный host image skill, включить output в приложение. Сохранить prompt без private data, tool/date, выбранный файл/причину, alt/decorative status, responsive crops и fallback по [UI asset policy](../ui/visual-output.md). Не фабриковать product screenshots/реальные товарные фото/логотипы: нужны разрешённые originals либо явно synthetic placeholder. Нет генератора/обязательного asset — gap/partial, а не полная visual acceptance.

Служебные development fixtures/state controls не должны попадать в production routes/bundle неконтролируемо. Файлы app живут в app directories; `.ai-development/frontend/` хранит rationale/mapping/evidence, не второй конкурирующий исходник приложения.
