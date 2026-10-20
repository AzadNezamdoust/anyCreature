// WF v8 (Generals units, 2026-09-29) — non-wheeled vehicles through the per-subject rule overrides: the `wheels`
// override's `running: "tracks" | "skids"` (runner assemblies on the ground, road wheels or none) and the `roles`
// override (turret / gun / rotor join the closed role table), with rotor / track palette zones through `paletteZones`.
// Hermetic like test/wf-v8-gate.test.js: fixtures built here from kernel primitives, frozen limits numbers.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, applyRuleOverrides, chainContext, overrideRoles, triBudgetOf, DEFAULT_LIMITS, RUNNING, RUNNER_ROLE, TRIS_OVERRIDE_CAP } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CLASS = JSON.parse(fs.readFileSync(path.join(ROOT, "classes/vehicle.json"), "utf8"));

await K.init();

const KEYS = ["body", "glass", "tyre", "hub", "bumper", "lamp"];
const CLS = Object.freeze({ ...CLASS, wheels: { count: 4, axles: 2 }, paletteZones: KEYS.map((key) => ({ key })), ruleOverrides: undefined });
const LIMITS = Object.freeze({ ...DEFAULT_LIMITS, v7: { ...DEFAULT_LIMITS.v7, wheel_diameter_frac_of_length: [0.1, 0.2], ground_clearance: [0.15, 0.5] } });
const META = { class: "vehicle", seed: 1, front: "+X", palette: { body: "#6b7040", tyre: "#303030" } };
const EV = "fixture measurement";
const seam = 0.001;
const withOverrides = (ruleOverrides) => ({ ...CLS, ruleOverrides });
const gate = (parts, cls = CLS) => validateParts(META, parts, LIMITS, { cls, rules: RULES });
const codes = (report) => report.violations.map((v) => v.v);
const overrideRows = (report) => report.advisories.filter((a) => a.v === "RULE_OVERRIDE");

/**
 * A box tank (nose +z): two track boxes (role track) standing on y = 0 along the flanks, a hull (role body) seated 1 mm
 * into their tops between them, `stations` road-wheel pairs (role wheel) seated 1 mm into the tracks' outer faces with
 * their bottoms `lift` above the ground, and a turret (role `turretRole`) + gun (role `gunRole`) on the hull.
 */
function tank({ L = 7, W = 3.4, th = 0.9, tw = 0.6, stations = 0, r = 0.3, t = 0.12, lift = 0.1, turretRole = "turret", gunRole = "gun", zone = "track" } = {}) {
  const parts = [];
  const add = (id, solid, z, role) => parts.push({ id, solid, zone: z, role });
  add("track_l", K.box([tw, th, L]).at([W / 2 - tw / 2, 0, 0]), zone, "track");
  add("track_r", K.box([tw, th, L]).at([-W / 2 + tw / 2, 0, 0]), zone, "track");
  add("hull", K.box([W - 2 * tw + 2 * seam, 0.9, L * 0.95]).at([0, th - 0.3, 0]), "body", "body");
  const disc = K.revolve(K.profile.poly([[0, 0], [r, 0], [r, t], [0, t]]), 16).rotZ(90);   // x -t..0
  for (let k = 0; k < stations; k += 1) {
    const z = -L / 2 + 0.8 + k * ((L - 1.6) / Math.max(1, stations - 1));
    add(`roadwheel_${k}l`, disc.at([W / 2 + t - seam, lift + r, z]), "tyre", "wheel");
    add(`roadwheel_${k}r`, disc.at([-W / 2 + seam, lift + r, z]), "tyre", "wheel");
  }
  add("turret", K.box([2.0, 0.7, 2.4]).at([0, th + 0.6 - seam, -0.3]), "body", turretRole);
  add("gun", K.box([0.2, 0.2, 3.0]).at([0, th + 0.85, 2.4 - seam]), "body", gunRole);
  return parts;
}

