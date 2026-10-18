# Foundations: связный визуальный язык

Сначала source UX и выбранный [design code](design-codes.md), затем foundations; не начинать с случайной палитры. Для каждого выбора нужны причина, alternatives и ссылка на reference observation/ADR. Сведения компании отделять от нашей адаптации.

## Tokens и иерархия

| Слой | Что определить | Проверка |
|---|---|---|
| Color | Semantic roles: surface, text, text-muted, border, action, on-action, focus, success/warning/error; interactive states | Contrast на реальном фоне; значение не только цветом |
| Typography | Семейство с доступной лицензией/fallback, размеры/вес/leading для heading/body/label; длинные значения | Читабельность, zoom, локализация, без декоративной многострочной простыни |
| Layout | Content width, columns, gutters, spacing scale, compact/comfortable density | Иерархия source UX, полезная площадь и touch targets |
| Shape/elevation | Радиусы, border, тени и порядок слоёв | Один принцип для похожих компонентов; overlay не закрывает действие |
| Material | Opaque/translucent surfaces, blur budget, fallback | Glass не делает текст или controls нечитаемыми |
| Icons/assets | Единая family/weight, смысл, источник/лицензия | Icon-only action имеет accessible name; не копировать логотип бизнеса |
| Motion | Цель перехода, duration/easing, reduced-motion вариант | Объясняет изменение состояния, не задерживает задачу |

Primitive values → semantic roles → component tokens. Не размазывать raw hex/px по каждой странице. Разные темы, если входят в scope, имеют одинаковые semantic roles и независимо проверенные значения. [Carbon](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview) иллюстрирует role-based color и слои; [Spectrum](https://spectrum.adobe.com/page/color-system/) — устройство color system. Это примеры, а не основание копировать их значения во все приложения.

Сохрани `tokens.json` и `tokens.css` в concept revision, укажи их соответствие. [Пример](../../templates/ui/tokens.example.json) — наш простой обменный формат, **не заявленная совместимость с DTCG**. Если проект требует стандарт [Design Tokens Format Module](https://www.designtokens.org/tr/drafts/format/), проверь актуальную версию/структуру и валидатор отдельно; community specification не называть W3C Recommendation.

## Компоненты и состояния

Сначала переиспользуй существующие компоненты target и UX blocks. Для кнопок, полей, navigation, cards, tables, dialogs опиши anatomy, variants, density и responsive behavior. Матрица состояний: default, hover при pointer, focus-visible, pressed/selected, disabled, pending, validation/error, empty и success там, где есть соответствующий UX state. N/A объяснить; не добавлять новые бизнес-состояния ради матрицы.

Disabled/pending не должны отличаться только очень слабой opacity; pending сохраняет размер/label context. Error не только красная рамка. Существующий короткий copy сохраняется; annotation дизайнера не становится UI текстом. Для overlays опиши focus/close/back/scroll согласно UX, не сочиняя новый сценарий.

Выбор библиотеки и код приложения — отдельные implementation decisions. Упоминание Material/Polaris/Lightning не разрешает автоматически установить package, принять несовместимую лицензию/платформу или скопировать бренд. Например, актуальная [Polaris](https://shopify.dev/docs/api/polaris) описывает web components; не назначать legacy React package по памяти. Для [SLDS](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds.html) учитывать текущую версию и styling hooks.
