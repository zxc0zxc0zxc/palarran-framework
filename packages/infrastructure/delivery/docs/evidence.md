# Evidence: where decisions come from

Reading date: 2026-10-18. Company practices below are described by their authors; historical material does not prove internal tools/processes remain unchanged. Concrete DAG, thresholds, filenames and tool combinations in this repository are our adaptation.

| Company and primary source | Authors' observation / principle | Our application | What the source does not prove |
|---|---|---|---|
| [Google: Release Engineering](https://sre.google/sre-book/release-engineering/) | Versioned automated builds, release identity and controlled actions | Pin toolchains/dependencies, release manifest and self-service deployment | Our builds are automatically hermetic or byte-for-byte reproducible |
| [Google: Canarying Releases](https://sre.google/workbook/canarying-releases/) | Bounded rollout evaluating version behavior | Health/SLI gates, clear abort and rollback | Identical bake times/thresholds suit all services |
| [Google Testing: Just Say No to More E2E](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Narrower tests often provide needed signals more cheaply | Unit/component/integration coverage + small critical E2E suite | All integration checks may be replaced by mocks or E2E removed |
| [Google Testing: Flaky tests](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html) | Test size/complexity relate to instability; flaky signals need work | Flake-rate metrics, resource isolation and bounded owned quarantine | Retrying until green fixes bugs |
| [Meta: Predictive test selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | Meta selected test subsets using a trained model and signal-quality validation | Start with dependency-aware affected tests, then compare with full suite | Simple path filters match their ML system's completeness |
| [Meta: Rapid release](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) | Frequent changes need automation/regression observation | Small releases, traceability, diagnosis and ownership | Every project needs their release cadence or branching model |
| [Netflix: Kayenta](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69) | Baseline/canary metric comparison enables automated assessment | Progressive delivery/automatic stop with suitable traffic | Spinnaker/Kayenta must be installed or empty metrics count as success |
| [Microsoft: Governed pipeline templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) | Shared templates enforce security checks and controlled flexibility | Shared versioned provider templates + small stack adapters; application flags cannot disable policy | Their Azure DevOps templates transfer directly to GitHub/GitLab |
| [AWS: Automated changes](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html) and [testing/rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html) | Documented AWS recommendations automate deployment, checks and recovery | API/GitOps/pull instead of host shell sessions; rollback within the flow | This describes all Amazon teams' internal pipelines or mandates Kubernetes |

## Our architectural decisions

1. Stable release IDs include source commit, image digest, test evidence, toolchain/lockfile fingerprints and policy version. Promotion moves the same artifact instead of rebuilding for every environment.
2. Prefer pull GitOps for Kubernetes deployment. Managed runtimes use deployment APIs with short-lived identities. A single VM uses a preconfigured narrow pull-agent, not a production-root CI runner.
3. Select `dev/test/prod` from verified environment registries describing infrastructure/policy without credentials.
4. Optimize measured critical paths: independent parallel jobs, correct cache keys, safe test selection and superseded-CI cancellation. Do not cancel active production deployment like a normal PR job.
5. Security gates and actual rollout checks are part of readiness. Quickly submitting a GitOps commit is not a fast successful deployment.

Stack guides use different techniques with the same shared basis. This selection contains no primary source proving Netflix uses our exact PHP commands or Meta our Rust configuration. Such attributions are forbidden.
