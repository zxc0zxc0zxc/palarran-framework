# Skill packages

[README](../README.md) · [Documentation](../docs/README.md) · [Configuration](../docs/setup/configuration.md) · [Command catalog](catalog.json) · [Package catalog](packages.json)

**38 canonical skills in 15 selectable packages.** Choose package IDs at setup; `setup` is always included. Shared guide/helper dependencies are carried for portability, while unselected skills receive no discovery links.

Codex uses `$palarran-*`. The unified Claude plugin exposes `/palarran:...`; standalone Claude discovery uses `/palarran-...`. These are separate interfaces.

```sh
python3 scripts/project_setup.py setup --target /ABSOLUTE/project --client codex \
  --packages backend app memory --skills-language en --code-language en --docs-language en --plan
```

| Package | What it adds | Location / prerequisites |
| --- | --- | --- |
| [`setup`](#setup) | Install, update and check the project connection. | Local library; checks an existing global memory connection |
| [`product`](#product) | Product definition, market evidence, competitors, revenue and first customers. | Local project; no service installed |
| [`ux`](#ux) | Responsive business flows, screen states and interaction diagrams. | Local project; no service installed |
| [`ui`](#ui) | Responsive visual concepts, design systems, tokens and generated assets. | Local project; no service installed |
| [`frontend`](#frontend) | SDD feature planning and browser-verified interface implementation. | Local project; no service installed |
| [`backend`](#backend) | Architecture, API/data contracts, SDD implementation and reliability checks. | Local project; no service installed |
| [`infra`](#infra) | Scale-aware VPS/Compose, K3s and Kubernetes infrastructure planning. | Local project; no service installed |
| [`ci-cd`](#ci-cd) | GitHub/GitLab delivery for Go, PHP, Next.js, Python and Rust. | Local project; no service installed |
| [`vps`](#vps) | Read-only host inspection and concrete authorized server/app-stack operations. | Local skills; SSH target only for authorized operations |
| [`ml`](#ml) | Hypotheses, experiment/model/data/cost planning, supervised training and benchmarks. | Local planning; training needs explicit scope/budget/provider |
| [`science`](#science) | Evidence-grounded LaTeX experiment reporting. | Local project; no service installed |
| [`app`](#app) | Independent business acceptance through browser, API and read-only DB checks. | Local project; no service installed |
| [`agent`](#agent) | Frozen task evaluations and regression-driven skill improvements. | Local project; no service installed |
| [`mcp`](#mcp) | Task-oriented agent tools, compact results, security and evaluations. | Local project; no service installed |
| [`memory`](#memory) | Quick notes, VPS context, structured session handoffs, recall and reviewed cleanup. | Local notes; optional configured private VPS memory |

## setup

Install, update and check the project connection.

Install selector: `--packages setup`. Portable Claude plugin: `palarran-setup`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:setup` | [`$palarran-setup`](palarran-setup/SKILL.md) | `{target?} [--client codex|claude|both] [--plan]` |

## product

Product definition, market evidence, competitors, revenue and first customers.

Install selector: `--packages product`. Portable Claude plugin: `palarran-product`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:product:define` | [`$palarran-product-define`](palarran-product-define/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:market` | [`$palarran-product-market`](palarran-product-market/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:compare` | [`$palarran-product-compare`](palarran-product-compare/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:revenue` | [`$palarran-product-revenue`](palarran-product-revenue/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:acquisition` | [`$palarran-product-acquisition`](palarran-product-acquisition/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:b2b` | [`$palarran-product-b2b`](palarran-product-b2b/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:product:b2c` | [`$palarran-product-b2c`](palarran-product-b2c/SKILL.md) | `{task/context} [profile flags]` |

## ux

Responsive business flows, screen states and interaction diagrams.

Install selector: `--packages ux`. Portable Claude plugin: `palarran-ux`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ux:design` | [`$palarran-ux-design`](palarran-ux-design/SKILL.md) | `{task/context} [profile flags]` |

## ui

Responsive visual concepts, design systems, tokens and generated assets.

Install selector: `--packages ui`. Portable Claude plugin: `palarran-ui`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ui:design` | [`$palarran-ui-design`](palarran-ui-design/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ux:design` | [`$palarran-ux-design`](palarran-ux-design/SKILL.md) | `{task/context} [profile flags]` |

## frontend

SDD feature planning and browser-verified interface implementation.

Install selector: `--packages frontend`. Portable Claude plugin: `palarran-frontend`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:frontend:plan` | [`$palarran-frontend-plan`](palarran-frontend-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:frontend:build` | [`$palarran-frontend-build`](palarran-frontend-build/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ui:design` | [`$palarran-ui-design`](palarran-ui-design/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ux:design` | [`$palarran-ux-design`](palarran-ux-design/SKILL.md) | `{task/context} [profile flags]` |

## backend

Architecture, API/data contracts, SDD implementation and reliability checks.

Install selector: `--packages backend`. Portable Claude plugin: `palarran-backend`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:backend:plan` | [`$palarran-backend-plan`](palarran-backend-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:backend:build` | [`$palarran-backend-build`](palarran-backend-build/SKILL.md) | `{task/context} [profile flags]` |

## infra

Scale-aware VPS/Compose, K3s and Kubernetes infrastructure planning.

Install selector: `--packages infra`. Portable Claude plugin: `palarran-infra`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:infra:plan` | [`$palarran-infra-plan`](palarran-infra-plan/SKILL.md) | `{low|med|high} [--plan]` |

## ci-cd

GitHub/GitLab delivery for Go, PHP, Next.js, Python and Rust.

Install selector: `--packages ci-cd`. Portable Claude plugin: `palarran-ci-cd`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ci-cd` | [`$palarran-ci-cd`](palarran-ci-cd/SKILL.md) | `{github|gitlab} [--plan]` |

## vps

Read-only host inspection and concrete authorized server/app-stack operations.

Install selector: `--packages vps`. Portable Claude plugin: `palarran-vps`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:vps:inspect` | [`$palarran-vps-inspect`](palarran-vps-inspect/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:vps:manage` | [`$palarran-vps-manage`](palarran-vps-manage/SKILL.md) | `{task/context} [profile flags]` |

The package stays on the agent workstation. Application deployment copies only its reviewed runtime/artifacts to the VPS, never the skills. [Application stack workflow](../docs/setup/vps-stack.md).

## ml

Hypotheses, experiment/model/data/cost planning, supervised training and benchmarks.

Install selector: `--packages ml`. Portable Claude plugin: `palarran-ml`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:ml:plan` | [`$palarran-ml-plan`](palarran-ml-plan/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:hypotheses` | [`$palarran-ml-hypotheses`](palarran-ml-hypotheses/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:model` | [`$palarran-ml-model`](palarran-ml-model/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:data` | [`$palarran-ml-data`](palarran-ml-data/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:cost` | [`$palarran-ml-cost`](palarran-ml-cost/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:train` | [`$palarran-ml-train`](palarran-ml-train/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:ml:benchmark` | [`$palarran-ml-benchmark`](palarran-ml-benchmark/SKILL.md) | `{task/context} [profile flags]` |

## science

Evidence-grounded LaTeX experiment reporting.

Install selector: `--packages science`. Portable Claude plugin: `palarran-science`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:science:preprint` | [`$palarran-science-preprint`](palarran-science-preprint/SKILL.md) | `{task/context} [profile flags]` |

## app

Independent business acceptance through browser, API and read-only DB checks.

Install selector: `--packages app`. Portable Claude plugin: `palarran-app`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:app:verify` | [`$palarran-app-verify`](palarran-app-verify/SKILL.md) | `{task/context} [profile flags]` |

## agent

Frozen task evaluations and regression-driven skill improvements.

Install selector: `--packages agent`. Portable Claude plugin: `palarran-agent`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:agent:eval` | [`$palarran-agent-eval`](palarran-agent-eval/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:agent:improve` | [`$palarran-agent-improve`](palarran-agent-improve/SKILL.md) | `{task/context} [profile flags]` |

## mcp

Task-oriented agent tools, compact results, security and evaluations.

Install selector: `--packages mcp`. Portable Claude plugin: `palarran-mcp`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:mcp:build` | [`$palarran-mcp-build`](palarran-mcp-build/SKILL.md) | `{task/context} [profile flags]` |

## memory

Quick notes, VPS context, structured session handoffs, recall and reviewed cleanup.

Install selector: `--packages memory`. Portable Claude plugin: `palarran-memory`.

| Unified command | Native skill | Arguments |
| --- | --- | --- |
| `/palarran:memory:recall` | [`$palarran-memory-recall`](palarran-memory-recall/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:memory:learn` | [`$palarran-memory-learn`](palarran-memory-learn/SKILL.md) | `{task/context} [profile flags]` |
| `/palarran:memorize` | [`$palarran-memorize`](palarran-memorize/SKILL.md) | `{short|long} {note} [--plan]` |
| `/palarran:remember` | [`$palarran-remember`](palarran-remember/SKILL.md) | `{query} [--plan]` |
| `/palarran:memorize:session` | [`$palarran-memorize-session`](palarran-memorize-session/SKILL.md) | `[--long] [--plan]` |
| `/palarran:remember:session` | [`$palarran-remember-session`](palarran-remember-session/SKILL.md) | `[--long] @file [--plan]` |
| `/palarran:vacuum` | [`$palarran-vacuum`](palarran-vacuum/SKILL.md) | `[--long] [--plan]` |

The explicit memorize/remember/session/vacuum commands are the main context interface. Existing memory:learn/recall preserve the verified-findings workflow. Long notes/session snapshots are separate owner-context candidates; generic vacuum does not physically purge the VPS database.

## Packages being designed

These are documentation-stage designs, not installable package selectors yet.

| Planned package | Commands | Design |
| --- | --- | --- |
| `git` | `git:commit`, `git:history`, `git:conflicts`, `git:mr` | [Git workflow](../docs/git/README.md) |
| `docs` | `doc:architecture`, `doc:feature`, `doc:api` | [Documentation workflow](../docs/documentation/README.md) |

## Compatibility and scope

[Migration](../docs/setup/palarran.md). Legacy packager selectors remain aliases, not additional public commands. Scale and CI provider are arguments. Project .palarran and agent client state are private/Git-ignored. Existing package selection is preserved during updates; changing it requires a reviewed migration. Global MCP/tunnel setup and VPS deployment are distinct from installing skills.

## Incident response

Infrastructure includes `/palarran:infrastructure:incident {what happened} [--plan]` ([skill](palarran-infrastructure-incident/SKILL.md)): parallel investigation, multi-developer coordination, scoped mitigation and independent recovery checks. Optional cross-machine chat requires a configured service; installation alone grants no production access.
