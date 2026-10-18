# Параллельные agents в actual worktrees

Прочитать planned DAG/touch sets/contract ownership/resource budgets по [SDD plan](../plan/sdd-agents.md). В build выполнять parallel ready lanes, если они независимы и host поддерживает delegation. User request `/backend:build` с этим workflow задаёт scope parallel subtasks; не требовать повторного разрешения на каждый агент. Host/system policy имеет приоритет. Не создавать отдельные user chats вместо внутренних subagents.

## Подготовка и dispatch

1. Проверить existing worktrees/attachments и reuse подходящие owned clean checkouts. В host с managed worktree API использовать его lifecycle/attach/archive, иначе standard Git. Явно задать frozen base/ref: tool может по умолчанию брать remote default branch; после создания сверить path/HEAD/branch. Pending setup дождаться до dispatch.
2. Каждая пишущая lane получает отдельный checkout/branch от baseline с её dependencies/contracts. Parent dirty/untracked edits не копируются автоматически. Не использовать force checkout того же branch; integration checkout также имеет одного owner.
3. Контрактные/schema/migration/lockfile/shared index changes — один owner и serial gate. Готовые contracts интегрировать до dependent lanes или передать согласованный immutable version; generated files не правят несколько агентов одновременно.
4. [Packet](../../../templates/backend/execution-agent.md): абсолютный workspace path и требование использовать его как cwd **каждой** команды; source revisions/IDs, allowed/forbidden files, dependencies, deliverables, тесты/DoD, namespace/ports/resource limits, progress reporting и no external mutations beyond scope. Spawn сам по себе не меняет cwd: многие agent tools делят файловую систему.
5. Запустить только ready tasks в пределах max agents/CPU/RAM/DB/CI budget; независимые lane commits/checks в своих branches. Нельзя выдавать всем repo root как общий writable workspace. Агенты не редактируют canonical progress/spec/index параллельно; возвращают commit hashes, actual checks/evidence, deviations/blockers.

[Git worktree](https://git-scm.com/docs/git-worktree) разделяет рабочие trees, но repository и часть metadata общие. Для runtime каждому task отдельные ports, temp/artifacts, DB/schema/test tenant, queue/cache namespace и sandbox credentials reference; resource pools суммарно ограничены. Worktree не контейнер/сеть/DB sandbox. Если это невозможно — serial безопасная работа с причиной; не имитировать parallelism и не направлять destructive tests в общую DB.

## Интеграция

Coordinator проверяет task diff/commit ownership/actual outcomes, затем интегрирует по DAG/project policy в одном integration checkout. [Cherry-pick](https://git-scm.com/docs/git-cherry-pick) — возможный механизм переноса commits, не обязательная замена merge policy. Не тянуть чужие unrelated commits. При конфликте исправить осознанно с owner, прогнать affected checks; результат lane проверок не равен проверке integrated code.

После каждого integration обновить progress commit/state и invalidation affected checks; после всей группы — full required integrated suite/API+DB/cross-module checks и feature gates. Ready task verified на своей revision не доказывает что всё ещё верно после изменения её dependency. Новую ready wave dispatch только с корректным base, не на устаревший contract.

Agent unavailable/no delegation tools — не писать «агенты параллельно сделали». Выполнить доступные independent tasks serial, отметить limitation; если пользователь требует именно parallel execution, эта часть остаётся unmet. Small DAG max=1 по source обосновать, не создавать overhead ради числа агентов.

Worktree cleanup: проверить commits/dirty/untracked/needed ignored artifacts, сохранить/integrate evidence и code; managed archive через host API, plain worktree remove лишь owned clean checkout. Не force-remove чужое/незакоммиченное, не удалять branches с неперенесёнными commits. Никаких auto reset --hard/clean --force для разрешения конфликтов.
