# Источники и применимость

Проверены 2026-10-24; rolling guides не имеют единой даты публикации. Версию image/digest фиксировать перед deployment, не считать current guide подтверждением выбранного image.

| ID | Primary source | Что используем |
| --- | --- | --- |
| E-MEM-001 | [Neo4j editions](https://neo4j.com/docs/operations-manual/current/introduction/) | CE single instance, Cypher/ACID; enterprise HA/online backup не обещаем |
| E-MEM-002 | [Fulltext](https://neo4j.com/docs/cypher-manual/current/indexes/search-indexes/full-text-indexes/) | Native Lucene indexes, relevance scores; это не semantic recall |
| E-MEM-003 | [Query API](https://neo4j.com/docs/query-api/current/query/) | Parameterized statement, implicit atomic transaction; HTTP202 сам по себе не success, проверять errors |
| E-MEM-004 | [Offline backup](https://neo4j.com/docs/operations-manual/current/backup-restore/offline-backup/) | CE dump при остановленной DB, отдельные system/auth/artifacts и restore drill |
| E-MEM-005 | [OpenSSH config](https://man.openbsd.org/ssh_config) | StrictHostKeyChecking, forwarding и BatchMode; host key не угадывается |
| E-MEM-006 | [Docker secrets](https://docs.docker.com/compose/how-tos/use-secrets/) | Credentials вне image/Git/logs; ограниченные file permissions |
| E-MEM-007 | [Google SRE Simplicity](https://sre.google/sre-book/simplicity/) | Минимум необходимых компонентов; конкретный выбор Neo4j — наш/user выбор |
| E-MEM-008 | [Hindsight retain](https://hindsight.vectorize.io/developer/api/retain), [recall](https://hindsight.vectorize.io/developer/api/recall) | Рассмотренная альтернатива с модельной обработкой; не подключена |

Из пользовательского диздока берём promotion loop и source/applies_when/limitations. Сравнительные оценки Hindsight/Graphiti и vendor performance не переносим как измеренные факты.
