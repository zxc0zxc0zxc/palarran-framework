# Workflow and reference CLI

`/palarran:mcp:build {tool/integration} [--plan]`: identify target separately from installed skill checkout. Read target README/AGENTS/INDEX/ADRs, actual business/API contracts and domain guides. Clarify unclear task/allowed data/side effects without asking already answered questions. Before dependent edits preserve options/rationale/sources and spec/revision. --plan writes artifacts/proposals only; no app edits/install/server/client calls/worktrees/paid APIs. Without it, perform authorized local implementation/tests, without implied remote registration/deploy.

Reference generator:

```sh
python3 scripts/mcp_build.py scaffold --spec /absolute/approved-catalog.json --output /absolute/new-project
python3 scripts/mcp_build.py validate --project /absolute/new-project
python3 scripts/mcp_build.py smoke --project /absolute/new-project
```

Scaffold/validate do not start servers. New output/no overwrite, regular canonical inputs, explicit public-source copies. Generated manifests bind files; checksums are not security boundaries. Smoke starts only exact trusted reference-server bytes with existing isolated Python, not arbitrary modified/third-party servers; it reads no credentials/env and connects no external services. Test custom SDK servers with separately authorized own tests; never manipulate manifests to pass reference smoke.

Catalog JSON version1,name,namespace,records[{id,title,text,tags}]. name/namespace lowercase identifier<=32, records1..200, unique readable IDs<=64, title<=160,text<=4096,tags<=10×32; total JSON<=1MiB. Curated approved data only, no automatic project/private corpus traversal. The synthetic [example](../../templates/mcp/catalog.example.json) is inert. Generated server.py/catalog.json/README.md/client.example.json/manifest.json are a starter, not active global configuration.

Tools: namespace.search_records(query,limit=5,cursor?,response_format=concise|detailed) with AND casefolded terms/stable-ID ordering; namespace.get_record(record_id) always returns the complete approved record. Search preserves ID/title and excerpt/full text with completeness labels; pages never truncate JSON/items. Cursor binds query/format/catalog revision/process, not an authorization token. Whole response<=64KiB, message<=64KiB, max2000 messages/session; oversized frames close the stream. Input files<=1MiB, bounded strings/records. Stdio profile has no external paths/API/writes. Local byte measurements are not actual model-token savings.

Save contracts/evals/results/remaining NOT_RUN using the [template](../../templates/mcp/build-plan.md) in target `.palarran/mcp/<task>/`; update INDEX/handoff. Actual provider SDK/version, auth, live integration and deployment require separate checks. Do not collect raw data/logs/secrets in packages/Git; sandboxes/data rights do not appear automatically.

Reference environment: Python>=3.9 + POSIX regular-file/pipe/process primitives. Choose/verify suitable SDKs/clients on other hosts. The generator does not guarantee Windows portability of this reference runtime.
