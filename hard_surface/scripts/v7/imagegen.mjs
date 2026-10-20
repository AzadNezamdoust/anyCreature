#!/usr/bin/env node
// imagegen.mjs — ONE image generation through an agent CLI (the setup's turnaround step: research/v7/IMAGEGEN-AB.md,
// scripts/v7/turnaround.mjs). GPT and Gemini are used ONLY to generate the image: no judging, no editing, no measuring —
// every number and verdict is the caller's.
//
//   node scripts/v7/imagegen.mjs --gen gemini|gpt [--ref <png> ...] --prompt-file <txt> --out <png>   (no --ref: text to image, e.g. a concept)
//        [--aspect 1:1|4:3|3:4|16:9|9:16] [--name <label>] [--timeout <s>] [--work-root <dir>]
//
// gemini: Antigravity `agy --print` (agent gemini-3.8-flash-high, effort high, --output-format stream-json) run in a
//   CLEAN temp dir that holds only copies of the refs (the dir is --add-dir'ed and the cwd). The instruction: call
//   generate_image ONCE with ImagePaths = the refs and the prompt verbatim, copy the image it wrote into <temp>/out
//   unchanged, reply with the path only — do not list, read or search any files. generate_image writes a JPEG into the agy
//   brain folder (the transcript's media entry names it): that original is kept beside the output (<out>.orig.jpg) and
//   converted to the PNG --out with sharp (lossless from the decoded pixels; the agent's copy is only checked).
// gpt: Codex CLI `codex exec` (scripts/codex-bin.mjs; -c mcp_servers={} --ephemeral --skip-git-repo-check -s
//   workspace-write -C <temp>, -m gpt-6-astra, effort high, each ref attached with -i in order, the instruction on stdin,
//   stdin closed); the built-in image_gen writes $CODEX_HOME/generated_images/<session>/*.png — that original is --out.
// Both: a timeout per call (gemini 540 s, gpt 720 s; the process tree is killed), ONE retry only on a TRANSPORT failure
//   (timeout, non-zero exit, a non-SUCCESS result, a failed generate_image step — and no image) — never because of what the
//   image shows, never when the agent simply did not generate. A provenance JSON beside the output
//   (<out base>.provenance.json): generator, CLI + version, agent model, image model (C2PA; the agent is asked for the
//   path only), command (argv; the instruction verbatim + sha256), prompt sha256, ref sha256s, wall time, output and
//   original sha256, the agent's tool calls (generate_image count, refs passed, prompt verbatim, extra calls), every try.
// Exit 0 = an image was written, 1 = no image (the provenance still says why), 2 = usage.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { ROOT } from "../subject.mjs";
import { codexBin } from "../codex-bin.mjs";

export const GEN = Object.freeze({
  gemini: Object.freeze({ agent: "gemini-3.8-flash-high", effort: "high", timeoutS: 540, imageTool: "generate_image" }),
  gpt: Object.freeze({ agent: "gpt-6-astra", effort: "high", timeoutS: 720, imageTool: "image_gen" }),
});
/** Retries after a transport failure (fixed: the rule is ONE retry). */
export const RETRIES = 1;
export const ASPECTS = Object.freeze(["1:1", "4:3", "3:4", "16:9", "9:16"]);
const IMAGE_EXT = /\.(png|jpe?g|webp)$/i;

