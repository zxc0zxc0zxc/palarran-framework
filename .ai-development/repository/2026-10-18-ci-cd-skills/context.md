# Контекст: CI/CD skills и память решений

- Target: корень `ai-tools`, исходный commit `fe5355d`.
- Запрос: создать `/ci-cd:github`, `/ci-cd:gitlab`; каждое принятое решение всех скиллов хранить с объяснением и использовать в следующих задачах.
- Основа: существующие 16 документов `docs/ci-cd/`, три infra skill и namespace `infra-plan`.
- Ограничения: для CI/CD нет SSH; no secrets in logs; пять стеков; fast CI с обязательными tests; optional environment selection; не активировать application production pipeline без конкретного target/config.
- Решения этой задачи: `0001` (memory), `0002` (skills), `0003` (packaging), `0004` (validation). До этой задачи `.ai-development/` не существовал; предыдущие сообщения не выдаём за исторические ADR с принятой тогда датой.
- Существующие документы — факты repository; доступность provider features при будущей интеграции сверяется отдельно. Это authoring skill, не фактическое применение к application repository.
- Открытый вопрос для следующей задачи: первое реальное применение к проекту с выбранным provider/стеком/environment contract; его timings и live security gates пока неизвестны.
