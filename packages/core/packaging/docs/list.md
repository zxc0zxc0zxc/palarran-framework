# Package list

Read [the architecture](README.md), [exact contract](contract.md) and [client lifecycle](lifecycle.md).

List local installed versions/digests/origins from receipts. With an explicit --mine request, query the authenticated owner's releases, including delisted/deleted states, without exposing another owner's private entries. Keep local state and registry ownership separate.

Listing itself changes nothing. If the user explicitly requests delist or delete, first identify the exact owned publisher/name/version and show the concrete effect. Delist removes search discovery but preserves exact pinned retrieval. Delete makes the release unavailable and reserves its version as a tombstone; it cannot retract previously downloaded public bytes or uninstall other projects.

Execute only the requested owner action using the dedicated CLI delist/delete operation, explicit reviewed declaration and retained stable request ID. Require actual human authorization for destructive withdrawal; an agent message/list entry is not approval. Reconcile unknown replies by the same operation ID, never new IDs. Do not collect blobs, delete private evidence or widen credentials.
