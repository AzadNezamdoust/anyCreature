// Seat adapter: GPT 5.6 Terra through the Codex CLI, BLIND, text mode only.
//
// Owner 2026-09-13: "if gemini can do it well and if gpt 5.6 terra also can do it well that
// is a pass on work flow". Terra is a TEST seat, so it must see nothing but this pass's
// artifacts:
//   - cwd is a private temp folder (no project AGENTS.md, no repo),
//   - --ephemeral (no session persisted), --ignore-user-config (no ~/.codex/config.toml),
//     --ignore-rules, -c mcp_servers={} (no tools), -s read-only (no writes),
//   - the prompt goes through stdin, images through -i, and the reply is the only output.
// The header assertion refuses any model other than the one requested.
//
// CHANNEL LIMIT (WF-BLIND-R2 C7, out/blind/diag/terra-P2.*): the same 30 kB prompt + 3 images went through in 129 s
// on a diagnostic call, and dropped twice in the blind run (77.6 s, 108 s) with codex exiting non-zero and NOTHING on
// stdout — no flag, image or stdin-size cause reproduces, so a drop is transient. The adapter records the exit status,
// signal and spawn error in the transcript; pass.mjs writes the transcript before it exits 2, and blind-test.mjs keeps
// one transcript per dropped attempt and records NO_RESULT instead of archiving a pass folder.
//
//   LLMM_TERRA_MODEL   model id (default gpt-5.6-terra)
//   LLMM_TERRA_EFFORT  reasoning effort (default high)
//   CODEX_BIN          codex executable
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

import { parseReply } from "../missing-keys.mjs";
import { codexBin } from "../codex-bin.mjs";

export const TERRA_DEFAULT_MODEL = "gpt-5.6-terra";
const DEFAULT_BIN = codexBin();

/** The blind argv, exported so a test can pin it without spawning. */
export function terraArgs({ dir, model, effort, images }) {
  const args = [
    "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
    "-c", "mcp_servers={}", "--skip-git-repo-check", "-s", "read-only", "-C", dir,
    "-m", model, "-c", `model_reasoning_effort="${effort}"`,
  ];
  for (const img of images) args.push("-i", img);
  args.push("Follow the instructions below.");
  return args;
}

const field = (text, name) => new RegExp(`^${name}:\\s*(.+)$`, "m").exec(text)?.[1]?.trim() ?? null;

export async function runSeat({ prompt, images = [], timeoutMs = 15 * 60 * 1000, tag = "seat", mode = "text", env = process.env } = {}) {
  const model = env.LLMM_TERRA_MODEL || TERRA_DEFAULT_MODEL;
  const effort = env.LLMM_TERRA_EFFORT || "high";
  const base = { answer: "", change: null, missingKeys: [], artifact: null, usage: { total: null }, seconds: 0, model, effort, sessionId: null, transcript: "" };
  if (mode !== "text") {
    return { ...base, failureClass: "contract", transcript: `terra seat supports --seat-mode text only (got ${mode})` };
  }

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `llmm-terra-${String(tag).replace(/[^\w-]/g, "_")}-`));
  const copied = images.map((src, i) => {
    const dest = path.join(dir, `image${i + 1}${path.extname(src) || ".png"}`);
    fs.copyFileSync(src, dest);
    return dest;
  });
  const args = terraArgs({ dir, model, effort, images: copied });
  console.log(`[terra] ${tag} model=${model} effort=${effort} mode=text dir=${dir} images=${copied.length} (blind)`);

  const t0 = Date.now();
  const run = spawnSync(env.CODEX_BIN || DEFAULT_BIN, args, {
    cwd: dir, input: String(prompt ?? ""), encoding: "utf8", timeout: timeoutMs, maxBuffer: 64 << 20, env,
  });
  const seconds = Math.round((Date.now() - t0) / 100) / 10;
  const stderr = String(run.stderr ?? "");
  const answer = String(run.stdout ?? "").trim();
  const exitLine = `---EXIT--- status=${run.status} signal=${run.signal ?? "none"} error=${run.error ? (run.error.code ?? run.error.message) : "none"} seconds=${seconds} promptBytes=${Buffer.byteLength(String(prompt ?? ""), "utf8")} images=${copied.length}`;
  const transcript = `${stderr}\n---STDOUT---\n${run.stdout ?? ""}\n${exitLine}\n`;

  if (run.error && /ETIMEDOUT/.test(String(run.error.code ?? run.error.message))) return { ...base, seconds, transcript, failureClass: "timeout" };
  if (/Unable to verify model access|stream disconnected|Reconnecting\.\.\./.test(stderr) && !answer) return { ...base, seconds, transcript, failureClass: "transport" };
  if (run.error || (run.status !== 0 && !answer)) return { ...base, seconds, transcript, failureClass: "transport" };

  const headerModel = field(stderr, "model");
  if (headerModel && headerModel !== model) {
    throw new Error(`terra seat: header says model="${headerModel}", required "${model}" (no fallback model is acceptable)`);
  }
  const lines = stderr.split(/\r?\n/);
  const at = lines.findLastIndex((l) => l.trim() === "tokens used");
  const total = at === -1 ? null : Number(String(lines[at + 1] ?? "").replace(/[^0-9]/g, "")) || null;

  const reply = parseReply(answer);
  return {
    ...base,
    answer,
    change: reply.change,
    missingKeys: reply.missingKeys,
    artifact: reply.artifact,
    usage: { total },
    seconds,
    sessionId: field(stderr, "session id"),
    transcript,
    failureClass: reply.artifact ? null : "contract",
  };
}
