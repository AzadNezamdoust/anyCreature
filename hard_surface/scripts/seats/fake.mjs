// Seat adapter for tests: no model, no network.
//
//   LLMM_FAKE_MODULE   file whose text is returned as the module (```js fence)
//   LLMM_FAKE_REPLY    file whose text is returned verbatim instead (e.g. no fence)
//   LLMM_FAKE_SCRIPT   JSON file: an array of replies served in call order (the last one repeats), WORKFLOW v4 V4-3 —
//                      each {reply: "<text>"} | {replyFile: "<path>"} | {module: "<path>"} | {echo: "READY"} (the
//                      prompt's READY CALLS fence returned as the insert block, as a seat pasting them would) |
//                      {failure: "transport" | "timeout"}
//   LLMM_FAKE_MISSING  "k1, k2" -> a `MISSING KEY:` line
//   LLMM_FAKE_FAILURE  "transport" | "timeout" -> that failureClass, empty answer
//   LLMM_FAKE_USAGE    JSON usage object, default {"total":0}
//
// In mode "agent" the module is also written to `modulePath`, as an agent seat would.
import fs from "node:fs";
import process from "node:process";

import { parseReply } from "../missing-keys.mjs";

/** call index per script file (in-process: the loop and its tests run the seat in one process) */
const served = new Map();

/** The reply text a script entry stands for, or {failure}. */
function scripted(file, prompt) {
  const list = JSON.parse(fs.readFileSync(file, "utf8"));
  const n = served.get(file) ?? 0;
  served.set(file, n + 1);
  const e = list[Math.min(n, list.length - 1)];
  if (e.failure) return { failure: e.failure };
  if (typeof e.reply === "string") return { answer: e.reply };
  if (e.replyFile) return { answer: fs.readFileSync(e.replyFile, "utf8") };
  if (e.module) {
    const module = fs.readFileSync(e.module, "utf8");
    return { answer: ["```js", module.replace(/\s+$/, ""), "```", "CHANGE: fake seat returned a scripted module"].join("\n"), module };
  }
  if (e.echo === "READY") {
    const m = /# READY CALLS[^\n]*\n+```js\n([\s\S]*?)```/.exec(String(prompt ?? ""));
    return { answer: m ? ["```js", m[1].replace(/\s+$/, ""), "```", "CHANGE: pasted the READY CALLS"].join("\n") : "CHANGE: no READY CALLS in the prompt" };
  }
  throw new Error(`fake seat: script entry ${n} of ${file} has no reply / replyFile / module / echo / failure`);
}

export async function runSeat({ prompt = "", mode = "text", modulePath = null, env = process.env } = {}) {
  const usage = env.LLMM_FAKE_USAGE ? JSON.parse(env.LLMM_FAKE_USAGE) : { total: 0 };
  const base = { answer: "", change: null, missingKeys: [], artifact: null, usage, seconds: 0, model: "fake", effort: null, sessionId: null, transcript: "(fake seat)" };
  if (env.LLMM_FAKE_FAILURE) return { ...base, failureClass: env.LLMM_FAKE_FAILURE };

  let answer;
  let module = null;
  if (env.LLMM_FAKE_SCRIPT) {
    const s = scripted(env.LLMM_FAKE_SCRIPT, prompt);
    if (s.failure) return { ...base, failureClass: s.failure };
    answer = s.answer;
    module = s.module ?? null;
  } else if (env.LLMM_FAKE_REPLY) {
    answer = fs.readFileSync(env.LLMM_FAKE_REPLY, "utf8");
  } else {
    if (!env.LLMM_FAKE_MODULE) throw new Error("fake seat: set LLMM_FAKE_MODULE, LLMM_FAKE_REPLY or LLMM_FAKE_SCRIPT");
    module = fs.readFileSync(env.LLMM_FAKE_MODULE, "utf8");
    answer = ["```js", module.replace(/\s+$/, ""), "```", "CHANGE: fake seat returned LLMM_FAKE_MODULE"].join("\n");
    if (env.LLMM_FAKE_MISSING) answer += `\nMISSING KEY: ${env.LLMM_FAKE_MISSING}`;
  }
  if (mode === "agent" && modulePath && module !== null) fs.writeFileSync(modulePath, module);

  const reply = parseReply(answer);
  return {
    ...base,
    answer,
    change: reply.change,
    missingKeys: reply.missingKeys,
    artifact: mode === "text" ? reply.artifact : null,
    failureClass: mode === "text" && !reply.artifact ? "contract" : null,
    transcript: `(fake seat)\n${answer}`,
  };
}
