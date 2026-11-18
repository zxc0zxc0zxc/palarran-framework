# Reproducible bounded experiments

Read the [audit](MARIN_ADOPTION_AUDIT.md), [architecture](ML_ARCHITECTURE.md) and existing [text runtime contract](data/pipeline.md). Use an already installed tokenizer backend for real tokenization; never install/download dependencies as part of a test.

## Prepare a reviewed dataset

The `prepare` command remains `python3 scripts/ml_data.py prepare --input /private/source.jsonl --config /private/split.json --output /private/new-prepared`. Output must not exist. Use only data you are authorized to process. Text/chat record schema, complete targets and full-output boundaries are unchanged.

The optional split recipe extension is:

```json
{
  "version": 1,
  "seed": 73,
  "split_weights": {"train": "0.8", "validation": "0.1", "test": "0.1"},
  "provenance": {
    "version": 1,
    "processing_version": "identity-v1",
    "sources": [{
      "source_id": "owned",
      "upstream": "https://example.org/owned-corpus",
      "revision": "owned-snapshot-v1",
      "license": "CC0-1.0",
      "rights_status": "approved",
      "rights_approval": "owner-review-v1",
      "allowed_uses": ["training", "evaluation"],
      "status": "active",
      "ingested_at": "2026-11-18T00:00:00Z"
    }],
    "protected_benchmarks": [{
      "benchmark_id": "final-v1",
      "revision": "snapshot-v1",
      "payload_sha256": ["REPLACE_WITH_CANONICAL_PAYLOAD_SHA256"]
    }]
  }
}
```

The fingerprint placeholder is deliberately invalid. Compute fingerprints locally with `scripts.ml_data.digest(scripts.ml_data.payload(record))` on authorized benchmark examples using exactly the same text/chat payload schema. Keep the fingerprint catalog private; no benchmark examples enter agent prompts. Hash matching ignores record/source IDs but preserves exact content. Protected examples in train or validation block preparation; test-only occurrences are allowed. An empty catalog is explicit no-coverage/NOT_RUN, never clean-benchmark evidence.

Every valid source record must match one registry entry, its license/approval and allowed split use. `status=withdrawn|blocked`, nonapproved rights and unknown sources block rather than silently quarantine. Source metadata is asserted operator evidence, not independently verified legal permission. Combine relevant sources in one input to dedup across them. Preparation does not query other previously prepared directories.

Review manifest identity, provenance, document lineage and overlap/dedup counts. `prepared_requires_review` is not permission to train. Call `scripts.ml_data.verify_prepared(directory)` to independently reread manifests/shards and check lineage. Never edit an existing dataset in place; changed data, revisions or recipes require a new output and reviewed experiment revision.

## Use the existing ML runtime

Put this same split recipe into `data_preparation.split` of the existing local text execution policy. The compiler pins its bytes; `ml-prepare` consumes it, emits the provenance/lineage artifacts and the independent gate regenerates them. Existing data/tokenizer/config stage lineage still needs `preparation_sha256`. The fit task receives the exact prepared packet only after approval, verified preparation and budget gates. Failure or source drift yields zero trainer launches; retries do not reset expenditure.

For benchmark output, optional `failures` is an object with exactly `model`, `invalid_output`, `scoring`, `infrastructure`, `timeout`, each a nonnegative integer. `sample_count` is the attempted evaluation-unit denominator; sum of failures cannot exceed it. Count one mutually exclusive terminal class per failed unit. Any scoring/infrastructure/timeout yields `inconclusive`. Quality failures must already be reflected by task-specific metrics; do not filter them out to improve scores. Legacy reports retain their previous semantics and do not claim classified failures.

## Offline validation and smoke

```sh
python3 -m unittest tests.test_ml_provenance -v
python3 -m unittest tests.test_ml_data tests.test_ml_data_gate tests.test_ml_pipeline -v
python3 scripts/validate_repo.py
python3 scripts/factory_acceptance.py
```

The provenance tests include a complete stdlib preparation/audit/mixture round trip on owned fixtures, source revision changes, protected-data rejection, metadata tampering and policy revocation. Existing `RealDataGateTest` exercises actual tokenization, collator, CPU unigram training and baseline/candidate evaluation when `AI_TOOLS_TOKENIZER_PYTHON` points to an existing compatible environment. Without it those tests SKIP, never fake PASS. The unigram is pipeline plumbing, not an LLM experiment or a Marin quality replication. Remaining semantic/privacy/near-overlap review and real target training/restore remain explicit missing evidence.

The owned CPU unigram smoke is directly reproducible with `python3 -m unittest tests.test_ml_provenance.ProvenanceTest.test_complete_cpu_unigram_comparison_and_reproducible_experiment_record -v`. It executes the existing `text_job.py` trainer/evaluator with explicit byte-encoded fixture batches and verifies actual checkpoint/protocol/output files, while supplying a synthetic planning envelope. It saves a private experiment record (inputs, seed, config, source hash, runtime, CPU backend, metrics, time and checkpoint) inside its isolated test directory. This is neither production tokenizer acceptance nor full managed orchestration acceptance. `ProvenanceRuntimeTest` separately covers the real managed gate when its preinstalled optional backend exists.
