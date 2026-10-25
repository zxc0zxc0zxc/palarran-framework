# Custom package author plan

Status: DRAFT
Publisher/name: choose explicitly
Version: stable major.minor.patch
Visibility: public or private, selected before publishing

## Documentation first
User outcome, capability boundaries, current project rules, primary sources and applicability, allowed tools/data, public license/provenance and privacy review.

## Implementation plan
Frozen requirements/contracts, acceptance and edge cases, dependency DAG and file ownership. Built-in prerequisites are explicit; external dependency resolution is unsupported in v1. No implied registry/global service activation.

## Implementation and tests
Actual feature/resources, source revision and exact tests/results. NOT_RUN remains visible. Scaffolding/build/byte hashes do not establish feature quality. Record decisions before dependent changes in target .palarran.

## Release review
Reviewed immutable archive SHA256, intended registry/owner/visibility, exact request ID, authorized publication scope, settings/permission impact and recovery. No raw sessions, tokens, private state or automatic hooks. Submission and acceptance remain separate.
