# Start the contract from the task

Following [E-MCP-001](sources.md), start with concrete agent tasks and observable success/failure. Inspect existing services/SDK/client conventions; do not build one tool per endpoint/table. One workflow tool fits when scope/errors stay clear; small composable read tools suit separate states. Never combine reading with unexpected send/delete/charge. Do not change the product for agent convenience.

Use namespace.verb_object, clear domain nouns and stable IDs. Description: purpose, when to use, required IDs/filters, returned data, important limitations/side effects. Not marketing copy or a full API manual. For each argument specify type/unit/enum/bounds, required/default and unknown-property policy; examples cover happy/error/ambiguous cases. Preserve selection IDs even in concise output. Do not require UUIDs when a human gives an unambiguous name that the tool can explicitly resolve; return alternatives for ambiguity.

Output schema defines machine-readable results with provenance/version, sufficient next-step fields, pagination and explicit completeness. Distinguish not found, permission denied, invalid input, unavailable/rate limited; errors are actionable/sanitized without stack traces/bodies/credentials. Do not return “success” text instead of observable results. Mutations need testable postconditions, idempotency keys/unknown outcomes/reconciliation and server-side authorization. Annotations describe rights but never enforce them.

Choose SDK/language from existing project stack, supported official SDK/version and minimum operational complexity; [SDK index](https://modelcontextprotocol.io/docs/sdk). Local stdio suits developer-owned tools; remote HTTP needs separate auth/transport/deploy design. The reference readonly catalog illustrates contracts, not a default backend architecture. Its `search_records` searches data, not tool-schema discovery.

## Usage examples

For reference namespace support, these are tools/call params, not shell commands or a real external-system request:

```json
{"name":"support.search_records","arguments":{"query":"deployment","limit":2,"response_format":"concise"}}
```

Take the stable ID from items; if content_complete=false, read the record for a complete answer:

```json
{"name":"support.get_record","arguments":{"record_id":"deployment-guide"}}
```

limit="all" violates the contract: the known tool returns isError/invalid_arguments. Use a bounded number; do not alter schema/ignore errors to pass. With has_more, copy next_cursor using the same query/response_format. Keep examples near contracts/host-supported instructions; do not add arbitrary provider input_examples/defer_loading fields to standard MCP tools/list.
