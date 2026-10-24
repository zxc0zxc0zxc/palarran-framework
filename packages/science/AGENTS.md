# Science

Inherits root. Read [domain contracts](../core/agents/docs/domain-contracts.md) and applicable capability guides before changes; local rationale belongs in target .palarran/.

- Owns reports from existing experiments. Bind claims to exact evidence, preserve negative/missing results and real authorship; no training or publication is implied.
- Keep implementation, skills, docs, templates and command adapters in the owning capability. Root CLI/import files are compatibility entrypoints; edit canonical implementation.
- Cross-package references must be explicit. Preserve source-path mapping and portable exports when moving public resources. Never duplicate domain implementation in Core.
- Checks from the repository root: `python3 scripts/validate_repo.py`, `python3 -m unittest discover -s tests -v`; runtime changes also `python3 scripts/factory_acceptance.py`. No paid/live deployment tests.
