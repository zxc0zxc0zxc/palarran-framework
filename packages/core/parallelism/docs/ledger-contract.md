# Local ledger extension contract

The Dispatcher owns execution policy. `dispatcher.ledger` exposes the trusted local SQLite transaction boundary for cooperating capabilities; it does not grant remote authority or create another budget.

`SQLiteLedger(path, read_only=False, timeout=30)` is inert until `initialize()` or `transaction()`. Dispatcher initialization explicitly initializes the unchanged v001 schema. A read-only ledger never creates directories, initializes a database, changes pragmas or upgrades state. The timeout defaults to the original 30 seconds; interactive read-only consumers may select a shorter timeout, such as 2 seconds.

- `transaction()` yields a `sqlite3.Connection` with `sqlite3.Row` results. Writable transactions retain `BEGIN IMMEDIATE`, full synchronization, commit on success and rollback on any exception. Read-only transactions use SQLite URI `mode=ro` and `BEGIN`.
- `read_run(db, run_id)` returns `(row, decoded_manifest)` or raises the existing `Unknown run` error.
- `read_tasks(db, run_id)` returns task rows in registration order; `read_task(db, run_id, task_id)` returns one row or `None`.
- `update_task_contracts(db, run_id, task_contracts)` replaces only unattempted pending/ready pins within that same transaction and returns their previous packets; a later failure rolls back the entire wave.
- `project_task(row)` returns the existing bounded public task report with unchanged evidence hashes and reason redaction.

Keep reads and dependent writes inside the same caller-owned transaction. Do not open a second ledger connection inside a transaction or call external verifiers while holding the lock. Recheck authority, subject and generation after callbacks. Capability SQL stays explicit, parameterized and in the same existing authority; this port is not an ORM or public HTTP API.

Compatibility Dispatcher helpers delegate to this port. New consumers use the public port. State enums derive from `str` and retain existing JSON/SQL values; they do not authorize transitions or migrate older state.
