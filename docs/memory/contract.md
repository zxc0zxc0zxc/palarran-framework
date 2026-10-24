# Контракт memory-v001

## Авторизация и запись

`POST /v1/<operation>` с JSON object и bearer token. Agent credential: search/get/neighbors/artifact/propose/feedback. Reviewer credential: те же операции плюс promote и link. Токены разные, минимум32 символа, constant-time comparison; не передавать в argv/MCP config с plaintext. Credentials берутся из защищённого global/project env по operations.md; MCP использует только agent credential view. Общий файл одного owner не изолирует недоверенные процессы OS. В HTTP нет public TLS: только loopback/SSH tunnel; proxy redirects/env proxy отключены.

`propose` принимает ровно `case` и optional `artifacts`. Схема case: type (pattern/incident/decision/solution/anti_pattern), title, problem, root_cause, solution, applies_when[], limitations[], tags[], source{repo,commit,adr}, evidence[] и privacy_reviewed:true. Repo — безопасный alias, без remote URL/credentials. Commit —40/64 lowercasehex. Evidence — обезличенные ссылки/IDs, не raw logs. Privacy flag — заявление автора, не автоматическая гарантия: reviewer проверяет содержимое. В явно включённом owner automatic cycle reviewer — trusted local coordinator после agent privacy/evidence review и детерминированных gates; это не независимый semantic/PII oracle. Нет загрузки приватных originals по ссылкам.

Артефакты: до4 текстов, type adr/patch/verification, summary и text; до128KiB каждый. UTF-8, без control chars; basic secret-pattern rejection — defence in depth, не полный DLP. SHA-256 dedup, private files, quota по всему store. DB failure может оставить immutable orphan: это не видимый case; GC только по согласованной retention, не автоматическое удаление.

Canonical case JSON <=8KiB; feedback JSON <=2KiB. get возвращает по3feedback/review entries с next_feedback_offset/next_review_offset. Порядок по stable ID; при concurrent inserts начать страницы заново. MCP request <=64KiB: большие разрешённые артефакты передавать через explicit HTTP client, не обрезать.

Candidate виден только своему project scope. `promote` требует reviewer, exact case ID, reason, evidence_reviewed:true и target status global/rejected/retracted. Нет отдельного автоматического LLM evaluator. Global означает reviewed portable experience, не универсальное правило. Retraction исключает global recall, история/status остаются при get с разрешённым project scope. Одинаковое повторное promote не даёт новую версию контента.

`feedback` идемпотентен по card+repo+commit+outcome+note; исход helped/not_applicable/refuted и evidence обязательны. `link` reviewer-only, фиксированный relation allowlist, source/target должны существовать. Отсутствие endpoint — ошибка, не успешная пустая запись. SUPERSEDES не удаляет predecessor и не утверждает истинность автоматически.

## Чтение и ошибки

Каждая операция несёт project alias; shared global + exact project visibility. Это фильтр контекста одного владельца, не ACL между враждебными пользователями. Search literal query <=256char, limit1..5, native card+artifact fulltext, candidate cap200. matched_artifact содержит hash/offset для jump к соответствующей странице; совпадение карточки даёт null fields. get по hash. Neighbors максимум20, явно has_more. Artifact <=4096символов/страница, next_offset и complete; выдача разрешена только для доступного case, который ссылается на hash. No path traversal/symlink reads.

JSON <=1MiB request/response, timeout на socket/DB, JSON duplicates/nonfinite/malformed отвергаются. Service logs не содержат headers/body/query/data/credentials. DB/network unknown result: ошибка reconciliation_required; не auto-retry write. Deterministic IDs позволяют сначала get, но не превращают lost reply в known zero execution.

MCP gateway pins lifecycle/tools profile из mcp-build; mutation annotations соответствуют поведению, promote/link отсутствуют из обычного agent tool inventory. Additional local reviewer mode должен включаться явно и с reviewer credential. Tool responses содержат structuredContent и идентичный JSON text. Это stdio bridge к private HTTP API, не remote Streamable HTTP implementation и не full SDK conformance.
