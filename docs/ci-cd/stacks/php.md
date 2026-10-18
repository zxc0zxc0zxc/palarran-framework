# PHP

Определить composer manifests/workspaces, framework (Laravel/Symfony/другое), PHP version/extensions, PHP-FPM/CLI/long-running workers, DB/queue/migrations и существующие test commands. HHVM/Tupperware исторических статей Meta не является основанием навязать проекту другой runtime. Общие аргументы — [фактура](../evidence.md).

## DAG и воспроизводимость

| Ветка | Содержание | Практика |
|---|---|---|
| Validate/style | `composer validate --strict`, pinned formatter в check-mode, syntax checks по scope | Не менять файлы автоматически в required job |
| Static analysis | PHPStan или существующий Psalm, стабильный baseline policy | Полный анализ с штатным result cache, не только changed files |
| Unit/integration | PHPUnit; ParaTest при доказанной изоляции | Real DB/queue для границ, отдельные resources на worker |
| Coverage | Выделенный required/scheduled scope согласно policy | Xdebug/PCOV только где нужен; не замедлять все jobs |
| Dependencies | Composer audit и отдельная runtime image policy | Lockfile, PHP/extensions compatibility, исключения с expiry |
| Candidate | Production deps + app container + startup/HTTP/worker smoke | Не выкатывать test vendor directory |

В CI `composer install`, не `composer update`. Dev dependencies нужны тестам/analysis, production stage — `--no-dev` и оптимизированный autoload после проверки совместимости. `--no-interaction --prefer-dist` полезны для автоматизации; plugins/scripts review обязателен. `--no-scripts --no-plugins` — опция отдельного dependency stage, если последующие необходимые действия вызваны явно; слепое отключение ломает framework setup. Команды и [platform checks/audit](https://getcomposer.org/doc/03-cli.md) адаптируются к pinned Composer и приложениям.

Нельзя применять `--ignore-platform-reqs` ради зелёной сборки. Проверить actual runtime extensions/ABI/libc, а не только `config.platform` при разрешении lock. Composer auth file/token не сохраняется в image/cache; trusted package download stage и plugins не получают prod secrets.

## Оптимизация

Cache Composer downloads с PHP/Composer/lock/trust metadata; кеширование `vendor` требует строгих platform/config keys и повторной валидации, оно не default вместо install. Изоляция cache writer от fork MR/PR.

[PHPStan result cache](https://phpstan.org/user-guide/result-cache) использует dependency analysis: сохранять стабильный полный список paths и version/config/lock inputs, не передавать только git diff. Это конкретный пример безопасной оптимизации анализа без уменьшения охвата.

[ParaTest](https://github.com/paratestphp/paratest) требует проверки совместимости PHPUnit и тестов. Worker/process token использовать для DB/schema, Redis namespace, temp files и ports. Глобальные fixtures и shared test user могут ломать параллелизм. Число workers подбирать по CPU/RAM/connection limits, не «все ядра» без измерений.

[PHPUnit coverage](https://docs.phpunit.de/en/12.4/code-coverage.html) зависит от driver; pin подходящую версию PHPUnit под runtime проекта, не обновлять проект до 12.4 только из-за ссылки. Coverage reports объединять с проверкой полноты shard set; instrumentation выключена в обычных быстрых jobs, где она не требуется.

## Production semantics

Один image включает production deps и versioned source, а secrets/DSN приходят runtime. Для Laravel/Symfony проверить framework config/container cache: не запекать dev/prod secrets в build cache или generated PHP files. Если config cache зависит от environment, генерировать безопасно при startup/revision initialization с реальным runtime config, без dump его содержимого. Это наша адаптация под выбранный framework; перед реализацией прочитать version-specific framework docs.

Web и queue workers обновляются согласованно; old/new versions должны понимать сообщения и schema в переходном окне. Миграция — отдельная идемпотентная serialized операция через runtime/controller API; не выполняется одновременно каждой PHP-FPM replica. OPcache/worker lifecycle привязать к immutable replacement/restart, не remote `git pull`.

Rollback: предыдущий digest + совместимые config/schema/queue contracts. Destructive migration и необратимые side effects требуют отдельного recovery plan. No SSH/scp/rsync/remote composer install.

## Provider mapping и приёмка

GitHub/GitLab orchestration из общих guides, test scripts одинаковы локально и в CI. Release stage не переиспользует vendor artifact из untrusted pipeline. Проверки: framework boot с production deps; extension compatibility; DB migration и rollback compatibility; worker restart/drain; cold/warm cache timing; отсутствие race при ParaTest; отсутствие credentials в exception/test reports, generated config и layer history. Показать, какой шаг экономит время и как измерено, не обещать benchmark без target.
