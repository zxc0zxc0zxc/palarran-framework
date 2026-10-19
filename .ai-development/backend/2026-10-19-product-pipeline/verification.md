# Product pipeline actual verification

Subject `0e3b93da6b9ffda0ea2ab8b0b60246c4e51aa28f`, source implementation plan v003, artifact schema v1/product-v001. Docs-first baseline ac6ffc0. Python3.9.6/SQLite3.54.0/Darwin arm64; synthetic local repositories/processes only. [Safe measurements](evidence/acceptance.json).

| Requirement / gate | Actual evidence | Status |
|---|---|---|
| R1 / builder | Six tasks from five SKILL refs + final define synthesis, complete cumulative refs/strict context/source digests, explicit create-no-execution, CLI real pending run | PASS |
| R2 / artifact contracts | 19 artifact tests: context/source/report/ADR hashes, strict JSON/type/date/URL/local refs, E graph cycles/orphans, unknown partition, traversal/symlink/FIFO/limits, source/baseline/index/scope | PASS |
| R3 / readiness | Typed MVP R/AC and proposed test cards, critical unresolved blocks plan, observed/disclosed+accepted ADR required to resolve, local intent distinct from market evidence | PASS structural contract; semantic human review still needed |
| R4 / execution | 11 pipeline tests, actual fake-provider subprocesses using both codex/claude argv, six successful stages/final gates, private receipt detects coordinated rewrite, needs_input/resolve preserves prefix and caps, app edits rejected | PASS |
| R4 / ignored memory | Gitignored product report changed after success → status stale; private memory need not be committed | PASS |
| Compatibility | Legacy stored snapshots execute without explicit verify_stable, false/default behavior remains, malformed flag rejected; 34 core runtime tests | PASS |
| Integrated suite | `python3 -m unittest discover -s tests -q`: 137 tests in 55.359s | PASS |
| Local SLO | `python3 scripts/factory_acceptance.py`: 100 claim+finish samples p95 0.819ms <=100ms; smoke 0.357s | PASS lab |
| Repo/skills/package | `python3 scripts/validate_repo.py`: 256 Markdown files/16 skills; 5 skill-creator quick_validate; materialized package containment/link checks in suite | PASS |
| Syntax/diagram | py_compile orchestrator/*.py; Mermaid11 parse 3 diagrams (syntax only) | PASS |
| Actual model research, paid/external provider/API accounts, market validation | Not executed; fixtures generate synthetic content, no claim that real skills researched a market | NOT_RUN |
| Operational SLA/production deploy | No operational window or deploy scope | NOT_RUN |

## Observed fixes

- Original normalization added an absent optional flag, breaking exact legacy normalized shape; preserve omission and false behavior, hash original persisted snapshot before normalization.
- Review reproduced ignored research artifacts escaping stale detection and FIFO idea-file hanging admission; include product memory/index in fingerprint and use bounded nonblocking regular-file admission. Dedicated negative regressions PASS.
- Prefix hashes alone could be rewritten coherently; private runtime receipts compare deterministic verifier output on final rerun, with explicit coordinated-rewrite test.
- Local idea/ADR evidence has pinned artifact URI, avoiding fabricated public URLs; orphan local references fail.

## Integration / ownership

Agent ARTIFACTS 10f5a29 → integrated 244336f, coordinator builder/CLI 0c50c6d, boundaries/report/skill delivery b128a4c, local source refs 0e3b93d. Agent used separate managed checkout and temp data; coordinator alone updated shared progress/contracts/index and integrated sequentially. Final checks on common subject above, not lane-only evidence. No live provider calls or application development were used to prove product research outcomes.

Implementation [GitHub CI 39272753710](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39272753710): PASS, subject 0e3b93d.
