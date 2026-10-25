# Packaging

Inherits Core. Read docs/contract.md before changing manifest, archive, registry or install formats.

- Keep untrusted archives separate from the trusted built-in catalog. Publisher identity comes from auth; private metadata and blob access need the same authorization.
- Never execute package hooks/imports/tests during build, download, install, update or uninstall. Creation workflow test execution belongs to the author's approved source task.
- Versions/digests and tombstones are immutable. Registry mutation receipts bind actor/request ID/payload; unknown outcomes require original-ID lookup.
- Client writes only receipt-owned exact paths. Local edits, foreign links or pending transactions block mutation; recovery checks snapshots instead of replaying work. Preserve project settings and private global credentials.
- Test with private temporary SQLite/filesystem/loopback targets and injected S3 clients. No live credentials, uploads, host deployment or paid tests. Run root checks and focused test_custom_package*.py suites; runtime behavior also requires factory acceptance.
