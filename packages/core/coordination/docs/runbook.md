# Coordination service installation runbook

Runbook ID: `palarran.coordination.install`; version: `1`. Supported target: an explicitly authorized, existing Ubuntu 22.04 Linux host with systemd, `/usr/bin/python3` (3.10), GCC, SSH and noninteractive sudo already available. This procedure installs only the standalone coordination service and a private SQLite 3.51.3 library. It does not install dependencies, skills or agent clients. Existing services, system libraries, SSH, firewall, public HTTP and global MCP configuration are outside its scope.

## Inputs and admission

An operator supplies an approved immutable full 40-character Git commit (`REV`), trusted local Git checkout (`CHECKOUT`), one safe project alias (`PROJECT`, 1–64 ASCII letters/digits/underscore/hyphen, starting with a letter), a locally obtained official SQLite amalgamation archive (`ARCHIVE`), a new absolute private packet directory (`PACKET`) and an explicit private SSH configuration (`ENV`, canonical location `~/.palarran/.env`). No input authorizes deployment by itself. Deployment requires authorization for this exact target and procedure.

The checkout must contain `packages/core/coordination/{service,build_sqlite,deploy}.py` exactly as stored at `REV`; the running deploy helper must be that checkout's committed file. Before preparation and every remote call it verifies all three files against `git show REV:PATH`. Uncommitted, substituted or symlinked sources fail. The packet binds the source commit and hashes; later calls must supply the same revision, project and checkout. Packets from the former private helper have no supported migration or adoption path.

The SQLite archive SHA256 is `acb1e6f5d832484bf6d32b681e858c38add8b2acdfd42ac5df24b8afb46552b4`. The reviewed builder verifies publisher source checksums, compiles using existing GCC and probes Python's actual loaded library. Sources: [official SQLite 3.51.3 release](https://sqlite.org/releaselog/3_51_3.html), [WAL reset bug and fixed versions](https://sqlite.org/wal.html), [systemd execution sandbox options](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html). Checked 2026-10-24. Vendor documentation describes component behavior; this runbook's isolation and phase sequencing are project recommendations, not a vendor deployment guarantee.

The fixed `--preflight` below performs read-only admission inventory. It requires at least 1 GiB RAM, one CPU and 2 GiB free on both `/var/lib` and `/var/tmp`, existing GCC/make/systemctl/sudo, supported OS/Python and a free loopback port. Installation repeats these gates. Inspect the receipt before proceeding: inventory must establish absence of TCP listener 18792, absence of account/group `palarran-coordination`, and absence of `/opt/palarran-coordination`, `/etc/palarran-coordination`, `/var/lib/palarran-coordination` and `/etc/systemd/system/palarran-coordination.service`. Stop on a mismatch. Never remove a foreign path to make installation pass. SSH host key verification must already be established. `ENV` is an owner-only regular file without symlink ancestors, from which the helper reads only `VPS_HOST`, `VPS_USER`, optional `VPS_PORT` and `VPS_IDENTITY_FILE`; never print its contents. SSH password collection and password-based sudo are unsupported.

## Fixed commands and phase gates

The following shell variables are operator-supplied absolute paths/approved values, not literal defaults. Keep packet and evidence outside Git. No command substitutes a discovered revision for the approved revision. First run the exact committed helper with no action, or `--plan`: it prints a fixed inert phase description and reads no files/environment, starts no process and writes nothing.

```sh
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --plan
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --preflight --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --env "$ENV"
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --prepare --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --archive "$ARCHIVE" --packet "$PACKET"
```

`prepared_private_packet` means local preparation only. The new packet is mode 0700, with mode 0600 inputs, profiles and durable intent. It contains distinct ordinary owner, operator and synthetic acceptance identities. Owner/operator access the chosen project and a unique synthetic project; acceptance accesses only the synthetic project. Profiles point to loopback 18792 and do not start tunnels or activate MCP. Record the returned runbook/version, revision, deployment ID and source/archive/unit hashes privately. Never record tokens, environment values or packet file bodies.

