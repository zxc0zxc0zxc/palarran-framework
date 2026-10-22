---
id: ml/2026-10-23-data-preparation/0001
status: accepted
date: 2026-10-23
scope: data-preparation
decision_basis: user-request
reuses: [ml/2026-10-20-ml-skills/0001, ml/2026-10-22-runtime-pipeline/0001, backend/2026-10-23-agent-eval/0001]
supersedes: []
superseded_by: []
---
# Data-first planning и bounded local preparation

## Контекст и основание

Пользователь просит инструменты очистки/подготовки и планирование нужных данных на научной базе, с patterns domain/language distribution и сохранением общего/полного ответа. Исследование и docs предшествуют code. Реального датасета/модели/целевых языков в запросе нет.

## Выбор и объяснение

Расширяем existing /ml:data, не создаём дубликат скилла. Отдельные guides: planning, cleaning, joint mixtures, answer integrity, tools, evaluation и dated sources. Stdlib CPU helper profile/prepare/audit-tokens/mix-plan: права/schema/exact dedup/group components/fixed split integrity, bounded tensors audit и decimal quota feasibility. Нет magic ratios, destructive response truncation, bytes-as-tokens, автоматического training/install/download. Unknown rights исключаются, missing joint cell/repeat cap блокируют, нерешённые audits не скрываются.

## Альтернативы

Переносить English heuristics/FineWeb масштабы на любой corpus рискованно; всякий semantic quality score требует task/language calibration. DoReMi требует proxy training и не равен арифметике weights. Универсальный tokenizer либо marker EOS и generic truncation ломают форматы/ответы, поэтому tool проверяет exported actual tensors и lineage, а подлинность tokenizer/collator остаётся отдельным gate. Web-scale near-dedup, PII/LID и streaming engine — documented adapters/future work, не fake implementation.

## Источники и evidence

Primary papers и версии в docs/ml/data/sources.md. Reused current source: ml-data skill, ML contracts/workflow/data, accepted ML ADR, packager/validator/tests. Paper/author results и наши hypotheses/observations различаются. Исследование title проверено: arXiv 2407.01231 оказался MIRAI, в evidence не использован; правильный DCLM 2406.11794.

## Последствия и пересмотр

Tools сохраняют raw text и existing fixed holdout, не создают data/model paid jobs. Joint language/domain quotas и preservation anchors выбираются experiment owner на dev; general/long-answer regression требуется после отдельно разрешённого обучения. Private manifests содержат ID/hash provenance и не коммитятся. Synthetic fixture PASS не model/data quality. Пересмотр после первого разрешённого tokenizer/collator+dataset pilot.

## Применение и проверка

До реализации NOT_RUN. План: ../plan.md; actual verification в ../handoff.md. Offline fixtures: preserved long/code content, unknown rights, duplicate/group bridges, fixed split conflicts, hashes/drift, pad=EOS, masked targets, overlong/incomplete answers, missing tokens, joint quota/cap/floors, private no-overwrite и portable packaging.

Фактически реализовано data-tools-v001: docs/skills/tools/templates/packaging и offline fixtures; 323 full +26 final focused tests PASS. Learning/tokenizer/PII/near-dedup/model outcomes NOT_RUN. Прогресс и объяснения: plan.md, handoff.md, example-report.json.
