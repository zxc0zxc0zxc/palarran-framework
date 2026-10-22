---
id: ml/2026-10-23-training-debug-design/0001
status: accepted
date: 2026-10-23
scope: ml-training-observability
decision_basis: user-request
reuses: [ml/2026-10-22-runtime-pipeline/0001, ml/2026-10-22-modal-adapter/0001, ml/2026-10-23-pipeline-data-gate/0003]
---
# Task-aware debugging, поведение и terminal reports

## Контекст и основание

Пользователь требует сохранять диагностику train/validation, подходящие эвристики, генерации во времени и отчёт при завершении/остановке. Текущая bounded telemetry не реализует полный цикл. Запрос — проработать дизайн, не запускать обучение или изменять scheduler.

## Выбор и объяснение

1. Три независимых слоя: correctness/learning, task quality/guardrails и behavior probes. Общий task profile связывает metric basis, slices, heuristics и действия; PPL только для совместимой autoregressive NLL, не универсальная primary metric. Не выбирать эвристики постфактум ради красивой кривой.
2. Private append-only events/metric records/evaluation receipts + content-addressed snapshots/checkpoints. У каждого aggregate numerator/denominator, subjects и status; итоговые JSON/Markdown/plots — derived views. Существующий budget ledger остаётся единственным финансовым authority.
3. Fixed diagnostic development probes до/во время/после обучения, native template и pinned decoding; сохранить полные observable outputs с artifact digests. Held-out final test не используется для регулярного наблюдения. Перечень примеров и ошибок сохраняется целиком в пределах заранее выбранного bounded набора.
4. Heuristics registry: applicability, inputs/formula, calibrated window/threshold, observation state, action и evidence. Hard integrity/budget stops отдельно от статистических review signals. Нет universal чисел grad norm/PPL/repetition и автоматического LR/GPU изменения.
5. Durable start stub и rolling report; bounded terminal finalizer для каждого исхода плюс coordinator recovery без GPU. Report completeness отдельно от training outcome/benchmark verdict/provider terminal proof. Budget/abort сначала, попытки checkpoint/eval не продлевают опасный run.
6. Templates храним в docs/ml/debugging/examples, чтобы существующий portable ML docs packaging включал их без runtime/code изменений. Existing experiment template ссылается на новый контракт. Реализация — отдельный pending DAG с offline DoD.

## Альтернативы

Одна loss/PPL кривая скрывает задачи и деградацию ответов. Внешний tracker не решает идентичность/checkpoint/report recovery и требует отдельного scope. Samples по вдохновению создают cherry-picking. finally в training process не переживает SIGKILL, поэтому нужен durable coordinator fallback. Полные logits/gradients на каждом шаге неоправданно дороги и чувствительны.

## Источники и evidence

Датированный реестр docs/ml/debugging/sources.md: Karpathy Recipe, Google Rules of ML, HF PPL/generation, PyTorch norms/AMP, sklearn evaluation/calibration, Chen et al. functional code evaluation, Hamel error analysis, MLflow artifacts. Таблицы/threshold policies/cadence — design ai-tools, не измеренные результаты этих авторов.

## Последствия и пересмотр

Дополнительное eval/generation/storage время учитывается заранее в том же бюджете. Private samples требуют прав/retention. Semantic correctness не доказывается entropy/length или token-only heuristics. Controller/storage outage допускает partial report с last-observed state, последующее восстановление не replay. Пересмотр после первого offline implementation и измеренного diagnostic overhead.

## Применение и проверка

Planned: repo links/portable packaging/template consistency. Runtime rollout, GPU training, auto finalizer и scientific replication — NOT RUN/NOT IMPLEMENTED в этой задаче. Конкретный план: docs/ml/debugging/integration-plan.md.

### Уточнение переносимости до зависимого изменения

Проверка portable package обнаружила: docs packaging включает Markdown, не произвольные JSON из docs. Поэтому design JSON examples сохраняются в Markdown code blocks с явным NOT RUN; code/packager не меняем ради documentation-only задачи. Содержимое остаётся JSON template, production schemas pending. Первая packaging попытка FAIL на missing JSON ref; после исправления повторить.

### Недеструктивность probes

Fixed observations должны измерять обучение, а не менять его: отдельный RNG/generator где поддержан, восстановление train/eval и RNG состояния после probes, никаких optimizer/sampler updates. Иначе diagnostic cadence становится скрытым изменением эксперимента. Проверить это в DBG-04 offline DoD.

### Verification outcome

Documentation/portable packaging PASS; strict design JSON parsing PASS. Runtime implementation/paid training NOT RUN. Полный scope и remaining DBG tasks: [handoff](../handoff.md).
