// WORKFLOW-V3 §7 item 9 — K.assemble.* helpers pass the kernel chain by
// construction, with the building class prior and no census/layout.
import { test } from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";

import * as K from "../src/kernel/index.mjs";
import { validateParts, DEFAULT_LIMITS, KERNEL_LIMIT_DEFAULTS } from "../src/validate/kernel-chain.mjs";
import * as BUILDING_RULES from "../src/validate/rules/building.mjs";
import BUILDING from "../classes/building.json" with { type: "json" };

await K.init();
await K.assemble.ready;

const MIN_FEAT = DEFAULT_LIMITS.styleFloor.building;
const meta = {
  front: "-Z", class: "building", seed: 1, census: false, layout: false,
  palette: { brick: "#a85643", iron: "#887768", frame: "#8b7e73", glass: "#80a9ac", sill: "#be9589" },
};

/** A solid block whose -Z face is the plane z = 0. */
const wall = (W = 8, H = 12, D = 4) => ({ id: "wall", solid: K.box([W, H, D]).at([0, 0, D / 2]), zone: "brick", role: "massing" });

async function gate(parts) {
  const report = await validateParts(meta, parts, DEFAULT_LIMITS, { cls: BUILDING, rules: BUILDING_RULES });
  return report;
}

function assertPass(report) {
  assert.equal(report.pass, true, report.text);
  assert.equal(report.text, "PASS: V0-V7 + V10 clean.");
}

const extent = (p, axis) => { const b = p.solid.aabb(); return b.max[axis] - b.min[axis]; };
function assertFloor(parts) {
  for (const p of parts) {
    for (const axis of [0, 1, 2]) assert.ok(extent(p, axis) >= MIN_FEAT - 1e-9, `${p.id} ${extent(p, axis)} < MIN_FEAT on ${axis}`);
  }
}

test("grate: slots <= deckGapMax, bars >= MIN_FEAT, passes the chain against a wall", async () => {
  const parts = K.assemble.grate({ w: 2.3, d: 1.2, at: [0, 3, 0], idPrefix: "g" });
  assertFloor(parts);
  const bars = parts.filter((p) => p.role === "landing").map((p) => p.solid.aabb()).sort((a, b) => a.min[0] - b.min[0]);
  assert.ok(bars.length >= 3);
  for (let i = 1; i < bars.length; i += 1) {
    assert.ok(bars[i].min[0] - bars[i - 1].max[0] <= KERNEL_LIMIT_DEFAULTS.deckGapMax + 1e-9);
  }
  // A grate alone hangs off the wall; stood on the ground it is a stoop. It is a
  // DECK, not a landing: everything but the guard passes, and V11_LANDING_GUARD
  // (v3-backlog item 3) is the one row that asks for the rails K.assemble.landing adds.
  const report = await gate([wall(), ...parts]);
  assert.deepEqual([...new Set(report.violations.map((v) => v.v))], ["V11_LANDING_GUARD"], report.text);
});

test("landing + drop ladder: gate gap clears V11_LADDER_ACCESS; without it the row fires", async () => {
  const top = 4;
  const drop = K.assemble.ladder({ base: [-0.8, top - 2.4, -1.4], height: 2.4, width: 0.5, idPrefix: "drop" });
  const xs = drop.filter((p) => p.role === "ladder").map((p) => p.solid.aabb());
  const gateAt = [Math.min(...xs.map((b) => b.min[0])), Math.max(...xs.map((b) => b.max[0]))];
  const withGate = K.assemble.landing({ span: 4, depth: 1.4, at: [0, top], wallZ: 0, gateAt, idPrefix: "deck" });
  assertFloor([...withGate, ...drop]);
  assertPass(await gate([wall(), ...withGate, ...drop]));

  const noGate = K.assemble.landing({ span: 4, depth: 1.4, at: [0, top], wallZ: 0, idPrefix: "deck" });
  const report = await gate([wall(), ...noGate, ...drop]);
  assert.equal(report.pass, false);
  assert.equal(report.violations[0].v, "V11_LADDER_ACCESS", report.text);
});

