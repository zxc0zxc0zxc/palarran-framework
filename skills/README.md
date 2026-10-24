# Skill packages

[Repository](../README.md) · [Package architecture](../packages/README.md) · [Machine catalog](../packages/catalog.json)

Canonical skills live with their owning capability. Core is included for every selected package. Canonical sources are English; agent interaction, code comments and generated documentation follow project preferences. HTML artifacts use `languages.docs` without a language selector.

```sh
python3 scripts/project_setup.py setup --target /ABSOLUTE/project --client codex \
  --packages code validation memory --skills-language en --code-language en --docs-language en --plan
```

## Core

Installer ID: `core`. Shared agent foundations, runtime, setup and safe package discovery.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:setup` | [`$palarran-setup`](../packages/core/setup/skills/palarran-setup/SKILL.md) | `{target?} [--client codex|claude|both] [--plan]` |
| `/palarran:mcp:build` | [`$palarran-mcp-build`](../packages/core/agents/skills/palarran-mcp-build/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:core:coop` | [`$palarran-core-coop`](../packages/core/coop/skills/palarran-core-coop/SKILL.md) | `[--alert {message}] [--plan]` |
| `/palarran:core:share` | [`$palarran-core-share`](../packages/core/coordination/skills/palarran-core-share/SKILL.md) | `{task?} [--plan]` |

## Memory

