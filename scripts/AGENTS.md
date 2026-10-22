# Скрипты

Наследует root; обязательные источники по trigger — docs/skills/domain-contracts.md. CLI и identifiers English, сообщения/гайд для skills — русский.

- Validators/inventory/cost helpers должны работать offline; отсутствие/unknown цены не считать нулём. --plan не допускает refresh/target access/provider calls.
- Packaging самодостаточен: включать только явные public resources; не копировать target memory, .graphify/venv/cache, .delivery, .env, state или внешние symlinks. При новых ресурсах обновить packager и packaging tests.
- execution_progress совместим с frontend/backend legacy markers, сохраняет revision/commits/evidence и remaining tasks; один coordinator обновляет общий progress/index.
- graph_context использует pinned optional graphifyy в target-local venv, code-only staging, scrubbed env, bounded output и dirty/untracked freshness. Не вызывать graphify install, cloud, semantic/media pass или project executables.
- CLI side effects должны быть явными. Не перезаписывать чужие файлы или генерировать target AGENTS в planning scope.
- Проверка: scripts/validate_repo.py и offline unit suite; изменение runtime-facing behavior — также scripts/factory_acceptance.py. Платных/live проверок не делать.
