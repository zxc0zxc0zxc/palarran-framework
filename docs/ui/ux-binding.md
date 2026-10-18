# Source UX → UI: что сохраняем и что можно менять

## Выбор source concept

Читать target `.ai-development/ux/INDEX.md`, accepted decisions, source concepts/revisions и user intent. Если source указан — использовать его; иначе выбрать однозначно актуальный подходящий concept, объяснив выбор. При конфликте нескольких approved/draft revisions уточнить, не брать самый новый filename автоматически.

Без UX можно исследовать visual preference/brand/references, но полноценный screen design остаётся draft. Предложить путь к концепту или UX этап; не запускать новый большой UX scope и не выдумывать screens за пользователя. Draft UX можно использовать с явным статусом и gap list, не называя его approved.

## Mapping

`ux-map.md`: UX concept/revision/commit → UI revision/direction → каждый Screen/State/Block ID → preview/spec → ADR и статус покрытия. По умолчанию UI охватывает все in-scope UX screens и обязательные states, включая mobile/desktop. Partial scope только явно запрошенный либо отмеченный incomplete draft; красивые 2 hero screens не подменяют всё приложение.

Сохранять:

- user goals/roles/permissions и navigation/back/recovery;
- приоритет основных/вторичных действий, порядок данных и обязательную информацию;
- короткую точную UI copy из UX, field labels и ошибки;
- loading/empty/error/validation/pending/success/permission behavior;
- responsive функциональные альтернативы и accessibility intent.

UI добавляет typography/scale/weights, role-based colors, spacing/grid/density, borders/shapes, elevation/materials, imagery/icons, component visual states, motion и согласованный responsive styling. Это не разрешение менять outcome действия, data model или добавить onboarding/paywall/consent.

## Если стиль конфликтует с UX

Сначала адаптировать style под UX. Например, glass effect можно ослабить/заменить opaque surface, если он мешает читать форму; его наличие не оправдывает перенос главного CTA в непонятную floating область. Более плотная таблица не должна терять данные/действия на mobile.

Если нужен новый screen/layout structure или смена flow — оформить `ux-deltas.md` с source ID, причиной, альтернативами, impact и proposed UX change. Не править approved UX незаметно и не выдавать UI preference за business approval. Независимые visual решения продолжать; зависящий экран обозначить pending. Технические preview controls не должны оказаться в самом app UI.

## Обновление и handoff

При новой UX revision проверить mapping, obsolete screen/state и effects на tokens/components; старую UI revision не перезаписывать. Reuse прежней UI системы возможен только с проверкой source UX/brand/style assumptions. В review отдельно показать UX-preserved vs UX-delta; новый разработчик должен найти исходный смысл экрана без восстановления всей переписки.
