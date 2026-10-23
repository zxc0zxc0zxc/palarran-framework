# Дизайн диагностики обучения

**Статус: runtime-v001.** [Runtime contract](runtime.md) реализует optional frozen diagnostics policy, bounded collectors, tracked rules, immutable generation snapshots и rolling/terminal reports. Data gate отдельно проверяет подготовку данных. Task/framework scorers и безопасная фиксация tensor state остаются ответственностью конкретного trainer hook; полный design шире generic runtime.

Цель — ответить: обучается ли модель корректно, улучшает ли нужную задачу, сохраняет ли полезное поведение и во что обходится результат. Loss остаётся одним из сигналов. Снижение loss/PPL при росте ошибок, обрывов или регрессий не считается успехом.

## Маршрут

| Документ | Что решает |
| --- | --- |
| [Sources](sources.md) | Первичные источники, даты и пределы переноса |
| [Artifacts](artifacts.md) | Какие данные сохраняем, lineage, streams, privacy и стоимость |
| [Task metrics](task-metrics.md) | Train/validation, PPL, primary metrics и slices по задаче |
| [Heuristics](heuristics.md) | Какая эвристика за что отвечает, когда применима и как действует |
| [Generation probes](generations.md) | Сравнимые примеры поведения по checkpoint/time |
| [Reports](reports.md) | Rolling/terminal report при success/stop/failure/unknown |
| [Integration plan](integration-plan.md) | Что нужно реализовать, task DAG и offline DoD |

Основа: [Karpathy Recipe](https://karpathy.github.io/2019/04/25/recipe/) — маленькие проверяемые шаги, осмотр данных и наблюдение фиксированных примеров; [Google Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) — проверять pipeline и соответствие цели. Для данного проекта адаптируем fixed probes на development данных, не на скрытом final test. Наши схемы хранения/остановок — инженерный выбор, не научный результат.

```mermaid
flowchart TD
  P[Experiment + task profile + budget + probes] --> F{Preflight contracts valid?}
  F -->|Нет| B[Blocked report: no training launch]
  F -->|Да| S[Durable start stub + approved training]
  S --> C[Train telemetry + bounded validation + generation snapshots]
  C --> H[Heuristic state + evidence + permitted action]
  H -->|Continue| C
  H -->|Complete / stop / fail| Q[Stop compute / confirm provider outcome]
  Q --> R[Bounded terminal report from durable artifacts]
  S -->|Worker/controller lost| D[Durable rolling state + recovery]
  D --> R
  R --> E[Separate frozen benchmark when authorized and budgeted]
```

## Что фиксировать до старта

В immutable experiment revision: task profile, hypothesis, supervised target basis, train/dev/final-test policy, primary metric и practical delta, general/domain/language guardrails, diagnostic probe version, registry эвристик с thresholds/windows, logging/evaluation/generation/checkpoint cadence и стоимость. Все неопределённости и отключённые сигналы имеют причину. Для baseline также нужен diagnostic snapshot или явный NOT RUN; нельзя придумывать сравнение после обучения.

Нет общего правильного «логировать каждые N шагов». Малый run: дешёвые per-update scalars и редкие небольшие probes. Длинный run: bounded scalars + периодическая validation, rotating debug cases и exported checkpoints. Полные gradient/activation histograms только ограниченными диагностическими окнами. Выбор cadence фиксируется до запуска, overhead измеряется в разрешённом pilot; при нехватке бюджета уменьшаем необязательную диагностику по заранее описанной политике и сохраняем причину, а не повышаем ceiling.

## DoD дизайна и реализации

Документационный DoD: все поля, состояния, decision rules и failure paths определены; примеры явно not_run, packaged links разрешаются. Runtime DoD дополнительно требует collectors/normalizers, finalizer/recovery, artifact integrity и offline failure-injection tests из плана. Наличие этого guide или скриншота tracker не даёт runtime PASS.

Шаблоны для следующей реализации: [diagnostics policy JSON](examples/diagnostics-policy.example.md), [generation snapshot JSON](examples/generation-snapshot.example.md), [training report](examples/training-report.md), [validation report](examples/validation-report.md). JSON записан в Markdown для portable docs package; все примеры NOT RUN.
