# Тесты edge cases и integrated DoD

Прочитать source [test matrix](../plan/testing.md), AC/invariants/contracts/reliability/DoD и реализовать **каждый in-scope critical case**. Сначала fast domain/unit/contract checks, затем реальные DB/driver/schema integration, concurrency/fault/recovery/load где запланировано; обязательный suite проекта не пропускать ради скорости. Tests должны проверять observable/durable outcomes, а не копировать implementation structure.

| Группа | Actual evidence |
|---|---|
| Inputs/state/auth/tenant | Positive/negative/boundary и запрещённые переходы; отсутствие запрещённого side effect |
| Idempotency/concurrency | Controlled duplicate writers/interleavings, key/payload conflict, final DB invariant, unknown outcome after commit |
| DB/migration | Actual constraints/isolation/driver, old/new coexist, backfill checkpoint/restart/reconcile, lock/space limits по source |
| Async/dependencies/cache | Retry/cancel/deadline/crash timing, duplicate/order/replay, stale/cold/unavailable/stampede cases по applicability |
| API/integration | Настоящий route→auth→domain→DB/dependency→response и read-back/reload, если результат должен сохраняться |
| Performance/recovery | Source workload/thresholds, saturation/correctness, bounded failure sandbox, restore/reconciliation/RTO/RPO где required |

Для каждого T-ID записать command/tool/version/environment/data, expected и actual outcome, subject commit, safe evidence и PASS/FAIL/NOT_RUN. Нет backend/service/tool/credentials — NOT_RUN с blocker, не считать mock equivalent. Reference [Google testing overview](https://abseil.io/resources/swe-book/html/ch11.html) помогает различать уровни; наши gates задаются feature risk/source plan, не универсальным coverage процентом.

После интеграции task commits обязательно запускать affected suites и cross-module/end-to-end checks на integration HEAD. Lane PASS на другой branch недостаточен. Regression от позднего dependency change инвалидирует affected checks/tasks и отражается в [progress](../progress.md), а не остаётся зелёным.

Исправить вызванные изменениями дефекты и повторить failed/affected checks, сохраняя историю failure/fix. Existing unrelated failures отделить по baseline evidence. Не бесконечно retry flaky tests до случайного PASS: найти источник, сделать deterministic/isolation fix или оставить blocker с причиной. Arbitrary sleeps, disabled assertions и обновлённые snapshots/thresholds не замена исправлению.

## DoD gate

Каждый task: scope implemented, integrated commit известен, required checks PASS на его subject commit и reviewed changes. Фича: все in-scope tasks verified, traceability R/AC/INV/C→TASK/T полная, integrated required suite/security/data/edge/reliability/recovery gates выполнены по source. Сравнить planned и actual code/contracts, перечислить deviations и ADR. Нет operational SLA evidence — operational acceptance pending, даже если local implementation проверен.

Не путать local implementation verified, release-ready, operational SLA met и deployed. [Build verification template](../../../templates/backend/build-verification.md) сохраняет эту границу. Plan checkboxes и helper structural success не заменяют фактический DoD.