test("ladder: front and side faces, stiles >= MIN_FEAT, pass against a wall", async () => {
  const front = K.assemble.ladder({ base: [1, 0, 0], height: 3, width: 0.5, idPrefix: "lf" });
  const side = K.assemble.ladder({ base: [4, 1, 2], height: 6, width: 0.58, face: "side", idPrefix: "ls" });
  assertFloor([...front, ...side]);
  assert.equal(front.filter((p) => p.role === "ladder").length, 2);
  assert.ok(front.filter((p) => p.role === "rung").length >= 9);
  assertPass(await gate([wall(), ...front, ...side]));
});

// WF-R3 H4 — the flight lands ON its decks: built by fireEscape (landings + flight + drop ladder in one call).
test("fireEscape: ceil(rise / maxRise) equal risers ON both decks, rails in band, passes the chain", async () => {
  const lowY = 3.0, highY = 6.0;
  const block = wall();
  const parts = K.assemble.fireEscape({ wall: [block], centreX: 0, span: 5, depth: 1.4, levels: [lowY, highY], dropLadder: { bottom: 0.8 }, idPrefix: "fe" });
  const f = parts.filter((p) => p.assembly?.helper === "flight");
  assertFloor(f.filter((p) => p.role !== "stringer"));
  const steps = f.filter((p) => p.role === "step").map((p) => p.solid.aabb().max[1]).sort((a, b) => a - b);
  const risers = Math.ceil((highY - lowY) / DEFAULT_LIMITS.v7.step_rise[1] - 1e-9);
  assert.equal(steps.length, risers - 1);
  const levels = [lowY, ...steps, highY];
  for (let i = 1; i < levels.length; i += 1) assert.ok(Math.abs(levels[i] - levels[i - 1] - (highY - lowY) / risers) < 1e-6);
  assert.equal(f.filter((p) => p.role === "railing").length, 2);
  const decks = K.assemble.deckBoxes(parts);
  const a = K.assemble.flightArrivals(f.filter((p) => p.role === "step").map((p) => p.solid.aabb()), decks, DEFAULT_LIMITS.v7.step_rise[1]);
  assert.deepEqual([a.bottomDeck, a.topDeck], [0, 1]);
  assertPass(await gate([block, ...parts]));
});

test("a flight hung in front of its decks is refused: flight({ decks }) and landing({ gateFor })", () => {
  const low = K.assemble.landing({ span: 5, depth: 1.4, at: [0, 3], wallZ: 0, idPrefix: "low" });
  const args = { bottom: [2.0, 3, -1.4], top: [-2.0, 6, -1.4], width: 0.7, idPrefix: "fl" };
  assert.throws(() => K.assemble.flight({ ...args, decks: low }), /BAD_ARG: flight "fl" bottom tread .* is not on a deck/);
  const f = K.assemble.flight(args);
  assert.throws(() => K.assemble.landing({ span: 5, depth: 1.4, at: [0, 3], wallZ: 0, gateFor: f }), /BAD_ARG: landing gateFor: flight "fl" does not arrive/);
});

test("flight with an impossible rise throws a clear error", () => {
  assert.throws(() => K.assemble.flight({ bottom: [0, 1, -1], top: [1, 1.25, -1], width: 0.7 }),
    (e) => e instanceof K.KernelError && /^BAD_ARG: impossible flight rise/.test(e.message) && /step_rise 0\.14\.\.0\.2/.test(e.message));
  assert.throws(() => K.assemble.flight({ bottom: [0, 1, -1], top: [1, 3, -1], width: 0.7, maxRise: 0.3 }), /BAD_ARG: flight maxRise/);
});

test("frame: proud frame, glass, sill on brackets, passes against a wall", async () => {
  const a = K.assemble.frame({ w: 0.8, h: 1.4, at: [-1.5, 3, 0], sill: { depth: 0.12, height: 0.08 }, idPrefix: "wa" });
  const b = K.assemble.frame({ w: 2.6, h: 1.2, at: [1.5, 6, 0], sill: { depth: 0.1, height: 0.06 }, idPrefix: "wb" });
  assertFloor([...a, ...b]);
  assert.deepEqual(a.map((p) => p.role), ["window", "window", "window", "window", "window", "sill", "support", "support"]);
  assertPass(await gate([wall(), ...a, ...b]));
});

