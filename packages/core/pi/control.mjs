/** Transactional command handling; process and model effects live elsewhere. */
import {
  need,
  id,
  text,
  integer,
  parent,
  limits,
  taskSpec,
  checkDag,
  stable,
  digest,
  token,
  GLOBAL_LIMITS,
} from "./validation.mjs";
const terminal = new Set([
  "SUCCEEDED",
  "SUBMITTED",
  "FAILED",
  "CANCELLED",
  "BLOCKED",
]);
export function snapshot(store, payload) {
  const run = store.owned(payload),
    tasks = store.all(
      "SELECT id,state,fence,verification,integrated_commit FROM tasks WHERE run_id=? ORDER BY id",
      run.id,
    ),
    counts = {
      total: tasks.length,
      queued: 0,
      starting: 0,
      cancelling: 0,
      running: 0,
      succeeded: 0,
      failed: 0,
      cancelled: 0,
      unknown: 0,
      submitted: 0,
      blocked: 0,
    };
  for (const t of tasks) {
    const k = t.state.toLowerCase();
    counts[k] = (counts[k] || 0) + 1;
  }
  return {
    status: run.status,
    run_id: run.id,
    counts,
    budget: store.budget(run.id),
    limits: JSON.parse(run.limits),
    attention: tasks
      .filter((t) => t.state === "UNKNOWN")
      .map((t) => ({ task_id: t.id, reason: "outcome_unknown" })),
    evidence_mode: store.get(
      "SELECT count(*) n FROM tasks WHERE run_id=? AND json_extract(spec,'$.profile.kind')='sdk'",
      run.id,
    ).n
      ? "provider_candidates"
      : "synthetic",
    tasks: tasks.slice(0, 50).map((t) => ({
      task_id: t.id,
      status: t.state,
      fence: t.fence,
      verification: t.verification,
      integrated_commit: t.integrated_commit,
    })),
    tasks_truncated: tasks.length > 50,
    acceptance: "NOT_RUN",
  };
}
function activeAttempt(store, p) {
  const { run, task } = store.task(p),
    attempt = store.get("SELECT * FROM attempts WHERE id=?", p.attempt_id);
  need(
    attempt &&
      attempt.run_id === run.id &&
      attempt.task_id === task.id &&
      attempt.fence === p.fence,
    "attempt_identity_mismatch",
  );
  need(
    task.fence === p.fence &&
      task.attempt_id === attempt.id &&
      ["STARTING", "RUNNING"].includes(task.state) &&
      run.approved &&
      ["RUNNING", "INTEGRATING"].includes(run.status),
    "stale_attempt",
  );
  return { run, task, attempt };
}
export function requestAdmit(store, p) {
  return store.tx(() => {
    const { run, task } = activeAttempt(store, p);
    id(p.request_id);
    const spec = JSON.parse(task.spec),
      profile = spec.profile;
    need(
      profile.kind === "sdk" &&
        p.provider === profile.provider &&
        p.model === profile.model,
      "profile_mismatch",
    );
    const inputs = integer(p.input_tokens_bound, 1e9),
      outputs = integer(p.output_tokens_bound, 1e7, 1),
      cost = integer(p.cost_micros_bound, 1e12),
      reserve = integer(inputs + outputs, 1e9, 1);
    need(outputs <= profile.max_output_tokens, "output_cap_exceeded");
    const pricing = profile.pricing;
    need(pricing && typeof pricing === "object", "missing_pricing");
    const inputRate = Math.max(
      integer(pricing.input_micros_per_million, 1e12),
      integer(
        pricing.cache_read_micros_per_million ??
          pricing.input_micros_per_million,
        1e12,
      ),
      integer(
        pricing.cache_write_micros_per_million ??
          pricing.input_micros_per_million,
        1e12,
      ),
    );
    const outputRate = integer(pricing.output_micros_per_million, 1e12);
    const required =
      (BigInt(inputs) * BigInt(inputRate) +
        BigInt(outputs) * BigInt(outputRate) +
        999999n) /
      1000000n;
    need(BigInt(cost) >= required, "request_cost_underreserved");
    const hash = digest(p),
      prior = store.get("SELECT * FROM requests WHERE id=?", p.request_id);
    if (prior) {
      need(prior.hash === hash, "request_id_conflict");
      return {
        status: prior.stream_active ? "ADMITTED" : "RECORDED",
        request_id: p.request_id,
      };
    }
    const b = store.budget(run.id);
    need(
      b.tokens_used + b.tokens_reserved + reserve <= b.token_limit &&
        b.cost_micros_used + b.cost_micros_reserved + cost <=
          b.cost_micros_limit,
      "budget_exhausted",
    );
    const limit = JSON.parse(run.limits);
    if (
      store.get("SELECT count(*) n FROM requests WHERE stream_active=1").n >=
        GLOBAL_LIMITS.model_requests ||
      store.get(
        "SELECT count(*) n FROM requests WHERE stream_active=1 AND run_id=?",
        run.id,
      ).n >= limit.model_requests
    )
      return { status: "WAIT", code: "request_capacity" };
    store.run(
      "INSERT INTO requests(id,run_id,task_id,attempt_id,fence,hash,state,stream_active,tokens_reserved,cost_reserved,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
      p.request_id,
      run.id,
      task.id,
      p.attempt_id,
      p.fence,
      hash,
      "ADMITTED",
      1,
      reserve,
      cost,
      Date.now(),
    );
    store.event(run.id, "request_admitted", task.id, {
      request_id: p.request_id,
    });
    return { status: "ADMITTED", request_id: p.request_id };
  });
}
export function requestComplete(store, p) {
  return store.tx(() => {
    const run = store.owned(p),
      r = store.get("SELECT * FROM requests WHERE id=?", p.request_id);
    need(
      r &&
        r.run_id === run.id &&
        r.task_id === p.task_id &&
        r.attempt_id === p.attempt_id &&
        r.fence === p.fence,
      "request_identity_mismatch",
    );
    need(
      ["known", "unknown", "cancelled"].includes(p.outcome),
      "invalid_request_outcome",
    );
    const hash = digest({ outcome: p.outcome, usage: p.usage ?? null });
    if (r.usage_hash) {
      need(r.usage_hash === hash, "usage_conflict");
      return { status: "RECORDED", request_id: r.id };
    }
    if (p.outcome === "known") {
      const u = p.usage;
      need(u && typeof u === "object", "missing_usage");
      const tokens = [
          "input_tokens",
          "output_tokens",
          "cache_read_tokens",
          "cache_write_tokens",
        ].reduce((n, k) => n + integer(u[k] ?? 0, 1e9), 0),
        cost = integer(u.cost_micros, 1e12);
      store.run(
        "UPDATE requests SET state=?,stream_active=0,tokens_reserved=0,cost_reserved=0,tokens_used=?,cost_used=?,usage_hash=? WHERE id=?",
        "KNOWN",
        tokens,
        cost,
        hash,
        r.id,
      );
    } else
      store.run(
        "UPDATE requests SET state=?,stream_active=0 WHERE id=?",
        "UNKNOWN",
        r.id,
      );
    store.event(run.id, "request_completed", r.task_id, {
      request_id: r.id,
      outcome: p.outcome,
    });
    const status = store.settleRun(run.id);
    return { status: "RECORDED", request_id: r.id, run_status: status };
  });
}
export function handle(store, command, p = {}) {
  if (command === "doctor")
    return {
      status: "READY",
      schema_version: 1,
      node_version: process.versions.node,
      limits: GLOBAL_LIMITS,
      model_calls: 0,
      supported_sdk: "1.0.0",
      live_provider_acceptance: "NOT_RUN",
    };
  if (command === "request_admit") return requestAdmit(store, p);
  if (command === "request_complete") return requestComplete(store, p);
  if (command === "spawn")
    return store.tx(() => {
      const scope = parent(p.parent),
        key = id(p.idempotency_key);
      return store.command(stable(scope), key, p, () => {
        const lim = limits(p.limits);
        need(
          Array.isArray(p.tasks) &&
            p.tasks.length > 0 &&
            p.tasks.length <= lim.queue,
          "queue_capacity",
        );
        need(
          store.get(
            "SELECT count(*) n FROM tasks WHERE state IN ('QUEUED','STARTING','RUNNING','CANCELLING')",
          ).n +
            p.tasks.length <=
            GLOBAL_LIMITS.queue,
          "host_queue_capacity",
        );
        const tasks = p.tasks.map((t) => taskSpec(t, scope));
        checkDag(tasks);
        const budget = p.budget || { tokens: 0, cost_micros: 0 };
        integer(budget.tokens, 1e12);
        integer(budget.cost_micros, 1e12);
        need(
          !tasks.some((t) => t.profile.kind === "sdk") ||
            (budget.tokens > 0 && budget.cost_micros > 0),
          "explicit_budget_required",
        );
        const runId = p.run_id ? id(p.run_id) : token("run"),
          now = Date.now();
        need(!store.get("SELECT id FROM runs WHERE id=?", runId), "run_exists");
        store.run(
          "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?)",
          runId,
          stable(scope),
          digest({ tasks, limits: lim, budget }),
          stable(lim),
          stable(budget),
          "DRAFT",
          0,
          now,
          now,
        );
        for (const t of tasks)
          store.run(
            "INSERT INTO tasks(run_id,id,spec,state,agent_id) VALUES(?,?,?,?,?)",
            runId,
            t.task_id,
            stable(t),
            "QUEUED",
            token("agent"),
          );
        store.event(runId, "run_created", null, { tasks: tasks.length });
        return {
          status: "QUEUED",
          run_id: runId,
          handles: tasks.map((t) => ({ run_id: runId, task_id: t.task_id })),
          launches: 0,
        };
      });
    });
  if (command === "status") return snapshot(store, p);
  if (command === "events" || command === "wait") {
    const run = store.owned(p),
      after = integer(p.after ?? 0),
      limit = integer(p.limit ?? 20, 100, 1),
      events = store
        .all(
          "SELECT seq,type,task_id,data,created FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT ?",
          run.id,
          after,
          limit,
        )
        .map((e) => ({ ...e, data: JSON.parse(e.data) }));
    return {
      status: "EVENTS",
      run_id: run.id,
      cursor: events.at(-1)?.seq ?? after,
      events,
      run_status: run.status,
    };
  }
  if (command === "result") {
    const { run, task } = store.task(p);
    return {
      status: task.result ? "RESULT" : "PENDING",
      run_id: run.id,
      task_id: task.id,
      execution_status: task.state,
      execution_mode: JSON.parse(task.spec).profile.kind,
      verification: task.verification,
      result: task.result ? JSON.parse(task.result) : null,
      acceptance: "NOT_RUN",
    };
  }
  if (command === "send")
    return store.tx(() => {
      const { run, task } = store.task(p);
      const message = text(p.message, 8192);
      return store.command(run.id, id(p.idempotency_key), p, () => {
        need(
          store.get("SELECT count(*) n FROM messages WHERE run_id=?", run.id)
            .n < 1000,
          "mailbox_capacity",
        );
        const row = store.run(
          "INSERT INTO messages(run_id,task_id,body,created) VALUES(?,?,?,?)",
          run.id,
          task.id,
          message,
          Date.now(),
        );
        store.event(run.id, "message_queued", task.id, {
          message_id: Number(row.lastInsertRowid),
        });
        return { status: "RECORDED", message_id: Number(row.lastInsertRowid) };
      });
    });
  if (command === "mailbox") {
    const { run, task } = activeAttempt(store, p),
      after = integer(p.after ?? 0);
    const messages = store
      .all(
        "SELECT id,body FROM messages WHERE run_id=? AND task_id=? AND id>? ORDER BY id LIMIT 20",
        run.id,
        task.id,
        after,
      )
      .map((m) => ({ id: m.id, message: m.body }));
    return {
      status: "MESSAGES",
      cursor: messages.at(-1)?.id ?? after,
      messages,
    };
  }
  if (command === "follow_up")
    return store.tx(() => {
      const { run, task } = store.task(p);
      need(terminal.has(task.state), "agent_still_active");
      need(
        !["ATTENTION", "BUDGET_OVERRUN", "CANCELLED", "CANCELLING"].includes(
          run.status,
        ),
        "run_not_continuable",
      );
      return store.command(run.id, id(p.idempotency_key), p, () => {
        const count = store.get(
          "SELECT count(*) n FROM tasks WHERE run_id=?",
          run.id,
        ).n;
        need(count < JSON.parse(run.limits).queue, "queue_capacity");
        const spec = taskSpec(
          { ...JSON.parse(task.spec), ...p.task, depends_on: [] },
          JSON.parse(run.parent),
        );
        need(
          spec.task_id !== task.id &&
            !store.get(
              "SELECT id FROM tasks WHERE run_id=? AND id=?",
              run.id,
              spec.task_id,
            ),
          "task_exists",
        );
        need(
          spec.repository === JSON.parse(task.spec).repository &&
            stable(spec.profile) === stable(JSON.parse(task.spec).profile) &&
            spec.mode === JSON.parse(task.spec).mode &&
            stable(spec.files) === stable(JSON.parse(task.spec).files),
          "follow_up_scope_change",
        );
        store.run(
          "INSERT INTO tasks(run_id,id,spec,state,agent_id) VALUES(?,?,?,?,?)",
          run.id,
          spec.task_id,
          stable(spec),
          "QUEUED",
          task.agent_id,
        );
        store.run(
          "UPDATE runs SET status=? WHERE id=?",
          run.approved ? "RUNNING" : "DRAFT",
          run.id,
        );
        store.event(run.id, "follow_up_queued", spec.task_id, {
          agent_id: task.agent_id,
        });
        return {
          status: "QUEUED",
          run_id: run.id,
          task_id: spec.task_id,
          launches: 0,
        };
      });
    });
  if (command === "approve" || command === "start")
    return store.tx(() => {
      const run = store.owned(p);
      need(["DRAFT", "RUNNING"].includes(run.status), "run_not_approvable");
      if (!run.approved) {
        store.run(
          "UPDATE runs SET approved=1,status=?,updated=? WHERE id=?",
          "RUNNING",
          Date.now(),
          run.id,
        );
        store.event(run.id, "run_approved");
      }
      return { status: "APPROVED", run_id: run.id, launches: 0 };
    });
  if (command === "cancel")
    return store.tx(() => {
      const run = store.owned(p);
      if (!p.task_id) {
        store.run(
          "INSERT OR REPLACE INTO meta VALUES(?,?)",
          "cancel:" + run.id,
          "1",
        );
        store.run(
          "UPDATE integration_operations SET status=CASE WHEN status='QUEUED' THEN 'CANCELLED' ELSE 'CANCELLING' END WHERE run_id=? AND status IN ('QUEUED','STARTING','RUNNING')",
          run.id,
        );
      }
      if (p.task_id) {
        store.run(
          "UPDATE integration_operations SET status=CASE WHEN status='QUEUED' THEN 'CANCELLED' ELSE 'CANCELLING' END WHERE run_id=? AND status IN ('QUEUED','STARTING','RUNNING') AND EXISTS (SELECT 1 FROM json_each(integration_operations.payload,'$.items') WHERE json_extract(value,'$.task_id')=?)",
          run.id,
          p.task_id,
        );
      }
      const tasks = p.task_id
        ? [store.task(p).task]
        : store.all("SELECT * FROM tasks WHERE run_id=?", run.id);
      for (const t of tasks) {
        if (
          terminal.has(t.state) &&
          !(t.state === "SUBMITTED" && !t.integrated_commit)
        )
          continue;
        const state = ["STARTING", "RUNNING", "CANCELLING"].includes(t.state)
          ? "CANCELLING"
          : t.state === "UNKNOWN" &&
              t.attempt_id &&
              !store.get(
                "SELECT stopped FROM attempts WHERE id=?",
                t.attempt_id,
              )?.stopped
            ? "CANCELLING"
            : t.state === "UNKNOWN"
              ? "UNKNOWN"
              : "CANCELLED";
        if (t.state !== state) {
          store.run(
            "UPDATE tasks SET state=?,fence=fence+1 WHERE run_id=? AND id=?",
            state,
            run.id,
            t.id,
          );
          if (state === "CANCELLING" && t.attempt_id)
            store.run(
              "UPDATE attempts SET state=? WHERE id=?",
              "CANCELLING",
              t.attempt_id,
            );
          store.event(run.id, "cancel_requested", t.id, { status: state });
        }
      }
      const status = store.settleRun(run.id);
      return {
        status:
          status === "CANCELLED" ||
          (p.task_id && store.task(p).task.state === "CANCELLED")
            ? "CANCELLED"
            : tasks.some((t) =>
                  ["RUNNING", "STARTING", "CANCELLING"].includes(t.state),
                )
              ? "CANCELLING"
              : status,
        run_id: run.id,
      };
    });
  if (command === "phase_admit")
    return store.tx(() => {
      const run = store.owned(p);
      need(
        run.approved &&
          !["ATTENTION", "BUDGET_OVERRUN", "CANCELLED", "CANCELLING"].includes(
            run.status,
          ),
        "run_not_approved",
      );
      need(["integration", "verification"].includes(p.kind), "invalid_phase");
      const kind = p.kind === "integration" ? "integration" : "heavy",
        cap = GLOBAL_LIMITS[kind];
      if (
        store.get(
          "SELECT count(*) n FROM phase_leases WHERE kind=? AND state IN ('ACTIVE','UNKNOWN')",
          kind,
        ).n >= cap ||
        store.get(
          "SELECT count(*) n FROM phase_leases WHERE kind=? AND run_id=? AND state IN ('ACTIVE','UNKNOWN')",
          kind,
          run.id,
        ).n >= JSON.parse(run.limits)[kind]
      )
        return { status: "WAIT", code: "phase_capacity" };
      const ticket = token("phase");
      store.run(
        "INSERT INTO phase_leases VALUES(?,?,?,?,?)",
        ticket,
        run.id,
        kind,
        "ACTIVE",
        Date.now(),
      );
      return { status: "ADMITTED", ticket };
    });
  if (command === "phase_complete")
    return store.tx(() => {
      const run = store.owned(p),
        row = store.get("SELECT * FROM phase_leases WHERE id=?", p.ticket);
      need(row && row.run_id === run.id, "unknown_phase");
      need(["known", "unknown"].includes(p.outcome), "invalid_phase_outcome");
      store.run(
        "UPDATE phase_leases SET state=? WHERE id=?",
        p.outcome === "known" ? "DONE" : "UNKNOWN",
        p.ticket,
      );
      return { status: "RECORDED" };
    });
  need(false, "unknown_command", "command");
}
export function claim(store) {
  return store.tx(() => {
    const count = store.get(
      "SELECT count(*) n FROM attempts WHERE stopped=0",
    ).n;
    if (count >= GLOBAL_LIMITS.workers) return null;
    const last =
      store.get("SELECT value FROM meta WHERE key=?", "last_parent")?.value ||
      "";
    const runs = store.all(
      "SELECT * FROM runs WHERE approved=1 AND status='RUNNING' ORDER BY CASE WHEN parent=? THEN 1 ELSE 0 END,updated,id",
      last,
    );
    for (const run of runs) {
      const lim = JSON.parse(run.limits);
      if (
        store.get(
          "SELECT count(*) n FROM attempts WHERE run_id=? AND stopped=0",
          run.id,
        ).n >= lim.workers
      )
        continue;
      for (const task of store.all(
        "SELECT * FROM tasks WHERE run_id=? AND state='QUEUED' ORDER BY id",
        run.id,
      )) {
        if (
          store.get(
            "SELECT count(*) n FROM attempts a JOIN tasks t ON t.run_id=a.run_id AND t.id=a.task_id WHERE t.agent_id=? AND a.stopped=0",
            task.agent_id,
          ).n
        )
          continue;
        const checkpoint = store.get(
          "SELECT * FROM agent_checkpoints WHERE agent_id=?",
          task.agent_id,
        );
        const spec = JSON.parse(task.spec),
          deps = spec.depends_on.map((d) => ({
            d,
            t: store.get(
              "SELECT * FROM tasks WHERE run_id=? AND id=?",
              run.id,
              d.task_id,
            ),
          }));
        if (
          deps.some(
            ({ t }) =>
              t && ["FAILED", "CANCELLED", "BLOCKED"].includes(t.state),
          )
        ) {
          store.run(
            "UPDATE tasks SET state=? WHERE run_id=? AND id=?",
            "BLOCKED",
            run.id,
            task.id,
          );
          store.event(run.id, "dependency_failed", task.id);
          continue;
        }
        if (
          deps.some(
            ({ d, t }) =>
              !t ||
              (d.condition === "artifact" && !t.result) ||
              (d.condition === "verified" && t.verification !== "PASS") ||
              (d.condition === "integrated" && !t.integrated_commit),
          )
        )
          continue;
        if (spec.mode === "write") {
          const global = store.get(
            "SELECT count(*) n FROM attempts a JOIN tasks t ON t.run_id=a.run_id AND t.id=a.task_id WHERE a.stopped=0 AND json_extract(t.spec,'$.mode')='write'",
          ).n;
          if (
            global >= GLOBAL_LIMITS.writers ||
            store.get(
              "SELECT count(*) n FROM attempts a JOIN tasks t ON t.run_id=a.run_id AND t.id=a.task_id WHERE a.run_id=? AND a.stopped=0 AND json_extract(t.spec,'$.mode')='write'",
              run.id,
            ).n >= lim.writers
          )
            continue;
        }
        const attemptId = token("attempt"),
          fence = task.fence + 1,
          now = Date.now();
        store.run(
          "INSERT INTO attempts(id,run_id,task_id,fence,state,started,deadline) VALUES(?,?,?,?,?,?,?)",
          attemptId,
          run.id,
          task.id,
          fence,
          "STARTING",
          now,
          now + lim.seconds * 1000,
        );
        store.run(
          "UPDATE tasks SET state=?,fence=?,attempt_id=? WHERE run_id=? AND id=?",
          "STARTING",
          fence,
          attemptId,
          run.id,
          task.id,
        );
        store.run(
          "INSERT OR REPLACE INTO meta VALUES(?,?)",
          "last_parent",
          run.parent,
        );
        store.run("UPDATE runs SET updated=? WHERE id=?", now, run.id);
        store.event(run.id, "attempt_admitted", task.id, {
          attempt_id: attemptId,
          fence,
        });
        return {
          run,
          task: { ...task, fence, attempt_id: attemptId },
          spec,
          attempt_id: attemptId,
          fence,
          checkpoint: checkpoint
            ? {
                attempt_id: checkpoint.attempt_id,
                ...JSON.parse(checkpoint.record),
              }
            : null,
        };
      }
      store.settleRun(run.id);
    }
    return null;
  });
}
