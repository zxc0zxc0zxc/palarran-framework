# Registry operations runbook

ID palarran.packaging.registry; version1.0.0; source baseline is the reviewed Packaging implementation commit. This is an installation procedure specification, not evidence of deployment. Use a trusted source-only image/export, Python>=3.9 runtime and a private local state volume; never install agent skills on the server.

## Inputs and scope

A separate service account, existing writable private DB/blob directories, owner-only credentials file, explicit host loopback port and approved image/source SHA are required. Credentials map distinct random tokens to `{actor,read_publishers}`. Tokens come from owner provisioning, never package metadata or public signup. Reject unrecognized state/schema, symlink paths and unsafe permissions. Source/config paths and port must not overlap existing services. Selecting packages alone does not authorize this procedure.

The service CLI accepts `--db`, `--blobs`, `--credentials`, `--port`; credentials are file references, never token values. Bind127.0.0.1 by default. Container mode explicitly allows a private bridge listener only when host publishing stays127.0.0.1. Do not put registry bytes/credentials in Git, open unauthenticated write endpoints publicly, or reuse memory/bus tokens.

## Ordered procedure

1. Inspect target/runtime, source SHA/image, existing workloads and state ownership within authorized host scope. Record runbook/source hashes and operation identity privately before changes.
2. Prepare exact local-volume/credential mounts and bounded resource settings from the inert example. Default storage is local filesystem; an S3 adapter requires a separately provisioned private bucket and existing trusted SDK client. No auto cloud account/bucket/dependency installation.
3. Start only the chosen service via the approved hosting pipeline/procedure. Read back actual container/image/port ownership. An unknown start reply requires inspecting that operation/container, not another start.
4. Through an owned tunnel, use two test actors to publish a disposable private version; verify unauthorized search/get/download denial, authorized exact SHA retrieval, duplicate operation lookup, restart persistence and owner delist/delete behavior. Clean test releases only through their explicit owner lifecycle. Never publish private application content as a health probe.
5. Record file/process/wire/security outcomes separately. A running server or exit0 is not marketplace acceptance. Global client configuration and actual publication require their own authorized inputs.

## Recovery and capacity

SQLite metadata/receipts and immutable blobs are one recovery unit. Stop writes and take a consistent stopped copy of both plus private config. Hash/restore into an isolated location, start the same reviewed schema version and verify authorized/denied reads and exact byte hashes before replacing active state. Do not copy a live SQLite file or rollback metadata while silently losing acknowledged blob references. Orphans are retained; no automatic blob garbage collection.

Initial bound:1000releases,10000receipts,4MiB archive,16MiB expanded,256payloadfiles,8handlers. Exhaustion rejects writes before requested metadata mutation. Monitor disk, request latency/failure and quota refusals without tokens/contents/unbounded labels. Proposed availability/latency/RPO/RTO in the feature plan need actual host/window acceptance; no HA or monthly SLA is established by local tests. Delist is discovery withdrawal; delete is a permanent tombstone, not secure erasure of prior downloads.
