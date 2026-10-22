# Offline verification

Наследует root. Suite: python3 -m unittest discover -s tests -v. Structural checks: python3 scripts/validate_repo.py; runtime lab: python3 scripts/factory_acceptance.py.

- Все provider-facing проверки используют fake transports/SDK/CLI; никаких auth, install, GPU, облачных API или paid launches. Optional tools не устанавливаются автоматически из tests.
- Проверять инварианты: approval/lineage, oversized/malformed receipts, unknown outcome, revoked lease, stale artifacts, budget overshoot, cancellation terminal proof, secret/path/output boundaries. Happy-path exit сам по себе недостаточен.
- Изолировать temp repositories/resources; не менять pinned source docs/code во время ML/product chain tests: это обязано вызвать source drift, а не быть скрыто.
- Graph tests проверяют источник dirty/untracked/delete drift и исключения. Fake extraction не доказывает качество реального графа; real local Graphify smoke отмечать отдельно.
- Не ослаблять independent verifiers ради fixture. В handoff сохранять PASS/FAIL/NOT RUN и границы lab vs operational evidence.
