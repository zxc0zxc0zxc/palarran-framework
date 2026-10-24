# Canonical source-path resolution

This is the local compatibility contract for the physical package layout, Feature PAL-20261024-A7F2C1. It describes lookup; files now live at canonical capability paths. The explicit move manifest and compatible entrypoints preserve legacy consumers without activating packages or services.

## Manifest and selection

`source_path(root, legacy_relative, *, required=False)` in [palarran_paths.py](../../../../scripts/palarran_paths.py) returns an absolute `Path`. The existing root must be a directory without symlink components. The reference is a nonempty relative POSIX string: no absolute paths, URI schemes, backslashes, empty segments, `.` or `..`, control characters or invalid Unicode.

The optional `packages/layout.json` is a UTF-8 regular JSON file of at most 64 KiB, with exactly this schema:

```json
{"version":1,"moves":{"docs/example":"packages/example/docs","scripts/example.py":"packages/example/scripts/example.py"}}
```

These are illustrative prefixes, not installed resources. `version` is integer 1, not a boolean. `moves` maps strict relative POSIX prefixes to strict relative POSIX prefixes; an empty mapping is allowed. Duplicate keys at any level, unknown fields, nonfinite values, invalid types and malformed/oversized input reject the manifest. Invalid unrelated entries also reject lookup rather than silently weakening it.

Choose the longest source prefix that equals the requested reference or ends at a path-segment boundary before its suffix. Rebase that suffix onto the selected canonical prefix once. For example, `docs/example/x.md` maps to `packages/example/docs/x.md`, while `docs/examples/x.md` does not match `docs/example`. Exact-file mappings and directory-prefix mappings are both supported; there is no recursive alias expansion or arbitrary filesystem search.

## Missing paths and containment

If the manifest is absent, return the strict legacy root-relative path, preserving older fixture libraries. If a valid manifest has no matching prefix, retain that same strict root-relative path. If a prefix matches but its canonical destination is missing, return the canonical missing path with `required=False`; **never fall back to an existing legacy file**. With `required=True`, the selected final path must exist or lookup raises `FileNotFoundError`.

All configured canonical prefixes and the final selected path must stay inside the supplied root. Reject existing symlink components, including dangling links and links pointing back inside the root; reject non-directory intermediate components and existing nonregular/non-directory targets. These checks also apply to the manifest path. Targets may be files or directories; callers impose any narrower type requirement themselves. Existing package prefixes need not all exist during a staged migration.

Only the bounded layout manifest is read. Source-file contents are never opened and nothing is executed, downloaded, installed or queried over a network. Resolution does not grant source permissions, guarantee a complete package, establish source freshness or protect a later caller against concurrent filesystem replacement. Callers retain their existing secure reads, digest checks and execution gates.

## Per-operation batches

`source_resolver(root)` validates one bounded manifest and returns a resolver with the same path/required checks. Use it only for a single bounded operation such as hashing a source set; selected paths are checked on every call. Do not retain it across tasks or treat it as filesystem freshness evidence. A new resolver reloads the map. The single-path `source_path` API remains unchanged.

## Acceptance

Offline temporary fixtures cover legacy compatibility, exact/longest prefix and segment boundaries, one-step rebasing, mapped-missing behavior without fallback, required existence, malformed/duplicate/schema/size rejection, and root/manifest/mapped-target symlink escapes. The focused command is `python3 -m unittest tests.test_palarran_paths -v`. Structural repository validation is separate from physical-migration and caller-integration acceptance; this helper alone proves neither.
