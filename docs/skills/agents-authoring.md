# Writing project and module AGENTS.md

## Basis

Checked 2026-10-22: the [official OpenAI guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) describes root-to-CWD discovery, nearer instructions and the default combined 32 KiB limit. [OpenAI scoped review rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex) recommends short concrete invariants at their scope. This is Codex behavior; check other hosts separately. Agents starting at root must explicitly read target-directory instructions: a nested file does not guarantee automatic loading of every module.

## Rules

1. Inspect actual README, manifests, code, tests and existing AGENTS/override files first. Preserve user rules. Never write instructions from an assumed stack.
2. Root: purpose/language, shared invariants, module/path map, documentation entrypoints, decision memory and main checks. Module AGENTS: local duties/contracts/edge cases/commands/verification criteria only. Do not copy root/sibling instructions.
3. Our suggested budget: root <=6 KiB, module <=4 KiB; local convention, not platform limit. Count the entire applicable chain, not only individual files. Overrides need explicit rationale/review; never create overrides merely to shorten text.
4. A rule has trigger, invariant, safe path and check. “Write good code” is unhelpful. Verify numbers/paths/commands against the repository; mark missing facts unknown and link the question's owner.
5. Decision history belongs in canonical ADRs; AGENTS links current constraints, not chat history. Distinguish planned/implemented/verified/deployed versions.
6. During authorized application changes, create/update AGENTS only at actual affected boundaries, such as existing services/billing or apps/web. Do not create one per file. In plan-only/read-only scope provide proposed templates/handoff only; never alter target instructions.
7. Graphify is optional navigation. After freshness checks read original source/applicable instructions; missing/stale graphs do not waive verification. No graph dumps, dependency lockfiles, raw logs or secrets in AGENTS.
8. Boundary/contract/test-command changes update nearest AGENTS/routing table. Define shared code/worktree ownership in SDD plans; AGENTS itself must not dispatch agents or authorize external actions.

## Templates and review

All portable packages include templates/agents/root.md and module.md with this guide: root purpose/boundaries/docs/memory/checks, module scope/contracts/verification. Fill verified facts only; placeholders are not ready instructions.

Review checks existing paths, scope-appropriate safe commands, no duplication/conflicts/secrets, preserved mandatory docs/source behavior and sufficient instructions without reading sibling modules. No obligation to launch paid model CLIs to test instruction loading. Local structural audits do not establish every host's behavior.
