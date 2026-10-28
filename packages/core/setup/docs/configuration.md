# Packages and language preferences

Palarran maintains one English source library. Installation asks which skill packages to enable and which languages to use for skill interaction, generated code comments, and generated documentation. Supported values are `en`, `ru`, and `sr-Latn` (Serbian Latin).

Language settings do not translate programming-language keywords or rename existing APIs. Existing project conventions and accepted decisions remain authoritative; explain conflicts before changing them. Source skill and guide files remain English for every locale. Newly generated application documentation follows `languages.docs`; agent explanations follow `languages.skills`; new code comments and human-facing development notes follow `languages.code`.

## Configuration and precedence

Global defaults live in `~/.palarran/config.json`. Project settings live in `<project>/.palarran/config.json`. Explicit installation options override project values, which override global values. Secrets belong in private `.env` files, never configuration JSON. Do not copy global credentials into projects.

```json
{
  "version": 1,
  "packages": ["code", "validation"],
  "languages": {"skills": "en", "code": "en", "docs": "en"}
}
```

Fresh installations use the public IDs in [the package catalog](../../../catalog.json): `core`, `memory`, `product`, `design`, `code`, `machine-learning`, `docs`, `science`, `validation`, `infrastructure`, and `security`. Each other package currently requires `core`; dependency resolution records the exact installed scope in the receipt. Core includes setup. Use `["all"]` only after an explicit choice; it cannot be mixed with individual IDs. Legacy names such as `backend`, `app`, `ml` and `infra` are compatibility inputs for eligible old receipts/releases, not fresh public package IDs.

Configuration schema version remains `1`; the receipt's package-selection version is separate. `packages` must be a nonempty list of distinct IDs. `languages` accepts only `skills`, `code`, and `docs`, each using `en`, `ru`, or `sr-Latn`. Partial preferences may be inherited, but fresh setup requires a resolved package selection and all three language fields. Unknown top-level fields are preserved; duplicate JSON keys, invalid values and unsafe paths are rejected. Package applicability is checked against the pinned catalog during selection, not inferred from a similarly named skill.

Shared guides and helper resources may remain in the pinned library to preserve cross-domain links; only selected skills receive native discovery links.

On a first interactive setup, ask for missing package and language preferences. In automation, supply explicit flags or checked configuration. Existing legacy installations retain their original scope until a reviewed selection change. An update must not silently widen the installed skill set. Preserve unrelated JSON fields and project-local changes; conflicting managed files stop before replacement.

## Safety and evidence

`setup --plan` reads configuration and the pinned source, checks local ownership, and computes the proposal without creating directories, editing files, executing application code, or contacting memory. With complete valid inputs it returns exit `0`, `PLANNED`, `writes: 0`, `network: false`, and `model_calls: 0`. Missing choices return exit `2` with `missing_preferences` and a packages/language remedy; this is not a request to guess defaults or modify global settings.

Fresh modern setup defaults to local mode in an existing Git repository. Git-local excludes must protect private outputs; explicit `--mode project` selects shared instruction/MCP changes. Existing receipts retain their mode and exact package/language selection. Unselected optional memory returns `NOT_SELECTED` without a probe; explicitly selected unhealthy memory remains `*_MEMORY_NOT_READY`/exit `2` after file installation. Never replay installation to repair a connection. File installation and memory connectivity are separate outcomes. A successful metadata check proves wire connectivity, not client UI discovery, application quality, or paid quota availability.

JSON serialization uses the [Python standard library](https://docs.python.org/3/library/json.html). The precedence and locale semantics above are Palarran policy, not vendor guarantees. Existing ownership and rollback behavior is documented in [setup](README.md).

## Optional parallel execution engine

Ask **Enable the Temporal engine for parallel execution?** when no existing project/global answer is recorded. The user's explicit `0`/`1` choice is separate from packages and locale settings. [Temporal configuration and actual harness levels](temporal.md) define atomic env-profile inheritance, private credential references and the read-only injected connection check. Saving a global switch requires actual global configuration authority. No setting deploys a server or starts paid models. Ordinary requests and every skill receive the same common parallelism instructions; native instruction-based integration is never presented as enforced interception.

## Fast offline feedback regressions

From a complete trusted checkout:

```sh
python3 -m unittest discover -s tests -p 'test_feedback*.py' -v
```

This focused suite checks the production-feedback regressions with offline fixtures and mocked external services. It starts no paid models, training or live deployment. Allow roughly 20 seconds as a machine-specific planning estimate; actual time varies with the checkout, hardware and test count. Its PASS is a quick regression signal, not full acceptance: run the repository validator, full test suite and any applicable domain/runtime checks before declaring the change verified. No fixture result establishes native client discovery, live multi-machine behavior or an operational SLA.
