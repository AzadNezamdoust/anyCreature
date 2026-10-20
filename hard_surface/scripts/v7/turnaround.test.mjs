// node --test scripts/v7/turnaround.test.mjs — the pure parts of turnaround.mjs: the prompt fill, the KEEP / REVERT rule,
// the attempt choice, the targets, the draft geometry, the views.json rewrite.
import test from "node:test";
import assert from "node:assert/strict";

import {
  FAMILIES, TARGETS, asymSentence, checkFacts, chooseAttempt, colourClusters, draftDims, factsDeviation, fillTemplate, jsonValueSpan, loadTemplates,
  matchClusters, mirrorRGB, proportionFactors, proposalTable, regeneratedSpec, repairPrompt, repairVerdict, residualBlocks, score, setupTargets,
  sheetPrompt, stretchBox, styleOrtho, targetMisses, viewExtra, withFamilies, parseRects, inRects, fixVerdict, keepOverrideRefusal, stopRule, stopRefusal, likeArgs,
} from "./turnaround.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { familyTable, viewFamilyTable } from "../v6/ortho.mjs";

const FACTS = {
  noun: "test van",
  description: "A box van with a striped awning on its left flank.",
  proportions: "at a width of 2 m it is 5 m long and 3 m tall.",
  sides: "the awning is on the LEFT flank only.",
  shape: { side: "side shape", front: "front shape", rear: "rear shape", top: "top shape" },
  faces: { rear: "Two rear doors on the back face." },
  asymmetric: [{ part: "the striped awning", plural: false, flank: "left", along: null, protrudes: true }],
  dims: { L: 5, W: 2, H: 3 },
};
const T = loadTemplates();

const summary = (vo, cob, resid = {}, aspect = null) => ({
  views: Object.fromEntries(Object.entries(vo).map(([v, x]) => [v, { viewOnly: x }])),
  worstViewOnly: Math.max(...Object.values(vo)), worstView: Object.entries(vo).sort((a, b) => b[1] - a[1])[0][0],
  conceptOnlyBlob: cob, residuals: resid, residualMax: Math.max(0, ...Object.values(resid).flatMap((p) => Object.values(p).map(Math.abs))),
  ...(aspect ? { aspect } : {}),
});

test("the template doc parses into its five blocks", () => {
  assert.match(T.sheet, /^One image: a 2 x 2 orthographic turnaround sheet/);
  assert.match(T.repair, /Image 1 is the current \{VIEW\} view/);
  assert.deepEqual(Object.keys(T.views).sort(), ["front", "rear", "side", "top"]);
  assert.match(T.projection, /never its length/);
  assert.ok(T.drafts.mirror && T.drafts.proportion);
});

test("fillTemplate fills dotted keys and refuses a missing value or a surviving brace", () => {
  assert.equal(fillTemplate("a {x} b {y.z}", { x: 1, y: { z: "q" } }), "a 1 b q");
  assert.throws(() => fillTemplate("a {missing}", {}), /no value for \{missing\}/);
  assert.throws(() => fillTemplate("a {x}", { x: { nested: 1 } }), /no value/);
  assert.throws(() => fillTemplate("a {x} }", { x: 1 }), /brace survives/);
});

test("the sheet prompt: every placeholder filled, the style orthographic, the awning on the right image side per view", () => {
  const p = sheetPrompt(T, FACTS);
  assert.doesNotMatch(p, /[{}]/);
  assert.doesNotMatch(p, /isometric view, 30 degree/);
  assert.match(p, /True orthographic elevation, no perspective\./);
  const lineOf = (tag) => p.split("\n").find((l) => l.startsWith(`- ${tag} view`));
  assert.match(lineOf("FRONT"), /awning sticks out beyond the body outline on the RIGHT of the image only/);
  assert.match(lineOf("REAR"), /on the LEFT of the image only.*Two rear doors|Two rear doors.*on the LEFT of the image only/);
  assert.match(lineOf("TOP"), /at the BOTTOM of the image only/);
  assert.match(lineOf("SIDE"), /on this flank/);
  assert.equal(styleOrtho("Orthographic isometric view, 30 degree elevation, 45 degree azimuth from front-left, no perspective, vertical edges perfectly vertical. Rest."), "True orthographic elevation, no perspective. Rest.");
});

