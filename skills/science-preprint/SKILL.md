---
name: science-preprint
description: Создать LaTeX отчёт-статью по существующим экспериментам с проверяемыми результатами, ссылками, ограничениями и claim-to-evidence. Использовать для /science:preprint; без обучения и публикации.
---

# /science:preprint {experiment/report paths}

Сначала прочитай [README](../../docs/science/README.md), [sources](../../docs/science/sources.md), [evidence](../../docs/science/evidence.md), [workflow](../../docs/science/workflow.md) и [decision-memory](../../docs/skills/decision-memory.md). Разреши installed checkout отдельно от target. Прочитай target README/AGENTS, INDEX, принятые решения, experiment/protocol/data/model/config/benchmark и отчёты всех попыток. Отсутствующие результаты не запускать автоматически.

Зафиксируй question/hypothesis, baseline, protocol revision, selection policy, seeds/N/splits, units/denominators, compute/cost basis и gaps. Каждое утверждение свяжи с exact artifact/hash и evidence pointer; self-consistent report не доказывает независимость оценки. Related work ищи по первичным работам, проверяй metadata и применимость; не выдумывай citations/DOI, novelty, авторов, significance или успешные результаты. Partial/negative/failed runs остаются видимыми. Development probes не heldout benchmark. Не вставляй private outputs без разрешения на их раскрытие.

Создай отдельный target LaTeX project с main.tex, tables/figures/references и evidence register. Для нового проекта используй доступный create_latex_project, если этот инструмент есть; иначе создай dedicated folder без overwrite. При наличии runtime report начни с `python3 scripts/science_preprint.py --report /private/report.json --output /private/preprint-v001`; это data-only draft, затем дополни объяснение по evidence. Используй [нейтральный шаблон](../../templates/science/main.tex) и [claim register](../../templates/science/claim-evidence.md). Приложи реальные графики из записанных наблюдений, честные сравнения baseline, полные ограничения и AI assistance disclosure. Не дорисовывай отсутствующие точки или доверительные интервалы.

Компилируй доступным built-in/local compiler без shell escape и автоматических установок; исправь ошибки в источнике, просмотри PDF доступным renderer. Missing compiler/viewer = NOT COMPILED / NOT VISUALLY REVIEWED. Успешная компиляция не подтверждает научные выводы. В portable package нет runtime/compiler: используй helper для source и явно отметь недоступные проверки.

До зависимых изменений запиши rationale/альтернативы/источники в target `.ai-development/science/<task>/decisions/`, обнови INDEX, coverage и handoff. Полные samples/state/checkpoints остаются private; в Git только разрешённые редакторские artifacts. Финал: source/PDF paths, scope/results/limitations, scientific checks, compile/visual status и remaining evidence. Не отправляй статью, не публикуй artifacts и не делай новые paid runs по этому вызову.
