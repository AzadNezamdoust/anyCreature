#!/usr/bin/env node
// WF v8 WP3 — START FROM THE NEAREST GOLD (research/v7/WF-V8-PLAN.md WP3, WF-REVIEW-fable.md C10): a subject's start.mjs
// is a copy of the gold module closest to its class shape, re-dimensioned, re-coloured and re-framed for the subject —
// round 1 then spends its iterations on the subject's features instead of rediscovering a vehicle body.
//
//   node scripts/v7/scaffold.mjs --subject <s> (--from out/ref/gold/<g>/model.mjs | --shape <shape>) [--out <dir>] [--force] [--no-step]
//
// Nearest gold per class shape (--shape; NEAREST below): sedan / hatchback / coupe -> taxi; box truck / box van on a cab
// chassis -> delivery_truck; cab-over, bus body, flat-front van -> school_bus; pickup / open bed -> pickup; machine (exposed
// wheels, open frame, mast / boom / loader / canopy) -> tractor. A blockout only when nothing is close.
// What it does (module text edited in place, the rest is the gold's code — its comments describe the gold subject):
//   1. dims: KNOBS L / W / H / wheelR, else top-level DEFAULTS L / W / H / R, else a `const L = <n>;` (steplib dimsPlan):
//      each x the target / source registered-dimension ratio (ortho.mjs reg.dims), the wheel radius from the target
//      prior's stylisation.wheelDoverH; an absolute-metre gold (delivery_truck, tractor) keeps its size — the concept frame
//      starts at the size ratio and the judge's sigma absorbs the rest (proportions are the modeller's round 1);
//   2. palette: every "#hex" of meta.palette through steplib remapColour (source family -> the target family of the same
//      name, cel tones kept as offsets; families the target lacks keep their colour);
//   3. header comment rewritten; the kernel import re-pointed when --out sits elsewhere;
//   4. frame knobs reset, then scripts/v7/frame.mjs --write (grid + search, from the size ratio);
//   5. scripts/v7/step.mjs --baseline none on the result (skip with --no-step).
// Writes <out>/start.mjs (default out/ref/gold/<s>/start.mjs; an existing one only with --force).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import { checkModule } from "../check-module.mjs";
import { ROOT } from "../subject.mjs";
import { knobNum, replaceKnobValues } from "../knobs.mjs";
import { hasTurnaround, loadTurnaround } from "../v6/ortho.mjs";
import { importModule, parseArgs } from "./lib.mjs";
import { braceRange, dimsPlan, mapHexIn, remapColour, setTopLevelValues, stripHeader, withFrameKnobs } from "./steplib.mjs";

/** The gold nearest each class shape. */
export const NEAREST = Object.freeze({ sedan: "taxi", box: "delivery_truck", bus: "school_bus", pickup: "pickup", machine: "tractor" });
const USAGE = `usage: node scripts/v7/scaffold.mjs --subject <s> (--from out/ref/gold/<g>/model.mjs | --shape ${Object.keys(NEAREST).join("|")}) [--out <dir>] [--force] [--no-step]`;
const args = parseArgs(process.argv.slice(2), ["force", "no-step", "help"]);
const str = (v) => (v && v !== true ? String(v) : null);
const rel = (p) => { const r = path.relative(ROOT, p); return (r && !r.startsWith("..") && !path.isAbsolute(r) ? r : p).replace(/\\/g, "/"); };
const r4 = (v) => Math.round(v * 1e4) / 1e4;

/**
 * The kernel import specifier for a module written into `dir`: relative when it can be, else the kernel's file URL in the
 * one-slash form `file:/D:/...` (check-module's comment stripper would eat a `file:///` URL's second `//`).
 */
