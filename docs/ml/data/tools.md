# Локальные инструменты v1

`python3 scripts/ml_data.py --help`. Python>=3.9, только stdlib. Ни downloads, ни tokenization model code, ни сеть, training/GPU/платные APIs не вызываются. Внешние transforms/tokenizer подключаются отдельным reviewed adapter; данные не исполняются. Raw/prepared/tokenized files и индивидуальные hashes — private artifacts, не Git. Outputs explicit, private permissions, no overwrite; при сбое неполный каталог не имеет valid manifest и не training-ready.

## Record schema

UTF-8 JSONL, nonempty lines, strict JSON без duplicate keys/NaN. Каждая запись имеет `id`, `group_id`, `source_id`, `domain`, `language`, `license`, `rights_status`, `rights_approval` и ровно одно из `text`/`messages`; optional `split` из train/validation/test и `completion={complete:bool,finish_reason:stop|eos|authored|length|content_filter|unknown}`. Schema helper сохраняет это утверждение без семантической аттестации; real pipeline gate требует complete=true и stop/eos/authored для messages. Metadata — короткие непустые строки; rights_status approved/unknown/rejected. approved без конкретного approval ref или с license unknown не допускается к use; строка approved — заявление оператора, не юридическая проверка CLI. Unknown domain/language хранить как explicit und/unknown, не заполнять English.

Messages v1: list из role/content (system/user/assistant), optional system только первым, затем чередование user/assistant и завершающий непустой assistant. Tool/function/multimodal/preference schemas не поддержаны; не сплющивать их в plain text без отдельного адаптера. Text whitespace/case/Unicode, messages boundaries и весь answer сохраняются побайтно внутри content strings. Для causal raw docs text подходит; схема не доказывает качество/фактологию.

Лимиты v1: input <=64MiB, line <=1MiB, rows <=100000. Это bounded local dataset helper, не web-scale streaming engine. Symlink (включая alias в parent paths; передавать canonical physical path)/FIFO/unsafe regular files и nested nonfinite JSON отвергаются без вывода содержимого. Не читать dataset за пределами явно разрешённого scope.

## profile

```sh
python3 scripts/ml_data.py profile --input /private/raw.jsonl --output /private/profile-v001.json
```

Читает разрешённый локальный файл: records/bytes/schema validity/rights и observed metadata domain/language, duplicates. Tokens=null: не считает символы токенами, не делает language detection. Raw text/IDs в stdout/report отсутствуют. Research/--plan не вызывает profile без отдельного разрешения читать raw data.

## prepare

```sh
python3 scripts/ml_data.py prepare --input /private/raw.jsonl --config templates/ml/data-prepare.example.json --output /private/prepared-v001
```

Config v1: version=1, seed (явный), split_weights (train/validation/test decimal strings с суммой 1). Все существующие fixed splits сохраняются. Same group и exact content соединяются в компоненты **до** assignment; несовместимые fixed splits внутри компоненты блокируют всю подготовку. Никаких time splits: для time series передать проверенные fixed chronological splits или использовать профильный адаптер.

Schema-invalid/unknown rights/empty/obvious private-key markers исключаются с безопасным reason; duplicate IDs и contradictory fixed splits — fatal до output. Duplicate key — содержимое text/messages, metadata не мешает dedup. Survivor выбирается воспроизводимо по ID, original content не обрезается. Private decisions.jsonl хранит row hashes/причины и provenance исключённых записей без текста. Group components/source refs остаются в private manifest; публичный summary только aggregates. Split counts после dedup могут отличаться от заданных fractions: малые/крупные группы не дробятся ради процентов.

Выход: train.jsonl, validation.jsonl, test.jsonl, decisions.jsonl, manifest.json с input/config/tool/shard hashes, before/after/filter counts и NOT_RUN audits. Нет accepted train data — status blocked. Manifest появляется последним; повторный output не перезаписывается. `verify_prepared()` проверяет shard/ledger digests, schema/rights/IDs, группы, exact duplicates и counts перед token audit.

## audit-tokens

```sh
python3 scripts/ml_data.py audit-tokens --prepared /private/prepared-v001 --tokens /private/unpacked-tensors.jsonl --policy templates/ml/token-audit.example.json --output /private/token-audit-v001.json
```

Производитель локального tokenizer/collator экспортирует одну запись на каждый prepared record: id, record_sha256 (canonical JSON записи включая assigned split), tokenizer_sha256, template_sha256, complete (bool), input_ids, labels, attention_mask, assistant_mask. Все arrays одинаковой длины, integer IDs/masks, **unshifted labels**, unpacked/right-padding only. Policy: version=1, objective=assistant/causal, max_sequence_tokens, end_token_ids, tokenizer_sha256, template_sha256, length_bins (возрастающие положительные int). Pure text не подходит для objective=assistant.

Проверки: полный coverage без unknown/duplicate IDs, binding к prepared/hash policy, complete=true, отсутствие overflow, mask/labels/padding consistency, ненулевые targets и хотя бы один обучаемый non-end token (не только EOS), последний real token — разрешённый supervised end token. Реальный EOS не маскируется по совпадению pad/eos ID. Любая ошибка означает audit FAIL; неисправные/пропущенные записи не исчезают из denominator. Report сохраняет только aggregate issue/slice/histogram counts и hashes, не токены/text/IDs. Изменённые prepared shards не принимаются.

Counts — реально предоставленные tensor IDs/labels, не estimates bytes/4. Но CLI **не доказывает**, что producer действительно применил заявленный tokenizer/template к тексту, и complete=true не доказательство смысловой полноты. `tokenization_verified=false`; независимый local tokenizer/collator inspection остаётся обязательным. Packed/left-padding/shifted layouts требуют другого adapter, а не отключения checks.

## mix-plan

```sh
python3 scripts/ml_data.py mix-plan --audit /private/token-audit-v001.json --recipe templates/ml/data-mixture.example.json --output /private/mix-v001.json
```

Recipe v1: version, total_tokens, seed, cells (domain/language/weight/max_repeats), minimum_domain_shares, minimum_language_shares. Weights и caps — decimal strings, sum(weights)=1. Только observed train cell tokens: validation/test не inventory. Largest-remainder allocation даёт целые квоты с суммой total_tokens; empty support/cap overflow/floor violation блокируют план, без перенормировки/заимствования holdout. Report содержит missing tokens, effective passes, source audit hash и explicit remaining gates. Это allocation plan, не sampler и не запуск обучения.

Toy templates — проверка формата/арифметики, **не рекомендованные доли** русского/английского или general/specialist. Audit file хранить immutable и pin его hash в experiment; semantic authenticity external report — trust boundary, не подпись независимого checker. Перед training заново проверить prepared/token/source hashes и actual sampler/collator по [evaluation](evaluation.md).
