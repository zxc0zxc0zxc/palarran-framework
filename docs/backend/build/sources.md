# Источники build workflow

Проверено **2026-10-18**. Новые operational/agent правила — наша адаптация source plan и user requirements, не обещание, что компании используют этот exact workflow.

| Источник | Что используем | Границы |
|---|---|---|
| [Git worktree](https://git-scm.com/docs/git-worktree) | Отдельные working trees общей repo и их lifecycle | Runtime/DB/ports/secrets не изолируются Git автоматически |
| [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick) | Один из способов переносить scoped commits при интеграции | Merge policy целевого проекта имеет приоритет; конфликты требуют review/retest |
| [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | SLI/SLO/SLA и measurement window | Lab test не evidence operational agreement за полное окно |
| [Google: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) | Назначение/границы тестов разных уровней | Наши per-feature risk gates, без универсального процента pyramid |
| [Grafana k6: Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) | Machine-readable acceptance для load метрик | Existing runner equivalent допустим; version/environment проверяются в target |

База architecture/data/cache/reliability/SDD: [backend planning sources](../plan/sources.md). Применять по actual target stack/versions. Host API/subagent availability исследовать на месте; не обещать headless agent/worktree feature, которой у host нет. Progress helper проверяет структуру журнала, не факты test execution/Git ancestry и не реальный SLA.
