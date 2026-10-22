---
id: repository/2026-10-22-graph-context/0001
status: accepted
date: 2026-10-22
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, backend/2026-10-19-incremental-context/0001]
---

## Контекст и основание

Пользователь просит Graphify для экономии контекста, правила написания AGENTS.md и инструкции по модулям приложения. В checkout пока только длинный root AGENTS и deterministic product context packets. Сохраняем private budgets/lineage и документы, незакоммиченные изменения ML не трогаем.

## Выбор и объяснение

Graphify Labs, официальный PyPI graphifyy 0.9.93, изолированная локальная установка; нет global install/install skill/hooks/cloud/MCP registration. Локальный code-only AST extraction на специально отобранной копии исходников; не semantic/docs/media extraction, нет LLM/API calls. Нормализованный graph — derived cache, не source of truth. Полный граф не инжектируется в prompt: bounded query, проверка freshness по hashes, затем source snippets и применимые AGENTS/ADR. Runtime budgets не меняются. CLI работает также из target проекта; cached graph хранится в target, не installed skill package.

Root инструкции сокращаем до общих инвариантов и маршрутизации; прежние подробные правила сохраняем в обязательном профильном контракте. Module AGENTS только для существующих каталогов/границ. Authoring guide + templates дают тот же подход target приложениям; не выдумываем сервисы/команды. Обновление target AGENTS запрещено в plan-only/read-only scope. Common decision-memory guide передаёт правило всем существующим skills без дублирования 25 текстов.

## Альтернативы

Авто graphify install меняет agent config/инструкции вне контролируемого контракта. Default semantic pass может расходовать model budget. Постоянно вкладывать полный graph/все module AGENTS экономию не даёт. Cloud/MCP/deep indexing пока не нужны. Root-only длинный policy плохо локализует контекст; полное удаление правил нарушило бы принятые ограничения.

## Источники и evidence

Graphify Labs README, PyPI release metadata и исходники официального wheel (SHA256 verified), code-only/no-cluster flags. OpenAI official AGENTS guide и custom code review article. Даты и applicability: docs/skills/graph-context.md и agents-authoring.md. Claims про 80% — vendor marketing, не наши замеры.

## Последствия и пересмотр

Runtime Python stdlib остаётся 3.9-compatible; optional Graphify требует Python>=3.10 в отдельном venv. Stale/missing graph даёт явный fallback к scoped search. Не повторяем/перезапускаем старые paid runs. Проверяем dirty/untracked drift, секретные пути/symlinks, output bounds, инструкции и portable packages, затем offline suite/factory acceptance. Реальные token savings измеряются отдельно на одинаковых задачах, не выводятся из размеров snippets.

## Применение и проверка

Сначала документация/этот ADR, затем wrapper/локальная установка/index, модульные AGENTS и checks. Фактический PASS/FAIL/NOT RUN и handoff сохраняются после проверки.

Фактически PASS: 270 offline tests (10 новых context/instruction), validator/compile/diff, factory_acceptance p95=1.174ms (lab). Реальный local index: 55 files, 769 nodes, 2658 edges; query и stale-file guard PASS; LLM calls 0. Root 10322→4380 bytes. Actual token savings NOT MEASURED. Подробности в handoff.md и verification.json.
