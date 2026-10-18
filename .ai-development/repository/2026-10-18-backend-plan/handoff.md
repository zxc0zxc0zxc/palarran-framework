# Backend plan handoff

Создана documentation-first база `docs/backend/plan/` (13 guides), 6 templates, skill `backend-plan`, slash `/backend:plan`, discovery link и manifest/package backend. Архитектура/stack foundation до feature plan при отсутствии backend; reuse существующей основы. Обязательные DB/data/cache/performance, SLA proposal/SLI/SLO/error budget/recovery, feature-specific edges/tests, SDD traceability/DoD и future worktree DAG/ownership/isolation/integration. Принятые причины: 0001–0004.

## Проверка authoring

- PASS: repository validator — 137 Markdown, 9 skills/adapters, 6 namespaces, links и decision memory.
- PASS: offline unit suite — 11 tests; все 6 packages isolated, backend содержит 1 skill и профильные templates/docs без live project memory/external symlinks/inventory script.
- PASS: skill-creator quick_validate source skill и packaged copy, после исправления YAML description separator.
- PASS: allowlisted package `artifacts/plugins/backend`; Claude plugin validate --strict.
- PASS: 2 Mermaid examples parsed with Mermaid 11 + JSDOM (syntax only, не rendered review).
- PASS: changed Python compilation и diff whitespace checks.
- PASS: [GitHub Actions 39146935543](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39146935543) для implementation commit `d7e4a9754a61df15337b960746e78010d317666c`: offline contracts/tests/compilation и Terraform validation.
- NOT RUN: application implementation/tests/load/migrations/deploy, live APIs/SSH/DB, worktree creation или implementation-agent dispatch. Они не входят в planning. Числовые цели будущего SLA — proposals/assumptions, не достигнутый SLA.

## Использование и контекст следующих задач

Codex `$backend-plan {фича}`, Claude backend plugin `/backend:plan {фича}`. Source docs/templates входят в пакет; копирования одного SKILL недостаточно. Output не перезаписывается, для пересборки выбрать новый каталог. Package не содержит context этого репозитория.

В target read-only local context → foundation/reuse gate → SDD spec/contracts/design → reliability/tests/rollout → future task DAG/DoD → plan consistency review и handoff. Результаты/canonical rationale/index в target `.ai-development/backend/` или связанном existing spec layout. Не запускать реализацию автоматически. Следующий execution scope отдельно проверяет актуальность assumptions/контрактов и выполняет planned gates.
