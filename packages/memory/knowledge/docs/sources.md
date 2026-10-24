# Sources and applicability

Checked 2026-10-24; rolling guides have no single publication date. Pin image version/digest before deployment; a current guide does not verify the chosen image.

| ID | Primary source | Use |
| --- | --- | --- |
| E-MEM-001 | [Neo4j editions](https://neo4j.com/docs/operations-manual/current/introduction/) | CE single instance, Cypher/ACID; no enterprise HA/online-backup promise |
| E-MEM-002 | [Fulltext](https://neo4j.com/docs/cypher-manual/current/indexes/search-indexes/full-text-indexes/) | Native Lucene indexes, relevance scores; not semantic recall |
| E-MEM-003 | [Query API](https://neo4j.com/docs/query-api/current/query/) | Parameterized statements, implicit atomic transaction; HTTP202 alone is not success, inspect errors |
| E-MEM-004 | [Offline backup](https://neo4j.com/docs/operations-manual/current/backup-restore/offline-backup/) | CE dump with stopped DB; separate system/auth/artifacts and restore drill |
| E-MEM-005 | [OpenSSH config](https://man.openbsd.org/ssh_config) | StrictHostKeyChecking, forwarding, BatchMode; never guess host keys |
| E-MEM-006 | [Docker secrets](https://docs.docker.com/compose/how-tos/use-secrets/) | Credentials outside image/Git/logs; restricted file permissions |
| E-MEM-007 | [Google SRE Simplicity](https://sre.google/sre-book/simplicity/) | Minimum necessary components; Neo4j selection is our/user choice |
| E-MEM-008 | [Hindsight retain](https://hindsight.vectorize.io/developer/api/retain), [recall](https://hindsight.vectorize.io/developer/api/recall) | Considered model-processing alternative; not connected |

The user's design document supplies the promotion loop and source/applies_when/limitations. Hindsight/Graphiti comparisons and vendor performance are not transferred as measured facts.
