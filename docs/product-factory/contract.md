# Workflow v1 и контракт модулей

Workflow — JSON object, только перечисленные поля; неизвестные поля запрещены. Все IDs `[A-Za-z0-9_-]{1,64}`, уникальны. Optional `usage_policy` определён в [usage accounting contract](usage-accounting.md): durable attempt ledger/schema v2, stdout usage callbacks, stage/run token/USD guards и явная unknown reconciliation. Optional `ai_policy` и task `model_role`/`model_calls` определены в [model budget contract](model-budgets.md); отсутствие policy сохраняет legacy поведение. Нужны `version:1`, `name`, `plan_revision`, `tasks`, `limits`, `policy`. Task count 1..100; DAG без циклов/неизвестных/повторных dependencies. Все числовые значения конечны, положительны, bool не number.

`limits`: `run_seconds` (<=86400), `task_seconds` (<=3600), `lease_seconds` (>=3, <=300), `max_attempts` (1..10), `output_bytes` (1024..10485760). Лимит run включает ожидание и простои после create. CPU/memory/network и денежные лимиты этим runtime не гарантируются. При невозможности hard monetary cap запускать provider в отдельно ограниченном account; не выдавать wall time за стоимость.

`policy`: `executables` — непустой список абсолютных путей executable; `adapters` — subset `command,codex,claude`; `env` — список явно наследуемых имён environment variables. Без shell expansion. `PATH`, `HOME`, auth/tool caches не наследуются автоматически: оператор явно разрешает их, понимая доступ subprocess. Allowlist контролирует первый процесс; это не sandbox его дочерних команд, Git hooks, project config, MCP или сеть. Только доверенные target/workflow. Автоматического deploy шага или SSH режима нет.

Task: `id`, `depends_on` (list, default []), `adapter` (`command` default), `argv` (для command), `prompt` (для AI), `executable` (для AI, абсолютный CLI path), `verify` (непустой list argv arrays), `replay_safe` (bool, default false), `verify_stable` (bool, default false). Stable verifier обязан печатать deterministic output: private receipt digest каждого успешного task verifier сравнивается с финальным rerun; изменение отвергает completion. Default false сохраняет совместимость с тестами, печатающими timestamps/durations. Никаких secrets в workflow/prompt/argv. Prompt обязан ссылаться на абсолютный `SKILL.md`, обязательную документацию, target plan revision/DoD и target decision-memory, а также велеть остановиться с exit failure при unresolved question. Он передаётся AI через stdin, не shell. Runtime дописывает обязательный протокол: создать `.ai-development/factory/<run>/<task>/attempt-N/handoff.json` с единственным полем `status`: `implemented` либо `needs_input`. Exit 0 без valid handoff не означает успех; implemented только разрешает independent checks. needs_input останавливает run. Свободный текст модели не парсится как согласие/проверка. Resolve передаёт agent безопасный operator context; новый attempt тратит cap. Handoff version v1, максимум 1024 bytes, symlinks запрещены.

Run/task state: `pending → running → verified`; failure после завершённого процесса: `pending` retry при replay-safe и остатке attempts, иначе `failed`; unknown lease outcome → `needs_input`. Budget stop → `failed`. `cancelled` терминален; отмена не доказывает отсутствие уже выполненных side effects. Финальные checks — отдельный синтетический task `__final__` во внутреннем store. `resolve` допускается только needs_input после ручной остановки старого worker/process tree, с безопасным reason и флагом `--processes-stopped`; переводит в pending, сохраняя attempts cap. Нет автоматического согласия.

## Frozen Python interfaces для v001

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

Codex task optional `transport:"app-server"` требует usage_policy/model profile. Trusted Python bridge executable также обязан быть в executable allowlist; server descendant остаётся в supervised process group. Legacy transport без поля не меняется. Usage policy optional `carry` описан в usage-accounting.md; workflow digest pinning сохраняется. Continuation добавляет command-only import/packet gates, не расходующие model launches; source skill context/prefix сохраняются.
