# Sources and applicability boundaries

Checked while preparing this reference: **2026-10-18**. This is a curated menu of ten recognizable systems, not a statistical top ten under one popularity metric. Native materials, enterprise systems and web-component ecosystems cannot be compared through one download count. Research additional business references anew for target UI; methodological sources do not replace that research.

| System / source | What we use | Boundary |
|---|---|---|
| [Google Material 3](https://developer.android.com/develop/ui/compose/designsystems/material3) | Color/typography/shapes as system foundations | Compose implementation is Android; select web/native adaptation separately |
| [Apple Liquid Glass announcement](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/) | Translucent material, functional controls/navigation layer, reaction to content | Announcement 2025-06-09; not a web implementation spec |
| [Microsoft Fluent 2](https://fluent2.microsoft.design/), [principles](https://fluent2.microsoft.design/design-principles) | Coherence, platform adaptation, inclusion | Check concrete web controls/versions in target stack |
| [IBM Carbon](https://www.carbondesignsystem.com/), [color](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview) | Semantic color roles, layers and enterprise organization | Dense-layout applicability depends on UX |
| [Atlassian foundations](https://atlassian.design/foundations/) | Foundations/components for complex work products | Do not impose Jira workflow as mandatory UX |
| [Shopify Polaris](https://shopify.dev/docs/api/polaris), [app design](https://shopify.dev/docs/apps/design) | Merchant/application surfaces and coherent components | Old polaris.shopify.com redirects here; do not prescribe legacy packages from memory |
| [Adobe Spectrum](https://spectrum.adobe.com/), [color system](https://spectrum.adobe.com/page/color-system/) | Color system, complex-tool structure | Visual adaptation does not mean copying creative-application UX |
| [Salesforce SLDS](https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-slds.html) | SLDS 2/version awareness, styling hooks | Do not mix legacy/current styling mechanisms |
| [Ant Design](https://ant.design/docs/spec/introduce/), [values](https://ant.design/docs/spec/values/) | Enterprise design language, hierarchy/consistency | Not a universal mobile pattern |
| [GitHub Primer](https://primer.style/) | System for coherent web interfaces | Root overview studied; check specific component specs when applying |
| [WCAG 2.2 contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [non-text](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | Applicable thresholds and exceptions | Partial checks do not establish full conformance |
| [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [targets](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [focus](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) | Responsive/accessibility review | Check actual output, not intent alone |
| [Animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) | Disabling interaction-triggered motion | AAA; reduced-motion policy is our baseline choice |
| [Design Tokens Format Module](https://www.designtokens.org/tr/drafts/format/) | Token-exchange standardization direction | Community spec; check version when applying; our example claims no conformance |

During verification, `m3.material.io` and Apple HIG materials/Liquid Glass overview returned JS shells without accessible content. We extracted no precise unverified requirements from them; readable official Android docs and Apple Newsroom were used instead. Some Primer deep links were inaccessible; menu descriptions are our recommendations based on accessible sources, not quotations of hidden pages.

Do not claim that recognition establishes system fit for the target or increased conversion. Such hypotheses require separate research. Before working on a concrete application, check current official docs and actual visual references; record date/platform/version/access in research cards.
