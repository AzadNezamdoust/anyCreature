#!/usr/bin/env node
// render-module.mjs — let an author SEE its own module against the target (owner 2026-09-26).
//
//   node scripts/render-module.mjs --subject pickup --module out/ref/work/pickup.mjs [--out out/ref/work/view]
//
// Renders any module under out/ref/ with the subject's solved camera and class (app `?module=`), never touching
// the live subject module: flat + shaded stills at the TARGET camera, a shaded three-quarter, the role id pass.
// Then composes compare.png in the REGISTERED frame (scripts/registered.mjs: target px fixed per subject, no bbox
// rescale — WF-V4 V4-1): target | shaded render mapped into the target frame | outlines (render outline from the Node
// projector) | three-quarter, and prints the registered silhouette IoU, after check-module's contract/gate lines.
// Needs the vite dev server at http://127.0.0.1:4210/ (preview "llmmodeling").
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

import * as capture2 from "./capture2.mjs";
import { ROOT, loadSubject } from "./subject.mjs";
import { project, subjectRegistration } from "./project.mjs";
import { captureToTarget, composeSheet, iou, readRGB, targetState } from "./registered.mjs";

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
};

const subjectId = arg("subject");
const moduleRel = arg("module")?.replace(/\\/g, "/");
if (!subjectId || !moduleRel || !/^out\/ref\/.+\.mjs$/.test(moduleRel)) {
  console.error("usage: node scripts/render-module.mjs --subject <id> --module out/ref/<...>.mjs [--out <dir>]");
  process.exit(3);
}
const S = loadSubject(subjectId);
const outDir = path.resolve(ROOT, arg("out", path.join(path.dirname(moduleRel), "view")));
fs.mkdirSync(outDir, { recursive: true });

const check = spawnSync(process.execPath, [path.join(ROOT, "scripts", "check-module.mjs"), moduleRel, "--subject", subjectId], { cwd: ROOT, encoding: "utf8" });
process.stdout.write(check.stdout + check.stderr);
if (check.status !== 0) { console.log("[render] module FAILS check-module — fix it before rendering"); process.exit(1); }

process.env.BLINDLOOP_CONFIG = process.env.BLINDLOOP_CONFIG || path.join(ROOT, "..", "BlindLoop", "config.llmmodeling.json");
const base = "http://127.0.0.1:4210/";
const q = `capture=1&subject=${subjectId}&seed=1&size=900&module=${encodeURIComponent(moduleRel)}`;
const shots = [
  { name: "target", url: `${base}?${q}&view=target` },
  { name: "target-shaded", url: `${base}?${q}&view=target&shade=1` },
  { name: "threeQuarter-shaded", url: `${base}?${q}&view=threeQuarter&shade=1` },
  { name: "idpass", url: `${base}?${q}&view=target&idpass=1` },
].map((s) => ({ ...s, out: path.join(outDir, `${s.name}.png`) }));
try {
  await capture2.captureAll(shots);
} catch (error) {
  console.log(`[render] capture refused: ${error.message}`);
  process.exit(2);
}

const target = await readRGB(S.paths.target);
const reg = subjectRegistration(subjectId);
const proj = await project({ subjectId, modulePath: moduleRel, frame: "target", size: target.w });
const map = captureToTarget(proj.registration, { centre: proj.capture.centre, half: proj.capture.half, size: 900 });
const renderMask = proj.foreground();
// V5-1 item 1: the same three-state target + IoU as residuals / FIT / the loop (was the whole-image foreground)
const tm = targetState(S, target);
const registeredIoU = iou(tm, renderMask);
await composeSheet({ target, shaded: await readRGB(path.join(outDir, "target-shaded.png")), threeQuarterFile: path.join(outDir, "threeQuarter-shaded.png"),
  map, renderMask, out: path.join(outDir, "compare.png"), iouValue: registeredIoU, targetMask: tm });
console.log(`[compare] registered silhouette IoU ${registeredIoU.toFixed(4)} (target frame, no bbox alignment; anchor: ${reg.anchor.why}, quad fit rms ${reg.rmsPx.toFixed(2)} px)`);
console.log(`[render] ${path.relative(ROOT, outDir)}/compare.png  (target | shaded render at the target camera | outline overlay | shaded three-quarter)`);
