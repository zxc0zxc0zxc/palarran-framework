# Подготовка текста в ML runtime

Сначала читать [источники](sources.md), [integrity](answer-integrity.md), [mixtures](mixtures.md) и [runtime contract](../pipeline-contract.md). Основания: Karpathy — проверить реальные данные; DoReMi/XLM-R — контролировать exposure и языки; HF — model-native template и корректные labels. Наш bounded adapter не воспроизводит результаты этих работ.

## Контракт запуска

Новый execution policy обязан задать `data_mode=text|non_text`. `text` требует `data_preparation`; `non_text` запрещает text config. `data_preparation` содержит: absolute canonical `python`, `source`, `tokenizer`, `template`, `split`, `mixture`; `tokenizers_version`; `objective=assistant|causal`, `max_sequence_tokens`, `end_token_ids`, `pad_token_id`, `batch_size`, `length_bins`, `max_share_deviation` (decimal string), `max_output_bytes`. Compiler фиксирует SHA каждого файла, Python executable и исполняемых файлов optional tokenizers distribution; missing dependency — ошибка до run. Пакет не содержит credentials. Interpreter должен уже иметь указанную версию optional `tokenizers`; runtime/tests ничего не устанавливают и не скачивают. `python` должен быть настоящим executable, не symlink; обычный venv/python symlink нужно разрешить заранее до canonical path.

Stage data/tokenizer/config lineage JSON каждый содержит `preparation_sha256` = canonical SHA frozen policy (включая files pins). Это связывает plan с реальными входами, не позволяет заменить recipe после approval. Context содержит эту policy как metadata для planning agents, raw corpus в prompt не попадает. Старые сохранённые workflow без mode: legacy/not_configured; новые non_text: not_applicable. Ни один из этих статусов не PASS. Для text training выбирать этот контракт явно.

После семи planning stages: operator approval точного prefix → `ml-prepare` → verified data → fit → evaluate → final verification. Подготовка deterministic, локальная и bounded существующими task/run wall time; reserves AI/train/evaluate и общий USD ceiling не меняются. Source/tokenizer/config drift и missing dependency — FAIL до запуска тренера. Новый запуск при неизвестном расходе по-прежнему требует reconciliation.

## Реальный tokenizer и collator

`tokenizer.json` загружается через `tokenizers.Tokenizer.from_str` из проверенного byte snapshot local tokenizer.json (семантика соответствует from_file), без Hub. Padding/truncation tokenizer отключены, special tokens уже в template, `add_special_tokens=False`. Literal template JSON: `version=1`, `bos`, `text_suffix`, `roles` с ровно system/user/assistant, каждый `{prefix,suffix}`. Template должен быть сверён с native model contract; произвольные Jinja/tool/multimodal layouts не поддержаны. Для каждой messages-записи требуется completion={complete:true,finish_reason:stop|eos|authored}. Отсутствие claim, length/content_filter/unknown блокируются до добавления EOT; authored означает проверенный автором полный export, не автоматически выставленный default. Assistant suffix обязан завершаться supervised end token. Никакого универсального EOS ID или шаблона по умолчанию.

Единый rendered string кодируется целиком, offsets относят токены к assistant content+suffix. Токен, пересекающий границу prompt/assistant, zero-length offset, UNK и потеря содержательных target tokens — blocker. Никакого тихого truncation/packing. Полный текст ответа не режется, но semantic completeness источника всё ещё требует review: добавление EOT не лечит уже оборванный raw ответ.

Collator возвращает batches `input_ids`, `attention_mask`, `assistant_mask`, `labels` и `ids`. Right padding по длине, labels=-100 на pad и non-assistant при SFT. При pad_id==eos_id реальный end сохраняет loss. Labels unshifted: trainer обязан делать ровно один causal shift. Все train/validation/test записи токенизируются и проверяются; mixture использует только train.

## Фактическая смесь и evidence

