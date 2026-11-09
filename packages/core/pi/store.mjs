/** Durable host-local source of admission, fencing and event truth. */
import fs from "node:fs";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";
import {
  need,
  physical,
  stable,
  digest,
  integer,
  parent,
  Fault,
} from "./validation.mjs";
export const ACTIVE = ["STARTING", "RUNNING", "CANCELLING"];
export class Store {
  constructor(filename) {
    this.path = physical(filename);
    const directory = path.dirname(this.path);
    fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
    need(!(fs.statSync(directory).mode & 0o077), "state_directory_not_private");
    if (fs.existsSync(this.path)) {
      const s = fs.lstatSync(this.path);
      need(
        s.isFile() && s.nlink === 1 && !(s.mode & 0o077),
        "unsafe_state_file",
      );
    }
    process.umask(0o077);
    this.db = new DatabaseSync(this.path);
    fs.chmodSync(this.path, 0o600);
    this.db
      .exec(`PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,parent TEXT NOT NULL,manifest_hash TEXT NOT NULL,limits TEXT NOT NULL,budget TEXT NOT NULL,status TEXT NOT NULL,approved INTEGER NOT NULL DEFAULT 0,created INTEGER NOT NULL,updated INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(run_id TEXT NOT NULL,id TEXT NOT NULL,spec TEXT NOT NULL,state TEXT NOT NULL,fence INTEGER NOT NULL DEFAULT 0,attempt_id TEXT,result TEXT,verification TEXT NOT NULL DEFAULT 'NOT_RUN',integrated_commit TEXT,agent_id TEXT NOT NULL,PRIMARY KEY(run_id,id),FOREIGN KEY(run_id) REFERENCES runs(id));
CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,task_id TEXT NOT NULL,fence INTEGER NOT NULL,state TEXT NOT NULL,pid INTEGER,start_identity TEXT,workspace TEXT,artifact_dir TEXT,started INTEGER NOT NULL,deadline INTEGER NOT NULL,stopped INTEGER NOT NULL DEFAULT 0,result_hash TEXT);
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,type TEXT NOT NULL,task_id TEXT,data TEXT NOT NULL,created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS commands(scope TEXT NOT NULL,key TEXT NOT NULL,hash TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(scope,key));
CREATE TABLE IF NOT EXISTS agent_checkpoints(agent_id TEXT PRIMARY KEY,attempt_id TEXT NOT NULL,record TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,task_id TEXT NOT NULL,body TEXT NOT NULL,created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,task_id TEXT NOT NULL,attempt_id TEXT NOT NULL,fence INTEGER NOT NULL,hash TEXT NOT NULL,state TEXT NOT NULL,stream_active INTEGER NOT NULL,tokens_reserved INTEGER NOT NULL,cost_reserved INTEGER NOT NULL,tokens_used INTEGER NOT NULL DEFAULT 0,cost_used INTEGER NOT NULL DEFAULT 0,usage_hash TEXT,created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS supervisor(id INTEGER PRIMARY KEY CHECK(id=1),pid INTEGER NOT NULL,identity TEXT NOT NULL,lease_until INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS integration_operations(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,status TEXT NOT NULL,payload TEXT NOT NULL,created INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS phase_leases(id TEXT PRIMARY KEY,run_id TEXT NOT NULL,kind TEXT NOT NULL,state TEXT NOT NULL,created INTEGER NOT NULL);`);
    this.tx(() => {
      const row = this.get("SELECT value FROM meta WHERE key=?", "schema");
      need(!row || row.value === "1", "unsupported_schema");
      this.run("INSERT OR IGNORE INTO meta VALUES(?,?)", "schema", "1");
    });
  }
  run(sql, ...args) {
    return this.db.prepare(sql).run(...args);
  }
  get(sql, ...args) {
    return this.db.prepare(sql).get(...args);
  }
  all(sql, ...args) {
    return this.db.prepare(sql).all(...args);
  }
  tx(fn) {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const v = fn();
      this.db.exec("COMMIT");
      return v;
    } catch (e) {
      this.db.exec("ROLLBACK");
      throw e;
    }
  }
  close() {
    this.db.close();
  }
  scope(payload) {
    return stable(parent(payload.parent));
  }
  owned(payload) {
    const run = this.get("SELECT * FROM runs WHERE id=?", payload.run_id);
    need(run, "unknown_run");
    need(run.parent === this.scope(payload), "scope_mismatch");
    return run;
  }
  task(payload) {
    const run = this.owned(payload);
    const task = this.get(
      "SELECT * FROM tasks WHERE run_id=? AND id=?",
      run.id,
      payload.task_id,
    );
    need(task, "unknown_task");
    return { run, task };
  }
  event(run, type, task = null, data = {}) {
    need(
      this.get("SELECT count(*) n FROM events").n < 50000,
      "event_storage_capacity",
    );
    this.run(
      "INSERT INTO events(run_id,type,task_id,data,created) VALUES(?,?,?,?,?)",
      run,
      type,
      task,
      stable(data),
      Date.now(),
    );
  }
  command(scope, key, payload, fn) {
    const hash = digest(payload),
      old = this.get(
        "SELECT * FROM commands WHERE scope=? AND key=?",
        scope,
        key,
      );
    if (old) {
      need(old.hash === hash, "idempotency_conflict");
      return JSON.parse(old.response);
    }
    need(
      this.get("SELECT count(*) n FROM commands").n < 10000,
      "command_storage_capacity",
    );
    const result = fn();
    this.run(
      "INSERT INTO commands VALUES(?,?,?,?)",
      scope,
      key,
      hash,
      stable(result),
    );
    return result;
  }
  budget(runId) {
    const row = this.get(
      `SELECT coalesce(sum(tokens_used),0) tokens_used,coalesce(sum(cost_used),0) cost_micros_used,coalesce(sum(tokens_reserved),0) tokens_reserved,coalesce(sum(cost_reserved),0) cost_micros_reserved,coalesce(sum(CASE WHEN state='UNKNOWN' THEN 1 ELSE 0 END),0) unknown_requests FROM requests WHERE run_id=?`,
      runId,
    );
    const b = JSON.parse(
      this.get("SELECT budget FROM runs WHERE id=?", runId).budget,
    );
    return { token_limit: b.tokens, cost_micros_limit: b.cost_micros, ...row };
  }
  settleRun(runId) {
    const run = this.get("SELECT * FROM runs WHERE id=?", runId),
      rows = this.all("SELECT state FROM tasks WHERE run_id=?", runId);
    let status = run.approved ? "RUNNING" : "DRAFT";
    if (rows.some((t) => t.state === "UNKNOWN")) status = "ATTENTION";
    else if (
      rows.every((t) =>
        ["SUCCEEDED", "SUBMITTED", "FAILED", "CANCELLED", "BLOCKED"].includes(
          t.state,
        ),
      )
    )
      status = rows.some((t) => ["FAILED", "BLOCKED"].includes(t.state))
        ? "FAILED"
        : rows.every((t) => t.state === "CANCELLED")
          ? "CANCELLED"
          : "COMPLETED";
    const operations = this.all(
      "SELECT status FROM integration_operations WHERE run_id=?",
      runId,
    );
    if (operations.some((o) => ["UNKNOWN", "BLOCKED"].includes(o.status)))
      status = "ATTENTION";
    else if (
      operations.some((o) =>
        ["QUEUED", "STARTING", "RUNNING", "CANCELLING"].includes(o.status),
      )
    )
      status = "INTEGRATING";
    if (this.get("SELECT value FROM meta WHERE key=?", "cancel:" + runId))
      status = rows.some((t) => t.state === "UNKNOWN")
        ? "ATTENTION"
        : rows.some((t) =>
              ["STARTING", "RUNNING", "CANCELLING"].includes(t.state),
            ) ||
            operations.some((o) =>
              ["STARTING", "RUNNING", "CANCELLING"].includes(o.status),
            )
          ? "CANCELLING"
          : "CANCELLED";
    const b = this.budget(runId);
    if (
      operations.some((o) => o.status === "UNKNOWN") ||
      b.unknown_requests > 0 ||
      this.get(
        "SELECT count(*) n FROM phase_leases WHERE run_id=? AND state='UNKNOWN'",
        runId,
      ).n
    )
      status = "ATTENTION";
    if (
      b.tokens_used > b.token_limit ||
      b.cost_micros_used > b.cost_micros_limit
    )
      status = "BUDGET_OVERRUN";
    this.run(
      "UPDATE runs SET status=?,updated=? WHERE id=?",
      status,
      Date.now(),
      runId,
    );
    return status;
  }
}
