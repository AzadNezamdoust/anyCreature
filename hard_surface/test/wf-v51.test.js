// WORKFLOW v5 — V5-1 (research/WF-V5-ACCURACY.md): honest scoring. Bugs (a) wall clock inside FIT / the loop,
// (b) a rejected edit is never re-sent nor re-scored; item 1 the three-state target + ONE IoU; item 2 the fitted
// similarity + free massing; items 3/4 the accuracy report (inventory items, MISSING, UNOWNED, render-as-target floor).
// Hermetic: fixtures under test/fixtures/v4, refs/ subjects/ classes/ read only; writes under test/.tmp-wf-v51-<pid>/.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { project } from "../scripts/project.mjs";
import { fit, fitTarget, score } from "../scripts/fit.mjs";
import { residuals } from "../scripts/residuals.mjs";
import { OCCLUDED, addFrameKnobs, iou, readRGB, registeredIoU, targetState } from "../scripts/registered.mjs";
import { accuracy, flatRender, groupOf } from "../scripts/accuracy.mjs";
import { atTarget, editSummary, placeModule, runLoop } from "../scripts/loop.mjs";
import { generateForSubject } from "../scripts/template-building.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TMP = path.join(ROOT, "test", `.tmp-wf-v51-${process.pid}`);
const FACADE = "test/fixtures/v4/start-knobs-facade.mjs";
const WORK = "test/fixtures/v4/work-pickup.mjs";
const LIVE = ["subjects/pickup/module.mjs", "subjects/facade_brick/facade.mjs", "subjects/school_bus/module.mjs"].map((f) => path.join(ROOT, f)).filter((f) => fs.existsSync(f));
const hash = (f) => createHash("sha256").update(fs.readFileSync(f)).digest("hex");
const liveBefore = LIVE.map(hash);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

test("V5-1 item 1: three-state target — facade has an OCCLUDED band, pickup none; OCCLUDED px are in neither I nor U", async () => {
  const S = loadSubject("facade_brick");
  const img = await readRGB(S.paths.target);
  const t = targetState(S, img);
  const n = [0, 0, 0];
  for (const v of t) n[v] += 1;
  assert.ok(n[OCCLUDED] > 20000 && n[1] > 150000, JSON.stringify(n));
  const P = loadSubject("pickup");
  const tp = targetState(P, await readRGB(P.paths.target));
  assert.equal(tp.filter((v) => v === OCCLUDED).length, 0);
  assert.equal(iou(Uint8Array.from([1, 2, 0, 1]), Uint8Array.from([1, 1, 1, 0])), 1 / 3, "the OCCLUDED px is skipped");
  assert.equal(iou(Uint8Array.from([1, 0]), Int32Array.from([3, -1]), { ids: true }), 1, "part-id rasters: -1 = background");
});

test("V5-1 item 1: compare = fit = residuals — ONE registered IoU for the same module", async () => {
  await K.init();
  const S = loadSubject("facade_brick");
  const img = await readRGB(S.paths.target);
  const proj = await project({ subjectId: "facade_brick", modulePath: FACADE, frame: "target", size: img.w });
  const compare = registeredIoU(S, img, proj.foreground());                      // render-module / composeSheet
  const fitWhole = score(await fitTarget(S, img.w), proj, S).whole;               // FIT score, full resolution
  const res = await residuals({ subjectId: "facade_brick", modulePath: FACADE });  // residual rows / loop guard
  assert.equal(Math.round(compare * 1e4) / 1e4, res.registeredIoU);
  assert.equal(fitWhole, compare);
  assert.ok(compare > 0.9, `occlusion-masked facade IoU ${compare} (whole-image 0.40, subject-only 0.70)`);
});

