# Cross-project engineering memory

Пользователь предоставил диздок promotion/recall/feedback, затем исключил Hindsight/paid memory calls и явно выбрал Neo4j Community. Нужны graph+fulltext, ADR/patch artifacts, VPS SSH skills и local .env + public .env.example. Target VPS известен локально; адрес/credentials не коммитим.

Read-only SSH authenticated with existing known host/key: Ubuntu22.04.5,8vCPU,24GiB RAM,~19GiB disk free, Docker/Python/systemd present. No host modifications. Existing workloads/ports preserved. Local Docker daemon absent: live DB integration NOT_RUN until test environment available; no silent production test.
