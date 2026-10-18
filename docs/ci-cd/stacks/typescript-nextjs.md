# TypeScript / Next.js

Определить Node и Next версии, package manager/lockfile, monorepo packages, App/Pages Router, SSR/SSG/ISR, build-time data fetching, backend API, test framework и target hosting. Для обычного TypeScript сервиса применять общие правила, Next-specific разделы пометить неприменимыми.

## Рекомендуемый DAG

| Ветка | Содержание | Оптимизация/границы |
|---|---|---|
| Format/lint/types | Реальные scripts проекта, ESLint и `tsc --noEmit` где применимо | Независимые jobs; не считать `next build` заменой lint в любой версии |
| Unit/component | Существующий Vitest/Jest или иной runner | Workers под RAM, affected graph только проверенный |
| Integration | API routes/server actions/auth/DB contracts | Ephemeral data/services, без production credentials |
| Build | Production Next artifact/container | `.next/cache`, lockfile, toolchain/base digest |
| E2E | Playwright critical journeys против собранного кандидата | Shards и browser coverage по риску, без повторного build каждого shard |
| Security | Dependency policy, image scan, secrets/public bundle checks | Не только `npm audit` и не blanket ignore findings |

Lockfile определяет manager: [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/) требует согласованного lock; pnpm/yarn frozen/immutable flags выбрать под pinned manager. Не смешивать package managers и не выполнять unpinned `npx` installation в trusted release. Installer lifecycle scripts тоже исполняемый код, особенно при private dependency credentials.

## Кеширование и E2E

[Next CI caching](https://nextjs.org/docs/app/guides/ci-build-caching): сохранять `.next/cache` в scope OS/arch/Node/Next/lock/config/trust и релевантных build inputs. Это **не готовый deploy artifact**. Cache может содержать fetched data: не допускать production private data в cache, доступный PR. Caching package-manager store обычно безопаснее слепого reuse `node_modules`; monorepo task cache требует completeness inputs и trusted writers.

Build один раз на release candidate; E2E shards запускаются против этого image/изолированных instance с одинаковым digest. [Playwright sharding](https://playwright.dev/docs/test-sharding) настраивается с учётом file/test granularity и fixture изоляции, reports объединяются после проверки всех shards. [Playwright CI](https://playwright.dev/docs/ci) не рекомендует считать browser binary caching универсальным ускорением; prebuilt browser image должен соответствовать package version, OS dependencies и arch.

Production env не используется для E2E fixtures. Trace/screenshots/HTML могут хранить headers/cookies/PII; ограничить capture, redaction/access/retention, не upload всего каталога. Не заменять ожидаемые network conditions фиксированными sleeps. Большой E2E suite вынести в отдельные shards, критичные journeys остаются release gate, дополнительные browsers не превращать в никогда не запускаемые jobs.

## Build once: важное ограничение Next.js

[`NEXT_PUBLIC_*`](https://nextjs.org/docs/app/guides/environment-variables) встраиваются в клиентский bundle во время build. Переменная в prod container не изменит уже встроенный test API URL. Server-side static generation и обращения к CMS тоже могут зафиксировать данные/конфиг при сборке. Публичный client config не должен содержать secrets вообще.

Предпочтительное решение для одного digest dev→test→prod: одинаковые public build inputs, same-origin API маршруты или специально спроектированный non-secret runtime configuration endpoint; server secrets читать на runtime там, где route/rendering mode реально это позволяет. Не обещать, что «все env становятся runtime» автоматически. Runtime config endpoint доступен клиенту и возвращает только разрешённые публичные поля.

Если проекту необходимы разные build-time значения, зафиксировать исключение: отдельные immutable build variants, каждый со своей идентичностью/digest и проверками. Нельзя называть их продвижением одного и того же artifact. Скилл обсуждает этот выбор до генерации deploy pipeline.

## Packaging, scaling и deploy

[Standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output) уменьшает runtime package, но проверить копирование `public`/`.next/static` и traced monorepo files; standalone не автоматически включает всё. Для native modules/image optimization проверить libc/arch/runtime deps. Server smoke запускается из production image, не dev server.

[Self-hosting](https://nextjs.org/docs/app/guides/self-hosting) требует отдельной проработки cache consistency/invalidation и совместимости нескольких instances/builds. Shared cache, version skew/server actions и graceful rollout — runtime вопросы, которые CI не решает одним `next build`. У runtime cache есть ограниченные writable paths; read-only rootfs настраивать по фактическим требованиям.

Deploy через GitOps или managed hosting API; если PaaS пересобирает source на каждом environment, это отдельный backend contract, не незаметное нарушение build-once. Проверить возможность deploy prebuilt artifact и переносимость adapter, не объявлять любой OCI image пригодным для всех hosting providers.

## Приёмка

PR required lint/types/tests и production build не обходятся флагами ignore errors; exact image проходит E2E; публичные URL dev/test не протекают в prod bundle; secrets не найдены в bundles/source maps/reports/cache; standalone assets и native modules доступны; Node/Next versions pinned; cache miss корректен; observed deploy показывает release digest и успешные SSR/API journeys. До выполнения этих проверок статический документ не даёт production-ready статус.
