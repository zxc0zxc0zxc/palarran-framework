# Независимая проверка

До implementation freeze user tasks, tool selection expectations, required outcomes и negative cases. По [Anthropic cases](sources.md) проверяй реальное достижение задачи, не только argument shape. Calibrate grader на good/bad/boundary; сохранение прежних tasks при правке tool — через /agent:eval и /agent:improve contracts. Не открывать скрытый holdout fixer и не объявлять development case независимым holdout.

Минимум: initialization/list/call wire, schemas/unknown fields/types/Unicode/empty/not-found/errors, required IDs, deterministic ordering/pagination/stale cursor, output bytes/completeness, denied access/timeout/unknown mutation по actual scope. Для SDK — actual installed SDK client interoperability отдельно от raw JSON-RPC lab. Для business integration — API/DB postconditions и /app:verify где применимо, не просто exit0.

Reference tests поднимают настоящий subprocess без модели/сети/SDK, проверяют compact vs detailed bytes и full get. Это protocol/fixture evidence; model tool selection, task reasoning, token/cost gains, production auth and host support NOT_RUN. В отчёте tool/source revision, cases/denominator, attempts, elapsed/bytes, missing dependencies/checks и explicit limits. Не подменять missing error/server failure пустым успешным списком. Бюджет/исторический unknown сохранять; paid evaluation не разрешается самим вызовом skill.
