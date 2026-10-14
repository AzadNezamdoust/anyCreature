// WORKFLOW v5 — V5-4 (research/WF-V5-ACCURACY.md): item 1 the ROI projection window, item 2 the per-feature FIT,
// item 3 the per-face palette {top, front, side}, item 4 the per-family noise floor.
// Hermetic: fixtures under test/fixtures/v4, refs/ subjects/ classes/ read only; writes under test/.tmp-wf-v54-<pid>/.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { FACES, NO_FACE, faceOf, project } from "../scripts/project.mjs";
import { accuracy, faceHex, featureScore, flatRender, paletteRegions, targetOf } from "../scripts/accuracy.mjs";
import { calibrateFaces } from "../scripts/calibrate-palette.mjs";
import { fitFeatures } from "../scripts/fit.mjs";
import { placeModule } from "../scripts/loop.mjs";
import { partFamilies } from "../scripts/residuals.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TMP = path.join(ROOT, "test", `.tmp-wf-v54-${process.pid}`);
const FACADE = "test/fixtures/v4/start-knobs-facade.mjs";
const WORK = "test/fixtures/v4/work-pickup.mjs";
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

test("V5-4 item 1: the ROI window is the full-resolution frame cropped (part ids and face ids), at 1 target px per px", async () => {
  await K.init();
  const full = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 1024 });
  const roi = { x0: 300, y0: 280, x1: 520, y1: 430 };
  const win = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 1024, roi });
  assert.deepEqual([win.w, win.h], [221, 151]);
  assert.deepEqual(win.roi, roi);
  let diff = 0;
  for (let y = 0; y < win.h; y += 1) for (let x = 0; x < win.w; x += 1) {
    const i = y * win.w + x;
    const j = (y + roi.y0) * full.w + x + roi.x0;
    if (win.partId[i] !== full.partId[j] || win.face[i] !== full.face[j]) diff += 1;
  }
  assert.equal(diff, 0);
  const seen = new Set();
  for (let i = 0; i < full.face.length; i += 1) if (full.partId[i] >= 0) { assert.notEqual(full.face[i], NO_FACE); seen.add(FACES[full.face[i]]); }
  for (const f of ["top", "front", "side"]) assert.ok(seen.has(f), `face ${f} visible`);
  assert.equal(faceOf(0, 1, 0), 0);
  assert.equal(faceOf(1, 0, 0.2), 1);
  assert.equal(faceOf(0.2, 0, -1), 2);
  await assert.rejects(project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 512, roi }), /roi needs frame/);
});