/** A box helicopter on two skids (role skid) with a fuselage on two struts, a main rotor on a mast. */
function heli({ L = 9, W = 2.4, skidW = 0.12, zone = "rotor", wheel = false } = {}) {
  const parts = [];
  const add = (id, solid, z, role) => parts.push({ id, solid, zone: z, role });
  add("skid_l", K.box([skidW, 0.1, 3.4]).at([W / 2 - skidW / 2, 0, 0]), "body", "skid");
  add("skid_r", K.box([skidW, 0.1, 3.4]).at([-W / 2 + skidW / 2, 0, 0]), "body", "skid");
  add("strut_l", K.box([skidW, 0.5 + 2 * seam, 0.12]).at([W / 2 - skidW / 2, 0.1 - seam, 0]), "body", "skid");
  add("strut_r", K.box([skidW, 0.5 + 2 * seam, 0.12]).at([-W / 2 + skidW / 2, 0.1 - seam, 0]), "body", "skid");
  add("fuselage", K.box([W, 1.6, L * 0.6]).at([0, 0.6 - seam, 0]), "body", "body");
  add("mast", K.box([0.2, 0.4 + 2 * seam, 0.2]).at([0, 2.2 - 2 * seam, 0]), "body", "rotor");
  add("rotor", K.box([0.3, 0.06, L]).at([0, 2.6 - 2 * seam, 0]), zone, "rotor");
  if (wheel) add("wheel_0", K.revolve(K.profile.poly([[0, 0], [0.2, 0], [0.2, 0.1], [0, 0.1]]), 16).rotZ(90).at([0.3, 0.2, 2.4]), "tyre", "wheel");
  return parts;
}

const TANK_ROLES = { roles: { value: { extra: ["turret", "gun"] }, evidence: EV }, paletteZones: { value: { extra: ["track"] }, evidence: EV } };
const HELI_ROLES = { roles: { value: { extra: ["rotor"] }, evidence: EV }, paletteZones: { value: { extra: ["rotor"] }, evidence: EV } };

test("running: tracks / skids / wheels; the runner role; malformed values throw; a road override keeps its WP2 shape", () => {
  assert.deepEqual(RUNNING, ["wheels", "tracks", "skids"]);
  assert.deepEqual(RUNNER_ROLE, { tracks: "track", skids: "skid" });
  const w = (value) => applyRuleOverrides(LIMITS, { wheels: { value, evidence: EV } }).values.wheels;
  assert.deepEqual(w({ count: 6, axles: 3, diameters: "equal" }), { count: 6, axles: 3, diameters: "equal" });
  assert.deepEqual(w({ count: 0, axles: 0, running: "tracks" }), { count: 0, axles: 0, diameters: "equal", running: "tracks", runners: 2 });
  assert.deepEqual(w({ count: 10, axles: 5, diameters: "equal", running: "tracks" }), { count: 10, axles: 5, diameters: "equal", running: "tracks", runners: 2 });
  assert.deepEqual(w({ count: 0, axles: 0, running: "skids", runners: 2 }), { count: 0, axles: 0, diameters: "equal", running: "skids", runners: 2 });
  const bad = (value) => () => w(value);
  assert.throws(bad({ count: 0, axles: 0, running: "hover" }), /running "hover" must be one of wheels, tracks, skids/);
  assert.throws(bad({ count: 0, axles: 0, diameters: "equal" }), /count 0 must be an integer >= 1/);
  assert.throws(bad({ count: 4, axles: 2, running: "skids", diameters: "equal" }), /running skids stands on no wheels/);
  assert.throws(bad({ count: 10, axles: 0, running: "tracks", diameters: "equal" }), /axles 0 \(road-wheel stations\) must be an integer 1\.\.count/);
  assert.throws(bad({ count: 10, axles: 5, running: "tracks" }), /diameters undefined/);
  assert.throws(bad({ count: 4, axles: 2, diameters: "equal", runners: 2 }), /runners is for running tracks \| skids only/);
  assert.throws(bad({ count: 0, axles: 0, running: "tracks", runners: 0 }), /runners 0 must be an integer >= 1/);
  const r = applyRuleOverrides(LIMITS, { wheels: { value: { count: 0, axles: 0, running: "skids" }, evidence: EV }, roles: { value: { extra: ["rotor", "rotor", "boom"] }, evidence: EV } });
  assert.deepEqual(r.values.roles, { extra: ["rotor", "boom"] });
  assert.deepEqual(overrideRoles(r.values), ["rotor", "boom", "skid"]);
  assert.match(r.rows[0].limit, /running skids: 2 "skid" assemblies on the ground, no wheels; chassis clearance band off/);
  assert.match(r.rows[1].limit, /V7_ROLE also accepts rotor, boom$/);
  assert.equal(r.limits, LIMITS);
  assert.throws(() => applyRuleOverrides(LIMITS, { roles: { value: { extra: ["Turret"] }, evidence: EV } }), /not a lower-case identifier/);
  assert.throws(() => applyRuleOverrides(LIMITS, { roles: { value: { extra: [] }, evidence: EV } }), /non-empty list/);
  assert.throws(() => applyRuleOverrides(LIMITS, { roles: { value: { extra: ["gun"] } } }), /needs \{value, evidence\}/);
});

