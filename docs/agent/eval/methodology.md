# Методика и качество

По [Anthropic evals](sources.md) заранее описать поведение, наблюдаемый outcome и grader, затем проверить grader на хорошем и заведомо плохом решении. Из реальных failures пополнять development suite; frozen holdout не использовать для few-shot или подбора порогов.

Категории: plan (контракты, edge cases, DoD), build (реальный код + тесты), review (найденные проблемы и ложные срабатывания), context (ответы из заданных исходников). Для каждого case точные пути/формат ответа, входы и недопустимые действия сообщаются агенту; ожидаемые ответы в evaluator bundle не являются частью prompt. Логическое разделение grader и candidate не обеспечивает конфиденциальность grader от враждебного процесса на том же хосте.

JSON exact grader годится для структурированного результата, а не оценки красоты текста. Command grader — доверенный executable + pinned external scripts; он обязан проверять поведение, regression/edge cases, не собственную строку PASS агента. Не хранить grader в candidate-owned worktree. Exit 0 означает check pass; ненулевой exit wrapper 1 означает mismatch, 2 — invalid/drift/infrastructure. Secrets/raw stdout/reasoning в report не включать.

Перед admission freeze suite/revision/prompts/checks/pins; runtime фиксирует baseline, модели/effort, policies, context receipts и workflow digest. До и после command grader сверять pinned bytes. Final повтор всех checks и subject fingerprint защищает от позднего drift. Одинаковая среда важна по [исследованию infrastructure noise](sources.md); CPU/RAM/network sandbox этот runtime не обеспечивает. Для недоверенных candidates нужен внешний sandbox.

Знаменатель — все frozen cases, включая NOT_RUN. PASS только после финальных gates на неизменном subject; failed checks не исчезают из статистики. Timeout/crash/unknown usage и stale evidence = INCONCLUSIVE, не качество FAIL и не бесплатный расход. v1 fail-fast: после первой ошибки оставшиеся cases NOT_RUN; это отражается coverage, не превращается в полный benchmark.

Для model trials менять только заявленную переменную. Повторы — заранее выделенные запуски с общим бюджетом/carry, без best-of-N selection. Публиковать N, все outcomes, requested model/effort, context/cache, лимиты и окружение. v1 compare допускает только одинаковые protocol/baseline/environment; выдаёт описательную разницу, не значимость/причинность. Одного smoke недостаточно для model routing.

Стоимость берётся из runtime ledger: provider_reported или pinned rate_card_estimate, не invoice и не процент подписки. Все failed attempts входят в расход; unknown остаётся null с observed lower bound. Cost-per-pass = расход всей suite / число PASS, только при полном учёте и >0 PASS. Время: отдельные execution и grader seconds, сумма всех финальных проверок, elapsed (включает ожидание); это не provider billing duration и не production SLA.
