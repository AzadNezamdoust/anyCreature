// Seat adapter: GPT Astra through `codex exec` (WORKFLOW-V3 §3, items 5-7 D2.2).
//
//   runSeat({prompt, images, workspace, timeoutMs, tag, mode, outFile?})
//     -> {answer, change, missingKeys, artifact, usage, seconds, model, effort,
//         sessionId, failureClass, transcript}
//
// Moved from pass.mjs `runCodex`. The Codex invocation is worker-codex.mjs's,
// verbatim in every part that matters (tools/BlindLoop/adapters/worker-codex.mjs:44-47, 107-131):
//  - `codex exec` HANGS if stdin is left open, and APPENDS piped stdin to the
//    argv prompt as a `<stdin>` block. So the long prompt goes through stdin
//    (spawnSync `input`) and the argv prompt stays one short sentence.
//  - The user's ~/.codex config starts three MCP servers per call and the call
//    never returns, so they are cleared with `-c mcp_servers={}`. The blunter
//    `--ignore-user-config` CANNOT be used here: it also discards the CODEX_HOME
//    trust state, and an untrusted workdir silently DOWNGRADES `-s
//    workspace-write` to read-only.
//  - When stdout is NOT a TTY the streams split: the session transcript
//    (header / user / codex / tokens used) goes to STDERR and STDOUT carries
//    only the final answer. Both are parsed; the transcript is the authority
//    for the header assertion.
//  - `-s workspace-write` is the least-dangerous sandbox that lets the seat edit
//    files under the project unattended (mode "agent"). Mode "text" runs
//    `-s read-only`: the seat returns the module in its reply and never touches the tree.
//
// failureClass: "transport" for a stream drop / "Unable to verify model access"
// (pass.mjs exits 2 and the seat is not counted), "timeout" for the wall clock,
// "contract" for a text-mode reply without a ```js fence, null otherwise.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

import { parseCodexTranscript, CODEX_MODEL, CODEX_EFFORT } from "../gen.mjs";
import { parseReply } from "../missing-keys.mjs";
import { codexBin } from "../codex-bin.mjs";

const CODEX_BIN = process.env.CODEX_BIN
  || codexBin();

/** What a dropped connection looks like in the transcript (run2-pass0b.log). */
export const TRANSPORT_RE = /stream disconnected before completion|Unable to verify model access|error sending request|Reconnecting\.\.\. 5\/5/i;

/**
 * @returns {null|"transport"|"timeout"}
 */
export function classifyCodexRun({ status, error, transcript, answer }) {
  if (error && error.code === "ETIMEDOUT") return "timeout";
  const text = String(transcript ?? "");
  if (status !== 0 && TRANSPORT_RE.test(text)) return "transport";
  if (status === 0 && !String(answer ?? "").trim() && TRANSPORT_RE.test(text)) return "transport";
  return null;
}

/**
 * The input / cached / output / reasoning split, read from the session's rollout
 * file (`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*-<sessionId>.jsonl`). The
 * transcript's `tokens used` scalar hides it (WORKFLOW-V3 §3). {} when absent.
 */
export function rolloutUsage(sessionId, home = process.env.CODEX_HOME || path.join(os.homedir(), ".codex")) {
  if (!sessionId) return {};
  const root = path.join(home, "sessions");
  const find = (dir, depth) => {
    if (!fs.existsSync(dir)) return null;
    const entries = fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => b.name.localeCompare(a.name));
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isFile() && e.name.includes(sessionId) && e.name.endsWith(".jsonl")) return full;
      if (e.isDirectory() && depth > 0) {
        const hit = find(full, depth - 1);
        if (hit) return hit;
      }
    }
    return null;
  };
  const file = find(root, 3);
  if (!file) return {};
  let total = null;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    if (!line.includes("token_count")) continue;
    try {
      const t = JSON.parse(line)?.payload?.info?.total_token_usage ?? JSON.parse(line)?.info?.total_token_usage;
      if (t) total = t;
    } catch { /* partial line */ }
  }
  if (!total) return {};
  return {
    input: total.input_tokens,
    cached: total.cached_input_tokens,
    output: total.output_tokens,
    reasoning: total.reasoning_output_tokens,
  };
}

