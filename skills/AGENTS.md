# Skills

Inherits root. Before skill changes read docs/skills/global-memory.md, docs/skills/decision-memory.md, agents-authoring.md and the mandatory profile in domain-contracts.md. Domain documentation precedes skill/command adapters.

- SKILL.md stays a concise workflow linking mandatory docs. Do not blur plan/build scope, permissions or evidence for brevity.
- Project instructions/ADRs/graphs belong to target root, not installed skill checkouts. Read applicable AGENTS before code changes; create them only within authorized implementation scope and actual boundaries.
- Graphify is optional: fresh bounded navigation, then original sources; graphs replace neither sources/UX/UI/API contracts/verification nor decisions. Never install tools automatically during planning.
- New skills update namespace plugins, .claude adapters, .agents discovery links, validator registration and packager resources together. No global Codex/Claude config changes without explicit user requests.
- Checks: scripts/validate_repo.py, offline suite and portable packaging tests. Missing tools/evidence mean draft/partial/NOT RUN, never verified outcomes.
