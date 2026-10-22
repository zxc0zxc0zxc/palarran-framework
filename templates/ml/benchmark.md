# Benchmark protocol and report

Template: все metrics unknown до actual evaluation. Protocol freeze предшествует final test.

- Protocol ID/revision/hash / predeclared date / task/H-IDs:
- Checkpoint hash / base+adapter or exported artifact hashes:
- Source commit/patch / image/dependencies / tokenizer/template/config:
- Dataset/split/corpus hashes / contamination audit/access policy:
- Baseline/model selection rule / seeds / all tried variants:
- Primary metric/direction/threshold/practical delta / guardrails:
- N/sampling unit / uncertainty method/level / paired comparison:
- Required edge/OOD/slices / judge rubric/version/calibration if used:
- Hardware/precision/batch/concurrency/input-output lengths:
- Cold/warm / model-only/end-to-end / timing synchronization:
- Independent evaluation command / exit / safe evidence refs:
- Total/evaluated/failed samples, missing policy / failed seeds:

| Gate | Metric/unit | N/basis | Baseline | Candidate | Interval/delta | Threshold | Evidence/state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary | unassigned | unknown | unknown | unknown | unknown | proposed | not_run |

Verdict: not_run. Acceptance требует все обязательные gates; partial не accept. Actual evaluation cost/provider/unknown reserves; limitations и ADR. Изменение model/data/protocol инвалидирует затронутые PASS. Production SLA/market success/publication не проверены.
