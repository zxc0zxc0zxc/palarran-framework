# Product pipeline v001: idea → justified MVP plan

First read the [case map](cases/README.md), [shared workflow](workflow.md), [evidence](evidence.md) and [artifact contract](pipeline-contract.md). The pipeline executes existing skills while preserving their boundaries. Superhuman/Buffer/GitLab/Ahrefs methods remain mandatory; composition and hash gates are our engineering adaptation, not those companies' stated workflow. [Sources/dates](sources.md).

```mermaid
flowchart LR
    I[Idea + project context] --> D[define: hypothesis]
    D --> M[market: demand and segments]
    M --> C[compare: alternatives and wedge]
    C --> R[revenue: economics / unknown]
    R --> A[acquisition: channels / tests]
    A --> S[palarran-product-define: synthesis MVP]
    S --> V[Independent artifact gates + final rerun]
    V --> P[plan / validate / pivot / stop]
```

Stages are serial; the cumulative prefix passes actual context/sources/ADRs; final mvp uses the same palarran-product-define with a synthesis task. No new standalone skill is added. Previous-agent summaries do not replace sources: read pinned reports/manifests/ADRs and relevant primary references. Do not regather usable evidence unnecessarily, but check freshness/contradictions.

## Running

```sh
python3 -m orchestrator product-create --idea-file /path/to/idea.md --target /path/to/product-repo --state /path/to/private-state --adapter codex --agent /absolute/path/to/codex --skills-root /path/to/palarran
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
python3 -m orchestrator status --state /path/to/private-state --run RUN_ID
```

The idea file is regular, non-symlink UTF-8, nonempty, <=32KiB, without credentials/customer PII. Create calls no model. Adapter codex/claude and installed executable are explicit; authorization stays outside the workflow. Before work, create/status shows immutable routing: all six research/synthesis stages receive the planning model (Codex gpt-6.1-sol/high or Claude opus/high), one launch each, 6 launches / 30 conditional units total. `--ai-policy` sets custom profiles/caps before create; this budgets launches. Additional `usage_policy` enables real token receipts and observed USD stops: defaults 600000 tokens/$12 per run, 100000/$2 per stage, including retries; `--usage-policy` replaces them before create. Codex cost uses an explicit pinned API-rate estimate; Claude uses reported CLI cost; neither equals an invoice/subscription. Missing telemetry stops the pipeline; unknown is not zero. Full contract: `packages/core/orchestration/docs/usage-accounting.md` in the full runtime checkout. Generic workflows support explicit task retry allocations; product defaults allocate no retries. Plain `resolve` never replenishes budget and stops the run when stage allocation is exhausted. Default PATH/HOME permits configured CLI auth/config access; this trusted workflow is not a sandbox. `--run-seconds` defaults to 7200, `--task-seconds` to 900, `--max-attempts` to 2; existing runtime maxima apply. Clarification waits consume the wall deadline; attempts never reset. Paid research/API calls are not automatically authorized; the runtime does not guarantee a dollar cap.

The source bundle of seven SKILL.md files, packages/product/research/docs, shared memory guide and packages/product/research/templates is hashed. A missing mandatory file, source symlink/bundle change, stale dependency hashes, application edits or altered Git HEAD causes verifier failure. Never edit skills root concurrently with a run; use a separate pinned checkout for stability. Runtime verifier code is trusted local code.

`product-create` creates the pipeline UUID/context and owned run worktree. An initializer writes context before pending-run admission; failure leaves work files for diagnosis without model-task execution. The original target checkout is unchanged. Status/export includes product.pipeline_id, mvp_plan path and recommendation after successful gates; market_validated=false. Results live in the worktree:

```text
.palarran/product/pipeline-<pipeline_id>/
  context.json                        # immutable idea/baseline/source digest/revision
  decisions/                          # canonical ADR, per-stage unique IDs
  stages/define/stage.json             # versioned envelope
  stages/define/report.md              # concise narrative + E/ADR refs
  stages/market/...                    # remaining stages
  stages/compare/...
  stages/revenue/...
  stages/acquisition/...
  stages/mvp/stage.json
  stages/mvp/report.md                 # final MVP plan and verdict
```

