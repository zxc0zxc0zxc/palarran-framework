# Responsive UX is mandatory

Responsiveness preserves tasks, hierarchy and control as available space/input changes. A scaled-down desktop image is not mobile UX. Every in-scope screen, including error/empty/permission states and overlays, has mobile/desktop diagrams and intermediate-width rules.

## Block contract

For every Block ID, specify priority and reading/focus order, desktop/mobile location, stretching/wrapping/collapsing, access to hidden content, scroll/sticky behavior and keyboard impact. Tablet need not be a third unique screen: a justified transition rule is required, with a separate diagram for fundamentally different composition.

| Pattern | Check |
|---|---|
| Desktop sidebar → mobile sheet | Discoverable trigger, visible selected filters, close/back/focus return and preserved data |
| Two columns → one | Reading order follows the task; primary context does not trail its action |
| Desktop dialog → mobile full-screen flow | Heading, exit, focus, back, scroll and data are preserved |
| Table/list/details | Meaningful fields remain accessible; cards or controlled scrolling serve the task instead of hiding essential data |
| Sticky action/navigation | Does not cover focused input, error, system keyboard or browser controls; no unexplained primary-action duplication |
| Hover-only control | Touch and keyboard equivalents; state does not depend solely on hover |
| Long text/translation/large fonts | Wrapping without lost meaning; actions remain accessible as content expands |

Do not impose a universal CSS breakpoint grid on every application. Start with content/task constraints and available area, then define transition rules. Account for existing platform/system safe areas and host controls (webview/mini-app) when used; do not import another platform's navigation pattern without verification.

## Accessibility in UX

- Navigation and forms work by keyboard: explicitly define focus order, visible current step, entry/return after modal/error and no keyboard traps.
- Inputs have labels/instructions and associated errors; status/loading/success need accessible messages without excessive intrusive announcements. [WAI forms tutorial](https://www.w3.org/WAI/tutorials/forms/) is the primary reference.
- [WCAG 2.2 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html): account for 320 CSS px width for vertical content and no need for two-directional scrolling except allowed exceptions. Justify content requiring 2D layout instead of declaring the entire application exempt.
- [Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): follow 24×24 CSS px or the criterion's conditions/exceptions. This is the corresponding AA minimum, not a promise that any tiny control is comfortable; assess touch ergonomics separately.
- [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html): sticky overlays must not fully hide focused components. Test specific dimensions/implementation later.

Including these items in a concept **does not establish WCAG conformance**. Check contrast, actual keyboard accessibility, announcements, text resizing and layout on the implementation/prototype; here we define UX requirements, not visual design tokens.

## Review matrix

Starting review probes: narrow 320, phone ~375/390, tablet ~768, desktop ~1280 CSS px, plus landscape/virtual keyboard and large text. Except for the normative reflow reference, these numbers are our test scenarios, not prescribed breakpoints. Account for project audience/platform; record chosen sizes and reasons.

For each screen/state/table row: what remains accessible, primary action, navigation/back, input/error/status, focus/scroll and long content. On static diagrams this is a walkthrough/planned validation, not browser-tested PASS. Without a prototype, live checks are NOT RUN, but a missing responsive concept is FAIL.
