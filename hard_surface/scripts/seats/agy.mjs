// Seat adapter: any model Antigravity serves (`agy --print`), default Gemini 3.8 Flash High.
//
// Owner 2026-09-13: "lets use gemini 3.8 high for tests." This is the third author
// family behind the same text-only contract as codex/relay/fake:
//   in : { prompt, images, timeoutMs, tag, mode }
//   out: { answer, change, missingKeys, artifact, usage, seconds, model, effort,
//          sessionId, transcript, failureClass: null|"transport"|"timeout"|"contract" }
//
// Text mode only. The prompt is too long for a Windows command line, so it is written
// to prompt.md in a private temp folder together with the images; the one-line
// instruction on argv points the agy agent at that folder and nothing else. The
// working directory is that temp folder, never the repo, so the seat cannot touch
// project files even though agy's print mode auto-approves its own tool calls.
//
//   LLMM_AGY_MODEL   model id (default gemini-3.8-flash-high; `agy models` lists them)
//   LLMM_AGY_EFFORT  low|medium|high (default high)
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

import { parseReply } from "../missing-keys.mjs";

export const AGY_DEFAULT_MODEL = "gemini-3.8-flash-high";

/** node's spawn does no PATHEXT lookup on Windows; find the real executable. */
function resolveAgy(env) {
  const dirs = String(env.PATH ?? env.Path ?? "").split(path.delimiter).filter(Boolean);
  const exts = process.platform === "win32" ? [".exe", ".cmd", ".bat", ""] : [""];
  for (const dir of dirs) {
    for (const ext of exts) {
      const candidate = path.join(dir, `agy${ext}`);
      if (fs.existsSync(candidate)) return candidate;
    }
  }
  return "agy";
}

export function buildInstruction(dir, imageNames) {
  const imgs = imageNames.length
    ? ` Look at the images ${imageNames.join(", ")} in the same folder: ${imageNames[0]} is the TARGET (style and model, not a trace)`
      + (imageNames.length > 1 ? "; the others are renders of the current module." : ".")
    : "";
  return `Read the file prompt.md in ${dir}.${imgs} Then reply exactly as the contract at the end of prompt.md says: `
    + "the COMPLETE module in one ```js fence, then one line starting CHANGE:, then optionally one line starting MISSING KEY:. "
    + "Do not create, edit, move or delete any file and do not run any command; your reply text is the only output.";
}

export async function runSeat({ prompt, images = [], timeoutMs = 15 * 60 * 1000, tag = "seat", mode = "text", env = process.env } = {}) {
  const model = env.LLMM_AGY_MODEL || AGY_DEFAULT_MODEL;
  const effort = env.LLMM_AGY_EFFORT || "high";
  const base = { answer: "", change: null, missingKeys: [], artifact: null, usage: { total: null }, seconds: 0, model, effort, sessionId: null, transcript: "" };
  if (mode !== "text") {
    return { ...base, failureClass: "contract", transcript: `agy seat supports --seat-mode text only (got ${mode})` };
  }

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `llmm-agy-${String(tag).replace(/[^\w-]/g, "_")}-`));
  fs.writeFileSync(path.join(dir, "prompt.md"), String(prompt ?? ""));
  const names = [];
  images.forEach((src, i) => {
    const name = `image${i + 1}${path.extname(src) || ".png"}`;
    fs.copyFileSync(src, path.join(dir, name));
    names.push(name);
  });

  const printTimeout = `${Math.max(1, Math.floor(timeoutMs / 60000) - 1)}m`;
  // BLIND (owner 2026-09-13): every call is a NEW Antigravity project with no --continue / --conversation,
  // so nothing from an earlier request (conversation, project memory, workspace index) reaches the model.
  const args = ["--print", buildInstruction(dir, names), "--new-project", "--add-dir", dir, "--dangerously-skip-permissions",
    "--model", model, "--effort", effort, "--output-format", "text", "--print-timeout", printTimeout];
  console.log(`[agy] ${tag} model=${model} effort=${effort} mode=text dir=${dir} images=${names.length}`);

  const t0 = Date.now();
  const run = spawnSync(resolveAgy(env), args, { cwd: dir, encoding: "utf8", timeout: timeoutMs, maxBuffer: 64 << 20, env });
  const seconds = Math.round((Date.now() - t0) / 100) / 10;
  const answer = String(run.stdout ?? "").trim();
  const transcript = `agy ${args.map((a) => (a.includes(" ") ? JSON.stringify(a) : a)).join(" ")}\n--- stdout ---\n${run.stdout ?? ""}\n--- stderr ---\n${run.stderr ?? ""}`;

  if (run.error && /ETIMEDOUT/.test(String(run.error.code ?? run.error.message))) {
    return { ...base, seconds, transcript, failureClass: "timeout" };
  }
  if (run.error || (run.status !== 0 && !answer)) {
    return { ...base, seconds, transcript, failureClass: "transport" };
  }

  const reply = parseReply(answer);
  return {
    ...base,
    answer,
    change: reply.change,
    missingKeys: reply.missingKeys,
    artifact: reply.artifact,
    seconds,
    transcript,
    failureClass: reply.artifact ? null : "contract",
  };
}
