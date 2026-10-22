# Документация

Наследует root. Профильные обязательные правила собраны в skills/domain-contracts.md; прочитать нужный раздел до изменения поведения/skill.

- Project guides — русский, identifiers/code — English. Сначала первичные источники; даты/version/applicability в sources.md, ссылки рядом с рекомендациями. Vendor claim не наш benchmark.
- Source of truth остаётся docs соответствующего профиля. Documentation-only не разрешает install/deploy/skill activation; если пользователь просит реализацию, менять связанные contracts/adapters/tests согласованно.
- Planning и execution разделены; numerical proposal не operational SLA, evidence completeness не market validation, training completion не benchmark acceptance.
- AGENTS не должен повторять учебник: короткие scoped инструкции по skills/agents-authoring.md; полные основания в docs/ADR. Новые links должны сохраняться в portable packages.
- Проверка: scripts/validate_repo.py; при contract/skill/runtime changes — соответствующие offline tests. Нет придуманного render/live/API evidence.
