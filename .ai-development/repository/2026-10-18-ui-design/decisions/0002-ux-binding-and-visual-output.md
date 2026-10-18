---
id: repository/2026-10-18-ui-design/0002
status: accepted
date: 2026-10-18
scope: ui-design-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ux-design/0002]
supersedes: []
superseded_by: []
---

# UI привязан к UX и даёт видимый результат

## Контекст и основание

Нужен visual design на наших UX concepts, responsive и сохраняемые решения. Прежний UX skill не реализует бренд/style.

## Выбор и объяснение

Зафиксировать source UX revision/Screen/State/Block IDs и сохранить navigation/actions/short copy/role behavior. UI задаёт type/color/spacing/shape/elevation/icons/motion и visual states. Default deliverable — local responsive HTML/CSS preview из synthetic data плюс tokens/components/screen specs; не production app edits. Для explicit Figma/native output использовать соответствующие tools/skills, не принуждать к ним.

## Альтернативы

Один Markdown/Mermaid report не показывает visual design. Смена UX ради красивого стиля ломает исходный контракт: UX changes только отдельным proposed delta с причинами. Раскрашенная desktop-картинка не доказывает responsiveness; нужны narrow/mobile/tablet/desktop, state views и actual render checks.

## Источники и evidence

Прямой запрос; accepted UX screen contract repository/2026-10-18-ux-design/0002; W3C contrast/reflow/focus/color/target-size и documented system foundations.

## Последствия и пересмотр

Если UX отсутствует/неясно какой актуален — запросить путь/выбор или предложить UX этап; style exploration возможно отдельно, полный screen set пока draft. Approval UX/UI не выдумывать. Пересмотр при изменении source UX или output medium.

## Применение и проверка

Реализовано. Local validation/package/skill checks PASS; подробная evidence и границы в [handoff](../handoff.md). Реального application UI target здесь нет.
