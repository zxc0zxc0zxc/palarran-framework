# Create a custom package

1. Choose publisher/name, explicit public/private visibility, built-in prerequisites and intended users. Inspect the target instructions and applicable project rules; preserve rationale in target `.palarran/`.
2. Write docs first: purpose, real boundaries, source references, architecture and permission model. Then freeze a versioned plan, acceptance/edge cases and task ownership. Follow Core capability organization; external archives use `capabilities/<id>/` rather than inserting unknown IDs into the trusted built-in catalog.
3. Implement the planned capability and its namespaced skills/resources. Each skill has a concise English SKILL.md, mandatory source guides and testable boundaries. A scaffold is DRAFT, not a verified product. No secrets, raw sessions or generated state belong in a bundle.
4. Run source-appropriate author tests under actual task authorization. Record exact subject/checks/limitations; a README naming tests is not evidence they ran. Review public license, provenance and private information.
5. Build and inspect the exact immutable archive. Publishing is a separate explicit action on the selected registry. Retain its request ID and reconcile an unknown reply; do not generate another operation to force success.

Creation itself never runs arbitrary package tests, executes archive hooks, provisions a server or publishes by default. Public packages require LICENSE and a meaningful license declaration. Private packages still need reviewed rights/access and cannot borrow another publisher's identity.

```text
package/
  palarran-package.json
  README.md
  AGENTS.md
  LICENSE                    # required for public
  docs/{README,plan,decisions}.md
  tests/README.md
  capabilities/<id>/
    docs/README.md
    skills/palarran-x-<publisher>-<package>-<skill>/SKILL.md
```

Use the CLI's create/build modes only after reviewing their exact parameters. The `package:create` skill orchestrates docs→plan→implementation→tests; it does not claim the deterministic scaffold implements a business capability.

Source refresh/build omits known local authoring caches such as `__pycache__` and `node_modules`; it never deletes them. These paths and bytecode/state/checkpoint files cannot be included explicitly in a distributed archive. Review the final manifest file list; all other payload extras still require explicit hashes.
