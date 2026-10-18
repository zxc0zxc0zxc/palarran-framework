# Rust

Определить Cargo workspace/members, `rust-toolchain.toml`, MSRV, `Cargo.lock`, feature sets, binary/library, target triples, linker/native dependencies и integration services. Для deployable app lockfile обязателен; library compatibility может требовать дополнительного разрешения зависимостей отдельно от reproducible app release.

## DAG

| Ветка | Содержание | Ограничение |
|---|---|---|
| Format | `cargo fmt --all -- --check` | Pinned rustfmt/component |
| Analysis | `cargo clippy --workspace --all-targets --locked -- -D warnings` как начальная форма | Реальные features/targets выбрать; all-targets не равно все target triples |
| Tests | `cargo test --workspace --locked` либо nextest + отдельный doctest contract | Scope включает применимые feature combinations и integration tests |
| Dependencies | Policy-driven audit/advisories/licenses с pinned tools | Не выдавать отсутствие advisories за доказательство корректности |
| Release | `cargo build --release --locked` для точного bin/target/features | Packaged binary проверяется отдельно от debug tests |
| Candidate | OCI/binary smoke на target arch/libc | Не подтверждается одним cross-compile |

Команды — адаптируемая форма, не готовый pipeline для любого workspace. `--all-features` применять только если features совместимы; взаимоисключающие backend/TLS features требуют явной matrix. [Cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html) и [build](https://doc.rust-lang.org/cargo/commands/cargo-build.html) — основание для flags/scope. `--locked` запрещает незапланированное изменение lock, `--offline` имеет другую семантику и требует доступных зависимостей.

## Главные возможности ускорения

Cache Cargo registry/git downloads отдельно от `target`/compiler results. Ключи: rustc/toolchain components, target triple, profile, features, Cargo.lock/manifests, RUSTFLAGS, linker/native libraries и trust scope. Разные runner paths могут ухудшать hits. Не сохранять registry tokens/credentials и не доверять untrusted binary build cache в release.

[Mozilla sccache](https://github.com/mozilla/sccache) может переиспользовать компиляцию через `RUSTC_WRAPPER`, но не ускоряет всё: linker jobs и incremental compilation имеют ограничения. Для shared CI sccache рассмотреть `CARGO_INCREMENTAL=0` после сравнения warm/cold measurements; не обещать выигрыш без статистики. В одном pipeline «кешировать огромный target целиком» может стоить больше network time, чем компиляция нужного набора.

[cargo-nextest](https://nexte.st/docs/running/) — опция для параллельного исполнения/разделения tests. Не предполагать, что переход с `cargo test` автоматически покрывает всё: inventory unit/integration/doctest/bench scope и capabilities pinned версии сверяются. Если doctests не выполняются выбранным nextest flow, добавить `cargo test --doc --workspace --locked` с согласованными features. Переход считается завершённым только после сравнения списков и результатов test suites.

Compile и test parallelism ограничиваются CPU/RAM: cargo `-j`, test threads/nextest workers и CI shard count перемножаются. На слабом runner лишние workers дают OOM и queue delays. Shard после общего compile либо отдельные runners с корректным compiler cache выбирать по measured artifact-transfer cost.

## Релиз и supply chain

Versioned toolchain/MSRV policy; production release features и target записаны в manifest. Build scripts/proc macros исполняют код: они не получают prod credentials. При vendoring/offline/hermetic goals контролировать все native tools/network inputs отдельно, Cargo.lock сам по себе не делает сборку герметичной.

Debug test build не равен optimized release: overflow/panic/linker/runtime flags могут отличаться. Проверить startup и critical behavior actual release binary. ThinLTO/full LTO/codegen-units подбирать по runtime/build tradeoff; выключение оптимизаций ради быстрого CI не должно незаметно менять production contract. Без обоснования не собирать полный release profile заново в каждом test shard.

Runtime image минимален, но содержит нужные dynamic libraries, CA certs и user configuration. musl/glibc и static/dynamic linking выбираются по dependencies, не универсальному правилу. Multiarch smoke и evidence для фактических platforms обязательны. Deploy — [контроллер/API](../architecture.md), old/new protocol/schema compatibility, no SSH/remote cargo install.

## Приёмка

Cargo.lock drift fail; cold/warm cache корректны; Clippy/test/doctest scope доказан; supported features/MSRV проверены по policy; release binary работает с target loader/libc/arch; signed eligible digest соответствует наблюдаемому rollout; build/test stderr и crash diagnostics не содержат secrets. В handoff — реальные timings и cache statistics, а не обещание «Rust будет быстрым» только от установки sccache. Основание общих safety/performance решений — [Google/Meta/Microsoft](../evidence.md); конкретные Rust tooling choices наши.
