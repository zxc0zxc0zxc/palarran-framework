# Source baseline, progress и resume

Найти план по пути/ID аргумента либо target backend index; несколько подходящих ревизий — конкретный вопрос, не первый файл. Прочитать foundation/spec/contracts/test matrix/reliability/tasks/DoD, context/ADR и текущую реализацию. Зафиксировать plan ID/revision/source commit, contract/schema revision, target code HEAD и dirty/untracked changes. Source plan-ready не означает выполненный foundation: task prerequisites могут требовать bootstrap до feature.

Если foundation/contracts содержат blocking unresolved choices, вернуться к плановым уточнениям для зависимой части; независимые ready tasks продолжать. Новый build не разрешает менять stack/бизнес/SLA threshold ради простоты. Spec delta — proposed/accepted по реальному основанию, новая revision/impact map, обновление tasks/tests/DoD. Не делать вид, что реализована старая revision без deviations.

Инициализировать либо прочитать canonical ledger и source plan section по [progress](../progress.md). Для старого плана без markers добавить выделенный execution section, сохранив semantic contents; для отсутствующего ledger составить все TASK IDs из source, а не только удобные. Helper запускается на source ledger вне plugin cache. Нет write доступа к source plan — явно сообщить blocker синхронизации, сохранить safe локальный report, не утверждать «план обновлён».

Перед повторным запуском проверить evidence на actual code: сообщения previous agent/old PASS — claims до проверки commits/artifacts и scope. Не переписывать чужие dirty changes, не объявлять их своим implemented commit. Если checkout содержит unrelated work, выбрать suitable isolated integration checkout по project policy; in-scope dirty edits должны быть явно включены в frozen base или аккуратный scoped patch, не потеряны и не коммитить постороннее.

На каждом событии обновлять ledger и **сам plan**: dispatch→in_progress, code handoff→implemented, принятие в integration→integrated, actual checks→verified, issue→blocked или regression state. Сохранять task/plan revision/evidence/commit, причина оставшегося. Coordinator один пишет shared progress/index; child agents возвращают task reports в своих worktrees.
