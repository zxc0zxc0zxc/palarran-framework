# PF v001: actual acceptance

Subject commit `e0b526cb73d48aafaf46f9eb9afbeeb2a93462e3`. Date 2026-10-19. Synthetic disposable local targets; no cloud, SSH, deployment or provider calls. Python 3.9.6, SQLite 3.54.0, Darwin arm64. [Измерения](evidence/acceptance.json).

| Gate | Actual result / command | Verdict |
|---|---|---|
| Strict v1 admission | 35 independent methods, nested/type/NaN/huge-int/DAG/allowlist cases | PASS |
| Process runner / adapter argv | 14 tests, real stdin/env/exit/flood/timeout/descendant/fencing; CLI builders compared with installed help | PASS |
| Core / Git / SQLite / CLI | 31 tests: real file readback, target isolation, 16 claim attempts/8 threads, stale finish, immutable snapshot, real worker kill with orphan, deadline, reconcile cap, final regression, fingerprint framing, AI control-file fixture/pause/resume | PASS |
| Full existing + new offline suite | `python3 -m unittest discover -s tests -q`: 104 tests, 13.721s | PASS |
| Repository contracts | `python3 scripts/validate_repo.py`: 200 Markdown files, 11 skills/adapters | PASS |
| Python syntax | `python3 -m py_compile orchestrator/*.py scripts/factory_acceptance.py` | PASS |
| Lab smoke/SLO | `python3 scripts/factory_acceptance.py`: actual worktree write/read, final checks; 100 claim+finish pairs p95 0.726ms <=100ms; smoke 0.295s | PASS |
| Diagram syntax | Mermaid 11 parse via local jsdom; no visual render claim | PASS |
| Live Codex/Claude account integration | Not called; fixture tests are not provider evidence | NOT_RUN |
| 30-day operational SLA, host/disk loss, multi-host | No operational environment/window; outside lab DoD | NOT_RUN |

Acceptance is local implementation verification. No exactly-once side effects, security sandbox, enforced monetary cap, product-market validation or deployment claim. Unknown outcome requires stopped-process reconciliation. Fingerprint excludes ignored files and caps 10k files/100MiB; these files/external data are outside acceptance identity.

## Review and corrections

Independent agent found unframed content ambiguity in fingerprint, malformed huge-int OverflowError and pause bypassing run deadline. Each corrected before acceptance with a dedicated regression test. An initial documentation link depth and canonical-temp-path test expectation were also corrected. Failures were not accepted as PASS; final suite ran on integrated subject above.

## Integration

Docs/contracts frozen at 81c135d before implementation. RUNNER agent commit d177025 → integrated 2b2ca37; CONTRACT-TEST agent 9327a5e → aec8004; coordinator core 1a0df1c plus final protocol/tests e0b526c. Separate managed worktrees and temp resources, sequential cherry-picks, then full integrated acceptance. Only coordinator changed shared progress/index/contracts. No runtime task parallelism claim: v001 serializes one run workspace.

CI implementation run: [GitHub Actions](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39190418028). Final conclusion recorded in handoff after live check.
