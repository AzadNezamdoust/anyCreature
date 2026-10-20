// WORKFLOW v5 — V5-2: kernel shapes for rounded / bevelled / hulled stylized targets (research/WF-V5-ACCURACY.md).
// K.profile.fillet / roundRect, K.hull / beam / taper, vehicleBody roofR / capR / cornerR. Hermetic: reads subjects/ and
// classes/; writes only under test/.tmp-*.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/vehicle.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";
import { replaceKnobValues } from "../scripts/knobs.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TMP = path.join(ROOT, "test", `.tmp-v52-${process.pid}`);
await K.init();
if (K.assemble?.ready) await K.assemble.ready;
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `m${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}
const area2 = (pts) => pts.reduce((s, [x0, y0], i) => { const [x1, y1] = pts[(i + 1) % pts.length]; return s + x0 * y1 - x1 * y0; }, 0);
const healthy = (s) => s.status() === "NoError" && s.genus() === 0 && s.decompose().length === 1;
const meshKey = (parts) => createHash("sha256").update(JSON.stringify(parts.map((p) => {
  const m = p.solid.mesh();
  return [p.id, p.zone, p.role, Array.from(m.vertProperties), Array.from(m.triVerts)];
}))).digest("hex");

test("V5-2 fillet: segs + 1 points per corner, arcs of radius r tangent to both edges, chamfer at segs 1, clamp to half the shorter edge", () => {
  const sq = K.profile.rect({ w: 2, h: 2 });           // (-1,0) (1,0) (1,2) (-1,2)
  const f = K.profile.fillet(sq, 0.3, 3);
  assert.equal(f.length, 16);
  assert.ok(area2(f) > 0, "CCW");
  assert.deepEqual(K.profile.poly(f), f, "a simple CCW profile poly() keeps as is");
  // the (1, 2) corner: every arc point 0.3 from (0.7, 1.7), and the two tangent points on the edges
  const arc = f.filter(([x, y]) => x > 0.69 && y > 1.69);
  assert.equal(arc.length, 4);
  for (const [x, y] of arc) assert.ok(Math.abs(Math.hypot(x - 0.7, y - 1.7) - 0.3) < 1e-12);
  assert.ok(arc.some(([x, y]) => Math.abs(x - 1) < 1e-12 && Math.abs(y - 1.7) < 1e-12));
  assert.ok(arc.some(([x, y]) => Math.abs(x - 0.7) < 1e-12 && Math.abs(y - 2) < 1e-12));
  const ch = K.profile.fillet(sq, 0.3, 1);
  assert.equal(ch.length, 8, "segs 1 = a straight chamfer: two points per corner");
  assert.ok(Math.abs(Math.abs(area2(ch)) / 2 - (4 - 4 * 0.045)) < 1e-12);
  // clamp: r 5 on a 2 m square = tangent length 1 = half each edge; neighbouring arcs share the midpoint
  const big = K.profile.fillet(sq, 5, 3);
  assert.equal(big.length, 12);
  for (const [x, y] of big) assert.ok(Math.abs(Math.hypot(x, y - 1) - 1) < 1e-12, "a full circle of radius 1");
  // r = 0 keeps the profile, collinear points stay
  assert.deepEqual(K.profile.fillet(sq, 0, 3), sq);
  assert.equal(K.profile.fillet([[-1, 0], [0, 0], [1, 0], [1, 2], [-1, 2]], 0.2, 2).length, 1 + 4 * 3);
});

test("V5-2 fillet: r[] per input point survives a clockwise input; bad arguments throw BAD_ARG", () => {
  const cw = [[-1, 0], [-1, 2], [1, 2], [1, 0]];        // clockwise; round only input point 2, (1, 2)
  const f = K.profile.fillet(cw, [0, 0, 0.5, 0], 4);
  assert.equal(f.length, 3 + 5);
  assert.ok(area2(f) > 0);
  assert.ok(!f.some(([x, y]) => x === 1 && y === 2), "(1, 2) is rounded");
  assert.ok(f.some(([x, y]) => x === 1 && y === 0) && f.some(([x, y]) => x === -1 && y === 2), "the others stay sharp");
  assert.throws(() => K.profile.fillet(cw, -0.1), /BAD_ARG/);
  assert.throws(() => K.profile.fillet(cw, 0.1, 0), /BAD_ARG/);
  assert.throws(() => K.profile.fillet(cw, [0.1, 0.1]), /BAD_ARG/);
  assert.throws(() => K.profile.fillet([[0, 0], [1, 0]], 0.1), /BAD_PROFILE/);
});

test("V5-2 roundRect: 4 (segs + 1) points, radius clamp, {w, h} and bounds frames; the mirror head's old outline exactly", () => {
  const rr = K.profile.roundRect({ w: 2, h: 1, r: 0.2, segs: 3 });
  assert.equal(rr.length, 16);
  assert.ok(area2(rr) > 0);
  const b = rr.reduce((a, [x, y]) => [Math.min(a[0], x), Math.max(a[1], x), Math.min(a[2], y), Math.max(a[3], y)], [Infinity, -Infinity, Infinity, -Infinity]);
  assert.deepEqual(b.map((v) => Math.round(v * 1e12) / 1e12), [-1, 1, 0, 1]);
  assert.equal(K.profile.roundRect({ w: 2, h: 1, r: 9, segs: 3 }).length, 14, "clamped to 0.5: the short sides' arcs meet");
  assert.equal(K.profile.roundRect({ w: 2, h: 1 }).length, 4);
  assert.throws(() => K.profile.roundRect({ w: 2, h: 1, r: -1 }), /BAD_ARG/);
  // the private assemblies.mjs roundRect it replaces (V4-5A mirror head), byte for byte
  const old = (x0, x1, y0, y1, r, k) => {
    const pts = [];
    for (const [cx, cy, a0] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]]) {
      for (let j = 0; j <= k; j += 1) {
        const a = ((a0 + (90 * j) / k) * Math.PI) / 180;
        pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
      }
    }
    return pts;
  };
  assert.deepEqual(K.profile.roundRect({ x: [1.1235, 1.3035], y: [1.402, 1.582], r: 0.05, segs: 2 }), old(1.1235, 1.3035, 1.402, 1.582, 0.05, 2));
  const heads = K.assemble.mirror({ side: 1, centreX: 0, centreY: 1.5, z: 1, head: { w: 0.2, h: 0.3, round: 0.06 }, arm: 0.1 });
  assert.ok(heads.every((p) => healthy(p.solid)));
});

test("V5-2 hull / beam / taper: manifold-valid, deterministic, tri counts", () => {
  const h = K.hull(K.box([1, 1, 1]), K.box([0.5, 0.5, 0.5]).at([2, 0, 0]));
  assert.ok(healthy(h));
  assert.equal(h.triCount(), 20);
  assert.ok(h.volume() > 1 + 0.125);
  assert.equal(meshKey([{ id: "a", solid: h }]), meshKey([{ id: "a", solid: K.hull([K.box([1, 1, 1]), K.box([0.5, 0.5, 0.5]).at([2, 0, 0])]) }]));
  const tet = K.hull([0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  assert.ok(healthy(tet));
  assert.equal(tet.triCount(), 4);
  assert.ok(Math.abs(tet.volume() - 1 / 6) < 1e-9);
  assert.throws(() => K.hull([0, 0, 0], [1, 0, 0], [0, 1, 0]), /BAD_ARG: hull is flat/);
  assert.throws(() => K.hull(), /BAD_ARG/);

  const bm = K.beam([0, 0, 0], [1, 1, 0.5], { w: 0.1, h: 0.2 });
  assert.ok(healthy(bm));
  assert.equal(bm.triCount(), 12);
  assert.ok(Math.abs(bm.volume() - 0.1 * 0.2 * 1.5) < 1e-9, "a prism w x h x length");
  const up = K.beam([0, 0, 0], [0, 2, 0], { w: 0.1, h: 0.2 });
  assert.deepEqual(up.aabb().max.map((v) => Math.round(v * 1e9) / 1e9), [0.05, 2, 0.1], "vertical: w along x, h along z");
  const tapered = K.beam([0, 0, 0], [0, 0, 1], { w: [0.2, 0.1], h: [0.2, 0.1] });
  assert.ok(healthy(tapered));
  assert.ok(Math.abs(tapered.volume() - (1 / 3) * (0.04 + 0.01 + 0.02)) < 1e-9, "a frustum");
  assert.throws(() => K.beam([0, 0, 0], [0, 0, 0], { w: 0.1, h: 0.1 }), /BAD_ARG/);
  assert.throws(() => K.beam([0, 0, 0], [1, 0, 0], { w: 0, h: 0.1 }), /BAD_ARG/);

  const tp = K.taper(K.profile.rect({ w: 1, h: 1 }), 2, 0.5);
  assert.ok(healthy(tp));
  assert.equal(tp.triCount(), 12);
  assert.ok(Math.abs(tp.volume() - (2 / 3) * (1 + 0.25 + 0.5)) < 1e-9);
  assert.deepEqual(tp.aabb(), { min: [-0.5, 0, 0], max: [0.5, 1, 2] });
  const tx = K.taper(K.profile.rect({ w: 1, h: 1 }), 1, [1, 0.5]);
  assert.ok(healthy(tx) && Math.abs(tx.volume() - 0.75) < 1e-9);
  const cone = K.taper(K.profile.roundRect({ w: 1, h: 1, r: 0.2, segs: 2 }), 1, 0);
  assert.ok(healthy(cone));
  assert.throws(() => K.taper(K.profile.rect({ w: 1, h: 1 }), 1, -1), /BAD_ARG/);
  assert.throws(() => K.taper(K.profile.rect({ w: 1, h: 1 }), 0, 1), /BAD_ARG/);
  // a filleted profile extrudes clean
  const fe = K.extrude(K.profile.fillet(K.profile.rect({ w: 2, h: 2 }), 0.3, 3), 1);
  assert.ok(healthy(fe));
  assert.equal(fe.triCount(), 60);
});

test("V5-2 vehicleBody: rounding defaults are byte-identical (bus build with the knobs at 0 = without them; pickup template sha)", async () => {
  const sha = createHash("sha256").update(generateForSubject("pickup").text).digest("hex");
  assert.equal(sha, "da7b65596be93da3a30246ce137bddaa7b3c543458d166a2a47de29d95b786ec");   // V5-9: keyed knobs ranged by the class prior
  const text = generateForSubject("school_bus").text;
  const line = "    roofR: k.roofR, capR: k.capR, cornerR: k.cornerR,   // V5-2 rounding (0 = sharp)\n";
  assert.ok(text.includes(line));
  const withKnobs = await importText(text);
  for (const n of ["roofR", "capR", "cornerR"]) assert.deepEqual([withKnobs.KNOBS[n].v, withKnobs.KNOBS[n].min], [0, 0], n);
  const without = await importText(text.replace(line, ""));
  assert.equal(meshKey(withKnobs.build()), meshKey(without.build()));
});

test("V5-2 vehicleBody: the rounded bus (roofR, capR, cornerR) passes the full gate within triBudget", async () => {
  const S = loadSubject("school_bus");
  const LAYOUT = S.readJson("layout");
  const CENSUS = Object.fromEntries(Object.entries(S.readJson("census")).filter(([k]) => !k.startsWith("_")));
  const base = generateForSubject("school_bus").text;
  const sharp = (await importText(base)).build();
  const text = replaceKnobValues(base, { roofR: 0.25, capR: 0.6, cornerR: 0.2 });
  const mod = await importText(text);
  const parts = mod.build();
  const cab = parts.find((p) => p.id === "cab");
  const cab0 = sharp.find((p) => p.id === "cab");
  assert.ok(healthy(cab.solid));
  assert.ok(cab.solid.volume() < cab0.solid.volume() - 0.05, "the rounding removed material");
  assert.ok(cab.solid.triCount() > cab0.solid.triCount());
  const bb = cab.solid.aabb();
  const bb0 = cab0.solid.aabb();
  for (let a = 0; a < 3; a += 1) assert.ok(Math.abs(bb.max[a] - bb0.max[a]) < 1e-6 && Math.abs(bb.min[a] - bb0.min[a]) < 1e-6, "the box extents hold");
  const tris = parts.reduce((s, p) => s + p.solid.triCount(), 0);
  assert.ok(tris <= S.cls.triBudget, `${tris} tris`);
  const roles = new Set(parts.map((p) => p.role));
  const census = Object.fromEntries(Object.entries(CENSUS).filter(([k]) => roles.has(S.cls.censusRules[k].role)));
  K.configure(gateConfig(S.cls));
  let report;
  try { report = await validateParts(mod.meta, parts, undefined, { cls: S.cls, rules, layout: LAYOUT, census }); } finally { K.configure(null); }
  assert.equal(report.pass, true, report.text);
});