export const agyBin = (env = process.env) => env.AGY_BIN
  || path.join(env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"), "agy", "bin", process.platform === "win32" ? "agy.exe" : "agy");
const agyHome = (env = process.env) => env.AGY_HOME || path.join(os.homedir(), ".gemini", "antigravity-cli");
const codexHome = (env = process.env) => env.CODEX_HOME || path.join(os.homedir(), ".codex");

const sha256 = (buf) => crypto.createHash("sha256").update(buf).digest("hex");
const shaFile = (f) => sha256(fs.readFileSync(f));
/** A path as the Windows agents expect it (backslashes, absolute). */
export const winPath = (p) => (process.platform === "win32" ? path.resolve(p).replace(/\//g, "\\") : path.resolve(p));
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const samePath = (a, b) => { const n = (p) => path.resolve(String(p)).replace(/\\/g, "/").toLowerCase(); return n(a) === n(b); };
const isInside = (file, dir) => { const r = path.relative(dir, file); return !!r && !r.startsWith("..") && !path.isAbsolute(r); };
const readText = (f) => (f && fs.existsSync(f) ? fs.readFileSync(f, "utf8") : "");
/** Prompt comparison: exact, or equal after CRLF -> LF and trailing-space trimming per line. */
export function promptMatch(got, want) {
  if (typeof got !== "string") return false;
  if (got === want) return "exact";
  const norm = (s) => s.replace(/\r\n/g, "\n").split("\n").map((l) => l.trimEnd()).join("\n").trim();
  return norm(got) === norm(want) ? "whitespace" : false;
}
const aspectWords = (a) => { const [w, h] = a.split(":").map(Number); return w === h ? "square (1:1)" : w > h ? `landscape (${a})` : `portrait (${a})`; };

// ---------------------------------------------------------------------------------------------------------------------
// Instructions (pure)
// ---------------------------------------------------------------------------------------------------------------------

/** The agy instruction: ONE generate_image call with the refs + the prompt verbatim, one copy, the path as the reply. */
export function geminiInstruction({ refs = [], prompt, outDir, name, aspect = "1:1" }) {
  return [
    "Call the generate_image tool exactly ONCE, with these arguments:",
    ...(refs.length ? ["- ImagePaths: these image files, in this order:", ...refs.map((r) => `  ${r}`)] : ["- ImagePaths: none (no reference image: the image comes from the prompt alone)"]),
    `- ImageName: ${name}`,
    `- AspectRatio: ${aspect}`,
    "- Prompt: the text between the lines BEGIN PROMPT and END PROMPT below, verbatim: every line, nothing added, removed or reworded.",
    `Then copy the image file that generate_image wrote, unchanged (no conversion, no re-encoding, no resizing), into the folder ${outDir} with one copy command, and reply with the full path of that copy and nothing else.`,
    "Do not list, read, view or search any files or folders, do not run any other command, do not retry, edit or check the image, and do not call generate_image a second time.",
    "BEGIN PROMPT",
    prompt,
    "END PROMPT",
  ].join("\n");
}

/** The codex instruction (stdin): ONE image_gen call with the attached refs, saved to outPng, the path as the reply. */
export function gptInstruction({ refs = [], prompt, outPng, aspect = "1:1" }) {
  const n = refs.length;
  return [
    `Use your built-in image generation tool (image_gen) to create exactly one image and save it as the PNG file ${outPng} (the file must exist on disk when you finish).`,
    n === 0 ? "There is no reference image: generate the image from the prompt alone." : n === 1
      ? "The attached image is the reference image: give it to the image tool as its reference / input image."
      : `The ${n} attached images are the reference images, in this order: ${refs.map((r, i) => `image ${i + 1} = ${path.basename(r)}`).join(", ")}; give all of them, in this order, to the image tool as its reference / input images.`,
    `Image shape: ${aspectWords(aspect)}.`,
    "Make exactly one generation call; do not retry, edit, crop, resize or post-process the result; do not write code, analyse anything, or list, read or search any files.",
    "Prompt for the image: the text between the lines BEGIN PROMPT and END PROMPT below, verbatim.",
    "BEGIN PROMPT",
    prompt,
    "END PROMPT",
    "Reply with the saved path only.",
  ].join("\n");
}

// ---------------------------------------------------------------------------------------------------------------------
// Parsing the agents' output (pure)
// ---------------------------------------------------------------------------------------------------------------------

/** agy stream-json: conversation id, agent model, final response / status, tool steps (index, tool, states), errors. */
export function parseAgyStream(text) {
  const info = { conversationId: null, agentModel: null, response: null, status: null, toolSteps: [], errors: [], events: 0 };
  for (const line of String(text ?? "").split(/\r?\n/)) {
    if (!line.trim()) continue;
    let ev;
    try { ev = JSON.parse(line); } catch { continue; }
    info.events += 1;
    if (ev.event === "init") { info.agentModel = ev.init?.model ?? info.agentModel; info.conversationId ??= ev.conversation_id ?? null; }
    if (ev.event === "result") { info.response = ev.result?.response ?? null; info.status = ev.result?.status ?? null; info.conversationId ??= ev.result?.conversation_id ?? null; }
    if (ev.event === "error" || ev.error) info.errors.push(String(ev.error?.message ?? ev.error ?? ev.message ?? "error").slice(0, 300));
    const su = ev.step_update;
    if (!su) continue;
    info.conversationId ??= su.conversation_id ?? null;
    if (su.step_type !== "tool") continue;
    let s = info.toolSteps.find((t) => t.index === su.step_index);
    if (!s) { s = { index: su.step_index, tool: su.tool_name ?? su.tool_info?.name ?? null, states: [] }; info.toolSteps.push(s); }
    s.tool ??= su.tool_name ?? su.tool_info?.name ?? null;
    if (su.state && s.states[s.states.length - 1] !== su.state) s.states.push(su.state);
  }
  return info;
}

/** agy brain transcript_full.jsonl: every tool call {step, name, args} and every image media entry {step, mime, file}. */
export function parseAgyTranscript(text) {
  const out = { toolCalls: [], media: [] };
  for (const line of String(text ?? "").split(/\r?\n/)) {
    if (!line.trim()) continue;
    let j;
    try { j = JSON.parse(line); } catch { continue; }
    for (const t of j.tool_calls || []) out.toolCalls.push({ step: j.step_index ?? null, name: t.name, args: t.args || {} });
    for (const m of j.media || []) {
      if (!/^image\//.test(m.mime_type || "") || !m.uri) continue;
      out.media.push({ step: j.step_index ?? null, mime: m.mime_type, file: m.uri.startsWith("file:") ? fileURLToPath(m.uri) : m.uri });
    }
  }
  return out;
}

/** codex exec stderr header: model, reasoning effort, sandbox, session id. */
export function parseCodexHeader(stderr) {
  const f = (n) => new RegExp(`^${n}:\\s*(.+)$`, "m").exec(String(stderr ?? ""))?.[1]?.trim() ?? null;
  return { version: /^OpenAI Codex (v\S+)/m.exec(String(stderr ?? ""))?.[1] ?? null, model: f("model"), effort: f("reasoning effort"), sandbox: f("sandbox"), sessionId: f("session id") };
}

/**
 * One call's outcome -> {ok, failure: null | "transport" | "agent" | "spawn", reason}. An image = ok (never retried).
 * transport (retried once): timeout, killed / non-zero exit, a non-SUCCESS agy result, a failed generate_image step.
 * agent (not retried): exit 0 and no image — the agent did not generate. spawn: the CLI could not start.
 */
export function classifyCall({ images = 0, spawnError = null, timedOut = false, exitCode = 0, status = null, toolErrors = 0 }) {
  if (images > 0) return { ok: true, failure: null, reason: null };
  if (spawnError) return { ok: false, failure: "spawn", reason: String(spawnError) };
  if (timedOut) return { ok: false, failure: "transport", reason: "timeout" };
  if (exitCode === null) return { ok: false, failure: "transport", reason: "killed (no exit code)" };
  if (exitCode !== 0) return { ok: false, failure: "transport", reason: `exit ${exitCode}` };
  if (status && status !== "SUCCESS") return { ok: false, failure: "transport", reason: `result ${status}` };
  if (toolErrors > 0) return { ok: false, failure: "transport", reason: `${toolErrors} failed image-tool step(s)` };
  return { ok: false, failure: "agent", reason: "no image generated" };
}

// ---------------------------------------------------------------------------------------------------------------------
// C2PA (read-only byte scan of the manifest's CBOR text fields; the same reader as the A/B's finalize.mjs)
// ---------------------------------------------------------------------------------------------------------------------

function cborText(b, i) {
  const h = b[i];
  if (h >= 0x60 && h <= 0x77) return b.toString("utf8", i + 1, i + 1 + (h - 0x60));
  if (h === 0x78) return b.toString("utf8", i + 2, i + 2 + b[i + 1]);
  if (h === 0x79) return b.toString("utf8", i + 3, i + 3 + b.readUInt16BE(i + 1));
  return null;
}
export function c2paInfo(file) {
  if (!file || !fs.existsSync(file)) return null;
  const b = fs.readFileSync(file);
  const s = b.toString("latin1");
  if (!s.includes("c2pa")) return { present: false };
  const out = { present: true, claimGenerator: null, softwareAgent: null, actions: [], ingredientAssertions: 0 };
  let i = -1;
  while ((i = s.indexOf("c2pa.ingredient", i + 1)) >= 0) out.ingredientAssertions += 1;
  i = -1;
  while ((i = s.indexOf("description", i + 1)) >= 0) { const t = cborText(b, i + 11); if (t && !out.actions.includes(t)) out.actions.push(t); }
  const a = s.indexOf("softwareAgent");
  if (a >= 0) out.softwareAgent = { name: cborText(b, s.indexOf("name", a) + 4), version: cborText(b, s.indexOf("version", a) + 7) };
  const g = s.indexOf("claim_generator_info");
  if (g >= 0) out.claimGenerator = cborText(b, s.indexOf("name", g) + 4);
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// Running the CLIs
// ---------------------------------------------------------------------------------------------------------------------

const versionCache = new Map();
function cliVersion(bin, args) {
  const key = `${bin} ${args.join(" ")}`;
  if (!versionCache.has(key)) {
    const r = spawnSync(bin, args, { encoding: "utf8", windowsHide: true, timeout: 30000 });
    versionCache.set(key, ((r.stdout || "") + (r.stderr || "")).trim().split(/\r?\n/)[0] || null);
  }
  return versionCache.get(key);
}

function killTree(child) {
  if (process.platform === "win32" && child.pid) spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { windowsHide: true });
  else child.kill("SIGKILL");
}

function runProcess(bin, args, { cwd, stdin, timeoutMs, stdoutFile, stderrFile }) {
  return new Promise((resolve) => {
    const started = Date.now();
    let child;
    try { child = spawn(bin, args, { cwd, windowsHide: true, stdio: ["pipe", "pipe", "pipe"] }); } catch (e) {
      resolve({ exitCode: null, signal: null, spawnError: e.message, timedOut: false, seconds: 0 });
      return;
    }
    const out = fs.createWriteStream(stdoutFile); const err = fs.createWriteStream(stderrFile);
    child.stdout.pipe(out); child.stderr.pipe(err);
    let timedOut = false; let spawnError = null; let settled = false;
    const timer = setTimeout(() => { timedOut = true; killTree(child); }, timeoutMs);
    const done = (exitCode, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      let pending = 2;
      const fin = () => { pending -= 1; if (!pending) resolve({ exitCode, signal, spawnError, timedOut, seconds: (Date.now() - started) / 1000 }); };
      out.end(fin); err.end(fin);
    };
    child.on("error", (e) => { spawnError = e.message; if (!child.pid) done(null, null); });
    child.on("close", (code, signal) => done(code, signal));
    child.stdin.on("error", () => {});
    if (stdin != null) child.stdin.end(stdin); else child.stdin.end();
  });
}

const listImages = (dir) => (dir && fs.existsSync(dir)
  ? fs.readdirSync(dir).filter((f) => IMAGE_EXT.test(f)).map((f) => path.join(dir, f)).sort((a, b) => fs.statSync(a).mtimeMs - fs.statSync(b).mtimeMs)
  : []);

function toolCallSummary(prompt) {
  return (t) => {
    const a = { ...t.args };
    if (typeof a.Prompt === "string") { a.promptChars = a.Prompt.length; a.promptVerbatim = promptMatch(a.Prompt, prompt); delete a.Prompt; }
    if (typeof a.CommandLine === "string") a.CommandLine = a.CommandLine.slice(0, 300);
    return { step: t.step, name: t.name, args: a };
  };
}

async function callGemini(ctx, n) {
  const { work, refs, prompt, name, aspect, timeoutS } = ctx;
  const outDir = path.join(work, "out");
  fs.mkdirSync(outDir, { recursive: true });
  const instruction = geminiInstruction({ refs: refs.map(winPath), prompt, outDir: winPath(outDir), name, aspect });
  const bin = agyBin();
  const args = ["--print", instruction, "--add-dir", winPath(work), "--dangerously-skip-permissions", "--disable-slash-commands",
    "--effort", GEN.gemini.effort, "--output-format", "stream-json", "--print-timeout", `${Math.max(60, timeoutS - 30)}s`, "--model", GEN.gemini.agent];
  const stdoutFile = path.join(work, `stdout-${n}.jsonl`), stderrFile = path.join(work, `stderr-${n}.txt`);
  const startedAt = new Date().toISOString();
  const res = await runProcess(bin, args, { cwd: work, stdin: null, timeoutMs: timeoutS * 1000, stdoutFile, stderrFile });
  const stream = parseAgyStream(readText(stdoutFile));
  const brain = stream.conversationId ? path.join(agyHome(), "brain", stream.conversationId) : null;
  const tr = parseAgyTranscript(readText(brain && path.join(brain, ".system_generated", "logs", "transcript_full.jsonl")));
  let images = [...new Set(tr.media.filter((m) => brain && isInside(m.file, brain) && fs.existsSync(m.file)).map((m) => m.file))];
  if (!images.length && brain) images = listImages(brain);   // no transcript media entry: the brain folder's own images
  const gcalls = tr.toolCalls.filter((t) => t.name === "generate_image");
  const toolErrors = stream.toolSteps.filter((t) => t.tool === "generate_image" && t.states.length && t.states[t.states.length - 1] !== "DONE").length;
  const record = {
    try: n, startedAt, wallSeconds: +res.seconds.toFixed(1), exitCode: res.exitCode, signal: res.signal, timedOut: res.timedOut, spawnError: res.spawnError,
    conversationId: stream.conversationId, agentModel: stream.agentModel, resultStatus: stream.status, reply: stream.response, streamErrors: stream.errors,
    generateImageCalls: gcalls.length,
    referencesPassed: gcalls.length ? (gcalls[0].args.ImagePaths || []).length === refs.length && refs.every((r, i) => samePath(gcalls[0].args.ImagePaths[i], r)) : false,
    promptVerbatim: gcalls.length ? promptMatch(gcalls[0].args.Prompt, prompt) : false,
    aspectAsked: aspect, aspectUsed: gcalls[0]?.args?.AspectRatio ?? null,
    extraToolCalls: tr.toolCalls.filter((t) => t.name !== "generate_image").map((t) => t.name + (t.args.CommandLine ? `: ${String(t.args.CommandLine).slice(0, 160)}` : "")),
    toolCalls: tr.toolCalls.map(toolCallSummary(prompt)),
    images: images.map((f) => ({ file: f.replace(/\\/g, "/"), sha256: shaFile(f) })),
    agentCopies: listImages(outDir).map((f) => ({ file: f.replace(/\\/g, "/"), sha256: shaFile(f) })),
    logs: { stdout: stdoutFile.replace(/\\/g, "/"), stderr: stderrFile.replace(/\\/g, "/") },
  };
  Object.assign(record, classifyCall({ images: images.length, spawnError: res.spawnError, timedOut: res.timedOut, exitCode: res.exitCode, status: stream.status, toolErrors }));
  return { record, images, instruction, command: { bin, argv: args.map((a) => (a === instruction ? "<instruction>" : a)), cwd: work, stdin: null } };
}

async function callGpt(ctx, n) {
  const { work, refs, prompt, name, aspect, timeoutS } = ctx;
  const outDir = path.join(work, "out");
  fs.mkdirSync(outDir, { recursive: true });
  const outPng = path.join(outDir, `${name}.png`);
  const lastMessage = path.join(work, `last-message-${n}.txt`);
  const instruction = gptInstruction({ refs: refs.map(winPath), prompt, outPng: winPath(outPng), aspect });
  const bin = codexBin();
  const args = ["exec", "-c", "mcp_servers={}", "--ephemeral", "--skip-git-repo-check", "-s", "workspace-write", "-C", winPath(work),
    "-m", GEN.gpt.agent, "-c", `model_reasoning_effort="${GEN.gpt.effort}"`, ...refs.flatMap((r) => ["-i", winPath(r)]),
    "-o", winPath(lastMessage), "Follow the instructions below."];
  const stdoutFile = path.join(work, `stdout-${n}.txt`), stderrFile = path.join(work, `stderr-${n}.txt`);
  const startedAt = new Date().toISOString();
  const res = await runProcess(bin, args, { cwd: work, stdin: instruction, timeoutMs: timeoutS * 1000, stdoutFile, stderrFile });
  const header = parseCodexHeader(readText(stderrFile));
  const images = header.sessionId ? listImages(path.join(codexHome(), "generated_images", header.sessionId)) : [];
  const record = {
    try: n, startedAt, wallSeconds: +res.seconds.toFixed(1), exitCode: res.exitCode, signal: res.signal, timedOut: res.timedOut, spawnError: res.spawnError,
    sessionId: header.sessionId, agentModel: header.model, agentEffort: header.effort, sandbox: header.sandbox, cliBanner: header.version,
    reply: (readText(lastMessage) || readText(stdoutFile)).trim(),
    generatedImages: images.length,
    referencesAttached: refs.length,
    images: images.map((f) => ({ file: f.replace(/\\/g, "/"), sha256: shaFile(f) })),
    agentCopies: listImages(outDir).map((f) => ({ file: f.replace(/\\/g, "/"), sha256: shaFile(f) })),
    logs: { stdout: stdoutFile.replace(/\\/g, "/"), stderr: stderrFile.replace(/\\/g, "/") },
  };
  Object.assign(record, classifyCall({ images: images.length, spawnError: res.spawnError, timedOut: res.timedOut, exitCode: res.exitCode }));
  return { record, images, instruction, command: { bin, argv: args, cwd: work, stdin: "<instruction>" } };
}

/** The default generator (owner 2026-10-04: "stop trying to use gemini"). */
export const DEFAULT_GEN = "gpt";
/**
 * The owner's ruling of 2026-10-04 ("stop trying to use gemini"): the gemini path stays in the code but is REFUSED unless
 * the caller passes --allow-gemini (opts.allowGemini). -> the refusal text, or null when the generator may run.
 */
export function geminiRefusal(gen, allow = false) {
  if (gen !== "gemini" || allow) return null;
  return "--gen gemini is refused: owner ruling 2026-10-04 \"stop trying to use gemini\" — use --gen gpt (the default); --allow-gemini overrides for an explicit owner exception";
}

/**
 * Generate one image. opts: {gen: "gpt" (default) | "gemini" (needs allowGemini), refs: [png, ...], prompt (text) | promptFile, out (png), aspect,
 * name, timeoutS, workRoot, log}. Writes out (+ <out>.orig.<ext> when the generator's original is not a PNG) and
 * <out base>.provenance.json. -> {ok, out, provenance, provenanceFile}
 */
export async function generateImage(opts) {
  const gen = opts.gen ?? DEFAULT_GEN;
  if (!GEN[gen]) throw new Error(`imagegen: --gen ${gen} (gpt | gemini)`);
  const refused = geminiRefusal(gen, !!opts.allowGemini);
  if (refused) throw new Error(`imagegen: ${refused}`);
  const refsIn = (opts.refs || []).map((r) => path.resolve(r));
  for (const r of refsIn) if (!fs.existsSync(r)) throw new Error(`imagegen: no ref ${r}`);
  const prompt = opts.prompt ?? fs.readFileSync(opts.promptFile, "utf8");
  if (!prompt.trim()) throw new Error("imagegen: empty prompt");
  const out = path.resolve(opts.out);
  if (!/\.png$/i.test(out)) throw new Error(`imagegen: --out ${opts.out} must be a .png`);
  const aspect = opts.aspect ?? "1:1";
  if (!ASPECTS.includes(aspect)) throw new Error(`imagegen: --aspect ${aspect} (${ASPECTS.join(" | ")})`);
  const name = String(opts.name ?? path.basename(out, path.extname(out))).replace(/[^A-Za-z0-9_-]+/g, "_").slice(0, 40) || "image";
  const timeoutS = Number(opts.timeoutS ?? GEN[gen].timeoutS);
  const log = opts.log ?? ((l) => console.log(l));
  const workRoot = path.resolve(opts.workRoot ?? path.join(os.tmpdir(), "llmm-imagegen"));
  fs.mkdirSync(workRoot, { recursive: true });
  const work = fs.mkdtempSync(path.join(workRoot, `${gen}-${name}-`));
  // the clean temp dir: copies of the refs only
  const refs = refsIn.map((r, i) => { const c = path.join(work, `ref-${i + 1}${path.extname(r).toLowerCase() || ".png"}`); fs.copyFileSync(r, c); return c; });
  const ctx = { work, refs, prompt, name, aspect, timeoutS };
  const started = Date.now();
  const tries = [];
  let last = null;
  for (let n = 1; n <= 1 + RETRIES; n += 1) {
    last = gen === "gemini" ? await callGemini(ctx, n) : await callGpt(ctx, n);
    tries.push(last.record);
    if (last.record.ok || last.record.failure !== "transport" || n > RETRIES) break;
    log(`[imagegen] ${gen} ${name}: transport failure (${last.record.reason}) — one retry`);
  }
  const rec = last.record;
  const prov = {
    tool: "scripts/v7/imagegen.mjs", written: new Date().toISOString(), generator: gen, name, aspect,
    cli: { bin: last.command.bin.replace(/\\/g, "/"), version: cliVersion(last.command.bin, ["--version"]) },
    agentModel: rec.agentModel ?? GEN[gen].agent, agentModelAsked: GEN[gen].agent, agentEffort: GEN[gen].effort, imageTool: GEN[gen].imageTool,
    prompt: { file: opts.promptFile ? rel(path.resolve(opts.promptFile)) : null, sha256: sha256(prompt), chars: prompt.length },
    instruction: { sha256: sha256(last.instruction), text: last.instruction },
    command: { ...last.command, bin: last.command.bin.replace(/\\/g, "/"), cwd: work.replace(/\\/g, "/") },
    refs: refsIn.map((r, i) => ({ source: rel(r), sha256: shaFile(r), copy: refs[i].replace(/\\/g, "/") })),
    wallSeconds: +((Date.now() - started) / 1000).toFixed(1),
    tries,
    ok: rec.ok, failure: rec.failure, reason: rec.reason,
    output: null, original: null, imageModel: null, checks: null,
  };
  const provenanceFile = out.replace(/\.png$/i, ".provenance.json");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  if (rec.ok) {
    const orig = last.images[0];
    const meta = await sharp(orig).metadata();
    const origSha = shaFile(orig);
    if (meta.format === "png") {
      fs.copyFileSync(orig, out);
      prov.original = { source: orig.replace(/\\/g, "/"), sha256: origSha, format: "png", width: meta.width, height: meta.height, sameAsOutput: true };
    } else {
      const keep = out.replace(/\.png$/i, `.orig.${meta.format === "jpeg" ? "jpg" : meta.format}`);
      fs.copyFileSync(orig, keep);
      await sharp(orig).png().toFile(out);
      prov.original = { source: orig.replace(/\\/g, "/"), file: rel(keep), sha256: origSha, format: meta.format, width: meta.width, height: meta.height, converted: "sharp png (decoded pixels, lossless from the decode)" };
    }
    const om = await sharp(out).metadata();
    prov.output = { file: rel(out), sha256: shaFile(out), width: om.width, height: om.height };
    const c2 = c2paInfo(orig);
    prov.imageModel = { reportedByAgent: null, c2pa: c2, note: gen === "gemini" ? "generate_image names no model; C2PA 'Google Generative AI' (+ 'Input ingredient' per reference)" : "C2PA softwareAgent = the OpenAI image model family" };
    const copies = rec.agentCopies || [];
    prov.checks = {
      images: last.images.length, usedImage: 1,
      ...(gen === "gemini" ? { generateImageCalls: rec.generateImageCalls, referencesPassed: rec.referencesPassed, promptVerbatim: rec.promptVerbatim, aspectUsed: rec.aspectUsed } : { referencesAttached: refs.length }),
      extraToolCalls: rec.extraToolCalls ?? null,
      agentCopySameBytes: copies.length ? copies.some((c) => c.sha256 === origSha) : null,
    };
    const warn = [];
    if (last.images.length > 1) warn.push(`${last.images.length} images generated (the first is used)`);
    if (gen === "gemini" && rec.generateImageCalls !== 1) warn.push(`generate_image called ${rec.generateImageCalls}x`);
    if (gen === "gemini" && !rec.referencesPassed) warn.push("ImagePaths != the refs");
    if (gen === "gemini" && !rec.promptVerbatim) warn.push("prompt not verbatim");
    if (warn.length) prov.checks.warnings = warn;
  }
  fs.writeFileSync(provenanceFile, `${JSON.stringify(prov, null, 2)}\n`);
  const w = prov.checks?.warnings?.length ? ` WARN ${prov.checks.warnings.join("; ")}` : "";
  log(`[imagegen] ${gen} ${name}: ${rec.ok ? `ok ${prov.output.width}x${prov.output.height} -> ${rel(out)}` : `FAILED (${rec.failure}: ${rec.reason})`} · ${prov.wallSeconds} s · ${tries.length} try${tries.length > 1 ? "s" : ""}${w}`);
  return { ok: rec.ok, out, provenance: prov, provenanceFile };
}

// ---------------------------------------------------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------------------------------------------------

function parseCli(argv) {
  const a = { ref: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const t = argv[i];
    if (!t.startsWith("--")) throw new Error(`unexpected argument ${t}`);
    const k = t.slice(2); const v = argv[i + 1];
    if (k === "allow-gemini" || v === undefined || v.startsWith("--")) { a[k] = true; continue; }
    if (k === "ref") a.ref.push(v); else a[k] = v;
    i += 1;
  }
  return a;
}

const USAGE = "usage: node scripts/v7/imagegen.mjs [--gen gpt|gemini --allow-gemini] [--ref <png> ...] --prompt-file <txt> --out <png> [--aspect 1:1] [--name <label>] [--timeout <s>] [--work-root <dir>]";

async function main() {
  let a;
  try { a = parseCli(process.argv.slice(2)); } catch (e) { console.error(`${e.message}\n${USAGE}`); return 2; }
  if (a.help || !a["prompt-file"] || !a.out) { console.error(USAGE); return 2; }
  const r = await generateImage({ gen: a.gen === true || !a.gen ? DEFAULT_GEN : a.gen, allowGemini: !!a["allow-gemini"], refs: a.ref, promptFile: a["prompt-file"], out: a.out, aspect: a.aspect === true ? undefined : a.aspect,
    name: a.name === true ? undefined : a.name, timeoutS: a.timeout && a.timeout !== true ? Number(a.timeout) : undefined, workRoot: a["work-root"] === true ? undefined : a["work-root"] });
  return r.ok ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[imagegen] ERROR ${e.stack || e.message || e}`); process.exitCode = 2; });
}
