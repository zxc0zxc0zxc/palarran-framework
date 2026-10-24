# Build-workflow sources

Checked **2026-10-18**. New operational/agent rules adapt source plans and user requirements; they do not claim companies follow this exact workflow.

| Source | What we use | Limits |
|---|---|---|
| [Git worktree](https://git-scm.com/docs/git-worktree) | Separate working trees of a shared repository and their lifecycle | Git does not automatically isolate runtimes/DBs/ports/secrets |
| [Git cherry-pick](https://git-scm.com/docs/git-cherry-pick) | One way to transfer scoped commits during integration | Target merge policy takes precedence; conflicts need review/retesting |
| [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | SLI/SLO/SLA and measurement windows | Lab tests do not establish full-window operational agreements |
| [Google: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) | Purposes/limits of testing levels | Our per-feature risk gates, no universal pyramid percentage |
| [Grafana k6: Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) | Machine-readable acceptance for load metrics | Existing equivalent runners allowed; verify target version/environment |

Architecture/data/cache/reliability/SDD basis: [backend planning sources](../plan/sources.md). Apply to actual target stack/versions. Inspect host API/subagent availability locally; do not promise unavailable headless-agent/worktree features. Progress helpers check journal structure, not actual test execution/Git ancestry or operational SLA.
