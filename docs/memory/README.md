# Межпроектная инженерная память

Бесплатный self-hosted graph+fulltext без внешних LLM API: Neo4j Community, небольшой Python service, MCP stdio gateway через SSH-туннель. Это отдельный слой над project-local ADR и Graphify. Память возвращает опыт с условиями применимости, а не инструкции или разрешения.

Обязательно читать [sources](sources.md), [architecture](architecture.md), [contract](contract.md), [operations](operations.md), [workflow](workflow.md) и [память решений](../skills/decision-memory.md). Skill checkout и target roots различаются.

Первый профиль — один доверенный владелец и несколько его проектов/агентов. Не multi-tenant SaaS, нет HA и скрытых paid jobs. Семантического поиска/автоматической классификации нет. Native fulltext ищет слова; агент может уточнить запрос синонимами/переводом в своём текущем бюджете.

| Слой | Источник правды |
| --- | --- |
| Локальный код/ADR | Текущий проект, commit и оригинальные файлы |
| Graphify | Optional fresh code-only navigation текущего проекта |
| Общая память | Отобранные карточки, provenance, связи и feedback |
| Артефакты | Проверенные обезличенные тексты по SHA-256 вне Git |

Интерфейсы и ограничения runtime описаны в contract; deployment templates инертны до review. Установка skill не регистрирует MCP глобально и не открывает VPS.

R&D findings — полноценная часть общей памяти: [research profile](../skills/research-memory.md). При отборе уроков приоритет у применимых результатов/отрицательных findings с условиями и evidence; кодовые patches сохраняются при пользе, массового импорта нет.

Все скиллы используют [автоматический цикл](../skills/global-memory.md): bounded recall до работы и verified sanitized learn после проверок. Автопубликация — только при явной owner policy; отсутствие сервиса не блокирует основную задачу.
