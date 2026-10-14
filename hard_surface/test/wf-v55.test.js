// WORKFLOW v5 — V5-5 (research/WF-V5-ACCURACY.md "Exactness diagnosis"): the accuracy metric measures the model, not
// its own artefacts — anchor-fraction tolerances + size-aware IoU floor (item 1), ink strip (item 2), target components
// touching the dilated render (item 3), a real noise floor (item 4), per-item alignment (item 7).
import test from "node:test";
import assert from "node:assert/strict";

import * as K from "../src/kernel/index.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { project } from "../scripts/project.mjs";
import { INK, SPEC, accuracy, flatRender, judgeRow, targetOf } from "../scripts/accuracy.mjs";

const WORK = "test/fixtures/v4/work-pickup.mjs";

test("V5-5 item 1: tolerances are anchor fractions; the IoU floor is size-aware; small items are judged by the edge", () => {
  assert.equal(SPEC.posFrac, 0.015);
  assert.equal(SPEC.sizeFrac, 0.02);
  assert.equal(SPEC.dE, 6);
  assert.equal(SPEC.edgePx, 2.5);
  assert.equal(SPEC.bigPx, 4000);
  const row = (px, iou, edgePx = null) => ({ pos: { dxPx: 10, dyPx: -10 }, size: { dwPx: 15, dhPx: 0, target: [100, 100] }, px: { target: px }, count: { target: null }, roiIoU: iou, edgePx, dE: 5 });
  const A = 870;   // pickup anchor px (4.8 m x ~181 px/m): pos tol 13.05, size tol 17.4
  const big = judgeRow(row(40000, 0.96), null, SPEC, A);
  const D = 2 * Math.sqrt(40000 / Math.PI);
  assert.equal(big.tol.iou, Math.round(1000 * (1 - 8 / D)) / 1000);
  assert.equal(big.tol.posPx, 13.05);
  assert.equal(big.tol.sizePx, 17.4);
  assert.deepEqual(big.fails, ["roiIoU"]);    // 0.96 < 1 - 8 / 225.7
  assert.equal(judgeRow(row(5000, 0.91), null, SPEC, A).status, "exact");   // D 79.8: floor 1 - 8 / 79.8 = 0.9
  assert.deepEqual(judgeRow(row(4000, 0.88), null, SPEC, A).fails, ["roiIoU"]);   // D 71.4: floor 0.888

  const small = judgeRow(row(900, 0.2, 2.4), null, SPEC, A);
  assert.equal(small.status, "exact", JSON.stringify(small));             // small: the edge chamfer, not the IoU
  assert.deepEqual(judgeRow(row(900, 1, 2.6), null, SPEC, A).fails, ["edge"]);
  assert.deepEqual(judgeRow({ ...row(900, 1, 1), dE: null, dESkipped: "no face interior" }, null, SPEC, A).fails, []);
  assert.deepEqual(judgeRow({ ...row(900, 1, 1), dE: null }, null, SPEC, A).fails, ["dE"]);
});

test("V5-5 items 2/3/4/7: ink strip is don't care; a real floor; aligned pos; a same-family blob in the pad is not the item", async () => {
  await K.init();
  const S = loadSubject("pickup");
  assert.equal(S.cls.likeness.inkOpen, 2);
  const full = await project({ subjectId: "pickup", modulePath: WORK, frame: "target", size: 1024 });
  const clean = flatRender(full);
  // item 4: the floor render is not the clean one (ink stroke, blur, shade)
  const floor = flatRender(full, { floor: true });
  let diff = 0, dark = 0;
  for (let i = 0; i < clean.data.length; i += 3) {
    if (clean.data[i] !== floor.data[i]) diff += 1;
    if (floor.data[i] < 60 && floor.data[i + 1] < 60 && floor.data[i + 2] < 60) dark += 1;
  }
  assert.ok(diff > 5000 && dark > 1000, `${diff} changed, ${dark} dark px`);
  // item 2: stripped px are INK and don't care; no strip without an opening radius
  const T = targetOf(S, floor, { polygon: false, palette: full.meta.palette });
  let ink = 0, careInk = 0;
  for (let i = 0; i < T.fam.length; i += 1) if (T.fam[i] === INK) { ink += 1; careInk += T.care[i]; }
  assert.ok(ink > 500 && careInk === 0, `${ink} ink px, ${careInk} cared`);
  assert.ok(!targetOf(S, floor, { polygon: false, palette: full.meta.palette, inkOpen: 0 }).fam.includes(INK));

  // item 7: the clean render as the target, shifted by (+2, -1) px -> every big item reads pos (-2, +1), IoU 1
  const w = clean.w, h = clean.h;
  const shifted = { ...clean, data: new Uint8Array(clean.data.length).fill(255) };
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
    const sx = x - 2, sy = y + 1;
    if (sx < 0 || sy >= h) continue;
    for (let c = 0; c < 3; c += 1) shifted.data[(y * w + x) * 3 + c] = clean.data[(sy * w + sx) * 3 + c];
  }
  const rep = await accuracy({ subjectId: "pickup", modulePath: WORK, target: shifted, floor: false });
  const bigRows = rep.items.filter((r) => r.pos && r.px.target >= SPEC.bigPx);
  // (an item whose same-family neighbours cut its target — the "other part draws it" mask is the unshifted render —
  // may align short; most must not)
  const aligned = bigRows.filter((r) => Math.abs(r.pos.dxPx + 2) <= 0.5 && Math.abs(r.pos.dyPx - 1) <= 0.5 && r.shift[0] === 2 && r.shift[1] === -1 && r.roiIoU >= 0.97);
  for (const id of ["windshield[glass]", "bumper", "hub"]) assert.ok(aligned.some((r) => r.id === id), id);
  assert.ok(bigRows.length >= 3 && aligned.length >= 0.5 * bigRows.length, bigRows.map((r) => `${r.id} ${JSON.stringify(r.pos)} ${r.roiIoU}`).join("; "));

  // item 3: a blob of the item's own colour in its ROI pad, > 4 px from the render, never joins the item's target
  const base = await accuracy({ subjectId: "pickup", modulePath: WORK, target: clean, floor: false });
  const row = base.items.find((r) => r.id === "lamp" && r.pos);
  assert.ok(row, "the pickup lamp row");
  const ids = new Set(row.feature.partIds);
  const own = full.parts.map((p) => ids.has(p.id));
  let x1 = -1, y0 = Infinity, y1 = -1;
  for (let i = 0; i < full.partId.length; i += 1) if (full.partId[i] >= 0 && own[full.partId[i]]) { const x = i % w, y = (i / w) | 0; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  const b = row.feature.box;
  const bx = x1 + 7, by = Math.round((y0 + y1) / 2);
  assert.ok(bx + 3 <= b.x1, `pad room: blob at ${bx} inside ROI x1 ${b.x1}`);
  const painted = { ...clean, data: Uint8Array.from(clean.data) };
  const lampPx = (() => { for (let i = 0; i < full.partId.length; i += 1) if (full.partId[i] >= 0 && own[full.partId[i]]) return i; return -1; })();
  for (let y = by - 3; y <= by + 3; y += 1) for (let x = bx; x <= bx + 6; x += 1) for (let c = 0; c < 3; c += 1) painted.data[(y * w + x) * 3 + c] = clean.data[lampPx * 3 + c];
  const withBlob = await accuracy({ subjectId: "pickup", modulePath: WORK, target: painted, floor: false });
  const r2 = withBlob.items.find((r) => r.id === "lamp");
  assert.equal(r2.px.target, row.px.target, "the pad blob is not the lamp's target");
  assert.equal(r2.status, row.status);
});
