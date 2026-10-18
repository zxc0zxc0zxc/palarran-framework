# Выбор дизайн-кода: 10 систем и свои references

«Дизайн-код» здесь — узнаваемая система визуальных правил/семейство, а не библиотека, которую нужно автоматически установить. Меню объединяет web/enterprise systems и native material; они не сравнимы по одной установленной нами метрике popularity. Выбраны известные системы с устойчивыми first-party sources. **Не называть список объективным top-10**, не приписывать ему доли рынка.

Machine-readable source меню — [catalog.json](catalog.json): ровно 10 уникальных system IDs. Custom — отдельный режим, не одиннадцатая «система компании». Цифры ниже — номера выбора.

| № / ID | Направление и canonical reference | Наша отправная визуальная интерпретация | Что учитывать |
|---|---|---|---|
| 1 `material-3` | **Material 3 — Google**, [официальная документация](https://developer.android.com/develop/ui/compose/designsystems/material3) | Semantic tonal palette, shape/type hierarchy, выразительные controls | Не смешивать M2/M3/Expressive версии; web-адаптация не означает Android UI everywhere |
| 2 `liquid-glass` | **Liquid Glass — Apple**, [официальное описание](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/) | Translucent functional layers, depth, restrained glass navigation | Apple описывает native real-time material; CSS blur — лишь вдохновлённая адаптация. Opaque fallback и contrast обязательны |
| 3 `fluent-2` | **Fluent 2 — Microsoft**, [система](https://fluent2.microsoft.design/) | Layered surfaces, calm workspaces, clear control hierarchy | Выбрать платформенную версию; не переносить Windows materials на web без проверки |
| 4 `carbon` | **Carbon — IBM**, [система](https://www.carbondesignsystem.com/) | Structured grids, neutral layered surfaces, disciplined data density | Dense desktop data не сжимать в нечитаемый mobile; source major/version фиксировать |
| 5 `atlassian` | **Atlassian Design System**, [foundations](https://atlassian.design/foundations/) | Team-workspace clarity, semantic status/color, consistent spacing | Наша app identity и UX важнее копии Jira shell; tokens/version проверять |
| 6 `polaris` | **Polaris — Shopify**, [официальные references](https://shopify.dev/docs/api/polaris) | Calm commerce/admin surfaces, actionable cards/forms/data | App surfaces и current web components отличаются от legacy packages; storefront не равен admin |
| 7 `spectrum` | **Spectrum — Adobe**, [система](https://spectrum.adobe.com/) | Content/tool-focused hierarchy, balanced controls and color roles | Проверять platform/version; не смешивать Spectrum variants без rationale |
| 8 `lightning` | **Lightning/SLDS 2 — Salesforce**, [официальное описание](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds.html) | Structured enterprise objects, record/form hierarchy and semantic styling | LWC framework не обязателен для вдохновения; native SLDS integration отличается от visual adaptation |
| 9 `ant-design` | **Ant Design — Ant**, [официальное введение](https://ant.design/docs/spec/introduce/) | Enterprise information hierarchy, consistent forms/tables and states | Ant web library не решает автоматически mobile UX/accessible custom overrides |
| 10 `primer` | **Primer — GitHub**, [система](https://primer.style/) | Practical developer-workspace surfaces, borders, restrained hierarchy | Не копировать GitHub branding/sidebar и не путать dark mode с отдельным design code |

Это наша прикладная интерпретация для выбора, не дословный список правил владельцев. Точные foundations/components и визуальные примеры выбранной версии агент читает/смотрит при реальном вызове. UI, вдохновлённый системой, не именуется её официальной реализацией или endorsement.

## Как предложить выбор

В application task показать все 10 названий со ссылками и коротким признаком + «Свои референсы». Рекомендовать 2–3 по UX/audience/platform/плотности, объяснив tradeoffs; не навязывать один default. При доступном визуальном output показать 2–3 сопоставимых style samples на **одном и том же UX screen/data**, а не рисовать 10 полных приложений автоматически.

Если host позволяет selectable options — использовать его, иначе краткое numbered menu с free-text ответом. При ограничении количества кнопок показать shortlist, но полный catalog оставить доступным и дать ввод любого ID/custom. Preselected пункт не выбран, пока пользователь не отправил ответ. Не спрашивать style при authoring самого скилла.

Уже заданный `Material`, `Liquid Glass`, system ID или «используй мои references» — достаточное preference, не начинать повторный опрос. Ранее accepted style переиспользовать, если новый запрос его не меняет; меню по-прежнему доступно для пересмотра. Пока выбора нет, сохранить independent work и alternatives, но не финализировать accepted design code за пользователя.

## Режимы

`system`: canonical system + минимум 2 дополнительных visual references. `custom`: присланные материалы + дополнительные релевантные источники по пробелам; не принуждать к одному preset. `system+custom`: один governing system, пользовательские материалы объясняют нужные overrides. Custom refs — полноценный выбор: «что именно нравится» (типографика, palette, плотность, shape, imagery) можно уточнить, не требуя от пользователя назвать техническую библиотеку.

Брендовые assets/шрифты/пакеты не переносятся автоматически: проверить права/доступность и уместность проекта. Нужен согласованный собственный visual language, а не смесь всех десяти palettes/components.
