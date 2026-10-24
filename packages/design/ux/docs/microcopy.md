# Concise copy and information load

UI copy is what users see. Internal specifications/decision explanations stay separate and do not appear in the interface. The user explicitly requires concise labels without listing every possible condition in one button.

## Core rules

- One task, a clear heading and one main CTA per screen/current step by default; equally prominent actions are allowed only when inherent to the task, with explanation. Do not add instructional paragraphs “just in case.”
- A CTA names the action's result. Usually 1–3 words; this is guidance, not a strict ban on precise “Save and exit.” Necessary amount/object/consequence takes precedence over an artificial limit.
- Show details/help beside the relevant field or through disclosure instead of a long introduction. Do not hide information needed for an informed action in a tooltip.
- Do not replace labels with placeholders; errors concisely name the problem and correction. Avoid repeating one meaning in heading, subtitle, card, tooltip and button.
- Do not combine independent actions/consents into one CTA. Do not promise security/outcomes the system cannot guarantee. Refusal/back/cancel must be clear and accessible.

Basis: [GOV.UK button guidance](https://design-system.service.gov.uk/components/button/) aligns text with actions and warns that competing CTAs obscure the next step. Brevity/limits and examples below are our adaptation and the user's direct requirement; we do not copy GOV.UK visual styles.

| Situation | Poor | Better for the specified action |
|---|---|---|
| Agree to stated terms | “Accept terms, rules, analytics and confirm age” | “Accept terms”; other necessary choices separately, only when actually required |
| Save profile | “Save your profile changes for future use” | “Save” |
| Submit payment | “Continue” when charging money | “Pay ₽2,400” |
| Request error | “An unexpected error occurred while communicating with the server” | “Could not load. Retry” |
| Empty search | Long explanation of search mechanics | “No results” + appropriate “Change query” |

Concise copy must not conceal price, irreversible deletion, data-access terms or necessary consent meaning. Required content follows actual product/legal requirements; the skill invents no universal legal/analytics/age check for every screen and claims no legal sufficiency for a label.

## Copy inventory

For each screen, record only necessary strings: heading, primary/secondary actions, field labels, required hints, empty/error/success and accessible names. Additional text needs a purpose. Prefer one short phrase with examples/links in context. Include translation length and screen-reader labels in adaptation.

Review: is the action understandable without an adjacent paragraph? Is a second action hidden? Was meaning lost for brevity? Did internal rationale become user-facing copy? If a label needs a paragraph to make sense, first inspect the flow/element instead of adding a paragraph automatically.
