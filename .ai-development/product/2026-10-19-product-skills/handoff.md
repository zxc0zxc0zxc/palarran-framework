# Product skills: handoff

## Что создано и почему

Docs-first baseline `07af290` создан **до** любых новых product skills. В docs/product/: five profiles, five case guides, case map, evidence/workflow/data/API/source guides. Templates: brief/research/competitors/economics/channels. Accepted rationale: product/2026-10-19-product-skills/0001..0006, общий INDEX.

Startup-first cases: Superhuman (ICP/survey/roadmap, founder account), Buffer (early validation и disclosed economics), Airbnb (early investor account), Ahrefs (product-led content). GitLab помогает JTBD-comparison; Amazon — customer narrative; Google — user-centered metrics; Microsoft — trustworthy experiment design. SweetyTreatyCo — отдельный vendor-selected TikTok SMB case, с переносимостью/attribution limits. Компания успешна не значит каждая тактика causal proof.

Созданы product-define/market/compare/revenue/acquisition, slash adapters `/product:*`, Codex discovery symlinks и self-contained plugin product. Все требуют профильные cases/docs, E-ID evidence, canonical target ADR/revisions/index/handoff, unknown vs estimates/scenarios, отдельные permissions для платных/внешних действий. Existing engineering runtime не менялся.

## Проверки

- `python3 scripts/validate_repo.py`: PASS; 16 skills/adapters, 7 namespaces; Markdown links/cases/decisions checked.
- `python3 -m unittest discover -s tests -q`: PASS, 104 tests; materialized product package tested for links/containment/no symlinks/no memory/no runtime spill. Existing suites passed.
- skill-creator quick_validate: PASS на всех пяти новых skills; YAML frontmatter valid.
- `python3 -m py_compile scripts/validate_repo.py scripts/package_plugin.py`: PASS.
- Mermaid 11 syntax parse: 2 diagrams PASS; не visual render evidence.
- Live provider integrations/real target market validation/ad campaigns: NOT_RUN. Ни один API не подключён, SDK/MCP не устанавливались, credits не расходовались.

## Ограничения и следующее применение

API catalog проверен 2026-10-19: Google Trends alpha approval, актуальный Google Ads Cloud/OAuth access, Meta/TikTok archive coverage, Similarweb/Appfigures entitlements и SEC public-data rules. Это factual access research, не подключение аккаунтов. Recheck before use. Search snippets/недоступные cases не использованы для verified numeric results; exclusions записаны в sources.

Следующая сессия читает общий INDEX, product catalog, accepted ADR и actual target README. Можно вызвать один product skill с бизнесом/регионом/аналогами; он создаёт target-specific report/evidence/revisions. Пока есть только reusable authoring capability: нет готового product idea, measured demand, private competitor revenue или proven CAC.

Release commit/CI фиксируются после публикации; docs baseline сохранён отдельно для проверки порядка.