test("V5-4 items 3/4: per-face palette sampled in the registered frame; flat render by face; per-family floor tight", async () => {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, "facade.mjs");
  placeModule(fs.readFileSync(path.join(ROOT, FACADE), "utf8"), file);
  const r = await calibrateFaces({ subjectId: "facade_brick", modulePath: file });
  const brick = r.zones.brick;
  assert.ok(brick.faces.front && brick.faces.side, JSON.stringify(brick));
  assert.ok(brick.splitDE > 2 && /^\{ front: "#[0-9a-f]{6}", side: "#[0-9a-f]{6}" \}$/.test(brick.entry), brick.entry);
  const text = fs.readFileSync(file, "utf8");
  assert.match(text, /brick: \{ front: "#[0-9a-f]{6}", side: "#[0-9a-f]{6}" \},/);
  const again = await calibrateFaces({ subjectId: "facade_brick", modulePath: file });
  assert.equal(again.changed, false, "deterministic: a second pass writes nothing");
  // faceHex + the flat render paint by face
  const entry = { front: "#a75642", side: "#843c2f" };
  assert.equal(faceHex(entry, 1), "#a75642");
  assert.equal(faceHex(entry, 3), "#843c2f");
  assert.equal(faceHex(entry, 0), "#a75642");
  assert.equal(faceHex("#123456", 2), "#123456");
  const proj = await project({ subjectId: "facade_brick", modulePath: file, frame: "target", size: 1024 });
  const flat = flatRender(proj);
  const cols = new Set();
  const bi = proj.parts.map((p) => p.zone === "brick");
  for (let i = 0; i < proj.partId.length; i += 1) if (proj.partId[i] >= 0 && bi[proj.partId[i]]) cols.add(flat.data.slice(i * 3, i * 3 + 3).join(","));
  assert.ok(cols.size >= 2, "the brick zone paints two face colours");
  // the per-face colours classify to the zone's region
  const S = loadSubject("facade_brick");
  assert.ok(paletteRegions(S, proj.meta.palette).zones["brick_front~side"]);
  // per-family floor: tight on the facade (V5-1: posPx 81.8 / sizePx 125 / roiIoU 0.52). V5-8 R1: measured on a
  // REGISTERED module (the fake loop's fitted start under the re-solved camera, test/fixtures/v58/fitted-facade.mjs):
  // the floor keeps the real target's don't-care band, so an unfitted start's self-IoU depends on how far the camera
  // leaves it from the target (the raw template start read wall 0.86 at phi 46.91, 0.91 at the old swapped phi 43.09).
  const fitted = path.join(TMP, "fitted.mjs");
  placeModule(fs.readFileSync(path.join(ROOT, "test/fixtures/v58/fitted-facade.mjs"), "utf8"), fitted);
  const acc = await accuracy({ subjectId: "facade_brick", modulePath: fitted });
  const fams = acc.noiseFloor.families;
  assert.ok(fams.brick && fams.iron, Object.keys(fams).join(","));
  // V5-5 item 4: the floor render carries ink strokes + AA + shade, so the floor is REAL (non-zero) yet bounded; the
  // 1-3 px ironwork sits under the 2-px stroke (its rows are untrusted / blind: sub-3-px features, diagnosis)
  for (const f of ["brick", "glass"]) assert.ok(fams[f].trusted >= 1 && fams[f].posPx <= 3 && fams[f].sizePx <= 6 && fams[f].roiIoU >= 0.9, `${f} ${JSON.stringify(fams[f])}`);
  assert.ok(fams.iron.trusted + fams.iron.untrusted >= 1, JSON.stringify(fams.iron));
  assert.ok(Object.values(fams).some((f) => f.posPx > 0), "a real, non-zero floor");
  assert.ok(Array.isArray(acc.noiseFloor.untrusted));
  const wall = acc.items.find((x) => x.id.startsWith("wall"));
  assert.ok(wall && wall.dEFaces && Object.keys(wall.dEFaces).length >= 1, JSON.stringify(wall));
});

test("V5-4 item 2: featureScore is perfect on render-as-target; the per-feature FIT holds whole IoU and never lowers exact", async () => {
  const S = loadSubject("pickup");
  const full = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 1024 });
  const self = flatRender(full);
  const rep = await accuracy({ subjectId: "pickup", modulePath: WORK, target: self, floor: false });
  const row = rep.items.find((x) => x.feature && x.px.target >= 400);
  const TS = targetOf(S, self, { polygon: false, palette: full.meta.palette });
  const b = row.feature.box;
  const win = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 1024, roi: { x0: b.x0 - 6, y0: b.y0 - 6, x1: b.x1 + 6, y1: b.y1 + 6 } });
  const f = featureScore(win, TS, row.feature, partFamilies(S, win.parts, TS));
  assert.equal(f.roiIoU, 1, JSON.stringify(f));
  assert.equal(f.chamferPx, 0);
  assert.equal(f.score, 1);

  fs.mkdirSync(TMP, { recursive: true });
  const out = path.join(TMP, "facade-feat.mjs");
  const start = path.join(TMP, "facade-start.mjs");
  placeModule(fs.readFileSync(path.join(ROOT, FACADE), "utf8"), start);
  await calibrateFaces({ subjectId: "facade_brick", modulePath: start });   // a calibrated palette: items are seen, not blind
  const r = await fitFeatures({ subjectId: "facade_brick", modulePath: start, out, evals: 30, perItem: 10 });
  assert.ok(r.evals <= 30 && r.items.length >= 3, JSON.stringify({ evals: r.evals, n: r.items.length, skipped: r.skipped }));
  assert.ok(r.wholeFit[1] >= r.wholeFit[0] - 0.0003 - 1e-9, JSON.stringify(r.wholeFit));
  const tried = r.items.filter((it) => it.before);
  assert.ok(tried.length >= 1 && tried.every((it) => it.after.score >= it.before.score), JSON.stringify(tried.map((it) => [it.id, it.before.score, it.after.score])));
  if (r.kept) {
    assert.ok(r.registeredIoU[1] >= r.registeredIoU[0] - 0.0005);
    const [a, b2] = [r.exact.before, r.exact.after].map((s) => Number(/^(\d+) of/.exec(s)[1]));
    assert.ok(b2 >= a, `${r.exact.before} -> ${r.exact.after}`);
  }
  assert.ok(fs.existsSync(out));
});
