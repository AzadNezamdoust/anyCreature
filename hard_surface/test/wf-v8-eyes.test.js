// WF v8 WP1 — the eyes: drift rects -> agree-IoU (ortho viewTarget / viewScore, concept targetState dontCare) and the
// blob table (judge.mjs blobTable). Hermetic: synthetic rasters only, reads and writes nothing.
import test from "node:test";
import assert from "node:assert/strict";

import { OCCLUDED, SUBJECT, careMask, iou, targetState } from "../scripts/registered.mjs";
import { driftOf, driftRects, maskOptions, viewDrift, viewScore, viewTarget } from "../scripts/v6/ortho.mjs";
import { blobLine, blobTable, driftWarnings } from "../scripts/v6/judge.mjs";

/** A w x h RGB image, white, with the px of `dark(x, y)` black. */
function image(w, h, dark) {
  const data = Buffer.alloc(w * h * 3, 255);
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) if (dark(x, y)) data.fill(0, (y * w + x) * 3, (y * w + x) * 3 + 3);
  return { data, w, h, c: 3 };
}

test("careMask: half-open image-px rects, sampled at pixel centres like viewTarget", () => {
  assert.equal(careMask(null, 4, 4), null);
  assert.equal(careMask([], 4, 4), null);
  const same = careMask([[1, 0, 3, 2]], 4, 3);
  assert.deepEqual([...same], [1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1]);
  // 10 x 10 image sampled at 5 x 5: raster px x reads image px 2x + 1; rect [2, 2, 6, 6] holds image px 2..5
  const down = careMask([[2, 2, 6, 6]], 5, 5, 10, 10);
  const zero = [];
  for (let i = 0; i < 25; i += 1) if (!down[i]) zero.push([i % 5, Math.floor(i / 5)]);
  assert.deepEqual(zero, [[1, 1], [2, 1], [1, 2], [2, 2]]);
  assert.throws(() => careMask([[3, 0, 3, 2]], 4, 4), /x1 > x0/);
  assert.throws(() => careMask([[0, 0, 2]], 4, 4), /not \[x0, y0, x1, y1\]/);
});

test("targetState dontCare: every px in the rects is OCCLUDED, iou leaves them out of I and U; maskOptions never adds it", () => {
  const img = image(6, 4, (x, y) => x >= 1 && x <= 3 && y >= 1 && y <= 2);
  const raw = targetState(null, img);
  const st = targetState(null, img, 235, { dontCare: [[2, 0, 5, 2]] });
  const at = (m, x, y) => m[y * 6 + x];
  assert.equal(at(raw, 2, 1), SUBJECT);
  assert.equal(at(st, 1, 1), SUBJECT);      // fg outside the rect
  assert.equal(at(st, 2, 1), OCCLUDED);     // fg inside
  assert.equal(at(st, 4, 0), OCCLUDED);     // background inside: the model is not scored there either
  assert.equal(at(st, 5, 0), 0);
  assert.equal(at(st, 3, 2), SUBJECT);      // y1 is exclusive
  // model = the fg px plus an extra px inside the rect and one outside
  const model = Uint8Array.from(raw, (v) => (v ? 1 : 0));
  model[0 * 6 + 4] = 1;
  model[3 * 6 + 5] = 1;
  assert.equal(iou(raw, model), 6 / 8);
  assert.equal(iou(st, model), 4 / 5);      // I: (1,1) (1,2) (2,2) (3,2); U + (5,3)
  assert.deepEqual(targetState(null, img, 235, { dontCare: null }), raw);
  assert.equal("dontCare" in maskOptions({ drift: { concept: [{ rect: [0, 0, 1, 1] }] } }, "concept"), false);
});

test("viewScore: agree drops the care-0 px from I and U; = iou without a care raster", () => {
  const table = { zoneFams: [], names: ["bg", "body", "other"] };
  const T = { fg: Uint8Array.from([1, 1, 0, 0]), fam: new Uint8Array(4), care: null };
  const partId = Int32Array.from([0, -1, 0, -1]);
  const a = viewScore(T, partId, Int32Array.from([1]), table);
  assert.equal(a.iou, 1 / 3);
  assert.equal(a.agree, a.iou);
  const b = viewScore({ ...T, care: Uint8Array.from([1, 0, 1, 1]) }, partId, Int32Array.from([1]), table);
  assert.equal(b.iou, 1 / 3);
  assert.equal(b.agree, 1 / 2);
});

test("viewTarget / viewDrift: the view's drift rects map to the judge raster; the share is of the reference fg", () => {
  const fam = new Uint8Array(100);
  for (let y = 0; y < 10; y += 1) for (let x = 0; x < 5; x += 1) fam[y * 10 + x] = 1;   // fg: x 0..4 (50 px)
  const reg = { s: 1, views: { side: { img: { w: 10, h: 10, fam }, ox: 0, oy: 0 } }, table: { drift: { side: [{ id: "D1", rect: [2, 2, 6, 6] }] } } };
  const T = viewTarget(reg, "side", 5);
  assert.deepEqual([T.w, T.h], [5, 5]);
  assert.deepEqual([...T.care], [...careMask([[2, 2, 6, 6]], 5, 5, 10, 10)]);
  assert.equal(viewDrift(reg, "side"), 12 / 50);    // fg px x 2..4, y 2..5
  const plain = { s: 1, views: reg.views, table: { drift: null } };
  assert.equal(viewTarget(plain, "side", 5).care, null);
  assert.equal(viewDrift(plain, "side"), 0);
});

