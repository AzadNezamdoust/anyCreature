// node --test scripts/v7/lib.test.mjs  — the pure helpers of scripts/v7/lib.mjs
import assert from "node:assert/strict";
import test from "node:test";

import { buildVariant, colourRuns, conceptFirst, coordinateSearch, gridFrames, medianColour, parseArgs, parseStages, projectPoint, unprojectPoint } from "./lib.mjs";

test("parseArgs: flags, booleans, negative-number positionals", () => {
  const a = parseArgs(["--subject", "bus", "-1.2,0,3", "--write", "--scale=2", "x"], ["write"]);
  assert.deepEqual(a, { _: ["-1.2,0,3", "x"], subject: "bus", write: true, scale: "2" });
});

test("project -> unproject round trip on each plane", () => {
  const c = Math.SQRT1_2;
  const reg = { s: 150, ox: 500, oy: 700, basis: { right: [c, 0, -c], up: [-0.34, 0.88, -0.34] } };
  const p = [1.2, 0.5, 3.1];
  const [X, Y] = projectPoint(reg, p);
  for (const ax of ["x", "y", "z"]) {
    const q = unprojectPoint(reg, X, Y, ax, p["xyz".indexOf(ax)]);
    q.forEach((v, k) => assert.ok(Math.abs(v - p[k]) < 1e-9, `${ax}: ${q} vs ${p}`));
  }
  assert.throws(() => unprojectPoint({ ...reg, basis: { right: [1, 0, 0], up: [0, 1, 0] } }, 0, 0, "x", 1), /edge-on/);
});

test("medianColour: per-channel median of a rect", () => {
  const data = Buffer.from([0, 0, 0, 10, 20, 30, 10, 20, 30, 255, 255, 255]);   // 2x2 RGB
  assert.deepEqual(medianColour(data, 2, 3, [0, 0, 2, 2]), [10, 20, 30]);
});

test("colourRuns: rgb tolerance against the run's first px, and labels", () => {
  const px = [[0, 0, 0], [10, 10, 10], [30, 30, 30], [30, 30, 30]];
  assert.deepEqual(colourRuns(px, 5, { tol: 18 }).map((r) => [r.s, r.e]), [[5, 6], [7, 8]]);
  assert.deepEqual(colourRuns(px, 0, { label: (c) => (c[0] > 5 ? "a" : "b") }).map((r) => [r.s, r.e, r.label]), [[0, 0, "b"], [1, 3, "a"]]);
});

test("coordinateSearch climbs to the optimum on the stage grid", async () => {
  const f = async (fr) => -((fr.scale - 1.01) ** 2) * 1e4 - (fr.tx - 6) ** 2 - (fr.ty + 3) ** 2;
  const r = await coordinateSearch(f, { scale: 1, tx: 0, ty: 0 }, parseStages("0.02:8,0.01:4,0.005:2,0.0025:1,0.00125:0.5"));
  assert.ok(Math.abs(r.frame.scale - 1.01) < 0.002 && Math.abs(r.frame.tx - 6) <= 0.5 && Math.abs(r.frame.ty + 3) <= 0.5, JSON.stringify(r.frame));
  assert.equal(gridFrames({ scale: 1, tx: 0, ty: 0 }).length, 125);
});

test("buildVariant: KNOBS set for one build and restored; other keys go to buildWith merged into DEFAULTS", () => {
  const mod = {
    KNOBS: { frameScale: { v: 1 }, w: { v: 2 } },
    DEFAULTS: { bf: { top: 1, bot: 0 }, R: 0.5 },
    build() { return [{ w: this.KNOBS.w.v }]; },
    buildWith(o) { return [{ w: mod.KNOBS.w.v, ...o }]; },
  };
  const a = buildVariant(mod, { w: 3, frameScale: 0.9 });
  assert.equal(a.parts[0].w, 3);
  assert.equal(a.frame.scale, 0.9);
  assert.equal(mod.KNOBS.w.v, 2);
  assert.deepEqual(buildVariant(mod, { bf: { top: 2 } }).parts[0].bf, { top: 2, bot: 0 });
  assert.throws(() => buildVariant(mod, { nope: 1 }), /neither KNOBS nor DEFAULTS/);
});

test("conceptFirst (variants.mjs --rule concept-first): ortho DQ, concept agree, 0.002 tie -> min ortho agree -> BASE", () => {
  const row = (label, side, front, concept) => ({ label, metrics: { views: { side: { iou: 0, agree: side }, front: { iou: 0, agree: front }, concept: { iou: 0, agree: concept } } } });
  const base = row("BASE", 0.95, 0.9, 0.95);
  // #1 loses 0.02 of front agree: disqualified although its concept is best; #2 wins on concept
  let r = conceptFirst([base, row('#1 {"a":1}', 0.95, 0.88, 0.99), row('#2 {"a":2}', 0.95, 0.895, 0.96)]);
  assert.equal(r.winner, "#2");
  assert.deepEqual(r.dq.map((d) => d.tag), ["#1"]);
  assert.match(r.dq[0].reasons[0], /^front agree 0\.8800 < BASE 0\.9000 - 0\.01$/);
  // a drop of exactly 0.01 is not a DQ
  assert.equal(conceptFirst([base, row("#1 x", 0.94, 0.9, 0.96)]).winner, "#1");
  // within 0.002 of the best: the higher min ortho agree wins; equal min ortho -> BASE
  assert.equal(conceptFirst([base, row("#1 x", 0.95, 0.905, 0.9515)]).winner, "#1");
  assert.equal(conceptFirst([base, row("#1 x", 0.95, 0.9, 0.9515)]).winner, "BASE");
  assert.equal(conceptFirst([base, row("#1 x", 0.95, 0.9, 0.953)]).winner, "#1");   // 0.003 better: not a tie
  // two tied variants, same min ortho, BASE out of the band: the higher concept, then the lower #n
  assert.equal(conceptFirst([base, row("#2 y", 0.95, 0.9, 0.96), row("#1 x", 0.95, 0.9, 0.9605)]).winner, "#1");
  assert.equal(conceptFirst([base, row("#2 y", 0.95, 0.9, 0.96), row("#1 x", 0.95, 0.9, 0.96)]).winner, "#1");
  // agree falls back to iou (metrics without drift fields); no BASE -> no winner
  const old = (label, s, c) => ({ label, metrics: { views: { side: { iou: s }, concept: { iou: c } } } });
  assert.equal(conceptFirst([old("BASE", 0.9, 0.9), old("#1 x", 0.9, 0.95)]).winner, "#1");
  assert.equal(conceptFirst([row("#1 x", 1, 1, 1)]).winner, null);
});
