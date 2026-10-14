#!/usr/bin/env node
// WORKFLOW v7 — fit ONLY the concept-view similarity (frameScale / frameX / frameY, scripts/registered.mjs framed) of a
// module, its geometry fixed: coarse grid around the module's current frame (scale x (1 +- 0.015 / 0.03), shifts +-4 /
// 8 px; --no-grid skips it), then a coordinate search on THE registered concept IoU (judge.mjs's number).
//
//   node scripts/v7/frame.mjs --subject <s> --module <m.mjs> [--no-grid] [--stages 0.02:8,0.01:4,...] [--start s,tx,ty] [--write]
//
// --start searches from another frame than the module's knobs (e.g. 1,0,0 after a big proportion change).
// --write rewrites the three knob values inside the module's KNOBS block (scripts/knobs.mjs replaceKnobValues, 4 dp)
// and nothing else. Run it after any change to the body's proportions, before reading concept IoU as a shape signal.
//
//   node scripts/v7/frame.mjs --subject <s> --module <m.mjs> --sigma [from:to:step]   (default 0.975:1.015:0.005)
//
// --sigma: the ORTHO side instead — per-view ortho IoU (judge.mjs JUDGE_SIZE raster) vs the uniform model scale sigma
// the judge fits (its sigma printed first). A view peaking at a sigma far from the others = that view's proportions
// disagree with the rest (fix the geometry, not the scale).
import fs from "node:fs";
import process from "node:process";

import { buildModule, meshParts } from "../project.mjs";
import { iou } from "../registered.mjs";
import { basisOf, loadTurnaround, rasterOrtho, viewMap, viewTarget } from "../v6/ortho.mjs";
import { JUDGE_SIZE, judge } from "../v6/judge.mjs";
import { knobNum, replaceKnobValues } from "../knobs.mjs";
import { DEFAULT_STAGES, conceptIoUFn, conceptTarget, fitFrame, modulePathOf, parseArgs, parseStages, roundFrame } from "./lib.mjs";

const args = parseArgs(process.argv.slice(2), ["no-grid", "write", "help"]);
if (args.sigma === true) args.sigma = "0.975:1.015:0.005";
if (args.help || !args.subject || !args.module) {
  console.log("usage: node scripts/v7/frame.mjs --subject <s> --module <m.mjs> [--no-grid] [--stages ds:dp,...] [--start s,tx,ty] [--write] | --sigma [from:to:step]");
  process.exit(args.help ? 0 : 3);
}

async function sigmaScan(built) {
  const [a, b, st] = String(args.sigma).split(":").map(Number);
  if (![a, b, st].every(Number.isFinite) || st <= 0) throw new Error(`bad --sigma "${args.sigma}" (want from:to:step)`);
  const { reg } = await loadTurnaround(args.subject);
  const { sigma } = await judge({ subjectId: args.subject, built, tiles: false });
  const { meshes } = meshParts(built.parts, 0);
  console.log(`judge sigma ${sigma.toFixed(4)}; ortho IoU at ${JUDGE_SIZE} px`);
  console.log("sigma ", ...reg.names.map((v) => v.padStart(7)), "   mean");
  const best = Object.fromEntries(reg.names.map((v) => [v, { sg: 0, v: -1 }]));
  for (let sg = a; sg <= b + st * 1e-3; sg += st) {
    const r = reg.names.map((v) => {
      const m = viewMap(reg, v, JUDGE_SIZE);
      const { partId } = rasterOrtho(meshes, basisOf(reg.views[v].spec), { k: m.k * sg, bx: m.bx, by: m.by }, m.w, m.h);
      const x = iou(viewTarget(reg, v, JUDGE_SIZE).fg, partId, { ids: true });
      if (x > best[v].v) best[v] = { sg, v: x };
      return x;
    });
    console.log(sg.toFixed(3).padEnd(6), ...r.map((x) => x.toFixed(4).padStart(7)), (r.reduce((p, q) => p + q, 0) / r.length).toFixed(4).padStart(7));
  }
  console.log("peak  ", reg.names.map((v) => `${v} ${best[v].sg.toFixed(3)}`).join("  "));
}

async function main() {
  const file = modulePathOf(args.module);
  const built = await buildModule(file);
  if (args.sigma) return sigmaScan(built);
  const { T } = await conceptTarget(args.subject);
  const f = conceptIoUFn(args.subject, T, built);
  const stages = args.stages ? parseStages(args.stages) : DEFAULT_STAGES;
  let start = built.frame;
  if (args.start) {
    const [scale, tx, ty] = String(args.start).split(",").map(Number);
    if (![scale, tx, ty].every(Number.isFinite)) throw new Error(`bad --start "${args.start}" (want scale,tx,ty)`);
    start = { scale, tx, ty };
  }
  const r = await fitFrame(f, start, { grid: !args["no-grid"], stages });
  const fmt = (fr, v) => `${JSON.stringify(roundFrame(fr))} iou ${v.toFixed(4)}`;
  console.log("start", fmt(r.start.frame, r.start.v));
  if (r.gridBest) console.log("grid ", fmt(r.gridBest.frame, r.gridBest.v));
  for (const t of r.trace) console.log(`stage ds ${t.ds} dp ${t.dp}`.padEnd(26), fmt(t.frame, t.v));
  console.log("best ", fmt(r.frame, r.v), `(${r.v >= r.start.v ? "+" : ""}${(r.v - r.start.v).toFixed(4)})`);
  if (args.write) {
    const best = r.frame;   // replaceKnobValues writes 4 dp
    const text = fs.readFileSync(file, "utf8");
    fs.writeFileSync(file, replaceKnobValues(text, { frameScale: best.scale, frameX: best.tx, frameY: best.ty }));
    console.log("wrote frameScale", knobNum(best.scale), "frameX", knobNum(best.tx), "frameY", knobNum(best.ty), "->", file);
  }
}

main().catch((e) => { console.error(e.message ?? e); process.exit(1); });
