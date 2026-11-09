/** Bounded operator inputs; exceptions contain fixed codes only. */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
export class Fault extends Error {
  constructor(code, field = null) {
    super(code);
    this.code = code;
    this.field = field;
  }
}
export function need(condition, code = "invalid_request", field = null) {
  if (!condition) throw new Fault(code, field);
}
export function text(value, max = 4096) {
  need(
    typeof value === "string" &&
      value.length > 0 &&
      value.length <= max &&
      !/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(value),
    "invalid_text",
  );
  return value;
}
export function id(value) {
  need(
    typeof value === "string" &&
      /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$/.test(value),
    "invalid_identifier",
  );
  return value;
}
export function integer(value, max = Number.MAX_SAFE_INTEGER, min = 0) {
  need(
    Number.isSafeInteger(value) && value >= min && value <= max,
    "invalid_limit",
  );
  return value;
}
export function stable(value) {
  if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
  if (value && typeof value === "object")
    return (
      "{" +
      Object.keys(value)
        .sort()
        .map((k) => JSON.stringify(k) + ":" + stable(value[k]))
        .join(",") +
      "}"
    );
  return JSON.stringify(value);
}
export function digest(value) {
  return crypto
    .createHash("sha256")
    .update(typeof value === "string" ? value : stable(value))
    .digest("hex");
}
export function token(prefix) {
  return prefix + "-" + crypto.randomUUID();
}
export function physical(value, { exists = false } = {}) {
  text(value);
  need(
    path.isAbsolute(value) && !value.split(path.sep).includes(".."),
    "unsafe_path",
  );
  let result = path.normalize(value);
  if (process.platform === "darwin")
    for (const [a, b] of [
      ["/tmp", "/private/tmp"],
      ["/var", "/private/var"],
      ["/etc", "/private/etc"],
    ])
      if (result === a || result.startsWith(a + "/")) {
        if (fs.lstatSync(a).isSymbolicLink()) {
          need(fs.realpathSync(a) === b, "unsafe_path");
          result = b + result.slice(a.length);
        }
        break;
      }
  let current = path.parse(result).root;
  for (const part of result
    .slice(current.length)
    .split(path.sep)
    .filter(Boolean)) {
    current = path.join(current, part);
    if (
      fs.existsSync(current) ||
      (() => {
        try {
          fs.lstatSync(current);
          return true;
        } catch {
          return false;
        }
      })()
    )
      need(!fs.lstatSync(current).isSymbolicLink(), "unsafe_path");
  }
  if (exists) need(fs.existsSync(result), "missing_path");
  return result;
}
export function parent(value) {
  need(value && typeof value === "object", "missing_parent", "parent");
  return {
    session_id: id(value.session_id),
    repository: physical(value.repository, { exists: true }),
  };
}
export function ownedFile(value) {
  text(value, 256);
  need(
    !path.isAbsolute(value) &&
      value
        .split("/")
        .every(
          (p) =>
            /^[A-Za-z0-9_.-]+$/.test(p) && ![".", "..", ".git"].includes(p),
        ),
    "unsafe_owned_file",
  );
  return value;
}
export const GLOBAL_LIMITS = Object.freeze({
  workers: 16,
  model_requests: 8,
  writers: 4,
  heavy: 4,
  integration: 1,
  queue: 1000,
});
export function limits(value = {}) {
  need(
    value && typeof value === "object" && !Array.isArray(value),
    "invalid_limits",
  );
  const result = {
    workers: 16,
    model_requests: 8,
    writers: 4,
    heavy: 4,
    integration: 1,
    queue: 500,
    seconds: 900,
  };
  for (const [k, v] of Object.entries(value)) {
    need(k in result, "invalid_limits");
    result[k] = integer(
      v,
      k === "seconds" ? 86400 : k === "queue" ? 500 : GLOBAL_LIMITS[k],
      1,
    );
  }
  return result;
}
export function taskSpec(value, scope) {
  need(value && typeof value === "object", "invalid_task");
  const task = {
    task_id: id(value.task_id),
    goal: text(value.goal, 8192),
    acceptance: value.acceptance,
    mode: value.mode || "read",
    repository: physical(value.repository || scope.repository, {
      exists: true,
    }),
    depends_on: value.depends_on || [],
    files: value.files || [],
    profile: value.profile || { kind: "fake" },
  };
  need(task.repository === scope.repository, "repository_mismatch");
  need(["read", "write"].includes(task.mode), "invalid_mode");
  need(
    Array.isArray(task.acceptance) &&
      task.acceptance.length > 0 &&
      task.acceptance.length <= 32,
    "missing_acceptance",
  );
  task.acceptance.forEach((x) => text(x, 2048));
  need(
    Array.isArray(task.depends_on) && task.depends_on.length <= 100,
    "invalid_dependencies",
  );
  task.depends_on = task.depends_on.map((d) =>
    typeof d === "string"
      ? { task_id: id(d), condition: "artifact" }
      : { task_id: id(d.task_id), condition: d.condition },
  );
  need(
    task.depends_on.every((d) =>
      ["artifact", "verified", "integrated"].includes(d.condition),
    ),
    "invalid_dependency_condition",
  );
  need(Array.isArray(task.files) && task.files.length <= 128, "invalid_files");
  task.files = task.files.map(ownedFile);
  need(task.mode === "read" || task.files.length > 0, "missing_owned_files");
  need(
    task.profile && ["fake", "sdk"].includes(task.profile.kind),
    "invalid_profile",
  );
  need(Buffer.byteLength(stable(task.profile)) <= 16384, "profile_too_large");
  if (task.profile.kind === "sdk") {
    const p = task.profile;
    need(
      p.sdk_version === "1.0.0" && typeof p.sdk_path === "string",
      "unsupported_sdk",
    );
    physical(p.sdk_path, { exists: true });
    need(
      ["openai", "anthropic"].includes(p.provider) &&
        p.api ===
          (p.provider === "openai"
            ? "openai-completions"
            : "anthropic-messages"),
      "unsupported_provider",
    );
    text(p.model, 128);
    need(
      /^[A-Z][A-Z0-9_]{0,127}$/.test(p.api_key_env || ""),
      "invalid_credential_reference",
    );
    integer(p.max_output_tokens, 1e7, 1);
    integer(p.context_window, 1e9, 1);
    need(p.max_output_tokens <= p.context_window, "invalid_model_capability");
    need(p.pricing && typeof p.pricing === "object", "missing_pricing");
    integer(p.pricing.input_micros_per_million, 1e12);
    integer(p.pricing.output_micros_per_million, 1e12);
    if (p.base_url) {
      const u = new URL(p.base_url);
      need(
        u.protocol === "https:" &&
          !u.username &&
          !u.password &&
          !u.search &&
          !u.hash,
        "unsupported_transport",
      );
    }
  }
  if (value.base_commit !== undefined) {
    need(
      /^[a-f0-9]{40}([a-f0-9]{24})?$/.test(value.base_commit),
      "invalid_base_commit",
    );
    task.base_commit = value.base_commit;
  }
  if (task.mode === "write") need(task.base_commit, "missing_base_commit");
  return task;
}
export function checkDag(tasks) {
  const map = new Map(tasks.map((t) => [t.task_id, t]));
  need(map.size === tasks.length, "duplicate_task");
  const visiting = new Set(),
    done = new Set();
  function visit(t) {
    need(!visiting.has(t.task_id), "dependency_cycle");
    if (done.has(t.task_id)) return;
    visiting.add(t.task_id);
    for (const d of t.depends_on) {
      need(map.has(d.task_id), "missing_dependency");
      visit(map.get(d.task_id));
    }
    visiting.delete(t.task_id);
    done.add(t.task_id);
  }
  tasks.forEach(visit);
}
