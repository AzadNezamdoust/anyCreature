#!/usr/bin/env node
// The QA sheet: one subject, three captures — target, threeQuarter, back —
// through the FROZEN Blind Loop capture path, never a screenshot tool.
//
//   node scripts/qa-sheet.mjs [subject] [--out-dir out/qa] [--size 900]
//
// Every frame goes through `tools/BlindLoop/capture.mjs` with
// `config.llmmodeling.json`, so viewport, deviceScaleFactor and the ready
// contract are the same ones the judge sees; a drift is a refusal, not a
// warning (BLIND_LOOP invariant 5). `capture.mjs` only templates
// (seed, view, size), so the subject is threaded through by building the URL
// here from the same template.
//
// DEVIATION (M2): compositing. The brief asks for one composited sheet if
// `sharp` is present in BlindLoop's node_modules, else three PNGs side by side
// with the deviation noted. BlindLoop ships playwright only — there is no
// `sharp` — so this writes the three PNGs plus `<subject>-sheet.html`, a
// three-up page that references them. Nothing downstream reads the sheet
// numerically; it is a human artefact, and adding an image dependency to a
// project whose whole point is "no binary in the inner loop" is not a trade M2
// gets to make.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const BLIND_LOOP = path.resolve(ROOT, "..", "BlindLoop");
const CONFIG = path.join(BLIND_LOOP, "config.llmmodeling.json");

export const QA_VIEWS = Object.freeze(["target", "threeQuarter", "back"]);

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

/** The capture URL for one (subject, view), off the frozen template. */
export function sheetUrl(config, { subject, view, seed = 1, size = 900 }) {
  const values = { ...config.capture.defaults, subject, view, seed, size };
  return config.capture.urlTemplate.replace(/\{(\w+)\}/g, (match, key) => {
    if (!(key in values)) throw new Error(`urlTemplate placeholder {${key}} has no value`);
    return encodeURIComponent(String(values[key]));
  });
}

function sheetHtml(subject, files) {
  const cells = files.map(({ view, file }) =>
    `  <figure><img src="./${path.basename(file)}" alt="${subject} ${view}"><figcaption>${view}</figcaption></figure>`).join("\n");
  return `<!doctype html>
<meta charset="utf-8">
<title>${subject} — QA sheet</title>
<style>
  body { margin: 0; background: #14161a; color: #e8e6e1; font: 13px/1.5 system-ui, sans-serif; }
  .sheet { display: flex; gap: 8px; padding: 8px; }
  figure { margin: 0; flex: 1 1 0; }
  img { width: 100%; display: block; background: #fff; }
  figcaption { padding: 4px 2px; opacity: 0.8; }
</style>
<div class="sheet">
${cells}
</div>
`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const subject = args._[0] ?? args.subject ?? "tenement_block";
  const outDir = path.resolve(ROOT, args["out-dir"] ?? "out/qa");
  const size = Number(args.size ?? 900);
  const seed = Number(args.seed ?? 1);

  const { capture, loadConfig } = await import(pathToFileURL(path.join(BLIND_LOOP, "capture.mjs")).href);
  const config = loadConfig(CONFIG);
  fs.mkdirSync(outDir, { recursive: true });

  const written = [];
  for (const view of QA_VIEWS) {
    const out = path.join(outDir, `${subject}-${view}.png`);
    const url = sheetUrl(config, { subject, view, seed, size });
    const result = await capture({ url, out, config });
    written.push({ view, file: result.out, triangles: result.manifest?.triangles, camera: result.manifest?.cameraId });
    console.log(`OK ${view} -> ${path.relative(ROOT, result.out).replace(/\\/g, "/")} (${result.manifest?.triangles} tris, ${result.manifest?.cameraId})`);
  }

  const sheet = path.join(outDir, `${subject}-sheet.html`);
  fs.writeFileSync(sheet, sheetHtml(subject, written));
  console.log(`OK sheet -> ${path.relative(ROOT, sheet).replace(/\\/g, "/")} (3 PNGs side by side; no sharp in BlindLoop/node_modules, see header)`);
}

const isCli = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url));
if (isCli) {
  main().catch((error) => {
    console.error(`REFUSED: ${error.message}`);
    process.exit(1);
  });
}
