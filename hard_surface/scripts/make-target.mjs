#!/usr/bin/env node
// make-target.mjs — generate a frozen TARGET reference image for one subject.
//
//   node scripts/make-target.mjs <subject> [--desc "<paragraph>"] [--desc-file <path>]
//                                [--out refs/<subject>.png] [--model gemini-3.1-pro-high]
//                                [--force] [--check-verticals]
//
// The image comes from the owner's Google AI Ultra subscription, driven
// headlessly through the Antigravity CLI (`agy --print ...`), whose agent owns
// a `generate_image` tool. No API key, no new dependency, no network code here:
// this script only composes the prompt, spawns `agy`, and audits the PNG that
// lands on disk.
//
// TARGETs are frozen (BLIND_LOOP invariant 1: fix the work, never the target),
// so an existing output file is a refusal, not an overwrite, unless --force.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const BLIND_LOOP = path.resolve(ROOT, "..", "BlindLoop");

/** Frozen style block. Every TARGET prompt ends with exactly this text. */
export const STYLE = [
  "Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left,",
  "no perspective, vertical edges perfectly vertical.",
  "Cartoon low-poly game asset: flat cel shading, one solid colour per surface, no textures,",
  "no gradients, no brick or tile patterns, thin dark outlines.",
  "Every surface is one uniform flat colour edge to edge: no individual bricks, no stray brick",
  "accents, no panel lines, no surface detail of any kind. Windows are a single flat colour with",
  "no reflections, streaks, highlights or glass shine.",
  "No people, no animals, no vehicles unless the subject is one, no props beyond those described,",
  "no text or signage.",
  "Solid white background, whole object in frame with margin, centred.",
].join(" ");

const MIN_BYTES = 50 * 1024;
const SPAWN_TIMEOUT_MS = 8 * 60 * 1000;
const PRINT_TIMEOUT = "6m";

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) { args._.push(token); continue; }
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) args[key] = true;
    else { args[key] = next; i += 1; }
  }
  return args;
}

/** subject description + the frozen STYLE block. */
export function composePrompt(description) {
  return `${description.trim().replace(/\s+/g, " ")} ${STYLE}`;
}

/** The single instruction handed to the agy agent. */
export function composeInstruction(pngPath, prompt) {
  return [
    `Use your generate_image tool to create this image and save the PNG file as ${pngPath}`,
    "(the file must exist on disk when you finish).",
    `Prompt for the image: ${prompt}`,
    "Reply with the saved path, the image model used, and nothing else.",
  ].join(" ");
}

/** Resolve `agy` to a real executable — node's spawn does no PATHEXT lookup. */
function resolveAgy() {
  if (process.env.AGY_BIN) return process.env.AGY_BIN;
  const exts = process.platform === "win32" ? [".exe", ".cmd", ".bat", ""] : [""];
  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      const candidate = path.join(dir, `agy${ext}`);
      try { if (fs.statSync(candidate).isFile()) return candidate; } catch { /* next */ }
    }
  }
  return "agy";
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

/**
 * Silhouette verticality audit. Advisory only — prints PASS/WARN, never blocks.
 * Needs `sharp`; BlindLoop ships playwright only, so this normally skips.
 */
