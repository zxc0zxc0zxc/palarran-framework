---
id: ml/2026-10-23-diagnostics-runtime/0002
status: accepted
date: 2026-10-23
scope: science-preprint
decision_basis: user-request
reuses: [ml/2026-10-23-training-debug-design/0001]
---
# Evidence-backed LaTeX preprint

## Контекст и основание

Пользователь просит новый science:preprint. Сначала scientific reporting docs, потом skill/helper/template.

## Выбор и объяснение

Portable science namespace: исследовательская статья по существующим experiment/diagnostic/benchmark artifacts с claim→evidence index, uncertainty, negative results, disclosure и limitations. Offline helper детерминированно экспортирует safe TeX/CSV/manifest из report, экранирует текст, не исполняет source LaTeX и не придумывает refs/авторов/выводов. Skill расширяет narrative только по проверенным материалам и настоящим sources; отсутствие evidence остаётся explicit draft. Optional runtime export после terminal report не запускает AI/GPU. Compile через доступный локальный/built-in compiler, no shell escape/auto install; source-only честно NOT COMPILED.

## Альтернативы

Красивый текст без traceability создаёт ложную научную уверенность. Автопубликация/выдуманные citations не разрешены. Venue-style копирование не обязательно: neutral article draft с отдельной адаптацией под venue.

## Источники и evidence

NeurIPS Paper Checklist и arXiv TeX submission guide, inspected 2026-10-23. ACM URL 403 и arXiv llm policy недоступны — не использовать как прочитанные основания. Research integrity и no fabricated results — existing project contract.

## Последствия и пересмотр

Generated TeX draft не peer-reviewed result/publication; автор/affiliation human-supplied. No claim independent verification без evidence. Samples private, публикационная версия требует redaction review. Optional compilation не равна scientific verification.

## Применение и проверка

Escaping/path/hash/partial-results/export/packaging tests, synthetic local LaTeX smoke где доступен compiler. Результат реализации и проверок: см. [handoff](../handoff.md).
