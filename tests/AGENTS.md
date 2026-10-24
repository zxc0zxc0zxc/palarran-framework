# Offline verification

Inherits root. Suite: python3 -m unittest discover -s tests -v. Structural checks: python3 scripts/validate_repo.py; runtime lab: python3 scripts/factory_acceptance.py.

- Provider-facing checks use fake transports/SDKs/CLIs; no authentication, installs, GPU, cloud APIs or paid launches. Tests never install optional tools automatically.
- Check approval/lineage, oversized/malformed receipts, unknown outcomes, revoked leases, stale artifacts, budget overshoot, cancellation terminal proof and secret/path/output boundaries. Happy-path exits alone are insufficient.
- Isolate temporary repositories/resources; do not change pinned source docs/code during ML/product-chain tests: this must trigger visible source drift.
- Graph tests check dirty/untracked/deletion drift and exclusions. Fake extraction does not establish real-graph quality; record actual local Graphify smoke separately.
- Never weaken independent verifiers for fixtures. Handoffs preserve PASS/FAIL/NOT RUN and lab/operational evidence boundaries.
