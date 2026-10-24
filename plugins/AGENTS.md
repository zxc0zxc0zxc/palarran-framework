# Plugin namespaces

Inherits root. Canonical public manifests, identifiers and skill instructions use English; interaction/new artifact preferences follow project/global .palarran/config.json.

- Namespace commands point to existing .claude adapters/canonical skills. Update scripts/validate_repo.py, scripts/package_plugin.py and packaging tests together when membership changes.
- Packages include self-contained mandatory docs/templates without outside links, target ADR/state/secrets or .graphify artifacts. Optional Graphify dependencies are not default runtime requirements.
- Manifest changes do not imply user-owned configuration/agent installation/activation. Checks are offline, without install hooks/cloud/paid APIs.
