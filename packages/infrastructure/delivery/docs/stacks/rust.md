# Rust

Identify Cargo workspace/members, `rust-toolchain.toml`, MSRV, `Cargo.lock`, feature sets, binary/library, target triples, linker/native dependencies and integration services. Deployable applications require lockfiles; library compatibility may need additional dependency resolution separately from reproducible application releases.

## DAG

| Branch | Contents | Limitation |
|---|---|---|
| Format | `cargo fmt --all -- --check` | Pinned rustfmt/component |
| Analysis | `cargo clippy --workspace --all-targets --locked -- -D warnings` as a starting form | Choose actual features/targets; all-targets is not all target triples |
| Tests | `cargo test --workspace --locked` or nextest + separate doctest contract | Scope includes applicable feature combinations/integration tests |
| Dependencies | Policy-driven audit/advisories/licenses with pinned tools | Absence of advisories does not prove correctness |
| Release | `cargo build --release --locked` for exact bin/target/features | Packaged binary checked separately from debug tests |
| Candidate | OCI/binary smoke on target architecture/libc | Cross-compilation alone is insufficient |

Commands are adaptable forms, not ready pipelines for every workspace. Use `--all-features` only for compatible features; mutually exclusive backend/TLS features require explicit matrices. [Cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html) and [build](https://doc.rust-lang.org/cargo/commands/cargo-build.html) define flags/scope. `--locked` prevents unplanned lock changes; `--offline` has different semantics and requires available dependencies.

## Main optimization opportunities

Cache Cargo registry/git downloads separately from `target`/compiler results. Keys include rustc/toolchain components, target triple, profile, features, Cargo.lock/manifests, RUSTFLAGS, linker/native libraries and trust scope. Different runner paths may reduce hits. Do not retain registry tokens/credentials or trust untrusted binary-build caches for releases.

[Mozilla sccache](https://github.com/mozilla/sccache) may reuse compilation through `RUSTC_WRAPPER` but does not speed everything: linker jobs/incremental compilation have limitations. For shared CI sccache, consider `CARGO_INCREMENTAL=0` after comparing warm/cold measurements; do not promise gains without statistics. Caching an enormous entire target directory may cost more network time than compiling the needed set.

[cargo-nextest](https://nexte.st/docs/running/) supports parallel test execution/splitting. Do not assume migration from `cargo test` automatically covers everything: reconcile unit/integration/doctest/bench inventory with pinned-version capabilities. If selected nextest flows omit doctests, add `cargo test --doc --workspace --locked` with agreed features. Migration completes only after comparing test inventories/results.

CPU/RAM bound compile/test parallelism: cargo `-j`, test threads/nextest workers and CI shard count multiply. Excess workers on weak runners cause OOM/queue delays. Choose shards after shared compilation or separate runners with correct compiler cache based on measured artifact-transfer cost.

## Release and supply chain

Version toolchain/MSRV policy; record production release features/target in manifests. Build scripts/proc macros execute code and receive no production credentials. For vendoring/offline/hermetic goals, control all native tools/network inputs separately; Cargo.lock alone does not make builds hermetic.

Debug test builds differ from optimized releases: overflow/panic/linker/runtime flags may differ. Check startup/critical behavior of actual release binaries. Choose ThinLTO/full LTO/codegen-units by runtime/build tradeoffs; disabling optimizations for fast CI must not silently change production contracts. Do not rebuild full release profiles in every test shard without justification.

Minimal runtime images still contain necessary dynamic libraries, CA certificates and user configuration. Choose musl/glibc/static/dynamic linking by dependencies, not universal rules. Multiarch smoke/evidence for actual platforms is mandatory. Deployment: [controller/API](../architecture.md), old/new protocol/schema compatibility, no SSH/remote cargo install.

## Acceptance

Cargo.lock drift fails; cold/warm caches are correct; Clippy/test/doctest scope proven; supported features/MSRV checked under policy; release binary runs with target loader/libc/architecture; signed eligible digest matches observed rollout; build/test stderr/crash diagnostics contain no secrets. Handoff includes actual timings/cache statistics, not “Rust will be fast” merely because sccache is installed. [Google/Meta/Microsoft](../evidence.md) inform shared safety/performance decisions; concrete Rust tooling choices are ours.
