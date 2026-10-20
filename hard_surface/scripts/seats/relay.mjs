// Seat adapter: a relay folder for any chat UI (Claude, Gemini, ...).
//
// Writes `relay/pending/<tag>.prompt.md` and copies the images next to it, then
// waits for a human (or another tool) to drop the chat's reply into
// `relay/done/<tag>.answer.md`. Optional `relay/done/<tag>.usage.json`
// (`{model, effort, input, cached, output, reasoning, total}`) is read when present;
// otherwise usage is total 0 — the relay never estimates a token count.
//
// Env: LLMM_RELAY_DIR (default <workspace>/relay), LLMM_RELAY_POLL_MS (default 2000).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

import { parseReply } from "../missing-keys.mjs";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function runSeat({ prompt, images = [], workspace, timeoutMs, tag, mode = "text", pollMs }) {
  const dir = process.env.LLMM_RELAY_DIR || path.join(workspace, "relay");
  const pending = path.join(dir, "pending");
  const done = path.join(dir, "done");
  fs.mkdirSync(pending, { recursive: true });
  fs.mkdirSync(done, { recursive: true });
  const poll = Number(pollMs ?? process.env.LLMM_RELAY_POLL_MS ?? 2000);

  const answerFile = path.join(done, `${tag}.answer.md`);
  if (fs.existsSync(answerFile)) fs.renameSync(answerFile, path.join(done, `${tag}.answer.stale-${Date.now()}.md`));

  const copied = images.map((image, i) => {
    const name = `${tag}.image${i + 1}${path.extname(image)}`;
    fs.copyFileSync(image, path.join(pending, name));
    return name;
  });
  const header = [
    `<!-- relay seat ${tag} · mode ${mode} · attach, in order: ${copied.join(", ") || "no images"} -->`,
    `<!-- save the chat's reply, verbatim, as ${path.relative(workspace, answerFile).replace(/\\/g, "/")} -->`,
    "",
  ].join("\n");
  const promptFile = path.join(pending, `${tag}.prompt.md`);
  fs.writeFileSync(promptFile, header + prompt);
  console.log(`[relay] ${tag} waiting for ${answerFile} (prompt ${promptFile})`);

  const started = Date.now();
  const base = { answer: "", change: null, missingKeys: [], artifact: null, usage: { total: 0 }, model: "relay", effort: null, transcript: "" };
  while (!fs.existsSync(answerFile) || fs.statSync(answerFile).size === 0) {
    if (Date.now() - started > timeoutMs) {
      return { ...base, seconds: (Date.now() - started) / 1000, failureClass: "timeout" };
    }
    await sleep(poll);
  }
  await sleep(poll);                                  // let a writer finish
  const answer = fs.readFileSync(answerFile, "utf8").trim();
  const seconds = (Date.now() - started) / 1000;

  const usageFile = path.join(done, `${tag}.usage.json`);
  const u = fs.existsSync(usageFile) ? JSON.parse(fs.readFileSync(usageFile, "utf8")) : {};
  const usage = { total: Number(u.total ?? 0) };
  for (const k of ["input", "cached", "output", "reasoning"]) if (Number.isFinite(u[k])) usage[k] = u[k];

  const reply = parseReply(answer);
  return {
    ...base,
    answer,
    change: reply.change,
    missingKeys: reply.missingKeys,
    artifact: mode === "text" ? reply.artifact : null,
    usage,
    seconds,
    model: u.model ?? "relay",
    effort: u.effort ?? null,
    failureClass: mode === "text" && !reply.artifact ? "contract" : null,
    transcript: `(relay) prompt ${promptFile}\n(relay) answer ${answerFile}\n\n${answer}`,
  };
}
