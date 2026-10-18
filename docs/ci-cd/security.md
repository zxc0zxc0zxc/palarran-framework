# Security: секреты, доверие и supply chain

## Trust boundaries

| Уровень | Разрешено | Запрещено |
|---|---|---|
| Fork/untrusted PR/MR | Lint/tests с synthetic secrets, ограниченный read source, отдельный cache scope | Prod identities, trusted cache write, registry release publish, private management runners |
| Reviewed protected source | Build/test candidate, publish в разрешённый registry | Автоматическое полномочие менять любой environment |
| Promotion controller/job | Проверить eligibility и изменить конкретный environment contract | Выполнять arbitrary scripts из выбранного user ref с deploy credentials |
| Runtime deploy controller | Применить разрешённый manifest локально/через scoped API | Получать команды shell из CI input, обслуживать произвольные registry/repositories |

CI config, reusable workflows/includes, Dockerfiles и environment registry — исполняемая часть supply chain: CODEOWNERS/review, pinned trusted refs и branch protection. Не разрешать автору app change самому отключать обязательный policy gate. Основание — [Microsoft governed templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates); provider mechanisms выбираются отдельно.

## Identity

Использовать OIDC/federation при наличии provider поддержки: ограничить issuer, audience, repository/project ID, protected ref, environment и trusted workflow claims по возможностям trust policy. `id-token: write` само по себе не ограничивает cloud роль нужным окружением. Если federation нет — короткий scoped app/deploy token с rotation и expiry, никогда SSH private key к target.

Build получает registry publish только на свой image; promotion — право изменить только свой environment/path; runtime — pull и нужные secret refs. Отдельные identities dev/test/prod. Нет долгоживущего cluster-admin kubeconfig в CI. Секреты приложения обычно извлекаются runtime secret provider, не проходят через build job.

## Никаких секретов в выводе

Запрещены `set -x`, debug trace/service debug при secrets, `env/printenv`, dump contexts, `curl -v` с auth, вывод response bodies без allowlist, логирование команд с password/token в argv, `.env`/kubeconfig/IaC plan upload. Также проверить test assertions, exception stacks, HTTP recording, SQL connection strings, Composer/npm/pip auth errors и application startup output.

Masking в [GitHub](https://docs.github.com/en/actions/reference/security/secure-use) и [GitLab variables](https://docs.gitlab.com/ci/variables/) — дополнительный слой; преобразованный, фрагментированный или намеренно выведенный секрет может его обойти. Mask runtime-generated credentials **до** использования, но не печатать их намеренно даже для проверки masking. Передавать credentials через provider credential helper/защищённый file mount/standard input там, где интерфейс поддерживает; исключать из artifacts и очищать ephemeral workspace.

Reports тоже данные: JUnit, coverage HTML, Playwright trace/screenshots/videos, service logs, core dumps могут содержать токены и PII. Synthetic accounts/data; redaction, restricted artifact access и retention; без dump всего workspace по `always()`. Контролировать exception messages и sanitization, не только console. Если инструмент безопасно не фильтрует данные, ограничить capture или отключить чувствительный capture с альтернативной диагностикой.

Build secrets подавать через [BuildKit secret mounts](https://docs.docker.com/build/building/secrets/), не Docker `ARG`/`ENV` или copied auth files. Mount не спасает от вредоносного `RUN`, который копирует секрет в слой или пишет в stdout. Private dependency installs — отдельная reviewed trust boundary; lockfile scripts/plugins способны выполнять код. Credentials на чтение private packages минимальны и не доступны forks.

## Integrity артефакта

Проверить source commit, builder/workflow identity и inputs, image digest, SBOM и vulnerability policy, provenance/signature. Создание attestation без проверки перед deployment не является enforcement. [GitHub attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) — возможная реализация; для GitLab выбрать совместимый signer/verifier, не предполагать идентичность механизмов.

Сканировать и зависимости, и итоговый runtime image; severity/fix availability/исключения с owner+expiry заданы policy. Не заменять build test только CVE scanner. Trusted release publish не потребляет неподтверждённые executables/artifacts/cache из непроверенного PR. Container build без privileged runner предпочтителен; если выбран Docker-in-Docker с privileged, явно обосновать изоляцию отдельного ephemeral pool и запрет prod network.

## Приёмка и реагирование

До включения реальных secrets прогнать synthetic sentinel только в изолированном harness: инструменты используют фиктивное значение нормальным путём; сканер проверяет logs/reports/cache/image history и layers, включая диагностические failure paths и известные encoding patterns. Не писать sentinel специально в public job output и не выводить совпавшие строки scanner-ом: только file/job ID и тип утечки. Это тест известных путей, не математическая гарантия отсутствия любого covert channel.

Negative tests: fork не получает deploy identity; неверные audience/ref/env не проходят IAM; неизвестный env и чужой registry/release отвергаются; debug capture с секретами блокируется; неподписанный/неeligible digest не разворачивается; prod config change требует нужного reviewer; cache poisoning не пересекает trust scope.

При утечке: отозвать/ротировать credential → остановить доступ/выпуски из затронутой identity → ограничить/удалить чувствительные logs/artifacts/cache по provider процедуре → определить доступ и затронутые releases → повторная проверка. Удаление строки из YAML не отзывает уже опубликованный секрет.
