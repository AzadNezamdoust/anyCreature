// V6-1 multi-view experiment + V6-2 generic contract: ortho camera conventions (views.json), turnaround registration,
// colour families, the ortho rasteriser, placement rules, the rules registry and the bus regression (the V6-1 B arm
// judged through the generic pipeline). Hermetic: in-process, reads only tracked files, writes nothing.
import fs from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";

import * as K from "../src/kernel/index.mjs";
import { meshParts } from "../scripts/project.mjs";
import { basisOf, celFactor, cross, familyTable, loadTurnaround, openMask, rasterOrtho, readJson, registerViews, spanOf, spanOpenOf, viewsFile } from "../scripts/v6/ortho.mjs";
import { RULES, attachmentChecks, mirrorPlacement, registerRules, rulesFor, stopArmPlacement } from "../scripts/v6/rules.mjs";
import { judge } from "../scripts/v6/judge.mjs";

const VIEWS = readJson(viewsFile("school_bus")).views;

test("V6-1 ortho cameras: right x up points at the camera; side/top show the nose (+z) on the left, top shows +x at the bottom", () => {
  assert.deepEqual(basisOf(VIEWS.side).back.map((v) => v + 0), [1, 0, 0]);
  assert.deepEqual(basisOf(VIEWS.front).back.map((v) => v + 0), [0, 0, 1]);
  assert.deepEqual(basisOf(VIEWS.rear).back.map((v) => v + 0), [0, 0, -1]);
  assert.deepEqual(basisOf(VIEWS.top).back.map((v) => v + 0), [0, 1, 0]);
  assert.equal(VIEWS.side.right[2], -1, "side: +z (nose) maps to screen left");
  assert.equal(VIEWS.top.up[0], -1, "top: +x flank maps to screen down");
  assert.deepEqual(cross([1, 0, 0], [0, 1, 0]), [0, 0, 1]);
});

/** A synthetic flat-colour view: a yellow body rect (x0..x1, y0..y1) + a black strip under it to the ground row gy. */
function synth(w, h, [x0, x1, y0, y1], gy) {
  const fam = new Uint8Array(w * h);
  for (let y = y0; y < gy; y += 1) for (let x = x0; x < x1; x += 1) fam[y * w + x] = y < y1 ? 5 : 1;
  return { w, h, c: 3, data: Buffer.alloc(w * h * 3, 255), fam };
}

test("V6-1 registerViews: one px/m from the anchor width, shared-dimension residuals, body-centre / ground offsets", () => {
  const images = {
    side: synth(400, 200, [50, 350, 40, 150], 170),   // L 300, H 130
    front: synth(400, 200, [150, 250, 40, 150], 170), // W 100
    rear: synth(400, 200, [148, 252, 40, 150], 170),  // W 104 (+2 %)
    top: synth(400, 200, [50, 350, 50, 150], 150),    // L 300, W 100
  };
  const reg = registerViews(images, { views: VIEWS, anchor: { dim: "W", m: 2 }, origin: { x: "centre", y: "min", z: "centre" }, body: 5 });
  assert.ok(Math.abs(reg.s - 101.333 / 2) < 0.01, `px/m ${reg.s}`);
  assert.equal(reg.residuals.L.maxAbs, 0);
  assert.ok(reg.residuals.W.maxAbs > 0.02 && reg.residuals.W.maxAbs < 0.03);
  assert.equal(reg.views.side.ox, 200);
  assert.equal(reg.views.side.oy, 170);
  assert.equal(reg.views.top.oy, 100);
});

