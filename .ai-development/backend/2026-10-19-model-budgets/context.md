# Контекст

Запрос: заранее выбирать модели по сложности и ограничивать расход каждого прогона. Target ai-tools, baseline 9e514d4. Повторно используем factory ADR 0003/0005 и pipeline 0006: durable attempts, no raw output, независимые gates. Модельный запуск не равен одному API request; подписочные лимиты opaque. Без live provider calls.
