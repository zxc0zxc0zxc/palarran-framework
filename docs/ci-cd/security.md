# Security: secrets, trust and supply chain

## Trust boundaries

| Level | Allowed | Forbidden |
|---|---|---|
| Fork/untrusted PR/MR | Lint/tests with synthetic secrets, limited source reads, separate cache scope | Production identities, trusted-cache writes, registry-release publication, private management runners |
| Reviewed protected source | Build/test candidate, publish to authorized registry | Automatic authority to change any environment |
| Promotion controller/job | Verify eligibility and change a specific environment contract | Execute arbitrary scripts from selected user refs with deployment credentials |
| Runtime deployment controller | Apply authorized manifests locally/through scoped APIs | Receive shell commands from CI inputs or serve arbitrary registries/repositories |

CI config, reusable workflows/includes, Dockerfiles and environment registries are executable supply-chain components: use CODEOWNERS/review, pinned trusted refs and branch protection. Application-change authors cannot independently disable required policy gates. Basis: [Microsoft governed templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates); select provider mechanisms separately.

## Identity

Use OIDC/federation where supported: restrict issuer, audience, repository/project ID, protected ref, environment and trusted-workflow claims as trust policies allow. `id-token: write` alone does not restrict cloud roles to required environments. Without federation, use short-lived scoped application/deployment tokens with rotation/expiry, never target SSH private keys.

Build gets registry publishing only for its own image; promotion may modify only its own environment/path; runtime gets pull and necessary secret refs. Separate dev/test/prod identities. No long-lived cluster-admin kubeconfig in CI. Runtime secret providers normally retrieve application secrets without passing them through build jobs.

## No secrets in output

Forbid `set -x`, debug trace/service debugging with secrets, `env/printenv`, context dumps, authenticated `curl -v`, response bodies without allowlists, logging commands with passwords/tokens in argv and `.env`/kubeconfig/IaC-plan uploads. Also inspect test assertions, exception stacks, HTTP recordings, SQL connection strings, Composer/npm/pip auth errors and application startup output.

Masking in [GitHub](https://docs.github.com/en/actions/reference/security/secure-use) and [GitLab variables](https://docs.gitlab.com/ci/variables/) is an extra layer; transformed, fragmented or deliberately printed secrets may bypass it. Mask runtime-generated credentials **before** use, but do not deliberately print them even to test masking. Pass credentials through provider credential helpers/protected file mounts/standard input where supported; exclude from artifacts and clean ephemeral workspaces.

Reports are data too: JUnit, coverage HTML, Playwright traces/screenshots/videos, service logs and core dumps may contain tokens/PII. Use synthetic accounts/data, redaction, restricted artifact access and retention; no entire-workspace dumps under `always()`. Control exception messages/sanitization, not just console output. When tools cannot safely filter data, bound capture or disable sensitive capture with alternative diagnosis.

Supply build secrets through [BuildKit secret mounts](https://docs.docker.com/build/building/secrets/), not Docker `ARG`/`ENV` or copied auth files. Mounts cannot protect against malicious `RUN` copying secrets into layers or stdout. Private-dependency installation is a separate reviewed trust boundary; lockfile scripts/plugins can execute code. Private-package read credentials are minimal and unavailable to forks.

## Artifact integrity

Verify source commit, builder/workflow identity and inputs, image digest, SBOM/vulnerability policy, provenance/signature. Creating attestations without predeployment verification is not enforcement. [GitHub attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) are one implementation; for GitLab, choose compatible signers/verifiers instead of assuming identical mechanisms.

Scan dependencies and final runtime images; policy defines severity/fix availability/exceptions with owner+expiry. CVE scanners do not replace build tests. Trusted release publishing must not consume unverified executables/artifacts/caches from unreviewed PRs. Prefer container builds without privileged runners; if privileged Docker-in-Docker is chosen, explicitly justify isolated ephemeral pools and no production network.

## Acceptance and response

Before enabling real secrets, run synthetic sentinels only in an isolated harness: tools consume fake values through normal paths; scanners check logs/reports/cache/image history/layers, including diagnostic failure paths and known encoding patterns. Do not deliberately print sentinels in public job output or have scanners print matching lines: report only file/job ID and leak type. This tests known paths, not mathematical absence of all covert channels.

Negative tests: forks cannot obtain deployment identity; wrong audiences/refs/environments fail IAM; unknown environments/foreign registries/releases are rejected; debug capture with secrets is blocked; unsigned/ineligible digests are not deployed; production config changes need required reviewers; cache poisoning cannot cross trust scopes.

On leakage: revoke/rotate credentials → stop access/releases from affected identity → restrict/delete sensitive logs/artifacts/caches under provider procedures → determine access/affected releases → reverify. Removing a YAML line does not revoke an already published secret.