test("V5-1 item 2: similarity + free W/H/D, massing first — the facade IoU rises well above the locked fit", async () => {
  fs.mkdirSync(TMP, { recursive: true });
  const start = path.join(TMP, "facade-sim.mjs");
  placeModule(addFrameKnobs(generateForSubject("facade_brick", { knobs: true }).text), start);
  const text = fs.readFileSync(start, "utf8");
  assert.match(text, /frameScale: \{ v: 1,/);
  assert.equal(addFrameKnobs(text), text, "idempotent");
  const r = await fit({ subjectId: "facade_brick", modulePath: start, out: path.join(TMP, "facade-sim-fit.mjs"), evals: 120 });
  assert.equal(r.sweeps[0].stage, "massing");
  assert.ok(r.end.registeredIoU >= 0.97 && r.end.registeredIoU >= r.start.registeredIoU + 0.02, `${r.start.registeredIoU} -> ${r.end.registeredIoU}`);
  assert.ok(Object.keys(r.knobs).some((n) => /^frame|^[WHD]$/.test(n)), JSON.stringify(Object.keys(r.knobs)));
});

test("V5-1 bug (a): the wall clock is enforced inside FIT and the loop (no stage runs unbounded)", async () => {
  const t = performance.now();
  const r = await fit({ subjectId: "facade_brick", modulePath: FACADE, evals: 300, deadline: performance.now() });
  assert.equal(r.timedOut, true);
  assert.ok(r.evals <= 2, `${r.evals} evals past the deadline`);
  assert.ok(performance.now() - t < 60000);
  const dir = path.join(TMP, "time");
  const script = path.join(TMP, "time-script.json");
  fs.writeFileSync(script, JSON.stringify([{ reply: "CHANGE: must not be called" }]));
  process.env.LLMM_FAKE_SCRIPT = script;
  try {
    const lr = await runLoop({ subjectId: "pickup", seat: "fake", images: false, turnaround: false, outDir: path.join(dir, "out"), workDir: path.join(dir, "work"), log: () => {}, timeMs: 1, exactStop: false, targetBand: 1.01 });
    assert.match(lr.stop, /^time/);
    assert.deepEqual(lr.steps.map((s) => s.step), ["start"]);
    assert.equal(lr.seatCalls.length, 0);
  } finally { delete process.env.LLMM_FAKE_SCRIPT; }
});

test("V5-1 bug (b): a rejected edit is named in the next prompt and an identical re-send is refused unscored; accuracy.json per step", async () => {
  fs.mkdirSync(TMP, { recursive: true });
  const text = fs.readFileSync(path.join(ROOT, WORK), "utf8");
  assert.ok(text.includes("const roofY = 0.962 * H;"));
  const edited = path.join(TMP, "roof-down.mjs");
  placeModule(text.replace("const roofY = 0.962 * H;", "const roofY = 0.85 * H;"), edited);
  const dir = path.join(TMP, "repeat");
  const script = path.join(TMP, "repeat-script.json");
  fs.writeFileSync(script, JSON.stringify([{ module: edited }]));   // the same complete module on every call
  process.env.LLMM_FAKE_SCRIPT = script;
  let r;
  try {
    r = await runLoop({ subjectId: "pickup", seat: "fake", images: false, turnaround: false, from: WORK, K: 2, outDir: path.join(dir, "out"), workDir: path.join(dir, "work"), log: () => {}, exactStop: false, similarity: false, targetBand: 1.01 });
  } finally { delete process.env.LLMM_FAKE_SCRIPT; }
  const out = path.join(dir, "out");
  // the work module lacks READY features, so BUILD takes the first send
  const v1 = JSON.parse(fs.readFileSync(path.join(out, "build", "verdict.json"), "utf8"));
  const v2 = JSON.parse(fs.readFileSync(path.join(out, "1", "verdict.json"), "utf8"));
  assert.equal(v1.accepted, false, v1.verdict);
  assert.ok(v1.iou !== null, "the first send was scored");
  assert.match(v2.verdict, /the same edit as step build, already rejected/);
  assert.equal(v2.iou, null, "the re-send was not re-scored");
  const p2 = fs.readFileSync(path.join(out, "1", "prompt.md"), "utf8");
  assert.match(p2, /ALREADY TRIED AND REJECTED/);
  assert.match(p2, /const roofY = 0\.85 \* H;/);
  assert.equal(r.stop, "2 consecutive rejects");
  const acc = JSON.parse(fs.readFileSync(path.join(out, "start", "accuracy.json"), "utf8"));
  assert.match(acc.summary, /^\d+ of \d+ items exact/);
  assert.ok(Array.isArray(acc.items) && acc.items.length > 5 && Array.isArray(acc.unowned));
  for (const k of ["id", "kind", "count", "pos", "size", "roiIoU", "edgePx", "dE", "status"]) assert.ok(k in acc.items[0], k);
  assert.match(JSON.parse(fs.readFileSync(path.join(out, "start", "verdict.json"), "utf8")).accuracy, /items exact/);
  assert.equal(editSummary("a\nb", "a\nc"), "`c`");
});

test("V5-1 items 3/4: render-as-target is exact on every seen item; bus markers are MISSING (needs helper); pickup unowned blobs", async () => {
  await K.init();
  // the noise floor: the module's own flat render measured AS the target
  const S = loadSubject("pickup");
  const img = await readRGB(S.paths.target);
  const proj = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: img.w });
  const self = await accuracy({ subjectId: "pickup", modulePath: WORK, target: flatRender(proj) });
  const seen = self.items.filter((r) => r.status !== "blind" && r.status !== "missing");
  assert.ok(seen.length >= 10, `${seen.length} seen items`);
  for (const r of seen) assert.equal(r.status, "exact", `${r.id}: ${r.fails?.join(", ")}`);
  // V5-5 item 4: the floor render (ink stroke + AA + shade) gives a real, non-zero floor; the alignment bounds its pos
  assert.ok(self.noiseFloor.posPx > 0 && self.noiseFloor.posPx <= 3, JSON.stringify(self.noiseFloor.posPx));
  const real = await accuracy({ subjectId: "pickup", modulePath: WORK });
  assert.match(real.summary, /^\d+ of \d+ items exact/);
  assert.equal(real.exact, false);
  assert.ok(real.unowned.length >= 1 && real.unowned.every((u) => u.px >= 60), JSON.stringify(real.unowned.slice(0, 2)));
  const busFile = path.join(TMP, "bus-start.mjs");
  placeModule((await import("../scripts/template-vehicle.mjs")).generateForSubject("school_bus").text, busFile);
  const bus = await accuracy({ subjectId: "school_bus", modulePath: busFile, floor: false });
  const marker = bus.items.find((r) => r.id === "marker");
  // V5-3: the marker lamps have a helper now (lamp face "cap"): the MISSING row names its READY call, no `needs helper` left
  assert.ok(marker && marker.status === "missing" && /^READY: markers/.test(marker.build), JSON.stringify(marker));
  assert.ok(!bus.items.some((r) => /needs helper/.test(r.build ?? "")), "every bus inventory item has a helper");
  assert.ok(bus.items.some((r) => r.status === "missing" && /^READY: /.test(r.build)), "a missing feature with a helper names its READY call");
  assert.equal(groupOf("wheel_fl"), "wheel");
  assert.equal(groupOf("window_0_1_frame"), "window_frame");
  // the exact stop is configurable: an inexact module never reaches target with it on
  const m = { loads: true, pass: true, coverage: { frac: 1 }, iou: 0.99, zoneRows: [], shown: [], accuracy: { exact: false } };
  assert.equal(atTarget(m, null, 0.97), true);
  assert.equal(atTarget(m, null, 0.97, { exact: true }), false);
});

test("V5-1: the live subject modules are byte-identical", () => {
  assert.deepEqual(LIVE.map(hash), liveBefore);
});
