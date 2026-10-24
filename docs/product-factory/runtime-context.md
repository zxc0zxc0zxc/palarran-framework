# Automatic agent context delivery

## Semantics

Before AI dispatch runtime appends applicable target AGENTS/context to the original prompt, preserving max_prompt_bytes. Per directory select AGENTS.override.md, otherwise AGENTS.md; root-to-module order/no automatic sibling loading follows the [official guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), checked 2026-10-22. User/global instructions remain host responsibility. Built-in delivery changes neither cwd, permissions nor source skill docs.

Optional task `context`: `paths` (1..8 relative owned code files/module directories), `query` (short search), `mode` (default `graph` or baseline `source`). No absolute paths/traversal/private/secret/cache directories/symlinks. Without it infer existing code paths only from prompt; otherwise root instructions/explicit root-only receipt. LLMs never guess broad unknown ownership. Future implementation plans must derive context.paths from file ownership.

Root/ancestor instructions are mandatory/untruncated; chains >24 KiB or existing prompt ceilings block before model calls. Nearest instructions apply only to their subtree; multi-module tasks receive deduplicated union chains. AGENTS/snippets retain path/SHA; instructions are trusted project guidance, code/graph/docs are source data, not new authority. Read canonical INDEX/ADRs/mandatory guides through original references, never replace with summaries.

## Graph and fallback

Create saves private source-root binding. Isolated worktrees use origin-target Graphify cache only when exact code-hash maps match workspace and cache is fresh. Runtime never treats skill-package graphs as target graphs. Missing tool/cache, incompatible/stale graphs or bounded-retrieval failures produce scoped source fallback. No auto installs/rebuild/cloud/semantic calls. The [graph contract](../skills/graph-context.md) remains mandatory.

Bound graph queries; filter source paths/lines by declared scope and check current workspace. Never include the full graph in prompts. Prelaunch source changes produce drift; final acceptance still checks actual subject. If optional retrieval does not fit, shorten/omit retrieval with explicit receipt, never required AGENTS. Source baselines require complete scoped source to fit; otherwise reject comparison, never select a convenient truncated baseline.

Private additive tables hold source-root binding/context receipts (task/attempt, hashes, bytes, selected paths/fallback reason). SQLite stores no prompt/AGENTS/code/raw-model text. Fenced receipts precede agent calls after host-independent composition/existing prompt-limit checks. Command tasks/legacy handoff/verifier protocol unchanged. Context preparation consumes deadline and cannot bypass budget callbacks.

## Same task: comparison contract

One pair = source arm/graph arm with identical task, source fingerprint, model/effort, applicable AGENTS, no-tools response protocol and independent answer rubric. Public final answers are saved only as bounded JSON measurement artifacts; hidden reasoning is neither requested nor stored. This specialized measurement coordinator does not replace engineering handoff/DoD.

Paired live runs require existing carry/verified remaining budget, separate arm reserves within the original ceiling, max 2 calls/no retry. Unknown outcomes retain full reserve; one unknown arm stops the pair. Sizes/estimated tokens are not actual usage. [Model reference](https://developers.openai.com/api/docs/models/gpt-6-luna), checked 2026-10-22, supplies compatibility only; pinned conservative rate cards estimate CLI usage, not subscription invoices.

Reports show actual input, cached input, output/reasoning, cumulative total, cache-breakdown unknowns, priced cost, elapsed, prompt/source/context hashes, quality verdict and absolute/percentage reduction only for valid complete matched arms. Show cached input separately when caches differ; n=1 establishes no causality across tasks. Failed/incomplete pairs are inconclusive, with no savings claim/automatic third call. This measurement establishes neither operational SLA nor invoice.

Measurement CLI (explicitly authorized runs only): `python3 -m orchestrator.context_benchmark --state EXISTING_PRIVATE_STATE --target CLEAN_FROZEN_TARGET --agent ABSOLUTE_CODEX --budget-file EXISTING_RECEIPT`. One pair consumes the budget receipt once, including failures. Preserve existing unknown carry; never restart incomplete pairs. Current verification uses an isolated fixture with byte-identical real ml_resources.py and identical root/module instructions, not source-product changes.

Optional task.context example (not full workflow/new budget): examples/product-factory/task-context.example.json in full checkout. Example paths name actual Palarran modules; adapt to another target's approved SDD ownership, never invent src/services layouts.

New files/directories from approved SDD ownership may not exist yet: runtime reads actual ancestor AGENTS, invents no leaf instructions and claims no source snippets for missing code. Root/module AGENTS are created separately under authorized implementation scope.
