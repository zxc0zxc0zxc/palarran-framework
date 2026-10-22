# diagnostics-policy — design JSON template

Status: NOT RUN / design-v001. Не runtime-accepted schema; null требует явного заполнения там, где поле applicable.

```json
{
  "schema_version": "design-v001",
  "artifact_type": "ml-diagnostics-policy-template",
  "execution_status": "not_run",
  "task_profile": "causal-sft",
  "configuration_status": "needs_project_values_and_calibration",
  "subject_refs": {
    "experiment_revision": null,
    "data_preparation_sha256": null,
    "model_sha256": null,
    "tokenizer_sha256": null,
    "template_sha256": null,
    "protocol_sha256": null
  },
  "metrics": [
    {
      "id": "dev/target_nll",
      "basis": "unregularized_autoregressive_after_shift",
      "unit": "nats_per_scored_token",
      "reduce": "sum_nll/sum_actual_scored_targets"
    },
    {
      "id": "dev/ppl",
      "basis": "same_as_dev/target_nll",
      "unit": "perplexity",
      "reduce": "exp(global_mean_nll)",
      "primary": false
    },
    {
      "id": "dev/task_success",
      "basis": "versioned_task_validator",
      "unit": "fraction",
      "reduce": "successes/evaluable_with_failure_policy"
    },
    {
      "id": "probe/length_stop",
      "basis": "fixed_paired_probes",
      "unit": "fraction",
      "reduce": "confirmed_length_stop/evaluated",
      "unknown_finish_policy": "report_separately"
    }
  ],
  "heuristics": [
    {
      "id": "H-DBG-INTEGRITY",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "stop_training",
      "calibration_ref": null,
      "rule_kind": "assertion",
      "predicate_ref": "invalid_data_or_lineage",
      "threshold_status": "not_applicable_exact_predicate"
    },
    {
      "id": "H-DBG-FINITE",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "stop_training",
      "calibration_ref": null,
      "rule_kind": "assertion",
      "predicate_ref": "nonfinite_objective_gradients_or_parameters",
      "threshold_status": "not_applicable_exact_predicate"
    },
    {
      "id": "H-DBG-BUDGET",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "stop_training",
      "calibration_ref": null,
      "rule_kind": "limit",
      "threshold_ref": "existing_runtime_budget_and_deadline_policy"
    },
    {
      "id": "H-DBG-STALL",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "reconcile",
      "calibration_ref": null,
      "rule_kind": "statistical_or_deadline"
    },
    {
      "id": "H-DBG-OBSERVABILITY",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "request_review",
      "calibration_ref": null,
      "rule_kind": "statistical_or_deadline"
    },
    {
      "id": "H-DBG-REGRESSION",
      "required": true,
      "version": 1,
      "threshold": null,
      "window": null,
      "min_support": null,
      "action": "block_acceptance",
      "calibration_ref": null,
      "rule_kind": "statistical_or_deadline"
    }
  ],
  "schedule": {
    "scalar_update_interval": null,
    "validation_update_interval": null,
    "generation_update_interval": null,
    "max_wall_gap_seconds": null,
    "checkpoint_update_interval": null
  },
  "generation": {
    "probe_manifest_ref": null,
    "probe_digest": null,
    "baseline_required": true,
    "decoding_config_ref": null,
    "decoding_sha256": null,
    "max_new_tokens": null,
    "seed": null,
    "full_output_required": true,
    "terminal_if_budget_allows": true,
    "final_test_access": false
  },
  "storage": {
    "private_root_ref": null,
    "retention_policy_ref": null,
    "max_bytes": null,
    "max_records": null,
    "allow_external_upload": false
  },
  "budget": {
    "authority": "existing_runtime_ledger",
    "diagnostic_compute_reserve_usd": null,
    "storage_reserve_usd": null,
    "max_overhead_fraction": null,
    "increase_ceiling": false
  },
  "terminal_report": {
    "start_stub_before_dispatch": true,
    "coordinator_recovery": true,
    "generate_with_existing_artifacts_only": true,
    "launch_gpu_during_finalization": false,
    "partial_report_on_missing_evidence": true
  }
}
```
