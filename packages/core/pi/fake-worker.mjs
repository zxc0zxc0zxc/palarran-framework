/** Offline supervisor fixture. Never imports an SDK or opens a network socket. */
import fs from "node:fs";
import path from "node:path";
import { physical, need, ownedFile } from "./validation.mjs";
let raw = "";
for await (const chunk of process.stdin) {
  raw += chunk;
  need(Buffer.byteLength(raw) <= 262144, "input_limit");
}
const c = JSON.parse(raw),
  p = c.profile;
await new Promise((r) => setTimeout(r, Math.min(p.delay_ms || 0, 30000)));
if (p.behavior === "fail") process.exit(1);
if (p.behavior === "hang") {
  setInterval(() => {}, 1000);
  await new Promise(() => {});
}
if (c.mode === "write" && p.writes) {
  for (const [name, body] of Object.entries(p.writes)) {
    ownedFile(name);
    need(c.allowed_files.includes(name), "unowned_file");
    const file = physical(path.join(c.workspace, name));
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, String(body));
  }
}
console.log(
  JSON.stringify({
    type: "result",
    run_id: c.run_id,
    task_id: c.task_id,
    attempt_id: c.attempt_id,
    fence: c.fence,
    result: {
      status: "COMPLETED",
      summary: p.summary || "Offline fixture completed.",
      findings: [],
      evidence: [],
      artifacts: [],
      blockers: [],
      acceptance: "NOT_RUN",
    },
  }),
);
