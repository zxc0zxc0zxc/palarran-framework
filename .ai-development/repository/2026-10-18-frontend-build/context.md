# Контекст: /frontend:build

- Target: ai-tools, baseline `d97060e`.
- Запрос: сначала документация, затем скилл реализации frontend по нашим UX/UI concepts; responsive обязательно, решения сохранять, результат проверять в браузере.
- Reuses: repository/2026-10-18-ci-cd-skills/0001,/0003,/0004; repository/2026-10-18-ui-design/0002,/0005.
- Здесь создаётся capability, не frontend приложения ai-tools. Нет отдельного application target, поэтому browser acceptance конкретного приложения не заявляется выполненным.
- Проверены первичные sources: React, Next.js, Google web.dev, Microsoft Playwright, W3C и OWASP. Предпочитаем existing stack и version-specific documentation, не навязываем React/Next всем проектам.
