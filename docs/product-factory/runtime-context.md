# Автоматическая доставка контекста агента

## Семантика

Перед AI dispatch runtime добавляет применимые target AGENTS и контекст к исходному prompt, сохраняя существующий max_prompt_bytes. Для каждой директории выбирается AGENTS.override.md, иначе AGENTS.md; root-to-module порядок и отсутствие автоматической загрузки соседей основаны на [официальном guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), проверено 2026-10-22. User/global instructions остаются ответственностью host. Встроенная доставка не меняет cwd, permissions или source skill docs.

Optional task field `context`: `paths` (1..8 относительных owned code files/module directories), `query` (короткий поиск), `mode` (`graph` default или `source` для baseline). Scope без absolute paths, traversal, private/secret/cache directories или symlinks. Без поля — infer только существующие code paths из prompt; если их нет — root instructions и явный root-only receipt. Широкое неизвестное владение не угадывается LLM. Планы будущих implementation tasks должны передавать context.paths из своего file ownership.

Root/ancestor instructions — обязательны и не урезаются; цепь >24 KiB или existing prompt ceiling блокирует запуск до model call. Ближайшие instructions применяются только к своему subtree; multi-module tasks получают union chains с dedup. AGENTS и snippets сохраняют path/SHA; instructions — trusted project guidance, code/graph/документы — source data, не новые разрешения. Canonical INDEX/ADR и mandatory guides читаются по исходным ссылкам, не заменяются summary.

## Graph и fallback

Create сохраняет private source-root binding. Рабочий isolated worktree использует Graphify cache исходного target только если exact code hash map совпадает с workspace и cache fresh. Runtime никогда не читает граф из skills package как target graph. При missing tool/cache, incompatible/stale graph или сбое bounded retrieval — scoped source fallback. Никаких auto installs/rebuild/cloud/semantic calls. [Graph contract](../skills/graph-context.md) остаётся обязательным.

Graph query ограничен, source paths/lines фильтруются по declared scope и проверяются в текущем workspace. Полный graph в prompt не попадает. После изменения source перед launch обнаруживается drift; final acceptance всё равно проверяет actual subject. Если optional retrieval не помещается, сокращается/исключается именно retrieval с явным receipt; required AGENTS не выбрасываются. Для source baseline full scoped source обязан целиком помещаться, иначе сравнение отклоняется, а не выбирает удобную усечённую baseline.

Private additive tables содержат source-root binding и context receipts (task/attempt, hashes, bytes, выбранные пути и fallback reason). Тексты prompt/AGENTS/кода/raw model output в SQLite не пишутся. Receipt записывается fenced перед agent call, после host-independent composition и существующего prompt-limit check. Command tasks и legacy handoff/verifier protocol неизменны. Context preparation входит в deadline и не разрешает обход budget callbacks.

## Одинаковая задача: comparison contract

Одна pair = source arm и graph arm: одинаковые task, source fingerprint, model/effort, applicable AGENTS, no-tools response protocol и independent answer rubric. Public final answer сохраняется только в ограниченном JSON artifact measurement scope; hidden reasoning не запрашивается/не сохраняется. Это специальный measurement coordinator, не замена engineering handoff/DoD.

Перед paired live run обязательны existing carry + verified remaining budget, отдельные arm reserves внутри прежнего ceiling, max calls 2 и no retry. Unknown outcome удерживает полный reserve; один неизвестный arm прекращает pair. Размеры/estimated tokens не считаются actual usage. [Model reference](https://developers.openai.com/api/docs/models/gpt-6-luna), проверено 2026-10-22, используется только для совместимости; pinned conservative rate card — экономическая оценка CLI usage, не счёт подписки.

Отчёт показывает actual input, cached input, output/reasoning, cumulative total, cache breakdown unknowns, priced cost, elapsed time, prompt/source/context hashes, quality verdict, сокращение абсолютное/% только при valid complete matched arms. При cache differences показывать cached отдельно; n=1 не доказывает причинность для других задач. Failed/incomplete pair — inconclusive, без заявления экономии и без автоматического третьего вызова. Operational SLA и invoice не выводятся из этого замера.

Measurement CLI (только explicit authorized run): `python3 -m orchestrator.context_benchmark --state EXISTING_PRIVATE_STATE --target CLEAN_FROZEN_TARGET --agent ABSOLUTE_CODEX --budget-file EXISTING_RECEIPT`. Бюджетный receipt расходуется одной парой только один раз, включая failures. Existing unknown carry сохраняется; incomplete pair не перезапускать. Для текущей проверки используется изолированный стенд с byte-identical реальным ml_resources.py и одинаковыми root/module instructions, а не изменение исходного продукта.

Пример самого optional task.context (не полный workflow и не новый budget): examples/product-factory/task-context.example.json из полного checkout. Пути в примере относятся к реальному модулю ai-tools; для другого target заменить по утверждённому SDD ownership, не выдумывать src/services layout.

Новые files/directories из утверждённого SDD ownership могут ещё отсутствовать: runtime читает реально существующие ancestor AGENTS, не выдумывает leaf instructions и не заявляет найденные source snippets для отсутствующего кода. Root/module AGENTS создаются отдельно в разрешённой implementation scope.