Update shared target INDEX and product INDEX without erasing existing entries. Each stage creates its own E/claim/unknown IDs and ADRs; prior-ID references are allowed, but copying IDs with a new meaning is not. A private runtime receipt pins the canonical manifest hash: the final stable rerun rejects even coordinated hash-chain rewrites. After passing a gate, a stage is immutable: downstream only reads it. Pre-gate drafts may be corrected after needs_input while preserving the previous attempt in history; never erase accepted ADRs. An observed failure without replay-safe means failed; scope revision needs a new revision/run; expired leases use existing runtime reconciliation.

## Final decision

The [MVP template](../templates/pipeline-mvp.md) structures the narrative; the artifact schema remains in the contract. The MVP report includes target/ICP/JTBD, competitor wedge, value proposition/model, scope/non-goals, requirements/AC/priorities, metric/validation plan, economics/channel assumptions, risks/open questions and UX/engineering-planning handoff. Each requirement and experiment has E/ADR references. Disposition every inherited unknown: resolved with evidence/ADR or unresolved. Never silently drop an inconvenient number/source.

`plan` is a justified recommendation for the next planning scope with no critical unresolved issues; `validate` requires a market test first; `pivot`/`stop` is a reasoned change/stop. Every verdict ends the bounded pipeline and may be artifact-verified. Always `market_validated=false`: a plan does not itself conduct user research/payments/advertising experiments. Critical business/authority ambiguity means needs_input/question.md; answer through existing resolve with a recorded reason.

Machine gates check structure/integrity/traceability and allowed changes, not source truth, sample adequacy, strategy quality or actual market readiness. Engineering start requires substantive review of reports/primary references/decisions. Runtime does not automatically start UX/build/ads/deploy.

The fingerprint includes product artifacts/decision INDEX even when target gitignore excludes .palarran; changes to those deliverables make status stale. Other ignored cache/runtime paths remain outside identity.

## B2B/B2C inside acquisition

Runtime retains define → market → compare → revenue → acquisition → mvp: six CLI attempts when each stage succeeds once. Acquisition reads/applies `/palarran:product:b2b` or `/palarran:product:b2c` within its report according to buyer/user; mixed models separate sides. No extra task/agent/CLI run or model-budget increase. The pinned source digest includes seven skill entrypoints, including both sales/growth profiles.

Before engineering, synthesis requires substantive [sellability review](go-to-market.md): small-fit candidates or a specific B2C audience/channels, supported offer, full costs/caps and an accessible inexpensive test. Unknown cash cap=0; expensive/unknown placements cannot enter the paid shortlist. After polish, update revision/claims/quotes in a separate research task, without automatic outreach.

The verifier establishes artifact integrity/traceability, not sales-narrative completeness, actual pain/revenue/price or market validation. Human/agent review must assess content; these fields do not introduce a falsely machine-verifiable market gate.

## Continuing a saved prefix

`product-continue --state STATE --target ORIGINAL_CLEAN_TARGET --source SAVED_WORKTREE --pipeline ID --through define --skills-root PINNED_ORIGINAL_SKILLS --agent /absolute/codex --route b2b --usage-policy REVIEWED_JSON --budget-ceiling ORIGINAL_USD` creates a separate owned run without invoking a model. Original target HEAD must match original context.baseline. Define/context/ADR/report/evidence are copied byte-exact; the workflow-pinned import receipt and independent original verifier run before the model stage and repeat in final checks. The former failed state is neither edited nor called verified.

Only remaining stages execute. Before each, a deterministic command materializes the complete mandatory pinned-guide package and compact upstream index with source IDs/classifications/URLs/manifest hashes. Identical guides are read once; complete original records remain available as needed before further claims. The package is not an LLM summary and does not raise confidence. New continuation/prompts have a separate workflow digest; original product context/prefix is not rewritten. A pinned import map protects prefix artifacts; indexes extend while preserving history.

Codex stages use `transport: app-server` with intermediate cumulative usage receipts. Supply reviewed carry entries for previous known/reserved-unknown spending; monetary max includes carry. Token caps change only through explicit review, never retry. Carry reserve is a scheduling allocation, not authoritative reconciliation of an old invoice/usage. `complete=false` remains visible for actual aggregates with historical unknowns even when all new attempts complete. Caps stop subsequent model launches, but one in-flight response may cross a threshold.

For new Codex pipelines, select the intermediate channel explicitly with `product-create --transport app-server`; old snapshots retain terminal-only transport. `product-continue` enables App Server for remaining stages and requires reviewed nonempty carry and explicit original monetary ceiling through --budget-ceiling. Preserve the original skill snapshot: continuation does not recalculate context/define against a new library version.
