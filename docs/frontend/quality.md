# Quality без фиктивных гарантий

Проверить существующие scripts и выполнить применимые lint/typecheck/build/unit/component/browser checks. Добавлять целевые tests для новых состояний/взаимодействий, где они ловят реальную регрессию; не писать snapshots/тесты, лишь повторяющие структуру реализации. Исправлять вызванные изменением failures. Existing failures описывать с baseline evidence, не объявлять новый код виноватым или всё зелёным без фактов.

Выделить быстрый feedback: component/state checks и targeted browser smoke до полного suite, reuse deterministic fixtures, изолировать tests, сохранять failure evidence. Полный обязательный suite проекта остаётся обязательным. Не отключать проверки ради скорости. Изменение CI — только если нужно запросу/согласованному scope, ориентир `docs/ci-cd/` (отдельная CI/CD база) доступна отдельно, не обязательная зависимость frontend package.

## Performance

Учитывать размеры assets и client JavaScript, изображения с явной геометрией, font loading/fallback, lazy loading неключевого content, ненужные re-renders и data waterfalls. Не превращать всю страницу в client component без причины в проектах с server rendering. Измерять на воспроизводимом маршруте/данных/device profile; budget выбирать по продукту и baseline, не придумывать универсальный bundle limit.

[Google Web Vitals](https://web.dev/articles/vitals) выделяет LCP, INP и CLS как Core Web Vitals. Lab замер помогает диагностировать, но не доказывает field показатели реальных пользователей. Записывать method/environment, до/после и ограничения; score Lighthouse не означает корректность UX, отсутствие XSS или WCAG certification. Если performance замер недоступен/вне scope, так и указать, не выдумывать проценты улучшения.

## Границы готовности

- Implemented: код и in-scope coverage существуют, integration gaps явно названы.
- Verified: применимые project checks и обязательный browser acceptance пройдены для зафиксированного scope/environment; mandatory missing asset/API/browser checks не скрыты.
- Partial/unverified: есть FAIL/NOT RUN обязательных checks или отсутствует нужный backend/tool/source; описать конкретный остаток, сохранить независимую выполненную часть.
- User-approved/deployed: только фактическое отдельное решение/событие, не следствие `build`.

В handoff отделить syntax/build, actual UI interactions, visual review и real API integration. Запуск dev server сам по себе не evidence результата в браузере.