test("families.spanOpen: the body span ignores 1-px halo lines (opening), absent = the raw mask; validation", () => {
  // a front view (W 100 px) whose mirror-head outline leaves a 1-px body-coloured halo column 20 px outside the body
  const halo = (img, x, y0, y1) => { for (let y = y0; y < y1; y += 1) img.fam[y * img.w + x] = 5; return img; };
  const front = halo(synth(400, 200, [150, 250, 40, 150], 170), 130, 60, 100);   // 40 px tall: >= 5 % of the peak column
  assert.deepEqual(spanOf(front, 5, "x"), [130, 250], "the raw rule counts the halo column");
  assert.deepEqual(spanOf(front, 5, "x", 0.05, 2), [150, 250], "opened: the body only");
  assert.deepEqual(spanOf(front, 5, "y", 0.05, 2), spanOf(front, 5, "y"), "a solid body keeps its span");
  // openMask: an n x n opening keeps every n x n square inside the mask and nothing thinner
  const m = new Uint8Array(8 * 6);
  for (let y = 1; y < 4; y += 1) for (let x = 1; x < 5; x += 1) m[y * 8 + x] = 1;   // 4 x 3 block
  m[5 * 8 + 6] = 1; m[4 * 8 + 6] = 1;                                               // a 1-px wide stub
  const o = openMask(m, 8, 6, 2);
  assert.equal(o.reduce((a, b) => a + b, 0), 12, "the block survives whole");
  assert.equal(o[5 * 8 + 6] + o[4 * 8 + 6], 0, "the 1-px stub drops out");
  assert.equal(openMask(m, 8, 6, 1), m, "n < 2: the mask itself");
  // registration: the halo column no longer inflates W
  const images = {
    side: synth(400, 200, [50, 350, 40, 150], 170), front,
    rear: synth(400, 200, [150, 250, 40, 150], 170), top: synth(400, 200, [50, 350, 50, 150], 150),
  };
  const base = { views: VIEWS, anchor: { dim: "W", m: 2 }, origin: { x: "centre", y: "min", z: "centre" }, body: 5 };
  assert.ok(registerViews(images, base).residuals.W.maxAbs > 0.1);
  assert.equal(registerViews(images, { ...base, spanOpen: 2 }).residuals.W.maxAbs, 0);
  // the table carries it only when set (absent = byte-identical tables); bad values throw
  const t = { table: { body: "#ffff00" }, body: "body" };
  assert.equal("spanOpen" in familyTable([], t), false);
  assert.equal(familyTable([], { ...t, spanOpen: 2 }).spanOpen, 2);
  assert.deepEqual(spanOpenOf({}), {});
  for (const bad of [1, 2.5, "2", 40]) assert.throws(() => spanOpenOf({ spanOpen: bad }), /spanOpen/);
});

test("V6-1 the school_bus turnaround registers within +-3 % on every shared dimension", async () => {
  const { reg } = await loadTurnaround("school_bus");
  for (const k of ["L", "H", "W"]) assert.ok(reg.residuals[k].maxAbs <= 0.03, `${k} residual ${reg.residuals[k].maxAbs}`);
  assert.ok(reg.dims.L / reg.dims.W > 2.3 && reg.dims.L / reg.dims.W < 2.8, "the concept's chibi L/W (~2.56)");
});

test("V6-1 rasterOrtho: a 1 m cube covers 1 m x 1 m in every ortho view (pixel centres, back faces culled)", async () => {
  await K.init();
  const { meshes } = meshParts([{ id: "c", role: "cab", zone: "body", solid: K.box([1, 1, 1]) }], 0);
  for (const v of Object.keys(VIEWS)) {
    const { partId } = rasterOrtho(meshes, basisOf(VIEWS[v]), { k: 10, bx: 20, by: 20 }, 40, 40);
    const n = partId.reduce((a, p) => a + (p >= 0 ? 1 : 0), 0);
    assert.equal(n, 100, `${v}: ${n} px`);
  }
});

