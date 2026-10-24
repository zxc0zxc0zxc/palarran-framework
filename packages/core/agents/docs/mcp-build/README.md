# /palarran:mcp:build — tools agents can use effectively

First read [sources](sources.md), [tool design](tool-design.md), [context](context-efficiency.md), [protocol/security](protocol-security.md), [evals](evaluation.md), [workflow](workflow.md) and [decision memory](../decision-memory.md). Input: business task, target README/AGENTS/accepted ADRs, actual API/data rights and existing stack. Output: narrow tool contracts + implementation + independent scenario evidence, not universal-access promises.

```mermaid
flowchart LR
  T[User task + scope + current project] --> C[Minimal contracts + frozen cases]
  C --> S[SDK / transport / permissions choice]
  S --> B[Implementation + bounded outputs]
  B --> P[Protocol + business / adversarial checks]
  P --> R[Measured results + remaining NOT_RUN]
  R --> M[ADR / handoff / regression]
```

Runtime-v001 in palarran: standalone scaffold/validate/smoke and a dependency-free read-only catalog stdio server, pinned MCP2025-11-25 profile. This first concrete MCP server implementation is not an HTTP/auth/SDK framework. Build other project tools with the chosen stack/official SDK; generated examples do not automatically become production integrations. No auto activation/install/deploy/paid API calls. --plan permits planning artifacts only.
