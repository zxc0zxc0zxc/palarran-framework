# Contributing to Palarran

Start with AGENTS.md, .palarran/INDEX.md and docs/skills/domain-contracts.md. Read the AGENTS of every affected module. Canonical source code, guides and skill instructions use English. Locale preferences apply to generated project artifacts and interaction.

Write source-backed documentation before implementation. Record each accepted decision with rationale, evidence, alternatives and consequences in target .palarran before dependent changes; preserve historical records. Graphify is optional: bounded fresh queries guide navigation, original files remain authoritative.

Keep skills/catalog.json, unified and domain manifests, adapters, discovery links, validator registration and packager resources aligned. Native skills use hyphenated names; plugin command aliases are a separate interface. Do not rename durable runtime task IDs for branding.

Run `python3 scripts/validate_repo.py` and `python3 -m unittest discover -s tests -v`; also run `python3 scripts/factory_acceptance.py` after runtime-facing changes. Provider-facing tests use fake transports, without paid APIs, GPUs or live infrastructure apply. Report missing optional checks as NOT_RUN.

Keep secrets, raw sessions/logs, customer data, runtime state, weights, checkpoints and private datasets out of Git and fixtures. Portable packages exclude target memory. Do not change global configuration without explicit scope or launch outreach, deployments, purchases or paid experiments from an ordinary contribution task.

Public interface changes need migration notes and checks preserving local edits. The library checkout, target project and project journal are distinct roots. A license has not yet been selected; this guide does not imply a public release or replace a license.
