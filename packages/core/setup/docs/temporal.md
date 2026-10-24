# Optional Temporal setup and harness compatibility

Contract version: 0.3. Sources checked **2026-10-24**. Before dependent writes, record the user's choice and exact runbook/source revision in the private project journal. Ask once: **Enable the Temporal engine for parallel execution?** Inherit an existing explicit project/global answer on update. Absence of an answer is not consent to change global settings.

## Profile selection

The project `.env` overrides global `~/.palarran/.env`. An absent project switch inherits the global switch; only literal `0` and `1` are accepted. Project `TEMPORAL_ENABLED=0` disables Temporal. A project connection field selects the entire project connection profile: require address and namespace together, never borrow global credentials or TLS settings. Project switch `1` alone may inherit a complete global connection. No connection configured means local execution. Enabled but incomplete configuration is an error, not a local fallback.

Connection fields: `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TLS` (`0` or `1`), `TEMPORAL_API_KEY_FILE`, `TEMPORAL_TLS_CERT_FILE`, `TEMPORAL_TLS_KEY_FILE`, `TEMPORAL_TLS_CA_FILE`. Authentication material uses absolute owner-only regular files without symlinks. Certificate and key are paired; API-key or client-certificate authentication requires TLS. Plaintext is limited to loopback through an already-authorized protected transport. Reports contain selected scope and status, never profile contents or credential paths.

[Temporal's Python client](https://docs.temporal.io/develop/python/client/temporal-client) supports namespace and TLS connection options. Atomic profile selection and stricter secret-file checks here are Palarran policy. `temporal_config.py` validates local files; injected transport probes must perform actual service and namespace checks before doctor reports CONNECTED. A TCP socket check is insufficient. Optional SDK absence, unauthorized probes and missing adapter support remain explicit NOT_RUN/UNSUPPORTED states. Doctor starts no model, Worker, server or tunnel.

## Install and update

The agent first resolves packages/languages, then asks the question above if no prior answer exists. Save a global choice only with actual authorization to modify the global profile; project setup alone never grants this. `write_choice` updates only the switch in the explicitly chosen private env file with expected-content comparison and atomic replacement, preserving other lines. It cannot accept credential values. Setting `1` must be followed by resolving and checking the complete profile; saving a choice alone is not a connection claim.

Configure the local Worker using the reviewed orchestration Worker entrypoint and its runtime dependencies. An unavailable SDK/unsupported version blocks Worker readiness; do not install dependencies, start background services or alter client settings as a side effect of project installation. Show separately: selected backend, service compatibility/connectivity, Worker NOT_STARTED/actual health, harness integration level. Normal setup installs shared entry instructions for ordinary requests and every skill; choosing a subject package cannot bypass them.

## Actual control levels

| Integration | Level | Basis |
| --- | --- | --- |
| Native Codex / Claude desktop instruction block | instruction-based | No verified per-message interception or full descendant control |
| Reviewed managed entry with Dispatcher and controlled callback adapter | enforced | Only its registered API calls and accounted descendants are in scope |
| Exact-argv headless subprocess without an external descendant supervisor | instruction-based | Timeout/usage/cancellation are bounded; arbitrary nested subprocesses are not contained |
| Unknown host, absent adapter or unsupported protocol version | unsupported | Never infer integration from an AGENTS file |

Supported managed protocol is `palarran.managed.v1`, Python 3.9+ on POSIX (Temporal SDK uses its separately pinned supported Python runtime). Headless child framing is one bounded JSON result on stdout; raw stderr is discarded. Native client version compatibility is NOT_VERIFIED until separately tested on that exact host/version. [Python subprocess](https://docs.python.org/3/library/subprocess.html) documents shell-free argv, explicit environment and timeout semantics; these do not promise a security sandbox.

## Verification and recovery

Offline tests cover scope inheritance, explicit disable, malformed switches, incomplete/mixed credentials, secret permissions, connection-probe failure, ordinary and skill entry, continuation identity, denied argv, bounded output, cancellation and unknown spend. No paid or network calls are needed. A failed Temporal probe never switches the run to local. An active run keeps its backend even after config changes; inspect/reconcile it before any retry or reassignment. A completed child process is submitted, not independently verified.

Local metadata observation, 2026-10-24: `codex --version` returned **codex-cli 0.163.0**, `claude --version` returned **2.1.286 (Claude Code)**. These version-only calls made no model requests; they do not establish a paid end-to-end adapter test. [Official OpenAI documentation](https://developers.openai.com/blog/codex-as-a-platform) distinguishes noninteractive `codex exec`, SDK and app-server integrations. This change uses the reviewed generic managed protocol; it does not silently reinterpret Codex JSONL as that protocol or claim native app interception. OpenAI Docs skill was used for this narrow compatibility/source check.

Read-only CLI entry: `python3 scripts/project_setup.py temporal-doctor --target /ABSOLUTE/project` resolves local configuration and reports NOT_RUN without network. Add `--check-temporal` only within an actual authorized connection-check scope: the pinned SDK adapter checks service health, exact supported versions and namespace. Missing optional dependencies produce NOT_READY, never simulated PASS. `--plan` performs no probe or writes. The normal memory doctor can include the same check explicitly with `--check-temporal`.
