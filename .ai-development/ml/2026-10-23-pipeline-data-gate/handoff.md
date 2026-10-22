# Handoff: ML text data gate

## Результат

Документация сначала: [runtime data contract](../../../docs/ml/data/pipeline.md). Реализация: orchestrator/ml_data_gate.py, ml_pipeline.py, ml_resources.py, ml_artifacts.py и engine.py. Source helper scripts/ml_data.py сохраняет optional completion provenance. Skills ml-data/ml-train и mandatory guides обновлены; portable ML package содержит public example config.

Новые execution policies обязаны объявить data_mode=text|non_text. text требует local data_preparation policy с pinned source/tokenizer/template/split/mixture/backend. Семь AI planning stages сохраняются, затем private exact-prefix approval → ml-prepare → independent regeneration → fit → evaluate → final rerun. Data/tokenizer/config lineage должны сослаться на preparation_sha256. Missing/failed/stale gate не даёт reserve/launch trainer. Existing budget ceilings и accounting не изменяются; local prep использует существующие task/run wall-time limits.

Реальная tokenizers library читает проверенный tokenizer.json byte snapshot; model/data не скачиваются. Literal model-native role template только system/user/assistant, assistant или causal objective, без truncation/packing. Right-pad collator выдаёт unshifted labels, маски и полные targets. Сообщения требуют documented completion claim; known length-stop нельзя исправить добавлением EOT. Actual whole-example mix проверяет joint shares, языковые/domain floors, nonzero positive cells и repeat caps; deterministic shuffle перемешивает occurrences. Private output files/receipt сравниваются после независимого воспроизведения и повторно до запуска. Изменение во время verifier не получает fresh attestation.

## Evidence

- PASS: python3 scripts/validate_repo.py; namespaces/skill guides/links/ADR registration.
- PASS: full python3 -m unittest discover -s tests -v с AI_TOOLS_TOKENIZER_PYTHON, **354 tests / 231.085s**, без skips. Реальный backend: tokenizers 0.22.1, заранее установленный в отдельной temporary environment; tests/runtime не устанавливают dependencies.
- PASS: focused data/helper/packaging 59 tests / 52.879s; после дополнительной race correction targeted negative/positive regeneration 2 tests / 1.753s, затем весь full suite выше на финальном коде.
- PASS: py_compile изменённых runtime/example modules и git diff --check.
- PASS: factory_acceptance.py, 100 samples, local smoke/control plane; p95 0.919ms при lab threshold 100ms. Это не operational SLA.
- Real integration: offline tiny byte-level BPE → collator → batch-consuming CPU unigram fixture → independent NLL protocol. Это не обучение LLM и не scientific benchmark.
- Negative checks: overflow, EOS-only, wrong/missing end, incomplete/length-stop, missing completion, impossible/rounded mixture, actual domain/language floor, fractional repeats, holdout exclusion, source drift, forged receipt, verifier-time mutation, output bound, mode omission и unsupported Modal text; failed data paths сохраняют zero resource attempts.
- NOT RUN: optional skill-creator quick_validate.py — отсутствует PyYAML в default Python. Оба вызова выполнены и завершились dependency error; repository validator и portable packaging checks PASS. Ничего автоматически не устанавливалось ради tests/helper.
- Paid APIs/GPU/Modal launches/model/data downloads: NOT RUN. SDK/provider tests используют fakes. Optional tokenizer wheel установлен только при подготовке development environment до тестов.

## Границы и следующий контекст

Local text backend only. Modal с text config отклоняется до run, существующий non-text Modal покрыт full regression. Нельзя утверждать, что local receipt доказывает содержимое удалённого Volume. Следующая отдельная задача: reviewed remote materialization/hash protocol, без implicit upload/paid smoke.

Реальные лицензии, содержание языка/домена, semantic answer completeness, PII/near contamination, general/domain quality после обучения остаются отдельными review/benchmark gates. Metadata complete=true не семантическое доказательство. Trusted trainer должен читать именно prepared_data batches и выполнять causal shift ровно один раз; generic allowlist не sandbox и не доказательство полного dependency closure.

Failed prep не перезаписывает partial private outputs. Перед retry — подтвердить остановку/known outcome и сохранить failure artifacts; изменение immutable inputs требует reviewed revision и переноса уже потраченного бюджета, без автоматического reset/increase. Все raw shards/token IDs/batches/decision ledgers/checkpoints остаются private, не Git.

Предыдущие изменения пользователя сохранены. No commits/push/deploy.
