# Packages and language preferences

Palarran maintains one English source library. Installation asks which skill packages to enable and which languages to use for skill interaction, generated code comments, and generated documentation. Supported values are `en`, `ru`, and `sr-Latn` (Serbian Latin).

Language settings do not translate programming-language keywords or rename existing APIs. Existing project conventions and accepted decisions remain authoritative; explain conflicts before changing them. Source skill and guide files remain English for every locale. Newly generated application documentation follows `languages.docs`; agent explanations follow `languages.skills`; new code comments and human-facing development notes follow `languages.code`.

## Configuration and precedence

Global defaults live in `~/.palarran/config.json`. Project settings live in `<project>/.palarran/config.json`. Explicit installation options override project values, which override global values. Secrets belong in private `.env` files, never configuration JSON. Do not copy global credentials into projects.

```json
{
  "version": 1,
  "packages": ["backend", "frontend", "app"],
  "languages": {"skills": "en", "code": "en", "docs": "en"}
}
```

Package identifiers match the domain inventory (`backend`, `frontend`, `product`, `ml`, `science`, `agent`, `app`, `infra`, `ci-cd`, `ux`, `ui`, `mcp`, `memory`, `vps`, `setup`). The setup skill is always available. `all` is an explicit selection, never an implicit user answer. Shared guides and helper resources may remain in the pinned library to preserve cross-domain links; only selected skills receive native discovery links.

On a first interactive setup, ask for missing package and language preferences. In automation, supply explicit flags or checked configuration. Existing legacy installations retain their original scope until a reviewed selection change. An update must not silently widen the installed skill set. Preserve unrelated JSON fields and project-local changes; conflicting managed files stop before replacement.

## Safety and evidence

`--plan` reads configuration and computes the proposal without creating directories, editing files, or contacting memory. File installation and memory connectivity are separate outcomes. A successful metadata check proves wire connectivity, not client UI discovery, application quality, or paid quota availability.

JSON serialization uses the [Python standard library](https://docs.python.org/3/library/json.html). The precedence and locale semantics above are Palarran policy, not vendor guarantees. Existing ownership and rollback behavior is documented in [setup](README.md).

## Optional parallel execution engine

Ask **Enable the Temporal engine for parallel execution?** when no existing project/global answer is recorded. The user's explicit `0`/`1` choice is separate from packages and locale settings. [Temporal configuration and actual harness levels](temporal.md) define atomic env-profile inheritance, private credential references and the read-only injected connection check. Saving a global switch requires actual global configuration authority. No setting deploys a server or starts paid models. Ordinary requests and every skill receive the same common parallelism instructions; native instruction-based integration is never presented as enforced interception.
