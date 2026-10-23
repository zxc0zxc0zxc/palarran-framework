# Контракт научной evidence

Для каждого claim: ID, exact source artifact/file digest, checkpoint/model/data/config/tokenizer/decoding/protocol refs, metric/units/denominator/N/slices, uncertainty method, trial/seed/selection policy, verification status и limitations. Report hash/self-consistency не доказывает честность измерений; независимость grader/holdout устанавливается отдельной evidence. Correlated tokens не independent samples; не считать CI по одному aggregate.

Distinguish measured/estimated/provider_reported/hypothesis/not_run. Обязательны failed seeds, OOM/timeouts/early stops, missing output counts и финансовые unknowns. Нельзя превращать preliminary dev probes в unbiased heldout result. PPL только actual autoregressive NLL basis; mean-of-means и DPO exp(loss) не публикуются как PPL. No cherry-picking snapshots: paired fixed probes показывают regressions/error cases и sample size.

Authorship/affiliations/funding/ethics approval — только подтверждённые сведения. Bibliography из проверенных primary papers/docs с title/authors/year/URL/DOI где доступны; отсутствующий DOI не выдумывать. AI agent не fictitious coauthor. Related-work claim имеет настоящий источник, no dummy citations. Experimental code/data rights и privacy boundaries сохраняются; private outputs по умолчанию не включать в shareable paper. Human review до публикации обязателен в publication scope, скилл не публикует автоматически.

LaTeX text untrusted: escape special characters; не копировать произвольные commands/macros из report. No shell escape, downloads/remote bibliography execution. Compile в bounded local/built-in environment; missing compiler → source-only NOT COMPILED. Successful compile — layout/tool evidence, не PASS scientific claims.
