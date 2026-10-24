# Documentation package design

Design-stage commands: `/palarran:doc:architecture`, `/palarran:doc:feature` and `/palarran:doc:api`. Read target sources, applicable AGENTS, accepted decisions, feature code and existing docs conventions before writing. Update existing canonical documents rather than creating competing copies. Use the selected documentation locale; canonical framework guides remain English.

Write plain concrete prose. Explain an unfamiliar term once when it helps the reader; avoid inflated terminology, repeated summaries and speculative guarantees. Distinguish current behavior, proposed changes, observed checks and unknowns. Every architecture/feature/API document includes a small useful Mermaid diagram with real names and explicit boundaries. Diagram presence is not rendering verification.

Read [architecture](architecture.md), [feature](feature.md), [API](api.md) and [storage/retrieval](memory.md). This package design does not authorize changes to application behavior, cloud configuration or deployment.
