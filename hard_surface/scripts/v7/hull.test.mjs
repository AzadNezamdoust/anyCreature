// node --test scripts/v7/hull.test.mjs — scripts/v7/hull.mjs on a SYNTHETIC subject (hermetic: a temp dir, nothing under
// subjects/): a body box + a cab box + two full-width drums rendered orthographically (ortho.mjs rasterOrtho, the judge's
// rasteriser) into side / front / rear / top and, through a solved-style camera (registered.mjs cameraBasis + framed),
// into a concept — then registered and carved exactly as the CLI does (registerViewSet + hullReport).
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import sharp from "sharp";

import { cameraBasis, foregroundMask, framed, readRGB } from "../registered.mjs";
import { basisOf, familyTable, rasterOrtho } from "../v6/ortho.mjs";
import { residualRows } from "./steplib.mjs";
import { cameraExtent, foregroundBox, frameQuad, hullReport, registerViewSet, stripMeasured } from "./hull.mjs";

const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

/** A convex solid's mesh from vertices + face loops, every triangle wound outward (rasterOrtho culls back faces). */
function convexMesh(verts, faces) {
  const c = verts.reduce((a, v) => a.map((x, k) => x + v[k] / verts.length), [0, 0, 0]);
  const tris = [];
  for (const f of faces) {
    for (let i = 1; i + 1 < f.length; i += 1) {
      const t = [f[0], f[i], f[i + 1]];
      const [a, b, d] = t.map((j) => verts[j]);
      tris.push(...(dot(cross(sub3(b, a), sub3(d, a)), sub3(a, c)) < 0 ? [t[0], t[2], t[1]] : t));
    }
  }
  return { pos: Float64Array.from(verts.flat()), tris: Uint32Array.from(tris) };
}
const box = ([x0, y0, z0], [x1, y1, z1]) => convexMesh(
  [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]],
  [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]);
/** A drum (cylinder along x) of radius r at (y, z) = (yc, zc) from x0 to x1, n segments. */
function drum(yc, zc, r, x0, x1, n = 48) {
  const ring = (x) => Array.from({ length: n }, (_, k) => [x, yc + r * Math.cos(2 * Math.PI * k / n), zc + r * Math.sin(2 * Math.PI * k / n)]);
  const faces = [Array.from({ length: n }, (_, k) => k), Array.from({ length: n }, (_, k) => n + k)];
  for (let k = 0; k < n; k += 1) faces.push([k, (k + 1) % n, n + (k + 1) % n, n + k]);
  return convexMesh([...ring(x0), ...ring(x1)], faces);
}

// author frame (vehicle): nose +z, near flank +x, y up, ground y = 0. W (body span) 1.8 m, L 4 m, H 2.2 m.
const BODY = [47, 111, 208], DARK = [51, 51, 51];
const MESHES = [box([-0.9, 0.5, -2], [0.9, 1.7, 2]), box([-0.7, 1.7, 0.2], [0.7, 2.2, 1.6]), drum(0.45, 1.4, 0.45, -1, 1), drum(0.45, -1.4, 0.45, -1, 1)];
const COLOURS = [BODY, BODY, DARK, DARK];
const S = 100;   // px / m in every view
const VIEWS = {
  side: { file: "side.png", right: [0, 0, -1], up: [0, 1, 0] },
  front: { file: "front.png", right: [1, 0, 0], up: [0, 1, 0] },
  rear: { file: "rear.png", right: [-1, 0, 0], up: [0, 1, 0] },
  top: { file: "top.png", right: [0, 0, -1], up: [-1, 0, 0] },
};
const SIZE = { side: [520, 290, 260, 250], front: [320, 290, 160, 250], rear: [320, 290, 160, 250], top: [520, 280, 260, 140] };   // w, h, bx, by
const TABLE = familyTable([], { table: { body: "#2f6fd0", dark: "#333333" }, body: "body" });
const ANCHOR = { dim: "W", m: 1.8 };
const ORIGIN = { x: "centre", y: "min", z: "centre" };
// the concept: a solved-style orthographic camera, the registration's frame FRAMED by a known similarity
const CW = 660, CH = 600;
const basis = cameraBasis({ theta_deg: 30, phi_deg: 40 });
const toPx = (s, ox, oy, p) => [s * dot(p, basis.right) + ox, -s * dot(p, basis.up) + oy];
const CREG = { s: 110, ox: 330, oy: 440, basis, turnDeg: 0, targetW: CW, targetH: CH,
  quadPx: [[0.9, 1.7, 2], [0.9, 1.7, -2], [0.9, 0.5, -2], [0.9, 0.5, 2]].map((p) => toPx(110, 330, 440, p)) };
const TRUE_FRAME = { scale: 1.04, tx: 10, ty: -6 };

