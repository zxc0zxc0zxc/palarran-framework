# Ten-package registry

Feature PAL-20261024-A7F2C1, contract frozen2026-10-24 from the user's ten-package ownership request and the repository's37 existing skills plus the separately assigned infrastructure incident skill. This is declarative module discovery, not installation, service activation, deployment or an availability attestation. The coordinator moves source files and integrates the installer separately.

`packages/catalog.json` is the public inventory. Capabilities live under `packages/<package>/<capability>/`; their skill entrypoint is `skills/<skill>/SKILL.md` within that capability. `legacy_path` records the former repository location for explicit migration, never a silent runtime fallback.

| ID | Exact title | Capability ownership |
| --- | --- | --- |
| core | Core | agents, parallelism, security, orchestration, pipelines, setup, packages, coordination |
| memory | Memory | memorize, remember, sessions, knowledge, vacuum |
| product | Product | research |
| design | Design | ux, ui |
| code | Code | frontend, backend |
| machine-learning | Machine Learning | experiments |
| docs | Docs | documentation (planned, no implemented skill) |
| science | Science | preprint |
| validation | Validation | agents, application |
| infrastructure | Infrastructure | planning, delivery, vps, incident |

Every non-Core package directly requires core. Additional dependencies must name known packages and remain acyclic. Optional Neo4j memory and cross-machine coordination services are not package prerequisites; selecting a package grants no service credentials or deployment authorization. Core's mcp-build skill belongs to agents. Agent eval/improve belong to Validation. VPS inventory/management and incident response belong to Infrastructure.

## Strict manifest

Exactly `{version:1,packages:[PACKAGE]}` with all ten distinct public IDs/titles. PACKAGE has exactly `id,title,description,requires,capabilities,skills`. Description is nonempty<=2000 characters; requires is a unique list of known IDs, without self-dependencies. Core requires[]; every other package includes core.

CAPABILITY has exactly `id,status,description`; status is implemented/planned. IDs are lowercase ASCII `[a-z][a-z0-9-]{0,63}`, unique within a package; each package has1..32capabilities. Status describes declared capability implementation, which may still exist at its legacy path during migration. It is not evidence that canonical modular paths already exist or that a service is running. Docs has an explicitly planned documentation capability and empty skills, never a fabricated available skill.

SKILL has exactly `name,path,legacy_path`; names are `palarran-` prefixed lowercase IDs<=128characters and globally unique owners. Path must be exactly `packages/<owning-package>/<declared-capability>/skills/<name>/SKILL.md`, legacy_path exactly `skills/<name>/SKILL.md`. No absolute paths, `..`, `.`, empty components, backslashes, escaping, aliases or ambiguous duplicate ownership. A capability may own several skills or none. Each package has<=100skills; catalog total<=1000. Catalog UTF-8<=1MiB; unknown fields, duplicate JSON keys, invalid types, booleans as version, nonfinite values and malformed JSON are rejected. It defines no commands/hooks/executable code.

## Python API

`packages.core.packages.registry` uses Python>=3.9 stdlib only:

- `validate(value) -> dict`: strict structural validation and an independent deep copy; reads no filesystem/executes nothing. Future canonical files need not exist yet.
- `Registry(value)` / `Registry.load(path)`: immutable-by-copy catalog wrapper; load reads a bounded regular UTF-8 JSON file, rejects symlink ancestors and performs structural validation. `catalog` returns a fresh copy.
- `resolve(selected) -> {packages:[id],skills:[SKILL]}`: validates a nonempty list of distinct known package IDs, computes dependency closure and orders dependencies before dependents. Ties use the fixed public-ID order above, not user-selection/dictionary order; skills are ordered by resolved package then skill name. Records contain canonical and legacy paths as data only. No installs, filesystem probes, model calls or optional-service dispatch.
- `check_paths(root, selected=None) -> [canonical_relative_path]`: **explicit** filesystem verification of all packages, or the selected closure. Every declared canonical skill must exist as a regular file below a real root with no symlink ancestors/components. Failure raises RegistryError; no partial-success claim or legacy fallback. It reads metadata, never imports/executes skill code. An empty skill list passes with zero checked skill files, not a claim that planned documentation exists.

RegistryError exposes safe fixed codes, not source content. The registry alone verifies neither linked guides, installed resources, skill semantics, byte integrity nor host discovery. Those belong to packaging/installer/domain checks. File/path validation assumes trusted local ownership; it is not protection against concurrent malicious same-user filesystem replacement.

## Verification

Offline fixtures cover all38 ownership declarations, exact ten-package IDs/titles, Core closure/order/dedup, optional-service independence, unknown/cyclic/duplicate schema rejection, capability/path ownership, path escapes/symlinks, absent canonical paths and declared-only planning. Synthetic temporary paths are not evidence that source migration is complete. Coordinator performs final repository/installer integration checks against the actual moved subject.
