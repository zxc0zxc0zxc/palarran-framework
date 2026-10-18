# Источники и границы применимости

Проверено при подготовке базы: **2026-10-18**. Это curated menu десяти узнаваемых систем, не статистический top-10 по единой метрике популярности. Native materials, enterprise systems и web component ecosystems несопоставимы по одному числу downloads. Дополнительные бизнес-референсы ищутся заново для target UI; источники этой методики не подменяют такое исследование.

| Система / источник | Что используем | Граница |
|---|---|---|
| [Google Material 3](https://developer.android.com/develop/ui/compose/designsystems/material3) | Color/typography/shapes как system foundations | Compose implementation — Android; web/native adaptation выбирается отдельно |
| [Apple Liquid Glass announcement](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/) | Translucent material, функциональный слой controls/navigation, реакция на контент | Announcement 2025-06-09; не web implementation spec |
| [Microsoft Fluent 2](https://fluent2.microsoft.design/), [principles](https://fluent2.microsoft.design/design-principles) | Цельность, platform adaptation, inclusion | Конкретные web controls/версии проверить в target stack |
| [IBM Carbon](https://www.carbondesignsystem.com/), [color](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview) | Semantic color roles, layers и enterprise organization | Применимость dense layouts зависит от UX |
| [Atlassian foundations](https://atlassian.design/foundations/) | Foundations/components для сложных рабочих продуктов | Не переносить workflow Jira как обязательный UX |
| [Shopify Polaris](https://shopify.dev/docs/api/polaris), [app design](https://shopify.dev/docs/apps/design) | Merchant/app surfaces и согласованные компоненты | Старый polaris.shopify.com перенаправляет сюда; не назначать legacy package по памяти |
| [Adobe Spectrum](https://spectrum.adobe.com/), [color system](https://spectrum.adobe.com/page/color-system/) | Цветовая система, структура сложных инструментов | Визуальная адаптация не означает копирование creative app UX |
| [Salesforce SLDS](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds.html) | SLDS 2/version awareness, styling hooks | Не смешивать legacy и текущие механизмы стилизации |
| [Ant Design](https://ant.design/docs/spec/introduce/), [values](https://ant.design/docs/spec/values/) | Enterprise design language, hierarchy/consistency | Не универсальный mobile pattern |
| [GitHub Primer](https://primer.style/) | Система для согласованного web interface | Root overview изучен; конкретные component specs проверять при применении |
| [WCAG 2.2 contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [non-text](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | Применимые thresholds и исключения | Частичные checks не доказывают полную conformance |
| [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [targets](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [focus](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) | Responsive/accessibility review | Проверять реальный output, не только намерение |
| [Animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) | Отключаемое взаимодействующее motion | Уровень AAA; reduced-motion policy — наше базовое решение |
| [Design Tokens Format Module](https://www.designtokens.org/tr/drafts/format/) | Направление стандартизации обмена tokens | Community spec, версия проверяется при применении; наш example не заявляет соответствие |

`m3.material.io` и Apple HIG materials/Liquid Glass overview при проверке отдавали JS shell без доступного содержимого. Точные неподтверждённые требования оттуда не извлекались: использованы читаемые official Android docs и Apple Newsroom. Часть deep links Primer была недоступна; описания меню — наши рекомендации на основе доступных источников, не цитаты скрытых страниц.

Не утверждать, что известность системы доказывает пригодность для target или рост conversion. Любая такая гипотеза требует отдельных исследований. Перед работой с конкретным приложением проверить актуальные official docs и реальные visual references, записать date/platform/version/access в research cards.
