# Canonical, дополнительные и свои visual references

## От UX research к UI research

Начать с source UX references и наблюдений: там уже есть релевантные бизнесы/screens. Проверить актуальность/платформу, не объявлять старый screenshot нынешним экраном. UX evidence поддерживает flow, но не автоматически выбранные colors/fonts/effects. Дополнительно изучить official foundations/components выбранной системы и как похожие реальные продукты применяют visual language.

Default: canonical system source + **не менее 2 дополнительных релевантных visual reference products/pages**. Не считать один и тот же screenshot дважды или method docs независимыми product examples. В custom mode присланные материалы — исходная основа; недостаток полноты можно закрывать дополнительным поиском без навязывания preset. Если источники недоступны, сохранять useful draft и coverage gaps, не выдумывать evidence ради quota.

## Собственные материалы пользователя

Поддерживаются URL сайтов/страниц, приложенные изображения/локальные файлы, screenshot collections, Figma links/files и краткие пожелания. До выводов открыть реальный источник/изображение доступным инструментом. Не считать название файла, alt-text или search snippet достаточным visual analysis. Если attachment недоступен, попросить приложить снова/дать доступный источник; текстовый инструмент вопросов не использовать для загрузки файла.

Для Figma/native-specific операций сначала применить требуемые host skills/tools. Не строить единственный workflow на наличии Figma или платной gallery. Ссылку на закрытый дизайн не обходить; использовать доступный preview/присланный кадр и обозначить scope. Публичная reference research не разрешает публикацию, изменение аккаунта или покупку assets.

Уточнять неизвестное через понятные вопросы: «В этом примере берём плотность и типографику или ещё палитру?» Если пользователь уже объяснил — не спрашивать повторно. Ref может быть anti-reference: записать, что избегать. Наличие картинки не означает согласие менять весь UX по ней.

## Карточка и наблюдения

В [reference template](../../templates/ui/reference.md) записать: ID, source URL/file, owner/publication/access date, platform/viewport/version (unknown отдельно), canonical/additional/user/anti-reference, что действительно видно и что интерпретируем. Для конкретного наблюдения `UI-R2-O01`: attribute → evidence crop/страница → применимость → proposed token/component/Screen ID → ADR.

Разбирать: palette roles/contrast, type hierarchy, whitespace/density/grid, shapes/borders/elevation, icons/imagery, motion/state treatment, responsive differences. Не утверждать точные font/hex/spacing по пиксельной догадке: нужны published tokens/inspectable source либо явно approximate estimate. Screenshot не подтверждает hover/focus/animation/keyboard поведение.

## Синтез

Выбрать governing source/brand rules и указать, что заимствуем/адаптируем/отвергаем у остальных. Palette от одного, type от другого и glass от третьего допустимы только при согласованной semantic token/component системе, не механическом collage. Existing project brand/accepted UI overrides приоритетны, если пользователь не просил смену.

Конфликты разрешать явно: наше UX действие/права, readability/accessibility и platform constraints сохраняются; спорный reference attribute становится proposed adaptation с альтернативой. Не переносить чужие логотипы, тексты, фотографии/real account data и font binaries как бесплатные production assets. Использовать разрешённые проектные assets, licensed substitutes или нейтральные placeholders.

## Evidence и ограничения

Screenshots/official examples — источник, generated mockups — наша визуальная гипотеза. Нельзя генерировать «скриншот Apple» и выдавать его за reference. Для remote image соблюдать доступ/preview ограничения tool host, не скачивать её в обход запрета отображения. Safe captures без personal data хранятся в task research; credentials/auth query strings и private customer content не попадают в Git.

В итоговом reference board указать источник и связь с нашим результатом, не только красивые картинки без объяснения. Короткая практическая интерпретация, не длинный конкурентный отчёт в пользовательском UI.