test("asymmetric parts: a right-flank part flips every image side; `along` reaches the top view's ends", () => {
  const right = { part: "the exhaust stack", flank: "right", along: "front", protrudes: false };
  assert.match(asymSentence(right, "front", "tractor"), /on the LEFT half of the image/);
  assert.match(asymSentence(right, "rear", "tractor"), /on the RIGHT half of the image/);
  assert.match(asymSentence(right, "top", "tractor"), /upper half of the plan, toward the LEFT end/);
  assert.match(asymSentence(right, "side", "tractor"), /far \(right\) side and not drawn/);
  const beacon = { part: "the beacon", flank: "left", along: "rear", protrudes: false };
  assert.match(asymSentence(beacon, "top", "forklift"), /lower half of the plan, toward the RIGHT end/);
  assert.equal(viewExtra({ ...FACTS, faces: {}, asymmetric: [] }, "front"), "");
});

test("the repair prompt: mirror drafts only for front / rear, naming the other end view", () => {
  const p = repairPrompt(T, FACTS, "rear", "mirror");
  assert.match(p, /^One image: the REAR view of the test van/);
  assert.match(p, /mirroring the FRONT view/);
  assert.match(p, /Do not copy any front-face part/);
  assert.match(p, /The view: REAR view: looking straight at the rear face.*rear shape\. Two rear doors/);
  assert.doesNotMatch(p, /[{}]/);
  assert.throws(() => repairPrompt(T, FACTS, "top", "mirror"), /only for front \/ rear/);
  assert.match(repairPrompt(T, FACTS, "top", "proportion"), /re-proportioned to the measured dimensions/);
});

test("checkFacts names what is missing", () => {
  assert.throws(() => checkFacts({ ...FACTS, dims: { L: 5, W: 2 } }), /dims\.H/);
  assert.throws(() => checkFacts({ ...FACTS, asymmetric: [{ part: "x", flank: "up" }] }), /asymmetric\[0\]/);
  assert.equal(checkFacts(FACTS), FACTS);
});

test("the setup targets and the keep numbers come from gold.config.json setupHull (+ the doctor's residual band)", () => {
  assert.deepEqual({ ...TARGETS, keep: { ...TARGETS.keep } }, { viewOnly: 0.03, conceptOnlyBlob: 0.025, aspect: 0.03, residual: 0.03, keep: { viewOnlyDrop: 0.003, conceptOnlyBlobRise: 0.0025, aspectGrow: 0.005 } });
  const T2 = setupTargets({ setupHull: { viewOnly: { warn: 0.02 }, conceptOnlyBlob: { warn: 0.01 }, aspect: { warn: 0.05 }, keep: { viewOnlyDrop: 0.01 } } });
  assert.deepEqual([T2.viewOnly, T2.conceptOnlyBlob, T2.aspect, T2.keep.viewOnlyDrop, T2.keep.aspectGrow], [0.02, 0.01, 0.05, 0.01, 0.005]);
});

