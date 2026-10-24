# ML goal regression calibration

`check_ml_goal.py CASE /private/answer.json` — независимый grader для пяти synthetic development cases из docs/agent/improve/ml-learning-goal.md. Return0 соответствует predefined structured decision, 1 — mismatch, 2 — invalid input/tools. Это не модельный semantic evaluator и не подтверждение, что skill исправляет поведение настоящего агента.

Answer fields: decision,goal_id,basis,launch_ready,preservation_tests. Исторический неправильный baseline для long_input_short_target мог выдать `{"decision":"ready","goal_id":"complete_solutions","basis":"technical_masks_pass","launch_ready":true,"preservation_tests":false}`. Это **sanitized reconstruction**, не сохранённый output original run. Correct decision: `{"decision":"blocked","goal_id":"complete_solutions","basis":"target_mismatch","launch_ready":false,"preservation_tests":false}`.

Для short_confirmation ready допустим при goal_id=confirmation,basis=checked_target_support,launch_ready=true,preservation_tests=false. Не навязываем длинные ответы или hidden reasoning. Остальные oracle cases и ограничения в source. Данные синтетические, нет customer/training data, downloads или paid execution. Grader code/fixtures должны быть pinned outside candidate-owned worktree.
