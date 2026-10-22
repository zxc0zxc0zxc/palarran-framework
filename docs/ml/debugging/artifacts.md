# Данные диагностики и хранение

Читать [контракты](../contracts.md), [data gate](../data/pipeline.md), [metrics](task-metrics.md). [MLflow](https://mlflow.org/docs/latest/ml/tracking/) показывает разделение parameters/metrics/artifacts; здесь задаём tracker-independent private contract. Перенос в W&B/MLflow не заменяет локальную durability и не разрешает upload.

## Private структура logical run

```text
run/
  manifest.json                 # immutable subject, config, source + diagnostics policy hashes
  lifecycle.jsonl               # coordinator events, attempts/stop/recovery
  attempts/<attempt>/
    segments/<segment>/
      metrics/<writer>.jsonl
      heuristics/<writer>.jsonl
      validations/<eval-id>/receipt.json
      generations/<snapshot-id>/manifest.json
      generations/<snapshot-id>/samples.jsonl
    terminal.json
  checkpoints/<digest>/manifest.json
  reports/<revision>/report.json
  reports/<revision>/report.md
  reports/<revision>/plots/
  latest-report.json            # atomic pointer + hash, previous revisions retained
```

Это design schema, не существующая SQLite/filesystem layout runtime. Raw/tokenized corpora не дублировать: manifest ссылается на проверенный private data bundle/digest. В Git target `.ai-development` — decisions, progress, sanitized aggregates и safe refs; samples, prompt IDs, per-example labels и checkpoints private. IDs/хеши не считаются анонимизацией.

## Что сохраняем

| Слой | Обязательные данные | Когда / зачем |
| --- | --- | --- |
| Identity | experiment/run/attempt/segment, plan/source/dirty-patch/image/dependency/hardware/model/tokenizer/template/data/config/protocol hashes, seeds | До старта; exact reproduction и сравнимость |
| Optimizer progress | microbatch, optimizer update, effective batch, accumulation, unique/consumed examples, input и supervised target tokens, LR, optimizer/scaler state ref | На запланированном интервале; skipped update не считать выполненным |
| Learning | отдельно objective и unregularized task loss; NLL sums/counts, validation receipt, loss reduction/units, regularization components где применимо | Train windows и validation; разные objectives не сливать |
| Stability | grad norm pre/post clip, clipping threshold/fraction, AMP scale/skip/overflow counters, nonfinite counts, zero-gradient/zero-update diagnostics | По profile/cadence; optimizer.apply и skipped differentiate |
| Data exposure | actual domain/language/class/length counts и token shares, repeat/unique exposure, padding/skipped/corrupt counts, sampler state digest | За window + cumulative; requested mixture отдельно от факта |
| Quality | primary + guardrails/slices, support, failures/unevaluable, uncertainty и evaluator version | Каждый planned dev evaluation; final heldout отдельно |
| Behavior | fixed prompt/output pair, rendering/decoding/checkpoint hashes, generation length/finish status, validity/correctness rubric | До train и по snapshot cadence; [полный контракт](generations.md) |
| Compute / reliability | monotonic elapsed, step/data-wait/eval/checkpoint/generation time, throughput useful tokens/s, memory peaks, provider/heartbeat/checkpoint state | Scalar windows + lifecycle events; gaps видимы |
| Money | ссылки на existing attempt receipts/reserves; estimated/provider-reported/invoiced, measurement time, unresolved | Не второй финансовый ledger и не средняя цена из головы |

Distributed: rank-local writers и один designated aggregator, никаких concurrent appends в общий файл. Rank норм/throughput aggregation объявляется; глобальный metric либо reduce sufficient statistics, либо versioned merge. Не складывать per-rank и уже global counts повторно. Gradient norm semantics для sharded/ZeRO/FSDP требуют framework-aware global computation, локальная shard norm так и подписывается. Activation/gradient histograms, top-k token scores, confusion matrices/residuals — bounded opt-in artifacts; полные logits/activation dumps/checkpoint на каждом шаге не default.

## Metric/event envelope

Каждая запись: `schema_version`, run/attempt/segment, writer, монотонный writer-local sequence, UTC, monotonic elapsed, microbatch/update/consumed-target counters, split, metric ID/version, value status, units/reduction/window, numerator/denominator/support где применимо, subject/protocol hashes, evidence ref. Validation также eval ID, checkpoint exact subject, expected/evaluated/failed counts и sampling policy. Event identity tuple `(run,attempt,segment,writer,sequence)`; duplicate byte-equivalent delivery идемпотентна, conflicting replay — corruption. Это diagnostic identity, не замена существующих resource receipt sequence rules.

Смена optimizer/data/decoding/protocol basis — новый revision/segment, не незаметное продолжение кривой. Resume от checkpoint не удваивает consumed counters: сохранять logical progress и отдельно physically processed tokens за все attempts. UTC не использовать как единственный порядок; restart/replay/gaps размечать явно.

`value_status=observed|estimated|missing|nonfinite|invalid|not_applicable`. JSON только finite numbers/null; NaN/Inf не сериализовать. При nonfinite сохранить null + safe enum kind и diagnostic event; не заменять нулём и не объявлять missing PASS. Nonfinite learning signal доходит до stop controller отдельным typed event, даже если scalar transport принимает только finite numbers. Missing target denominator означает invalid metric.

## Durability, приватность, лимиты

Append-only chunks со checksum/length, manifest публиковать atomic rename после полной записи. Interrupted trailing line отмечается truncated/corrupt, не успешно прочитанной записью; сохранять hash исходного damaged chunk и evidence gap. Canonical report ссылается только на завершённые chunks. Checkpoint manifest — commit marker после проверки всех файлов; weights-only не exact-resume state. Checkpoints/snapshots с одинаковым digest не копировать заново ради каждого poll.

До запуска задать retention/access/encryption, предел bytes/records/sample length/histogram bins, max event frequency и storage/evaluation/generation reserves. Overflow storage — recorded failure и stop/review по policy; не молчаливое удаление плохих samples или обрезка ответа. Секреты/env/provider raw logs/неразрешённые данные не сохранять. Raw private outputs допускаются только в approved storage; публичный report получает redacted presentation с отдельным digest и пометкой преобразования. Если samples нельзя сохранять — explicit unresolved requirement до обучения, не отчёт с выдуманными outputs.
