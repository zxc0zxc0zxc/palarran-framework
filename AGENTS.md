# Repository instructions

- Public code and identifiers are English; infrastructure guides and user-facing skill instructions are Russian.
- `docs/infra/plan/` is the mandatory source of truth for infrastructure skills. Update affected guides and adapters together when behavior changes.
- Distinguish vendor statements from our architectural recommendations. Cite primary sources near recommendations; keep source dates and applicability in `sources.md`.
- Infrastructure examples are inert until adapted to a target. Never introduce real addresses, secrets, state files or credentials into Git.
- `--plan` means no target access, cloud API calls or remote state refresh. Default mode allows read-only inventory; deployment requires authorization for the concrete plan.
- Run `python3 scripts/validate_repo.py` and the offline unit suite after changing skills or inventory code. Never run a live infrastructure apply as a test.

- `docs/ci-cd/` is the research/specification base for future GitHub/GitLab CI/CD skills. CI/CD work never requests SSH target access; use GitOps, scoped deployment APIs or an existing trusted pull-controller. Documentation-only requests do not authorize creating skills, installing agents or activating application deployment pipelines.
