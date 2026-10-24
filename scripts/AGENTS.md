# Scripts

Inherits root; mandatory sources by trigger are in docs/skills/domain-contracts.md. Canonical public CLI messages, identifiers and skill guides use English; interaction/new artifact preferences follow project/global .palarran/config.json.

- Validators/inventory/cost helpers must work offline; missing/unknown prices are not zero. --plan permits no refresh/target access/provider calls.
- Packaging is self-contained: explicit public resources only; never copy target memory, .graphify/venv/cache, .delivery, .env, state or external symlinks. Update packagers/packaging tests for new resources.
- execution_progress preserves frontend/backend legacy-marker compatibility, revisions/commits/evidence and remaining tasks; one coordinator updates shared progress/index.
- graph_context uses pinned optional graphifyy in target-local venvs, code-only staging, scrubbed environments, bounded outputs and dirty/untracked freshness. Never invoke Graphify installs, cloud, semantic/media passes or project executables.
- CLI side effects must be explicit. Never overwrite others' files or generate target AGENTS within planning scope.
- keenable_auth headers exposes secrets only to Codex's internal channel; never display stdout. check is offline, doctor metadata-only without tools/call; fixed HTTPS origin/no redirects.
- project_setup setup selects install/update by receipt; never adopt partial/corrupt states. Fresh setup also checks memory; MEMORY_NOT_READY does not mean writes were undone.
- project_setup update: old/local/new ownership, configs untouched, --plan offline; pending transaction blocks replay. Rollback checks exact current state before restore; memory doctor uses pristine public release, not carried project code.
- Checks: scripts/validate_repo.py and offline unit suite; runtime-facing behavior changes additionally require scripts/factory_acceptance.py. No paid/live checks.
