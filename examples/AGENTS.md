# Примеры

Наследует root; relevant contracts — docs/skills/domain-contracts.md.

- Examples инертны, не production-ready конфигурация. Явно обозначать placeholders, exclusions и cost scope. Не подставлять нулевую цену вместо неизвестной.
- ML/Modal пример связан с frozen protocol и exact checkpoint. Remote Volume v2 sync не требует передачи coordinator credentials в Sandbox; image/resources готовятся отдельно в разрешённом scope.
- Local regression fixture — synthetic CPU evidence; это не прикладная ML quality или live integration. Ни примеры, ни tests не запускают paid training/deploy автоматически.
- Изменение example contract сопровождать docs и relevant offline fixture test. Не удалять/менять target artifacts как «cleanup» без scope.
