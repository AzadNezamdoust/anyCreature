#!/usr/bin/env node
// M3 — the LLM authors the spec.
//
//   node scripts/gen.mjs <subject> [--runner cli|codex|file|fake] [--out subjects/<subject>_llm]
//                        [--cache cache] [--fake <module.mjs>] [--inventory refs/<file>.md]
//
// LISTER -> (MEASURE skipped, see DEVIATIONS) -> BUILDER A -> validate -> auto-repair ->
// REPAIR seat (<=2) -> BUILDER B -> ... -> BUILDER C -> full chain.
//
// V0-V3 only after tiers A and B (props are not placed yet, so a stability hull or a scale
// table measured there would be measuring a half-built model); the full V0-V7 + V10 chain
// after tier C. Zero LLM tokens are spent inside the validators.
//
// The model call is PLUGGABLE because this machine has no API key and the standalone CLI is
// not logged in:
//   --runner cli   spawn `${CLAUDE_BIN:-claude} -p <prompt> --model <id> --output-format json`
//   --runner codex spawn `${CODEX_BIN} exec ... -m gpt-6-astra` (GPT Astra, reasoning effort
//                  high, read-only sandbox). The LISTER seat is Fable's by routing standard,
//                  so under this runner the lister alone falls back to the `file` path.
//   --runner file  write cache/pending/<hash>.{prompt.md,meta.json} and exit 3; a later run
//                  finds <hash>.response.md and resumes at the first missing response
//   --runner fake  a JS module mapping {seat, tier, attempt} -> canned response (tests)
//
// Never writes into subjects/tenement_block/ — the hand BASELINE is frozen.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import { validateSpec, reportText } from "../src/validate/index.js";
import { repair } from "../src/validate/repair.js";
import { compile } from "../src/compile/build.js";
import { codexBin } from "./codex-bin.mjs";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

/** Model ids are pinned exactly. An alias would auto-upgrade into an un-vetted model. */
export const SEAT_MODEL = {
  lister: "claude-fable-5-1",
  "builder-a": "claude-opus-5",
  "builder-b": "claude-opus-5",
  "builder-c": "claude-opus-5",
  repair: "claude-opus-5",
};

/** GPT Astra, via the OpenAI Codex CLI. Pinned exactly, same reason as above. */
export const CODEX_MODEL = "gpt-6-astra";
export const CODEX_EFFORT = "high";
/** The LISTER is Fable's seat; `--runner codex` leaves it on the file-runner path. */
const CODEX_EXEMPT_SEATS = new Set(["lister"]);

const TIERS = [
  { tier: "A", seat: "builder-a", template: "builder-a", chain: "partial" },
  { tier: "B", seat: "builder-b", template: "builder-b", chain: "partial" },
  { tier: "C", seat: "builder-c", template: "builder-c", chain: "full" },
];

const PARTIAL_CODES = new Set(["V0", "V1", "V2", "V3"]);
const MAX_REPROMPTS = 2;
const FROZEN_OUT = path.resolve(ROOT, "subjects/tenement_block");

// --- small helpers -----------------------------------------------------------------------

const sha256 = (text) => crypto.createHash("sha256").update(text).digest("hex");
const clone = (value) => JSON.parse(JSON.stringify(value));
const read = (relative) => fs.readFileSync(path.join(ROOT, relative), "utf8");

export class PendingResponse extends Error {
  constructor(hash, promptPath, metaPath) {
    super(`pending response: write ${path.relative(ROOT, promptPath).replace(/\\/g, "/").replace(/\.prompt\.md$/, ".response.md")}`);
    this.code = 3;
    this.hash = hash;
    this.promptPath = promptPath;
    this.metaPath = metaPath;
  }
}

function fill(template, vars) {
  return template.replace(/\{\{([A-Z_]+)\}\}/g, (match, key) => (Object.hasOwn(vars, key) ? String(vars[key]) : match));
}

