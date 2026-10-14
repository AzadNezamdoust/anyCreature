// blind-r1 B2 follow-up: every APPEARANCE number measure-vehicle froze into
// subjects/pickup/layout.json is GATED by V12_LAYOUT (src/validate/rules/vehicle.mjs),
// so a blind author's wrong lamp, grille, mirror or window size cannot pass unnoticed.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const S = loadSubject("pickup");
const CLS = S.cls;
const LAYOUT = S.readJson("layout");

await K.init();
const smoke = await import("./fixtures/vehicle/smoke.mjs");

const KEYS = [
  "headlight.diameter", "grille.w", "grille.h",
  "mirror.head.w", "mirror.head.h", "mirror.offsetX", "mirror.arm.length",
  "window.front.w", "window.front.bottom",
  "window.side.start", "window.side.end", "window.side.bottom", "window.side.top",
];
/** The frozen scalar per key (a mirrored list contributes its + member). */
const V = Object.fromEntries(KEYS.map((k) => [k, LAYOUT[k].value ?? Math.max(...LAYOUT[k].values)]));

// ---------------------------------------------------------------------------
// Measure harness: the rules only read ctx.records / ctx.cls / ctx.geo, so a key
// can be measured on any part list — also one the generic chain stops earlier on.
// geo mirrors kernel-chain.mjs (groupAssemblies / unionBox / clusters).
// ---------------------------------------------------------------------------
const spanOverlap = (aMin, aMax, bMin, bMax) => Math.min(aMax, bMax) - Math.max(aMin, bMin);
function unionBox(members) {
  const pick = (fn, key, axis) => fn(...members.map((m) => m.aabb[key][axis]));
  return { min: [0, 1, 2].map((a) => pick(Math.min, "min", a)), max: [0, 1, 2].map((a) => pick(Math.max, "max", a)) };
}
function groupAssemblies(records, axes, pad = 0) {
  const parent = records.map((_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  for (let i = 0; i < records.length; i += 1) {
    for (let j = i + 1; j < records.length; j += 1) {
      if (axes.every((a) => spanOverlap(records[i].aabb.min[a], records[i].aabb.max[a], records[j].aabb.min[a], records[j].aabb.max[a]) > -pad - 1e-9)) parent[find(i)] = find(j);
    }
  }
  const groups = new Map();
  records.forEach((r, i) => { const root = find(i); if (!groups.has(root)) groups.set(root, []); groups.get(root).push(r); });
  return [...groups.values()].map((members) => ({ members, box: unionBox(members) }));
}
function clusters(values, eps) {
  const sorted = [...values].sort((a, b) => a - b);
  const out = [];
  let bucket = [];
  for (const v of sorted) { if (bucket.length > 0 && v - bucket[bucket.length - 1] > eps) { out.push(bucket); bucket = []; } bucket.push(v); }
  if (bucket.length > 0) out.push(bucket);
  return out.map((b) => b.reduce((s, x) => s + x, 0) / b.length);
}
const harness = (parts) => ({
  cls: CLS,
  records: parts.map((p) => ({ id: p.id, role: p.role ?? null, zone: p.zone, aabb: p.solid.aabb() })),
  geo: { groupAssemblies, unionBox, clusters },
});
/** key -> [measured values] on `parts`, or null when the key's role is not built. */
function measureKey(parts, key) {
  const ctx = harness(parts);
  const F = RULES.layoutFrame(ctx);
  const rule = RULES.layoutRules[key];
  if (rule.roles.some((role) => !ctx.records.some((r) => r.role === role))) return null;
  return rule.measure(ctx, F).map((m) => m.measured);
}
const tolOf = (key) => LAYOUT[key].tol;
const within = (key, measured) => {
  const e = LAYOUT[key];
  if (Array.isArray(e.values)) {
    const want = [...e.values].sort((a, b) => a - b);
    const got = [...measured].sort((a, b) => a - b);
    return got.length === want.length && got.every((g, i) => Math.abs(g - want[i]) <= e.tol + 1e-9);
  }
  return measured.length > 0 && measured.every((g) => Math.abs(g - e.value) <= e.tol + 1e-9);
};

// ---------------------------------------------------------------------------
// Fixture: the frozen smoke truck + windows, lamps, grille and mirrors built to
// the measured fractions (`over` replaces any of them). Every part is seated 1 mm
// into the body so the chain reaches V12_LAYOUT.
// ---------------------------------------------------------------------------
const slab = (x0, x1, y0, y1, z0, z1) => K.box([x1 - x0, y1 - y0, z1 - z0]).at([(x0 + x1) / 2, y0, (z0 + z1) / 2]);

function appearance(over = {}) {
  const v = { ...V, "window.front.top": 0.93, ...over };
  const parts = smoke.build();
  const F = RULES.layoutFrame(harness(parts));
  const { L, W, H, zFront } = F;
  const cabFront = parts.find((p) => p.id === "cab").solid.aabb().max[2];
  const seam = 0.001;
  const both = (id, zone, role, x0, x1, y0, y1, z0, z1) => {
    parts.push({ id: `${id}_l`, zone, role, solid: slab(x0, x1, y0, y1, z0, z1) });
    parts.push({ id: `${id}_r`, zone, role, solid: slab(-x1, -x0, y0, y1, z0, z1) });
  };

  // side windows: panes on the flanks
  both("window_side", "glass", "window", W / 2 - seam, W / 2 + 0.05, v["window.side.bottom"] * H, v["window.side.top"] * H,
    zFront - v["window.side.end"] * L, zFront - v["window.side.start"] * L);
  // windshield on the cab front face
  parts.push({ id: "window_front", zone: "glass", role: "window",
    solid: slab(-v["window.front.w"] * W / 2, v["window.front.w"] * W / 2, v["window.front.bottom"] * H, v["window.front.top"] * H, cabFront - seam, cabFront + 0.05) });
  // headlights + grille on the nose face
  const hlY = LAYOUT["headlight.centreY"].value * H;
  const hlX = Math.max(...LAYOUT["headlight.offsetX"].values) * W;
  const d = v["headlight.diameter"] * W;
  both("headlight", "lamp", "headlight", hlX - d / 2, hlX + d / 2, hlY - d / 2, hlY + d / 2, zFront - seam, zFront + 0.05);
  const gw = v["grille.w"] * W, gh = v["grille.h"] * H;
  // WF-BLIND-R2 C12: the target's grille is a panel with grille.slots recessed slots (0.02 m deep, >= MIN_FEAT margins, 0.07 m panel)
  const nSlots = LAYOUT["grille.slots"].value;
  const slots = K.union(Array.from({ length: nSlots }, (_, i) => slab(-gw / 2 + 0.05, gw / 2 - 0.05,
    hlY - gh / 2 + ((i + 0.5) * gh) / nSlots - 0.03, hlY - gh / 2 + ((i + 0.5) * gh) / nSlots + 0.03, zFront + 0.05, zFront + 0.08)));
  parts.push({ id: "grille", zone: "grille", role: "grille", solid: K.cut(slab(-gw / 2, gw / 2, hlY - gh / 2, hlY + gh / 2, zFront - seam, zFront + 0.07), slots) });
  // mirrors: arm (along X, off the flank) + head, two parts per side
  const mY = LAYOUT["mirror.centreY"].value * H;
  const mZ = cabFront - 0.08;
  const hw = v["mirror.head.w"] * W, hh = v["mirror.head.h"] * H;
  const inner = "mirror.offsetX" in over ? over["mirror.offsetX"] * W - hw / 2 : W / 2 + v["mirror.arm.length"] * W;
  both("mirror_arm", "mirror", "mirror", W / 2 - seam, inner + seam, mY - 0.025, mY + 0.025, mZ - 0.025, mZ + 0.025);
  both("mirror_head", "mirror", "mirror", inner, inner + hw, mY - hh / 2, mY + hh / 2, mZ - 0.03, mZ + 0.03);
  return parts;
}

const gate = (parts) => validateParts(smoke.meta, parts, undefined, { layout: LAYOUT, cls: CLS, rules: RULES });
const layoutMiss = (report, key) => report.violations.find((x) => x.v === "V12_LAYOUT" && x.measured.startsWith(`${key} `));

// WF-R3 R3-B item 5: the rake is measured now (window.front.top + window.front.topAt), so neither is an UNVERIFIED advisory.
test("every appearance key in layout.json has a rule; the windshield rake keys are measured, never reported unverified", async () => {
  for (const k of [...KEYS, "window.front.top"]) assert.ok(RULES.layoutRules[k], `rule for ${k}`);
  for (const k of KEYS) assert.ok(!LAYOUT[k].unverified && Number.isFinite(LAYOUT[k].tol), `${k} verified with tol`);
  const report = await gate(appearance());
  assert.equal(report.pass, true, report.text);
  for (const k of ["window.front.top", "window.front.topAt"]) {
    assert.ok(RULES.layoutRules[k] && !LAYOUT[k].unverified && LAYOUT[k].evidence?.px, k);
    assert.ok(!report.advisories.some((a) => a.v === "V12_LAYOUT" && a.measured.startsWith(`${k} UNVERIFIED`)), k);
  }
});

test("each appearance rule measures the fixture built to the measured numbers inside its tol", () => {
  const parts = appearance();
  for (const k of KEYS) {
    const got = measureKey(parts, k);
    assert.ok(got && got.length > 0, `${k} measured`);
    assert.ok(within(k, got), `${k} measured ${got.map((x) => x.toFixed(3))} vs ${V[k]} +/- ${tolOf(k)}`);
  }
});

test("a role not built yet stands down: the P0 smoke truck measures none of the appearance keys", async () => {
  const parts = smoke.build();
  for (const k of KEYS) assert.equal(measureKey(parts, k), null, k);
  const report = await gate(parts);
  assert.equal(report.pass, true, report.text);
  assert.ok(!report.advisories.some((a) => /window\.front\.top/.test(a.measured)), "no window role, no window advisory");
});

/** 30% off, in the direction that keeps the pane / box a valid solid. */
const OFF = {
  "headlight.diameter": { "headlight.diameter": 1.3 * V["headlight.diameter"] },
  "grille.w": { "grille.w": 1.3 * V["grille.w"] },
  "grille.h": { "grille.h": 1.3 * V["grille.h"] },
  "mirror.head.w": { "mirror.head.w": 1.3 * V["mirror.head.w"] },
  "mirror.head.h": { "mirror.head.h": 1.3 * V["mirror.head.h"] },
  "mirror.offsetX": { "mirror.offsetX": 1.3 * V["mirror.offsetX"] },
  "window.front.w": { "window.front.w": 1.3 * V["window.front.w"] },
  "window.front.bottom": { "window.front.bottom": 1.3 * V["window.front.bottom"] },
  "window.side.start": { "window.side.start": 1.3 * V["window.side.start"] },
  "window.side.end": { "window.side.end": 1.3 * V["window.side.end"] },
  "window.side.bottom": { "window.side.bottom": 1.3 * V["window.side.bottom"] },
  // x 1.3 would lift the pane over the roof and raise H with it; 30% low needs a lower sill
  "window.side.top": { "window.side.top": 0.7 * V["window.side.top"], "window.side.bottom": 0.5 },
};

for (const [key, over] of Object.entries(OFF)) {
  test(`V12_LAYOUT fails ${key} built 30% off`, async () => {
    const report = await gate(appearance(over));
    assert.equal(report.pass, false, `${key}: expected a V12_LAYOUT miss`);
    assert.ok(layoutMiss(report, key), `${key}: ${report.text}`);
  });
}

test("mirror.arm.length: its tol floor (0.02 W) is 41% of 0.049 W, so 30% off stays inside tol; 60% off fails", async () => {
  // A layout.json property (tol = max(0.02, 0.15 x value)), not a rule gap — reported upward.
  const plus30 = await gate(appearance({ "mirror.arm.length": 1.3 * V["mirror.arm.length"] }));
  assert.ok(!layoutMiss(plus30, "mirror.arm.length"), plus30.text);
  const plus60 = await gate(appearance({ "mirror.arm.length": 1.6 * V["mirror.arm.length"] }));
  assert.ok(layoutMiss(plus60, "mirror.arm.length"), plus60.text);
});

test("agy first-seat P1 (an author with no appearance numbers) misses several appearance keys", async (t) => {
  const src = fs.readFileSync(path.join(ROOT, "out/blind/pickup/agy/first-seat-P1.mjs"), "utf8")
    .replace("../../src/kernel/index.mjs", pathToFileURL(path.join(ROOT, "src/kernel/index.mjs")).href);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "llmm-appear-"));
  const file = path.join(dir, "first-seat-P1.mjs");
  fs.writeFileSync(file, src);
  let parts;
  try {
    parts = (await import(pathToFileURL(file).href)).build();
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  const off = [];
  for (const k of KEYS) {
    const got = measureKey(parts, k);
    assert.ok(got && got.length > 0, `${k} measured on first-seat P1`);
    const ok = within(k, got);
    if (!ok) off.push(k);
    t.diagnostic(`${k}: ${got.map((x) => x.toFixed(3)).join(", ")} vs ${LAYOUT[k].value ?? LAYOUT[k].values.join(", ")} +/- ${tolOf(k)} ${ok ? "ok" : "OFF"}`);
  }
  assert.ok(off.length >= 3, `off: ${off.join(", ")}`);
});
