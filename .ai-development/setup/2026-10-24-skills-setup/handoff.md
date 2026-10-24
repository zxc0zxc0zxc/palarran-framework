# Skills setup handoff

Decision: [single-entry/0001](decisions/0001-single-entry.md). Implemented docs first, then skills-setup, namespace adapter/plugin, discovery, setup dispatcher and portable package resources. Catalog:35skills/15namespaces. Client inherited on update; partial/corrupt/pending/conflicting state never falls back to install. Preserved settings and independent local changes; health uses pinned public code and explicit global scope. Native calls and plugin aliases distinguished in usage.

## Verification

Frozen staged source tree `eeaad758f62bb2d328a1009be057fc491c9d513f` (before this final handoff): validator PASS,536Markdown/35skills; complete offline suite491tests in320.066s,470PASS,21optional real-tokenizer tests NOT_RUN because the prior temporary tokenizer environment is absent. All9new setup tests PASS, existing22update tests and portable packaging PASS. No failed tests, no paid/model launches. Existing unpublished ML/SFT changes excluded from subject/commit.

Factory acceptance PASS:100samples, control-plane p951.196ms, smoke0.417s. Live providers/operational SLA NOT_RUN. Root working validator also PASS584Markdown/35skills (includes unrelated unpublished docs). Optional skill-creator quick_validate NOT_RUN: PyYAML unavailable; repository frontmatter/discovery/docs checks PASS; no dependency installed.

Real authenticated global-memory wire from temporary projects PASS: fresh INSTALLED → oldpublic34skill install updated to35skills → UNCHANGED repeat. AGENTS/CLAUDE/.mcp.json/.env and independent local documentation edit preserved. Six MCP tools, readonly initialize/list/search, zero model calls or service writes. Host UI discovery NOT_VERIFIED; no global MCP/tunnel/policy changes or application deployment.

Private full suite evidence SHA256 `b869d4b659549e91717411463ebdab87c2f3e5cbbc2ca9631605705587a650c6`; sanitized live proof SHA256 `55c7d81b5960899a56ae3eb70b8bff2b6a94dc6d1f5bac0a42ccf920a73bb530`. Private evidence remains outside Git under owner memory-evidence/skills-setup. The first interrupted run lost its temporary final log and is not counted as PASS; the complete repeated run above is authoritative.

## Memory and use

Recall APPLIED:921cacabd6a45f0e9fb9f874a4c639474482ab6b25886e097ad56b54e0bd74e2 (explicit global credential scope). Revalidated against code and actual wire. Learn SKIPPED: no distinct portable lesson to duplicate. Decisions/verified limits remain here.

Use `/skills:setup` with plugin/adapters, Codex `$skills-setup`, standalone Claude `/skills-setup`; `--plan` offline/read-only. Updated source comes from trusted pinned full checkout/snapshot, never custom installed overlay. Conflict/recovery: review exact diff/backup, no force/reinstall. Missing memory: retain completed file changes, report NOT_READY and retry readonly doctor. Publishing does not install into existing user applications automatically.
