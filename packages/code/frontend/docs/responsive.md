# Responsive implementation

The source [UI responsive contract](../../../design/ui/docs/responsive.md) becomes working layouts. Use fluid widths, Grid/Flex and content-driven breakpoints; a fixed desktop canvas with transform/scale is not responsive. [Google web.dev](https://web.dev/articles/responsive-web-design-basics) recommends viewport meta and adapting layout to content/device capabilities; details below are our verification policy.

For each screen/state, preserve access to tasks: navigation, primary/secondary actions, forms, dialogs, tables and long content. Probes at 320/390/768/1440 CSS px plus layout boundaries and an intermediate width are a starting matrix, not universal breakpoints. Specify viewport height; check landscape/short windows when relevant to the scenario. Check keyboard, safe area and virtual keyboard in the real runtime when that target is specified; do not present device emulation as a physical iPhone/Android test.

Practical checks:

- Headings/labels/values/CTA remain unclipped; strings beyond the happy path, empty data and localization preserve layout. Choose `min-width`, wrapping and local scrolling for two-dimensional tables according to meaning.
- Content reflows at 320 CSS px under [W3C](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), with applicable exceptions. Fix page-wide horizontal overflow; distinguish local table scrolling from a whole-page defect.
- Do not disable user zoom. Check text zoom/scaling, not viewport resizing alone; sticky layers must not cover a focused field/action.
- Verify semantic controls/labels, keyboard navigation, visible focus, dialog close/focus return and error association through interaction. Screenshots do not establish these.
- Contrast/target sizes/use of color follow [UI criteria](../../../design/ui/docs/responsive.md), with exceptions and correct thresholds; do not promise full WCAG conformance from one scan.
- Check reduced motion, unsupported effects and an opaque glass variant; contrast after compositing and both themes when within source UI scope.

Do not hide necessary mobile actions/data without the UX-defined access path. If adaptation requires changing a flow, record a UX delta; explain minor layout choices within source through ADRs without unnecessary approvals. Record checks by actual screen/state/browser/viewport instead of unsupported “mobile works” claims.
