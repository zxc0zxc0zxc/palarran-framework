# Одинаковая задача: полный source и Graphify

Дата: 2026-10-22. Одна контрольная пара, requested model **gpt-6-luna / low**, две ephemeral no-tools sessions. Стенд содержит byte-identical реальный orchestrator/ml_resources.py и одинаковые root/module AGENTS для обеих arms. Baseline передаёт весь source; Graphify — свежие связи и четыре source excerpts. Это controlled context-delivery canary, не полноценный implementation/tool-search benchmark.

| Метрика | Полный source | Graphify | Разница |
| --- | ---: | ---: | ---: |
| Actual input tokens | 24 723 | 22 095 | −2 628 / −10.63% |
| Cached input tokens | 12 544 | 12 544 | одинаково |
| Output tokens | 35 | 35 | одинаково |
| Reasoning output tokens | 0 | 0 | одинаково |
| Total tokens | 24 758 | 22 130 | **−2 628 / −10.61%** |
| Context bytes | 22 970 | 11 176 | размер текста, не usage |
| Cost по pinned conservative rate card | $0.002712930 | $0.002187330 | −19.37%, не invoice |
| Independent exact JSON rubric | PASS | PASS | четыре одинаковых корректных поля |

Usage взят из cumulative App Server receipts, terminal completion подтверждён; final independent commands и unchanged subject fingerprint PASS. Cached counters равны, output одинаков; это усиливает сопоставимость данной пары, но n=1 не даёт статистической гарантии для других задач/порядка/моделей. Base system/host context также входит в actual counters, поэтому уменьшение retrieval bytes нельзя считать равным уменьшению total tokens.

## Бюджет

Прежний combined потолок **$11.9974214 / 5 000 000 tokens** сохранён. Исторические **13 unknown** перенесены неизменно. Пара заранее ограничена **$0.04 / 60 000 tokens**, max calls 2, retries 0; фактически **46 888 tokens / $0.004900260** по rate card. Свободный scheduling reserve после пары: **$0.111553140 / 52 204 tokens**. Речь о worker pipeline budget, не стоимости текущего чата, invoice или проценте подписки. Actual aggregate historical billing остаётся unknown.

Старый BOUNDED-MVP-BUDGET.json не перезаписан. Новый private CONTEXT-COMPARISON-BUDGET.json содержит прежний carry плюс две complete receipts. Повтор той же budget snapshot запрещён даже при JSON reformat; никакого третьего вызова или нового лимита.

Числовой отчёт с hashes и публичными refs: [comparison.json](comparison.json). Public final JSON — только результаты рубрики; hidden reasoning/raw model logs не сохранялись.
