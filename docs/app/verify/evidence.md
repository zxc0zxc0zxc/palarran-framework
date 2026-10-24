# Evidence, баги и privacy

Отчёт связывает suite/protocol digest, source files/revision, live identity before/after, run/entity correlation, actual browser engine/version/runtime pins, case/R-ID, step outcome/seconds, required/missing/N/A surfaces и artifact hashes. Verdict только по выполненному scope. JSON/MD summaries не включают response bodies, DB rows, console text, credentials/cookies/env dumps. Внутренние exceptions — только enum/class, без str(exception) с URL/PII.

Screenshot opt-in, фиксированный viewport, private local file with SHA. Captured != viewed != approved; внешний человек/agent должен реально открыть изображение и записать review subject/ограничения. V1 не исполняет автоматический эстетический grader, не пишет trace.zip/auth state. Существующие Playwright traces допустимы лишь в конкретном разрешённом private workflow после privacy review, без public upload.

Report artifact hash — consistency receipt, не подпись независимого нотариуса. Trusted evaluator и suite separation — assumptions. Публичная defect карточка содержит минимальный sanitized repro и predicates, private evidence refs вместо raw customer content. Model evaluation/skill quality и product business validation отдельны от deterministic fixture/browser assertions.

При cancellation/crash/timeout сохраняется intent/частичный отчёт; unknown mutation не становится «ничего не произошло». Не повторять этот run. Operator проверяет реальные effects и актуальную среду до нового сценария. Report после source/artifact tamper = stale/INCONCLUSIVE; не re-run ради чтения отчёта.
