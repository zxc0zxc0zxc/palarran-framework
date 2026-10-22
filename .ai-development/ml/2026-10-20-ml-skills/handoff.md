# ML skills handoff

## Результат

Применено решение [ml/2026-10-20-ml-skills/0001](decisions/0001-scope.md). Сначала созданы docs/ml, затем семь skills и adapters. [Карта документации](../../../docs/ml/README.md) связывает experiment planning, hypotheses, model/method, data, Modal cost, train/metrics и benchmark. [Реестр источников](../../../docs/ml/sources.md): 29 первичных публикаций/docs, retrieval 2026-10-20. Karpathy/исследовательские кейсы отделены от наших рекомендаций и vendor claims.

Все skills требуют target decision memory, immutable source/model/data/config/checkpoint refs, progress/remaining gates. Paid compute не разрешается планом/калькулятором, failed/restarted/unknown attempts не обнуляют расход. Existing product-factory runtime/private product artifacts не менялись.

## Проверка

- PASS: `python3 scripts/validate_repo.py` — 25 skills/adapters, mandatory documentation/links/decision memory.
- PASS: `python3 -m unittest discover -s tests -v` — 234 tests, 88.837s; в том числе 8 новых cost tests и ML package portability/containment/run of shipped helper.
- PASS: skill-creator `quick_validate.py` для всех семи ML skills. В системном/bundled Python отсутствовал PyYAML; использован временный isolated validation venv с PyYAML, repo dependencies не изменены.
- PASS: Python compilation, `git diff --check`; offline sample CLI сохраняет `within_budget=null` при неизвестных extras.
- NOT RUN: live Modal SDK/API, GPU pilot/training, actual benchmark, operational budget enforcement; не входят в создание suite.

## Следующая задача

Применить `/ml:plan` к конкретной цели/README в target repository, затем выбрать данные/модель и пересчитать current tariff. До training нужен конкретный experiment/config/compute/budget scope; не запускать paid jobs для проверки этой поставки. [План и прогресс](plan.md) содержит implemented v001 и оставшиеся live checks.
