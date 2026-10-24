# Visual output and verification

The mandatory `/palarran:ui:design` result is a visible interface linked to source UX, not merely a palette/advice list. Record the medium in context: default local runnable HTML/CSS preview; on request, Figma/native/another agreed format with available tools. Concept work does not authorize production implementation/deployment.

## Before direction selection

Show the [menu](design-codes.md) and propose 2–3 suitable directions with reasons. If needed, prepare 2–3 **comparable** style samples of one existing UX screen/state using identical data/CTA. Do not spend resources on ten complete applications or present the first sample as an agreed selection. Samples remain exploration; final style is pending without an answer. An explicit earlier accepted direction needs no repeat selection.

## After selection

Create a versioned preview of all in-scope screens and UX states: semantic HTML, CSS tokens, responsive layouts, component/state gallery and synthetic data. A small local JS navigation/state switcher is allowed. Label preview-shell screen/state links as utility controls: they do not become application UX. Reproduce error/loading/empty deterministically rather than waiting for random API responses.

Default: standalone local files without telemetry, actual credentials, remote scripts or mandatory CDNs. Store assets with provenance/license; explain any needed external resource dependency and fallback. Do not create a package ecosystem merely for a static concept when HTML/CSS suffices. Prefer existing project conventions within agreed implementation scope.

For each screen, save a [screen spec](../templates/screen.md): source screen/state/block IDs, visible content, size variants, tokens/components, copy, evidence and ADR. The [concept](../templates/concept.md) contains UX coverage, references, style guide and handoff. Mermaid may explain mapping/flow but does not replace visual UI.

## Render review

With a browser/renderer, open the actual preview, check asset loading/console, capture and view renders at representative widths and layout boundaries. Check all screens/states through the coverage matrix; shared components may be tested in a gallery plus representative screens, with sampling described explicitly. Exercise keyboard navigation, focus, overflow, long/empty/error content, readable text/contrast and effects fallback with available tools. Record viewport, screen/state, tool, outcome and evidence path; store no personal data.

Rendering without viewing the image is not visual review. Syntax/lint does not replace rendering; screenshots do not establish interactions. Without tools, save a runnable draft and mark visual/interaction checks **NOT RUN**, listing remaining checks. Do not claim “implementation-ready” with broken coverage/readability. User-tested/approved requires actual data/user decisions.

For Figma, first use required host skills/tools; create editable frames/components by explicit request rather than arbitrary PNGs. Required bitmap assets must be generated under the rule below; do not turn code-native layouts into generated images. Format does not remove narrow/tablet/desktop and UX traceability requirements.

## Mandatory generation of required images

If the visual concept requires an image—illustration, hero, cover, texture or another bitmap asset—**generate it** with an available image-generation tool and include the selected output in the preview. Do not stop at “add an illustration.” First define purpose, composition and responsive placement; do not add unnecessary graphics without UX/visual grounds. Read a mandatory host image skill before generation when available.

In revision `assets/`, preserve the image and asset record: purpose, prompt without secrets/personal data, tool/date, authorized inputs used, selected variant/reason, dimensions/format, alt or decorative status, narrow/desktop crops/focal point and fallback/loading. Check actual rendering with the asset; do not bake text/actions into backgrounds instead of accessible HTML. Check tool/input-asset usage terms in applicable context without promising exclusive rights.

Generated assets are our concepts, not real evidence screenshots or exact photographs of real products/people. Use authorized originals for logos, actual product shots or documentary imagery; explicitly label synthetic placeholders. If image generation is unavailable, save a draft with an explicit placeholder and **NOT RUN / required asset missing**. It is not review-ready if the accepted design requires that image. Do not replace custom references with generation without a reason; do not generate CSS layouts/simple SVG icons as raster images.
