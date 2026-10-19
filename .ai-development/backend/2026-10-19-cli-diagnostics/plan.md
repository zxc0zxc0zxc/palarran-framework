# CLI diagnostics v001

- [x] Docs и accepted rationale: bounded enum-only diagnosis, no billing inference.
- [x] Реализация: stream diagnostics и fenced pre-pause outcome persistence.
- [x] Проверки: meaningful failures/secrets/fencing, offline suite, factory acceptance.
- [x] Диагностика: устранена потеря process metadata; current compatibility проверена completed canary. Историческая underlying cause неизвестна из-за утраченного output, не выдумывается. Дополнительный canary budget/recovery записан в ADR0003.
- [ ] Recovery: сохранить old unknown; новый pipeline только после safe canary/обоснованного recovery; actual status/usage/handoff.

DoD: no raw payload leaks, paused attempts retain process metadata, no accounting weakening, actual root-cause evidence distinguished from inference. Pipeline success claimed only after independent final verification; otherwise concrete blocker and retained result.

Implemented authoring v001: observable step enums + safe public decision summary renderer/protocol, fenced pre-pause and terminal-budget outcome retention.212tests PASS; actual current CLI canary VERIFIED. Full product recovery pending.
