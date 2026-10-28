# Existing project test suites

This optional adapter covers local server, worker and bot tests when the web CLI's HTTP/SQLite/Playwright shape does not apply. It runs reviewed project commands and links their results to requirement IDs. It does not replace browser/API/DB evidence or certify the test's business predicates. Primary basis, read2026-10-28: [Google review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [focused testing guidance](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) (published2015-04-22), and the [Git diff manual](https://git-scm.com/docs/git-diff). Documentation preceded this adapter's implementation.

## Frozen binding

Use `packages.validation.application.project_tests.run_project_tests(*, target, revision, cases, bindings, authorized=False, run_seconds=60)`. The target must be an existing clean Git worktree at the exact full commit. System path aliases are canonicalized only through Core's reviewed local-I/O policy; arbitrary symlink targets/cwd/executables are rejected.

Cases: `{id, requirements, binding, kind}`. IDs are bounded ASCII identifiers, requirements are nonempty distinct `R1`-style IDs, and `kind` is `fixture` or `project_test`. Bindings are trusted operator-owned Python dictionaries with exactly `{argv, cwd, environment, seconds, max_output_bytes}`. `argv` is a nonempty string list with an existing absolute executable, never a shell command string. `cwd` is an existing canonical directory within target. Environment is explicit and is not inherited from the launching chat. Test executables and every argument still need human/trusted-agent review: an argv list is not a security sandbox and cannot prove that a test will not call a paid provider. Use fake providers/disposable data where the real dependency is outside the authorized scope.

All cases/bindings validate before any command runs. Up to50cases,20requirements per case,64arguments per binding,16KiB argument text,128environment entries,1MiB output per case, and a total run bound of600seconds. Each command is bounded by its own limit and the remaining run time. Initial/final Git verification has its own bounded5second operations; this is not a hard real-time OS sandbox. No retries, package installation, browser downloads or hidden provider/model calls.

The existing orchestration subprocess transport drains output to a digest, bounds bytes/time and checks process-group termination. Neither raw output nor command/environment values are put in the report. Group absence does not control a process that deliberately escapes or remote effects; unknown termination stays INCONCLUSIVE and needs reconciliation. A timeout/output limit is not a negative business assertion.

## Statuses and scope

Each case returns `PASS`, `FAIL`, `INCONCLUSIVE` or `NOT_RUN`, its requirement IDs/kind, binding ID and opaque reviewed-definition/output SHA256, byte/time counters, stop evidence and a safe reason code. Exit0 with complete transport/stop evidence gives test PASS. A normal nonzero test exit is FAIL. Timeout, missing stop evidence, source drift or an interrupted/unsupported execution is INCONCLUSIVE; unexecuted later cases stay NOT_RUN.

The aggregate is `CHECKS_PASSED`, `FAIL` or `INCONCLUSIVE`. **`acceptance` remains `NOT_RUN`**, and browser/API/DB remain NOT_RUN. A fixture PASS and an existing project-test PASS retain their different `kind`; neither becomes live-provider, deployment or full application acceptance. Reports record `model_calls: 0` for the adapter itself, `provider_cost: null`; they do not claim that arbitrary operator commands are free. Exact clean Git source is checked again after execution. Any changed source invalidates the aggregate even when commands exited successfully.

## CLI and main-agent use

`python3 -m packages.validation.application.project_tests --plan` performs no target input reads, binding imports, writes or launches. Actual execution requires `--target /ABSOLUTE/project --revision FULL_COMMIT --binding reviewed_module:factory --authorized`. After exact clean-source preflight, the explicit trusted factory returns `{cases, bindings, run_seconds}`. Importing it executes operator code; never select a module from a model-generated suite or download it automatically. Run from the trusted library root with a reviewed Python import path. CLI emits structured JSON, no files; redirect only into an already ignored private target journal or use the Python API and the project's existing evidence writer.

For example, an existing fake-provider Go test can be bound to an R-ID after the command and test scope are approved. The adapter only records its exit/transport evidence. A reviewer still verifies that its assertions cover the specified failure and binds the report's digest to the actual test source and result. No direct production Postgres or paid model adapter is implied.

## Good small server-side pass

An approved fake-provider test for `R7` covers two turns: a provider failure followed by a normal reply. The reviewer checks that a replacement code is not lost or delivered on an unrelated turn. Bind only that existing test command, run it against the reviewed clean commit, and retain its output hash/result. A failing assertion is a test FAIL; fixing or calling the real provider is separate scope. The final summary explains what the fake proves and which live integration remains untested.

A trusted Python factory can return this inert shape after replacing every placeholder and approving the command:

```python
def factory():
    return {
        'run_seconds': 30,
        'cases': [{'id': 'CASE_DELIVERY', 'requirements': ['R7'],
                   'binding': 'delivery-test', 'kind': 'fixture'}],
        'bindings': {'delivery-test': {
            'argv': ['/ABSOLUTE/go', 'test', './internal/conversation',
                     '-run', '^TestDeliveryFailure$', '-count=1'],
            'cwd': '/ABSOLUTE/reviewed-project',
            'environment': {'PATH': '/usr/bin:/bin', 'GOPROXY': 'off',
                            'GOCACHE': '/PRIVATE/existing-go-cache'},
            'seconds': 20, 'max_output_bytes': 65536}}
    }
```

The example is not auto-discovered or executed. The named test/cache may not exist; the operator supplies an actual existing executable, cache and fake-provider test. No dependency download or cache creation is performed by the adapter.

The definition digest binds the reviewed command values, not the executable or complete transitive toolchain bytes. Preserve actual tool/runtime versions in the surrounding review when reproducibility needs them. Unexpected trusted-binding errors receive a safe CLI fallback without raw exception values or traceback; this does not make arbitrary binding code safe to import.

The CLI discards synchronous stdout/stderr while importing and evaluating the reviewed binding, including ordinary logging and writes to file descriptors1/2. Output goes directly to the null sink, never an unbounded in-memory capture. This single-threaded CLI boundary restores its streams before the structured result; it is not a sandbox for untrusted code, background threads, later exit hooks, files or remote effects. Bindings must only return the reviewed local definitions without starting background work. Test subprocess output uses the existing bounded runner.