function kernelSpecifier(dir) {
  const kernel = path.join(ROOT, "src", "kernel", "index.mjs");
  const r = path.relative(dir, kernel);
  if (path.isAbsolute(r) || /^[A-Za-z]:/.test(r)) return pathToFileURL(kernel).href.replace(/^file:\/\/\//, "file:/");
  const p = r.replace(/\\/g, "/");
  return p.startsWith(".") ? p : `./${p}`;
}

async function main() {
  const s = str(args.subject);
  const shape = str(args.shape);
  if (args.help || !s || (!str(args.from) && !shape)) { console.log(USAGE); return args.help ? 0 : 3; }
  if (shape && !NEAREST[shape]) throw new Error(`--shape ${shape}: one of ${Object.keys(NEAREST).join(", ")}`);
  const from = str(args.from) ? path.resolve(args.from) : path.join(ROOT, "out", "ref", "gold", NEAREST[shape], "model.mjs");
  const g = str(args["from-subject"]) ?? /[\\/]gold[\\/]([^\\/]+)[\\/][^\\/]+$/.exec(from)?.[1];
  if (!g || !hasTurnaround(g)) throw new Error(`cannot tell the gold subject of ${from} (--from-subject <g>)`);
  if (!hasTurnaround(s)) throw new Error(`${s} has no subjects/${s}/turnaround/views.json`);
  const outDir = str(args.out) ? path.resolve(args.out) : path.join(ROOT, "out", "ref", "gold", s);
  const outFile = path.join(outDir, "start.mjs");
  if (fs.existsSync(outFile) && !args.force) throw new Error(`${rel(outFile)} exists (--force overwrites it)`);

  const src = await loadTurnaround(g);
  const dst = await loadTurnaround(s);
  const mod = await importModule(from);
  let text = fs.readFileSync(from, "utf8").replace(/\r\n/g, "\n");
  const lines = [];

  // 1. dims (dropped again when the re-dimensioned module does not build: the gold's other numbers are absolute)
  const constL = /\n\s*const L = (-?[\d.]+);/.exec(text);
  let plan = dimsPlan({ knobs: mod.KNOBS, defaults: mod.DEFAULTS, consts: constL ? { L: Number(constL[1]) } : null, srcDims: src.reg.dims, dstDims: dst.reg.dims, prior: dst.prior });
  const sized = plan.reduce((t, p) => (p.where === "KNOBS" ? replaceKnobValues(t, { [p.key]: p.to })
    : p.where === "DEFAULTS" ? setTopLevelValues(t, "export const DEFAULTS = {", { [p.key]: p.to })
      : t.replace(/(\n\s*const L = )(-?[\d.]+);/, `$1${knobNum(p.to)};`)), text);
  let dimsFail = null;
  if (plan.length) {
    fs.mkdirSync(outDir, { recursive: true });
    const probe = path.join(outDir, `.scaffold-${process.pid}.mjs`);
    fs.writeFileSync(probe, sized.replace(/(import \* as K from ["'])([^"']*src\/kernel\/index\.mjs)(["'])/, `$1${kernelSpecifier(outDir)}$3`));
    try {
      const cm = await checkModule(probe, { label: "the re-dimensioned module", subjectId: s });
      if (!cm.pass) dimsFail = cm.lines.slice(1).join(" ").trim().slice(0, 200);
    } finally { fs.rmSync(probe, { force: true }); }
  }
  if (dimsFail) plan = [];
  else text = sized;
  const ratio = Object.fromEntries(["L", "W", "H"].map((D) => [D, dst.reg.dims[D] / src.reg.dims[D]]));
  const sizeK = plan.length ? 1 : r4(Math.cbrt(ratio.L * ratio.W * ratio.H));   // an absolute-metre gold: the frame starts at the size ratio
  lines.push(plan.length ? `dims ${plan.map((p) => `${p.where} ${p.key} ${knobNum(p.from)} -> ${knobNum(p.to)} (${p.why})`).join(" · ")}`
    : `dims: ${dimsFail ? `NOT applied — ${g} re-dimensioned fails check-module (${dimsFail})` : `${g} has no L / W / H / R knob, DEFAULTS entry or const L`} — geometry kept at ${g}'s size; ${s} / ${g} = L x${r4(ratio.L)} W x${r4(ratio.W)} H x${r4(ratio.H)} (frame starts at x${sizeK})`);

  // 2. palette (every hex of the meta.palette block)
  const metaAt = text.indexOf("export const meta");
  const palAt = metaAt >= 0 ? text.indexOf("palette:", metaAt) : -1;
  const range = palAt >= 0 ? braceRange(text, palAt) : null;
  if (!range) throw new Error(`${rel(from)}: no meta.palette block`);
  const moved = new Map();
  text = mapHexIn(text, [range[0], range[1] + 1], (hex) => {
    const r = remapColour(hex, src.table, dst.table);
    if (r.moved) moved.set(r.family, (moved.get(r.family) ?? 0) + 1);
    return r.hex;
  });
  const kept = Object.keys(mod.meta.palette ?? {}).length;
  lines.push(`palette: ${[...moved.entries()].map(([f, n]) => `${f} (${n} colour${n > 1 ? "s" : ""})`).join(", ") || "nothing"} -> ${s}'s families.table; ${s} lacks the other families: kept (${kept} zones)`);

  // 3. header + kernel import
  const date = new Date().toISOString().slice(0, 10);
  const header = [
    `// START — ${s} (refs/${s}.png + subjects/${s}/turnaround), scaffolded ${date} by scripts/v7/scaffold.mjs from`,
    `// ${rel(from)} — the nearest gold of its class shape. Set here: ${plan.length ? plan.map((p) => `${p.key} ${knobNum(p.to)}`).join(", ") : `nothing (${g}'s size kept)`}; palette`,
    `// remapped to ${s}'s colour families; frame knobs refitted on the concept. EVERYTHING ELSE IS ${g.toUpperCase()}'S GEOMETRY and every`,
    `// comment below describes ${g}: rebuild the features against ${s}'s references (step.mjs is the loop).`,
    "// Frame (classes/vehicle.md): +Y up, nose at +Z, +X flank toward the camera, centred on x = 0, ground y = 0.",
  ];
  text = `${header.join("\n")}\n${stripHeader(text)}`;
  const spec = kernelSpecifier(outDir);
  text = text.replace(/(import \* as K from ["'])([^"']*src\/kernel\/index\.mjs)(["'])/, `$1${spec}$3`);

  // 4. frame knobs reset (inserted when the gold has none), then the fit
  text = withFrameKnobs(text, { scale: 1, tx: 0, ty: 0 });
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(outFile, text);
  const fr = spawnSync(process.execPath, ["scripts/v7/frame.mjs", "--subject", s, "--module", outFile, "--write", "--start", `${sizeK},0,0`], { cwd: ROOT, encoding: "utf8" });
  if (fr.status !== 0) throw new Error(`frame.mjs failed: ${(fr.stderr || fr.stdout).trim().split(/\r?\n/).slice(-2).join(" / ")}`);
  const best = fr.stdout.split(/\r?\n/).find((l) => l.startsWith("best "));
  lines.push(`frame ${best ? best.replace(/^best\s+/, "") : "?"}`);
  console.log(`[scaffold] ${s} <- ${rel(from)} · wrote ${rel(outFile)}`);
  for (const l of lines) console.log(`[scaffold] ${l}`);

  // 5. the step verdict of the start (no baseline)
  if (!args["no-step"]) {
    const st = spawnSync(process.execPath, ["scripts/v7/step.mjs", "--subject", s, "--module", outFile, "--baseline", "none"], { cwd: ROOT, encoding: "utf8" });
    process.stdout.write(st.stdout);
    if (st.status === 2) process.stderr.write(st.stderr);
  }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().then((c) => { process.exitCode = c; }).catch((e) => { console.error(`[scaffold] ERROR ${e.message ?? e}`); process.exitCode = 2; });
}
