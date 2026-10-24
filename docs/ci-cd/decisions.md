# Decisions the skill must discuss

An ADR contains question, verified facts, assumptions, options, choice, primary source, our adaptation, cost/risk, owner, acceptance and reconsideration condition. Starting directions below do not replace intake.

| Question | Preferred starting point | When alternatives make sense | Basis |
|---|---|---|---|
| Kubernetes, managed API or VM pull | Preserve existing supported SSH-free backend | New backend only for explicit need/cost/bootstrap | [AWS automation](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html), our topology |
| Full suite or affected | Full release gate; validated dependency selection for PR feedback | Selective release gate only after evidence/ADR/shadow full | [Meta selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/); do not automatically copy its ML |
| One build or variants | One digest across environments, runtime configuration | Unavoidable build-time differences require separately tested variants | [Google release](https://sre.google/sre-book/release-engineering/), [Next env](https://nextjs.org/docs/app/guides/environment-variables) |
| Manual button or automatic promotion | Project choice; one shared deployment contract | Production approval, freeze or separate risk/policy gate | [Google canary](https://sre.google/workbook/canarying-releases/); manual ≠ authorization |
| Recreate, rolling, blue-green or canary | Rolling with capacity/compatibility; explicit downtime for single instance | Canary with sufficient traffic/metrics; blue-green with suitable data/session contracts | [Netflix ACA](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69), our thresholds |
| Canary with low traffic | INCONCLUSIVE, longer window/synthetic checks or another gate | Do not call missing metrics green | [Google canary](https://sre.google/workbook/canarying-releases/) |
| Runner placement | Ephemeral build pool, separate trusted management observer | Self-hosted only with maintenance/isolation/capacity owner | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use), [GitLab security](https://docs.gitlab.com/ci/pipeline_security/) |
| Cache aggressiveness | Dependencies/compiler/framework-native cache with trust scope | More complex remote task cache after proving complete inputs | [Docker cache](https://docs.docker.com/build/cache/backends/), stack guides |
| Shared pipeline blocks or duplication | Versioned reusable policy/provider layer + stack scripts | Owned expiring exception, not uncontrolled forks of all checks | [Microsoft governance](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) |
| CI or runtime secrets | Runtime retrieval; CI gets minimal build/deployment identities | Private-package fetch temporarily needs a scoped secret in a reviewed build stage | [BuildKit secrets](https://docs.docker.com/build/building/secrets/), [GitLab variables](https://docs.gitlab.com/ci/variables/) |
| DB migrations and rollback | Serialized expand/contract; old/new compatibility | Destructive migration as a separate agreed operation with recovery | [AWS testing/rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html); source does not guarantee data reversibility |
| GitHub/GitLab tier lacks required gate | Identify missing enforcement and workable alternative | External promotion policy or different tier | Provider environment docs; cosmetic buttons cannot bypass requirements |

## Specific blockers

No trusted deployment controller/API; unknown production target/architecture; missing current environment config; no authorized identity; pipeline can execute arbitrary selected refs with secrets; missing release evidence; irreversible data changes without recovery; no failed-deployment owner. These cannot be fixed through SSH fallback or disabling gates.

Unknown timings alone do not block documentation/design, but do block claims of achieved speedup. Before measurements, performance budgets are objectives. Project policy defines allowed automatic-deployment events/approvals once; no repeated chat requests are needed for each authorized pipeline run.

Record accepted decisions and rationale under the [shared contract](../skills/decision-memory.md) in target `.palarran/`; this document remains a question catalog. The next task must read relevant accepted records and account for their context.
