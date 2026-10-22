# Датированные первичные источники

Проверено 2026-10-23. Внешние рекомендации — основания метода; наши offline результаты приведены отдельно в task handoff.

| Источник | Дата публикации / состояние | Что переносим | Предел |
|---|---|---|---|
| [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 2026-01-09 | task/trial/grader, повторные trials, проверяемый outcome, калибровка graders | Опыт автора, не доказательство качества нашего harness. Полные приватные reasoning traces не собираем |
| [Anthropic: Quantifying infrastructure noise](https://www.anthropic.com/research/infrastructure-noise) | 2026-02-05 | одинаковая среда/лимиты, инфраструктурные ошибки отдельно от ошибок решения | Их численные результаты не прогноз нашей экономии |
| [SWE-bench: Evaluation Guide](https://www.swebench.com/SWE-bench/guides/evaluation/) | rolling guide, проверен 2026-10-23 | применение результата и независимые repository tests, точный instance/patch | Наши небольшие fixtures не SWE-bench и не изолированные Docker environments |

Не копировать benchmark solutions в few-shot; удерживать holdout отдельно от обучающих карточек. Датасеты, версии контейнеров и зависимости требуют своих лицензий/проверок. v1 не устанавливает SWE-bench, не загружает наборы и не вызывает платных judges.
