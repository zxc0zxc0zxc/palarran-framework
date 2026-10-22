# Шаблоны

Наследует root; профильные контракты — docs/skills/domain-contracts.md.

- Примеры инертны до адаптации к target и разрешения конкретного действия. Не добавлять реальные endpoints, keys, state, credentials или customer data.
- AGENTS templates заполнять только из фактических manifests/code/commands. Не генерировать несуществующие сервисы и не перезаписывать пользовательские инструкции; planning даёт только proposal/handoff.
- ADR template сохраняет canonical ID/status/basis/rationale/evidence/alternatives/consequences. Plan/progress templates сохраняют pending state, source revision и DoD traceability.
- Новые resources явно включать в нужный portable namespace; проверять package-contained links. Graph/venv/target memory не входят в шаблоны.
- Проверка: scripts/validate_repo.py и packaging tests; никаких live apply/train/deploy.
