# Data preparation v001 — handoff

Применено ml/2026-10-23-data-preparation/0001; reuses ML docs-first/lineage/approval и independent evidence. Existing dirty changes сохранены, commits/push/deploy отсутствуют. Никаких реальных dataset/model downloads, installs, GPU, API generation или paid training.

## Что сделано и почему

- Сначала docs/ml/data/: восемь guides, 13 dated primary references (Karpathy, dedup, RefinedWeb, DoReMi, Dolma, FineWeb, DCLM, XLM-R, LIMA, forgetting, Tülu 3, versioned HF docs). GIGO — эвристика, reported research не наши measurements.
- Coverage/data-needs planning и source/annotation/rights gates. Joint domain/language token exposure, floors/repeat caps, preservation anchors, length/source/task diversity; no universal ratios/alpha/row counts. Toy templates явно не training recommendations.
- Сохранение general capabilities отделено от механического truncation: complete targets, assistant/causal objective, EOS/EOT/padding/masks, context budget, inference finish_reason и frozen general/domain/language/full-answer regression.
- scripts/ml_data.py (stdlib CPU): profile, prepare, audit-tokens, mix-plan. Input bounds, strict schemas, no overwrite/secret stdout, explicit approval metadata, text/code/Unicode preservation, connected group/exact-content components до split, protected fixed holdout, private ledger/shards/hash verification.
- Tensor integrity с exact prepared record bindings, actual provided ID/label counts, zero/only-EOS target rejection, pad=EOS, full coverage и slice failures; semantic correctness и tokenizer authenticity не выводятся из IDs/flags. Mix feasibility train-only, exact decimal quotas/rounding, capacity/unique-token deficits и no silent renormalization.
- Existing /ml:data/adapter, mandatory profile validation, ML route/source/plan docs, data-plan/JSON templates и standalone package resources обновлены. Runtime ML stages остаются research/planning по прежнему контракту; helper не меняет training approvals/бюджет и не запускается автоматически.

## Verification

- PASS: 323 full offline tests (230.254s).
- PASS: 26 final focused data tests (0.429s), включая последний only-EOS target gate; длинные/Unicode/code-preserving answers, connected duplicate groups, fixed holdout conflicts, rights/secret exclusions, raw/report privacy, file/ledger drift, mask/EOS/layout/coverage failures, source bindings, domain/language quotas/floors/repeats и standalone CLI end-to-end.
- PASS: 4 portable packaging tests (0.501s), включая запуск packaged data helper без checkout/runtime/dependencies. Первый packaging probe использовал macOS alias parent /var и был корректно отклонён no-symlink contract; fixture исправлена на canonical physical path, без ослабления проверки.
- PASS: repo validator/mandatory docs/links/26 skills, py_compile, git diff --check. Code runtime не изменялся; factory lab отдельно не запускался в этой задаче, runtime regression включён в full suite.
- Standalone skill-creator YAML helper не перезапускался: в предыдущей задаче import PyYAML unavailable; новых dependencies не ставили. Repository skill frontmatter/guides/packaging проверены.

## Пример и пределы

[Sanitized fixture report](example-report.json): 6 synthetic records → 4 accepted, 1 unknown-rights exclusion и 1 exact duplicate; exported fake tensor audit PASS, 8-token joint plan feasible. Token IDs — явно синтетические fixtures, **не реальная токенизация**. training_ready=false, tokenization_verified=false; sampler/training/model quality NOT_RUN. Temporary raw/prepared/tensor artifacts вне Git, удалены только собственные disposable fixtures. В journal только aggregates/hashes, не raw content/token arrays.

v1 text/chat JSONL и unpacked/right-padding/unshifted tensors. Web-scale streaming, LID, полноценный PII, near/semantic/translation dedup, benchmark decontamination, actual tokenizer/collator/packing/sampler и domain/general model regression — отдельные mandatory gates/adapters, NOT_RUN. Порядок train output воспроизводим по survivor IDs; реальный dataloader обязан shuffle/соблюдать mixture и проверить rolling exposure, план не притворяется sampler. Producer complete=true и declared tokenizer/template hashes не доказывают смысловую полноту/верность mapping. Ни FineWeb recipe, ни DoReMi optimization, ни отсутствие forgetting не заявляются реализованными/воспроизведёнными.

Следующий конкретный шаг после выбора target model/domain/languages и разрешённых данных: local tokenizer/template/collator adapter и decoded sample inspection, затем без training проверить actual exposure/overflow/length slices. Любой pilot/training — отдельный scope и общий сохранённый budget.
