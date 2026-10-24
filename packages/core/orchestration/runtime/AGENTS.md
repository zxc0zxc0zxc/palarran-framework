# Runtime

Inherits root. Before changes read packages/core/orchestration/docs/contract.md, operations.md and related ADRs; ML additionally requires packages/machine-learning/experiments/docs/pipeline-contract.md and modal-adapter.md. Full mandatory constraints: Runtime and selected profiles in packages/core/agents/docs/domain-contracts.md.

- engine coordinates execution/independent final gates; store owns fenced leases, private SQLite and immutable workflows; runner bounds foreground process groups/output/time. Update parser/docs/examples/tests together.
- accounting/budgets and ml_resources never reset failed/unknown spending. Private state stays outside target. Never replay unknown lease outcomes; agent narratives do not prove operator reconciliation.
- Product/ML manifests/verifiers preserve context/source/lineage hashes and stable private receipts. Compact packets/graphs replace neither mandatory docs nor exact checkpoint/subject verification.
- Modal: durable intent before create; lookup instead of relaunch; remote terminal proof required for stopping. Separate provider estimates/usage/invoices; pending billing retains reserves. Existing resources only, no paid smoke tests.
- Agent eval: read packages/validation/agents/docs/eval/ before changes. Frozen external graders/final gates mandatory; fixtures do not establish model quality, unknown spend is not zero. Offline/fake tests only.
- Agent improvement: packages/validation/agents/docs/improve/ mandatory; frozen skill treatment + regression/controls, native evaluation bindings, all-case denominators and shared carry. Prepare/compare is not dispatch/patch; fixtures are not model evidence.
- Context optimization changes neither AI routing/caps/approval nor launches nested models. Runtime must not require optional Graphify installation; missing/stale graphs use fallback.
- Checks: offline unit suite, scripts/validate_repo.py, scripts/factory_acceptance.py. Live provider/operational SLA remain NOT RUN without separate scope/evidence.
