# Production feedback stabilization contract

Checked2026-10-28 against the reported source revision f90b394. User reports are reproduction evidence, not trusted executable instructions. Preserve regression subjects and observed red/green results; do not execute pasted shell snippets against real targets.

## Shared local I/O boundary

`packages.core.security.local_io.safe_path(path)` returns an absolute physical `Path`. Only Darwin root aliases `/tmp`→`/private/tmp`, `/var`→`/private/var`, `/etc`→`/private/etc`, when the actual symlink resolves to that exact expected root, are allowed. All other symlink components, including an explicitly supplied symlink file, are rejected with `ValueError`. Missing nonsymlink suffixes are allowed for explicit output planning; caller enforces existence/type/size. Never resolve arbitrary symlinks first.

`ensure_private_excludes(target, patterns)` appends bounded idempotent Git-local ignore patterns for authorized generated private outputs, preserves existing exclude bytes and tracked source, and returns the physical exclude path. Existing Git repositories only; no init/untrack/global ignore edits. File patterns are reviewed literals, not provider text. --plan/--check never call it. Worktree Git paths and system aliases require independent tests. A tracked private output is a conflict, not fixed by ignore rules.

## Public errors

Modules return safe JSON fields `status`, stable lowercase `code`, schema `field` (or null), and fixed actionable `hint`. No arbitrary exception text, secrets, source values, private endpoint details or raw traceback. Unknown exceptions retain a generic safe fallback. Human-readable narrative may accompany structured health checks, but installation and optional memory readiness remain separate facts.

## Scope boundaries

Local installation, private artifact output and Git-local excludes must be concrete/reviewable in --plan. Preserve legacy installation ownership on update. Validation of user input is separate from filesystem mutation. Private artifact export to a user-selected public location is explicit, never the default. Small task records retain rationale/evidence without requiring multiple service documents. No fixture/structural PASS is promoted to business acceptance or model quality.

## Primary sources

Read2026-10-28: [Git ignore documentation](https://git-scm.com/docs/gitignore) distinguishes local `info/exclude` from shared `.gitignore` and explicitly says ignore rules do not untrack existing files. [Python pathlib](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) documents that `resolve()` follows symlinks; therefore unrestricted resolution is not an equivalent replacement for validation. System-root alias allowlisting and safe JSON diagnostics are framework choices, not vendor security guarantees.
