/** Bounded one-shot client. Supervisor owns durable state and authorization. */
import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const CREDENTIAL_NAMES = new Set(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]);
const MUTATING = new Set([
  "spawn",
  "send",
  "follow_up",
  "cancel",
  "approve",
  "start",
  "recover",
  "integrate",
  "tick",
]);
const DEFAULT_SUPERVISOR = fileURLToPath(
  new URL("../supervisor.mjs", import.meta.url),
);
function absolute(value) {
  return (
    typeof value === "string" &&
    path.isAbsolute(value) &&
    !value.split(path.sep).includes("..") &&
    !/[\x00-\x1f\x7f]/u.test(value)
  );
}
function rejected(command, code) {
  return {
    status: MUTATING.has(command) ? "UNKNOWN" : "REJECTED",
    code,
    hint: "Inspect the scoped run before retrying; no automatic replay was performed.",
  };
}
export function createRpcClient(options = {}) {
  const supervisorPath = options.supervisorPath ?? DEFAULT_SUPERVISOR;
  const statePath =
    options.statePath ??
    process.env.PALARRAN_PI_STATE ??
    path.join(os.homedir(), ".palarran/pi/state.sqlite");
  const timeoutMs = options.timeoutMs ?? 8000;
  const outputLimit = options.outputLimit ?? 262144;
  const credentialNames =
    options.credentialEnv ??
    (process.env.PALARRAN_PI_CREDENTIAL_ENV ?? "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  const validCredentials =
    Array.isArray(credentialNames) &&
    credentialNames.length <= 2 &&
    new Set(credentialNames).size === credentialNames.length &&
    credentialNames.every((x) => CREDENTIAL_NAMES.has(x));
  return async function rpc(command, payload = {}, call = {}) {
    if (!validCredentials)
      return {
        status: "REJECTED",
        code: "invalid_credential_selection",
        hint: "Select only reviewed provider credential names in operator configuration.",
      };
    if (!absolute(supervisorPath) || !absolute(statePath))
      return {
        status: "REJECTED",
        code: "unsafe_operator_path",
        hint: "Use absolute operator-owned runtime and state paths.",
      };
    let input;
    try {
      input = JSON.stringify({ version: 1, command, payload });
    } catch {
      return {
        status: "REJECTED",
        code: "invalid_request",
        hint: "Provide bounded serializable command data.",
      };
    }
    if (Buffer.byteLength(input) > 131072)
      return {
        status: "REJECTED",
        code: "request_size_limit",
        hint: "Split the task batch or shorten the explicit request.",
      };
    if (call.signal?.aborted) return rejected(command, "supervisor_aborted");
    const seconds =
      command === "wait" && Number.isFinite(payload.seconds)
        ? Math.max(0, Math.min(30, payload.seconds))
        : 0;
    return await new Promise((resolve) => {
      let child,
        finished = false,
        total = 0,
        chunks = [];
      const env = {
        PATH: process.env.PATH ?? "/usr/bin:/bin",
        HOME: os.homedir(),
        LANG: "C.UTF-8",
        NODE_NO_WARNINGS: "1",
      };
      for (const name of credentialNames) {
        const value = process.env[name];
        if (
          typeof value === "string" &&
          value.length > 0 &&
          value.length <= 16384
        )
          env[name] = value;
      }
      const finish = (value) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        call.signal?.removeEventListener("abort", abort);
        resolve(value);
      };
      const abort = () => {
        child?.kill("SIGKILL");
        finish(rejected(command, "supervisor_aborted"));
      };
      const timer = setTimeout(
        () => {
          child?.kill("SIGKILL");
          finish(rejected(command, "supervisor_timeout"));
        },
        timeoutMs + seconds * 1000,
      );
      try {
        child = spawn(
          process.execPath,
          [supervisorPath, "rpc", "--state", statePath],
          {
            cwd: path.dirname(supervisorPath),
            env,
            stdio: ["pipe", "pipe", "ignore"],
            windowsHide: true,
          },
        );
        call.signal?.addEventListener("abort", abort, { once: true });
        child.stdout.on("data", (part) => {
          if (finished) return;
          total += part.length;
          if (total > outputLimit) {
            child.kill("SIGKILL");
            chunks = [];
            finish(rejected(command, "supervisor_output_limit"));
            return;
          }
          chunks.push(part);
        });
        child.on("error", () =>
          finish(rejected(command, "supervisor_unavailable")),
        );
        child.stdin.on("error", () => {});
        child.on("close", (code) => {
          if (finished) return;
          try {
            const value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            if (
              !value ||
              typeof value !== "object" ||
              Array.isArray(value) ||
              typeof value.status !== "string"
            )
              throw new Error();
            if (
              code !== 0 &&
              ![
                "REJECTED",
                "UNKNOWN",
                "CONFLICT",
                "BLOCKED",
                "ATTENTION",
              ].includes(value.status)
            )
              throw new Error();
            finish(value);
          } catch {
            finish(rejected(command, "invalid_supervisor_response"));
          }
        });
        child.stdin.end(input + "\n");
        if (call.signal?.aborted) abort();
      } catch {
        finish(rejected(command, "supervisor_unavailable"));
      }
    });
  };
}