// Run 4's P2 layout, rebuilt with the helpers: two landings, one flight, a drop
// ladder and the side roof ladder.
function escape() {
  const W = 7.5, H = 16.5, D = 0.874 * W, rowPitch = 0.283 * H;
  const upperY = 12.525, lowerY = upperY - rowPitch;
  const parts = [{ id: "block", solid: K.box([W, H, D]).at([0, 0, D / 2]), zone: "brick", role: "massing" }];
  parts.push(...K.assemble.fireEscape({ wall: parts, centreX: 0, span: 5.5, depth: 1.4, levels: [lowerY, upperY],
    dropLadder: { bottom: lowerY - 0.16 * H, width: 0.58 }, idPrefix: "fe" }));
  parts.push(...K.assemble.ladder({ base: [W / 2, 0.21 * H, 0.177 * W], height: 16.401 - 0.21 * H, width: 0.58,
    face: "side", idPrefix: "roof" }));
  return parts;
}

test("two-landing escape passes the chain; parts and tris vs run 4's hand-built ironwork", async () => {
  const parts = escape();
  const report = await gate(parts);
  assertPass(report);
  const iron = parts.filter((p) => p.zone === "iron");
  const tris = iron.reduce((sum, p) => sum + p.solid.triCount(), 0);
  // run 4's module imports the kernel relative to subjects/<s>/, so load its text
  // with that import re-pointed at the kernel.
  const here = new URL("./", import.meta.url);
  const text = fs.readFileSync(new URL("../out/facade/run4/P2/facade.mjs", here), "utf8")
    .replace(/from\s+"[^"]*src\/kernel\/index\.mjs"/, `from "${new URL("../src/kernel/index.mjs", here).href}"`);
  const run4 = await import(`data:text/javascript;base64,${Buffer.from(text).toString("base64")}`);
  const hand = run4.build().filter((p) => p.zone === "iron" && p.role !== "ac");
  const handTris = hand.reduce((sum, p) => sum + p.solid.triCount(), 0);
  console.log(`# escape via K.assemble: ${iron.length} parts, ${tris} tris (merged model ${report.measurements.tris}); run 4 hand-built ironwork: ${hand.length} parts, ${handTris} tris`);
  assert.ok(tris <= BUILDING.triBudget);
});

function digest(parts) {
  const hash = crypto.createHash("sha256");
  for (const p of parts) {
    const mesh = p.solid.mesh();
    hash.update(`${p.id}|${p.role}|${p.zone}|${p.embed === true}|`);
    hash.update(Buffer.from(mesh.vertProperties.buffer, mesh.vertProperties.byteOffset, mesh.vertProperties.byteLength));
    hash.update(Buffer.from(mesh.triVerts.buffer, mesh.triVerts.byteOffset, mesh.triVerts.byteLength));
  }
  return hash.digest("hex");
}

test("assemblies are byte-stable across two runs", () => {
  const frames = () => K.assemble.frame({ w: 0.8, h: 1.4, at: [0, 3, 0], sill: { depth: 0.1, height: 0.06 } });
  assert.equal(digest(escape()), digest(escape()));
  assert.equal(digest(frames()), digest(frames()));
});

test("withDefaults replaces the role table without touching the default", () => {
  const custom = K.assemble.withDefaults({ roles: { ...K.assemble.DEFAULT_TABLE.roles, ladder: { stile: "rail_side", rung: "bar" } } });
  const parts = custom.ladder({ base: [0, 0, 0], height: 1, width: 0.5 });
  assert.equal(parts[0].role, "rail_side");
  assert.equal(parts[2].role, "bar");
  assert.equal(K.assemble.ladder({ base: [0, 0, 0], height: 1, width: 0.5 })[0].role, "ladder");
});
