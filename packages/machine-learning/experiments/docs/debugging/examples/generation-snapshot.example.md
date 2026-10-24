# generation-snapshot — design JSON template

Status: NOT RUN / design-v001. Not a runtime-accepted schema; fill null explicitly wherever a field is applicable.

```json
{
  "schema_version": "design-v001",
  "artifact_type": "ml-generation-snapshot-template",
  "measurement_status": "not_run",
  "run_id": null,
  "attempt_id": null,
  "segment_id": null,
  "snapshot_id": null,
  "optimizer_update": null,
  "consumed_target_tokens": null,
  "subject": {
    "model_sha256": null,
    "checkpoint_ref": null,
    "tokenizer_sha256": null,
    "template_sha256": null,
    "decoding_sha256": null,
    "probe_set_sha256": null
  },
  "samples": [
    {
      "probe_id": "synthetic-json-completeness",
      "domain": "structured-output",
      "language": "en",
      "input_messages": [
        {
          "role": "user",
          "content": "Return a JSON object with a title and exactly three steps for checking a backup restore."
        }
      ],
      "rendered_input_ref": null,
      "rendered_input_sha256": null,
      "input_tokens": null,
      "generation_seed": null,
      "output": {
        "private_text_ref": null,
        "private_token_ids_ref": null,
        "sha256": null,
        "generated_token_count": null,
        "storage_status": "not_run",
        "full_output_preserved": null
      },
      "finish_cause": "unknown",
      "finish_evidence_ref": null,
      "validator_results": [],
      "expected_behavior": "Valid JSON with all three substantive steps; correctness/completeness require versioned rubric, not length alone."
    }
  ],
  "comparison": {
    "baseline_snapshot_ref": null,
    "previous_snapshot_ref": null,
    "matched_basis": null
  },
  "remaining_checks": [
    "bind_exact_subject",
    "generate_within_approved_budget",
    "persist_full_observable_output",
    "evaluate_versioned_rubric"
  ]
}
```
