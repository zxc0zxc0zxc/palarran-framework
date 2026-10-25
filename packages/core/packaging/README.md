# Core: Packaging

Create and manage reviewed custom packages without changing the eleven built-in package identities. The registry is a private self-hosted HTTP API with immutable versions, scoped visibility and content-addressed archives; it is not an S3 protocol server.

[Contract](docs/contract.md) · [Architecture and workflow](docs/README.md) · [Sources](docs/sources.md) · [Create](docs/create.md) · [Lifecycle](docs/lifecycle.md) · [Operations](docs/operations.md)

Native Claude: `/palarran-package-create`, `/palarran-package-search`, `/palarran-package-install`, `/palarran-package-update`, `/palarran-package-uninstall`, `/palarran-package-list`. Unified plugin aliases: `/palarran:package:create|search|install|update|uninstall|list`.

Implementation, tested local behavior and real deployment are separate statuses. Selecting Core never activates a registry, downloads a third-party package or grants publication credentials.
