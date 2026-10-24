# Implementation and integrations

## Existing stack before a new template

Inspect target instructions, Git diff, package manifests/lockfile, runtime versions, scripts, routing, CSS/tokens, UI library and data clients. Preserve others' unfinished work. Use the existing package manager and version-compatible APIs. If no foundation exists, choose a new project foundation based on constraints and record why; do not prescribe Next/React for every project or update all dependencies along the way.

Split UI into meaningful reusable components and source blocks, preserving semantic tokens and shared states. [React Thinking in React](https://react.dev/learn/thinking-in-react) helps React projects with component hierarchy and minimal necessary state. Do not duplicate derived values in state without a reason. For [Next Server/Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components), respect the server/client boundary; localize interactivity and keep server secrets out of client props/bundles. For other frameworks, read their version-specific official documentation.

## Data and behavior

Connect existing API contracts: loading, empty, validation, forbidden, not-found, timeout/error/retry where specified. Check response shapes, pagination, cancellation/stale requests, pending/double-submit and error correctness against target behavior. Do not create fake endpoints/success alerts to simulate a completed action. Without an API, use isolated, explicitly labeled adapters/fixtures and mark integration **NOT RUN**; do not implement backend/migrations without corresponding scope.

Hiding a client-side button does not replace server authorization. Credentials stay in the designated server/env mechanism, outside bundles, URLs, screenshots and logs. Do not print auth payloads/responses containing personal data for debugging. [OWASP XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html): do not insert untrusted HTML through dangerous sinks; use context-appropriate escaping/sanitization when rich text is actually necessary. This is a targeted security review, not a full audit.

Do not treat real payment/email/account mutations as harmless smoke tests. Use local/test fixtures or an explicitly authorized sandbox; build authorization does not authorize messages/payments. Enter existing test credentials through a secure mechanism without copying them into durable context.

## Assets and fidelity

Transfer source UI tokens and authorized assets into the application's native structure with source mapping; do not blindly copy preview CSS together with demo navigation. Check font availability/licensing/fallback, icon family, contrast, crops and responsive sizing. Keep CSS/SVG primitives as code. **Reuse** required generated assets that already exist instead of regenerating them on every build.

If UI requires a missing bitmap image, **generate it** using an available image tool after reading the mandatory host image skill, and include the output in the application. Preserve a prompt without private data, tool/date, chosen file/reason, alt/decorative status, responsive crops and fallback under the [UI asset policy](../ui/visual-output.md). Do not fabricate product screenshots/real product photos/logos: use authorized originals or an explicitly synthetic placeholder. A missing generator/mandatory asset means a gap/partial result, not complete visual acceptance.

Development fixtures/state controls must not enter production routes/bundles unchecked. Application files belong in application directories; `.palarran/frontend/` stores rationale/mapping/evidence, not a competing second application source tree.
