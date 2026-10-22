# Контекст

Target: ai-tools. Запрос: дизайн диагностики обучения, task-appropriate эвристики, training/validation отчёты, perplexity и другие метрики, terminal report при любом исходе и samples генерации во времени. Scope этой задачи: документация, переносимые design templates и implementation plan; runtime/training/provider execution не запрошены.

Reuses: ml/2026-10-22-runtime-pipeline/0001; ml/2026-10-22-modal-adapter/0001; ml/2026-10-23-pipeline-data-gate/0001..0003. Код сверён: ml_resources сохраняет usage/reserves, Modal metrics_snapshot принимает bounded finite numeric values; это не task-profile evaluator, generation gallery или universal terminal-report finalizer. Эти возможности нельзя объявить реализованными по наличию метрик/README.

Ограничения: private artifacts, без paid calls/train/download, без изменения ceilings/существующего runtime state. Mandatory docs: docs/ml/contracts.md, metrics.md, train.md, benchmark.md, data/pipeline.md, docs/skills/decision-memory.md. Источники перепроверяются на 2026-10-23; versioned docs — reference, не приказ менять версии проекта.
