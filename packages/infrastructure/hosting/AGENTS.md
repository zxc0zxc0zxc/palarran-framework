# Palarran container hosting

Inherits Infrastructure. Read docs/runbook.md, docs/sources.md and the Core installation runbook contract before host actions. This capability owns Compose and its private-file adapter/preparation, not domain API semantics.

- Source preparation/build is not deployment or data migration. Parent operator owns exact legacy resources, consistent copies, attempt receipts and rollback; preserve unknown outcomes and original state.
- Keep graph, memory and bus separate and non-root: graph only on internal private, Memory on access+private, bus only on access. Access is a standard bridge with outbound connectivity; never claim global egress denial. Only host127.0.0.1 API publishing is supported; no socket/privileged/host network. Default standalone APIs stay loopback.
- Numeric UID/private-file contracts, selected image/archive/source pins and exact graph hostname are executable boundaries. Never relax them to make startup pass; never log secret values or render expanded configuration.
- Check copied new-state trees for symlinks/hardlinked files/special files and traversal errors before ownership changes. Never apply recursive ownership/deletion to legacy or inferred paths.
- Offline checks: tests/test_container_hosting.py, tests/test_memory.py, tests/test_coordination.py and factory_acceptance.py. Actual Linux image build, bridge behavior, graph restoration and authenticated/restart acceptance need independent target evidence.