test("KEEP at SET level: every target met -> KEEP; else worst viewOnly -0.3 pts AND conceptOnlyBlob +<= 0.25 pts AND |aspect| +<= 0.5 pts AND no new residual BLOCK; a copy never", () => {
  const A = (h, l) => ({ HoverW: h, LoverW: l });
  // garbage_truck repair-2 (2026-09-27): its own view's viewOnly rose 1.59 -> 2.14 %, but the set meets every target
  const gb = summary({ side: 0.0009, front: 0.0368, rear: 0.0159, top: 0.0159 }, 0.0202, { W: { front: 0.002, rear: -0.042, top: 0.04 } }, A(0.01, -0.01));
  const ga = summary({ side: 0.0009, front: 0.021, rear: 0.0214, top: 0.0159 }, 0.0233, { W: { front: 0.01, rear: -0.019, top: 0.009 } }, A(0.01, -0.012));
  const g = repairVerdict(gb, ga, "rear");
  assert.deepEqual([g.verdict, g.met], ["KEEP", true]);
  // forklift repair-2: rear 7.3 -> 3.3 % (worst 7.3 -> 3.9 front) but conceptOnlyBlob +0.46 pts -> REVERT; +0.18 pts -> KEEP
  const fb = summary({ side: 0.001, front: 0.039, rear: 0.073, top: 0.002 }, 0.0448, {}, A(-0.02, 0.01));
  const r1 = repairVerdict(fb, summary({ side: 0.001, front: 0.039, rear: 0.033, top: 0.002 }, 0.0494, {}, A(-0.02, 0.01)), "rear");
  assert.equal(r1.verdict, "REVERT");
  assert.match(r1.reasons.join(";"), /conceptOnlyBlob rose/);
  assert.equal(repairVerdict(fb, summary({ side: 0.001, front: 0.039, rear: 0.032, top: 0.002 }, 0.0466, {}, A(-0.02, 0.01)), "rear").verdict, "KEEP");
  // the worst viewOnly must drop by >= 0.3 pts (0.29 is not enough)
  const b = summary({ side: 0.001, front: 0.05, rear: 0.14, top: 0.007 }, 0.03, {}, A(0, 0));
  assert.equal(repairVerdict(b, summary({ side: 0.001, front: 0.05, rear: 0.1371, top: 0.007 }, 0.03, {}, A(0, 0)), "rear").verdict, "REVERT");
  assert.equal(repairVerdict(b, summary({ side: 0.001, front: 0.05, rear: 0.137, top: 0.007 }, 0.03, {}, A(0, 0)), "rear").verdict, "KEEP");
  // |aspect| growing by > 0.5 pts in either ratio (a sign flip counts by magnitude)
  const asp = repairVerdict(b, summary({ side: 0.001, front: 0.05, rear: 0.05, top: 0.007 }, 0.03, {}, A(-0.006, 0)), "rear");
  assert.equal(asp.verdict, "REVERT");
  assert.match(asp.reasons.join(";"), /aspect H\/W/);
  assert.equal(repairVerdict(b, summary({ side: 0.001, front: 0.05, rear: 0.05, top: 0.007 }, 0.03, {}, A(-0.005, 0.004)), "rear").verdict, "KEEP");
  // a new residual BLOCK (D, view) reverts; an old one getting worse does not count as new
  const rb = summary({ side: 0.001, front: 0.05, rear: 0.14, top: 0.007 }, 0.03, { W: { rear: -0.05, top: 0.02 } }, A(0, 0));
  const nb = repairVerdict(rb, summary({ side: 0.001, front: 0.05, rear: 0.05, top: 0.007 }, 0.03, { W: { rear: -0.06, top: 0.031 } }, A(0, 0)), "rear");
  assert.equal(nb.verdict, "REVERT");
  assert.match(nb.reasons.join(";"), /new residual BLOCK W top/);
  assert.equal(repairVerdict(rb, summary({ side: 0.001, front: 0.05, rear: 0.05, top: 0.007 }, 0.03, { W: { rear: -0.06, top: 0.02 } }, A(0, 0)), "rear").verdict, "KEEP");
  assert.deepEqual(residualBlocks(rb), ["W rear"]);
  const c = repairVerdict(b, ga, "rear", { copyOf: "image 2 (the draft)" });
  assert.equal(c.verdict, "REVERT");
  assert.match(c.reasons[0], /copy of image 2/);
});