test("tracks: a tank fails the wheeled class (roles, ground, wheels) and passes under running tracks + roles + track zone", async () => {
  const parts = tank();
  const plain = await gate(parts);
  assert.equal(plain.pass, false);
  assert.ok(codes(plain).includes("V7_ROLE"), plain.text);

  const zonesOnly = await gate(parts, withOverrides({ ...TANK_ROLES }));
  assert.equal(zonesOnly.pass, false);   // "track" is still no role, the tracks still no wheels
  assert.ok(codes(zonesOnly).includes("V7_ROLE"), zonesOnly.text);

  const ok = await gate(parts, withOverrides({ ...TANK_ROLES, wheels: { value: { count: 0, axles: 0, running: "tracks" }, evidence: EV } }));
  assert.equal(ok.pass, true, ok.text);
  assert.deepEqual(overrideRows(ok).map((r) => r.part), ["roles", "paletteZones", "wheels"]);
});

test("tracks with road wheels: count / stations measured, no diameter band unless diameterFrac; runners counted", async () => {
  const over = (value) => withOverrides({ ...TANK_ROLES, wheels: { value: { running: "tracks", diameters: "equal", ...value }, evidence: EV } });
  const parts = tank({ stations: 5 });   // d 0.6 over L 7 = 0.086: under the road band 0.1..0.2, off for road wheels
  const ok = await gate(parts, over({ count: 10, axles: 5 }));
  assert.equal(ok.pass, true, ok.text);
  const wrongCount = await gate(parts, over({ count: 12, axles: 6 }));
  assert.deepEqual(codes(wrongCount), ["VEH_WHEELS"], wrongCount.text);
  assert.equal(wrongCount.violations[0].measured, "10 wheel assemblies");
  const wrongStations = await gate(parts, over({ count: 10, axles: 4 }));
  assert.deepEqual(codes(wrongStations), ["VEH_WHEELS"], wrongStations.text);
  assert.equal(wrongStations.violations[0].measured, "5 axle position(s) along z");
  const band = await gate(parts, over({ count: 10, axles: 5, diameterFrac: [0.1, 0.2] }));
  assert.deepEqual(codes(band), ["VEH_WHEELS"], band.text);
  assert.match(band.violations[0].measured, /^diameter\/length 0\.08/);
  // hidden road wheels (count 0) but the model builds them: fails
  const hidden = await gate(parts, over({ count: 0, axles: 0 }));
  assert.deepEqual(codes(hidden), ["VEH_WHEELS"], hidden.text);
  assert.equal(hidden.violations[0].measured, "10 wheel assemblies");
  // one track only (the whole chain stops at V4 first: the tank tips; the class row alone names the missing track)
  const row = RULES.validators.find(([n]) => n === "VEH_WHEELS")[1];
  const one = row(chainContext(META, tank().filter((p) => p.id !== "track_r"), LIMITS, { cls: over({ count: 0, axles: 0 }), rules: RULES })).violations;
  assert.deepEqual(one.map((v) => [v.v, v.measured, v.limit]), [["VEH_WHEELS", "1 track assemblies", "2"]]);
});

test("tracks: VEH_GROUND wants the tracks on y = 0 and nothing else but tracks / road wheels there", () => {
  const row = RULES.validators.find(([n]) => n === "VEH_GROUND")[1];
  const cls = withOverrides({ ...TANK_ROLES, wheels: { value: { count: 0, axles: 0, running: "tracks" }, evidence: EV } });
  const ctxOf = (parts) => chainContext(META, parts, LIMITS, { cls, rules: RULES });
  assert.deepEqual(row(ctxOf(tank())).violations, []);
  const floating = tank().map((p) => (p.id === "track_l" ? { ...p, solid: K.box([0.6, 0.9, 7]).at([1.4, 0.05, 0]) } : p));
  const v = row(ctxOf(floating)).violations;
  assert.equal(v.length, 1);
  assert.match(v[0].hint, /^track "track_l" floats 0\.050 m/);
  const grounded = [...tank(), { id: "crate", solid: K.box([0.4, 0.4, 0.4]).at([0, 0, 4]), zone: "body", role: "prop" }];
  assert.match(row(ctxOf(grounded)).violations[0].hint, /only the tracks do/);
});

