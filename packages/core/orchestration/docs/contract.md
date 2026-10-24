# Workflow v1 and module contract

ML pipeline adds optional `ml_policy` ([ML contract](../../../machine-learning/experiments/docs/pipeline-contract.md)): shared USD ceiling, resource allocations, private approvals and usage rows. Without it generic/product workflows keep their previous contract. Additional SQLite tables `ml_resource_attempts`, `ml_approvals`, `ml_resource_reconciliations`, `ml_modal_jobs`, `ml_modal_metrics` are additive without changing existing tables/receipts. Existing database version 2 stays readable.

Workflow is a JSON object with listed fields only; unknown fields forbidden. All IDs unique `[A-Za-z0-9_-]{1,64}`. Optional `usage_policy` follows the [usage accounting contract](usage-accounting.md): durable attempt ledger/schema v2, stdout usage callbacks, stage/run token/USD guards and explicit unknown reconciliation. Optional `ai_policy` and task `model_role`/`model_calls` follow [model budgets](model-budgets.md); absent policy preserves legacy behavior. Required `version:1`, `name`, `plan_revision`, `tasks`, `limits`, `policy`. Task count 1..100; DAG without cycles/unknown/duplicate dependencies. All numeric values finite/positive; bool is not number.

`limits`: `run_seconds` (<=86400), `task_seconds` (<=3600), `lease_seconds` (>=3, <=300), `max_attempts` (1..10), `output_bytes` (1024..10485760). Run limit includes waiting/idling after create. Runtime guarantees no CPU/memory/network/financial limits. If hard financial caps are unavailable, use separately limited provider accounts; never equate wall time with cost.

`policy`: `executables` nonempty absolute executable paths; `adapters` subset `command,codex,claude`; `env` explicitly inherited environment-variable names. No shell expansion. `PATH`, `HOME`, auth/tool caches are not inherited automatically; operators explicitly permit them, understanding subprocess access. Allowlist controls the first process, not a sandbox for child commands, Git hooks, project config, MCP or network. Trusted targets/workflows only. No automatic deployment step/SSH mode.

Task: `id`, `depends_on` (list, default []), `adapter` (default `command`), `argv` (command), `prompt` (AI), `executable` (AI, absolute CLI path), `verify` (nonempty list of argv arrays), `replay_safe` (bool, default false), `verify_stable` (bool, default false). Stable verifiers must print deterministic output: each successful task-verifier private receipt digest is compared with final rerun; changes reject completion. Default false preserves tests printing timestamps/durations. No secrets in workflow/prompt/argv. Prompts must reference absolute `SKILL.md`, mandatory docs, target plan revision/DoD and target decision-memory, and instruct stopping with exit failure for unresolved questions. AI receives prompts through stdin, not shell. Runtime appends mandatory protocol: create `.palarran/factory/<run>/<task>/attempt-N/handoff.json` containing only `status`: `implemented` or `needs_input`. Exit 0 without valid handoff is not success; implemented merely permits independent checks. needs_input stops the run. Never parse model prose as consent/verification. Resolve passes safe operator context; new attempts spend allocation. Handoff v1, <=1024 bytes, no symlinks.

Run/task state: `pending → running → verified`; observed completed-process failures retry as `pending` only when replay-safe with remaining attempts, otherwise `failed`; unknown lease outcome → `needs_input`. Budget stop → `failed`. `cancelled` is terminal; cancellation does not prove absence of prior side effects. Final checks use synthetic internal task `__final__`. `resolve` is allowed only for needs_input after manually stopping old worker/process tree, with safe reason and `--processes-stopped`; it returns to pending preserving attempt caps. No automatic consent.

## Frozen Python interfaces for v001

`orchestrator.runner` (lane RUNNER):

```python
@dataclass(frozen=True)
class Result:
    returncode: int
    reason: str  # exited / timeout / output_limit / lease_lost / spawn_error
    output_sha256: str
    output_bytes: int
    seconds: float
    usage_complete: Optional[bool] = None
    diagnostics: Optional[dict] = None  # enum-only CLI observations
    stopped: Optional[bool] = None  # additive: actual process-group absence proof

def execute(argv, cwd, *, timeout, output_limit, env, heartbeat, stdin_text="",
            usage_adapter=None, on_usage=None) -> Result:
    # heartbeat() -> bool; call at least every 0.2s, False kills process group
    # shell=False; no raw output persisted/printed; env exact supplied mapping
    ...

def invocation(task, workspace, *, profile=None, telemetry=False, max_cost_usd=None):
    # returns (argv: list[str], stdin_text: str)
    # command passes argv; codex/claude explicit noninteractive argv, no bypass
    ...
```

Coordinator owns `spec.py` (`validate(dict)->dict` returns normalized deep copy), `store.py` (`Store(path)`, run/task durable state), `engine.py` (`create(state, workflow, target)->run_id`, `work(state, run_id)->status`, `status(state, run_id)->dict`), CLI `python3 -m orchestrator`. Independent tests lane owns only `tests/test_factory_contract.py`; core owns other tests. CLI detailed options: [operations](operations.md).

Optional Codex task `transport:"app-server"` requires usage_policy/model profile. Trusted Python bridge executable must also be allowlisted; server descendants stay in the supervised process group. Missing transport preserves legacy behavior. Optional usage-policy `carry` is in usage-accounting.md; workflow-digest pinning remains. Continuation adds command-only import/packet gates consuming no model launches; original skill context/prefix remains.

## Runtime context

Optional task.context/automatic scoped AGENTS/Graphify delivery follows [runtime-context](runtime-context.md). Model/usage policies, handoff and independent final gates remain unchanged. Private context bindings/receipts are additive.

Canonical decision section headings are English. Artifact verification also recognizes the documented Russian and Serbian Latin section aliases for existing/localized target journals; all six semantic sections remain required, not arbitrary headings.
