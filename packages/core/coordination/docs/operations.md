# Operate private coordination

Read the [contract](contract.md) and exact [wire fields](wire.md). These instructions prepare an optional installation, not proof of a live service. No paid API/model dependency exists in this service. SSH/VPS provider charges, if any, are separate existing infrastructure costs.

## Server

Check the linked Python SQLite version against the contract admission rule before installation. Export the reviewed standalone service.py from an approved pinned source revision into `/opt/palarran-coordination/releases/<release-id>/`; keep code root-owned/read-only to the service user and point a root-owned current link at that release. This server needs no skills, agent clients, private framework home or full repository checkout. Create a dedicated unprivileged `palarran-coordination` account, a private0700 `/var/lib/palarran-coordination` directory and a non-world-readable `/etc/palarran-coordination` directory. Place owner-only0600 credentials.json readable by that account. The trusted file maps each random token to one distinct `{actor,projects,role}` profile. Generate at least32 random bytes per token using the OS CSPRNG; do not paste populated files into chat, Git or terminal transcripts. Keep an operator credential separate from ordinary agent profiles.

If the linked SQLite is too old, provision a reviewed fixed runtime privately for this service; never replace the system SQLite implicitly. A service-scoped LD_LIBRARY_PATH can select a separately compiled official library after ABI/startup tests; record archive/build/runtime hashes and use the explicit library version path.

Review the [system unit](../templates/palarran-coordination.service) for actual Python/source paths, user/group, state directory and memory limits before installation. The process listens only on127.0.0.1:18792. Do not open an Internet firewall port, bind0.0.0.0, share SQLite over NFS or run as root. Service startup and the existing Neo4j memory service are independent; restarting one must not restart the other.

A membership change is a private credential-file change followed by an explicit service restart. Remove the old token when rotating it; keep actor IDs stable for attribution and idempotency. Reusing a former identity for a different person/agent is unsafe. Restart invalidates in-flight transports but preserves committed receipts and claims; recover using their original IDs.

## Each developer machine

Provision that participant's own SSH access through the operator's existing process. Verify the host fingerprint through a trusted channel. Establish numeric loopback forwarding to the server's loopback18792; the [example user unit](../templates/tunnel.service.example) is for Linux, not a macOS auto-install. On macOS use the existing approved LaunchAgent/tunnel workflow. Do not enable agent forwarding, auto-accept host keys or include passwords/tokens in SSH arguments.

Store the participant's private profile from [client.env.example](../templates/client.env.example) in owner-only0600 project `.env` or global `~/.palarran/.env`. Explicit `--env` wins; otherwise a project containing coordination keys wins as a complete profile, then global fallback. A partial project profile is rejected, not merged across scopes. Other unrelated project keys do not shadow the global profile. Files are parsed as literal values, never shell-sourced.

Offline config validation:

```sh
python3 -m packages.core.coordination.client check
```

Start a local stdio MCP server from the pinned library root:

```sh
python3 -m packages.core.coordination.client mcp
```

Configure the host client's `command`, `args` and working-directory equivalent for that source root. Do not embed credentials in a public MCP manifest; invoke the private profile loader. This source workflow does not itself register or activate a global MCP server. Ordinary tools omit operator reconciliation; the trusted operator uses the fixed API/CLI with their separate profile.

For CLI calls use `request --operation OP --input PRIVATE_JSON`, with owner-only0600 request input. `--plan` performs no profile read, networking or writes. Save an action's stable request_id before sending; after timeout read `operation.get` using the same ID. No automatic replay is performed by the client.

## Capacity, recovery and acceptance

Review room/message/resource/receipt and byte quotas in wire.md. The service never silently deletes old messages/receipts or unresolved claims. Monitor capacity on the host; retention/archival is an explicit operator task. SQLite observed admission/WAL checkpoint bounds are not a hard filesystem quota during host faults.

Back up a consistently stopped service and its private database/credential files with an approved encrypted backup destination. Do not copy a live main database alone while WAL has uncheckpointed transactions. Test restore into an isolated directory/port before trusting the backup. Never restore an old coordination snapshot into active use without reconciling newer external actions and invalidating stale holders; older receipts are not proof that later actions never happened.

Required acceptance: two distinct clients on the same project exchange messages; unauthorized projects fail; simultaneous acquisition yields exactly one holder; expiry blocks takeover; a lost response can be looked up after restart; a stale holder cannot release a new claim; different projects stay isolated. Local automated tests cover synthetic clients only. Real different-machine tunnels, client-host interoperability, restart/restore on the VPS and operational availability must be reported separately as NOT_RUN until observed.
