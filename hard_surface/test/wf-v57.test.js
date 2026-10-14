// V5-7 — thin features measurable (ink centreline + count / pitch profile), plate decks + measured member pitches.
// Hermetic: synthetic masks, the kernel helpers, the template text and the frozen target measurement.
import { test } from "node:test";
import assert from "node:assert/strict";

import * as K from "../src/kernel/index.mjs";
import { validateParts, DEFAULT_LIMITS } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import BUILDING from "../classes/building.json" with { type: "json" };
import { judgeThin, skeletonOf, thinMeasure } from "../scripts/accuracy.mjs";
import { inkPeaks } from "../scripts/measure-target.mjs";
import { generateForSubject } from "../scripts/template-building.mjs";

await K.init();
await K.assemble.ready;

const CFG = BUILDING.likeness.thin;

/** A bw x bh window with `n` vertical members 2 px wide at x0 + i * pitch, rows 5..34: render mask, part ids, boundary,
 *  its ink (both sides of every boundary) and a target ink drawn as the members' outline pair shifted by `dx`. */
function scene({ n = 6, pitch = 10, x0 = 8, targetN = n, targetPitch = pitch, dx = 0 } = {}) {
  const bw = 80, bh = 40, N = bw * bh;
  const Rc = new Uint8Array(N), pl = new Int32Array(N).fill(-1), care = new Uint8Array(N).fill(1);
  for (let i = 0; i < n; i += 1) for (let y = 5; y < 35; y += 1) for (const x of [x0 + i * pitch, x0 + i * pitch + 1]) { Rc[y * bw + x] = 1; pl[y * bw + x] = i; }
  const E = new Uint8Array(N), Rink = new Uint8Array(N);
  const at = (x, y) => (x < 0 || y < 0 || x >= bw || y >= bh ? -1 : pl[y * bw + x]);
  for (let y = 0; y < bh; y += 1) {
    for (let x = 0; x < bw; x += 1) {
      const q = at(x, y);
      const diff = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => at(x + a, y + b) !== q && (q >= 0 || at(x + a, y + b) >= 0));
      if (diff) Rink[y * bw + x] = 1;
      if (q >= 0 && diff) E[y * bw + x] = 1;
    }
  }
  const Tink = new Uint8Array(N);
  for (let i = 0; i < targetN; i += 1) {
    const c = x0 + dx + i * targetPitch;
    for (let y = 4; y < 36; y += 1) for (const x of [c - 1, c + 2]) if (x >= 0 && x < bw) Tink[y * bw + x] = 1;
    for (const y of [4, 35]) for (let x = c - 1; x <= c + 2; x += 1) if (x >= 0 && x < bw) Tink[y * bw + x] = 1;
  }
  return { bw, bh, Rc, E, care, pl, Tink, Rink, role: "baluster" };
}

test("V5-7 item 1: skeletonOf thins a 3-px bar to a 1-px line", () => {
  const bw = 20, bh = 9, m = new Uint8Array(bw * bh);
  for (let y = 3; y <= 5; y += 1) for (let x = 2; x <= 17; x += 1) m[y * bw + x] = 1;
  const s = skeletonOf(m, bw, bh);
  for (let x = 4; x <= 15; x += 1) assert.equal(s[3 * bw + x] + s[4 * bw + x] + s[5 * bw + x], 1, `column ${x}`);
});

