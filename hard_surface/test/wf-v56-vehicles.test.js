// V5-6 (vehicles): the ABSORB guard never loses an exact item; vehicleBody `tread: false` / `liner: false` / plain hub;
// the bus template builds them; the cap-lamp housing stays on the forward-facing surface.
import test from "node:test";
import assert from "node:assert/strict";

import * as K from "../src/kernel/index.mjs";
import { absorbJudge } from "../scripts/loop.mjs";
import { generateForSubject } from "../scripts/template-vehicle.mjs";

await K.init();

const m = (o) => ({ loads: true, iou: 0.95, tris: 100, triBudget: 4000, codes: [], blocking: 0, coverage: { frac: 1, have: 5, total: 5, missing: [] }, zoneRows: [], minZone: 0.8, ...o });

test("V5-6 ABSORB guard: a re-FIT the IoU guard accepts is refused when it loses an exact item", () => {
  const before = m({ accuracy: { exactN: 8 } });
  assert.equal(absorbJudge(m({ iou: 0.96, accuracy: { exactN: 7 } }), before).accept, false);
  assert.match(absorbJudge(m({ iou: 0.96, accuracy: { exactN: 7 } }), before).reasons[0], /exact items 8 -> 7/);
  assert.equal(absorbJudge(m({ iou: 0.96, accuracy: { exactN: 8 } }), before).accept, true);
  assert.equal(absorbJudge(m({ iou: 0.96, accuracy: { exactN: 9 } }), before).accept, true);
  assert.equal(absorbJudge(m({ iou: 0.9505, accuracy: { exactN: 9 } }), before).accept, false, "IoU tier still decides");
});

test("V5-6 vehicleBody: tread false = one tyre part, liner false = no arch liners, a hub without ring / cap = the plain disc", () => {
  const base = {
    W: 2, H: 2, hood: false, bed: null, side: [[2.4, 1.8], [2.2, 2], [-2.4, 2], [-2.4, 0.4], [2.4, 0.4]],
    section: [[-1, 0], [1, 0], [1, 2], [-1, 2]], cab: [-2.4, 2.4], sill: 0.4, clearance: 0.3,
    arches: [{ z: 1.6, halfLength: 0.45, rise: 0.45, n: 2 }, { z: -1.4, halfLength: 0.45, rise: 0.45, n: 2 }],
  };
  const full = K.assemble.vehicleBody({ ...base, wheels: { r: 0.38, z: [1.6, -1.4], hub: { r: 0.2, ring: 0.04, cap: 0.1 } } });
  const lean = K.assemble.vehicleBody({ ...base, liner: false, wheels: { r: 0.38, z: [1.6, -1.4], hub: { r: 0.2 }, tread: false } });
  const ids = (ps) => ps.map((p) => p.id);
  for (const id of ["tread_fl", "arch_fl", "hubring_fl", "hubcap_fl"]) {
    assert.ok(ids(full).includes(id), id);
    assert.ok(!ids(lean).includes(id), id);
  }
  // the one tyre solid spans the full width of the tyre + tread pair
  const a = full.find((p) => p.id === "wheel_fl").solid.aabb(), t = full.find((p) => p.id === "tread_fl").solid.aabb(), b = lean.find((p) => p.id === "wheel_fl").solid.aabb();
  assert.ok(Math.abs((b.max[0] - b.min[0]) - (Math.max(a.max[0], t.max[0]) - Math.min(a.min[0], t.min[0]))) < 2e-3);
});

test("V5-6 bus template: plain hub, one tyre solid, no liner, a wrapped rear bumper from the measured rear wrap", async () => {
  const { text } = generateForSubject("school_bus");
  assert.match(text, /hub: \{ r: k\.hubR \}/);
  assert.match(text, /tread: false/);
  assert.match(text, /liner: false/);
  assert.match(text, /face: "tail", [^\n]*wrap: k\.bumperRWrap/);
  assert.doesNotMatch(text, /hubRing|hubCap/);
  const mod = await import(`data:text/javascript;base64,${Buffer.from(text.replace(/from "[^"]*kernel\/index\.mjs"/, `from "${new URL("../src/kernel/index.mjs", import.meta.url).href}"`)).toString("base64")}`);
  const ids = mod.build().map((p) => p.id);
  assert.ok(ids.includes("bumper_rear") && ids.includes("hub_fl") && !ids.some((i) => /^(tread|arch|hubring|hubcap)_/.test(i)), ids.join(" "));
});
