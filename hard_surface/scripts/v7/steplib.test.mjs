// node --test scripts/v7/steplib.test.mjs — the pure rules of step.mjs / doctor.mjs / scaffold.mjs (scripts/v7/steplib.mjs)
// + the per-view `scale: {right}` registration (scripts/v6/ortho.mjs). Hermetic: synthetic data only.
import assert from "node:assert/strict";
import test from "node:test";

import {
  CLASS_CONFIG, STEP, baselineOf, bodyColourRows, braceRange, cameraRows, centringRow, chainKey, clipKey, dimsPlan, doctorVerdict,
  enclosedWhite, frameMove, gateRows, lineRuns, mapHexIn, parseProbes, probeCompare, probeLine, remapPalette, residualRows,
  setTopLevelValues, stepVerdict, stripHeader, whiteRows, withFrameKnobs,
} from "./steplib.mjs";
import { basisOf, pxToView, registerViews } from "../v6/ortho.mjs";

const V = (iou, agree = iou) => ({ iou, agree });
const cur = (over = {}) => ({ checkModule: { pass: true, line: "PASS m.mjs" }, views: { side: V(0.95), front: V(0.9), concept: V(0.96) },
  floats: [], clips: [], chainRows: [], chainError: null, tris: 3000, budget: 4000, ...over });
const base = (over = {}) => ({ views: { side: V(0.95), front: V(0.9), concept: V(0.96) }, floats: [], clips: [], chainRows: [], ...over });

test("stepVerdict: identical to the baseline -> KEEP", () => {
  const v = stepVerdict(cur(), base());
  assert.equal(v.keep, true);
  assert.equal(v.line, "KEEP");
});

test("stepVerdict: an agree drop over 0.01 reverts, 0.01 exactly does not; a drop inside drift (raw only) is a note", () => {
  assert.equal(stepVerdict(cur({ views: { side: V(0.94), front: V(0.9), concept: V(0.96) } }), base()).keep, true);   // -0.01: kept
  const v = stepVerdict(cur({ views: { side: V(0.9389), front: V(0.9), concept: V(0.96) } }), base());
  assert.equal(v.keep, false);
  assert.match(v.line, /^REVERT: side agree 0\.9389 < base 0\.9500 - 0\.01$/);
  const d = stepVerdict(cur({ views: { side: V(0.92, 0.951), front: V(0.9), concept: V(0.96) } }), base());
  assert.equal(d.keep, true);
  assert.match(d.notes[0], /side raw iou 0\.9200 .* inside the drift rects/);
  // a baseline JSON from before WF v8 (no agree): its iou is the agree
  assert.equal(stepVerdict(cur(), base({ views: { side: { iou: 0.97 } } })).keep, false);
});

test("stepVerdict: a new float / clip / chain row, a check-module fail, tris over budget each revert and are named", () => {
  const v = stepVerdict(cur({
    floats: [{ name: "mirror_l", why: "not reached: mirror_head_l" }, { name: "bumper_front", why: "x" }],
    clips: [{ a: "b", b: "a" }, { a: "c", b: "d" }],
    chainRows: [{ v: "V2_GAP", part: "mirror_head_l" }, { v: "V5_THIN", part: "grille" }],
    tris: 4100,
  }), base({ floats: ["bumper_front"], clips: [clipKey({ a: "a", b: "b" })], chainRows: [chainKey({ v: "V5_THIN", part: "grille" })] }));
  assert.equal(v.keep, false);
  assert.deepEqual(v.reasons, ["new float mirror_l (not reached: mirror_head_l)", "new clip c x d", "new chain row V2_GAP mirror_head_l", "tris 4100 > budget 4000"]);
  assert.deepEqual(v.newRows, [{ v: "V2_GAP", part: "mirror_head_l" }]);
  const cm = stepVerdict(cur({ checkModule: { pass: false, line: "build() threw: x" } }), base());
  assert.equal(cm.line, "REVERT: check-module FAIL: build() threw: x");
  assert.equal(stepVerdict(cur({ chainError: "boom" }), base()).line, "REVERT: chain error: boom");
});