test("V6-1 mirrorPlacement: the arm is clamped into the rule range by moving the head along z only", () => {
  const base = { W: 2.4, noseZ: 3, chamfer: 0.1, centreY: 1.8, headOut: 0.09, headW: 0.23, headH: 0.5 };
  const short = mirrorPlacement({ ...base, ahead: -0.13 });
  assert.ok(Math.abs(short.armLength - RULES.mirror.armM[0]) < 1e-9, `short ${short.armLength}`);
  const long = mirrorPlacement({ ...base, ahead: 1 });
  assert.ok(Math.abs(long.armLength - RULES.mirror.armM[1]) < 1e-9, `long ${long.armLength}`);
  assert.equal(long.arm, 0.09, "x (front-ortho evidence) is never moved");
  const ok = mirrorPlacement({ ...base, ahead: 0.18 });
  assert.ok(ok.armLength > 0.25 && ok.armLength < 0.45);
  assert.ok(ok.z > base.noseZ, "the head stands ahead of the nose");
});

test("V6-1 stopArmPlacement: a sign straddling the band's lower edge drops below it; clear signs stay", () => {
  const a = stopArmPlacement({ z: 2, y: 1.3, diameter: 0.48, border: 0.02, bandBottom: 1.5 });
  assert.ok(a.centre[1] + 0.26 <= 1.5 - 0.004 && a.dropped > 0);
  const b = stopArmPlacement({ z: 2, y: 1.0, diameter: 0.48, border: 0.02, bandBottom: 1.5 });
  assert.equal(b.centre[1], 1.0);
});

test("V6-1 attachmentChecks: a bumper hanging below the nose face floats, one flush on it does not; group overlap is a clip", async () => {
  await K.init();
  const at = (lo, hi) => K.box([hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]]).at([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]);
  const cab = { id: "cab", role: "cab", zone: "body", solid: at([-1, 0.5, -3], [1, 2.5, 3]) };
  const hanging = { id: "bumper_front", role: "bumper", zone: "black", solid: at([-1.05, 0.1, 2.99], [1.05, 0.49, 3.15]) };
  const flush = { id: "bumper_front", role: "bumper", zone: "black", solid: at([-1.05, 0.6, 2.99], [1.05, 0.9, 3.15]) };
  const bad = attachmentChecks([cab, hanging]);
  assert.equal(bad.groups.find((g) => g.name === "bumper_front").float, true);
  assert.equal(bad.pass, false);
  const good = attachmentChecks([cab, flush]);
  assert.equal(good.groups.find((g) => g.name === "bumper_front").float, false);
  const lamp = { id: "lamp_l", role: "headlight", zone: "lamp", solid: at([0.5, 0.7, 2.99], [0.7, 0.85, 3.05]) };
  const clip = attachmentChecks([cab, flush, lamp]);
  assert.deepEqual(clip.clips.map((c) => [c.a, c.b]), [["bumper_front", "headlights"]]);
});

test("V6-2 families: derived from the concept palette (regions medians), near colours merge, the body family is named", async () => {
  const { table } = await loadTurnaround("school_bus");
  assert.equal(table.names[table.body], "body");
  assert.deepEqual(table.members.body.sort(), ["body_front", "body_side", "roof"]);
  assert.ok(table.names.includes("amber") && table.names.includes("signal"), "amber / signal stay their own families");
  const t = familyTable([], { table: { brick: "#a0522d", glass: ["#88aacc"] }, body: "brick" });
  assert.equal(t.names[t.body], "brick");
  assert.deepEqual(t.zoneFams.map((f) => t.names[f]), ["glass"]);
});

test("V6-2 cel: a face toward the viewer 100 %, a top 105 %, a side 85 %", () => {
  assert.equal(celFactor([0, 0, 1], [0, 0, 1]), 1);
  assert.equal(celFactor([0, 1, 0], [0, 0, 1]), 1.05);
  assert.equal(celFactor([1, 0, 0], [0, 0, 1]), 0.85);
  assert.equal(celFactor([0, 1, 0], [0, 1, 0]), 1, "the top ortho sees the roof as facing");
});