/** Model output -> object. Tolerates a ```json fence and leading/trailing prose. */
export function extractJson(text) {
  const fenced = /```(?:json|jsonc)?\s*([\s\S]*?)```/i.exec(text);
  const body = fenced ? fenced[1] : text;
  const start = body.indexOf("{");
  const end = body.lastIndexOf("}");
  if (start === -1 || end <= start) throw new Error("no JSON object in model response");
  return JSON.parse(body.slice(start, end + 1));
}

/** 08:D4 — later tiers see a SUMMARY of the earlier ones, never the full JSON. */
export function summarise(spec, solved) {
  if ((spec.parts ?? []).length === 0) return "_(none — this is the first tier)_";
  const lines = [];
  if (solved?.bounds) {
    const b = solved.bounds;
    lines.push(`bounds: ${b.w.toFixed(2)} w x ${b.h.toFixed(2)} h x ${b.d.toFixed(2)} d m; ${solved.parts.length} solved parts, ${solved.triangles} tris`);
  }
  lines.push(`palette zones: ${Object.keys(spec.palette ?? {}).join(", ")}`);
  lines.push("parts (id | prim | dims | attaches to · face):");
  for (const part of spec.parts) {
    const where = part.ground ? "ground" : `${part.attach?.to} · ${part.attach?.face} ${part.attach?.contact ?? "flush"}`;
    lines.push(`- ${part.id} | ${part.prim} | [${part.dims.join(", ")}] | ${where}`);
  }
  if ((spec.facades ?? []).length > 0) {
    lines.push("facades (id | on · face | occlude):");
    for (const facade of spec.facades) lines.push(`- ${facade.id} | ${facade.on} · ${facade.face} | ${facade.occlude !== false}`);
  }
  return lines.join("\n");
}

function mergeFragment(base, fragment) {
  const out = clone(base);
  if (fragment.class) out.class = fragment.class;
  if (fragment.unit) out.unit = fragment.unit;
  if (fragment.seed !== undefined) out.seed = fragment.seed;
  if (fragment.palette) out.palette = { ...(out.palette ?? {}), ...fragment.palette };
  out.parts = [...(out.parts ?? []), ...(fragment.parts ?? [])];
  const facades = [...(out.facades ?? []), ...(fragment.facades ?? [])];
  if (facades.length > 0) out.facades = facades;
  else delete out.facades;
  return out;
}

/** Full chain always runs; `mode` decides which codes are allowed to BLOCK this tier. */
function evaluate(spec, mode) {
  let report;
  try {
    report = validateSpec(spec);
  } catch (error) {
    return { pass: false, violations: [{ v: "COMPILE", part: null, measured: "threw", limit: "compiles", hint: error.message }], text: `FAIL: compile threw — ${error.message}`, report: null };
  }
  const violations = mode === "full" ? report.violations : report.violations.filter((x) => PARTIAL_CODES.has(x.v));
  return { pass: violations.length === 0, violations, text: violations.length === 0 ? (mode === "full" ? report.text : "PASS: V0-V3 clean (tier gate).") : reportText(violations), report };
}

// --- runners -----------------------------------------------------------------------------