test("V5-7 item 1: the ink measure is exact on a matching run and fails a shift, a count and a pitch", () => {
  const ok = thinMeasure(scene(), CFG);
  assert.equal(ok.stroke, true);
  assert.deepEqual(ok.count, { target: 6, render: 6 });
  assert.equal(ok.pitch.target, 10);
  assert.equal(ok.pitch.render, 10);
  assert.equal(judgeThin({ ink: ok }, CFG).status, "exact", JSON.stringify(ok));

  const shifted = thinMeasure(scene({ dx: 4 }), CFG);
  assert.ok(shifted.centrePx > CFG.centrePx, JSON.stringify(shifted));
  assert.ok(judgeThin({ ink: shifted }, CFG).fails.includes("centre"));

  const more = thinMeasure(scene({ targetN: 7 }), CFG);
  assert.deepEqual(more.count, { target: 7, render: 6 });
  assert.ok(judgeThin({ ink: more }, CFG).fails.includes("count"));

  const pitch = thinMeasure(scene({ n: 5, pitch: 14, targetN: 7, targetPitch: 10 }), CFG);
  assert.ok(judgeThin({ ink: pitch }, CFG).fails.some((f) => f === "pitch" || f === "count"), JSON.stringify(pitch));
  // a role outside profileRoles is judged on its centreline only
  assert.equal(thinMeasure({ ...scene({ targetN: 7 }), role: "window" }, CFG).count, null);
});

test("V5-7 item 2: measure-target inkPeaks merges an outline pair into one member", () => {
  const prof = new Array(60).fill(0);
  for (const c of [5, 17, 29, 41]) { prof[c] = 1; prof[c + 3] = 1; }
  assert.deepEqual(inkPeaks(prof, 7).length, 4);
  assert.equal(inkPeaks(prof, 2).length, 8);
});

test("V5-7 item 2: fireEscape deck 'plate' — one plate per deck, no bars / brackets, balusters at the pitch on front AND returns, passes the chain", async () => {
  const block = { id: "wall", solid: K.box([8, 12, 4]).at([0, 0, 2]), zone: "brick", role: "massing" };
  const parts = K.assemble.fireEscape({ wall: [block], centreX: 0, span: 4, depth: 1.4, levels: [3, 6.6], dropLadder: { bottom: 0.8, rungPitch: 0.35 },
    idPrefix: "fe", deck: "plate", balusterPitch: 0.35 });
  const ids = parts.map((p) => p.id);
  assert.deepEqual(ids.filter((id) => /_plate$/.test(id)), ["fe_deck0_plate", "fe_deck1_plate"]);
  assert.equal(ids.filter((id) => /_bar_/.test(id) || /_bracket_/.test(id)).length, 0);
  assert.ok(ids.some((id) => /^fe_deck1_baluster_[lr]_\d+$/.test(id)), "return balusters");
  const front = parts.filter((p) => /^fe_deck1_baluster_\d+$/.test(p.id)).map((p) => p.solid.aabb().min[0]).sort((a, b) => a - b);
  const gaps = front.slice(1).map((x, i) => x - front[i]);
  assert.ok(gaps.every((g) => Math.abs(g - 0.35) < 0.06), JSON.stringify(gaps));
  const rungs = parts.filter((p) => p.id.startsWith("fe_drop_rung")).map((p) => p.solid.aabb().min[1]).sort((a, b) => a - b);
  assert.ok(Math.abs(rungs[1] - rungs[0] - 0.35) < 1e-6);
  const meta = { front: "-Z", class: "building", seed: 1, census: false, layout: false, palette: { brick: "#a85643", iron: "#887768" } };
  const report = await validateParts(meta, [block, ...parts], DEFAULT_LIMITS, { cls: BUILDING, rules: BUILDING_RULES });
  assert.equal(report.pass, true, report.text);
});

test("V5-7 item 2: the facade template builds plate decks + measured, LOCKED member pitches and px-banded pane sizes", () => {
  const { text, knobs } = generateForSubject("facade_brick", { knobs: true });
  assert.match(text, /deck: "plate", balusterPitch: k\.feBaluster/);
  assert.match(text, /dropLadder: \{ bottom: k\.dropBottom, rungPitch: k\.ladderRung \}/);
  assert.match(text, /idPrefix: "roof", rungPitch: k\.ladderRung/);
  for (const n of ["feBaluster", "ladderRung"]) assert.equal(knobs[n].min, knobs[n].max, n);
  // +/- 2 target px of the 550 px face height on the pane height (not the key's +/- 17 %)
  assert.ok(knobs.winH.max - knobs.winH.min < 0.02 * knobs.winH.v * 6, JSON.stringify(knobs.winH));
});
