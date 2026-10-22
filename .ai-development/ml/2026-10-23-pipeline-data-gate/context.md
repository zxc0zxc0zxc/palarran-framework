# Контекст

Target: ai-tools. Scope: документация, local text preparation и mandatory gate перед fit/evaluate, без платных запусков. Reuses: ml/2026-10-23-data-preparation/0001, ml/2026-10-22-runtime-pipeline/0001. Существующий tensor audit доверяет producer; нужен реальный tokenizer и independently regenerated collator. Все исходные данные/тензоры остаются в private state. Старые non-text workflows сохраняются.
