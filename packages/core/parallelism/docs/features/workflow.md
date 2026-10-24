# Coordinated implementation workflow

## Establish the feature

Read each project's instructions, private decisions, stack, API and deployment contracts. Assign one stable feature ID and a coordinator. Verify each remote default branch and base commit using the existing feature lifecycle; a stale local default is insufficient. Record repository owners, permitted files and tools. No user-supplied repository URL becomes an authenticated room or execution permission automatically.

Write the passport under `.palarran/features/{feature_id}/` in the chosen coordinator project. Link local participant records to its identity, revision and authority; do not create independently mutable copies. Pin specification, plan, contracts, invariants, acceptance criteria and release plan. A contradictory or unanswered business rule blocks dependent work rather than becoming an agent's silent product decision.

For a referral feature, decide when referral binding becomes immutable, what qualifies for a reward, who confirms it, money units/precision, rule version, deduplication key, reversal and compensation. Name an owner, independent check and expected outcome for each rule.

## Freeze boundaries before parallel work

Every HTTP/RPC/event/data contract defines producer and all consumers, schema format/hash/version, semantics, required/absent/null, IDs and units, errors, authentication/authorization, timeouts/retries, idempotency, duplicate/out-of-order/late delivery, compatibility and retirement window. Use OpenAPI, Protobuf, JSON Schema or AsyncAPI already used by the project.

A change proposal includes the old/new diff, reason, consumers and release impact. Obtain affected boundary-owner approval against its exact hash, update the plan/contract revision and invalidate previous acceptance. An approval is an assertion through a trusted operator binding; an agent-written boolean or message ACK is not human attestation and never widens deployment permissions.

Build one cross-repository DAG with owned contracts, integration and migrations. Each task binds feature/run/task/attempt, plan/contract revisions, its repository/base, dependencies, owner/worktree/session, allowed files/tools/actions, expected output and time/token/cash limits. Namespace file claims by repository; serialize overlapping boundaries and shared resources. Register descendants in the same root run and immutable backend. Never start a budget per repository.

## Implement, integrate and accept

Dispatch only ready independent tasks. Keep model and developer credentials on approved worker machines. Native chat instructions do not establish enforced runtime interception. Use the existing local/Temporal dispatcher and authority transport; failure of the selected backend is visible and never triggers hidden local execution.

Integrate each repository through its existing queue, preserving stage commits and unrelated dirt. Link PR identities and commits in the feature; PR status is not acceptance. Freeze a complete composition, test suite/config/data hashes, images, migrations and feature flags. Run the independent acceptance protocol against those exact versions. If one component changes, create a new composition and invalidate affected evidence; unknown impact reruns all gates.

Keep the source plan's completed/remaining work, implemented revision, commits, blocked questions and actual checks synchronized from the authoritative report. Human and browser views must show the same version and budget. A worker exit or successful local test does not mean feature acceptance.

## Finish the authorized scope

A library/build scope can finish at `release_ready`. Production merge/deploy requires actual separate authorization and the frozen CI/CD/controller binding. Before any action compare the real environment with the reviewed predecessor. Unknown action outcome retains its intent and root reservation until explicit reconciliation; never retry blindly.

Store rationale and bounded evidence locally. Publish only separately verified, sanitized portable findings to long-term memory through its existing gates. Source, raw logs, sessions, credentials and customer data stay private.
