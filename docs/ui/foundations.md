# Foundations: coherent visual language

Start with source UX and selected [design code](design-codes.md), then foundations; do not begin with a random palette. Every choice needs reasons, alternatives and a reference-observation/ADR link. Separate company information from our adaptation.

## Tokens and hierarchy

| Layer | Define | Check |
|---|---|---|
| Color | Semantic roles: surface, text, text-muted, border, action, on-action, focus, success/warning/error; interactive states | Contrast on actual backgrounds; meaning conveyed beyond color |
| Typography | Licensed family/fallback, heading/body/label sizes/weight/leading; long values | Readability, zoom, localization, no decorative multiline walls of text |
| Layout | Content width, columns, gutters, spacing scale, compact/comfortable density | Source UX hierarchy, useful space and touch targets |
| Shape/elevation | Radii, borders, shadows and layer order | Consistent principles for similar components; overlays do not obscure actions |
| Material | Opaque/translucent surfaces, blur budget, fallback | Glass does not make text/controls unreadable |
| Icons/assets | Consistent family/weight, meaning, source/license | Icon-only actions have accessible names; do not copy business logos |
| Motion | Transition purpose, duration/easing, reduced-motion variant | Explains state changes without delaying tasks |

Primitive values → semantic roles → component tokens. Do not scatter raw hex/px values across pages. In-scope themes share semantic roles with independently verified values. [Carbon](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview) illustrates role-based color/layers; [Spectrum](https://spectrum.adobe.com/page/color-system/) illustrates color-system structure. These are examples, not grounds to copy values into every application.

Save `tokens.json` and `tokens.css` in the concept revision and describe their mapping. The [example](../../templates/ui/tokens.example.json) is our simple exchange format, **not claimed DTCG compatibility**. If the project needs [Design Tokens Format Module](https://www.designtokens.org/tr/drafts/format/), separately check current version/structure and validator; do not call a community specification a W3C Recommendation.

## Components and states

First reuse existing target components and UX blocks. For buttons, fields, navigation, cards, tables and dialogs, describe anatomy, variants, density and responsive behavior. State matrix: default, hover for pointer, focus-visible, pressed/selected, disabled, pending, validation/error, empty and success where corresponding UX states exist. Explain N/A; do not add business states merely to fill a matrix.

Disabled/pending must not differ only through very low opacity; pending preserves size/label context. Error is more than a red border. Preserve existing concise copy; designer annotations do not become UI text. For overlays, describe focus/close/back/scroll under UX without inventing scenarios.

Library selection and application code are separate implementation decisions. Naming Material/Polaris/Lightning does not authorize installing packages, accepting incompatible licenses/platforms or copying branding. For example, current [Polaris](https://shopify.dev/docs/api/polaris) documents web components; do not prescribe its legacy React package from memory. For [SLDS](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds.html), account for current version and styling hooks.
