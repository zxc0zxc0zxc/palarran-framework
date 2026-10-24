# Feature validation and ledger boundary

Feature metadata validation is separate from execution. `feature_validation.validate_passport(passport, *, manifest, tasks)` normalizes a bounded JSON copy and checks the exact frozen repositories, budget, owners, service boundaries, contracts, task graph, acceptance slots, business invariants and release transitions. Its inputs are ordinary in-memory mappings. It opens no database and never starts a worker or performs network I/O.

The validation helpers run in the existing order and retain canonical JSON, error types and messages. This is a maintainability refactor; accepted passport shapes, hashes and stored rows do not change. Named helpers isolate one boundary so a contributor can review or extend it without tracing database control flow.

`FeatureAuthority` gathers root snapshots through the public Dispatcher ledger interface inside the same transaction, then calls the pure validator. It owns only feature metadata. Root task pin changes use the ledger's guarded operation, retaining the unattempted pending-task constraint and the shared rollback boundary. Verifier callbacks still run outside transactions with bounded deep copies; composition and root ownership are rechecked afterwards.

Use `FeatureAuthority.read_only(dispatcher, run_id)` for reports. This constructor performs no schema initialization and uses a query-only ledger connection; mutations fail closed. Normal construction initializes the feature table explicitly. Existing state remains readable without migration.

Tests compare old and new validation outcomes on valid and malformed passports, compare canonical hashes, and exercise actual SQLite lifecycle, callback, cancellation, unknown-spend and composition-fencing regressions. Structural tests do not establish production deployment health.
