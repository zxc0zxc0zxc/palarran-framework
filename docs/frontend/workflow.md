# Workflow и память реализации

1. Определить target и scope запроса, прочитать общую память, relevant frontend/UX/UI records, repo instructions и actual code. Зафиксировать обе source revisions и [coverage](source-contract.md). Если неясны source/процесс — ранний конкретный вопрос, независимую работу продолжать. Не повторять выбор уже принятого UI направления.
2. Обследовать stack/runtime/lockfile/scripts/components/API/assets. Принятые решения объяснить **до** зависимого изменения в canonical `decisions/`: reuse, необходимые новые dependencies, component/data boundaries, responsive adaptation, asset choices, проверки/исключения. Не записывать каждую команду как ADR. Existing user authorization и repo workflow использовать без лишнего запроса разрешения.
3. Реализовать полный запрошенный scope в app code по [implementation](implementation.md) и [responsive](responsive.md): реальные routes/components/states/actions, tokens/assets и integration contracts. Недостающие обязательные изображения генерировать; mocks обозначать и изолировать. UX/UI changes только explicit proposals; implementation детали в рамках concepts решать самостоятельно с причинами.
4. Выполнить [quality](quality.md) checks и **обязательный [browser acceptance](browser-verification.md)** на фактическом приложении. Посмотреть renders, пройти interactions/состояния, narrow/tablet/desktop, console/network. Исправлять свои дефекты и повторять затронутые проверки. Без tools/данных — конкретный partial/NOT RUN, не false completion.
5. Сохранить evidence, mapping, decisions и handoff; обновить общий/frontend индексы с проверенным scope. При следующей задаче сначала читать этот контекст, source revisions и изменения, затем делать новую проверку вместо механического переноса старого PASS.

```text
.ai-development/
  INDEX.md
  frontend/
    INDEX.md
    <task>/
      context.md                  # target/source UX/UI revisions/constraints
      decisions/0001-<choice>.md   # canonical accepted explanations
      coverage.md                 # source IDs → app code → browser scenarios
      browser-review.md           # steps/environment/PASS/FAIL/NOT RUN
      evidence/                   # sanitized screenshots, safe summaries
      handoff.md
      scratch/                    # disposable
```

Application sources/tests/assets находятся в штатных app directories, ссылки на них — в mapping; не создавать второй frontend в журнале. Новая task/revision не стирает предыдущую evidence. UI/UX catalogs обновлять ссылкой на реализацию, не перезаписывать исходные concepts и их approval status.

[Handoff template](../../templates/frontend/handoff.md): что реализовано, почему (ADR IDs), как запустить/открыть, source→code mapping, выполненные checks, фактический browser/viewport, mock vs real API, screenshots, unresolved gaps и следующие шаги. Перед публикацией проверить отсутствие credentials/PII в evidence. Deploy не подразумевается, следовать ранее заданному scope и разрешениям.
