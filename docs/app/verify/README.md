# Независимая приёмка приложения

`/app:verify {target/scenarios} [--plan]` связывает бизнес-требование → действия пользователя → browser/API/DB observations → verdict. Сначала [sources](sources.md), [methodology](methodology.md), [contract](contract.md), [operations](operations.md), [evidence](evidence.md), target AGENTS/INDEX/accepted ADR. Implementation не исправляется во время acceptance; найденный дефект возвращается builder с repro, после исправления новая subject/revision и повтор затронутых/критических сценариев.

V1 CLI реализует trusted local HTTP app + optional existing Playwright Chromium + readonly SQLite. Другие DB, remote/staging и native/mobile сценарии доступны через отдельно разрешённые existing tools/manual protocol, не считаются проверенными CLI-адаптерами. Никаких model/paid judge calls, installs, deploy, production writes или автоматических retries.

```mermaid
flowchart LR
  R[Business requirements + frozen scenarios] --> S[Exact source / application revision / test fixtures]
  S --> B[Browser: real controls + assertions]
  B --> A[API: independent read-back]
  A --> D[DB: readonly invariant + same run/entity]
  D --> F{Coverage + final subject unchanged?}
  F -->|Да| P[PASS within declared scope]
  F -->|Нет| I[FAIL / INCONCLUSIVE / NOT_RUN + repro]
```

CLI source включён в app portable package, вместе с templates и Node bridge. Browser dependencies устанавливаются оператором отдельно; отсутствующий browser = NOT_RUN, не HTTP substitute. Captured screenshot не равен визуальному review. Result scientific/operational SLA, security audit и production readiness не выводятся из fixture PASS.