const empty = (extra) => ({
  answer: "", change: null, missingKeys: [], artifact: null, usage: { total: 0 },
  seconds: 0, model: CODEX_MODEL, effort: CODEX_EFFORT, sessionId: null, failureClass: null, transcript: "", ...extra,
});

export async function runSeat({ prompt, images = [], workspace, timeoutMs, tag, mode = "text", outFile = null }) {
  const sandbox = mode === "agent" ? "workspace-write" : "read-only";
  const out = outFile ?? path.join(os.tmpdir(), `llmm-codex-${tag}-${process.pid}.md`);
  const args = [
    "exec",
    "-c", "mcp_servers={}",
    "--skip-git-repo-check",
    "-s", sandbox,
    "-C", workspace,
    "-m", CODEX_MODEL,
    "-c", `model_reasoning_effort="${CODEX_EFFORT}"`,
  ];
  for (const image of images) args.push("-i", image);
  args.push("-o", out, "Follow the instructions below.");

  const rel = (file) => path.relative(workspace, file).replace(/\\/g, "/");
  console.log(`[codex] ${tag} model=${CODEX_MODEL} effort=${CODEX_EFFORT} sandbox=${sandbox} mode=${mode} cwd=${workspace}`);
  console.log(`[codex] ${tag} images: ${images.map((i) => rel(i)).join(", ")}`);

  const started = Date.now();
  const result = spawnSync(CODEX_BIN, args, {
    cwd: workspace,
    input: prompt,            // stdin must be fed and closed, or codex exec hangs
    encoding: "utf8",
    timeout: timeoutMs,
    maxBuffer: 64 * 1024 * 1024,
  });
  const seconds = (Date.now() - started) / 1000;

  if (result.error && result.error.code !== "ETIMEDOUT") {
    throw new Error(`could not run "${CODEX_BIN}" — ${result.error.message}. Set CODEX_BIN to the codex executable.`);
  }

  const transcript = result.stderr ?? "";
  const stdoutText = result.stdout ?? "";
  const fileAnswer = fs.existsSync(out) ? fs.readFileSync(out, "utf8") : "";

  const early = classifyCodexRun({ status: result.status, error: result.error, transcript, answer: fileAnswer || stdoutText });
  if (early) {
    console.log(`[codex] ${tag} ${early.toUpperCase()} after ${seconds.toFixed(1)} s — not a seat`);
    return empty({ seconds, transcript, failureClass: early });
  }

  // The header is the only proof of WHICH model ran; a silent downgrade voids
  // the pass. `parseCodexTranscript` (gen.mjs:181-207) throws on a mismatch.
  const headerLines = transcript.split(/\r?\n/)
    .filter((line) => /^(model|reasoning effort|session id|sandbox|approval|workdir):/.test(line.trim()));
  for (const line of headerLines) console.log(`[codex] ${line.trim()}`);

  const headerSandbox = /^sandbox:\s*(.+)$/m.exec(transcript)?.[1]?.trim() ?? null;
  if (!new RegExp(`^${sandbox}`).test(headerSandbox ?? "")) {
    throw new Error(`codex header asserts sandbox="${headerSandbox}"; required "${sandbox}" (an untrusted workdir downgrades it silently)`);
  }

  const parsed = parseCodexTranscript(transcript, stdoutText);
  if (result.status !== 0) throw new Error(`codex exited ${result.status}\n${transcript.slice(-800)}`);

  const answer = fileAnswer.trim() ? fileAnswer.trim() : parsed.answer;
  const reply = parseReply(answer);
  const usage = { ...rolloutUsage(parsed.sessionId), total: parsed.tokensUsed };
  return {
    answer,
    change: reply.change,
    missingKeys: reply.missingKeys,
    artifact: mode === "text" ? reply.artifact : null,
    usage,
    seconds,
    model: parsed.model,
    effort: parsed.effort,
    sessionId: parsed.sessionId,
    failureClass: mode === "text" && !reply.artifact ? "contract" : null,
    transcript,
  };
}
