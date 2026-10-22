# Data readiness и независимая проверка

До launch: frozen data/model/tokenizer/template/config/transform hashes, права/consent, train-only preprocessing, group/duplicate separation, реальные domain/language/length/sources counts, full-response/loss mask/EOS/collator checks и реализуемый mixture plan. Missing cell/unknown rights/tokenization не превращать в ноль или «готово».

| Gate | Минимальная evidence | Если нет |
| --- | --- | --- |
| Rights/provenance | source register + approval evidence + exclusions | blocked use; research candidate допустим |
| Split/leakage | exact/group assertions, near/translation/benchmark audit scope | exact-only ≠ leakage-free; remaining audit NOT_RUN |
| Content/labels | sampled annotation/quality review по slices, disagreement | schema-valid ≠ factual/correct |
| Privacy | локальный профильный scan и review; controlled storage | marker scan ≠ PII-free |
| Tokens/answers | actual tokenizer/template/collator tensors, unmasked targets/end tokens, no truncation | inventory token counts unknown; no ready mixture |
| Mix feasibility | joint quotas, floors, repeats, source/length review и realized sampler test | planned, а не sampled |
| Regression | base/adapted domain+general frozen suite, per-language metrics, N/uncertainty | training/quality benefit NOT_RUN |

Independent data verification повторно читает manifest+shards, проверяет digests, exact group/duplicate constraints и tokenized record bindings. Изменение raw/prepared/tokens/policy инвалидирует downstream audit/plan. Script report — арифметика/контракт, не самоаттестация dataset author. Token IDs/producer flags не доказывают соответствие исходному тексту без проверки local tokenizer/template pipeline.

Сначала дешёвые schema/golden fixtures, затем ручной audit и только разрешённый tokenizer/collator smoke, после этого разрешённый tiny pilot/learning curve; дорогие сеты/LLM judges/GPU не следуют из data skill. Unit tests нашего CLI — только synthetic CPU fixtures, не научная репликация paper. Финальное улучшение проверяется `/ml:benchmark`/`/agent:eval` по frozen applicable protocol; деньги и прежние unknowns сохраняются в existing runtime, новый data helper их не обнуляет.

Сохранять prep status, все reasons/counts и список NOT_RUN; rejected rows не исчезают из denominator. В target memory только safe aggregates/private refs. Data artifacts/IDs/token arrays могут раскрывать raw text и принадлежат private store; token IDs тоже не анонимизация.
