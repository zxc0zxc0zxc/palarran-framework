---
id: product/2026-10-19-bounded-mvp/0002
status: accepted
date: 2026-10-19
supersedes: []
superseded_by: []
---
# Cleanup PermissionError и проверенный compare prefix

## Контекст и основание
New runf87a2c24a5194d8891e4483248da1b65 created complete compare manifest. Supervisor exception PermissionError at runner.py:67 (os.killpg), receipt162500tokens/$0.2445270 lower bound, no terminal receipt persisted. Process-name inventory shows no remaining provider/bridge. Exact phase/group absence at historical syscall is not retrospectively proven. Original pinned compare verifier PASS0355e109c1e3e21b6d386d658bc87850fd4b2ce641cf526b081f9a0b9201d054; prefix/draft guards PASS.

## Выбор и объяснение
Handle PermissionError only if root poll confirms exit AND read-only /bin/ps group inventory proves process group absent. Otherwise re-raise/fail closed. No signal permissions bypass, fallback elevation or assumption that denial means success. Unknown old attempt stays unknown; no billing reconciliation from artifact success.

Import verified define/market/compare in new workflow, model stages only revenue/acquisition/mvp. Carry compare reserve210000tokens/$0.50 (original new allocation, not observed lower bound). Remaining new allocation exactly2.47USD/1.04m tokens; combined11.9974214USD/5m unchanged. No repeat/probe for compare or earlier stages.

## Альтернативы
Ignore all PermissionError — can leave live descendants. Re-run compare — waste and unauthorized repetition. Reconcile unknown from manifest — artifacts are not billing telemetry. Give another budget — prohibited.

## Последствия и пересмотр
Cleanup failure with active root/group or unproven inventory still blocks progress. /bin/ps is platform dependency used only after denial + root exit, finite timeout and strict numeric snapshot. Child exiting before pipe drain must not lose terminal output when absence is proven. Remaining product work never starts before independent prefix acceptance.

## Источники и evidence
Private result numeric receipt + safe exception site; read-only local process inventory; independent pinned artifact verifier and draft guard. POSIX process-group semantics underpin recommendation; no vendor billing inference.

## Применение и проверка
Fault tests: exited+absent succeeds; active/root group/uncertain inventory re-raises; real subprocess drains full terminal despite mocked group PermissionError. Full offline suite, validator/factory acceptance after runtime change. New immutable runtime archive; existing source skill snapshot unchanged.
