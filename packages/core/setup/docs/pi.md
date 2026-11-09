# Install Palarran in pi

Checked2026-11-09 against the installed pi1.0.0 package docs and SDK types. Pi loads a local package through the personal `packages` list in `~/.pi/agent/settings.json`; an explicit `pi` manifest selects extension and skill resources. Host-provided pi modules are peers rather than bundled dependencies. Primary references: [pi package documentation at v1.0.0](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/packages.md), [pi skill discovery](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/skills.md). Source/version compatibility and observed local loader results remain separate from live provider evidence.

## Review then install

From a clean trusted Palarran checkout containing the pi capability:

```sh
python3 packages/core/setup/pi_setup.py --source /TRUSTED/palarran --packages all --plan
python3 packages/core/setup/pi_setup.py --source /TRUSTED/palarran --packages all
```

`--home` and `--agent-dir` select an explicit test/operator home and pi configuration directory. Default paths are the current user's home and `~/.pi/agent`. The supervisor requires Node **22.13 or newer** with built-in `node:sqlite` `DatabaseSync`. Actual installation checks the selected local Node executable with one in-memory SQLite query before changing settings or creating a runtime; it loads no pi SDK, providers or auth. `--node /ABSOLUTE/node` selects the Node executable used by the intended pi installation; otherwise the existing PATH Node is resolved. Missing/unsupported runtime is a safe `node_runtime_unsupported` error, without automatic installation or upgrade. The native package also declares `engines.node: ">=22.13"`.

No network, package-manager install, model prompt, auth read, supervisor start, MCP activation or remote deployment occurs. `--plan` reads the trusted source and owned installation metadata but writes nothing and does not run the Node capability probe. This command installs a reviewed local package; pi loads it on a fresh session or `/reload`.

The runtime is pinned under `~/.palarran/pi/runtimes/<commit>/<selection-hash>/`. The public Git snapshot preserves original canonical paths and `packages/layout.json`; Python integration imports, Node sibling imports and relative skill guides remain unchanged. It does not reuse the old flattened project-library layout. Complete supporting guides and helpers stay together; only selected canonical skill paths are exposed by the native package manifest. Explicit `--packages` wins. Updates otherwise inherit their exact selection. A fresh installation can inherit `packages` from the global Palarran config; absent choices are `missing_packages`, not an implicit `all`.

## Ownership and recovery

The installer owns one local package declaration, a private receipt and immutable runtime files. It never edits auth, model registries, custom extensions/subagent definitions, agents, themes, provider selection or project settings. Existing unrelated settings fields and package declarations are preserved. A receipt verifies file hashes and the owned declaration before update; changed local runtime files or ambiguous/missing ownership stop before replacement. Existing source journals, `.env` secrets, caches and Git history are excluded.

Preflight completes before writes. Installation keeps old runtimes and a private exact settings backup. A durable pending intent precedes replacing settings/receipt; interruption yields `recovery_required`, never automatic replay. Ordinary errors restore settings only if the current bytes still match the installer's expected state. No force flag, secret output or automatic cleanup of unknown state is provided. Inspect the pending intent and backups before a manual recovery.

## Native use and verification

Pi exposes discovered skills as `/skill:<frontmatter-name>`, for example `/skill:palarran-code-review`; the library's conceptual `/palarran:code:review` alias is not a promise of a native pi slash command. `/swarm` and the `swarm_*` tools come from the separate pi extension when it actually loads. The installer reports resource paths and expected counts; only the real pi loader can establish discovery/loading.

Offline installation tests use temporary homes and no provider calls. A local SDK/resource-loader check proves compatible resource discovery; it does not establish model quality, supported transport costs, live parallel throughput or operational availability. Review the [pi integration contract](../../pi/docs/contract.md) before authorizing worker execution.