Source JSONL и split recipe — [tools schema](tools.md). Сначала exact dedup/group splits, затем encode/audit всех survivors. Любой quarantine кроме exact_duplicate блокирует gate: плохую запись нельзя незаметно исключить. Existing [mixture recipe](mixtures.md) задаёт joint domain/language input-token quotas. Deterministic seed сортирует whole examples; запись не режется для попадания в quota. Repeat ceiling на запись = floor(max_repeats); дробная верхняя граница не даёт дополнительного повтора. Общий недобор exposure и отклонения shares допустимы только при явно заданном `max_share_deviation`; actual cell shares, domain/language floors проверяются по реально материализованным input tokens. No holdout borrowing и no silent fallback. Нулевой exposure cell с positive weight — FAIL, даже при округлении quota до нуля. После отбора deterministic shuffle по occurrence перемешивает домены, а не выдаёт целые domains блоками; per-batch exact shares не гарантируются. Hard limits: source/output ≤64MiB, total encoded и padded tokens ≤1 млн, requested mixture ≤1 млн input tokens, context ≤8192 tokens, batch ≤32, JSONL line ≤1MiB. Quotas не заполняются обрезанными answers. Max requested tokens/outputs bounded; для крупных корпусов нужен отдельный streaming adapter.

Private state `prepared-data/` хранит shards/decision ledger/token rows/train+holdout batches/audit/mixture/receipt. Independent verifier в отдельном bounded процессе заново читает pinned source, выполняет prepare/encode/collate/sampling и сравнивает exact bytes. До resource reservation gate сверяет private stable verifier receipt с digest всех файлов; перед actual launch — повторно. Fit/evaluate получают JSON `prepared_data` с directory, hashes и receipt digest. Trusted trainer обязан читать именно batches оттуда; внешняя произвольная программа остаётся trust boundary, hash не доказывает обучение на файле.

## Пределы

Local text backend only. `backend=modal` с data_preparation отклоняется до run: remote dataset materialization и проверка содержимого Volume пока не реализованы. Legacy Modal execution не изменён. No cloud calls, no model weights downloads, no paid tests. Gate PASS означает механическую целостность/смесь/lineage, не юридическую экспертизу лицензии, язык по содержанию, PII audit, semantic quality, отсутствие forgetting или качество обученной модели. Frozen benchmark остаётся обязательным.

## Локальная проверка optional adapter

Dependency устанавливается оператором отдельно; runtime/tests не делают install. `AI_TOOLS_TOKENIZER_PYTHON=/absolute/canonical/python python3 -m unittest tests.test_ml_data_gate -v` использует уже существующую среду с `tokenizers==0.22.1`. Без неё real integration tests честно SKIP/NOT RUN, stdlib checks работают. Fixture создаёт tiny byte-level BPE локально, без Hub/corpora downloads. Сквозной example text_job — CPU unigram, не LLM и не доказательство отсутствия forgetting.

Пример входной config: [data-preparation.example.json](../../../templates/ml/data-preparation.example.json). Пути/версии/EOS/template — placeholders для конкретной модели, не готовый preset. В execution policy добавить data_mode=text и объект data_preparation из шаблона; actual review/pins создаёт compiler. Нужные model-native special tokens уже должны существовать в tokenizer vocabulary.

```mermaid
flowchart LR
  P[Hypotheses → plan → model → data → cost → train plan → benchmark protocol] --> A[Exact-prefix approval]
  A --> D[ml-prepare: split → real encode → collator → whole-example mix]
  D --> V{Independent regeneration PASS?}
  V -->|Нет| S[STOP: zero trainer launches]
  V -->|Да| F[fit: exact prepared_data packet]
  F --> B[Independent benchmark + final rerun]
```

Failure recovery: failed preparation не перезаписывает существующий private каталог. Сначала проверить known outcome/остановку процесса; partial artifacts сохранять для диагностики. Изменение frozen inputs требует новой reviewed revision с переносом уже израсходованного бюджета, не автоматического retry/reset ceiling.
