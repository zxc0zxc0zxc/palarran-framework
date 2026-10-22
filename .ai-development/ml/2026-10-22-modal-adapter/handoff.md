# Modal adapter — handoff

Revision modal-v001 реализована. Документация создана до кода; [решение](decisions/0001-adapter.md), [контекст](context.md), [план](plan.md). Существующие ML suite/pipeline изменения сохранены. Commit/push и product runs не выполнялись.

## Реализация

- `backend: modal` в существующем ML compiler; strict pinned policy, исходный общий ceiling и exact-prefix approval сохранены. Create/approve не вызывают provider.
- Lazy SDK adapter: existing App.lookup/Image.from_id/Volume, отдельная named Sandbox на attempt, CPU/RAM limits, GPU, block_network, hard lifetime. Нет installs/image builds/deploy/create_if_missing.
- Intent до create, durable name/object ID/terminal proof, no automatic replay. Lost create response reconciles через lookup; NotFound остаётся unknown.
- Numeric metrics со strict sequence/finite validation, bounded private history; estimate по durable wall time, status по этапам. Unknown outcome удерживает reserve и блокирует downstream.
- Успешное remote выполнение проходит независимые checkpoint/protocol/final-fingerprint gates. Пока billing неизвестен, awaiting_billing удерживает полный reserve и не притворяется actual invoice. `ml-reconcile` требует remote terminal proof и отдельно импортирует проверенную оператором стоимость. Late overspend сохраняется и останавливает run.
- Budget/deadline/lost lease/transport failure вызывают terminate + bounded poll; acknowledgement не terminal proof. Cancel/recover доступны без живого worker; только lookup/stop, без нового launch. Local cancelled и remote terminal proof различаются в status.
- Инертные policy и remote regression examples. Remote пример требует заранее созданный Volume v2, использует atomic files + sync mountpoint; credentials внутрь не передаются.

## Проверка

PASS full offline suite: **259 tests**, 208.928s, включая 9 новых adapter tests. После уточнения Volume v2 sync remote example: **10 focused Modal tests PASS**, 45.863s (добавлена отдельная CPU-only проверка remote-примера без Modal SDK/auth; остальные 9 повторены). Полный suite включал существующие local ML/product/runtime/packaging tests без регрессий.

PASS `scripts/validate_repo.py`, Python compile, diff whitespace. PASS `scripts/factory_acceptance.py`: 100 samples, control-plane p95 **1.314 ms**, lab threshold 100 ms, smoke 0.380s. Финальный структурный validator повторён после записи handoff.

NOT RUN: live Modal API/SDK integration, GPU, paid training, account/auth, real cancellation/billing, operational SLA и прикладное качество модели. Fake async SDK проверяет публичные signatures/args/timeout; это не live compatibility claim. Платных запусков для тестов не было.

## Границы эксплуатации

SDK/version, image, существующий App/Volume v2, права на model/data и all-in rate/fixed storage/transfer reserve выбираются оператором для конкретного target. Unknown rate не считать нулём. SDK credentials только в trusted coordinator environment. Не обещаем hard invoice cap при provider failures, неверных ценах или storage retention после завершения.

Автоматический импорт workspace billing пока отсутствует: delayed/object attribution и storage требуют отдельной сверки. Provider-reported расход до неё null, invoice null. Recovery не делает task verified и не возобновляет неизвестный launch; последующая работа требует прежних independent gates и operator reconciliation. Original product budget не менялся.
