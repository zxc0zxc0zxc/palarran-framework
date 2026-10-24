# Local tools v1

`python3 scripts/ml_data.py --help`. Python>=3.9, stdlib only. No downloads, tokenization-model code, networking, training/GPU/paid APIs. External transforms/tokenizers require separately reviewed adapters; data is never executed. Raw/prepared/tokenized files and individual hashes are private artifacts, not Git contents. Explicit outputs, private permissions, no overwrite; a failed incomplete directory lacks a valid manifest and is not training-ready.

## Record schema

UTF-8 JSONL, nonempty lines, strict JSON without duplicate keys/NaN. Every record has `id`, `group_id`, `source_id`, `domain`, `language`, `license`, `rights_status`, `rights_approval` and exactly one of `text`/`messages`; optional `split` is train/validation/test and `completion={complete:bool,finish_reason:stop|eos|authored|length|content_filter|unknown}`. The schema helper retains this assertion without semantic attestation; the real pipeline gate requires complete=true and stop/eos/authored for messages. Metadata consists of short nonempty strings; rights_status is approved/unknown/rejected. Approved without a specific approval ref or with license unknown cannot be used; approved is an operator assertion, not CLI legal review. Preserve unknown domain/language as explicit und/unknown, never fill with English.

Messages v1: a role/content list (system/user/assistant), optional system first only, then alternating user/assistant and a final nonempty assistant. Tool/function/multimodal/preference schemas are unsupported; do not flatten them into plain text without a separate adapter. Text whitespace/case/Unicode, message boundaries and the whole answer remain byte-exact within content strings. Text suits causal raw documents; the schema proves neither quality nor factuality.

v1 limits: input <=64MiB, line <=1MiB, rows <=100000. This is a bounded local dataset helper, not a web-scale streaming engine. Reject symlinks (including parent-path aliases; supply canonical physical paths)/FIFO/unsafe regular files and nested nonfinite JSON without printing content. Do not read datasets beyond explicitly authorized scope.

## profile

```sh
python3 scripts/ml_data.py profile --input /private/raw.jsonl --output /private/profile-v001.json
```

Reads an authorized local file: records/bytes/schema validity/rights, observed domain/language metadata and duplicates. Tokens=null: characters are not tokens; no language detection. Raw text/IDs do not enter stdout/reports. Research/--plan does not invoke profile without separate authorization to read raw data.

## prepare

```sh
python3 scripts/ml_data.py prepare --input /private/raw.jsonl --config templates/ml/data-prepare.example.json --output /private/prepared-v001
```

Config v1: version=1, explicit seed, split_weights (train/validation/test decimal strings summing to 1). Preserve all existing fixed splits. Same groups and exact content join components **before** assignment; incompatible fixed splits inside one component block the entire preparation. No time splits: for time series provide verified fixed chronological splits or a specialist adapter.

Exclude schema-invalid/unknown-rights/empty/obvious-private-key-marker records with safe reasons; duplicate IDs and contradictory fixed splits are fatal before output. Duplicate keys use text/messages content; metadata must not prevent deduplication. Choose survivors reproducibly by ID without truncating original content. Private decisions.jsonl stores row hashes/reasons and excluded-record provenance without text. Group components/source refs remain in private manifests; public summaries contain aggregates only. Post-dedup split counts may differ from fractions: never split small/large groups to hit percentages.

Outputs: train.jsonl, validation.jsonl, test.jsonl, decisions.jsonl, manifest.json with input/config/tool/shard hashes, before/after/filter counts and NOT_RUN audits. No accepted training data means blocked. Write the manifest last; never overwrite an existing output. `verify_prepared()` verifies shard/ledger digests, schema/rights/IDs, groups, exact duplicates and counts before token auditing.

## audit-tokens

```sh
python3 scripts/ml_data.py audit-tokens --prepared /private/prepared-v001 --tokens /private/unpacked-tensors.jsonl --policy templates/ml/token-audit.example.json --output /private/token-audit-v001.json
```

The local tokenizer/collator producer exports one row per prepared record: id, record_sha256 (canonical record JSON including assigned split), tokenizer_sha256, template_sha256, complete (bool), input_ids, labels, attention_mask, assistant_mask. All arrays have equal lengths, integer IDs/masks, **unshifted labels**, unpacked/right-padding only. Policy: version=1, objective=assistant/causal, max_sequence_tokens, end_token_ids, tokenizer_sha256, template_sha256, length_bins (increasing positive integers). Plain text cannot use objective=assistant.

Checks: full coverage without unknown/duplicate IDs, prepared/hash-policy binding, complete=true, no overflow, mask/label/padding consistency, nonzero targets and at least one trainable non-end token (not EOS alone); the last real token is an authorized supervised end token. Do not mask real EOS merely because pad/eos IDs match. Any error means audit FAIL; broken/missing records stay in the denominator. Reports preserve aggregate issue/slice/histogram counts and hashes only, not tokens/text/IDs. Reject changed prepared shards.

Counts are actually supplied tensor IDs/labels, not bytes/4 estimates. However, the CLI **does not prove** that the producer applied the claimed tokenizer/template to text; complete=true does not prove semantic completeness. `tokenization_verified=false`; independent local tokenizer/collator inspection remains mandatory. Packed/left-padding/shifted layouts need another adapter, not disabled checks.

## mix-plan

```sh
python3 scripts/ml_data.py mix-plan --audit /private/token-audit-v001.json --recipe templates/ml/data-mixture.example.json --output /private/mix-v001.json
```

Recipe v1: version, total_tokens, seed, cells (domain/language/weight/max_repeats), minimum_domain_shares, minimum_language_shares. Weights/caps are decimal strings, sum(weights)=1. Observed train-cell tokens only: validation/test are not inventory. Largest-remainder allocation creates integer quotas summing to total_tokens; empty support/cap overflow/floor violations block the plan, without renormalization/holdout borrowing. Report missing tokens, effective passes, source-audit hash and explicit remaining gates. This is allocation planning, not a sampler or training launch.

Toy templates test format/arithmetic; they are **not recommended shares** of Russian/English or general/specialist data. Keep audit files immutable and pin their hash in the experiment; external-report semantic authenticity is a trust boundary, not an independent checker's signature. Recheck prepared/token/source hashes and actual sampler/collator before training per [evaluation](evaluation.md).
