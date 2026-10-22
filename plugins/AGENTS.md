# Plugin namespaces

Наследует root. Public manifests/identifiers English; пользовательские инструкции — русский.

- Namespace command указывает на существующий .claude adapter и canonical skill. Синхронно обновить scripts/validate_repo.py, scripts/package_plugin.py и packaging tests при изменении состава.
- Package самодостаточен по mandatory docs/templates, без ссылок наружу, target ADR/state/secrets и .graphify artifacts. Не включать optional Graphify dependency в runtime по умолчанию.
- User-owned config/agent installation/активация не подразумеваются изменением manifest. Проверки offline, без install hooks/cloud или paid APIs.
