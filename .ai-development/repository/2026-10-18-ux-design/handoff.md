# Handoff: UX design documentation и /ux:design

## Выполнено и основания

- Созданы 10 guides `docs/ux/`: business/README fallback, research кабинетов/screenshots, сопоставимый анализ, диаграммы, adaptive/accessibility, concise copy, workflow/review и source registry. Основание — [0001](decisions/0001-research.md) и [0002](decisions/0002-screen-contract.md).
- Добавлены templates concept/screen/reference. Каждый in-scope Screen ID требует functional desktop/mobile schemes, tablet/content rules, states/actions/entry/back/recovery, evidence/ADR и короткий UI текст. Visual design/production implementation отдельно.
- Добавлены `skills/ux-design`, project discovery link, `/ux:design` adapter и отдельный `ux` manifest. Default 4 distinct products, minimum 3 с объяснением; screenshots не доказывают скрытые интеракции. Сам authoring не исследует бизнес ai-tools.
- Концепты/revisions/UX catalog сохраняются в target `.ai-development/ux/`; canonical decisions и общий INDEX объясняют выбор для следующих задач. Новые записи этой задачи переиспользуют ранее принятые memory/packaging/validation решения.
- Packager/validator и offline portability test расширены на UX namespace без изменения infra/CI команд — [0003](decisions/0003-delivery.md).

## Проверки

| Проверка | Результат | Граница |
|---|---|---|
| `python3 scripts/validate_repo.py` | PASS | 70 Markdown files; 6 skills/adapters, namespaces и memory contracts |
| `python3 -m unittest discover -s tests -v` | PASS, 11 tests | Включая self-contained packages всех трёх namespaces, local links и containment; без live target |
| Bundled skill `quick_validate.py skills/ux-design` | PASS | Frontmatter/name/structure, не LLM behavioral evaluation |
| `claude plugin validate artifacts/plugins/ux --strict` | PASS | Реальный manifest/path check; skill invocation в application project NOT RUN |
| Mermaid parser | PASS, 8 diagrams в UX docs/templates | Только syntax parse; visual render review NOT RUN |
| Python compile / `git diff --check` | PASS | Syntax/whitespace |
| Repository GitHub CI | PASS | [Run 39141839387](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39141839387) для implementation commit `ebed76d`; последующее уточнение full-app scope и evidence обновлено отдельно |
| Реальное UX исследование приложения | NOT RUN | Пользователь просит documentation+skill, business target не выбран |
| User testing / adaptive implementation / WCAG conformance | NOT RUN | Нужен конкретный prototype/application и отдельная проверка |

Локальный isolated plugin создан в ignored `artifacts/plugins/ux`; воспроизводимая сборка в root README. Agent должен писать application concepts в target project, а не этот package/cache.

## Следующая задача

Прочитать общий [индекс](../../INDEX.md), относящиеся ADR и этот handoff. Для применения вызвать `/ux:design` с описанием либо из target проекта с README. Там сначала прочитать existing UX concepts/decisions, понять роли/процессы, задать конкретный business вопрос при неясности и выполнить реальное reference research. Методы NN/G/W3C/Mermaid в этой базе не заменяют 3–4 бизнес-референса. Approved статус и user-testing evidence не выдумывать.
