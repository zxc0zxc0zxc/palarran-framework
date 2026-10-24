---
name: palarran-security-infrastructure
description: Audit infrastructure identities, exposure, privilege and recovery boundaries from scoped evidence. Use for /palarran:security:infrastructure; default local read-only review, --plan executes nothing.
---

# Infrastructure security audit

Invocation: `/palarran:security:infrastructure {scope} [--plan]`.

Read the [profile guide](../../docs/README.md), [primary-source register](../../docs/sources.md), [shared audit contract](../../../shared/docs/contract.md), [global memory](../../../../core/agents/docs/global-memory.md) and [decision memory](../../../../core/agents/docs/decision-memory.md) before work. These documents are mandatory context, not optional follow-up reading.

1. Identify the target repository/environment, subject revision and requested boundaries. Read its AGENTS, `.palarran/INDEX.md`, accepted decisions and language preferences. Reuse relevant permitted local evidence; no new remote memory call is implied by this audit. Record missing evidence without installing or repairing anything.
2. Set the actual scope. Default: read local source/IaC/manifests and existing sanitized evidence, then write audit artifacts only. `--plan`: produce the evidence/inspection plan without commands, SSH, target/provider calls, remote refresh, scanning or tests. Live read-only inspection requires existing authorization naming target, environment, allowed reader role and exact read scope. If that scope is absent, continue locally and mark runtime rows `NOT_RUN`; do not collect login passwords or elevate privileges automatically.
3. Map human/CI/workload identities and control plane, ingress, management, storage, backup and outbound boundaries. Adapt depth to VPS/Compose versus Kubernetes/cloud. Follow a deployment identity to its artifact, runtime privileges and data permissions; distinguish end-user authorization from service identity. Inspect metadata/credential reachability assumptions from configuration without contacting metadata.
4. Apply the guide's coverage model to users/roles, network exposure, host/container privileges, workload tokens, provenance/updates and backup/recovery. Pair each claimed property with source lines/configuration identity and evidence dates. Desired configuration, effective observed state and demonstrated recovery are different layers. Missing platform enforcement evidence prevents a runtime pass.
5. Produce a readable summary and the shared-contract version 1 JSON report with a boundary diagram and coverage rows marked `PASS`, `FAIL`, `NOT_RUN` or justified `NA`. For findings, explain preconditions, affected principal/asset, impact, confidence, primary-source applicability, narrow remediation options and future verification. Do not label an untested possibility as a confirmed exploit, a backup job as a proven restore, or a clean static review as compliance.
6. Preserve sanitized results and accepted rationale in target `.palarran/security/<task>/`, update its index/handoff, and use its documentation language. Keep credentials, raw inventory/logs and private endpoint values out of Git and user-facing output. Summarize confirmed findings, unverified boundaries and next scoped checks. Applying changes, probing exposure, scanning, restoring data or restarting services requires separate authorization; this skill does not perform them automatically.

Keep finding severity and confirmed/suspected confidence separate from control coverage. Use the shared offline report validator for structure/traceability when available within the execution scope; a valid report is not a security PASS. With `--plan`, report validation remains unexecuted.
