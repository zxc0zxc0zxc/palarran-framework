# Runtime

Наследует root. Перед изменениями читать docs/product-factory/contract.md, operations.md и связанные ADR; для ML — docs/ml/pipeline-contract.md и modal-adapter.md. Полные обязательные ограничения: раздел Runtime и выбранный профиль docs/skills/domain-contracts.md.

- engine координирует execution/independent final gates; store владеет fenced leases, private SQLite и immutable workflow; runner ограничивает foreground process groups/output/time. Parser/docs/examples/tests обновлять вместе.
- accounting/budgets и ml_resources не обнуляют failed/unknown spend. Private state вне target. Не replay unknown lease outcome; operator reconciliation не доказывается agent narrative.
- Product/ML manifests и verifiers сохраняют context/source/lineage hashes и stable private receipts. Compact packet/graph не заменяют mandatory docs и проверку exact checkpoint/subject.
- Modal: durable intent до create; lookup вместо повторного launch; remote terminal proof обязателен для stop. Provider estimates/usage/invoice раздельны, billing pending удерживает reserve. Existing resources, никакого paid smoke.
- Agent eval: перед изменениями читать docs/agent/eval/. Frozen external graders и final gates обязательны; fixture evidence не model quality, unknown расход не ноль. Tests только offline/fake.
- Agent improvement: docs/agent/improve/ обязательны; frozen skill treatment + regression/controls, native eval bindings, all-case denominator и общий carry. Prepare/compare не dispatch/patch, fixture не model evidence.
- Context optimization не меняет AI routing/caps/approval и не запускает вложенные модели. Runtime не должен обязательно зависеть от optional Graphify installation; missing/stale graph = fallback.
- Проверка: offline unit suite, scripts/validate_repo.py, scripts/factory_acceptance.py. Live provider/operational SLA остаются NOT RUN без отдельного scope/evidence.
