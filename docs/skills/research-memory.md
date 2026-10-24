# R&D-результаты в общей памяти

Профиль обязателен, когда задача дала результат исследования, эксперимента, benchmark, абляции, product discovery или UX/infra измерения. Применяется через [общий цикл](global-memory.md) ко всем скиллам; [локальные решения](decision-memory.md) и полные domain reports остаются источником контекста. Результат исследования часто переносимее конкретного patch: при выборе0–3уроков сначала рассмотреть релевантные R&D findings. Это приоритет отбора агентом, не реализованный новый ranking алгоритм Neo4j. Общий лимит, owner policy и бюджет не увеличиваются.

## Основание

Проверены2026-10-24: [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist), rolling guide — reproducibility, experimental settings, limitations, variability/error bars; [Google Model Cards2019](https://research.google/pubs/model-cards-for-model-reporting/) — оценка в разных условиях и intended use. Здесь используем их как reporting principles, а не доказательство качества нашей памяти. Наши0–3лимит, совместимое field mapping и отбор negative findings — проектные решения. Для ML/data/product/science применяются также собственные mandatory guides; запись карточки не запускает новый эксперимент.

## Какие результаты сохранять

- `empirical`: проведённый эксперимент, benchmark/абляция, измерение latency/cost/качества, подтверждённый провал. Фиксировать наблюдение, а причинное объяснение обозначать hypothesis, если причинность не проверялась.
- `source_review`: проверенный обзор первичных статей/кейсов. Сохранять авторство, URL/DOI, дату/версию и условия claims; вывод источника остаётся `source_claim`, не `observed` и не независимой репликацией.
- `discovery`: evidence-backed исследование спроса/конкурентов/UX с датой, сегментом, географией и ограничениями выборки. Исследование рынка само по себе не market validation; заявленная выручка/оценка провайдера не наблюдаемая выручка.

Отрицательные результаты, отсутствие измеримого эффекта и остановки по бюджету полезны. Нельзя выбирать только удачные запуски или выдавать остановленный/искажённый benchmark за доказательство бесполезности метода. Outcome: `supported`, `refuted`, `inconclusive` или `not_tested`. `Refuted` — только в заданных условиях; null result без достаточной чувствительности чаще inconclusive. Source review без собственного теста использует not_tested для локальной гипотезы и отдельно сообщает outcome, заявленный авторами.

## Минимальное содержание

Карточка должна позволять следующему агенту решить, применим ли результат, без исходной беседы:

| Раздел | Что записать |
| --- | --- |
| Вопрос | Гипотеза/JTBD, заранее заданный критерий успеха; post-hoc критерий явно отметить |
| Subject | Версии модели/метода/конфига/кода; безопасные hashes/IDs данных и split/protocol, не содержимое датасета |
| Условия | Размер/домены/языки данных, аппаратное окружение/нагрузка, существенные параметры, дата/рынок; N/A с причиной |
| Метод | Baseline и кандидат, измеряемое изменение, protocol, seeds/repeats/объём выборки либо ограничения; observational comparison не controlled experiment |
| Наблюдение | Метрики baseline/candidate с единицами, направлением улучшения и denominators; delta если корректна; uncertainty/доверительный интервал либо явно unknown |
| Ресурсы | Наблюдаемое время/токены/GPU и стоимость с основанием estimate/provider_usage/invoice, валютой/датой; неизвестное не считать нулём |
| Вывод | Outcome, уровень evidence observed/source_claim/hypothesis, что поддержано и что не установлено |
| Повторное применение | applies_when, limitations, возможные confounders, условия пересмотра/следующая проверка |
| Provenance | Source repo alias+commit+ADR, E-IDs/URL источников и hashes проверенных отчётов; ссылки без credentials |

Для не-ML задачи не придумывать model/seed/GPU: сохранить нужные контекстные измерения и объяснить неприменимость. Одна попытка не независимая репликация; повторная запись того же результата из другого проекта тоже не репликация. Точные subjects/условия/числа нельзя потерять ради краткости.

## Совместимость с memory-v001

Профиль не добавляет API fields/types. Имеющийся service принимает case type только pattern/incident/decision/solution/anti_pattern. Для нейтрального R&D finding использовать `decision`; `anti_pattern` подходит лишь обоснованному отрицательному инженерному уроку, а не любому неудачному обучению. Не отправлять `type:research_result` или поля `metrics`/`experiment` верхнего уровня: развёрнутый service их отвергает.

Mapping в существующие fields:

- `title`: короткий вопрос/результат. `tags`: research-result, область, kind и outcome плюс значимые retrieval keywords; оставить место для служебного fingerprint.
- `problem`: гипотеза + точный subject/data/protocol identity + существенные условия. Это помогает retrieval/dedup отличить исследования.
- `root_cause`: наблюдаемый эффект/неопределённость и статус объяснения. Если причина неизвестна, написать unknown; для обзора — attribution source_claim.
- `solution`: компактные подписанные секции method/baseline/metrics/resources/outcome/conclusion. Вывод может быть «не применять в этих условиях», «требуется следующая проверка» или «гипотеза не проверялась», а не обязательно исправление кода.
- `applies_when` и `limitations`: границы переноса, confounders/unknowns; не прятать критические условия только в source evidence.
- `source`: стандартные repo/commit/adr текущего локального журнала, даже если это обзор статей. `evidence`: безопасные первичные ссылки/E-IDs/report hashes, attribution originals отдельно.

Пример содержимого совместимой карточки (синтетический, не реальный опыт):

```text
type: decision
tags: research-result, ml, empirical, inconclusive, cache
problem: H: cache improves p95; subject fixture-v1; data fixture-a;
         protocol fixed-1000-requests; single-worker; workload read-only.
root_cause: Observed sample difference; causal effect and variability unknown.
solution: Method: baseline cache-off vs candidate cache-on, one run each.
          Metrics: p95 100ms vs 90ms on 1000requests each; lower is better.
          Uncertainty: unknown; single run. Outcome: inconclusive.
          Resources: elapsed/cost unknown. Conclusion: insufficient evidence
          to promise improvement; repeat under the same frozen workload.
applies_when: same workload and version; exploratory comparison only
limitations: synthetic fixture; no production SLA; no independent replication
```

JSON формируется по существующему case/lesson contract; это пример значений, не payload для загрузки. Полная карточка <=8KiB с verification refs; automatic finish добавляет proof/fingerprint и может отвергнуть слишком большой input. Не обрезать тихо метрики/условия/limitations: сузить один finding или оставить local draft. `finish` передаёт только case, не artifacts. Для разрешённого manual propose допускается отдельный обезличенный `verification` artifact по существующему контракту; нет нового типа research-report. Полные данные/веса/raw generations/логи/персональные ответы не загружать. Hash — связь с evidence, не доступ к приватному оригиналу и не доказательство истины.

## Verification, запись и поиск

До finish агент проверяет источник/идентичность subject, измерения/denominators, вывод и ограничения, privacy/права и смысловые duplicates. Existing checks PASS означают, что результат корректно зафиксирован и проверен; они не превращают refuted/inconclusive outcome в поддержанную гипотезу. В `verification.checks` включать все применимые проверки с реальными report hashes. Провал/отсутствие обязательной проверки => local draft/DEFERRED, не фиктивный PASS. Проверенная остановка может обосновывать только факт/условия остановки, не неполученные метрики качества.

Automatic finish сохраняет прежние commit/clean-source/ADR/evidence/privacy/dedup gates, propose→read-back→promotion→read-back и reconciliation при unknown outcome. Уже существующие reports не публиковать автоматически задним числом. Изменившиеся model/data/protocol/conditions/outcome/числа отражать в fingerprinted problem/root_cause/solution: source/evidence/tags сами по себе не меняют semantic fingerprint. Повтор того же finding — feedback/reuse; противоречащие результаты не затирать и не склеивать. Связи CONTRADICTS/VALIDATED_BY/SUPERSEDES доступны только reviewer; без полномочий сохранить refs и предложить связь, не расширять MCP inventory.

Перед следующей R&D-задачей искать не только названия технологий, но и гипотезу/метод, домен/язык и workload, обязательно учитывать отрицательные findings и ограничения. Сначала bounded3cards, затем нужные originals; FTS не гарантирует semantic/cross-language recall. Проверять версии и применимость, не переносить чужой эффект/числа на новый dataset или рынок без проверки. Existing published bundles получают профиль после обычного safe update; это instruction-level workflow, не новый host hook или отдельный фоновой extractor.
