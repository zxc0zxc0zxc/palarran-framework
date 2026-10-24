# setup-update-v001: verified delivery

## Final behavior

Explicit update/rollback entrypoints inherit installed Codex/Claude scope. Three-way hashes preserve independent edits/deletions/extras/directories/modes. Overlapping edits, removal of locally customized resources/skills, unowned path collisions, modified discovery links and unsafe manifests/paths stop before replacement. AGENTS/CLAUDE/.env/.mcp.json/app code/Git index untouched; custom USAGE preserved. Installed helper is self-contained and disables bytecode writes into its managed bundle.

Candidate/original backup, cached pristine public release, fsynced pending intent and nonblocking single-project Unix lock. v1 installation migrates to v2 with upstream baselines and override metadata. Health executes only pristine pinned public code with exact file-set/hash validation; no user hooks/merge drivers/carried code/custom MCP launcher. Global env/user MCP/SSH/policy unchanged. Global connectivity is separate from customized project integration/client UI (NOT_VERIFIED). Memory outage keeps completed update with NOT_READY/exit2; same-version retry only repeats readonly health.

I/O error attempts guarded rollback; interruption blocks replay until explicit recovery. Restore refuses newer user changes and checks complete expected trees/metadata/links before writes. Completed backup can be explicitly rolled back. Explicit successful rollback exits0; failed update with successful automatic rollback still exits2 (CLI regression covered). Attempt ADR/history and private ignored backups retained. No automatic pruning/force reset or multi-file ACID/power-loss/zero-downtime guarantee; stop active clients for update.

## Verification

- Final exact implementation suite482 PASS (357.580s), including22 updater tests; original installer8 compatibility tests retained. Exact staged validator531 Markdown/34 skills PASS; working tree579 Markdown/34 skills PASS. Factory100 samples p95 0.948ms, smoke0.379s PASS. Live paid providers/operational SLA NOT_RUN.
- Actual temporary project upgraded from published127198e; authenticated global MCP initialize/list/search returned six tools. Settings/custom skill bytes, local library note, uncommitted app diff and Git index unchanged. Pristine release did not include project note. Installed doctor and repeated installed updater passed with no file changes.
- Committed source b78e7614504d4503e48fc581efbf0a1ee876751c verified: actual update, installed explicit rollback exit0, reapply and global memory PASS; settings/local override/app/index preserved throughout. Earlier explicit rollback exit classification defect fixed and included in regression.
- Existing global credential-scope lesson921cacabd6a45f0e9fb9f874a4c639474482ab6b25886e097ad56b54e0bd74e2 reused. Actual Codex MCP knowledge.feedback ACK85c5eac7d21df2ae2e816612ec35bdf62c28a59ecc3499974af8186fab87a23e records helped on verified commit; no duplicate/new case and no raw configs/backups uploaded.

## Scope and next context

No real application project upgraded implicitly; tests used temporary authorized fixtures. Global installed runtime/tunnel unchanged. No paid model/training calls. Parallel ML/SFT dirty work preserved and excluded from publication. Source commit remains in final history; final origin/main SHA is the publication receipt. Cache/backups cleanup requires reviewed owner scope.
