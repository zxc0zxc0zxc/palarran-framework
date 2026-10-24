# Understand the business and reuse screens

## /palarran:ux:design input

The description after the command is the primary intent. Without one, find README in the target root; in a monorepo, find the relevant product/package README and product-document links. A library-installation README may not explain the business: do not turn dependencies into a product specification. If the target itself is unclear, clarify the project first.

Reconcile the description with current PRD/DESIGN/product docs, existing routes/screens and accepted `.palarran/` decisions. The user's latest request takes precedence over an old hypothesis; describe substantive contradictions. Code shows what is implemented, not proof of what is desired. Do not invent product decisions from the repository name.

A concise business brief includes:

- Intended audience: roles, permissions, usage context/devices/language/market; label assumptions.
- The person's task, process trigger and successful outcome for them.
- Business entities and lifecycle: for example request → results → selection → saving. Do not add payments/chat/registration unless the business requires them.
- Primary journeys, existing constraints, monetization only when known, privacy/trust and important failure cases.
- Current scope and unknowns; success criteria remain hypotheses without user data.

Method basis: [NN/G task analysis](https://www.nngroup.com/articles/task-analysis/) decomposes an actual goal into actions and context. Our brief format and catalog are a project contract, not a particular company's recipe.

## Inventory and clarification

First collect a screen/process inventory from docs, UI/routes and previous concepts. For each process: role, entry, data/preconditions, actions, success, errors/denial and exit. A URL/route is not always a separate screen: the same task may have state variants, modals or tabs. Account for auth/privacy boundaries and different roles explicitly.

If a process's input/meaning/outcome is unclear, ask: **“What does this business process—<name>—do? What does the user start, and what do they get at the end?”** Narrow this to the precise unknown when possible. Do not ask “which screens should I draw?” instead: the agent investigates the business process. Group questions without overloading the user; dependent screens remain proposed while independent research continues.

Example: “What does ‘profile verification’ do: does the user submit data to a moderator or confirm a contact method?” These options need different states and trust boundaries; choosing without an answer would be guesswork.

## Reuse before creation

| Catalog match | Decision |
|---|---|
| Same role/goal/entities/actions/permissions | Reuse Screen ID; update its revision with a reuses link |
| Same goal, different loading/empty/error/pending | Add a state to the existing screen |
| Shared functional block across different tasks | Reuse Block ID/interaction contract without merging whole screens |
| Different outcome, role/permissions or long separate process | New Screen ID with rationale and process link |
| Temporary context with a preserved return path | Consider an overlay/sheet; explain focus, dismiss, back and deep link instead of creating one for fashion |

In `reuse-map.md`: process → existing screen/block/state → reuse/change/new → explanation/ADR → affected journeys. Separately assess whether reuse harms clarity or permissions; “fewer screens” is not an end in itself. Do not silently overwrite old concepts: create a new revision and supersedes link. Earlier materials provide context, but matching screen names do not establish compatibility.
