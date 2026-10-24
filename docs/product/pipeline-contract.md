# Artifact contract product pipeline v1

English JSON keys; UTF-8 docs. Numbers/strings must be finite and bounded; unknown JSON fields are forbidden. Contract for generator/verifier/tests; actual source versions use pinned SHA-256, not latest links.

## Context

`context.json`: exactly `schema_version:1`, `pipeline_id` (32 lowercase hex), `idea` (1..32768 UTF-8 bytes), `source_digest` (64 hex), `plan_revision:"product-v001"`, `baseline` (Git SHA). `context_sha256` = canonical JSON SHA (sort_keys=True, separators=(',',':'), ensure_ascii=False, allow_nan=False, UTF-8). Root path `.palarran/product/pipeline-<id>`.

## Stages and envelope

Order: `define, market, compare, revenue, acquisition, mvp`. Each `stages/<name>/stage.json` has exactly:

- `schema_version:1`, `pipeline_id`, `stage`, `revision:"v001"`, `status:"research_complete"`, `context_sha256`.
- `inputs`: object stage→canonical manifest SHA, **all** preceding stages and no others. First `{}`. The verifier rereads the entire prefix, reports/ADRs and shared source bundle; the final rerun checks the latest outcome.
- `report`: `{path,sha256}`; exact target-relative `<pipeline_root>/stages/<stage>/report.md`, nonempty Markdown <=256KiB.
- `evidence`: nonempty record list; globally unique `id` prefixed `E-<stage>-`; exact fields `id,claim,classification,source_url,publisher,published_at,retrieved_at,metric_as_of,period,geography,entity_product,unit,method,value_or_range,limitations,confidence,confidence_reason,input_ids,formula`. Classification observed/disclosed/estimated/hypothesis/scenario/unknown. Every text field nonempty <=8192 chars (explicit N/A/unknown), retrieved_at ISO date, confidence low/medium/high. source_url is HTTP(S) without credentials/query/fragment, or `artifact:context` (pinned context.json) / `artifact:decision/<canonical-id>` (already checked current/prefix ADR). Unknown local references are forbidden. observed/disclosed/estimated require a reference; others permit null. Local URIs express user intent/decision basis, not market-demand proof. Input E-IDs must exist in current/prefix and form an acyclic graph; hypothesis/scenario require input_ids, scenario also a nonempty formula. Unknown value must be `unknown`, never zero.
- `decisions`: nonempty list `{id,path,sha256,status}`, status accepted/proposed. Canonical file within `<pipeline_root>/decisions/`, unique ID/path; id/status match Markdown metadata, all six shared ADR headings mandatory. ID appears in target `.palarran/INDEX.md`; pipeline ID appears in product INDEX. Paths/bytes pinned; duplicates forbidden.
- `claims`: nonempty list `{id,text,evidence_ids,decision_ids}`, prefix `C-<stage>-`, references resolve in cumulative closure. Evidence references nonempty; decision references may be empty for descriptive claims. Orphan references/duplicate IDs forbidden.
- `unknowns`: list `{id,question,critical}`, prefix `U-<stage>-`, boolean critical. Declared unknowns cannot disappear from the final decision.
- `verdict`: null before mvp; final exactly `{recommendation,market_validated,unresolved,resolutions}`. Recommendation plan/validate/pivot/stop; market_validated literal false. Unresolved lists unique unknown IDs from closure; resolutions are `{id,evidence_ids,decision_ids}` with observed/disclosed evidence references and an accepted decision reference. Resolved/unresolved partition **all** unknowns without duplicates. Critical unresolved issues forbid `plan`.
- `requirements`: [] before mvp; final nonempty list `{id,description,acceptance,priority,evidence_ids,decision_ids}`, prefix R-mvp-, priority must/later; nonempty evidence+decision references.
- `experiments`: [] before mvp; final nonempty list `{id,hypothesis,metric,threshold,window,budget,stop,evidence_ids,decision_ids}`, prefix T-mvp-, nonempty text/references. Proposed cards, not completed experiments.

Each JSON <=1MiB, each collection <=100 records (evidence/claims/requirements/experiments/unknowns/decisions), strings <=8192 chars; bounded relative POSIX paths, no `..`, symlinks or escaping. Regular files only; bounded reads. Strip source-URL query only if a faithful stable canonical locator remains; if a query is essential for an exact reference, use a safe artifact reference in narrative and explicit limitation rather than falsifying the link.

## Frozen Python API and CLI verifier

`orchestrator/product_artifacts.py` — standalone stdlib module, agent-owned:

```python
STAGES = ('define', 'market', 'compare', 'revenue', 'acquisition', 'mvp')
def canonical_sha(value): ...
def source_digest(skills_root): ...
def pipeline_dir(root, pipeline_id): ...
def validate_stage(root, pipeline_id, stage, expected_context_sha, skills_root):
    # returns final checked manifest, raises ValueError/OSError on failure
    ...
```

`source_digest` includes reviewed `skills/palarran-product-*/SKILL.md` for seven skills (define, market, compare, revenue, acquisition, b2b, b2c), all docs/product/**/*.md, docs/skills/decision-memory.md, templates/product/*.md. Hash the sorted relative-path→content-hash map canonically; reject symlinks/missing mandatory profiles/cases/pipeline guides/templates. `pipeline_dir` validates UUID and returns a confined path.

Verifier CLI: `python3 /absolute/palarran/orchestrator/product_artifacts.py --root . --pipeline ID --stage STAGE --context-sha SHA --skills-root /absolute/palarran`; successful stdout is exactly `PASS <canonical_sha(checked_manifest)>` + newline, without timestamps. Runtime task verify_stable=true stores an independent receipt digest in the private DB and compares the final rerun; coordinated rewrites of all workspace manifest/hash links still change the receipt. Exit 0 means artifact-contract PASS. Errors print safe generic messages, not raw artifact content. Max 6 stages; IDs/references must be more than search mentions in prose.

Planning scope guard: current HEAD == context.baseline; changed tracked/untracked paths (including ignored) are confined to the current pipeline root, shared .palarran/INDEX.md and .palarran/product/INDEX.md, and runtime .palarran/factory/. Git/path-containment checking guards a trusted agent; it is not an isolation sandbox and does not control external side effects. Create ignored artifacts outside workspace through TMPDIR. No Git commits/build/deploy/app edits.

Coordinator owns `orchestrator/product_pipeline.py`: `build(idea, skills_root, adapter, executable, *, python=None, limits=None, env=None, pipeline_id=None, baseline=None) -> (workflow, context)`; `create_product(state, idea, target, skills_root, adapter, executable, **options) -> run_id`. `baseline` is mandatory for build (ValueError when absent); create_product determines HEAD. Builder generates six task prompts + independent verifier argv; `replay_safe=false`. Default env PATH/HOME, explicit adapter/executable; default limits run7200/task900/lease30/attempts2/output1MiB. Initialize context before Store.add; create calls no provider.

Acquisition report includes the applicable B2B/B2C sales/growth plan under go-to-market.md; schema/stage ID stays acquisition. Source bundle explicitly requires new guides/cases/templates and rejects missing mandatory files. The schema does not validate substantive sellability/buyer-list completeness; review remains mandatory and this extension establishes no market validation.
