# Handoff: CI/CD skills и общая память решений

## Выполнено и почему

- Созданы `ci-cd-github` и `ci-cd-gitlab`, project discovery links и slash adapters. Mandatory docs/provider/all detected stacks, no SSH, fast CI с тестами, eligible artifact promotion и machine config memory — [0002](decisions/0002-ci-cd-workflow.md).
- Все пять скиллов используют один decision-memory contract. Target `.ai-development/INDEX.md` и relevant accepted records читаются до выбора, любой новый принятый выбор объясняется до изменения, сохраняются история и handoff — [0001](decisions/0001-decision-memory.md).
- `.delivery/` — действующий environment config, `.ai-development/` — причины; `.delivery/decisions/` и планы не становятся дублирующими ADR-журналами. Scratch ignored; durable sanitized records доступны следующей задаче.
- Добавлен allowlisted local packager двух независимых namespace с полными внутренними docs/template links, без external symlinks, project history и перезаписи existing output — [0003](decisions/0003-plugin-packaging.md).
- Repository validator проверяет регистрацию всех навыков и обязательную memory ссылку, adapters, namespace, local links и explanation sections/index для accepted records — [0004](decisions/0004-validation.md).

## Evidence

| Проверка | Результат | Предел |
|---|---|---|
| `python3 scripts/validate_repo.py` | PASS | Markdown/contracts всех пяти skills, adapters, namespace и project memory; не proof поведения LLM |
| `python3 -m unittest discover -s tests -v` | PASS, 11 tests | Inventory safety + package portability/containment/refusal overwrite; нет SSH/network deploy |
| Bundled `quick_validate.py` для пяти скиллов | PASS | Frontmatter/name/structure; использован отдельный временный Python env с PyYAML |
| `claude plugin validate ... --strict` для обоих materialized plugins | PASS | Реальный plugin manifest/path validation, не вызов агентом application integration |
| Python compile + `git diff --check` | PASS | Syntax/whitespace |
| GitHub repository CI | PASS | [Run 39140562657](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39140562657), implementation commit `c915764`; offline + Terraform jobs прошли |
| Реальный GitHub/GitLab application pipeline | NOT RUN | Пользователь попросил создать скиллы; application repo/targets не выбраны |
| Live performance/identity/env gates/secret-leak/rollout | NOT RUN | Нужны конкретный sandbox проект/backend и соответствующий разрешённый scope |

Локальные пакеты находятся в ignored `artifacts/plugins/ci-cd` и `artifacts/plugins/infra-plan`; переносимая сборка описана в root README. Изменения sources требуют нового output path, чтобы не затирать существующие артефакты.

## Следующая задача

Прочитать [индекс](../../INDEX.md), затем релевантные ADR. Применить `/ci-cd:github` либо `/ci-cd:gitlab` к выбранному application project; его `.ai-development/` и `.delivery/` находятся в **том** проекте. Сначала прочитать его existing decisions/config и проверить assumptions. CI timings/rollout readiness не выводить из успешного authoring validation. Ни старый ADR, ни наличие credentials не разрешают новый destructive scope.