function runCli(model, prompt) {
  // Nested-session guard: a `claude -p` spawned from inside Claude Code inherits these and
  // refuses (or recurses). Strip them before the spawn, never afterwards.
  const env = { ...process.env };
  delete env.CLAUDECODE;
  delete env.CLAUDE_CODE_ENTRYPOINT;
  delete env.CLAUDE_CODE_SSE_PORT;

  const bin = process.env.CLAUDE_BIN || "claude";
  const started = Date.now();
  const result = spawnSync(bin, ["-p", prompt, "--model", model, "--output-format", "json"], {
    env,
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw new Error(`runner cli: ${result.error.message} (CLAUDE_BIN=${bin})`);
  if (result.status !== 0) throw new Error(`runner cli exited ${result.status}: ${(result.stderr || result.stdout || "").trim().slice(0, 400)}`);

  const payload = JSON.parse(result.stdout);
  return {
    text: payload.result ?? "",
    tokensIn: payload.usage?.input_tokens ?? 0,
    tokensOut: payload.usage?.output_tokens ?? 0,
    ms: payload.duration_api_ms ?? Date.now() - started,
  };
}

/**
 * `codex exec` transcript -> { model, effort, sessionId, answer, tokensUsed }.
 *
 * Shape (v0.154): a header block (`model:`, `reasoning effort:`, `session id:`), then `user`,
 * the prompt, then `codex`, the answer, then `tokens used` and the count. On a TTY all of it
 * is one merged stream and the answer is repeated after the count; with stdout piped the
 * transcript goes to stderr and stdout carries the bare answer. This parser reads the merged
 * form; `preferredAnswer` (the piped stdout) wins when present, because it is the raw reply
 * and never re-wrapped.
 *
 * The model/effort assertion is FATAL by design: a silent downgrade to a fallback model would
 * poison the cache with output nobody asked for.
 */
export function parseCodexTranscript(transcript, preferredAnswer = null) {
  const text = String(transcript ?? "");
  const field = (name) => new RegExp(`^${name}:\\s*(.+)$`, "m").exec(text)?.[1]?.trim() ?? null;
  const model = field("model");
  const effort = field("reasoning effort");
  const sessionId = field("session id");

  if (model !== CODEX_MODEL) {
    throw new Error(`runner codex: header says model="${model}", required "${CODEX_MODEL}" (no fallback model is acceptable)`);
  }
  if (effort !== CODEX_EFFORT) {
    throw new Error(`runner codex: header says reasoning effort="${effort}", required "${CODEX_EFFORT}"`);
  }

  const lines = text.split(/\r?\n/);
  let tokensIdx = -1;
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    if (lines[i].trim() === "tokens used") { tokensIdx = i; break; }
  }
  const tokensUsed = tokensIdx === -1 ? 0 : Number(String(lines[tokensIdx + 1] ?? "").replace(/[^0-9]/g, "")) || 0;

  const end = tokensIdx === -1 ? lines.length : tokensIdx;
  let codexIdx = -1;
  for (let i = end - 1; i >= 0; i -= 1) {
    if (lines[i].trim() === "codex") { codexIdx = i; break; }
  }
  let answer = codexIdx === -1 ? "" : lines.slice(codexIdx + 1, end).join("\n").trim();
  if (preferredAnswer && String(preferredAnswer).trim()) answer = String(preferredAnswer).trim();

  return { model, effort, sessionId, answer, tokensUsed };
}

export function runCodex(prompt) {
  const bin = process.env.CODEX_BIN
    || codexBin();
  const started = Date.now();
  // `codex exec` hangs with stdin open and appends piped stdin to the argv prompt, so the
  // real prompt travels on stdin and argv carries one short sentence. `--ignore-user-config`
  // is required: the user's config boots three MCP servers per call and never returns.
  // read-only sandbox — these seats answer with JSON, they never touch the tree.
  const args = [
    "exec",
    "--ignore-user-config",
    "--skip-git-repo-check",
    "-s", "read-only",
    "-C", ROOT,
    "-m", CODEX_MODEL,
    "-c", `model_reasoning_effort="${CODEX_EFFORT}"`,
    "Follow the instructions below.",
  ];
  const result = spawnSync(bin, args, {
    cwd: ROOT,
    input: prompt,
    encoding: "utf8",
    timeout: Number(process.env.LLMMODELING_CODEX_TIMEOUT_MS || 18 * 60 * 1000),
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw new Error(`runner codex: ${result.error.message} (CODEX_BIN=${bin})`);
  if (result.status !== 0) {
    throw new Error(`runner codex exited ${result.status}: ${(result.stderr || result.stdout || "").trim().slice(-400)}`);
  }

  const parsed = parseCodexTranscript(result.stderr ?? "", result.stdout ?? "");
  return {
    text: parsed.answer,
    tokensIn: 0,
    tokensOut: 0,
    tokensUsed: parsed.tokensUsed,
    ms: Date.now() - started,
    codex: { model: parsed.model, effort: parsed.effort, sessionId: parsed.sessionId },
  };
}

function runFile(ctx, { hash, seat, tier, model, prompt }) {
  const pendingDir = path.join(ctx.cacheDir, "pending");
  fs.mkdirSync(pendingDir, { recursive: true });
  const promptPath = path.join(pendingDir, `${hash}.prompt.md`);
  const metaPath = path.join(pendingDir, `${hash}.meta.json`);
  const responsePath = path.join(pendingDir, `${hash}.response.md`);

  if (fs.existsSync(responsePath)) {
    const text = fs.readFileSync(responsePath, "utf8");
    for (const file of [promptPath, metaPath, responsePath]) if (fs.existsSync(file)) fs.rmSync(file);
    return { text, tokensIn: 0, tokensOut: 0, ms: 0, fromPending: true };
  }

  fs.writeFileSync(promptPath, prompt);
  fs.writeFileSync(metaPath, `${JSON.stringify({ model, seat, subject: ctx.subject, tier }, null, 2)}\n`);
  throw new PendingResponse(hash, promptPath, metaPath);
}

async function resolveFake(fake) {
  if (typeof fake === "function") return fake;
  const target = path.isAbsolute(fake) ? fake : path.join(ROOT, fake);
  const module = await import(pathToFileURL(target).href);
  return module.default ?? module.respond;
}

// --- the seat call, with the cache in front of it ------------------------------------------

async function callSeat(ctx, { seat, tier, templateName, vars, attempt = 0, keyExtra = null }) {
  const template = ctx.templates[templateName] ?? (ctx.templates[templateName] = read(`prompts/${templateName}.md`));
  const prompt = fill(template, vars);
  // Under `--runner codex` every seat but the LISTER moves to GPT Astra; the lister stays on
  // the file path (Fable's seat) and the run records the split so nobody reads run.json and
  // concludes Astra wrote the parts plan.
  const codexSeat = ctx.runner === "codex" && !CODEX_EXEMPT_SEATS.has(seat);
  const effectiveRunner = ctx.runner === "codex" ? (codexSeat ? "codex" : "file") : ctx.runner;
  const model = codexSeat ? CODEX_MODEL : SEAT_MODEL[seat];
  // PLAN 3: sha256(promptTemplate + inputsHash + dslVersion + seat + tier). `attempt` rides
  // inside inputsHash because a repair prompt already carries the report text that changed.
  // `keyExtra` names an out-of-band input (the --inventory path) so two runs reading two
  // different inventory files can never share a cache entry; it is omitted when no such
  // input exists, which keeps every pre-existing hash exactly where it was.
  const keyInputs = [sha256(template), sha256(`${JSON.stringify(vars)}|${attempt}`), ctx.dslVersion, seat, tier];
  if (keyExtra) keyInputs.push(keyExtra);
  const hash = sha256(keyInputs.join("|"));
  const cacheFile = path.join(ctx.cacheDir, "specs", `${hash}.json`);

  if (fs.existsSync(cacheFile)) {
    const cached = JSON.parse(fs.readFileSync(cacheFile, "utf8"));
    return { ...cached, hash, cached: true, prompt };
  }

  let out;
  if (effectiveRunner === "cli") out = runCli(model, prompt);
  else if (effectiveRunner === "codex") out = runCodex(prompt);
  else if (effectiveRunner === "file") out = runFile(ctx, { hash, seat, tier, model, prompt });
  else if (effectiveRunner === "fake") out = await ctx.fakeFn({ seat, tier, attempt, model, hash, prompt, subject: ctx.subject });
  else throw new Error(`unknown runner "${ctx.runner}"`);

  const record = { seat, model, tier, attempt, text: out.text, tokensIn: out.tokensIn ?? 0, tokensOut: out.tokensOut ?? 0, ms: out.ms ?? 0 };
  if (out.tokensUsed !== undefined) record.tokensUsed = out.tokensUsed;
  if (out.codex) record.codex = out.codex;
  fs.mkdirSync(path.dirname(cacheFile), { recursive: true });
  fs.writeFileSync(cacheFile, `${JSON.stringify(record, null, 2)}\n`);
  return { ...record, hash, cached: false, prompt };
}

// --- the run -------------------------------------------------------------------------------

/**
 * @param {{subject:string, runner?:"cli"|"codex"|"file"|"fake", outDir?:string, cacheDir?:string,
 *          fake?:string|Function, log?:Function}} options
 */
export async function generate(options) {
  const subject = options.subject;
  const runner = options.runner ?? "file";
  // The LISTER's text fallback. Default is the tenement inventory; --inventory points it at
  // another subject's written target (M5: refs/pickup_truck.README.md).
  const inventoryPath = options.inventory ?? "refs/README.md";
  const inventoryFile = path.resolve(ROOT, inventoryPath);
  if (!fs.existsSync(inventoryFile)) throw new Error(`--inventory: no such file "${inventoryPath}"`);
  const log = options.log ?? (() => {});
  const cacheDir = path.resolve(options.cacheDir ? path.resolve(ROOT, options.cacheDir) : path.join(ROOT, "cache"));
  const outDir = path.resolve(options.outDir ? path.resolve(ROOT, options.outDir) : path.join(ROOT, "subjects", `${subject}_llm`));
  if (outDir === FROZEN_OUT || outDir.startsWith(`${FROZEN_OUT}${path.sep}`)) {
    throw new Error("refusing to write into subjects/tenement_block/ — the hand BASELINE is frozen");
  }

  const ctx = {
    subject,
    runner,
    cacheDir,
    templates: {},
    dslVersion: sha256(read("dsl/SPEC.md")).slice(0, 12),
    fakeFn: runner === "fake" ? await resolveFake(options.fake ?? "test/fixtures/fake-runner.mjs") : null,
  };

  const run = {
    subject,
    runner,
    startedAt: new Date().toISOString(),
    dslVersion: ctx.dslVersion,
    seats: SEAT_MODEL,
    deviations: [],
    calls: [],
    tiers: [],
  };

  const record = (call, verdict) => {
    run.calls.push({
      seat: call.seat,
      model: call.model,
      tier: call.tier,
      attempt: call.attempt,
      hash: call.hash,
      cached: call.cached,
      tokensIn: call.tokensIn,
      tokensOut: call.tokensOut,
      tokensUsed: call.tokensUsed ?? null,
      codex: call.codex ?? null,
      ms: call.ms,
      pass: verdict?.pass ?? null,
      violations: (verdict?.violations ?? []).map((v) => `${v.v}${v.part ? ` ${v.part}` : ""}`),
    });
  };

  // --- LISTER -----------------------------------------------------------------------------
  const refImage = path.join(ROOT, "refs", `${subject}.png`);
  const hasImage = fs.existsSync(refImage);
  if (!hasImage) {
    run.inventory = inventoryPath;
    run.deviations.push(`refs/${subject}.png absent — the LISTER was fed ${inventoryPath}'s structural inventory text instead of the image (04:T6 assumes a VLM reading a picture). Re-run the lister when the PNG lands; its cache key changes with the prompt inputs, so nothing stale survives.`);
  }
  if (runner === "codex") {
    log(`runner codex: builder-a/b/c + repair -> ${CODEX_MODEL} (effort ${CODEX_EFFORT}); the LISTER seat stays on the file runner (Fable's seat).`);
    run.codex = { model: CODEX_MODEL, effort: CODEX_EFFORT, sandbox: "read-only" };
    run.deviations.push(`--runner codex routes builder-a/b/c and repair to ${CODEX_MODEL} (reasoning effort ${CODEX_EFFORT}) via the OpenAI Codex CLI. The LISTER seat is exempt — it is Fable's by routing standard — and falls back to the file-runner path (cache/pending/<hash>.prompt.md), so the parts plan in this run was NOT authored by Astra.`);
  }
  run.deviations.push("MEASURE (Grounded SAM / operator-clicked boxes, PLAN 3) is NOT implemented in M3. Every rel_size the LISTER returns stays a hypothesis; only V0-V7 + V10 constrain the metres.");

  const listerCall = await callSeat(ctx, {
    seat: "lister",
    tier: "-",
    templateName: "lister",
    vars: {
      SUBJECT: subject,
      REFERENCE_MODE: hasImage
        ? `The reference image is \`refs/${subject}.png\`. Read it.`
        : `**No reference image is available in this run** (\`refs/${subject}.png\` has not landed yet). You are reading a written structural inventory of it instead. Treat it as the reference: do not invent parts it does not mention, and mark anything it leaves uncounted as \`count_uncertain\`.`,
      REFERENCE: hasImage ? "" : fs.readFileSync(inventoryFile, "utf8"),
    },
    keyExtra: options.inventory ? `inventory:${options.inventory.split(path.sep).join("/")}` : null,
  });
  const partsPlan = extractJson(listerCall.text);
  record(listerCall, null);

  // --- tiers ------------------------------------------------------------------------------
  let spec = { schema: "pg/1", subject, seed: 1, parts: [] };
  let solved = null;

  for (const tier of TIERS) {
    const summary = summarise(spec, solved);
    const vars = {
      SUBJECT: subject,
      DSL_SPEC: read("dsl/SPEC.md"),
      EXAMPLE_CRATE: read("dsl/examples/crate.json").trim(),
      EXAMPLE_FACADE: read("dsl/examples/facade-demo.json").trim(),
      PARTS_PLAN: JSON.stringify(partsPlan, null, 2),
      PREV_SUMMARY: summary,
    };

    const call = await callSeat(ctx, { seat: tier.seat, tier: tier.tier, templateName: tier.template, vars });
    let fragment = extractJson(call.text);
    let candidate = mergeFragment(spec, fragment);
    let verdict = evaluate(candidate, tier.chain);
    const tierLog = { tier: tier.tier, seat: tier.seat, autoRepairs: [], reprompts: 0, pass: false, text: "" };

    if (!verdict.pass && verdict.report) {
      const fixed = repair(candidate, verdict.report);
      if (fixed.applied.length > 0) {
        const after = evaluate(fixed.spec, tier.chain);
        if (after.pass || after.violations.length < verdict.violations.length) {
          candidate = fixed.spec;
          verdict = after;
          tierLog.autoRepairs = fixed.applied;
        }
      }
    }
    record(call, verdict);

    for (let attempt = 1; attempt <= MAX_REPROMPTS && !verdict.pass; attempt += 1) {
      const repairCall = await callSeat(ctx, {
        seat: "repair",
        tier: tier.tier,
        templateName: "repair",
        attempt,
        vars: { TIER: tier.tier, FRAGMENT: JSON.stringify(fragment, null, 2), REPORT: verdict.text },
      });
      tierLog.reprompts = attempt;
      fragment = extractJson(repairCall.text);
      candidate = mergeFragment(spec, fragment);
      verdict = evaluate(candidate, tier.chain);
      if (!verdict.pass && verdict.report) {
        const fixed = repair(candidate, verdict.report);
        if (fixed.applied.length > 0) {
          const after = evaluate(fixed.spec, tier.chain);
          if (after.pass || after.violations.length < verdict.violations.length) {
            candidate = fixed.spec;
            verdict = after;
            tierLog.autoRepairs.push(...fixed.applied);
          }
        }
      }
      record(repairCall, verdict);
    }

    tierLog.pass = verdict.pass;
    tierLog.text = verdict.text;
    run.tiers.push(tierLog);
    log(`tier ${tier.tier}: ${verdict.pass ? "PASS" : "FAIL"}${tierLog.reprompts ? ` after ${tierLog.reprompts} repair prompt(s)` : ""}${tierLog.autoRepairs.length ? `, ${tierLog.autoRepairs.length} auto-repair(s)` : ""}`);

    spec = candidate;
    if (!verdict.pass) {
      // Budget rule: a tier that will not validate ends the run. The next tier would build on
      // geometry the validator has already rejected.
      run.pass = false;
      run.stoppedAt = tier.tier;
      break;
    }
    solved = verdict.report ? compile(spec).solved : null;
  }

  // --- artefacts --------------------------------------------------------------------------
  const finalReport = validateSpecSafely(spec);
  run.pass = finalReport.pass;
  run.violations = finalReport.violations.map((v) => `${v.v}${v.part ? ` ${v.part}` : ""}`);
  run.totals = {
    calls: run.calls.length,
    cached: run.calls.filter((c) => c.cached).length,
    tokensIn: run.calls.reduce((sum, c) => sum + c.tokensIn, 0),
    tokensOut: run.calls.reduce((sum, c) => sum + c.tokensOut, 0),
    // codex reports one undivided count per call, not an in/out split
    tokensUsed: run.calls.reduce((sum, c) => sum + (c.tokensUsed ?? 0), 0),
    ms: run.calls.reduce((sum, c) => sum + c.ms, 0),
  };
  run.summary = `${run.totals.calls} call(s) (${run.totals.cached} cached), ${run.totals.tokensIn}/${run.totals.tokensOut} tokens in/out, ${run.tiers.reduce((n, t) => n + t.reprompts, 0)} repair prompt(s), FINAL ${finalReport.pass ? "PASS" : "FAIL"} (${run.violations.length} violation(s))`;

  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, "spec.json"), `${JSON.stringify(spec, null, 2)}\n`);
  let solvedOut = null;
  try {
    solvedOut = compile(spec).solved;
  } catch { /* a failed run has no solved model; report.json says why */ }
  fs.writeFileSync(path.join(outDir, "solved.json"), `${JSON.stringify(solvedOut, null, 2)}\n`);
  fs.writeFileSync(path.join(outDir, "report.json"), `${JSON.stringify({ pass: finalReport.pass, violations: finalReport.violations, advisories: finalReport.advisories ?? [], context: finalReport.context ?? null, text: finalReport.text }, null, 2)}\n`);
  fs.writeFileSync(path.join(outDir, "run.json"), `${JSON.stringify(run, null, 2)}\n`);

  log(run.summary);
  return { run, spec, report: finalReport, outDir, cacheDir };
}

function validateSpecSafely(spec) {
  try {
    return validateSpec(spec);
  } catch (error) {
    return { pass: false, violations: [{ v: "COMPILE", part: null, measured: "threw", limit: "compiles", hint: error.message }], advisories: [], text: `FAIL: compile threw — ${error.message}` };
  }
}

// --- CLI ------------------------------------------------------------------------------------

function parseArgs(argv) {
  const options = { subject: null, runner: "file" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--runner") options.runner = argv[++i];
    else if (arg === "--out") options.outDir = argv[++i];
    else if (arg === "--cache") options.cacheDir = argv[++i];
    else if (arg === "--fake") options.fake = argv[++i];
    else if (arg === "--inventory") options.inventory = argv[++i];
    else if (!arg.startsWith("--") && !options.subject) options.subject = arg;
    else throw new Error(`unrecognised argument "${arg}"`);
  }
  if (!options.subject) throw new Error("usage: node scripts/gen.mjs <subject> [--runner cli|codex|file|fake] [--out dir] [--cache dir] [--fake module] [--inventory path]");
  if (!["cli", "codex", "file", "fake"].includes(options.runner)) throw new Error(`--runner must be cli, codex, file or fake (got "${options.runner}")`);
  return options;
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    const options = parseArgs(process.argv.slice(2));
    const result = await generate({ ...options, log: (line) => console.log(line) });
    process.exit(result.run.pass ? 0 : 1);
  } catch (error) {
    if (error instanceof PendingResponse) {
      const rel = (file) => path.relative(ROOT, file).replace(/\\/g, "/");
      console.log(`PENDING ${rel(error.promptPath)} + ${rel(error.metaPath)} — write the model's reply to ${rel(error.promptPath).replace(/\.prompt\.md$/, ".response.md")} and re-run the same command`);
      process.exit(3);
    }
    console.error(`gen: ${error.message}`);
    process.exit(2);
  }
}
