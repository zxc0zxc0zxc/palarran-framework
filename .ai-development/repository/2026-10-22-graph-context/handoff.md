# Graphify / AGENTS — handoff

Реализована revision graph-context-v001 по [решению 0001](decisions/0001-context.md); [план](plan.md), [контекст](context.md), [machine-readable evidence](verification.json). Существующие ML changes и старые product runs/budgets сохранены. Commit/push не выполнялись.

## Что поставлено

- Документация до реализации: docs/skills/graph-context.md, agents-authoring.md. Primary Graphify/PyPI/OpenAI references с датой и applicability; vendor savings не объявлены нашими measurements.
- Optional Graphify Labs graphifyy 0.9.93 установлен локально в ignored .graphify/venv; dependency snapshot .graphify/installed-requirements.txt. Runtime/tests не требуют optional package и остаются Python 3.9-compatible; tool venv использует отдельный Python 3.12.
- scripts/graph_context.py: явные setup/index/status/query; code-only AST на filtered staging copy, очищенное environment, bounded time/output, hashes для dirty/untracked/delete drift, content-addressed graph publication и safe diagnostic enums. Не запускает graphify install, hooks, cloud, semantic extraction или model API. Unknown/stale/missing graph требует scoped source search, не возвращается как fresh.
- Root AGENTS: 10 322 → 4 380 bytes; восемь module AGENTS для реальных orchestrator/scripts/tests/skills/docs/templates/plugins/examples. Прежние подробные ограничения сохранены в docs/skills/domain-contracts.md; exact historical root — prior-AGENTS.md. Корневые инварианты и профильные обязательные guides сохранены.
- Target root/module templates и общий decision-memory contract для всех 25 skills: читать applicable instructions, создавать/обновлять AGENTS по реальным границам только в разрешённой реализации. Planning/read-only пишет proposal/handoff без target instruction edits/tool installs.
- Validator проверяет наличие и budgets инструкций (root <=6 KiB, module <=4 KiB); все portable namespaces получают templates/agents, cache/venv не пакуются. Global agent config не менялся.

## Проверка

PASS full offline suite: **270 tests**, 202.755s, включая **10 новых graph/instruction tests**: filtered sources, symlinks/private paths, mutable/untracked/deleted files, tampering, failed atomic refresh, concurrent source drift, version/size/output/time limits и environment key scrubbing. Provider tests — fake transports, installation/network/model calls из tests отсутствуют.

PASS actual local Graphify smoke: **55 source files / 489 003 bytes / 769 nodes / 2658 edges**, zero LLM calls. Fresh query ml_resources с budget proxy 1200 вернул 4098 bytes source-linked navigation. Реальный added-file probe дал stale_graph и exit 2; удаление probe восстановило fresh без rebuild. Current fingerprint — в verification.json. Не загружается полный graph в prompt.

PASS structural validator, Python compile и diff whitespace; runtime acceptance: 100 samples, p95 **1.174 ms**, threshold 100 ms, smoke 0.418s. Это lab, не operational SLA. После записи handoff validator/status повторены.

## Ограничения и продолжение

Фактическая экономия billed/input/cached tokens — **NOT MEASURED**: ни одного live model run или изменения бюджета. Сокращение root bytes — измерение текста, не подписки/качества ответов. Graphify AST не содержит docs/media/config semantics/ADR и не доказывает полноту dynamic calls; original source/mandatory docs/решения остаются authority. Sensitive filename filtering не заменяет secret scanner; секреты не должны жить в source code.

Graph cached локально и заменяем, refresh после code changes явный; старые cache blobs могут сохраняться до отдельной уборки. Existing mandatory materialized product context packets не изменены и не заменены графом. Cloud/MCP/global skill installation, paid training/deploy/outreach — NOT RUN. В других target проектах tool setup отдельный явный шаг; шаблоны нельзя применять как готовые выдуманные инструкции.