Explicit authorization for the concrete deployment and reviewed preparation receipt is required before the next command. Phases never chain automatically:

```sh
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --build --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --install --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --verify --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
```

Proceed from build only on `built_verified`: the deploy user has compiled/probed the private library, and its hash is bound to intent. Proceed from install only on `installed_active`: root installed the immutable hash-named service release and private library, created the dedicated account/private configuration/state, and started only the namespaced systemd unit. Service-scoped `LD_LIBRARY_PATH` selects `/opt/palarran-coordination/sqlite/3.51.3/lib`; it does not replace the OS library. Code/library are root-owned read-only; credentials/state belong to the unprivileged service user. Unit hardening includes no new privileges, private devices/temp, strict read-only system paths, private home protection, restricted capabilities, resource limits and a single writable state directory.

`verified_readonly` establishes the observed unit/library hashes, active process mapping to the pinned library, authenticated receipt lookup, 401 without credentials and 403 for the synthetic probe against the real project. This is narrower than application acceptance, multi-machine connectivity or operational availability. Stop on any other status/nonzero exit. Errors contain safe codes only; retain private intent and identifiers, never enable verbose SSH/body/header logging.

## Unknown outcomes and reconciliation

Before each mutating SSH call, intent records `unknown` durably under an advisory packet lock. Interrupted calls, timeouts and malformed replies are unknown outcomes; killing a local SSH process does not prove remote cancellation. Repeating build/install/rollback is refused, including after a successful phase. Do not create another packet or deployment ID to bypass an unresolved attempt.

```sh
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --reconcile build --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --reconcile install --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
```

Run only the command matching the unknown phase. Reconciliation observes existing markers, exact hashes and unit state; it does not rerun a mutation. `observed_build_complete`/`observed_install_complete` can resolve the corresponding unknown intent. Missing/partial/foreign artifacts remain blocked for operator investigation. There is no force/adopt/delete/automatic repair path. An interrupted install before its completion marker requires manual review, even when a process appears healthy. The previous private helper's existing packet is a separate recorded legacy-v0 procedure and cannot be loaded by this public helper.

## Joint acceptance: separate explicit operator action

After readonly verification, authorized operators use two independently authenticated SSH tunnels/clients and the synthetic project named in the private intent. Follow the [wire contract](wire.md) with stable request IDs: ensure two rooms; post/list a synthetic message; acknowledge it as the second identity; retrieve the original actor's receipt; demonstrate a claim cannot be acquired from the other room in the same project; release and reacquire with a greater fence. Confirm the probe cannot access the real project and an ordinary actor cannot reconcile. Do not claim external shell fencing from advisory claims. Never use real production resources for this exercise.

With explicit restart authorization, restart only `palarran-coordination.service`; repeat receipt/message/ACK/claim observations to prove persistence and rerun readonly verify. An operator reconciles expired synthetic claims only after observing the associated external state; never auto-reassign. Preserve quota-bound synthetic records: the API intentionally has no delete operation. Record exact source/library/unit hashes, identities without tokens, request IDs, expected/observed outcomes, restart evidence, and PASS/FAIL/NOT_RUN separately. Different physical developer machines, native client interoperability and SLA windows remain NOT_RUN unless actually observed.

## Rollback and handoff

```sh
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --rollback --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
python3 "$CHECKOUT/packages/core/coordination/deploy.py" --reconcile rollback --checkout "$CHECKOUT" --source-revision "$REV" --project "$PROJECT" --packet "$PACKET" --env "$ENV"
```

Rollback is explicitly authorized separately, applies only after a completed install and stops/disables only the new unit; `stopped_disabled_state_preserved` retains credentials, code, build artifacts, state and receipts. Reconcile rollback only after an unknown rollback. Partial install rollback and removal/upgrades/token rotation require a separately reviewed procedure. Final handoff records completed/remaining phases, source revision/hashes, exact subjects, private evidence locations, unknown outcomes, separate joint acceptance and operational limitations. No helper exit alone constitutes deployment acceptance.
