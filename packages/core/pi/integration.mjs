/** Existing Python integration queue bridge; no second Git merge algorithm. */
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { need, id, physical, stable, digest, token } from "./validation.mjs";
import { processIdentity, groupStopped } from "./execution.mjs";
const DIR = path.dirname(fileURLToPath(import.meta.url));
export function enqueueIntegration(store, p) {
  return store.tx(() => {
    const run = store.owned(p);
    need(
      run.approved &&
        !["ATTENTION", "BUDGET_OVERRUN", "CANCELLED", "CANCELLING"].includes(
          run.status,
        ),
      "run_not_integratable",
    );
    need(
      !store.get("SELECT value FROM meta WHERE key=?", "cancel:" + run.id),
      "run_cancelled",
    );
    const key = id(p.idempotency_key || "integration");
    let config = p.config;
    if (!config) {
      const file = physical(
        path.join(
          path.dirname(store.path),
          "reviews",
          run.id,
          "integration.json",
        ),
        { exists: true },
      );
      const info = fs.statSync(file);
      need(
        info.isFile() && info.size <= 131072 && !(info.mode & 0o077),
        "invalid_integration_config",
      );
      config = JSON.parse(fs.readFileSync(file, "utf8"));
    }
    need(
      config &&
        typeof config === "object" &&
        Array.isArray(config.items) &&
        config.items.length > 0 &&
        config.items.length <= 100,
      "invalid_integration_config",
    );
    need(
      config.gate_registry && Array.isArray(config.required_gates),
      "missing_integration_gates",
    );
    physical(config.python || "/usr/bin/python3", { exists: true });
    need(
      Number.isSafeInteger(config.seconds ?? 900) &&
        (config.seconds ?? 900) > 0 &&
        (config.seconds ?? 900) <= 3600,
      "invalid_integration_timeout",
    );
    need(
      /^[a-f0-9]{40}([a-f0-9]{24})?$/.test(config.base_commit),
      "invalid_base_commit",
    );
    if (p.task_id)
      need(
        config.items.length === 1 && config.items[0].task_id === p.task_id,
        "integration_scope_mismatch",
      );
    const items = config.items.map((item) => {
      const task = store.task({ ...p, task_id: item.task_id }).task;
      need(task.state === "SUBMITTED" && task.result, "task_not_submitted");
      const result = JSON.parse(task.result);
      need(
        result.source_base === config.base_commit && result.source_commit,
        "candidate_base_mismatch",
      );
      return {
        ...item,
        item_id: id(item.task_id),
        owner: task.agent_id,
        source_fence: task.fence,
        source_commit: result.source_commit,
        task_receipt_sha256: item.receipt_sha256 || item.task_receipt_sha256,
      };
    });
    for (const attempt of store.all(
      "SELECT workspace,artifact_dir FROM attempts WHERE run_id=?",
      run.id,
    )) {
      for (const file of [
        ...items.map((i) => i.receipt_file),
        ...Object.values(config.gate_registry).flatMap((g) =>
          Object.keys(g.pins || {}),
        ),
      ]) {
        const checked = physical(file, { exists: true });
        for (const owned of [attempt.workspace, attempt.artifact_dir].filter(
          Boolean,
        ))
          need(
            checked !== owned && !checked.startsWith(owned + path.sep),
            "verifier_owned_by_builder",
          );
      }
    }
    const operation = run.id + ":" + key,
      hash = digest({ ...config, items }),
      old = store.get(
        "SELECT * FROM integration_operations WHERE id=?",
        operation,
      );
    if (old) {
      need(
        JSON.parse(old.payload).hash === hash,
        "integration_idempotency_conflict",
      );
      return { status: old.status, operation_id: operation, run_id: run.id };
    }
    const workspace = path.join(
      path.dirname(store.path),
      "integration-workspaces",
      run.id,
      token("composition"),
    );
    const queue = path.join(
      path.dirname(store.path),
      "integration-state",
      run.id,
      digest(operation).slice(0, 20),
      "queue.sqlite",
    );
    const payload = {
      ...config,
      items,
      run_id: run.id,
      parent: JSON.parse(run.parent),
      repository: JSON.parse(run.parent).repository,
      branch: "codex/pi-" + digest(operation).slice(0, 20),
      workspace,
      queue_path: queue,
      state_path: store.path,
      node: process.execPath,
      supervisor: path.join(DIR, "supervisor.mjs"),
      hash,
    };
    store.run(
      "INSERT INTO integration_operations VALUES(?,?,?,?,?)",
      operation,
      run.id,
      "QUEUED",
      stable(payload),
      Date.now(),
    );
    store.event(run.id, "integration_queued", null, {
      operation_id: operation,
    });
    store.settleRun(run.id);
    return {
      status: "QUEUED",
      operation_id: operation,
      run_id: run.id,
      acceptance: "NOT_RUN",
    };
  });
}
export class IntegrationScheduler {
  constructor(store) {
    this.store = store;
    this.children = new Map();
  }
  recover() {
    this.store.tx(() => {
      for (const row of this.store.all(
        "SELECT * FROM integration_operations WHERE status IN ('STARTING','RUNNING','CANCELLING')",
      )) {
        this.store.run(
          "UPDATE integration_operations SET status=? WHERE id=?",
          "UNKNOWN",
          row.id,
        );
        this.store.event(row.run_id, "integration_unknown", null, {
          operation_id: row.id,
        });
        this.store.settleRun(row.run_id);
      }
    });
  }
  tick() {
    this.cancel();
    const row = this.store.tx(() => {
      if (
        this.store.get(
          "SELECT count(*) n FROM integration_operations WHERE status IN ('STARTING','RUNNING','CANCELLING','UNKNOWN')",
        ).n >= 1
      )
        return null;
      const row = this.store.get(
        "SELECT * FROM integration_operations WHERE status='QUEUED' ORDER BY created LIMIT 1",
      );
      if (row)
        this.store.run(
          "UPDATE integration_operations SET status=? WHERE id=?",
          "STARTING",
          row.id,
        );
      return row;
    });
    if (row)
      try {
        this.launch(row);
      } catch {
        this.store.tx(() => {
          this.store.run(
            "UPDATE integration_operations SET status=? WHERE id=?",
            "UNKNOWN",
            row.id,
          );
          this.store.settleRun(row.run_id);
        });
      }
  }
  launch(row) {
    const payload = JSON.parse(row.payload),
      python = payload.python || "/usr/bin/python3";
    let child,
      entry,
      raw = "",
      bytes = 0,
      reason = "exited";
    this.store.tx(() => {
      need(
        this.store.get(
          "SELECT status FROM integration_operations WHERE id=?",
          row.id,
        )?.status === "STARTING",
        "integration_fenced",
      );
      need(
        !this.store.get(
          "SELECT value FROM meta WHERE key=?",
          "cancel:" + row.run_id,
        ),
        "run_cancelled",
      );
      for (const item of payload.items) {
        const t = this.store.get(
          "SELECT state,fence FROM tasks WHERE run_id=? AND id=?",
          row.run_id,
          item.task_id,
        );
        need(
          t?.state === "SUBMITTED" && t.fence === item.source_fence,
          "candidate_fenced",
        );
      }
      child = spawn(
        python,
        [path.join(DIR, "bridge.py"), "--palarran-integration", row.id],
        {
          cwd: path.resolve(DIR, "../../.."),
          env: {
            PATH: "/usr/bin:/bin",
            HOME: path.dirname(this.store.path),
            LC_ALL: "C",
            PYTHONPATH: path.resolve(DIR, "../../.."),
          },
          detached: true,
          stdio: ["pipe", "pipe", "pipe"],
        },
      );
      entry = {
        child,
        row,
        identity: child.pid ? processIdentity(child.pid) : null,
        signalAt: null,
      };
      this.store.run(
        "UPDATE integration_operations SET status=?,payload=? WHERE id=?",
        "RUNNING",
        stable({
          ...payload,
          pid: child.pid ?? null,
          start_identity: entry.identity,
        }),
        row.id,
      );
      this.store.settleRun(row.run_id);
    });
    this.children.set(row.id, entry);
    const requestStop = () => {
      this.store.tx(() =>
        this.store.run(
          "UPDATE integration_operations SET status=? WHERE id=?",
          "CANCELLING",
          row.id,
        ),
      );
      this.cancel();
    };
    const timer = setTimeout(
      () => {
        reason = "deadline";
        requestStop();
      },
      Math.min(payload.seconds || 900, 3600) * 1000,
    );
    child.stdin.on("error", () => {});
    child.stdin.end(stable(payload) + "\n");
    child.stderr.on("data", () => {});
    child.stdout.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > 262144) {
        reason = "output_limit";
        requestStop();
      } else raw += chunk.toString("utf8");
    });
    child.on("error", () => {
      reason = "spawn_failed";
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      this.children.delete(row.id);
      let report,
        known = false,
        mapped = [];
      try {
        report = JSON.parse(raw);
        known =
          code === 0 &&
          reason === "exited" &&
          groupStopped(child.pid) &&
          ["ready_pr", "blocked", "failed"].includes(report.status);
        if (known && report.pr_ready) {
          need(
            report.status === "ready_pr" &&
              /^[a-f0-9]{40}([a-f0-9]{24})?$/.test(report.head),
            "invalid_integration_report",
          );
          need(
            Array.isArray(report.items) &&
              report.items.length === payload.items.length,
            "integration_items_mismatch",
          );
          const seen = new Set();
          mapped = report.items.map((item) => {
            const original = payload.items.find(
              (x) => x.item_id === item.item_id,
            );
            need(
              original &&
                !seen.has(item.item_id) &&
                item.source_commit === original.source_commit &&
                item.status === "integrated",
              "integration_items_mismatch",
            );
            seen.add(item.item_id);
            return original;
          });
        }
      } catch {
        known = false;
      }
      this.store.tx(() => {
        const current = this.store.get(
          "SELECT status FROM integration_operations WHERE id=?",
          row.id,
        ).status;
        const fenced =
          current !== "RUNNING" ||
          this.store.get(
            "SELECT value FROM meta WHERE key=?",
            "cancel:" + row.run_id,
          ) ||
          mapped.some((item) => {
            const t = this.store.get(
              "SELECT state,fence FROM tasks WHERE run_id=? AND id=?",
              row.run_id,
              item.task_id,
            );
            return t?.state !== "SUBMITTED" || t.fence !== item.source_fence;
          });
        const status =
          fenced || !known
            ? "UNKNOWN"
            : report.pr_ready
              ? "VERIFIED"
              : "BLOCKED";
        this.store.run(
          "UPDATE integration_operations SET status=?,payload=? WHERE id=?",
          status,
          stable({ ...payload, report: known ? report : null }),
          row.id,
        );
        if (status === "VERIFIED")
          for (const item of mapped)
            this.store.run(
              "UPDATE tasks SET integrated_commit=?,verification=? WHERE run_id=? AND id=?",
              report.head,
              "PASS",
              row.run_id,
              item.task_id,
            );
        this.store.event(row.run_id, "integration_finished", null, {
          operation_id: row.id,
          status,
        });
        this.store.settleRun(row.run_id);
      });
    });
  }
  cancel() {
    for (const entry of this.children.values()) {
      if (
        this.store.get(
          "SELECT status FROM integration_operations WHERE id=?",
          entry.row.id,
        ).status !== "CANCELLING"
      )
        continue;
      try {
        if (!entry.signalAt) {
          need(
            processIdentity(entry.child.pid) === entry.identity,
            "process_identity_mismatch",
          );
          process.kill(-entry.child.pid, "SIGTERM");
          entry.signalAt = Date.now();
        } else if (Date.now() - entry.signalAt > 5000) {
          need(
            processIdentity(entry.child.pid) === entry.identity,
            "process_identity_mismatch",
          );
          process.kill(-entry.child.pid, "SIGKILL");
        }
      } catch {}
    }
  }
  stop() {
    for (const entry of this.children.values())
      this.store.tx(() =>
        this.store.run(
          "UPDATE integration_operations SET status=? WHERE id=?",
          "CANCELLING",
          entry.row.id,
        ),
      );
    this.cancel();
  }
}
