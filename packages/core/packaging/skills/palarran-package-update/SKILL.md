---
name: palarran-package-update
description: Update an installed custom package using exact versions, receipts and local-edit preservation. Use for /palarran:package:update; --plan is offline and writes nothing.
---

# Package update

Read [Packaging](../../docs/README.md), [contract](../../docs/contract.md), [update guide](../../docs/update.md), [lifecycle](../../docs/lifecycle.md), [domain contracts](../../../agents/docs/domain-contracts.md), [decision memory](../../../agents/docs/decision-memory.md) and [global memory](../../../agents/docs/global-memory.md). Read target instructions, private INDEX and accepted decisions; package source and target project are different roots.

`--plan` uses visible context only: no profile/source/target reads, network, writes, tests, subprocesses or activation. Outside plan mode, preserve budget, known/unknown outcomes and decisions before dependent changes. Optional graph context is bounded navigation, never authority.

Read the installed receipt, source registry origin and current owned-file/link hashes. Compare old/local/new contents, capabilities, prerequisite changes and the exact replacement version/digest. Explain the scoped change before applying. A floating search result never silently becomes an update.

Use the installer update path only after full preflight. Local modifications, foreign extra files, changed discovery links or origin drift stop the entire operation; preserve them and present a concrete conflict. Do not force overwrite, regenerate missing ownership or broaden project/global permissions. Preserve settings and unrelated files.

Retain the durable transaction/backup and exact old/new pins. An interruption means recovery_required; use checked recovery, never blind replay. Report actual installed revision and missing discovery/memory/quality checks. Updates execute no package hooks or code.

Preserve a concise target handoff: exact subject/pin, operation ID, actual checks, preserved settings/local changes and remaining work. Apply bounded recall and sanitized verified learning under the owner policy without recursive memory-skill calls. No secrets or raw sessions in packages, logs or shared memory.
