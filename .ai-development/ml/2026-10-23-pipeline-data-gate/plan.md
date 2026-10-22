# План data-gate-v001

- [x] Документация и accepted ADR до реализации.
- [x] Real tokenizer/collator, bounded whole-example mixture и independent verifier.
- [x] Runtime approval, dependency gate, launch packet и stable receipts.
- [x] Offline positive/negative integration, full regression и runtime acceptance.
- [x] Handoff с evidence и точными пределами.

Implemented revision: ml-v002-data-gate. Verification: PASS в описанном local/synthetic scope. Commit: NOT CREATED (существующий dirty checkout сохранён).

Реализовано: explicit data_mode/preparation policy, обязательный ml-prepare для text, source/backend/template pins, completion provenance, no truncation, pad==eos-safe labels, actual domain/language floors/repeat ceiling, deterministic interleaving, private stable receipt, защита от подмены во время verifier и final rerun.

Проверено: 354 tests PASS, 231.085s, без skips при configured real tokenizer environment; validator PASS; factory acceptance PASS. Full suite includes all новых 30 data gate checks. Результат и remaining scope: [handoff](handoff.md).

Что осталось вне scope: Modal text dataset transport/verification, tool/multimodal/Jinja/packing adapters, semantic completeness/PII/near contamination reviews, обучение и general regression настоящей LLM. Эти пункты не отмечены PASS и не являются скрыто выполненными задачами.
