# Palarran banner

`palarran-banner.png` is the approved README banner, generated with the built-in image generation tool on2026-10-24. Near-black background, a flat geometric ship mark, warm-white Palarran wordmark and short subtitle. Rounded outer corners use transparent alpha. No external company logo or reference screenshot is embedded.

Final edit prompt: preserve the minimal banner typography, layout and dimensions; round all four outer corners with genuine transparent pixels outside the rounded rectangle; preserve the existing flat ship mark; no border, shadow or additional graphics.

The earlier illustrated/cartographic exploration is not selected.

## Framework diagrams

The three diagrams use original SVG geometry/text, rendered to PNG with a local browser. Source files stay editable and text-searchable. All use the approved near-black background, warm-white typography, muted lines, rounded corners and transparent outer pixels.

| Diagram | Editable source | README image |
| --- | --- | --- |
| Architecture | [SVG](architecture.svg) | [PNG](architecture.png) |
| Development workflow | [SVG](development-pipeline.svg) | [PNG](development-pipeline.png) |
| Capabilities beyond skills | [SVG](framework-features.svg) | [PNG](framework-features.png) |

Architecture sources: [memory](../docs/memory/architecture.md), [web context](../docs/skills/context-retrieval.md), [configuration](../docs/setup/configuration.md), [runtime](../docs/product-factory/README.md). Workflow sources: [execution progress](../docs/skills/execution-progress.md), frontend/backend planning and build guides, [application acceptance](../docs/app/verify/README.md). Figures illustrate component responsibilities and workflow boundaries; they are not live topology or deployment evidence.

The global profile is shown at the requested canonical `~/.palarran/` location. Existing machine configuration must be migrated with its pinned runtime/MCP/tunnel references. Native Keenable usage is outside runtime accounting; the diagrams retain this boundary. Browser renders were visually inspected for clipping, readability and arrow direction on2026-10-24.

Re-render the original SVG diagrams with `node scripts/render_readme_assets.cjs` after setting `PALARRAN_PLAYWRIGHT` to an existing local Playwright module and `PALARRAN_CHROMIUM` to the existing browser executable. The renderer blocks page network requests and installs nothing. This does not edit or regenerate the approved bitmap banner.
