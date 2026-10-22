# Modal: ресурсы, запуск и восстановление

Этот guide описывает Modal Functions training jobs; runtime Sandbox backend имеет отдельный [контракт](modal-adapter.md). Modal Training/Dojo, Sandbox и другие продукты не считать взаимозаменяемыми: отдельно проверять API maturity, цены и разрешения. Мы не подключаем сервис, не создаём аккаунт и не устанавливаем SDK при чтении документации.

## Тарифный ориентир

Проверено 2026-10-20 по [официальной странице](https://modal.com/pricing); это несколько ориентиров, не вечный прайс и не обещание доступности GPU. USD per GPU-second: T4 `0.000164`, L4 `0.000222`, A10 `0.000306`, A100 80 GB `0.000694`, H100 SXM5 `0.001097`. Functions CPU: `0.0000131` за physical core-second; RAM: `0.00000222` за GiB-second. На странице Sandbox CPU/RAM имеют другие rates. Все значения перед запуском перепроверять; billed CPU/RAM/ephemeral disk объясняет [resources guide](https://modal.com/docs/guide/resources).

Storage и egress считать отдельными строками с актуальной inclusion/plan basis, без автоматического «бесплатно». [Volumes](https://modal.com/docs/guide/volumes) описывает snapshot-based storage billing и возможное продолжение платы после удаления; retention не заканчивается по завершении GPU run.

## Reviewable launch packet

До paid action подготовь exact plan/config hash, source/image/lockfile, model/data/license refs, region/privacy/storage, GPU type/count, CPU/RAM/disk request+limits, concurrency, wall/step/token caps, exception retry/preemption policy, total reserve, existing secret **names**, outputs, checkpoint и stop/reconciliation commands. Примеры `app.function(gpu=..., timeout=..., retries=...)` сами по себе не training pipeline. SDK version/API signatures сверяются с текущими official reference; не отправлять вызов «на пробу» для поиска правильного API.

Сначала локально проверить подготовленный code/config (в execution scope), smoke на tiny train-only set, загрузку/сохранение checkpoint и data visibility. GPU smoke/pilot тоже платный attempt и требует бюджета. Создание Volume, image build, account authentication, upload, deploy/invoke — внешние действия; explicit plan-only их не делает. Существующие resources проверять read-only только в разрешённом execution scope; `from_name(..., create_if_missing=True)` может создавать storage и не годится для read-only inventory.

## Timeouts и retries

[Modal timeouts](https://modal.com/docs/guide/timeouts) применяются к отдельному execution attempt, а не ко всей logical job; startup отдельно. [Retries](https://modal.com/docs/guide/retries) добавляют новые attempts. Наша рекомендация: не включать exception retries без выделенного лимита/резерва и resume protocol. При OOM сначала анализ memory/sequence/batch, не автоэскалация GPU. Потеря соединения не доказывает, что compute завершён.

[Preemption](https://modal.com/docs/guide/preemption) по документации может перезапускать тот же input. Поэтому один client invocation не гарантирует один billable execution. Стабильный logical run ID + per-start attempt ID, durable attempt/restart counter, общий deadline и резерв нужны внутри процесса/хранилища, а не только в живом клиенте. Если SDK не даёт достаточно сведений/контроля, пометить enforcement gap и не обещать строго ограниченный spending.

## Checkpoints и остановка

Сохраняй immutable step-specific checkpoint path, закрой файлы, проверь manifest/hash и explicit durability (`Volume.commit()` для используемой Volume семантики). [Volumes guide](https://modal.com/docs/guide/volumes) объясняет commit/reload; простое наличие локального файла не доказательство persistent artifact. Не допускать нескольких writers одного checkpoint; interrupted write не публикует completed manifest. Graceful signal handler — дополнение, periodic checkpoints нужны и при неуспевшем handler.

Abort должен остановить конкретный job и проверить terminal provider outcome; отключение polling, закрытие терминала или отмена локального subprocess не обязательно отменяют remote compute. Сохрани cancellation acknowledgement/terminal timestamp, последний durable checkpoint, estimate и неизвестный usage. Нет подтверждения — unknown, reserve удерживается, retry запрещён до reconciliation. Не удаляй volumes/checkpoints и не деплой модель как часть уборки без отдельного scope.
