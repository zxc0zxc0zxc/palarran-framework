# Reuse existing memory MCP in pi

Checked2026-11-09 against installed pi1.0.0 [MCP configuration documentation](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/mcp.md). Pi accepts `mcpServers` in personal `~/.pi/agent/mcp.json`; stdio uses `command`, `args`, `env` and `cwd`. Its server names normalize hyphens and underscores, and env values support interpolation and shell commands. These details require guarded conversion rather than copying an arbitrary client configuration. Python's [tomllib](https://docs.python.org/3.11/library/tomllib.html) provides the parser; Python3.11 or newer is required, without automatic dependency installation.

## Explicit migration

Choose the existing memory entry and the exact source file:

```sh
python3.11 packages/core/setup/pi_mcp.py \
  --codex-config /HOME/.codex/config.toml \
  --source-server engineering-memory --plan
python3.11 packages/core/setup/pi_mcp.py \
  --codex-config /HOME/.codex/config.toml \
  --source-server engineering-memory
```

`--home` and `--agent-dir` select an explicit operator/test home and personal pi directory. Only `engineering-memory` or `engineering_memory` may be selected. The target name is `engineering_memory`. No source entry means DEFERRED with no write; it never creates a new memory service. This does not copy Keenable, HTTP headers, other Codex servers, credentials into project files, tunnels or memory policies. Migration itself performs no server execution, network connection, model request or deployment.

Only an already configured trusted absolute regular executable and literal stdio fields are reused. Shell/package-manager launchers, inline interpreter execution, HTTP/mixed transports, unknown execution/access restrictions, relative cwd and dynamic pi env syntax (`${...}` or `!command`) are rejected for operator review. This migration is not a sandbox or an audit of the selected program. Existing local wrappers remain local; executable bytes are not copied.

## Ownership and recovery

The adapter changes one personal pi entry, preserving unrelated entries and JSON fields. A different unowned entry or a normalized-name collision is CONFLICT; an identical unowned entry is ALREADY_CONFIGURED without adoption. The private hash-only receipt verifies the previously owned entry before update; user edits stop before replacement. Source values are not included in CLI output or receipts. The personal MCP config and private exact backups are0600; metadata directory is0700.

Plan reads source/target/ownership metadata but writes nothing and starts no process. Actual conversion uses a private backup and pending intent before atomic replacement. Unknown/interrupted outcomes block replay with `recovery_required`; ordinary failures restore only exact installer-owned target bytes, preserving concurrent user changes. No force overwrite or automatic removal is available.

## Verify separately

Start a fresh pi session or `/reload`. Native tools use the `mcp__engineering_memory__...` prefix. A separate explicitly authorized `pi mcp list` checks configured connections and tool-list metadata; it does not invoke memory tools or models. It connects every enabled pi server, so review existing target entries before running it. A migration status is not proof of connectivity, native tool discovery, data access or cross-project recall quality.