Installer ID: `memory`. Local notes, session context and optional reviewed cross-project knowledge.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:memorize` | [`$palarran-memorize`](../packages/memory/memorize/skills/palarran-memorize/SKILL.md) | `{short|long} {note} [--plan]` |
| `/palarran:remember` | [`$palarran-remember`](../packages/memory/remember/skills/palarran-remember/SKILL.md) | `{query} [--plan]` |
| `/palarran:memorize:session` | [`$palarran-memorize-session`](../packages/memory/sessions/skills/palarran-memorize-session/SKILL.md) | `[--long] [--plan]` |
| `/palarran:remember:session` | [`$palarran-remember-session`](../packages/memory/sessions/skills/palarran-remember-session/SKILL.md) | `[--long] @file [--plan]` |
| `/palarran:memory:learn` | [`$palarran-memory-learn`](../packages/memory/knowledge/skills/palarran-memory-learn/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:memory:recall` | [`$palarran-memory-recall`](../packages/memory/knowledge/skills/palarran-memory-recall/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:vacuum` | [`$palarran-vacuum`](../packages/memory/vacuum/skills/palarran-vacuum/SKILL.md) | `[--long] [--plan]` |

## Product

Installer ID: `product`. Evidence-backed product definition, market and customer planning.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:product:define` | [`$palarran-product-define`](../packages/product/research/skills/palarran-product-define/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:market` | [`$palarran-product-market`](../packages/product/research/skills/palarran-product-market/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:compare` | [`$palarran-product-compare`](../packages/product/research/skills/palarran-product-compare/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:revenue` | [`$palarran-product-revenue`](../packages/product/research/skills/palarran-product-revenue/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:acquisition` | [`$palarran-product-acquisition`](../packages/product/research/skills/palarran-product-acquisition/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:b2b` | [`$palarran-product-b2b`](../packages/product/research/skills/palarran-product-b2b/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:b2c` | [`$palarran-product-b2c`](../packages/product/research/skills/palarran-product-b2c/SKILL.md) | `{task/context} [profile flags]` |

## Design

Installer ID: `design`. Adaptive UX concepts and visual UI design.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ux:design` | [`$palarran-ux-design`](../packages/design/ux/skills/palarran-ux-design/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ui:design` | [`$palarran-ui-design`](../packages/design/ui/skills/palarran-ui-design/SKILL.md) | `{task/context} [profile flags]` |

## Code

Installer ID: `code`. Specification-driven frontend and backend planning and implementation.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:frontend:plan` | [`$palarran-frontend-plan`](../packages/code/frontend/skills/palarran-frontend-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:frontend:build` | [`$palarran-frontend-build`](../packages/code/frontend/skills/palarran-frontend-build/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:backend:plan` | [`$palarran-backend-plan`](../packages/code/backend/skills/palarran-backend-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:backend:build` | [`$palarran-backend-build`](../packages/code/backend/skills/palarran-backend-build/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:git:commit` | [`$palarran-git-commit`](../packages/code/git/skills/palarran-git-commit/SKILL.md) | `{stage?} [--plan]` |
| `/palarran:git:history` | [`$palarran-git-history`](../packages/code/git/skills/palarran-git-history/SKILL.md) | `@file [--plan]` |
| `/palarran:git:conflicts` | [`$palarran-git-conflicts`](../packages/code/git/skills/palarran-git-conflicts/SKILL.md) | `{target-branch} [--plan]` |
| `/palarran:git:mr` | [`$palarran-git-mr`](../packages/code/git/skills/palarran-git-mr/SKILL.md) | `[--plan]` |

## Machine Learning

Installer ID: `machine-learning`. Bounded experiment design, data, training and independent benchmarks.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ml:plan` | [`$palarran-ml-plan`](../packages/machine-learning/experiments/skills/palarran-ml-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:hypotheses` | [`$palarran-ml-hypotheses`](../packages/machine-learning/experiments/skills/palarran-ml-hypotheses/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:model` | [`$palarran-ml-model`](../packages/machine-learning/experiments/skills/palarran-ml-model/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:data` | [`$palarran-ml-data`](../packages/machine-learning/experiments/skills/palarran-ml-data/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:cost` | [`$palarran-ml-cost`](../packages/machine-learning/experiments/skills/palarran-ml-cost/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:train` | [`$palarran-ml-train`](../packages/machine-learning/experiments/skills/palarran-ml-train/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:benchmark` | [`$palarran-ml-benchmark`](../packages/machine-learning/experiments/skills/palarran-ml-benchmark/SKILL.md) | `{task/context} [profile flags]` |

## Docs

Installer ID: `docs`. Human-readable documentation and portable review artifacts.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:docs:artifact` | [`$palarran-docs-artifact`](../packages/docs/documentation/skills/palarran-docs-artifact/SKILL.md) | `{description?}` |

## Science

Installer ID: `science`. Evidence-grounded scientific reporting from existing experiments.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:science:preprint` | [`$palarran-science-preprint`](../packages/science/preprint/skills/palarran-science-preprint/SKILL.md) | `{task/context} [profile flags]` |

## Validation

Installer ID: `validation`. Independent application acceptance and measured agent evaluation.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:agent:eval` | [`$palarran-agent-eval`](../packages/validation/agents/skills/palarran-agent-eval/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:agent:improve` | [`$palarran-agent-improve`](../packages/validation/agents/skills/palarran-agent-improve/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:app:verify` | [`$palarran-app-verify`](../packages/validation/application/skills/palarran-app-verify/SKILL.md) | `{task/context} [profile flags]` |

## Infrastructure

Installer ID: `infrastructure`. Infrastructure design, delivery, VPS operations and scoped incidents.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:infra:plan` | [`$palarran-infra-plan`](../packages/infrastructure/planning/skills/palarran-infra-plan/SKILL.md) | `{low|med|high} [--plan]` |
| `/palarran:ci-cd` | [`$palarran-ci-cd`](../packages/infrastructure/delivery/skills/palarran-ci-cd/SKILL.md) | `{github|gitlab} [--plan]` |
| `/palarran:vps:inspect` | [`$palarran-vps-inspect`](../packages/infrastructure/vps/skills/palarran-vps-inspect/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:vps:manage` | [`$palarran-vps-manage`](../packages/infrastructure/vps/skills/palarran-vps-manage/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:infrastructure:incident` | [`$palarran-infrastructure-incident`](../packages/infrastructure/incident/skills/palarran-infrastructure-incident/SKILL.md) | `{what happened} [--plan]` |


## Security

Installer ID: `security`. Optional scoped audits; no automatic fixes or target access.

| Command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:security:infrastructure` | [`$palarran-security-infrastructure`](../packages/security/infrastructure/skills/palarran-security-infrastructure/SKILL.md) | `{scope?} [--plan]` |
| `/palarran:security:ingress` | [`$palarran-security-ingress`](../packages/security/ingress/skills/palarran-security-ingress/SKILL.md) | `{scope?} [--plan]` |
| `/palarran:security:log` | [`$palarran-security-log`](../packages/security/log/skills/palarran-security-log/SKILL.md) | `{scope?} [--plan]` |
| `/palarran:security:egress` | [`$palarran-security-egress`](../packages/security/egress/skills/palarran-security-egress/SKILL.md) | `{scope?} [--plan]` |
| `/palarran:security:code` | [`$palarran-security-code`](../packages/security/code/skills/palarran-security-code/SKILL.md) | `{scope?} [--plan]` |
| `/palarran:security:cve` | [`$palarran-security-cve`](../packages/security/cve/skills/palarran-security-cve/SKILL.md) | `{scope?} [--plan]` |