test("the proportion draft uses the concept's proportions when aspect is off, facts.json dims otherwise", () => {
  const facts = { W: 2.5, L: 7.1, H: 3.43 };
  const sm = { dims: { W: 2.5, L: 5.0, H: 3.3 }, aspect: { HoverW: 0.1, LoverW: -0.02 } };
  const d = draftDims(sm, facts);
  assert.ok(Math.abs(d.dims.H - 3.0) < 1e-12 && Math.abs(d.dims.L - 5.0 / 0.98) < 1e-12 && d.dims.W === 2.5, JSON.stringify(d));
  assert.match(d.from, /the concept's proportions/);
  assert.equal(draftDims({ ...sm, aspect: { HoverW: 0.03, LoverW: -0.02 } }, facts).dims, facts);
  assert.equal(draftDims({ dims: sm.dims }, facts).from, "facts.json dims");
});

test("the attempt choice: the lowest conceptOnlyBlob + worst viewOnly, ties to the earlier, failures skipped", () => {
  const a = { id: "attempt-0", summary: summary({ side: 0, front: 0.05, rear: 0.14, top: 0.01 }, 0.024) };
  const b = { id: "attempt-1", summary: summary({ side: 0, front: 0.06, rear: 0.04, top: 0.01 }, 0.03) };
  const c = { id: "attempt-2", summary: summary({ side: 0, front: 0.06, rear: 0.04, top: 0.01 }, 0.03) };
  assert.equal(score(a.summary), 0.164);
  assert.equal(chooseAttempt([a, b, c]), "attempt-1");
  assert.equal(chooseAttempt([{ id: "attempt-9", error: "x" }, c, b]), "attempt-2");
  assert.equal(chooseAttempt([{ id: "x" }]), null);
});

test("targets: viewOnly <= 3 %, conceptOnlyBlob <= 2.5 %, |aspect| <= 3 % per ratio, residual within +-3 %", () => {
  assert.deepEqual(targetMisses(summary({ side: 0.001, front: 0.03, rear: 0.029, top: 0 }, 0.025, { W: { front: 0.03, top: -0.029 } }, { HoverW: 0.03, LoverW: -0.03 })), []);
  const m = targetMisses(summary({ side: 0.001, front: 0.031, rear: 0.02, top: 0 }, 0.0251, { W: { rear: 0.107 }, H: { side: -0.031 } }, { HoverW: 0.074, LoverW: -0.031 }));
  assert.deepEqual(m, ["viewOnly front 3.1 %", "conceptOnlyBlob 2.51 %", "aspect H/W +7.4 %", "aspect L/W -3.1 %", "residual W rear +10.7 %", "residual H side -3.1 %"]);
});

test("per-view families: clusters of a view, ONE colour offset, the proposal table (a view drawn +10 lighter keeps its families)", () => {
  const table = familyTable([], { table: { body: ["#43863b", "#367131"], hopper: "#2d5c34", dark: "#26292c" }, body: "body" });
  // a 100 px 'view': 60 body px, 25 hopper px, 15 dark px, all drawn 10 lighter than the concept's colours
  const px = [...Array(60).fill([0x43 + 10, 0x86 + 10, 0x3b + 10]), ...Array(25).fill([0x2d + 10, 0x5c + 10, 0x34 + 10]), ...Array(15).fill([0x26 + 10, 0x29 + 10, 0x2c + 10])];
  const data = Buffer.from(px.flat());
  const fam = new Uint8Array(100).fill(1);
  const { fg, clusters } = colourClusters(data, 3, fam);
  assert.equal(fg, 100);
  assert.deepEqual(clusters.map((c) => Math.round(c.share * 100)), [60, 25, 15]);
  const m = matchClusters(clusters, table);
  assert.ok(m.offset.every((v) => Math.abs(v - 10) < 0.01), JSON.stringify(m.offset));
  assert.deepEqual(m.rows.map((r) => r.family), ["body", "hopper", "dark"]);
  assert.ok(m.rows.every((r) => r.d < 0.01 && !r.ambiguous && !r.far));
  const vt = proposalTable(m.rows, table, m.offset);
  assert.deepEqual(vt, { body: ["#4d9045", "#407b3b"], hopper: ["#37663e"], dark: ["#303336"] });
  // an unambiguous cluster off the moved anchors joins its family; the anchors always stay
  const extra = proposalTable([{ rgb: [0x55, 0x99, 0x4a], share: 0.2, family: "body", d: 12, major: true, ambiguous: false, far: false }], table, [0, 0, 0]);
  assert.deepEqual(extra.body, ["#43863b", "#367131", "#55994a"]);
  assert.deepEqual(proposalTable([{ rgb: [0x3c, 0x6c, 0x38], share: 0.02, family: "body", d: 8, major: true, ambiguous: true, far: false }], table).body, ["#43863b", "#367131"]);
  // the offset is capped (FAMILIES.maxOffset): a view drawn 40 darker is not re-read as another family's colours
  const dark = colourClusters(Buffer.from(px.map((c) => c.map((v) => v - 50)).flat()), 3, fam).clusters;
  const md = matchClusters(dark, table);
  assert.ok(Math.hypot(...md.offset) <= FAMILIES.maxOffset + 1e-9, JSON.stringify(md.offset));
  // viewFamilyTable: the view's own colours for the named families, names / indices unchanged; absent -> the table itself
  const t2 = viewFamilyTable(table, { viewTable: { side: vt } }, "side");
  assert.deepEqual(t2.names, table.names);
  assert.deepEqual(t2.rgb[table.names.indexOf("hopper")], [[0x37, 0x66, 0x3e]]);
  assert.equal(viewFamilyTable(table, { viewTable: { side: vt } }, "front"), table);
  assert.equal(viewFamilyTable(table, {}, "side"), table);
  assert.throws(() => viewFamilyTable(table, { viewTable: { side: { cab: "#ffffff" } } }, "side"), /"cab" is not a family/);
});

test("views.json families block rewrite: the rest of the file byte-identical, strings with braces skipped", () => {
  const text = [
    "{",
    '  "_comment": "a {brace} and a \\"quote\\"",',
    '  "views": { "side": { "file": "side.png" } },',
    '  "families": {',
    '    "body": "body",',
    '    "table": { "body": ["#43863b", "#367131"] }',
    "  },",
    '  "tail": [1, 2]',
    "}",
    "",
  ].join("\n");
  const span = jsonValueSpan(text, "families");
  assert.equal(text.slice(span[0], span[0] + 1), "{");
  assert.equal(text.slice(span[1] - 1, span[1]), "}");
  const out = withFamilies(text, { ...JSON.parse(text).families, viewTable: { side: { body: ["#498840"] } }, _viewTable: "note {x}" });
  const j = JSON.parse(out);
  assert.deepEqual(j.families.viewTable, { side: { body: ["#498840"] } });
  assert.equal(j._comment, 'a {brace} and a "quote"');
  assert.equal(out.slice(0, span[0]), text.slice(0, span[0]));
  assert.equal(out.slice(out.length - (text.length - span[1])), text.slice(span[1]));
  assert.ok(out.includes('\n    "viewTable": {\n      "side": { "body": ["#498840"] }\n    },'), out);
});

test("draft geometry: proportion factors per view, the canvas fit, the mirror", () => {
  const f = proportionFactors("rear", { W: 300, H: 360 }, { W: 2.5, H: 2.72 });
  assert.ok(Math.abs(f.kx - (2.5 / 2.72) / (300 / 360)) < 1e-12);
  assert.equal(f.ky, 1);
  const t = proportionFactors("top", { W: 200, L: 800 }, { W: 2.5, L: 7.2 });
  assert.equal(t.kx, 1);
  assert.ok(Math.abs(t.ky - (2.5 / 7.2) / 0.25) < 1e-12);
  const s = proportionFactors("side", { L: 800, H: 400 }, { L: 6, H: 2.5 });
  assert.ok(Math.abs(s.kx - 1.2) < 1e-12);
  assert.throws(() => proportionFactors("concept", {}, {}), /no proportion draft/);
  assert.deepEqual(stretchBox(400, 300, 1.25, 1, 1024), { w: 500, h: 300, fit: 1 });
  const big = stretchBox(900, 300, 1.2, 1, 1024, 8);
  assert.equal(big.w, 1008);
  assert.equal(big.h, Math.round(300 * (1008 / 1080)));
  const img = { data: Buffer.from([255, 0, 0, 0, 0, 255, 1, 2, 3]), width: 3, height: 1 };
  const m = mirrorRGB(img);
  assert.deepEqual([...m.data], [1, 2, 3, 0, 0, 255, 255, 0, 0]);
  assert.deepEqual([...mirrorRGB(m).data], [...img.data]);
});

test("views.json for a regenerated set drops the per-view measured keys, keeps the concept's, adds _note after _comment", () => {
  const spec = {
    _comment: "c",
    views: { side: { file: "side.png", right: [0, 0, -1], up: [0, 1, 0] }, top: { file: "top.png", right: [0, 0, -1], up: [-1, 0, 0], shift: { up: 0.16 }, _shift: "why" } },
    anchor: { dim: "W", m: 2 },
    families: { body: "body", holes: { top: [[1, 2]], concept: [[3, 4]] } },
    drift: { audited: "x", top: [{ id: "D1", rect: [0, 0, 5, 5] }], concept: [{ id: "D2", rect: [1, 1, 4, 4] }] },
  };
  const { spec: out, dropped } = regeneratedSpec(spec, "regenerated.");
  assert.deepEqual(dropped.sort(), ["drift.top", "holes.top", "top.shift"]);
  assert.deepEqual(Object.keys(out).slice(0, 2), ["_comment", "_note"]);
  assert.match(out._note, /^regenerated\. Dropped \(measured on the previous images\): /);
  assert.equal(out.views.top.shift, undefined);
  assert.equal(out.views.top._shift, undefined);
  assert.deepEqual(out.families.holes, { concept: [[3, 4]] });
  assert.deepEqual(Object.keys(out.drift), ["audited", "concept"]);
  assert.equal(spec.views.top.shift.up, 0.16);   // the input is not mutated
  const clean = regeneratedSpec({ _comment: "c", views: { side: { file: "side.png" } } }, "n.");
  assert.deepEqual(clean.dropped, []);
  assert.match(clean.spec._note, /none present/);
});

test("proportions against facts.json dims are anchor-free ratios", () => {
  assert.deepEqual(factsDeviation({ W: 2.5, L: 7.018, H: 3.12 }, { W: 2.5, L: 7.22, H: 2.71 }), { "L/W": -0.028, "H/W": 0.1513 });
  assert.deepEqual(factsDeviation({ W: 2.0, L: 3.434, H: 3.297 }, { W: 2.5, L: 4.7, H: 4.7 }), { "L/W": -0.0867, "H/W": -0.1231 });
  assert.deepEqual(factsDeviation({ W: 2 }, { W: 2, L: 4 }), {});
});

test("fix --rects: half-open audit rects; an EDIT may move the foreground but never a px outside the rects", () => {
  const R = parseRects("355,338,392,392; 632,338,669,392");
  assert.deepEqual(R, [[355, 338, 392, 392], [632, 338, 669, 392]]);
  assert.equal(inRects(R, 355, 338), true);
  assert.equal(inRects(R, 391, 391), true);
  assert.equal(inRects(R, 392, 350), false, "x1 is outside (half-open, like drift rects)");
  for (const bad of ["", "1,2,3", "5,5,4,9", "a,b,c,d", "1.5,2,3,4"]) assert.throws(() => parseRects(bad), /--rects/);
  // without rects: the 0.5 % foreground rule (a recolour)
  assert.equal(fixVerdict({ why: "w", changed: 900, moved: 0.004 }).verdict, "KEEP");
  assert.equal(fixVerdict({ why: "w", changed: 900, moved: 0.0149 }).verdict, "REVERT");
  // with rects: the foreground may move (a part added), any px outside the rects reverts
  assert.equal(fixVerdict({ why: "w", changed: 2100, moved: 0.0149, rects: R, outside: 0 }).verdict, "KEEP");
  const out = fixVerdict({ why: "w", changed: 2100, moved: 0.0149, rects: R, outside: 3 });
  assert.equal(out.verdict, "REVERT");
  assert.match(out.reasons[0], /3 px changed outside/);
});

test("verdict --keep --ruling: only a REVERTed repair of the current set, never a copy, fix or rejudge", () => {
  const rep = { id: "repair-9-top-gpt-proportion", verdict: "REVERT", rule: "set", reasons: ["worst viewOnly ... did not drop"] };
  assert.equal(keepOverrideRefusal(rep), null);
  assert.match(keepOverrideRefusal({ ...rep, verdict: "KEEP" }), /only a REVERTed/);
  assert.match(keepOverrideRefusal({ ...rep, verdict: "FAILED" }), /only a REVERTed/);
  assert.match(keepOverrideRefusal({ ...rep, rule: "fix" }), /fix record/);
  assert.match(keepOverrideRefusal({ ...rep, rejudgeOf: "repair-2" }), /rejudge record/);
  assert.match(keepOverrideRefusal({ ...rep, reasons: ["the generated view is a copy of image 1 (the current view)"] }), /copy/);
  assert.match(keepOverrideRefusal({ ...rep, override: { by: "ruling" } }), /overridden already/);
  assert.match(keepOverrideRefusal(rep, ["rear"]), /differs from current\/ in rear/);
});

test("setup stop rule (gold.config.json setupStop): gen refused after 3 failed sets, a view's repair after 3 failed repairs of it", () => {
  const good = { views: { side: { viewOnly: 0.01 } }, conceptOnlyBlob: 0.01, residuals: {}, aspect: { HoverW: 0, LoverW: 0 } };
  const bad = { ...good, conceptOnlyBlob: 0.05 };
  assert.deepEqual(targetMisses(bad), ["conceptOnlyBlob 5.00 %"]);
  const st = { attempts: [{ id: "attempt-0", summary: bad }, { id: "attempt-1", summary: good }], repairs: [] };
  assert.equal(stopRefusal(stopRule(st), "gen"), null);
  st.attempts.push({ id: "attempt-2", error: "no image" }, { id: "attempt-3", summary: bad });
  assert.match(stopRefusal(stopRule(st), "gen"), /gen refused by the setup stop rule: 3 failed whole-set regenerations .*--owner-override/);
  const rp = { attempts: [{ id: "attempt-0", summary: good }], repairs: ["a", "b", "c"].map((k, i) => ({ id: `repair-${i + 1}-rear-gemini-mirror`, view: "rear", verdict: "REVERT" })) };
  assert.match(stopRefusal(stopRule(rp), "repair", "rear"), /repair rear refused .*3 failed rear repairs/);
  assert.equal(stopRefusal(stopRule(rp), "repair", "top"), null);
  assert.equal(stopRefusal(stopRule(rp), "gen"), null);
});

test("normalize size args: --like the live set only when its side view exists (views.json views.side.file), else a first set's --side-l 800 --canvas 1024", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "turn-like-"));
  const t = path.join(root, "subjects", "nv", "turnaround");
  assert.deepEqual(likeArgs("nv", root), ["--side-l", "800", "--canvas", "1024"]);   // no folder at all
  fs.mkdirSync(t, { recursive: true });
  fs.writeFileSync(path.join(t, "views.json"), JSON.stringify({ views: { side: { file: "side_right.png" } } }));
  fs.writeFileSync(path.join(t, "side.png"), "x");   // not the file views.json names
  assert.deepEqual(likeArgs("nv", root), ["--side-l", "800", "--canvas", "1024"]);
  fs.writeFileSync(path.join(t, "side_right.png"), "x");
  assert.deepEqual(likeArgs("nv", root), ["--like", "subjects/nv/turnaround"]);
  fs.rmSync(root, { recursive: true, force: true });
});
