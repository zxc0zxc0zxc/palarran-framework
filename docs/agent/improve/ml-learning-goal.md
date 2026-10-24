# Первый кейс: чему именно учим

Основание — пользовательское замечание 2026-10-24: skill проверял masks/loss/техническую механику, но сначала требовалось зафиксировать desired learned behavior и проверить, что actual selected targets обучают ему. Это user_report, не восстановленный historical trace. Числа старого эксперимента, cause-of-degradation и usage здесь не подтверждены. Не запускать training ради воспроизведения ошибки процесса.

Existing candidate на момент authoring workspace: docs/ml/learning-contract.md и seven ML skill changes уже присутствуют в workspace. Не переписывать/публиковать параллельный SFT controller. Candidate proposal: цель learn/preserve/evaluate/non-goals до recipe, content+actual target exposure audit до launch-ready. Технический mask PASS остаётся полезным, но не заменяет audit. Scope learning-contract и его ML mandatory guides читать при фактической правке; эта страница не разрешает новые paid ML runs.

Regression oracle проверяет структурированное решение planner о readiness и traceability, не наличие слова «goal» в SKILL.md. Минимальные development cases:

| Case | Input | Required observable outcome |
| --- | --- | --- |
| long_input_short_target | Нужны полные решения, длинные inputs, только короткие реакции в scored targets | blocked, mismatch reason + goal ID; не launch-ready на основании input length |
| goal_missing | «Обучи как надо», data технически корректны, desired behavior не задано | needs_clarification, не выдумать цель/recipe |
| short_confirmation | Цель коротких подтверждений, корректные short targets | ready в пределах evidence; не требовать длинных ответов/hidden reasoning |
| no_data_access | Цель задана, содержимое/actual exposure недоступны | not_run/blocked audit; можно conditional planning, нельзя launch-ready |
| preserved_ability | Меняем style, reasoning нужно сохранить, demonstrations не добавляют new reasoning | preservation tests нужны; отсутствие hidden CoT само не blocker |

В tests есть независимый `ml_goal_grader`: отклоняет технически зелёный, но не покрывающий goal план; принимает correct blocked и valid ready controls; проверяет минимальные goal/evidence links. Это calibration на synthetic fixtures, **не полноценный semantic grader и не измерение, что текущая модель следует новому skill**. Review обязателен для смысла цели, actual content/sample sufficiency, temporal/domain slices. Исторический reproduction, model A/B и tokens/cost savings NOT_RUN до разрешённого парного запуска. Existing candidate diff можно получить из точной предыдущей revision и checked current bytes; не включать raw data/чужие SFT изменения.

Standalone proposal и его apply/validator/package evidence сохранены в task handoff ai-tools. В clean checkout само наличие этого кейса не означает, что ML proposal уже применён: перед приёмкой сверить actual files/revision; не применять diff повторно поверх существующего candidate.