async function checkVerticals(pngPath) {
  let sharp;
  try {
    sharp = createRequire(path.join(BLIND_LOOP, "package.json"))("sharp");
  } catch {
    console.log("verticals: SKIP — `sharp` is not in tools/BlindLoop/node_modules (no dependency added).");
    return;
  }
  const { data, info } = await sharp(pngPath).greyscale().raw().toBuffer({ resolveWithObject: true });
  const { width, height } = info;
  const lo = Math.floor(height * 0.2);
  const hi = Math.ceil(height * 0.8);
  const lefts = [];
  const rights = [];
  for (let y = lo; y < hi; y += 1) {
    let left = -1;
    let right = -1;
    for (let x = 0; x < width; x += 1) {
      if (data[y * width + x] < 240) { if (left < 0) left = x; right = x; }
    }
    if (left >= 0) { lefts.push(left); rights.push(right); }
  }
  if (lefts.length === 0) { console.log("verticals: WARN — no non-white pixels in the middle 60% of height."); return; }
  const spread = (a) => Math.max(...a) - Math.min(...a);
  const dl = spread(lefts);
  const dr = spread(rights);
  const verdict = dl <= 2 && dr <= 2 ? "PASS" : "WARN";
  console.log(`verticals: ${verdict} — left edge varies ${dl}px, right edge varies ${dr}px over the middle 60% of height (tolerance 2px).`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const subject = args._[0];
  if (!subject) {
    console.error('usage: node scripts/make-target.mjs <subject> [--desc "..."] [--desc-file <path>] [--out <png>] [--model <id>] [--force] [--check-verticals]');
    process.exit(2);
  }

  let description = typeof args.desc === "string" ? args.desc : null;
  if (!description && typeof args["desc-file"] === "string") {
    description = fs.readFileSync(path.resolve(ROOT, args["desc-file"]), "utf8");
  }
  if (!description || !description.trim()) {
    console.error('no subject description: pass --desc "<one paragraph>" or --desc-file <path>.');
    process.exit(2);
  }

  const outPath = path.resolve(ROOT, typeof args.out === "string" ? args.out : path.join("refs", `${subject}.png`));
  if (fs.existsSync(outPath) && !args.force) {
    console.error(`refusing to overwrite ${outPath} — TARGETs are frozen. Pass --force if the owner asked for a new one.`);
    process.exit(1);
  }

  const prompt = composePrompt(description);
  console.log(`subject : ${subject}`);
  console.log(`out     : ${outPath}`);
  console.log(`model   : ${typeof args.model === "string" ? args.model : "(agy default)"}`);
  console.log(`\n--- STYLE (frozen) ---\n${STYLE}\n`);
  console.log(`--- full prompt ---\n${prompt}\n`);

  const workDir = fs.mkdtempSync(path.join(os.tmpdir(), "make-target-"));
  const tmpPng = path.join(workDir, `${subject}.png`);
  const instruction = composeInstruction(tmpPng, prompt);

  const agyArgs = ["--print", instruction, "--add-dir", workDir, "--dangerously-skip-permissions",
    "--effort", "high", "--output-format", "text", "--print-timeout", PRINT_TIMEOUT];
  if (typeof args.model === "string") agyArgs.push("--model", args.model);

  console.log(`spawning agy (timeout ${SPAWN_TIMEOUT_MS / 60000}m, cwd ${workDir}) ...`);
  const started = Date.now();
  const run = spawnSync(resolveAgy(), agyArgs, {
    cwd: workDir,
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf8",
    timeout: SPAWN_TIMEOUT_MS,
    windowsHide: true,
  });
  const elapsed = ((Date.now() - started) / 1000).toFixed(1);
  const reply = (run.stdout || "").trim();
  if (run.error) { console.error(`agy failed: ${run.error.message}`); process.exit(1); }
  console.log(`agy exited ${run.status} after ${elapsed}s`);
  if (reply) console.log(`--- agy reply ---\n${reply}\n`);
  if (run.stderr && run.stderr.trim()) console.log(`--- agy stderr ---\n${run.stderr.trim()}\n`);

  if (!fs.existsSync(tmpPng)) {
    console.error(`FAIL — no PNG at ${tmpPng}. The agent did not write the file.`);
    process.exit(1);
  }
  const bytes = fs.statSync(tmpPng).size;
  if (bytes <= MIN_BYTES) {
    console.error(`FAIL — ${tmpPng} is ${bytes} bytes (<= ${MIN_BYTES}); that is not a real render.`);
    process.exit(1);
  }

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.copyFileSync(tmpPng, outPath);
  const digest = sha256(outPath);

  const sidecar = outPath.replace(/\.png$/i, "") + ".prompt.md";
  fs.writeFileSync(sidecar, [
    `# TARGET provenance — ${subject}`,
    "",
    `- date: ${new Date().toISOString()}`,
    `- model flag: ${typeof args.model === "string" ? args.model : "(agy default)"}`,
    `- image: ${path.relative(ROOT, outPath).split(path.sep).join("/")}`,
    `- bytes: ${bytes}`,
    `- sha256: ${digest}`,
    "",
    "## Full prompt",
    "",
    "```",
    prompt,
    "```",
    "",
    "## agy final reply",
    "",
    "```",
    reply || "(empty)",
    "```",
    "",
  ].join("\n"), "utf8");

  console.log(`wrote ${outPath} (${bytes} bytes)`);
  console.log(`sha256 ${digest}`);
  console.log(`wrote ${sidecar}`);

  if (args["check-verticals"]) await checkVerticals(outPath);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((err) => { console.error(err); process.exit(1); });
}
