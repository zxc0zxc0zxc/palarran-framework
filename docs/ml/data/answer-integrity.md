# Чтобы не деградировали общие и полные ответы

Две разные проблемы: forgetting общих навыков после узкой адаптации и механически оборванный/слишком краткий ответ. Состав данных влияет на обе, но не гарантирует решение. [Luo et al.](sources.md) и [Tülu 3](sources.md) — основания general regression/multi-skill evaluation; [LIMA](sources.md) — качество примеров. Для формата использовать actual [chat template и SFT semantics](sources.md), не универсальную строку EOS.

## Данные и objective

Сохранять substantive ответы, соответствующие задаче: короткие там, где достаточно, длинные там, где нужны объяснение, доказательство, код или несколько шагов. Не навязывать всем ответам один предел слов и не удалять «слишком длинное» ради красивого throughput. Увеличение длины само по себе не качество; оценивать полноту и корректность отдельно.

General anchor должен покрывать реально нужные навыки и языки; domain corpus — полные решения и сложные края. Не обучать модель на незавершённых генерациях teacher: `finish_reason=length`, потерянный tail, оборванный код/JSON, incomplete export должны попадать в quarantine/re-generation с отдельным budget, не автоматически получать EOS и label complete. Meta complete=true — заявление producer, не семантическая экспертиза текста.

Сравнить domain-only, domain+general replay и настройки adaptation/LR/epochs только на dev при одинаковом compute/exposure. LoRA/QLoRA не гарантируют отсутствие forgetting. Не выбирать лучший checkpoint только по domain loss: freeze допустимые general regressions и complete-answer критерии заранее.

## От raw messages до labels

1. Зафиксировать model/tokenizer revisions, actual tokenizer files/template SHA, role mapping, trainer/collator version и objective. Training template без generation suffix; generation template с нужным assistant prefix. Специальные токены не добавлять дважды после template render.
2. Измерять actual `input_ids`, `attention_mask`, assistant span mask и **unshifted** labels после collator; в decoder-only trainer shift может делаться внутри model. Tool v1 проверяет именно unshifted layout, не все trainer formats.
3. Assistant-only SFT: user/system/padding labels=-100, assistant target labels=input_ids. Causal pretraining имеет другой objective; не требовать assistant mask там. Zero supervised tokens или обучение только на EOS/EOT без non-end targets — blocker, не хороший нулевой loss.
4. Padding определять по attention_mask/позиции, а не по сравнению ID: pad_id иногда совпадает с eos_id. Настоящий EOT/EOS в конце полного assistant turn должен оставаться supervised. Выбор end_token_ids сверить с моделью: EOS, EOT и turn delimiters не всегда один token.
5. `prompt + response + required special tokens` должны помещаться в context window. Не делать generic truncation=True и затем ставить «конец» обрубку. Сначала bucket/smaller prompt/разрешённый semantic chunking; complete SFT answer сохранять целиком, иначе отклонить/переподготовить. При code/tool/multi-turn chunking сохранять зависимости и group lineage. Excess samples и lost target tokens обязательно учитывать по language/domain/length.
6. Packing — optimization, требующая проверки boundary/EOS, attention isolation либо явно принятого cross-example objective, position IDs и loss masks. В v1 token audit **unpacked only**, все input examples проверяются отдельно; packing integration NOT_RUN. Не обещать защиту от межпримерной утечки по одному EOS.

## Генерация и benchmark

После обучения отдельно проверить max_new_tokens/stop strings/eos_token_id, template compatibility, repetition/length penalty и finish_reason. Инференс cap может обрезать ответ даже при идеальном train corpus. Падение average answer length — сигнал, не автоматический FAIL: нужны correctness/completeness на одинаковых prompts и task-dependent expected length.

Frozen suite включает short factual, complete multi-part answer, длинный code+tests, schema JSON, multi-turn recall, multilingual/код-switch, длинный input+полный answer, benign controversial questions where allowed, и domain edges. Считать truncation/finish_reason=length, missing sections/invalid JSON, incomplete code/tests, unrequested refusal, factuality и verbosity отдельно. General acceptance = заранее заданные non-inferiority bounds по slices, N/uncertainty и сравнение base vs adapted exact checkpoint. Наш data gate не заменяет этот benchmark и не заявляет «общий ответ больше не режется» без обучения/инференс evidence.
