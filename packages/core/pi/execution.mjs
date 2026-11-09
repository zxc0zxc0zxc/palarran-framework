/** Owned process groups and workspaces; no model tools or shell interpolation. */
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  need,
  physical,
  stable,
  digest,
  token,
  GLOBAL_LIMITS,
} from "./validation.mjs";
import { claim } from "./control.mjs";
import { buildTaskContext, validateCheckpoint } from "./context.mjs";
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const env = {
  PATH: "/usr/bin:/bin",
  LC_ALL: "C",
  GIT_CONFIG_NOSYSTEM: "1",
  GIT_CONFIG_GLOBAL: "/dev/null",
  GIT_TERMINAL_PROMPT: "0",
  GIT_OPTIONAL_LOCKS: "0",
};
export function git(repo, ...args) {
  const r = spawnSync(
    "/usr/bin/git",
    [
      "--no-replace-objects",
      "--literal-pathspecs",
      "-c",
      "core.hooksPath=/dev/null",
      "-c",
      "core.fsmonitor=false",
      "-c",
      "commit.gpgsign=false",
      "-c",
      "user.name=Palarran Worker",
      "-c",
      "user.email=palarran@localhost",
      "-C",
      repo,
      ...args,
    ],
    { env, encoding: "utf8", timeout: 15000, maxBuffer: 1048576 },
  );
  need(r.status === 0, "git_operation_failed");
  return r.stdout.trim();
}
export function validateCandidate(repo, base, allowed) {
  need(git(repo, "rev-parse", "HEAD") === base, "candidate_head_changed");
  const changed = new Set(
    [
      ...git(repo, "diff", "--name-only", "-z", base, "--").split("\0"),
      ...git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(
        "\0",
      ),
    ].filter(Boolean),
  );
  need(
    changed.size > 0 && [...changed].every((f) => allowed.includes(f)),
    "unowned_code_change",
  );
  for (const file of changed) {
    const target = physical(path.join(repo, file));
    if (fs.existsSync(target))
      need(
        fs.lstatSync(target).isFile() && !fs.lstatSync(target).isSymbolicLink(),
        "unsafe_candidate_file",
      );
  }
  return [...changed];
}
export function groupStopped(pgid) {
  if (!Number.isSafeInteger(pgid) || pgid <= 0) return false;
  const r = spawnSync("/bin/ps", ["-axo", "pgid=,stat="], {
    env,
    encoding: "utf8",
    timeout: 2000,
    maxBuffer: 1048576,
  });
  if (r.status !== 0) return false;
  return !r.stdout.split("\n").some((line) => {
    const fields = line.trim().split(/\s+/);
    return Number(fields[0]) === pgid && !fields[1]?.startsWith("Z");
  });
}
export function processIdentity(pid) {
  const r = spawnSync(
    "/bin/ps",
    ["-p", String(pid), "-o", "lstart=", "-o", "command="],
    { env, encoding: "utf8", timeout: 2000, maxBuffer: 8192 },
  );
  return r.status === 0 ? r.stdout.trim() : null;
}
function signalOwned(attempt, signal) {
  if (!attempt.pid || !attempt.start_identity) return false;
  if (groupStopped(attempt.pid)) return true;
  const current = processIdentity(attempt.pid);
  if (!current) return false;
  need(
    current === attempt.start_identity && current.includes(attempt.id),
    "process_identity_mismatch",
  );
  try {
    process.kill(-attempt.pid, signal);
  } catch (e) {
    if (e.code !== "ESRCH") throw e;
  }
  return !processIdentity(attempt.pid);
}
export function prepareWorkspace(store, admitted) {
  const { run, spec, attempt_id } = admitted,
    root = path.dirname(store.path),
    artifacts = path.join(root, "artifacts", run.id, attempt_id),
    workspace = path.join(root, "workspaces", run.id, attempt_id);
  fs.mkdirSync(artifacts, { recursive: true, mode: 0o700 });
  let cwd = spec.repository,
    base = spec.base_commit;
  const integrated = spec.depends_on
    .filter((d) => d.condition === "integrated")
    .map(
      (d) =>
        store.get(
          "SELECT integrated_commit FROM tasks WHERE run_id=? AND id=?",
          run.id,
          d.task_id,
        )?.integrated_commit,
    );
  if (integrated.length) {
    need(integrated.every(Boolean), "integration_dependency_missing");
    base = integrated[0];
    for (const commit of integrated.slice(1)) {
      if (git(spec.repository, "merge-base", base, commit) === base)
        base = commit;
      else
        need(
          git(spec.repository, "merge-base", commit, base) === commit,
          "incompatible_integrated_dependencies",
        );
    }
  }
  const isGit = spawnSync(
    "/usr/bin/git",
    [
      "-c",
      "core.hooksPath=/dev/null",
      "-c",
      "core.fsmonitor=false",
      "-C",
      spec.repository,
      "rev-parse",
      "--show-toplevel",
    ],
    { env, encoding: "utf8", timeout: 5000, maxBuffer: 8192 },
  );
  if (isGit.status === 0) {
    need(
      physical(isGit.stdout.trim()) === spec.repository,
      "repository_root_required",
    );
    const filters = spawnSync(
      "/usr/bin/git",
      [
        "-C",
        spec.repository,
        "config",
        "--local",
        "--get-regexp",
        "^filter\\..*\\.(smudge|process|required)$",
      ],
      { env, encoding: "utf8", timeout: 5000, maxBuffer: 8192 },
    );
    need(filters.status === 1, "repository_filters_require_review");
    base = base || git(spec.repository, "rev-parse", "HEAD");
    need(
      git(spec.repository, "rev-parse", base + "^{commit}") === base,
      "base_commit_mismatch",
    );
    fs.mkdirSync(path.dirname(workspace), { recursive: true, mode: 0o700 });
    git(spec.repository, "worktree", "add", "--detach", workspace, base);
    cwd = workspace;
  } else
    need(
      spec.mode === "read" && spec.profile.kind === "fake",
      "git_snapshot_required",
    );
  store.tx(() =>
    store.run(
      "UPDATE attempts SET workspace=?,artifact_dir=? WHERE id=?",
      cwd,
      artifacts,
      attempt_id,
    ),
  );
  return { workspace: cwd, artifact_dir: artifacts, base_commit: base };
}
export function finishAttempt(
  store,
  admitted,
  result,
  { stopped = true, reason = "exited" } = {},
) {
  return store.tx(() => {
    const a = store.get(
        "SELECT * FROM attempts WHERE id=?",
        admitted.attempt_id,
      ),
      task = store.get(
        "SELECT * FROM tasks WHERE run_id=? AND id=?",
        a.run_id,
        a.task_id,
      );
    if (a.result_hash) {
      need(a.result_hash === digest(result ?? {}), "result_conflict");
      return;
    }
    let state = "UNKNOWN";
    if (stopped) {
      state =
        task.state === "CANCELLING" || a.state === "CANCELLING"
          ? "CANCELLED"
          : reason !== "exited"
            ? "FAILED"
            : result?.status === "COMPLETED"
              ? "SUCCEEDED"
              : result?.status === "INCONCLUSIVE"
                ? "SUBMITTED"
                : "FAILED";
    }
    const same = task.fence === a.fence && task.attempt_id === a.id;
    const cancellation =
      (task.state === "CANCELLING" || a.state === "CANCELLING") &&
      task.attempt_id === a.id;
    if (!same && !cancellation) state = "UNKNOWN";
    store.run(
      "UPDATE attempts SET state=?,stopped=?,result_hash=? WHERE id=?",
      state,
      stopped ? 1 : 0,
      digest(result ?? {}),
      a.id,
    );
    if (same || cancellation) {
      store.run(
        "UPDATE tasks SET state=?,result=? WHERE run_id=? AND id=?",
        state,
        result ? stable(result) : null,
        a.run_id,
        a.task_id,
      );
      if (
        same &&
        stopped &&
        ["SUCCEEDED", "SUBMITTED"].includes(state) &&
        result?.session_checkpoint
      ) {
        const checked = validateCheckpoint(
            a.artifact_dir,
            result.session_checkpoint,
          ),
          old = store.get(
            "SELECT attempt_id FROM agent_checkpoints WHERE agent_id=?",
            task.agent_id,
          );
        need(
          (old?.attempt_id ?? null) ===
            (admitted.checkpoint?.attempt_id ?? null),
          "checkpoint_cas_conflict",
        );
        store.run(
          "INSERT OR REPLACE INTO agent_checkpoints VALUES(?,?,?)",
          task.agent_id,
          a.id,
          stable({
            ...checked,
            summary: String(result.summary || "").slice(0, 1000),
            verification: "NOT_RUN",
          }),
        );
      }
      store.event(a.run_id, "attempt_finished", a.task_id, {
        attempt_id: a.id,
        status: state,
        stopped,
        reason,
      });
    }
    // Process exit proves no active stream in that process, not zero spend.
    if (stopped)
      store.run(
        "UPDATE requests SET stream_active=0,state='UNKNOWN' WHERE attempt_id=? AND stream_active=1",
        a.id,
      );
    store.settleRun(a.run_id);
  });
}
export class Scheduler {
  constructor(store, { integrations = null } = {}) {
    this.store = store;
    this.integrations = integrations;
    this.children = new Map();
    this.stopping = false;
    this.identity = token("supervisor");
  }
  lease() {
    return this.store.tx(() => {
      const old = this.store.get("SELECT * FROM supervisor WHERE id=1");
      if (
        old &&
        old.identity !== this.identity &&
        (old.lease_until > Date.now() || processIdentity(old.pid))
      )
        return false;
      this.store.run(
        "INSERT OR REPLACE INTO supervisor VALUES(1,?,?,?)",
        process.pid,
        this.identity,
        Date.now() + 5000,
      );
      return true;
    });
  }
  recover() {
    return this.store.tx(() => {
      for (const a of this.store.all(
        "SELECT * FROM attempts WHERE state IN ('STARTING','RUNNING','CANCELLING')",
      )) {
        if (this.children.has(a.id)) continue;
        this.store.run(
          "UPDATE attempts SET state=? WHERE id=?",
          "UNKNOWN",
          a.id,
        );
        this.store.run(
          "UPDATE tasks SET state=?,fence=fence+1 WHERE run_id=? AND id=?",
          "UNKNOWN",
          a.run_id,
          a.task_id,
        );
        this.store.event(a.run_id, "attempt_outcome_unknown", a.task_id, {
          attempt_id: a.id,
        });
        this.store.settleRun(a.run_id);
      }
    });
  }
  async tick() {
    if (!this.lease()) return { started: 0, status: "SUPERVISOR_BUSY" };
    this.stopCancelled();
    let started = 0;
    while (!this.stopping) {
      const a = claim(this.store);
      if (!a) break;
      started++;
      try {
        this.launch(a);
      } catch {
        if (!this.children.has(a.attempt_id))
          try {
            finishAttempt(this.store, a, null, {
              stopped: false,
              reason: "launch_configuration_unknown",
            });
          } catch {}
      }
    }
    return { status: "TICKED", started };
  }
  launch(a) {
    let dirs;
    try {
      dirs = prepareWorkspace(this.store, a);
    } catch {
      finishAttempt(this.store, a, null, { reason: "workspace_rejected" });
      return;
    }
    const packet = buildTaskContext({
      workspace: dirs.workspace,
      files: a.spec.files,
      goal: a.spec.goal,
      prior: a.checkpoint?.summary
        ? {
            summary: a.checkpoint.summary,
            verification: a.checkpoint.verification,
          }
        : null,
      dependencies: a.spec.depends_on.map((d) => {
        const row = this.store.get(
          "SELECT id,state,verification,integrated_commit,result FROM tasks WHERE run_id=? AND id=?",
          a.run.id,
          d.task_id,
        );
        return {
          task_id: row.id,
          status: row.state,
          verification: row.verification,
          integrated_commit: row.integrated_commit,
          summary: row.result
            ? JSON.parse(row.result).summary?.slice(0, 1000)
            : "",
        };
      }),
    });
    const profile = a.spec.profile;
    const worker =
      profile.kind === "fake"
        ? path.join(ROOT, "fake-worker.mjs")
        : path.join(ROOT, "worker", "worker.mjs");
    if (!fs.existsSync(worker)) {
      finishAttempt(this.store, a, null, { reason: "worker_unavailable" });
      return;
    }
    const config = {
      version: 1,
      state_path: this.store.path,
      run_id: a.run.id,
      task_id: a.task.id,
      attempt_id: a.attempt_id,
      fence: a.fence,
      parent: JSON.parse(a.run.parent),
      ...dirs,
      prompt: packet.prompt,
      context: packet.context,
      session_checkpoint: a.checkpoint
        ? { path: a.checkpoint.path, sha256: a.checkpoint.sha256 }
        : undefined,
      context_sources: packet.context_sources,
      acceptance: a.spec.acceptance,
      profile,
      mode: a.spec.mode,
      allowed_files: a.spec.files,
      limits: JSON.parse(a.run.limits),
    };
    const environment = {
      PATH: process.env.PATH || "/usr/bin:/bin",
      HOME: path.join(dirs.artifact_dir, "home"),
      NODE_NO_WARNINGS: "1",
      LANG: "C.UTF-8",
    };
    if (profile.kind === "sdk") {
      need(
        typeof profile.api_key_env === "string" &&
          /^[A-Z][A-Z0-9_]{0,127}$/.test(profile.api_key_env),
        "invalid_credential_reference",
      );
      if (process.env[profile.api_key_env])
        environment[profile.api_key_env] = process.env[profile.api_key_env];
    }
    let child;
    try {
      this.store.tx(() => {
        const owner = this.store.get("SELECT * FROM supervisor WHERE id=1");
        need(
          owner?.identity === this.identity && owner.pid === process.pid,
          "supervisor_fenced",
        );
        const current = this.store.get(
          "SELECT * FROM tasks WHERE run_id=? AND id=?",
          a.run.id,
          a.task.id,
        );
        need(
          current.state === "STARTING" &&
            current.fence === a.fence &&
            current.attempt_id === a.attempt_id,
          "launch_fenced",
        );
        child = spawn(
          process.execPath,
          [worker, "--palarran-attempt", a.attempt_id],
          {
            cwd: dirs.workspace,
            env: environment,
            detached: true,
            stdio: ["pipe", "pipe", "pipe"],
          },
        );
        if (child.pid) {
          const identity = processIdentity(child.pid);
          this.store.run(
            "UPDATE attempts SET state=?,pid=?,start_identity=? WHERE id=?",
            "RUNNING",
            child.pid,
            identity,
            a.attempt_id,
          );
          this.store.run(
            "UPDATE tasks SET state='RUNNING' WHERE run_id=? AND id=? AND fence=?",
            a.run.id,
            a.task.id,
            a.fence,
          );
        }
      });
    } catch {
      if (!child)
        finishAttempt(this.store, a, null, { reason: "spawn_failed" });
      else {
        try {
          process.kill(-child.pid, "SIGKILL");
        } catch {}
      }
      return;
    }
    let result = null,
      raw = "",
      bytes = 0,
      reason = "exited",
      finished = false;
    this.children.set(a.attempt_id, { child, a });
    const timer = setTimeout(
      () => {
        reason = "deadline";
        try {
          signalOwned(
            this.store.get("SELECT * FROM attempts WHERE id=?", a.attempt_id),
            "SIGKILL",
          );
        } catch {
          reason = "termination_unknown";
        }
      },
      JSON.parse(a.run.limits).seconds * 1000,
    );
    child.stdout.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes > 1048576) {
        reason = "output_limit";
        try {
          signalOwned(
            this.store.get("SELECT * FROM attempts WHERE id=?", a.attempt_id),
            "SIGKILL",
          );
        } catch {}
        return;
      }
      raw += chunk.toString("utf8");
      let index;
      while ((index = raw.indexOf("\n")) >= 0) {
        const line = raw.slice(0, index);
        raw = raw.slice(index + 1);
        try {
          const e = JSON.parse(line);
          if (e.type === "result") {
            need(
              e.run_id === a.run.id &&
                e.task_id === a.task.id &&
                e.attempt_id === a.attempt_id &&
                e.fence === a.fence,
              "result_identity_mismatch",
            );
            need(
              Buffer.byteLength(stable(e.result)) <= 32768,
              "result_too_large",
            );
            result = e.result;
          }
        } catch {
          reason = "invalid_worker_metadata";
        }
      }
    });
    child.stderr.on("data", () => {});
    child.on("error", () => {
      reason = "spawn_failed";
    });
    child.stdin.on("error", () => {});
    child.stdin.end(JSON.stringify(config) + "\n");
    child.on("close", async (code, signal) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      let stopped = groupStopped(child.pid);
      if (!stopped) {
        reason = "unexpected_descendant";
        try {
          process.kill(-child.pid, "SIGKILL");
        } catch {}
        for (let n = 0; n < 40 && !stopped; n++) {
          await new Promise((r) => setTimeout(r, 25));
          stopped = groupStopped(child.pid);
        }
      }
      this.children.delete(a.attempt_id);
      if (code !== 0 && reason === "exited") reason = "worker_failed";
      try {
        if (
          a.spec.mode === "write" &&
          reason === "exited" &&
          result?.status === "COMPLETED"
        ) {
          validateCandidate(dirs.workspace, dirs.base_commit, a.spec.files);
          git(dirs.workspace, "add", "--", ...a.spec.files);
          git(dirs.workspace, "commit", "-m", "Implement " + a.task.id);
          result = {
            ...result,
            status: "INCONCLUSIVE",
            source_commit: git(dirs.workspace, "rev-parse", "HEAD"),
            source_base: dirs.base_commit,
            blockers: [
              ...(result.blockers || []),
              "Independent verification and integration required.",
            ],
          };
        }
        finishAttempt(this.store, a, result, { stopped, reason });
      } catch {
        finishAttempt(this.store, a, null, {
          stopped: true,
          reason: "candidate_rejected",
        });
      }
    });
  }
  stopCancelled() {
    for (const a of this.store.all(
      "SELECT a.* FROM attempts a JOIN tasks t ON t.run_id=a.run_id AND t.id=a.task_id WHERE t.state='CANCELLING' AND a.state IN ('STARTING','RUNNING','CANCELLING')",
    )) {
      try {
        const stopped = signalOwned(a, "SIGTERM");
        if (stopped && !this.children.has(a.id))
          finishAttempt(this.store, { attempt_id: a.id }, null, {
            stopped: true,
            reason: "cancelled",
          });
      } catch {
        this.store.tx(() => {
          this.store.run(
            "UPDATE tasks SET state=? WHERE run_id=? AND id=?",
            "UNKNOWN",
            a.run_id,
            a.task_id,
          );
          this.store.settleRun(a.run_id);
        });
      }
    }
  }
  async serve() {
    need(this.lease(), "supervisor_busy");
    this.recover();
    this.integrations?.recover();
    while (!this.stopping) {
      const tick = await this.tick();
      if (tick.status === "SUPERVISOR_BUSY") {
        this.stopping = true;
        break;
      }
      this.integrations?.tick();
      await new Promise((r) => setTimeout(r, 100));
    }
    this.integrations?.stop();
    while (this.children.size || this.integrations?.children.size) {
      this.stopCancelled();
      this.integrations?.cancel();
      await new Promise((r) => setTimeout(r, 50));
    }
    this.store.tx(() =>
      this.store.run("DELETE FROM supervisor WHERE identity=?", this.identity),
    );
  }
}
export async function cancelProcesses(store, p) {
  const tasks = p.task_id
    ? [store.task(p).task]
    : store.all("SELECT * FROM tasks WHERE run_id=?", store.owned(p).id);
  for (const task of tasks) {
    if (task.state !== "CANCELLING") continue;
    const a = store.get("SELECT * FROM attempts WHERE id=?", task.attempt_id);
    try {
      signalOwned(a, "SIGTERM");
      let stopped = false;
      for (let i = 0; i < 20; i++) {
        if (groupStopped(a.pid)) {
          stopped = true;
          break;
        }
        await new Promise((r) => setTimeout(r, 50));
      }
      if (!stopped) {
        signalOwned(a, "SIGKILL");
        for (let i = 0; i < 20; i++) {
          if (groupStopped(a.pid)) {
            stopped = true;
            break;
          }
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      if (stopped) {
        const fresh = store.get("SELECT * FROM attempts WHERE id=?", a.id);
        if (!fresh.result_hash)
          finishAttempt(store, { attempt_id: a.id }, null, {
            stopped: true,
            reason: "cancelled",
          });
      } else
        store.tx(() => {
          store.run(
            "UPDATE tasks SET state=? WHERE run_id=? AND id=?",
            "UNKNOWN",
            a.run_id,
            a.task_id,
          );
          store.settleRun(a.run_id);
        });
    } catch {
      store.tx(() => {
        store.run(
          "UPDATE tasks SET state=? WHERE run_id=? AND id=?",
          "UNKNOWN",
          a.run_id,
          a.task_id,
        );
        store.settleRun(a.run_id);
      });
    }
  }
}