test("skids: a skid helicopter passes under running skids + rotor role / zone; a wheel part or a missing skid fails", async () => {
  const cls = (extra = {}) => withOverrides({ ...HELI_ROLES, wheels: { value: { count: 0, axles: 0, running: "skids" }, evidence: EV }, ...extra });
  const plain = await gate(heli());
  assert.equal(plain.pass, false);
  assert.ok(codes(plain).includes("V7_ROLE"), plain.text);
  const ok = await gate(heli(), cls());
  assert.equal(ok.pass, true, ok.text);
  const noZone = await gate(heli(), withOverrides({ roles: HELI_ROLES.roles, wheels: { value: { count: 0, axles: 0, running: "skids" }, evidence: EV } }));
  assert.deepEqual(codes(noZone), ["PALETTE_ZONE"], noZone.text);
  const row = RULES.validators.find(([n]) => n === "VEH_WHEELS")[1];
  const withWheel = row(chainContext(META, heli({ wheel: true }), LIMITS, { cls: cls(), rules: RULES })).violations;
  assert.deepEqual(withWheel.map((v) => [v.v, v.measured, v.limit]), [["VEH_WHEELS", "1 wheel assemblies", "0"]]);
  const oneSkid = row(chainContext(META, heli().filter((p) => !p.id.endsWith("_r")), LIMITS, { cls: cls(), rules: RULES })).violations;
  assert.deepEqual(oneSkid.map((v) => [v.measured, v.limit]), [["1 skid assemblies", "2"]]);
});

test("a road vehicle's rows are unchanged by the new keys: no running = wheels, the band and clearance on", () => {
  const ctx = chainContext(META, tank(), LIMITS, { cls: CLS, rules: RULES });
  assert.equal(RULES.runningOf(ctx), "wheels");
  assert.deepEqual(RULES.runnerGroups(ctx), []);
  assert.deepEqual(overrideRoles(ctx.overrides), []);
});

test("tris: the subject's triangle budget (1..12000) replaces the class's and meta.triBudget; a RULE_OVERRIDE row; bad values throw", async () => {
  assert.equal(TRIS_OVERRIDE_CAP, 12000);
  const TRACKS = { ...TANK_ROLES, wheels: { value: { count: 0, axles: 0, running: "tracks" }, evidence: EV } };
  const tight = { ...withOverrides(TRACKS), triBudget: 20 };
  const over = await gate(tank(), tight);
  assert.equal(over.pass, false);
  assert.ok(codes(over).includes("V10"), over.text);
  assert.equal(over.measurements.triBudget, 20);

  const tris = { ...TRACKS, tris: { value: 8000, evidence: "owner 2026-09-29: detailed like the combat bike" } };
  const ok = await gate(tank(), { ...withOverrides(tris), triBudget: 20 });
  assert.equal(ok.pass, true, ok.text);
  assert.equal(ok.measurements.triBudget, 8000);
  const row = overrideRows(ok).find((r) => r.part === "tris");
  assert.match(row.limit, /V10 triangle budget -> 8000 .*cap 12000/);
  assert.match(row.hint, /detailed like the combat bike/);
  // the module's meta.triBudget does not undercut the subject's override
  const metaTight = await validateParts({ ...META, triBudget: 20 }, tank(), LIMITS, { cls: withOverrides(tris), rules: RULES });
  assert.equal(metaTight.measurements.triBudget, 8000);
  assert.equal(metaTight.pass, true, metaTight.text);

  assert.equal(triBudgetOf({ triBudget: 30 }, { triBudget: 4000 }, {}), 30);
  assert.equal(triBudgetOf({}, { triBudget: 4000 }, { tris: 9000 }), 9000);
  const t = (value) => () => applyRuleOverrides(LIMITS, { tris: { value, evidence: EV } });
  assert.equal(t(12000)().values.tris, 12000);
  assert.equal(t(12000)().limits, LIMITS);   // limits.json numbers untouched
  for (const v of [12001, 0, 7999.5, "8000", null]) assert.throws(t(v), /ruleOverrides\.tris|needs \{value, evidence\}/);
  assert.throws(() => applyRuleOverrides(LIMITS, { tris: { value: 8000 } }), /needs \{value, evidence\}/);
});