test("driftOf: notes ignored, rects validated, unknown views refused", () => {
  const views = { side: { file: "s.png" } };
  assert.equal(driftOf({ views }), null);
  const d = driftOf({ views, drift: { audited: "2026-09-28", side: [{ id: "D1", rect: [1, 2, 3, 4], decides: "concept", why: "w" }], concept: [{ rect: [0, 0, 5, 5] }] } });
  assert.deepEqual(Object.keys(d), ["side", "concept"]);
  assert.deepEqual(d.side[0], { id: "D1", rect: [1, 2, 3, 4], decides: "concept", why: "w" });
  assert.equal(d.concept[0].id, "concept1");
  assert.deepEqual(driftRects({ drift: d }, "side"), [[1, 2, 3, 4]]);
  assert.equal(driftRects({ drift: d }, "front"), null);
  assert.equal(driftRects(null, "side"), null);
  assert.throws(() => driftOf({ views, drift: { rear: [{ rect: [0, 0, 1, 1] }] } }), /drift\.rear is not an image/);
  assert.throws(() => driftOf({ views, drift: { side: [{ id: "D9", rect: [4, 0, 1, 1] }] } }), /D9/);
  assert.throws(() => driftOf({ views, drift: [] }), /must be an object/);
});

test("blobTable: opening, min size, care, top-N, part attribution (extra = mode, missing = nearest part)", () => {
  const w = 40, h = 30;
  const refFg = new Uint8Array(w * h);
  const partId = new Int32Array(w * h).fill(-1);
  const box = (m, x0, y0, x1, y1, v) => { for (let y = y0; y <= y1; y += 1) for (let x = x0; x <= x1; x += 1) m[y * w + x] = v; };
  box(partId, 5, 5, 24, 19, 0);      // body (also in the reference)
  box(refFg, 5, 5, 24, 19, 1);
  box(partId, 25, 8, 29, 11, 1);     // mirror: model only, 20 px -> "extra"
  box(partId, 32, 25, 35, 28, 2);    // tiny: model only, 16 px -> under BLOB_MIN_PX
  box(refFg, 5, 20, 14, 24, 1);      // missing under the body, 50 px -> nearest part body
  box(refFg, 32, 8, 36, 13, 1);      // missing, detached, 30 px -> nearest part mirror
  box(refFg, 3, 5, 4, 19, 1);        // 2 px wide outline strip, 30 px -> opened away
  box(refFg, 18, 25, 23, 29, 1);     // missing, 30 px, inside the care-0 rect -> not reported
  const care = new Uint8Array(w * h).fill(1);
  box(care, 17, 24, 24, 29, 0);
  const modelFg = Uint8Array.from(partId, (p) => (p >= 0 ? 1 : 0));
  const parts = [{ id: "body" }, { id: "mirror" }, { id: "tiny" }];
  const place = (b) => ({ bbox: [b.x0, b.y0, b.x1 + 1, b.y1 + 1], centroid: [b.cx + 0.5, b.cy + 0.5] });
  const refPx = refFg.reduce((a, v) => a + v, 0);
  const rows = blobTable({ refFg, modelFg, partId, w, h, care, parts, refPx, place });
  assert.deepEqual(rows.map((r) => [r.kind, r.px, r.part]), [["missing", 50, "body"], ["missing", 30, "mirror"], ["extra", 20, "mirror"]]);
  assert.deepEqual(rows[0].bbox, [5, 20, 15, 25]);
  assert.deepEqual(rows[0].centroid, [10, 22.5]);
  assert.equal(rows[0].share, Math.round(50 / refPx * 1e4) / 1e4);
  // no care: the masked block comes back; no opening: the strip comes back; top 1 per kind
  assert.ok(blobTable({ refFg, modelFg, partId, w, h, parts, refPx, place }).some((r) => r.bbox[0] === 18));
  assert.ok(blobTable({ refFg, modelFg, partId, w, h, care, parts, refPx, place, open: 0 }).some((r) => r.bbox[0] === 3 && r.px === 30));
  assert.deepEqual(blobTable({ refFg, modelFg, partId, w, h, care, parts, refPx, place, top: 1 }).map((r) => r.px), [50, 20]);
  // a raster without model px: the missing blobs have no part
  assert.equal(blobTable({ refFg, modelFg: new Uint8Array(w * h), partId: new Int32Array(w * h).fill(-1), w, h, care, parts, refPx, place })[0].part, null);
  assert.match(blobLine("concept", rows[0]), /^blob concept missing 50 px [\d.]+ % · px x 5\.\.15 y 20\.\.25 · at \(10, 23\) · nearest part body$/);
  assert.match(blobLine("side", { kind: "extra", px: 20, share: 0.01, bbox: { right: [1, 1.2], up: [0.3, 0.5] }, centroid: [1.1, 0.4], part: "mirror" }),
    /^blob side extra 20 px 1\.00 % · right 1\.000\.\.1\.200 up 0\.300\.\.0\.500 m · at \(1\.100, 0\.400\) · part mirror$/);
});

test("driftWarnings: views over the 5 % bound", () => {
  assert.deepEqual(driftWarnings({ views: { side: { drift: 0.05 }, top: { drift: 0.0501 }, concept: { iou: 0.9 } } }).map((l) => l.split(":")[0]), ["WARN drift top"]);
});
