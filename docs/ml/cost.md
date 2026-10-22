# Оценка стоимости и общий бюджет

Оценка предшествует запуску и не запускает GPU для собственного подтверждения. Public [Modal pricing](https://modal.com/pricing) — vendor tariff, не connected account и не invoice. В report обязательно `as_of`, USD/единицы, выбранный Modal product (Functions vs Sandboxes), regional/contract assumptions, hardware/count, physical CPU cores и RAM GiB, длительность всех phases/attempts. Public rates перепроверяются перед конкретным paid approval; в offline `--plan` используй датированный snapshot и явно отметь возможную устарелость.

## Считать весь experiment

Для одного сценария compute:

`sum_attempts(seconds × (GPU_count × GPU_USD_per_second + billed_physical_CPU × CPU_rate + billed_RAM_GiB × RAM_rate))`.

При разных timings/resources phases считаются отдельными строками. Время — billed container duration, включая relevant load/eval/checkpoint/idle intervals; training step time сам по себе меньше end-to-end. CPU/RAM у Functions могут биллиться по большему из requested и actual; ephemeral disk может повышать RAM billing basis. Это [правила Modal resources](https://modal.com/docs/guide/resources), поэтому вводи billable resource scenario, а не только requests.

Сверху: preprocessing/build, dataset/model download, baseline, pilot, failed/OOM attempts, resume/replayed work, ablations/seeds, validation/final benchmark/judges, checkpoint/export/storage/egress, внешний annotation/synthetic API, subscription/taxes где применимо. Unknown extra остаётся unknown; credit entitlement не считать до подтверждения доступного остатка. Cash charge, credit consumption и economic cost раздельно. Запас для unknowns не превращает unknown в известный ноль.

## Low/base/high

Время оценивай из representative measured throughput, либо пометь borrowed/assumed. Для LLM: effective processed tokens / observed aggregate useful tokens per second, включая epochs/padding/packing/accumulation и eval overhead без двойного подсчёта. Для CV — samples/second при той же resolution/augmentation. Multi-GPU efficiency не линейна; учесть communication/dataloader. Warmup, caching и cold path измерять отдельно.

Low/base/high — сценарии, не confidence interval и не статистический гарантированный upper bound. Если high/unknown не помещаются в ceiling, уменьшить scope/модель/число trials или запросить недостающие условия; **не повышать лимит**. Для разрешения запуска нужен обоснованный reserve и bounded control plan, даже если ожидаемая цена очень мала.

## Offline helper

`python3 scripts/ml_cost.py templates/ml/cost.example.json` проверяет явные rates/durations/units/unknown extras, считает Decimal compute low/base/high и reserve с contingency. Нет сетевых вызовов, SDK, live price lookup, списания и запуска jobs. Все numbers example — условные; они не rate snapshot. Helper не поддерживает billing reconciliation и не является launch gate. При реальных phases вызови его для каждой строки и сложи результаты без повторного начисления общих fixed extras.

Report имеет `known_total`, `unknown_extras`, `reserve`, `within_budget` (`null`, если total неполный). Даже известный итог — scenario, не spending guarantee. Не подставлять 0 за отсутствие цены. Отрицательные значения, NaN/Infinity, bool вместо чисел, неполные scenarios, неодинаковые единицы — ошибка входа.

## Контроль после запуска

До dispatch резервируется весь допустимый attempt envelope и доля final eval. Новая работа возможна, если confirmed spend + unresolved reserves + proposed reserve не превышают общий ceiling. В incremental ledger различай observed wall-time estimate, provider usage и invoice; поздний billing может менять оценку. Отсутствие receipt блокирует освобождение reserve. Учти provider automatic preemption/restart даже при application retries=0.

Нужны limits на total wall clock, attempts/restarts, steps/tokens, workers, GPU class/count, checkpoint/storage, bounded telemetry и abort controller. Stop threshold оставляет headroom на обнаружение/остановку/checkpoint и delayed accounting. Vendor [budgets](https://modal.com/docs/guide/budgets) — дополнительный workspace/environment механизм, его availability/scope/права проверяются отдельно; не менять общие limits аккаунта без разрешения. Local polling/таймер не гарантирует invoice hard cap.