async function renderPng(file, b, map, w, h) {
  const { partId } = rasterOrtho(MESHES, b, map, w, h);
  const rgb = Buffer.alloc(w * h * 3, 255);
  for (let i = 0; i < w * h; i += 1) if (partId[i] >= 0) { const c = COLOURS[partId[i]]; rgb[i * 3] = c[0]; rgb[i * 3 + 1] = c[1]; rgb[i * 3 + 2] = c[2]; }
  await sharp(rgb, { raw: { width: w, height: h, channels: 3 } }).png().toFile(file);
}

/** Background px of a mask not 4-connected to the image border (pin holes / enclosed see-throughs). */
function enclosedBg(mask, w, h) {
  const seen = new Uint8Array(w * h);
  const st = [];
  const push = (i) => { if (!mask[i] && !seen[i]) { seen[i] = 1; st.push(i); } };
  for (let x = 0; x < w; x += 1) { push(x); push((h - 1) * w + x); }
  for (let y = 0; y < h; y += 1) { push(y * w); push(y * w + w - 1); }
  while (st.length) { const i = st.pop(), x = i % w; if (x > 0) push(i - 1); if (x < w - 1) push(i + 1); if (i >= w) push(i - w); if (i < w * h - w) push(i + w); }
  let n = 0;
  for (let i = 0; i < w * h; i += 1) if (!mask[i] && !seen[i]) n += 1;
  return n;
}

let dir = null;   // views + concept (consistent)
let bad = null;   // the same views, side.png drawn 10 % too long along its right axis
let tall = null;  // all four views of the object stretched 10 % in H (y), the concept unchanged
test.before(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "llmm-hull-"));
  bad = path.join(dir, "stretched");
  tall = path.join(dir, "tall");
  fs.mkdirSync(bad);
  fs.mkdirSync(tall);
  const TALL = { k: 1.1 };
  for (const [v, spec] of Object.entries(VIEWS)) {
    const [w, h, bx, by] = SIZE[v];
    await renderPng(path.join(dir, spec.file), basisOf(spec), { k: S, bx, by }, w, h);
    if (v === "side") await renderPng(path.join(bad, spec.file), basisOf({ ...spec, scale: { right: 1.1 } }), { k: S, bx, by }, w, h);
    else fs.copyFileSync(path.join(dir, spec.file), path.join(bad, spec.file));
    // y (H) scaled 1.1 about the ground: the up axis of side / front / rear drawn 1.1 x, the top view unchanged
    const b = basisOf(spec);
    await renderPng(path.join(tall, spec.file), v === "top" ? b : { ...b, up: b.up.map((c) => c * TALL.k) }, { k: S, bx, by: v === "top" ? by : by + 40 }, w, h + 50);
  }
  const fr = framed(CREG, TRUE_FRAME);
  await renderPng(path.join(dir, "concept.png"), basis, { k: fr.s, bx: fr.ox, by: fr.oy }, CW, CH);
});
test.after(() => { if (dir) fs.rmSync(dir, { recursive: true, force: true }); });

