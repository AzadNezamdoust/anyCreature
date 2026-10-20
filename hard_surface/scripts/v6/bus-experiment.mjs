#!/usr/bin/env node
// WORKFLOW v6 — V6-1: the BUS MULTI-VIEW EXPERIMENT (research/WF-V6-PLAN.md "Experiment").
//
//   node scripts/v6/bus-experiment.mjs [--fit]        (--fit re-runs the two FITs; else reuses out/v6/{B,CONTROL}.mjs)
//
// Arms: A = the v56 bus (copied to out/v6/A.mjs); B = out/v6/bus-start.mjs FIT on the concept view + the 4 turnaround
// orthos (scripts/v6/mvfit.mjs); CONTROL = the same start FIT on the concept view only. Every arm is judged on the same
// 6-view sheet (scripts/v6/judge.mjs). Writes out/v6/ortho-registration.json, out/v6/<arm>-sheet.png,
// out/v6/bus-experiment.png (reference row + the three arms) and out/v6/bus-experiment.json.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

import { ROOT } from "../subject.mjs";
import { mvFit, subjectOrthos } from "./mvfit.mjs";
import { composeRows, judge, referenceTiles, sheetOrder } from "./judge.mjs";

const SUBJECT = "school_bus";
const OUT = "out/v6";
const ARMS = Object.freeze({ A: `${OUT}/A.mjs`, B: `${OUT}/B.mjs`, CONTROL: `${OUT}/CONTROL.mjs` });
const r3 = (v) => Math.round(v * 1000) / 1000;

async function main() {
  const abs = (p) => path.resolve(ROOT, p);
  fs.mkdirSync(abs(OUT), { recursive: true });
  // 1 — ortho registration + the stylisation ratio measured off the turnaround
  const { prior, reg } = await subjectOrthos(SUBJECT);
  const ORTHO_NAMES = reg.names;
  const stylisation = { LoverW: r3(reg.dims.L / reg.dims.W), HoverW: r3(reg.dims.H / reg.dims.W), realLoverW: prior.real.LoverW, realHoverW: prior.real.HoverW };
  const registration = { pxPerM: r3(reg.s), dims: Object.fromEntries(Object.entries(reg.dims).map(([k, v]) => [k, r3(v)])), shared: reg.shared, residuals: reg.residuals, stylisation,
    views: Object.fromEntries(ORTHO_NAMES.map((v) => [v, { ox: reg.views[v].ox, oy: reg.views[v].oy, fgBox: reg.views[v].box }])) };
  fs.writeFileSync(abs(`${OUT}/ortho-registration.json`), `${JSON.stringify(registration, null, 2)}\n`);
  console.log(`[v6] ortho px/m ${r3(reg.s)}; body ${registration.dims.L} x ${registration.dims.W} x ${registration.dims.H} m; residuals L ${reg.residuals.L.maxAbs.toFixed(4)} H ${reg.residuals.H.maxAbs.toFixed(4)} W ${reg.residuals.W.maxAbs.toFixed(4)} (bbox W ${reg.residuals.Wbbox.maxAbs.toFixed(4)})`);
  // 2 — arms
  if (!fs.existsSync(abs(ARMS.A))) fs.copyFileSync(abs("out/v56/loop-school_bus/build/module.mjs"), abs(ARMS.A));
  const fit = process.argv.includes("--fit");
  if (fit || !fs.existsSync(abs(ARMS.B))) await mvFit({ subjectId: SUBJECT, modulePath: `${OUT}/bus-start.mjs`, out: ARMS.B, log: `${OUT}/B.fit.json` });
  if (fit || !fs.existsSync(abs(ARMS.CONTROL))) await mvFit({ subjectId: SUBJECT, modulePath: `${OUT}/bus-start.mjs`, out: ARMS.CONTROL, views: ["concept"], log: `${OUT}/CONTROL.fit.json` });
  // 3 — judge
  const ref = await referenceTiles(SUBJECT);
  const rows = [{ label: "REFERENCE — turnaround side / front / rear / top, concept (front-left), rear-right: no reference", tiles: ref }];
  const results = {};
  for (const [arm, modulePath] of Object.entries(ARMS)) {
    const { metrics, tiles } = await judge({ subjectId: SUBJECT, modulePath });
    results[arm] = metrics;
    const c = metrics.checks;
    const floats = c.groups.filter((g) => g.float).map((g) => g.name);
    const iouLine = [...ORTHO_NAMES, "concept"].map((v) => `${v} ${metrics.views[v].iou.toFixed(3)}`).join(" · ");
    const label = `${arm} — ${iouLine} · sigma ${metrics.sigma} · float [${floats.join(", ")}] · clips ${c.clips.length} · mirror arm ${c.mirror?.armLength ?? "-"} m${c.mirror?.swept?.clip ? " SWEPT-CLIP" : ""}`;
    const notes = Object.fromEntries(ORTHO_NAMES.map((v) => [v, `IoU ${metrics.views[v].iou.toFixed(3)}`]));
    notes.frontLeft = `concept IoU ${metrics.views.concept.iou.toFixed(3)}`;
    const row = { label, tiles, notes };
    rows.push(row);
    await composeRows([rows[0], row], `${OUT}/${arm}-sheet.png`, 220, sheetOrder(reg));
    console.log(`[v6] ${label}`);
  }
  await composeRows(rows, `${OUT}/bus-experiment.png`, 220, sheetOrder(reg));
  fs.writeFileSync(abs(`${OUT}/bus-experiment.json`), `${JSON.stringify({ registration: { pxPerM: registration.pxPerM, dims: registration.dims, residuals: reg.residuals, stylisation }, arms: results }, null, 2)}\n`);
  console.log(`[v6] wrote ${OUT}/bus-experiment.png, ${OUT}/bus-experiment.json`);
}

main().catch((error) => { console.error(error); process.exit(1); });