test("V6-2 rules registry: vehicle registered; an unknown class gets a no-rule entry; registerRules replaces", async () => {
  const v = await rulesFor("vehicle");
  assert.ok(v.groups.some((g) => g.name === "mirror_l") && v.symmetry.view === "front");
  assert.deepEqual(v.frame.origin, { x: "centre", y: "min", z: "centre" });
  const none = await rulesFor("no_such_class_v62");
  assert.deepEqual(none.checks([]), { groups: [], clips: [], pass: true });
  registerRules("no_such_class_v62", { groups: [{ name: "g" }], checks: () => ({ groups: [], clips: [], pass: false }) });
  assert.equal((await rulesFor("no_such_class_v62")).checks([]).pass, false);
});

test("V6-2 bus regression: the V6-1 B arm judged through the generic pipeline reproduces its IoUs (+-0.005), no float / clip", async () => {
  const B = JSON.parse(fs.readFileSync(new URL("../out/v6/bus-experiment.json", import.meta.url), "utf8")).arms.B;
  const { metrics } = await judge({ subjectId: "school_bus", modulePath: "out/v6/B.mjs", tiles: false });
  for (const v of ["side", "front", "rear", "top", "concept"]) assert.ok(Math.abs(metrics.views[v].iou - B.views[v].iou) <= 0.005, `${v} ${metrics.views[v].iou} vs ${B.views[v].iou}`);
  assert.equal(metrics.checks.pass, true);
  assert.deepEqual(metrics.checks.groups.filter((g) => g.float), []);
  assert.deepEqual(metrics.checks.clips, []);
});

// ---- V6-2 loop integration (scripts/v6/loop6.mjs): knob rewrite, guard, stop, START stretch, prompt budget
test("V6-2 setKnob: rewrites one entry's v / min / max and drops only its locked", async () => {
  const { setKnob } = await import("../scripts/v6/loop6.mjs");
  const text = 'export const KNOBS = {\n  L: { v: 4.8, min: 4.8, max: 4.8, unit: "m", locked: "anchor" },   // c\n  W: { v: 2, min: 1.9, max: 2.1, unit: "m", locked: "x" },\n};';
  const out = setKnob(text, "L", { v: 6.2, min: 5, max: 12.7 }, true);
  assert.match(out, /L: \{ v: 6\.2, min: 5, max: 12\.7, unit: "m" \},/);
  assert.match(out, /W: \{ v: 2, min: 1\.9, max: 2\.1, unit: "m", locked: "x" \}/);
});

const fakeM = (views, { rows = [], blocking = 0, codes = [], score = null } = {}) => {
  const ortho = Object.entries(views).filter(([k]) => k !== "concept").map(([, v]) => v);
  const all = Object.values(views);
  return { loads: true, pass: blocking === 0, blocking, codes, tris: 1000, triBudget: 9000,
    v6: { views: Object.fromEntries(Object.entries(views).map(([k, v]) => [k, { iou: v }])), placementRows: rows, checks: { pass: !rows.length },
      minOrtho: Math.min(...ortho), minView: Math.min(...all), score: score ?? (2 * views.concept + ortho.reduce((a, b) => a + b, 0)) / (2 + ortho.length) } };
};

test("V6-2 judge6: lexicographic — gate, placement, per-view min, then the score gain", async () => {
  const { judge6, SCORE_GAIN } = await import("../scripts/v6/loop6.mjs");
  const b = fakeM({ side: 0.93, front: 0.92, concept: 0.95 }, { rows: ["PLACEMENT: mirror arm 0.1 m outside"] });
  assert.equal(judge6(fakeM({ side: 0.99, front: 0.99, concept: 0.99 }, { rows: ["PLACEMENT: mirror arm 0.1 m outside", "PLACEMENT: bumper_front floats (x)"] }), b).accept, false, "a new placement row loses");
  assert.equal(judge6(fakeM({ side: 0.9, front: 0.9, concept: 0.9 }), b).accept, true, "fewer placement rows win");
  assert.equal(judge6(fakeM({ side: 0.93, front: 0.92, concept: 0.95 }, { rows: ["PLACEMENT: mirror arm 0.2 m outside"] }), b).accept, false, "same row (numbers moved), no score gain");
  assert.equal(judge6(fakeM({ side: 0.99, front: 0.91, concept: 0.99 }, { rows: b.v6.placementRows }), b).accept, false, "per-view min lower");
  const up = fakeM({ side: 0.93 + 6 * SCORE_GAIN, front: 0.92, concept: 0.95 }, { rows: b.v6.placementRows });
  assert.equal(judge6(up, b).accept, true);
  assert.equal(judge6(fakeM({ side: 0.99, front: 0.99, concept: 0.99 }, { blocking: 1, codes: ["V12_CENSUS"] }), fakeM({ side: 0.9, front: 0.9, concept: 0.9 })).accept, false, "gate first");
});

