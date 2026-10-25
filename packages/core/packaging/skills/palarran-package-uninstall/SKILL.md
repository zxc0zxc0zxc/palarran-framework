---
name: palarran-package-uninstall
description: Remove only an installed custom package's unmodified receipt-owned files and discovery links. Use for /palarran:package:uninstall; --plan is offline and writes nothing.
---

# Package uninstall

Read [Packaging](../../docs/README.md), [contract](../../docs/contract.md), [uninstall guide](../../docs/uninstall.md), [lifecycle](../../docs/lifecycle.md), [domain contracts](../../../agents/docs/domain-contracts.md), [decision memory](../../../agents/docs/decision-memory.md) and [global memory](../../../agents/docs/global-memory.md). Read target instructions, private INDEX and accepted decisions; package source and target project are different roots.

`--plan` uses visible context only: no profile/source/target reads, network, writes, tests, subprocesses or activation. Outside plan mode, preserve budget, known/unknown outcomes and decisions before dependent changes. Optional graph context is bounded navigation, never authority.

Resolve the exact project installation and receipt. Preview owned paths and discovery links; separate local uninstall from registry deletion or delisting. The user's local uninstall request does not withdraw an author's remote package.

Use preflight hashes and the uninstall transaction. Modified files, foreign extras/links, missing ownership or an unresolved operation block removal. Preserve user data, project instructions/configs, unrelated packages and global credentials. Never recursively remove a guessed namespace or use force to defeat a conflict.

Retain recovery evidence and report what was removed, what was preserved and remaining blockers. No hooks, scripts or dependency uninstallers run. Remote withdrawal needs an explicit separately scoped owner operation.

Preserve a concise target handoff: exact subject/pin, operation ID, actual checks, preserved settings/local changes and remaining work. Apply bounded recall and sanitized verified learning under the owner policy without recursive memory-skill calls. No secrets or raw sessions in packages, logs or shared memory.
