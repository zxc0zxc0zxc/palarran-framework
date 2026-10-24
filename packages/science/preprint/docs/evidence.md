# Scientific evidence contract

Each claim needs ID, exact source artifact/file digest, checkpoint/model/data/config/tokenizer/decoding/protocol references, metric/units/denominator/N/slices, uncertainty method, trial/seed/selection policy, verification status and limitations. Report hashes/self-consistency do not prove honest measurements; establish grader/holdout independence separately. Correlated tokens are not independent samples; do not calculate CI from a single aggregate.

Distinguish measured/estimated/provider_reported/hypothesis/not_run. Include failed seeds, OOM/timeouts/early stops, missing-output counts and financial unknowns. Preliminary development probes are not unbiased heldout results. PPL requires actual autoregressive NLL; never publish mean-of-means or DPO exp(loss) as PPL. Do not cherry-pick snapshots: fixed paired probes expose regressions/error cases/sample size.

Authorship/affiliations/funding/ethics approval require confirmed facts only. Bibliography uses verified primary papers/docs with title/authors/year/URL/DOI where available; never invent DOI. An AI agent is not a fictitious coauthor. Related-work claims require real sources, no dummy citations. Preserve experimental code/data rights/privacy; private outputs stay out of shareable papers by default. Human review before publication is mandatory within publication scope; skills never publish automatically.

LaTeX text is untrusted: escape special characters; do not copy arbitrary report commands/macros. No shell escape/downloads/remote-bibliography execution. Compile in a bounded local/built-in environment; missing compiler means source-only NOT COMPILED. Successful compilation is layout/tool evidence, not scientific-claim PASS.
