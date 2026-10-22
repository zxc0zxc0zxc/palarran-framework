# Skills

Наследует root. Перед изменением skill читать docs/skills/decision-memory.md, agents-authoring.md и его обязательный профиль в domain-contracts.md. Сначала профильная документация, затем skill/command adapter.

- SKILL.md остаётся коротким workflow с ссылками на mandatory docs. Scope plan/build, permissions и evidence не размывать ради компактности.
- Project instructions/ADR/graph относятся к target root, не installed skill checkout. Применимые AGENTS читать перед code changes; создавать их только в разрешённом implementation scope по реальным границам.
- Graphify optional: fresh bounded navigation, затем source; graph не заменяет источники/UX/UI/API contracts/verification или решения. Не устанавливать tools автоматически в planning run.
- При новом skill синхронно обновить namespace plugin, .claude adapter, .agents discovery link, validator registration и packager resources. Не менять глобальный Codex/Claude config.
- Проверка: scripts/validate_repo.py, offline suite и portable packaging tests. Missing tools/evidence отражать как draft/partial/NOT RUN, не выдавать за проверенный результат.
