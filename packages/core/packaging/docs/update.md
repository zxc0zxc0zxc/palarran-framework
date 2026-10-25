# Package update

Read [the architecture](README.md), [exact contract](contract.md) and [client lifecycle](lifecycle.md).

Read the installed receipt, source registry origin and current owned-file/link hashes. Compare old/local/new contents, capabilities, prerequisite changes and the exact replacement version/digest. Explain the scoped change before applying. A floating search result never silently becomes an update.

Use the installer update path only after full preflight. Local modifications, foreign extra files, changed discovery links or origin drift stop the entire operation; preserve them and present a concrete conflict. Do not force overwrite, regenerate missing ownership or broaden project/global permissions. Preserve settings and unrelated files.

Retain the durable transaction/backup and exact old/new pins. An interruption means recovery_required; use checked recovery, never blind replay. Report actual installed revision and missing discovery/memory/quality checks. Updates execute no package hooks or code.
