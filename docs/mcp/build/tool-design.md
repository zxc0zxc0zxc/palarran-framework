# Контракт от задачи

По [E-MCP-001](sources.md) начни с конкретных задач агента и observable success/failure. Посмотри existing services/SDK/client conventions; не строй tool на каждую endpoint/table. Один workflow tool уместен, если сохраняет ясный scope/ошибки; маленькие composable read tools полезны для отдельных состояний. Не объединяй чтение с неочевидным send/delete/charge. Не меняй продукт ради удобства агента.

Имя namespace.verb_object, понятные domain nouns и стабильные IDs. Description: что делает, когда использовать, required IDs/filters, что возвращает, важные ограничения/side effects. Не рекламный текст и не полный API manual. Для каждого argument type/unit/enum/bounds, required/default, unknown-property policy; examples на happy/error/ambiguous case. Нужные selection IDs сохранять даже в concise output. Не требовать UUID, если человек дал однозначное имя и tool может явно resolve; неоднозначность вернуть как варианты.

Output schema задаёт machine-readable result с provenance/version, достаточными полями для следующего шага, pagination и явной полнотой. Not found, permission denied, invalid input, unavailable/rate limited различать; errors actionable и sanitized, без stack trace/body/credentials. Не возвращать текст «успех» вместо наблюдаемого результата. При mutation — testable postcondition, idempotency key/unknown outcome/reconciliation, server-side authorization. Annotations описывают, но не обеспечивают права.

Выбор SDK/языка: existing project stack и supported official SDK/version, минимальная operational complexity; [SDK index](https://modelcontextprotocol.io/docs/sdk). Local stdio хорош для developer-owned tools; remote HTTP требует отдельного auth/transport/deploy design. Reference read-only catalog — пример контракта, а не default architecture для любого backend. Его `search_records` ищет данные; не заменяет discovery схем инструментов.

## Примеры использования

Для reference namespace support ниже показаны params для tools/call, не команды shell и не запрос на реальную внешнюю систему:

```json
{"name":"support.search_records","arguments":{"query":"deployment","limit":2,"response_format":"concise"}}
```

Из items взять стабильный ID; если content_complete=false, для полного ответа прочитать запись:

```json
{"name":"support.get_record","arguments":{"record_id":"deployment-guide"}}
```

limit="all" не соответствует контракту: известный tool вернёт isError/invalid_arguments. Исправить на ограниченное число; не менять schema/ignore errors ради PASS. При has_more копировать next_cursor с теми же query/response_format. Usage examples держать рядом с contract/host-supported instructions; не добавлять произвольные provider input_examples/defer_loading поля в стандартный MCP tools/list.
