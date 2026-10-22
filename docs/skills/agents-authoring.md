# Как писать AGENTS.md проекта и модулей

## Основание

Проверено 2026-10-22: [официальный OpenAI guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md) описывает root-to-CWD discovery, более близкие инструкции и стандартный combined limit 32 KiB. [OpenAI: scoped review rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex) рекомендует короткие конкретные инварианты по месту действия. Это поведение Codex; другие hosts проверять отдельно. Агент, запущенный в root, должен явно читать инструкции целевых каталогов: наличие вложенного файла не гарантирует автоматическую загрузку всех modules.

## Правила

1. Сначала исследовать реальный README, manifests, код, tests и существующие AGENTS/override files. Сохранить пользовательские правила. Не создавать инструкции на основе предполагаемого стека.
2. Root: цель/язык, общие инварианты, карта модулей с путями, входы в docs, память решений и главные checks. Module AGENTS: только локальные обязанности, контракты, edge cases, команды и критерии проверки. Не копировать root и соседние инструкции.
3. Рекомендуемый наш budget: root <=6 KiB, module <=4 KiB; это локальный convention, не limit платформы. Считать всю применимую chain, не только каждый файл. Override требует явного основания и review; не создавать override ради сокращения текста.
4. Правило содержит trigger, инвариант, безопасный путь и проверку. «Пиши хороший код» не помогает. Числа, paths и команды сверять по repository; неизвестное помечать unknown и ссылаться на owner вопроса.
5. История решений живёт в canonical ADR; AGENTS содержит ссылку и действующее ограничение, а не историю чата. Версии plans/implemented/verified/deployed не смешивать.
6. При разрешённых application changes создавать/обновлять AGENTS только в реально затронутых границах: например services/billing или apps/web, если они существуют. Не плодить AGENTS на каждый файл. В plan-only/read-only — только предложенный template/handoff; target инструкции не менять.
7. Graphify — optional navigation. После freshness check прочитать source и applicable instructions; отсутствующий/stale graph не отменяет проверки. Не класть graph dump, dependency lockfiles, raw logs или secrets в AGENTS.
8. При изменении boundary/contract/test command обновлять ближайший AGENTS и routing table. Shared code owners и worktree ownership задавать в SDD плане; AGENTS не должен сам dispatch агентов или разрешать внешние действия.

## Шаблоны и review

Шаблоны templates/agents/root.md и module.md включаются во все portable packages вместе с этим guide: root с purpose/boundaries/docs/memory/checks и module с scope/contracts/verification. Заполнить только verified facts; placeholders не выдавать за ready instructions.

Review проверяет: все paths существуют; команды уместны для scope и безопасны; нет повторов/конфликтов/секретов; mandatory docs и source behavior сохранены; инструкция достаточна без чтения соседних модулей. Нет обязательства запускать платный model CLI для проверки загрузки инструкций. Local structural audit не доказывает поведение каждого agent host.
