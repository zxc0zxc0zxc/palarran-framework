# Artifact contract product pipeline v1

English JSON keys; UTF-8 docs. Числа/строки конечны и bounded, unknown JSON fields запрещены. Контракт для генератора/verifier/tests; actual source versions pinned SHA-256, не ссылка на latest.

## Context

`context.json`: exactly `schema_version:1`, `pipeline_id` (32 lowercase hex), `idea` (1..32768 UTF-8 bytes), `source_digest` (64 hex), `plan_revision:"product-v001"`, `baseline` (Git SHA). `context_sha256` = canonical JSON SHA (sort_keys=True, separators=(',',':'), ensure_ascii=False, allow_nan=False, UTF-8). Root path `.ai-development/product/pipeline-<id>`.

## Stages и envelope

Порядок `define, market, compare, revenue, acquisition, mvp`. Каждый `stages/<name>/stage.json` exactly:

- `schema_version:1`, `pipeline_id`, `stage`, `revision:"v001"`, `status:"research_complete"`, `context_sha256`.
- `inputs`: object stage→canonical manifest SHA, **все** preceding stages и только они. Первый `{}`. При проверке verifier перечитывает весь prefix, reports/ADR и общий source bundle; final rerun проверяет последний outcome.
- `report`: `{path,sha256}`; target-relative exact `<pipeline_root>/stages/<stage>/report.md`, непустой Markdown <=256KiB.
- `evidence`: непустой list records; `id` prefix `E-<stage>-`, уникален глобально; поля exactly `id,claim,classification,source_url,publisher,published_at,retrieved_at,metric_as_of,period,geography,entity_product,unit,method,value_or_range,limitations,confidence,confidence_reason,input_ids,formula`. Classification observed/disclosed/estimated/hypothesis/scenario/unknown. Все text поля непустые <=8192 chars (N/A/unknown явно), retrieved_at ISO date, confidence low/medium/high. source_url — HTTP(S) без credentials/query/fragment либо `artifact:context` (pinned context.json) / `artifact:decision/<canonical-id>` (уже проверенный current/prefix ADR). Неизвестные local refs запрещены. Для observed/disclosed/estimated требуется reference, null допустим для остальных. Local URI отражает user intent/decision basis, не доказательство рыночного спроса. Input E-IDs должны существовать в current/prefix и образовывать acyclic graph; hypothesis/scenario требуют input_ids, scenario также nonempty formula. unknown value только `unknown`; нельзя подменить нулём.
- `decisions`: непустой list `{id,path,sha256,status}`, status accepted/proposed. Canonical file внутри `<pipeline_root>/decisions/`, unique ID/path; id и status совпадают с Markdown metadata, все шесть headings shared ADR обязательны. ID найден в target `.ai-development/INDEX.md`; pipeline ID — в product INDEX. Paths/bytes pinned, duplicates запрещены.
- `claims`: непустой list `{id,text,evidence_ids,decision_ids}`; prefix `C-<stage>-`, refs разрешаются в cumulative closure. Evidence refs непусты, decision refs могут быть пусты для descriptive claims. orphan refs/duplicate IDs запрещены.
- `unknowns`: list `{id,question,critical}` с prefix `U-<stage>-`, bool critical. Объявленный unknown не исчезает из final decision.
- `verdict`: null до mvp; final exactly `{recommendation,market_validated,unresolved,resolutions}`. Recommendation plan/validate/pivot/stop, market_validated literal false. Unresolved — unique unknown IDs из closure; resolutions — `{id,evidence_ids,decision_ids}`, с evidence refs observed/disclosed и accepted decision ref. Resolved/unresolved разбивают **все** unknowns без дубликатов. `plan` запрещён при critical unresolved.
- `requirements`: [] до mvp, final непустой list `{id,description,acceptance,priority,evidence_ids,decision_ids}`, prefix R-mvp-, priority must/later; evidence+decision refs непустые.
- `experiments`: [] до mvp, final непустой list `{id,hypothesis,metric,threshold,window,budget,stop,evidence_ids,decision_ids}`, prefix T-mvp-, text fields nonempty, refs непустые. Это proposed cards, не completed experiments.

Каждый JSON <=1MiB, коллекция <=100 записей (evidence/claims/requirements/experiments/unknowns/decisions), strings <=8192 chars; paths bounded relative POSIX, без `..`, symlinks и escaping. Regular files only; чтение bounded. Source URL query отсекать только если остаётся faithful stable canonical locator; если query необходим для точной ссылки — safe artifact ref в narrative и explicit limitation, не подделывать ссылку.

## Frozen Python API и CLI verifier

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

`source_digest` включает reviewed `skills/product-*/SKILL.md` для семи skills (define, market, compare, revenue, acquisition, b2b, b2c), все docs/product/**/*.md, docs/skills/decision-memory.md, templates/product/*.md. Sorted relative path→content hash map hashed canonical; reject symlinks/missing mandatory profiles/cases/pipeline guides/templates. `pipeline_dir` validates UUID and returns confined path.

Verifier CLI: `python3 /absolute/ai-tools/orchestrator/product_artifacts.py --root . --pipeline ID --stage STAGE --context-sha SHA --skills-root /absolute/ai-tools`; Успешный stdout exactly `PASS <canonical_sha(checked_manifest)>` + newline, без timestamps. Runtime task verify_stable=true сохраняет independent receipt digest в private DB и сравнивает с final rerun; согласованная перезапись всех workspace manifest/hash ссылок всё равно изменит receipt. Exit 0 означает artifact contract PASS. Ошибки печатают safe generic message, не raw artifact contents. Max stages 6; IDs/refs не просто поисковые упоминания в prose.

Planning scope guard: current HEAD == context.baseline; изменённые tracked/untracked (включая ignored) paths только текущий pipeline root, общие .ai-development/INDEX.md и .ai-development/product/INDEX.md и runtime .ai-development/factory/. Проверка Git и path containment — guard для trusted agent, не isolation sandbox; внешние side effects не контролируются этим diff. Игнорируемые artifacts создавать вне workspace через TMPDIR. No Git commits/build/deploy/app edits.

Coordinator owns `orchestrator/product_pipeline.py`: `build(idea, skills_root, adapter, executable, *, python=None, limits=None, env=None, pipeline_id=None, baseline=None) -> (workflow, context)`; `create_product(state, idea, target, skills_root, adapter, executable, **options) -> run_id`. `baseline` обязателен build (ValueError если отсутствует), create_product определяет HEAD. Builder генерирует six task prompts + independent verifier argv; `replay_safe=false`. Default env PATH/HOME, adapter/executable explicit; default limits run7200/task900/lease30/attempts2/output1MiB. Initialized context before Store.add, create не вызывает provider.

Acquisition report включает применимый B2B/B2C sales/growth plan по go-to-market.md; schema/stage ID остаются acquisition. Source bundle требует новые guides/cases/templates явно, отсутствие обязательного файла отклоняется. Содержательная продаваемость/полнота списка покупателей не валидируется схемой и требует review; никакого подтверждения market validation этим расширением.
