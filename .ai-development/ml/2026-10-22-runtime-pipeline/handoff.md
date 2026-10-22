# ML runtime pipeline — handoff

Реализована revision **ml-v001**, [план/прогресс](plan.md), accepted [0001](decisions/0001-pipeline.md). Предыдущие ML suite изменения сохранены; original product run не продолжался и его бюджет не менялся.

## Что работает

- [Documentation-first маршрут](../../../docs/ml/pipeline.md) и [typed contract](../../../docs/ml/pipeline-contract.md).
- Семь ML skills → private approval exact prefix → supervised local fit → independent evaluation → final stable receipt rerun/fingerprint.
- Cumulative E/H/ADR IDs, явные unknown dispositions, context/source/policy/model/data/tokenizer/config/protocol hashes; verified prefix нельзя незаметно переписать даже с пересчётом публичных hashes.
- Общий USD ceiling: AI usage envelope и resource reserves; отдельные token/stage caps, actual CLI receipts, supervisor estimate и adapter-reported resource cost. Invoice unknown остаётся unknown. Failed/unknown attempts не обнуляют бюджет; reserve/approval/lease state durable в SQLite.
- Unknown outcome блокирует replay и обычный resolve, нужен отдельный ml-reconcile после остановки; critical unknown блокирует compute. Deadline/наблюдаемый budget stop останавливают local process group и следующие задачи.
- Frozen protocol до training; независимый evaluation пересчитывает accept/reject/inconclusive, проверяет actual checkpoint digest; подмена после PASS даёт stale. Large artifacts вне Git; прошлые retry outputs архивируются.
- CLI: ml-create, общие work/status/events/cancel, ml-approve, ml-reconcile. Create ничего не исполняет; model/usage/execution policies явные, дефолтные цены моделей не подставляются. Skills/adapters/packaging и root docs обновлены. Private SQLite — authoritative progress, project progress/plan — derived snapshot.

## Проверка

PASS: `python3 -m unittest discover -s tests -v` — **250 tests**, 161.016s. В том числе actual fake-agent chain, настоящий маленький scalar regression fit с held-out evaluation, approval pause/continue без повторения upstream, forged acceptance, coordinated prefix rewrite, checkpoint drift, leases, telemetry errors, unknown receipts, critical unknowns, token/resource stops, silent-task deadline, oversized AI receipt и null policy. ML subset — 24 tests PASS.

PASS: `python3 scripts/factory_acceptance.py` — smoke/control-plane, 100 samples, p95 **0.867 ms**, threshold 100 ms; smoke 0.381s. Это laboratory control-plane check, не operational SLA.

PASS: repo validator (25 skills/adapters), Python compilation, portable ML package checks и diff whitespace check. Raw output/данные/секреты не сохранялись в Git.

## Границы и следующий шаг

Backend только trusted foreground local processes. Это не sandbox и не защита от злонамеренного кода с правами владельца state; executable allowlist не проверяет всю dependency closure. Нет встроенного Modal launch/status/cancel supervisor: remote backend admission отвергается. Оценивать Modal можно существующим ml-cost, но local kill не считается remote cancellation.

Live Codex/Claude, Modal/GPU billing, remote cancellation, production SLO и качество пользовательской модели — **NOT RUN**. Реальные paid/remote training jobs для проверки runtime не запускались. Следующая эксплуатационная задача: выбрать конкретный target и reviewed policies, выполнить preparation под его AI budget, затем отдельно разрешить подготовленный exact plan. Для Modal сначала нужен отдельный supervisor contract, а не shell-wrapper под видом local backend.
