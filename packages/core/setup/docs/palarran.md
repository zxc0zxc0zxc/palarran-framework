# Palarran interface and compatibility

Basis: explicit user naming and interface choices,2026-10-24. The official [Claude plugin manifest reference](https://code.claude.com/docs/en/plugins-reference), checked2026-10-24, supports command map keys after a plugin prefix. The installed offline validator accepted the nested `infra:plan` key; this is not evidence of a model executing the command. Codex native skill names use lowercase hyphenated identifiers.

## Canonical names

- Repository: `palarran-framework`; brand: Palarran.
- Target decisions, plans and context: hidden `.palarran/INDEX.md` with the existing domain/task hierarchy. Preserve historical IDs and provenance.
- Unified plugin commands: `/palarran:setup`, `/palarran:infra:plan low|med|high`, `/palarran:ci-cd github|gitlab`, and `/palarran:domain:action`.
- Codex native examples: `$palarran-setup`, `$palarran-infra-plan low`, `$palarran-ci-cd github`, `$palarran-backend-plan`. Plugin slash syntax is a separate interface.
- Infrastructure scale and CI provider are arguments. Preserve profile guides, permissions and the domain-specific meaning of `--plan`. `medium` is an input alias for canonical `med`.

## Existing projects

Use `.palarran` for new work. If `.ai-development` exists, first read its INDEX and accepted ADRs as legacy history. Do not delete or relocate a user's project history implicitly. Link the old index from the new one. This framework repository's journal is moved under the owner's explicit migration request, preserving untracked work and unrelated changes.

The private pinned library and ownership receipt remain in `.ai-tools` for compatibility with the safe updater. This internal store is not a second decision journal. Moving it alongside the brand without a transactional migration would break project MCP paths, managed instructions and rollback references.

Updates remove only owned unchanged old discovery links/files and add the new names. Conflicting local skill edits produce CONFLICT and remain intact. A rename never authorizes restarting old product/ML runs: preserve their source digests, budget and unknown-outcome state. Existing runs use their original pin; historical names remain valid provenance.

## Global profile

The requested canonical home is `~/.palarran`, with global `config.json` and private `.env`; each target has its own `.palarran/config.json`. See [packages and languages](configuration.md). The owner explicitly authorized migration from the old personal directory. Future project setup does not imply a global move.

A real migration must preserve all private files, owner policy, dedup ledgers, pending intents, backups and pinned runtimes. Preflight existing configuration and ownership; stop the owned login tunnel, move the directory on the same filesystem, update owned MCP/helper/LaunchAgent references to a verified new runtime, then restart the tunnel and perform metadata/read-only memory checks. Do not leave credential reads depending on an old-home symlink: secure readers reject symlink ancestors. Do not rewrite immutable historical source pins or replay old runs. If an operation fails, restore backed-up configuration and the prior directory before declaring recovery.

Current diagrams show this requested canonical layout. They are not proof that a particular machine was migrated. Source-path changes, actual private-state movement and connectivity evidence are separate checklist items.

## Public release boundaries

English is the canonical source-language policy; configured locales control interaction and newly generated artifacts, not source translation forks. Historical journals retain their original evidence and language. A complete guide translation is tracked separately from setting a locale preference.

README and catalogs describe the chosen interface and verified capabilities. Preparing for open source does not change repository visibility or select a license; do not claim MIT, Apache or redistribution rights without the actual license decision.
