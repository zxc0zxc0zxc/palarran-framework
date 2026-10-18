# Repository instructions

- Public code and identifiers are English; project guides and user-facing skill instructions are Russian.
- `docs/infra/plan/` is the mandatory source of truth for infrastructure skills. Update affected guides and adapters together when behavior changes.
- Distinguish vendor statements from our architectural recommendations. Cite primary sources near recommendations; keep source dates and applicability in `sources.md`.
- Infrastructure examples are inert until adapted to a target. Never introduce real addresses, secrets, state files or credentials into Git.
- For infra skills, `--plan` means no target access, cloud API calls or remote state refresh. Default mode allows read-only inventory; deployment requires authorization for the concrete plan.
- Run `python3 scripts/validate_repo.py` and the offline unit suite after changing skills or inventory code. Never run a live infrastructure apply as a test.

- `docs/ci-cd/` is the mandatory source of truth for GitHub/GitLab CI/CD skills. CI/CD work never requests SSH target access; use GitOps, scoped deployment APIs or an existing trusted pull-controller. Documentation-only requests do not authorize creating skills, installing agents or activating application deployment pipelines.

- Before every task, read `.ai-development/INDEX.md` and relevant accepted decisions/context; verify assumptions against current evidence. Follow `docs/skills/decision-memory.md` for every skill and future skill.
- Every accepted choice must have a concise rationale/evidence/alternatives/consequences recorded in target-project `.ai-development/<area>/<task>/decisions/` before dependent changes. Update the index and handoff; preserve superseded history and reuse prior records as context. Never store secrets/raw logs there. Scratch is temporary; durable decisions are not auto-deleted.
- Skill checkout and target project are different roots. Write project memory/results in the target, never the installed package. `.delivery/` owns current machine/environment config; `.ai-development/` owns the rationale.

- `docs/ux/` is the mandatory source of truth for `/ux:design`: business description or target README, 3–4 distinct researched products (default 4), evidence-backed account/screenshot analysis, per-screen adaptive diagrams/states and concise UI copy. UX does not prescribe visual style or application implementation.
- UX concepts/revisions and the screen catalog persist in target `.ai-development/ux/`; accepted rationale belongs in canonical decision records. Read them before subsequent tasks, and do not claim screenshot inference/user testing/adaptive implementation as observed fact.

- `docs/ui/` is mandatory for `/ui:design`: bind to source UX revision/screens/states; offer ten established systems plus custom references, with no invented popularity rank. Study canonical/main plus at least two additional visual references. Preserve UX behavior and short copy; propose UX changes explicitly.
- UI delivers responsive visual previews, semantic tokens/components and real render evidence when tools allow; missing mandatory checks means draft, not verified. If the design needs bitmap imagery, generate it using available image tools and include it with asset provenance/responsive crops; never fabricate observed reference screenshots. Persist UI concepts/assets/revisions and rationale in target `.ai-development/ui/` and reuse them in later tasks.

- `docs/frontend/` is mandatory for `/frontend:build`: bind implementation to source UX/UI revisions and all in-scope screens/states, preserve existing stack and source behavior/style, and persist implementation decisions/coverage in target `.ai-development/frontend/`.
- Frontend completion requires actual browser interaction and viewed render evidence across responsive layouts, with mocks distinguished from real API outcomes. Build alone is insufficient; unavailable mandatory browser/runtime/integration checks mean partial/unverified. Reuse UI images; generate required missing bitmap assets with provenance. No deployment or unrelated backend rewrite implied.