test("V6-2 atTarget6: gate PASS, no placement row, every ortho >= 0.92, concept >= 0.96", async () => {
  const { atTarget6 } = await import("../scripts/v6/loop6.mjs");
  assert.equal(atTarget6(fakeM({ side: 0.93, front: 0.92, concept: 0.96 })), true);
  assert.equal(atTarget6(fakeM({ side: 0.93, front: 0.919, concept: 0.97 })), false);
  assert.equal(atTarget6(fakeM({ side: 0.93, front: 0.93, concept: 0.959 })), false);
  assert.equal(atTarget6(fakeM({ side: 0.95, front: 0.95, concept: 0.97 }, { rows: ["PLACEMENT: x floats"] })), false);
  assert.equal(atTarget6(fakeM({ side: 0.95, front: 0.95, concept: 0.97 }), { exact: true }), false, "--v5-detail on: exactness stop");
});

test("V6-2 START stretch: a module already at the turnaround's dimensions keeps ratio ~1 and still builds", async () => {
  const { priorStart } = await import("../scripts/v6/loop6.mjs");
  const dir = new URL("./.tmp-v62/", import.meta.url);
  fs.mkdirSync(dir, { recursive: true });
  try {
    const file = new URL("B.mjs", dir);
    const text = fs.readFileSync(new URL("../out/v6/B.mjs", import.meta.url), "utf8");
    const r = await priorStart(text, { subjectId: "school_bus", file: file.pathname.replace(/^\/([A-Za-z]:)/, "$1") });
    assert.equal(r.fallback, undefined);
    for (const x of r.ratio) assert.ok(Math.abs(x - 1) < 0.06, `ratio ${r.ratio}`);
    assert.match(r.moved.L, /soft \[5, 12\.7\]/, "prior softRanges replace L's range");
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

test("V6-2 LOOP prompt: view-tagged rows, <= 6 kB, cites the building lines", async () => {
  const { loopPrompt6 } = await import("../scripts/v6/loop6.mjs");
  const { PROMPT_MAX } = await import("../scripts/loop.mjs");
  const { loadSubject } = await import("../scripts/subject.mjs");
  const { metrics } = await judge({ subjectId: "school_bus", modulePath: "out/v6/A.mjs", tiles: false });
  const text = fs.readFileSync(new URL("../out/v6/A.mjs", import.meta.url), "utf8");
  const m = { text, mod: { meta: { palette: { body: "#f4b719" } } }, pass: true, blocking: 0, codes: [], tris: metrics.tris, triBudget: 9000, v6: metrics };
  const p = loopPrompt6({ subjectId: "school_bus", S: loadSubject("school_bus"), rejected: [] }, m, { k: 1, K: 3, verdict: "START", ready: [] });
  assert.ok(Buffer.byteLength(p, "utf8") <= PROMPT_MAX, `${Buffer.byteLength(p, "utf8")} bytes`);
  assert.match(p, /^1\. PLACEMENT: /m, "placement rows first");
  assert.match(p, /^\d\. (SIDE|FRONT|REAR|TOP): /m, "view-tagged rows");
  assert.match(p, /^\s*\d+\| .*K\.assemble\./m, "numbered module lines are cited");
});
