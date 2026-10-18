# Фактура: откуда берутся решения

Дата чтения — 2026-10-18. Практики компаний ниже описаны их авторами; исторический материал не доказывает, что внутренние инструменты или процессы остались прежними. Конкретный DAG, thresholds, названия файлов и комбинации инструментов в этом репозитории — наша адаптация.

| Компания и первоисточник | Наблюдение авторов / принцип | Наше применение | Чего источник не доказывает |
|---|---|---|---|
| [Google: Release Engineering](https://sre.google/sre-book/release-engineering/) | Версионированная автоматизированная сборка, идентификация release и контролируемые действия | Pin toolchains/dependencies, release manifest и self-service deployment | Наши builds автоматически hermetic или byte-for-byte reproducible |
| [Google: Canarying Releases](https://sre.google/workbook/canarying-releases/) | Ограниченный rollout с оценкой поведения версии | Health/SLI gates, понятный abort и rollback | Одинаковые bake time и пороги подходят всем сервисам |
| [Google Testing: Just Say No to More E2E](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Нужный сигнал часто дешевле получить более узким тестом | Unit/component/integration coverage плюс небольшой critical E2E suite | Можно заменить все интеграционные проверки mocks или убрать E2E |
| [Google Testing: Flaky tests](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html) | Размер и сложность тестов связаны с нестабильностью; flaky сигнал требует работы | Метрики flake rate, изоляция ресурсов и ограниченный quarantine с владельцем | Retry до зелёного исправляет баг |
| [Meta: Predictive test selection](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | У Meta выбор подмножества тестов опирался на обученную модель и проверку качества сигнала | Начинаем с dependency-aware affected tests, затем сверяем с full suite | Простые path filters имеют ту же полноту, что их ML-система |
| [Meta: Rapid release](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) | Частые изменения требуют автоматизации и наблюдения за регрессиями | Небольшие releases, traceability, диагностика и ownership | Каждому проекту нужна их частота релизов или тот же branching model |
| [Netflix: Kayenta](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69) | Сравнение baseline/canary по метрикам позволяет автоматизировать оценку | Для подходящего трафика progressive delivery и автоматический stop | Обязательно ставить Spinnaker/Kayenta или считать пустые метрики успехом |
| [Microsoft: Governed pipeline templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) | Общие шаблоны закрепляют security checks и контролируемую гибкость | Общие versioned provider templates + небольшие stack adapters; policy нельзя отключить флагом приложения | Их Azure DevOps templates прямо переносятся в GitHub/GitLab |
| [AWS: Automated changes](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html) и [testing/rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html) | Документированные AWS рекомендации автоматизировать deployment, проверки и восстановление | API/GitOps/pull вместо shell-сессии на host; rollback как часть flow | Это рассказ о внутреннем pipeline всех команд Amazon; Kubernetes обязателен |

## Что фиксируем как собственные архитектурные решения

1. Стабильный release ID содержит source commit, image digest, test evidence, toolchain/lockfile fingerprints и policy version. Promotion переносит тот же артефакт, а не пересобирает его для каждого стенда.
2. Предпочтительный Kubernetes deploy — pull GitOps. Для managed runtimes — deployment API с короткой identity. Для одной VM — заранее настроенный узкий pull-agent, а не CI runner с root на production.
3. `dev/test/prod` выбираются из проверенной environment registry. В ней описана инфраструктура и политика, но отсутствуют credentials.
4. Оптимизируем measured critical path: параллельные независимые jobs, корректные cache keys, безопасный test selection и отмена устаревшего CI. Активный production deploy не отменяем как обычную PR job.
5. Security gates и проверки реального rollout входят в готовность. Быстрая отправка GitOps commit не является быстрым успешным deployment.

У каждого stack guide своя техника, но общие основания те же. Мы не нашли в этой подборке первоисточник, доказывающий, что Netflix использует наш конкретный набор PHP-команд или Meta — нашу конфигурацию Rust. Такие атрибуции запрещены.
