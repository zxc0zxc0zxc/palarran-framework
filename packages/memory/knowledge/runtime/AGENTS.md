# Engineering memory service

Inherits root; packages/memory/knowledge/docs/ guides and domain-contracts are mandatory. Native Neo4j CE + private content-addressed artifacts; Graphify/local ADRs are not replaced.

- Fixed parameterized operations only; no user Cypher, shell or path/URL fetching. Propose != promote; never advertise reviewer credentials in ordinary agent MCP inventories.
- IDs are immutable/deterministic; provenance/applicability/evidence mandatory. Missing evidence/DB errors/unknown outcomes never become success or retries.
- Service is loopback-only; SSH tunnels are separate. Never log tokens/headers/bodies. Environment/state/artifacts stay outside Git. Secret scans do not guarantee privacy.
- Offline fixtures check contracts, not Cypher compatibility. Real Neo4j tests are opt-in on isolated local test DBs only; production is not a test environment.
- Checks: test_memory.py, test_packaging.py, validate_repo.py, full offline suite and factory_acceptance.py. Deployment/restores/live semantic quality remain separately NOT_RUN without evidence.
