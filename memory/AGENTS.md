# Engineering memory service

Наследует root; mandatory docs/memory/ guides и domain-contracts. Native Neo4j CE + private content-addressed artifacts; Graphify/local ADR не заменяются.

- Только fixed parameterized operations; никакого user Cypher, shell, path/URL fetch. Propose != promote; reviewer credential никогда не рекламировать обычному agent MCP inventory.
- IDs immutable/deterministic, provenance/applicability/evidence обязательны. Missing evidence/DB errors/unknown outcome не превращать в success или retry.
- Service loopback-only, SSH tunnel отдельно. Не логировать tokens/headers/bodies. Env/state/artifacts вне Git. Secret scan не гарантия privacy.
- Offline fixtures проверяют контракты, не Cypher compatibility. Real Neo4j test opt-in и только isolated local test DB; production не тестовый стенд.
- Проверки: test_memory.py, test_packaging.py, validate_repo.py, full offline suite и factory_acceptance.py. Deployment/restore/live semantic quality отдельно NOT_RUN без evidence.
