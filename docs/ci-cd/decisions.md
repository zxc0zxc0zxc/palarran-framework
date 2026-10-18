# Решения, которые будущий скилл обязан обсудить

ADR содержит вопрос, проверенные факты, допущения, варианты, выбранный вариант, первоисточник, нашу адаптацию, стоимость/риск, owner, acceptance и условие пересмотра. Стартовые направления ниже не заменяют intake.

| Вопрос | Предпочтительный старт | Когда другой вариант разумен | Основание |
|---|---|---|---|
| Kubernetes или managed API или VM pull | Сохранить существующий поддерживаемый backend без SSH | Новый backend только при явной потребности/стоимости/bootstrap | [AWS automation](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html), наша topology |
| Полный suite или affected | Full release gate; validated dependency selection для PR feedback | Выборочный release gate только после evidence/ADR/shadow full | [Meta selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/), не копируем их ML автоматически |
| Один build или variants | Один digest между стендами, runtime config | Неустранимые build-time differences требуют отдельных проверенных variants | [Google release](https://sre.google/sre-book/release-engineering/), [Next env](https://nextjs.org/docs/app/guides/environment-variables) |
| Manual кнопка или auto promotion | Выбор проекта; один общий deploy contract | Prod approval, freeze или отдельный gate по риску/политике | [Google canary](https://sre.google/workbook/canarying-releases/); manual ≠ authorization |
| Recreate, rolling, blue-green или canary | Rolling при capacity и совместимости, явный downtime для single-instance | Canary при достаточном трафике/метриках; blue-green при подходящих data/session contracts | [Netflix ACA](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69), наши thresholds |
| Canary при малом трафике | INCONCLUSIVE, более длинное окно/synthetic checks или другой gate | Не выдавать отсутствие метрик за зелёный результат | [Google canary](https://sre.google/workbook/canarying-releases/) |
| Где runners | Ephemeral build pool, отдельный trusted management observer | Self-hosted только с maintenance/isolation/capacity owner | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use), [GitLab security](https://docs.gitlab.com/ci/pipeline_security/) |
| Насколько агрессивный cache | Deps/compiler/framework-native cache с trust scope | Более сложный remote task cache при доказанной полноте inputs | [Docker cache](https://docs.docker.com/build/cache/backends/), stack guides |
| Общие pipeline blocks или копипаста | Versioned reusable policy/provider layer + stack scripts | Исключение с owner/expiry, не бесконтрольный fork всех checks | [Microsoft governance](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) |
| Secrets в CI или runtime | Runtime retrieval; CI получает только минимальные build/deploy identities | Private package fetch временно требует scoped secret в reviewed build stage | [BuildKit secrets](https://docs.docker.com/build/building/secrets/), [GitLab variables](https://docs.gitlab.com/ci/variables/) |
| DB migrations и rollback | Serialized expand/contract; old/new совместимы | Destructive migration как отдельная согласованная операция с recovery | [AWS testing/rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html); source не гарантирует обратимость данных |
| GitHub/GitLab tier не даёт нужного gate | Описать недостающий enforcement и рабочую альтернативу | External promotion policy или изменение тарифа | Provider environment docs; не обходить требование через cosmetic button |

## Отдельные blockers

Нет trusted deployment controller/API; неизвестен production target/arch; отсутствует current environment config; нет разрешённой identity; pipeline может исполнять arbitrary selected ref с секретами; отсутствует release evidence; данные необратимо меняются без recovery; не определён owner failed deployment. Эти случаи не исправляются fallback на SSH или отключением gate.

Неизвестные timings сами по себе не блокируют документацию/проектирование, но блокируют утверждение о достигнутом ускорении. До measurements performance budgets называются целями. Политика разрешённых auto deploy events и approvals фиксируется один раз в проекте; повторные запросы в чате на каждый разрешённый pipeline run не нужны.