test("hull: four consistent views + their concept -> viewOnly ~ 0, conceptOnly ~ 0, the frame recovered, no pin holes", async () => {
  const reg = await registerViewSet({ views: VIEWS, dir, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  assert.ok(Math.abs(reg.s - S) < 0.01, `s ${reg.s}`);
  assert.equal(residualRows(reg.residuals)[0].level, "PASS");
  const cimg = await readRGB(path.join(dir, "concept.png"));
  const T = foregroundMask(cimg);
  const { report: R, rasters } = await hullReport({ reg, concept: { T, creg: CREG, w: CW, h: CH } });
  for (const [v, m] of Object.entries(R.views)) {
    assert.ok(m.viewOnly < 0.002, `${v} viewOnly ${m.viewOnly}`);
    assert.equal(m.viewOnlyBlob, 0, `${v} viewOnlyBlob`);
    assert.ok(m.iou > 0.97, `${v} IoU ${m.iou}`);
    assert.equal(m.blobs.length, 0, `${v} viewOnly blobs ${JSON.stringify(m.blobs)}`);
  }
  const C = R.concept;
  assert.ok(C.conceptOnly < 0.004, `conceptOnly ${C.conceptOnly}`);
  assert.equal(C.conceptOnlyBlob, 0);
  assert.equal(C.blobs.length, 0, `conceptOnly blobs ${JSON.stringify(C.blobs)}`);
  assert.ok(C.iou > 0.97, `concept IoU ${C.iou}`);
  assert.ok(C.hullOnly > 0.002, `hullOnly ${C.hullOnly} (the drums' square corners no axis view carves)`);
  // the IoU optimum of the SUPERSET hull (its drum corners) sits slightly smaller than the true frame (1.04, +10, -6):
  // measured 1.0305 +8.24 -6.98 — at the true frame conceptOnly is 0 and hullOnly 2.1 %, at the fit 0.28 % / 0.46 %
  const f = C.frame.fitted;
  assert.ok(Math.abs(f.scale - TRUE_FRAME.scale) < 0.015 && Math.abs(f.tx - TRUE_FRAME.tx) < 3 && Math.abs(f.ty - TRUE_FRAME.ty) < 3, JSON.stringify(f));
  assert.equal(enclosedBg(T, CW, CH), 0);   // the fixture's concept has no see-through
  assert.equal(enclosedBg(rasters.concept.hull, CW, CH), 0, "pin holes in the concept splat");
});

test("hull: a view drawn 10 % too long along its right axis -> viewOnly in that view, the residual row names it", async () => {
  const reg = await registerViewSet({ views: VIEWS, dir: bad, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  assert.ok(Math.abs(reg.residuals.L.side - 0.0476) < 0.002, `L residual side ${reg.residuals.L.side}`);
  const row = residualRows(reg.residuals).find((r) => r.id === "residual-L");
  assert.equal(row?.level, "BLOCK");
  assert.ok(Math.abs(row.data.side - 0.0476) < 0.002, JSON.stringify(row.data));
  const { report: R } = await hullReport({ reg });
  assert.ok(R.views.side.viewOnly > 0.03 && R.views.side.viewOnlyBlob > 0.03, `side viewOnly ${R.views.side.viewOnly} / ${R.views.side.viewOnlyBlob}`);
  for (const v of ["front", "rear", "top"]) assert.ok(R.views[v].viewOnly < 0.002 && R.views[v].viewOnlyBlob === 0, `${v} viewOnly ${R.views[v].viewOnly}`);
  // the two ends of the stretched body: the top view carves everything beyond z = +-2 m (right -2.2..-2 and 2..2.2 m)
  const ends = R.views.side.blobs.slice(0, 2).map((b) => b.right).sort((a, b) => a[0] - b[0]);
  assert.equal(ends.length, 2);
  assert.ok(ends[0][0] < -2.1 && ends[0][1] <= -1.98 && ends[1][0] >= 1.98 && ends[1][1] > 2.1, JSON.stringify(ends));
});

test("hull: views.json scale honoured on the live set, ignored with --views-dir (stripMeasured)", async () => {
  const views = { ...VIEWS, side: { ...VIEWS.side, scale: { right: 1.1 }, _scale: "measured on the live images" } };
  const live = await registerViewSet({ views, dir: bad, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  assert.ok(Math.abs(live.residuals.L.side) < 0.002, `live L residual side ${live.residuals.L.side}`);
  assert.ok((await hullReport({ reg: live })).report.views.side.viewOnly < 0.002);
  const spec = { views, families: { holes: { side: [[1, 1]], concept: [[5, 5]] } }, drift: { side: [{ id: "D1", rect: [0, 0, 4, 4] }], audited: "x" } };
  const st = stripMeasured(spec);
  assert.deepEqual(st.dropped, ["side.scale", "holes.side", "drift.side"]);
  assert.deepEqual(st.views.side, VIEWS.side);
  assert.deepEqual(st.holes, { concept: [[5, 5]] });
  const vd = await registerViewSet({ views: st.views, dir: bad, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  assert.ok((await hullReport({ reg: vd })).report.views.side.viewOnly > 0.03);
});

test("hull --aniso: the views' object stretched 10 % in H against an unchanged concept -> aspect H/W +10 % (+-1.5), L/W 0 (+-1.5); a consistent set -> both within +-1.5 %", async (t) => {
  const cimg = await readRGB(path.join(dir, "concept.png"));
  const T = foregroundMask(cimg);
  const concept = { T, creg: CREG, w: CW, h: CH };
  const consistent = await registerViewSet({ views: VIEWS, dir, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  const R0 = (await hullReport({ reg: consistent, concept, aniso: true })).report;
  assert.ok(Math.abs(R0.aspect.HoverW) <= 0.015 && Math.abs(R0.aspect.LoverW) <= 0.015, `consistent aspect ${JSON.stringify(R0.aspect)}`);
  assert.ok(R0.concept.aniso.iou >= R0.concept.iou - 0.002, `aniso IoU ${R0.concept.aniso.iou} vs isotropic ${R0.concept.iou}`);
  const reg = await registerViewSet({ views: VIEWS, dir: tall, table: TABLE, anchor: ANCHOR, origin: ORIGIN });
  assert.ok(Math.abs(reg.dims.H / 2.2 - 1.1) < 0.01, `registered H ${reg.dims.H} (want 2.42)`);
  const { report: R } = await hullReport({ reg, concept, aniso: true });
  assert.ok(Math.abs(R.aspect.HoverW - 0.1) <= 0.015, `aspect H/W ${R.aspect.HoverW} (want +0.10)`);
  assert.ok(Math.abs(R.aspect.LoverW) <= 0.015, `aspect L/W ${R.aspect.LoverW} (want 0)`);
  // the per-axis scales: the views' object over the concept's (the concept is the true frame's 1.04 x): W, L ~ 1 / 1.04, H ~ 1.1 / 1.04
  const A = R.concept.aniso;
  t.diagnostic(`consistent aspect H/W ${R0.aspect.HoverW} L/W ${R0.aspect.LoverW} · stretched H/W ${R.aspect.HoverW} L/W ${R.aspect.LoverW} · scale ${JSON.stringify(A.scale)} · IoU iso ${R.concept.iou} aniso ${A.iou}`);
  assert.ok(Math.abs(A.scale.H / A.scale.W - 1.1) <= 0.015 && A.iou > R.concept.iou + 0.01, JSON.stringify({ scale: A.scale, aniso: A.iou, iso: R.concept.iou }));
});

test("--write-frame: the extent fitted to the concept bbox; registered.mjs registration() recovers s / ox / oy from the quad (rms 0)", async () => {
  const { anchorFace, registration, subjectFront, turnFn } = await import("../registered.mjs");
  const { frontRotationDeg } = await import("../../src/kernel/toThree.mjs");
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "hull-frame-"));
  const camera = { theta_deg: 25.08, phi_deg: 44.89 };
  const camFile = path.join(dir, "camera.json");
  fs.writeFileSync(camFile, JSON.stringify(camera));
  const basis = cameraBasis(camera);
  const S0 = { klass: "vehicle", readJson: () => null };
  const turn = turnFn(frontRotationDeg(subjectFront(S0)));
  // a 3.2 x 1.2 x 2.2 m box: its projected extent, the frame for a bbox of 783 x 709 px
  const pts = [];
  for (const x of [-0.6, 0.6]) for (const y of [0, 2.2]) for (const z of [-1.6, 1.6]) pts.push([x, y, z]);
  const ext = cameraExtent(pts, basis, turn);
  assert.ok(ext.a1 > ext.a0 && ext.b1 > ext.b0);
  const padded = cameraExtent(pts, basis, turn, [0.1, 0.2]);
  assert.ok(Math.abs(padded.a0 - (ext.a0 - 0.1)) < 1e-12 && Math.abs(padded.b1 - (ext.b1 + 0.2)) < 1e-12);
  const bbox = [98, 150, 881, 859];
  const fit = frameQuad({ ext, bbox, corners: anchorFace(S0).corners, basis, turn });
  assert.ok(Math.abs(fit.s - (fit.sx + fit.sy) / 2) < 1e-12);
  // the extent's centre lands on the bbox centre
  assert.ok(Math.abs(fit.s * (ext.a0 + ext.a1) / 2 + fit.ox - (bbox[0] + bbox[2]) / 2) < 1e-9);
  assert.ok(Math.abs(fit.s * (ext.b0 + ext.b1) / 2 + fit.oy - (bbox[1] + bbox[3]) / 2) < 1e-9);
  const png = path.join(dir, "c.png");
  await sharp({ create: { width: 1024, height: 1024, channels: 3, background: { r: 255, g: 255, b: 255 } } }).png().toFile(png);
  const S = { klass: "vehicle", readJson: (k) => (k === "layoutMeasured" ? { _frame: { quadPx: fit.quadPx } } : null), paths: { camera: camFile, target: png }, rel: { layoutMeasured: "x" } };
  const reg = registration(S);
  assert.ok(reg.rmsPx < 0.1, `rms ${reg.rmsPx}`);   // quadPx is rounded to 0.1 px
  assert.ok(Math.abs(reg.s / fit.s - 1) < 1e-3 && Math.abs(reg.ox - fit.ox) < 0.2 && Math.abs(reg.oy - fit.oy) < 0.2);
  fs.rmSync(dir, { recursive: true, force: true });
});

test("--write-frame: the concept foreground bbox (darkest channel < fgMax, exclusive ends); an empty concept throws", () => {
  const w = 6, h = 5, data = new Uint8Array(w * h * 3).fill(255);
  const set = (x, y, v) => { data.set([v, 250, 250], (y * w + x) * 3); };
  set(1, 2, 10); set(4, 3, 234); set(5, 0, 236);   // 236 >= fgMax: background
  assert.deepEqual(foregroundBox(data, w, h, 3, 235), [1, 2, 5, 4]);
  assert.throws(() => foregroundBox(new Uint8Array(w * h * 3).fill(255), w, h, 3), /no foreground/);
});
