/** Private JSON operator interface; --plan is handled before any state I/O. */
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Store } from "./store.mjs";
import { handle, snapshot } from "./control.mjs";
import { Scheduler, cancelProcesses } from "./execution.mjs";
import { need, Fault, integer, stable } from "./validation.mjs";
export async function dispatch(store, request) {
  need(
    request && request.version === 1 && typeof request.command === "string",
    "invalid_request",
  );
  const { command, payload: p = {} } = request;
  if (command === "tick") {
    const s = new Scheduler(store);
    const approved = store.get(
      "SELECT count(*) n FROM runs WHERE approved=1 AND status='RUNNING'",
    ).n;
    if (!approved) return { status: "TICKED", started: 0 };
    return { status: "START_REQUESTED", started: 0 };
  }
  if (command === "recover") {
    store.owned(p);
    const s = new Scheduler(store);
    need(s.lease(), "supervisor_busy");
    s.recover();
    store.tx(() =>
      store.run("DELETE FROM supervisor WHERE identity=?", s.identity),
    );
    return { status: "RECOVERED", ...snapshot(store, p) };
  }
  if (command === "integrate") {
    const { enqueueIntegration } = await import("./integration.mjs");
    return enqueueIntegration(store, p);
  }
  const result = handle(store, command, p);
  if (command === "cancel") {
    await cancelProcesses(store, p);
    return {
      ...result,
      status:
        store.owned(p).status === "CANCELLED" ? "CANCELLED" : result.status,
    };
  }
  if (command === "wait" && result.events.length === 0) {
    const deadline = Date.now() + integer(p.seconds ?? 1, 30) * 1000;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 100));
      const next = handle(store, "events", p);
      if (
        next.events.length ||
        ["COMPLETED", "FAILED", "CANCELLED", "ATTENTION"].includes(
          next.run_status,
        )
      )
        return next;
    }
    return handle(store, "events", p);
  }
  return result;
}
async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--plan")) {
    console.log(
      JSON.stringify({
        status: "PLANNED",
        writes: 0,
        network: false,
        model_calls: 0,
      }),
    );
    return;
  }
  const mode = args[0],
    i = args.indexOf("--state");
  need(
    ["rpc", "serve"].includes(mode) && i >= 0 && args[i + 1],
    "invalid_arguments",
  );
  const store = new Store(args[i + 1]);
  if (mode === "serve") {
    const { IntegrationScheduler } = await import("./integration.mjs");
    const integrations = new IntegrationScheduler(store);
    const scheduler = new Scheduler(store, { integrations });
    const stop = () => {
      scheduler.stopping = true;
      for (const { a } of scheduler.children.values())
        try {
          handle(store, "cancel", {
            parent: JSON.parse(a.run.parent),
            run_id: a.run.id,
            task_id: a.task.id,
          });
        } catch {}
    };
    process.once("SIGTERM", stop);
    process.once("SIGINT", stop);
    try {
      await scheduler.serve();
    } finally {
      store.close();
    }
    return;
  }
  let raw = "";
  for await (const chunk of process.stdin) {
    raw += chunk;
    need(Buffer.byteLength(raw) <= 262144, "input_limit");
  }
  let req;
  try {
    req = JSON.parse(raw);
  } catch {
    throw new Fault("invalid_json");
  }
  const result = await dispatch(store, req);
  store.close();
  if (
    req.command === "start" ||
    req.command === "integrate" ||
    (req.command === "tick" && result.status === "START_REQUESTED")
  ) {
    const child = spawn(
      process.execPath,
      [fileURLToPath(import.meta.url), "serve", "--state", args[i + 1]],
      {
        detached: true,
        stdio: "ignore",
        env: { ...process.env, NODE_NO_WARNINGS: "1" },
      },
    );
    child.unref();
  }
  console.log(stable(result));
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  main().catch((e) => {
    console.log(
      JSON.stringify({
        status: "REJECTED",
        code: e instanceof Fault ? e.code : "supervisor_unavailable",
        field: e instanceof Fault ? e.field : null,
        hint: "Check reviewed scope, runtime compatibility and private state; reconcile unknown outcomes before retrying.",
      }),
    );
    process.exitCode = 2;
  });
}