test("stepVerdict: without baseline chain rows, class-config rows are notes and any other row counts", () => {
  const rows = [{ v: CLASS_CONFIG[0], part: "trim" }, { v: "V2_GAP", part: "x" }];
  const v = stepVerdict(cur({ chainRows: rows }), base({ chainRows: null }));
  assert.equal(v.keep, false);
  assert.deepEqual(v.reasons, ["chain row V2_GAP x (no baseline rows)"]);
  assert.match(v.notes[0], /PALETTE_ZONE trim \(class-config/);
  assert.equal(stepVerdict(cur({ chainRows: [rows[0]] }), base({ chainRows: null })).keep, true);
  // two rows of one rule on one part (two measurements) are one reason
  assert.deepEqual(stepVerdict(cur({ chainRows: [rows[1], { ...rows[1] }] }), base({ chainRows: [] })).reasons, ["new chain row V2_GAP x"]);
  // no baseline at all: no IoU comparison, every float counts
  assert.equal(stepVerdict(cur({ floats: [{ name: "f" }] }), null).line, "REVERT: new float f");
});

test("baselineOf: view JSON (checks, no chain), step JSON (chain rows), state.json views", () => {
  const view = { views: { side: V(0.9) }, checks: { groups: [{ name: "a", float: true }, { name: "b", float: false }], clips: [{ a: "y", b: "x" }] } };
  assert.deepEqual(baselineOf(view), { views: view.views, floats: ["a"], clips: ["x x y"], chainRows: null });
  assert.deepEqual(baselineOf({ views: {}, chain: { rows: [{ v: "V5_THIN", part: "p" }] } }).chainRows, ["V5_THIN|p"]);
  assert.deepEqual(baselineOf({ views: { top: V(0.8) } }), { views: { top: V(0.8) }, floats: null, clips: null, chainRows: null });
  assert.equal(baselineOf(null), null);
});

test("frameMove: WARN over 1 % scale or 6 px", () => {
  assert.equal(frameMove({ scale: 1, tx: 0, ty: 0 }, { scale: 1.009, tx: 5.9, ty: -6 }).warn, null);
  assert.match(frameMove({ scale: 1, tx: 0, ty: 0 }, { scale: 0.985, tx: 0, ty: 0 }).warn, /scale -1\.50 %/);
  assert.match(frameMove({ scale: 1, tx: 2, ty: 0 }, { scale: 1, tx: 8.5, ty: 0 }).warn, /shift \+6\.5 \/ \+0\.0 px/);
});

test("parseProbes: the format, and errors naming the probe", () => {
  const views = ["side", "front", "concept"];
  const ok = parseProbes({ _comment: "x", probes: [{ id: "P1", view: "side", axis: "row", index: 600, from: 0, to: 1023, what: "hubs" }] }, views);
  assert.deepEqual(ok, [{ id: "P1", view: "side", axis: "row", index: 600, from: 0, to: 1023, what: "hubs" }]);
  assert.equal(parseProbes([{ id: "C1", view: "concept", axis: "col", index: 5, from: 1, to: 2 }], views).length, 1);
  assert.throws(() => parseProbes([{ id: "P1", view: "top", axis: "row", index: 1, from: 0, to: 9 }], views), /\(P1\): view "top"/);
  assert.throws(() => parseProbes([{ id: "P1", view: "side", axis: "diag", index: 1, from: 0, to: 9 }], views), /axis/);
  assert.throws(() => parseProbes([{ id: "P1", view: "side", axis: "row", index: 1.5, from: 0, to: 9 }], views), /index must be an integer/);
  assert.throws(() => parseProbes([{ id: "P1", view: "side", axis: "row", index: 1, from: 9, to: 9 }], views), /to must be > from/);
  assert.throws(() => parseProbes([{ id: "P1", view: "side", axis: "row", index: 1, from: 0, to: 9 }, { id: "P1", view: "side", axis: "col", index: 1, from: 0, to: 9 }], views), /duplicate id P1/);
  assert.throws(() => parseProbes({ lines: [] }, views), /must be \[/);
});

test("lineRuns / probeCompare / probeLine: edges and deltas", () => {
  const set = (on) => (i) => on.some(([a, b]) => i >= a && i <= b);
  assert.deepEqual(lineRuns(set([[2, 5], [8, 8], [10, 12]]), 0, 12), [[2, 5], [10, 12]]);   // the 1 px run dropped
  assert.deepEqual(lineRuns(set([[0, 20]]), 3, 9), [[3, 9]]);
  assert.deepEqual(probeCompare([[10, 50]], [[12, 47]]), { same: true, deltas: [[2, -3]], outer: [2, -3] });
  assert.deepEqual(probeCompare([[10, 20], [30, 50]], [[9, 52]]), { same: false, deltas: null, outer: [-1, 2] });
  assert.equal(probeCompare([], [[1, 2]]).outer, null);
  const p = { id: "P3", view: "front", axis: "col", index: 512, from: 0, to: 1023, what: "centre" };
  assert.equal(probeLine(p, [[300, 664]], [[301, 642]]), "probe P3 front col 512 [0..1023] (centre): ref 300..664 | model 301..642 | d +1/-22");
  assert.equal(probeLine(p, [[1, 5], [9, 20]], [[2, 21]]), "probe P3 front col 512 [0..1023] (centre): ref 1..5 9..20 | model 2..21 | runs 2/1, outer d +1/+1");
});

test("residualRows: W / L / H beyond +-3 % BLOCK naming the view; bbox beyond 5 % WARNs; else PASS", () => {
  const taxi = { W: { front: 0.068, rear: 0.025, top: -0.093, meanPx: 300, maxAbs: 0.093 }, L: { side: 0.004, top: -0.004, meanPx: 700, maxAbs: 0.004 }, H: { side: 0.001, front: -0.002, rear: 0.001 } };
  const rows = residualRows(taxi);
  assert.deepEqual(rows.map((r) => [r.level, r.id]), [["BLOCK", "residual-W"]]);
  assert.match(rows[0].text, /registration W: front \+6\.8 %, top -9\.3 % \(band \+-3 %\)/);
  assert.deepEqual(rows[0].data, { front: 0.068, top: -0.093 });
  const pickup = { W: { front: -0.017, rear: 0.004, top: 0.013 }, Wbbox: { front: 0.02, rear: -0.09, top: 0.133 }, Lbbox: { side: 0.01, top: 0.02 } };
  const pr = residualRows(pickup);
  assert.deepEqual(pr.map((r) => [r.level, r.id]), [["PASS", "residuals"], ["WARN", "residual-Wbbox"]]);
  assert.match(pr[1].text, /rear -9\.0 %, top \+13\.3 %/);
  assert.match(residualRows({ W: { front: 0.03 } })[0].text, /within/);   // 3 % exactly is inside the band
});

test("enclosedWhite: border-connected white is background, an enclosed white patch is a candidate, a hole seed clears it", () => {
  // 12 x 8 RGB: white background, a dark 8 x 6 body at (2..9, 1..6) with a 2 x 2 white window at (5..6, 3..4)
  const w = 12, h = 8, c = 3;
  const data = Buffer.alloc(w * h * c, 255);
  for (let y = 1; y <= 6; y += 1) for (let x = 2; x <= 9; x += 1) if (!(x >= 5 && x <= 6 && y >= 3 && y <= 4)) data.fill(40, (y * w + x) * c, (y * w + x) * c + 3);
  const r = enclosedWhite(data, w, h, c, 235, { minShare: 0.001 });
  assert.equal(r.fg, 44);
  assert.equal(r.comps.length, 1);
  assert.deepEqual(r.comps[0].bbox, [5, 3, 7, 5]);
  assert.equal(r.comps[0].n, 4);
  assert.ok(Math.abs(r.total - 4 / 44) < 1e-12);
  assert.equal(enclosedWhite(data, w, h, c, 235, { holes: [[5, 3]] }).comps.length, 0);
});

test("whiteRows: undecided enclosedFg with >= 0.5 % BLOCKs, a decision passes", () => {
  const imgs = [{ image: "front", total: 0.012, comps: [{ n: 50, share: 0.012, bbox: [1, 2, 3, 4] }] }, { image: "side", total: 0, comps: [] }];
  assert.equal(whiteRows(imgs, undefined)[0].level, "BLOCK");
  assert.match(whiteRows(imgs, undefined)[0].text, /front 1\.20 % \[1,2,3,4 1\.20 %\]/);
  assert.equal(whiteRows(imgs, true)[0].level, "PASS");
  assert.equal(whiteRows([{ image: "top", total: 0.004, comps: [{ n: 9, share: 0.004, bbox: [0, 0, 1, 1] }] }], undefined)[0].level, "PASS");
  assert.equal(whiteRows([{ image: "top", total: 0, comps: [] }], undefined)[0].level, "PASS");
});

test("bodyColourRows / cameraRows / gateRows / centringRow / doctorVerdict", () => {
  assert.equal(bodyColourRows([[240, 239, 235]], 235)[0].level, "BLOCK");   // darkest 235 >= 235 - 8: the default fgMax eats a white body
  assert.equal(bodyColourRows([[240, 239, 235]], 252)[0].level, "PASS");   // families.fgMax 252 (delivery_truck): 235 < 244
  assert.deepEqual(cameraRows({ provisional: false, residual_px: 0.4, vertical_tilt_deg: 0.01 }).map((r) => r.level), ["PASS"]);
  assert.deepEqual(cameraRows({ provisional: true, residual_px: 1.2, vertical_tilt_deg: 0.9 }).map((r) => r.level), ["WARN", "WARN", "WARN"]);
  const g = gateRows({ pass: false, violations: [{ v: "PALETTE_ZONE", part: "trim" }, { v: "V2_GAP", part: "x" }], tris: 1, budget: 2 });
  assert.deepEqual(g.map((r) => [r.level, r.id]), [["BLOCK", "gate"], ["WARN", "gate-class"]]);
  assert.equal(gateRows({ pass: true, violations: [], tris: 1, budget: 2 })[0].level, "PASS");
  assert.equal(centringRow({ view: "rear", axis: "right", dBox: 0.1, dMass: 0.08 }).level, "WARN");
  assert.match(centringRow({ view: "rear", axis: "right", dBox: 0.1, dMass: 0.08 }).text, /shift candidate \+0\.090 m/);
  assert.equal(centringRow({ view: "rear", axis: "right", dBox: 0.1, dMass: -0.08 }).level, "PASS");   // opposite sides: a mirror, not a skew
  assert.equal(centringRow({ view: "rear", axis: "right", dBox: 0.104, dMass: 0.111, shift: 0.11 }).level, "PASS");   // delivery_truck rear
  assert.match(centringRow({ view: "top", axis: "up", dBox: 0.043, dMass: 0.029, shift: 0.162 }).text, /the fg centres say \+0\.036/);
  assert.deepEqual(doctorVerdict([{ level: "PASS" }, { level: "WARN" }]), { level: "WARN", blocks: 0, warns: 1 });
  assert.equal(doctorVerdict([{ level: "BLOCK" }, { level: "WARN" }]).level, "BLOCK");
  assert.equal(STEP.maxLines, 40);
});

test("dimsPlan: KNOBS win, ratios keep each knob's meaning, the wheel radius from the prior", () => {
  const src = { L: 4.0, W: 1.85, H: 2.0 }, dst = { L: 4.4, W: 2.0, H: 2.2 };
  const plan = dimsPlan({ knobs: { L: { v: 4.074 }, W: { v: 1.89 }, H: { v: 1.581 }, wheelR: { v: 0.345 } }, defaults: { R: 0.5 }, srcDims: src, dstDims: dst, prior: { stylisation: { wheelDoverH: 0.3 } } });
  assert.deepEqual(plan.map((p) => [p.where, p.key, p.to]), [["KNOBS", "L", 4.4814], ["KNOBS", "W", 2.0432], ["KNOBS", "H", 1.7391], ["KNOBS", "wheelR", 0.33]]);
  const bus = dimsPlan({ defaults: { L: 6.2633, W: 2.4408, H: 2.7848, R: 0.46 }, srcDims: src, dstDims: dst });
  assert.deepEqual(bus.map((p) => [p.where, p.key, p.to]), [["DEFAULTS", "L", 6.8896], ["DEFAULTS", "W", 2.6387], ["DEFAULTS", "H", 3.0633], ["DEFAULTS", "R", 0.506]]);
  assert.deepEqual(dimsPlan({ defaults: { stripeY: [1, 2] }, srcDims: src, dstDims: dst }), []);
  // the pickup: W and H follow `const L` through the module's own fractions
  assert.deepEqual(dimsPlan({ consts: { L: 4.8 }, srcDims: src, dstDims: dst }).map((p) => [p.where, p.key, p.to]), [["const", "L", 5.28]]);
});

test("scaffold text edits: top-level DEFAULTS values, palette hexes, the header, frame knobs", () => {
  const mod = [
    "// GOLD taxi — old header",
    "//   more of it",
    "",
    'import * as K from "../../../../src/kernel/index.mjs";',
    "",
    "export const meta = { class: \"vehicle\", palette: { body: { top: \"#D23C32\", front: \"#be2d28\" }, tyre: '#2f2f2f' } };",
    "export const DEFAULTS = {",
    "  L: 6.2633, W: 2.4408, H: 2.7848,   // { a brace in a comment",
    "  rear: { R: 0.76, W: 9 }, R: 0.46,",
    "  note: \"L: 1\",",
    "};",
    "export function build() { return []; }",
  ].join("\n");
  const d = setTopLevelValues(mod, "export const DEFAULTS = {", { W: 2.6387, R: 0.5 });
  assert.match(d, /L: 6\.2633, W: 2\.6387, H: 2\.7848/);
  assert.match(d, /rear: \{ R: 0\.76, W: 9 \}, R: 0\.5,/);   // the nested R and W untouched
  assert.throws(() => setTopLevelValues(mod, "export const DEFAULTS = {", { Q: 1 }), /no top-level numeric Q/);
  const [o, c] = braceRange(mod, mod.indexOf("palette:"));
  assert.equal(mod.slice(o, c + 1), "{ body: { top: \"#D23C32\", front: \"#be2d28\" }, tyre: '#2f2f2f' }");
  const m = mapHexIn(mod, [o, c + 1], (h) => (h === "#d23c32" ? "#ffd21e" : h));
  assert.match(m, /top: "#ffd21e", front: "#be2d28" \}, tyre: '#2f2f2f'/);
  assert.equal(stripHeader(mod).split("\n")[0], 'import * as K from "../../../../src/kernel/index.mjs";');
  const k = withFrameKnobs(mod, { scale: 0.9123456, tx: -3.5, ty: 2 });   // no KNOBS block: one is inserted before the first export
  assert.match(k, /export const KNOBS = \{\n {2}frameScale: \{ v: 0\.9123,[^\n]*\n {2}frameX: \{ v: -3\.5,[^\n]*\n {2}frameY: \{ v: 2,[^\n]*\n\};\n\nexport const meta/);
  const k2 = withFrameKnobs("export const KNOBS = {\n  L: { v: 4, min: 3, max: 5, unit: \"m\" },\n};\nexport const meta = {};\n", { scale: 1.1, tx: 0, ty: 0 });
  assert.match(k2, /L: \{ v: 4,[^\n]*\n {2}frameScale: \{ v: 1\.1,/);
  assert.equal(withFrameKnobs(k2, { scale: 1.2, tx: 1, ty: 1 }).match(/frameScale/g).length, 1);
});

test("remapPalette: families by name, cel tones kept as offsets, unknown families untouched", () => {
  const tbl = (names, rgb) => ({ names: ["bg", ...names, "other"], rgb: [null, ...rgb, null] });
  const src = tbl(["body", "dark"], [[[200, 50, 40]], [[40, 40, 40]]]);
  const dst = tbl(["body", "glass"], [[[250, 200, 20]], [[100, 150, 250]]]);
  const r = remapPalette({ body: { top: "#d23c32", front: "#be2d28" }, tyre: "#2f2f2f", paint: "#c83228" }, src, dst);
  assert.deepEqual(r.palette, { body: { top: "#ffd21e", front: "#f0c314" }, tyre: "#2f2f2f", paint: "#fac814" });
  assert.deepEqual(r.rows.map((x) => [x.zone, x.family]), [["body", "body"], ["tyre", "dark"], ["paint", "body"]]);
});

test("ortho scale.right: residuals, basis and pxToView see the corrected axis; absent = unchanged", () => {
  // two views of a 4 x 2 m box at 50 px/m: side (right = -z, measures L and H) and top (right = -z, up = -x: L and W);
  // the top view is drawn 10 % too long along its right axis
  const img = (w, h, x0, x1, y0, y1) => {
    const fam = new Uint8Array(w * h);
    for (let y = y0; y < y1; y += 1) for (let x = x0; x < x1; x += 1) fam[y * w + x] = 1;
    return { w, h, fam };
  };
  const views = { side: { right: [0, 0, -1], up: [0, 1, 0] }, top: { right: [0, 0, -1], up: [-1, 0, 0] } };
  const images = { side: img(400, 200, 100, 300, 50, 150), top: img(400, 200, 90, 310, 50, 150) };
  const spec = (tv) => ({ views: { side: views.side, top: tv }, anchor: { dim: "L", m: 4 }, origin: { x: "centre", y: "min", z: "centre" }, body: 1 });
  const plain = registerViews(images, spec(views.top));
  assert.ok(Math.abs(plain.residuals.L.top - 0.0476) < 1e-3);   // 220 px vs 200 px
  const scaled = registerViews(images, spec({ ...views.top, scale: { right: 1.1 } }));
  assert.ok(Math.abs(scaled.residuals.L.top) < 1e-9 && Math.abs(scaled.s - 50) < 1e-9);
  assert.equal(scaled.views.top.kr, 1.1);
  assert.equal(plain.views.top.kr, undefined);
  assert.deepEqual(basisOf({ ...views.top, scale: { right: 1.1 } }).right.map((c) => +c.toFixed(6)), [0, 0, -1.1]);
  assert.equal(basisOf(views.top).right, views.top.right);   // the same array: byte-identical rasters without a scale
  assert.deepEqual(pxToView(scaled, "top", 310, 50).map((v) => +v.toFixed(6)), [2, 1]);   // the right edge = +2 m (z -2), up edge = +1 m (x -1)
  assert.throws(() => registerViews(images, spec({ ...views.top, scale: { right: 3 } })), /scale\.right/);
});

test("ortho scale.up: the up axis corrected like scale.right (residuals, basis, pxToView, shift.up); absent = unchanged", () => {
  // a 4 x 2 m box at 50 px/m: side (right -z, up +y: L, H), front (right +x, up +y: W, H), top (right -z, up -x: L, W);
  // the top view is drawn 10 % too wide across (its up axis)
  const img = (w, h, x0, x1, y0, y1) => {
    const fam = new Uint8Array(w * h);
    for (let y = y0; y < y1; y += 1) for (let x = x0; x < x1; x += 1) fam[y * w + x] = 1;
    return { w, h, fam };
  };
  const views = { side: { right: [0, 0, -1], up: [0, 1, 0] }, front: { right: [1, 0, 0], up: [0, 1, 0] }, top: { right: [0, 0, -1], up: [-1, 0, 0] } };
  const images = { side: img(400, 200, 100, 300, 50, 150), front: img(200, 200, 50, 150, 50, 150), top: img(400, 200, 100, 300, 45, 155) };
  const spec = (tv) => ({ views: { ...views, top: tv }, anchor: { dim: "L", m: 4 }, origin: { x: "centre", y: "min", z: "centre" }, body: 1 });
  const plain = registerViews(images, spec(views.top));
  assert.ok(Math.abs(plain.residuals.W.top - 0.0476) < 1e-3);   // 110 px vs 100 px
  const scaled = registerViews(images, spec({ ...views.top, scale: { up: 1.1 } }));
  assert.ok(Math.abs(scaled.residuals.W.top) < 1e-9 && Math.abs(scaled.s - 50) < 1e-9);
  assert.equal(scaled.views.top.ku, 1.1);
  assert.equal(scaled.views.top.kr, undefined);
  assert.equal(plain.views.top.ku, undefined);
  assert.deepEqual(basisOf({ ...views.top, scale: { up: 1.1 } }).up.map((c) => +c.toFixed(6)), [-1.1, 0, 0]);
  assert.equal(basisOf(views.top).up, views.top.up);   // the same array: byte-identical rasters without a scale
  assert.equal(basisOf({ ...views.top, scale: { up: 1.1 } }).right, views.top.right);
  assert.deepEqual(pxToView(scaled, "top", 300, 45).map((v) => +v.toFixed(6)), [2, 1]);   // the top edge = +1 m across
  const shifted = registerViews(images, spec({ ...views.top, scale: { up: 1.1 }, shift: { up: 0.1 } }));
  assert.ok(Math.abs(shifted.views.top.oy - (scaled.views.top.oy - 0.1 * 50 * 1.1)) < 1e-9);   // shift.up moves ku x as many px
  assert.throws(() => registerViews(images, spec({ ...views.top, scale: { up: 0.4 } })), /scale\.up/);
});
