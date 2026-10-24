# UI responsiveness and accessibility

UI must implement [source UX](../../ux/docs/responsive.md) behavior in visual layouts. One desktop screenshot scaled to a phone is not responsive UI. Explain placement through tasks, reading, control reachability and content priority.

## Layout contract

For each screen/state, describe narrow/mobile, tablet and desktop: content width, columns, gutters, navigation type, action-group wrapping, tables/cards/dialogs, long strings and text. Choose breakpoints where content breaks rather than by device brand. Probes at 320, 390, 768 and 1440 CSS px are our starting checks, not a universal standard; also check layout transition points and intermediate widths. Account for viewport height, safe areas, touch and virtual keyboard when corresponding preview/runtime exists.

Preserve primary action, reading order and UX states. Hide a secondary column only with an accessible UX-defined path to its contents. Record changed task methods in `ux-deltas.md` instead of introducing them silently. Tables may need local horizontal scrolling; do not accidentally make the entire screen scroll horizontally. Distinguish valid two-dimensional-content exceptions from ordinary text.

## Visual criteria

- [WCAG contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): normal text 4.5:1, large text 3:1 using the source's large-text definition and applicable exceptions. Do not call 3:1 sufficient for every heading; never round ratios upward.
- [Non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html): check visual parts needed to identify controls/states/graphics under the applicable 3:1 criterion; do not require it for every decorative line.
- [Use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html): states/errors use more than color. [Focus visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html): visible keyboard focus; do not remove outlines without replacement or cover focus with sticky layers.
- [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html): check ordinary content at 320 CSS px with exceptions. Zoom/enlarged text must not clip labels/values/actions; breakpoint screenshots alone do not test zoom.
- [Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): 24×24 CSS px or applicable conditions/exceptions, including spacing; comfortable touch targets may be larger. Check size and spacing together.
- `prefers-reduced-motion` is our baseline policy for substantial motion. [Animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) is **AAA**; do not attribute it to AA.

These are targeted checks, not full WCAG certification. Handoff lists actually checked criteria and limitations: screenshots do not establish keyboard/screen-reader behavior.

## Glass, themes and fallbacks

For Liquid Glass and any translucent materials, check contrast after compositing on the lightest/darkest and heterogeneous actual backgrounds. An opaque token-pair formula does not establish contrast under blur. Controls/text need stable readable surfaces; material must not obscure action priority. Provide opaque/high-contrast variants and fallback for unsupported `backdrop-filter`; reduced effects preserve hierarchy without blur/animation. Check dark mode separately if selected.

[Apple](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/) describes native material reacting to content. Label CSS approximation in web previews as adaptation, not native reproduction of Apple's renderer. Do not automatically transfer native-platform assumptions to web.
