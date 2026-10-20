// WF v8 WP2 (research/v7/WF-V8-PLAN.md "Gate", WF-REVIEW-opus.md C10) — the per-subject `wheels` and `paletteZones`
// rule overrides (owner 2026-09-26: TARGET WINS through measured, recorded overrides; limits.json never changes).
// Hermetic: FROZEN fixtures built here from kernel primitives, a frozen palette list and frozen limits numbers; no subject
// module and no subject file is read.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, applyRuleOverrides, gateConfig, chainContext, DEFAULT_LIMITS, RULE_OVERRIDES } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LIMITS_FILE = path.join(ROOT, "src/validate/limits.json");
const LIMITS_TEXT = fs.readFileSync(LIMITS_FILE, "utf8");
const CLASS = JSON.parse(fs.readFileSync(path.join(ROOT, "classes/vehicle.json"), "utf8"));

await K.init();

// Frozen gate inputs: the class prior with a frozen closed palette and the class wheel prior, and the limits numbers the
// fixtures are sized against (the class band 0.1..0.2, wheel diameter over the longer horizontal bound).
const KEYS = ["body", "glass", "tyre", "hub", "bumper", "lamp"];
const CLS = Object.freeze({ ...CLASS, wheels: { count: 4, axles: 2 }, paletteZones: KEYS.map((key) => ({ key })), ruleOverrides: undefined });
const LIMITS = Object.freeze({ ...DEFAULT_LIMITS, v7: { ...DEFAULT_LIMITS.v7, wheel_diameter_frac_of_length: [0.1, 0.2] } });
const META = { class: "vehicle", seed: 1, front: "+X", palette: { body: "#e0e0e0", tyre: "#303030" } };
const EV = "fixture measurement";

/**
 * A box vehicle (classes/vehicle.md frame: +Y up, nose +Z, x centred) on `axles` [{z, r, rRight?}]: two discs per axle,
 * outer faces flush with the flanks; a chassis between the wheels' inner faces seated 1 mm into them; a body box above
 * the tallest wheel seated 1 mm into the chassis.
 */
function vehicle(axles, { L = 6, W = 2.2, H = 2.6, t = 0.3, clearance = 0.3 } = {}) {
  const seam = 0.001;
  const parts = [];
  const add = (id, solid, zone, role) => parts.push({ id, solid, zone, role });
  const disc = (r) => K.revolve(K.profile.poly([[0, 0], [r, 0], [r, t], [0, t]]), 16).rotZ(90);   // x -t..0
  const deckY = 2 * Math.max(...axles.flatMap((a) => [a.r, a.rRight ?? a.r])) + 0.02;
  add("chassis", K.box([W - 2 * t + 2 * seam, deckY - clearance, L]).at([0, clearance, 0]), "tyre", "chassis");
  axles.forEach(({ z, r, rRight = r }, k) => {
    add(`wheel_${k}l`, disc(r).at([W / 2, r, z]), "tyre", "wheel");
    add(`wheel_${k}r`, disc(rRight).at([-W / 2 + t, rRight, z]), "tyre", "wheel");
  });
  add("body", K.box([W, H - deckY + seam, L]).at([0, deckY - seam, 0]), "body", "body");
  return parts;
}

const TANDEM = [{ z: 2.0, r: 0.42 }, { z: -1.2, r: 0.42 }, { z: -2.2, r: 0.42 }];          // 6 wheels, 3 axles, d/L 0.14
const FOUR = [{ z: 2.0, r: 0.42 }, { z: -2.0, r: 0.42 }];
const TRACTOR = [{ z: 1.2, r: 0.45 }, { z: -0.8, r: 0.75 }];                                // d 0.9 / 1.5 over L 3.4
const TRACTOR_SIZE = { L: 3.4, W: 2.0, H: 2.4 };

const withOverrides = (ruleOverrides) => ({ ...CLS, ruleOverrides });
const gate = (parts, cls = CLS) => validateParts(META, parts, LIMITS, { cls, rules: RULES });
const codes = (report) => report.violations.map((v) => v.v);
const overrideRows = (report) => report.advisories.filter((a) => a.v === "RULE_OVERRIDE");

test("WP2: wheels / paletteZones are known override names; each needs {value, evidence}; malformed values throw", () => {
  assert.deepEqual(RULE_OVERRIDES, ["step_rise_max", "stairRails", "flightTreads", "wheels", "paletteZones", "roles", "tris", "mirror"]);
  assert.throws(() => applyRuleOverrides(LIMITS, { wheel_count: { value: 6, evidence: EV } }), /unknown override "wheel_count"/);
  assert.throws(() => applyRuleOverrides(LIMITS, { wheels: { value: { count: 6, axles: 3, diameters: "equal" } } }), /needs \{value, evidence\}/);
  assert.throws(() => applyRuleOverrides(LIMITS, { paletteZones: { value: { extra: ["tail"] }, evidence: "" } }), /needs \{value, evidence\}/);
  assert.throws(() => applyRuleOverrides(LIMITS, { paletteZones: { evidence: EV } }), /needs \{value, evidence\}/);
  const wheels = (value) => () => applyRuleOverrides(LIMITS, { wheels: { value, evidence: EV } });
  assert.throws(wheels(6), /wheels value must be an object/);
  assert.throws(wheels({ count: 6.5, axles: 3, diameters: "equal" }), /count 6\.5 must be an integer >= 1/);
  assert.throws(wheels({ count: 4, axles: 5, diameters: "equal" }), /axles 5 must be an integer 1\.\.count/);
  assert.throws(wheels({ count: 4, axles: 2 }), /diameters undefined must be "equal" or "per-axle"/);
  assert.throws(wheels({ count: 4, axles: 2, diameters: "front-big" }), /diameters "front-big" must be/);
  assert.throws(wheels({ count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.5, 0.2] }), /diameterFrac \[0\.5,0\.2\] must be/);
  assert.throws(wheels({ count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.2] }), /diameterFrac \[0\.2\] must be/);
  assert.throws(wheels({ count: 4, axles: 2, diameters: "per-axle", diameterfrac: [0.2, 0.5] }), /unknown key\(s\) diameterfrac/);
  const zones = (value) => () => applyRuleOverrides(LIMITS, { paletteZones: { value, evidence: EV } });
  assert.throws(zones(["tail"]), /paletteZones value must be an object/);
  assert.throws(zones({ extra: [] }), /extra must be a non-empty list/);
  assert.throws(zones({ extra: ["tail", 3] }), /holds a non-string or empty zone name/);
  assert.throws(zones({ extras: ["tail"] }), /unknown key\(s\) extras/);
});

test("WP2: the overrides are advisory RULE_OVERRIDE rows (value, limit, evidence); only diameterFrac touches a limit; limits.json unchanged", () => {
  const o = {
    _comment: "skipped",
    wheels: { value: { count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.25, 0.47] }, evidence: "tyres 0.81 / 1.37 m" },
    paletteZones: { value: { extra: ["tail", "trim", "tail"] }, evidence: "tail #e13738" },
  };
  const { limits, rows, waived, values } = applyRuleOverrides(LIMITS, o);
  assert.deepEqual(waived, []);
  assert.deepEqual(values.wheels, { count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.25, 0.47] });
  assert.deepEqual(values.paletteZones, { extra: ["tail", "trim"] });
  assert.deepEqual(limits.v7.wheel_diameter_frac_of_length, [0.25, 0.47]);
  assert.deepEqual(LIMITS.v7.wheel_diameter_frac_of_length, [0.1, 0.2]);
  assert.deepEqual(DEFAULT_LIMITS.v7.wheel_diameter_frac_of_length, [0.1, 0.2]);
  assert.equal(fs.readFileSync(LIMITS_FILE, "utf8"), LIMITS_TEXT);
  assert.deepEqual(rows.map((r) => `${r.v} ${r.part} ${r.blocking}`), ["RULE_OVERRIDE wheels false", "RULE_OVERRIDE paletteZones false"]);
  assert.equal(rows[0].measured, JSON.stringify(o.wheels.value));
  assert.match(rows[0].limit, /4 wheels on 2 axles, equal diameters within each axle; limits\.v7\.wheel_diameter_frac_of_length 0\.1\.\.0\.2 -> 0\.25\.\.0\.47/);
  assert.match(rows[0].hint, /TARGET WINS.*tyres 0\.81 \/ 1\.37 m/);
  assert.match(rows[1].limit, /PALETTE_ZONE also accepts tail, trim$/);
  assert.match(rows[1].hint, /tail #e13738/);
  // paletteZones and a band-less wheels override are class config: the gate digest stays the class digest
  const digest = gateConfig(CLS, LIMITS).digest;
  assert.equal(gateConfig(withOverrides({ paletteZones: o.paletteZones }), LIMITS).digest, digest);
  assert.equal(gateConfig(withOverrides({ wheels: { value: { count: 6, axles: 3, diameters: "equal" }, evidence: EV } }), LIMITS).digest, digest);
  assert.notEqual(gateConfig(withOverrides({ wheels: o.wheels }), LIMITS).digest, digest);
  // no override: no rows, no values, the very same limits object
  const none = applyRuleOverrides(LIMITS, undefined);
  assert.equal(none.limits, LIMITS);
  assert.deepEqual([none.rows, none.waived, none.values], [[], [], {}]);
});

test("WP2 paletteZones: undeclared zones fail PALETTE_ZONE; the override passes the declared ones; an undeclared zone still fails", async () => {
  const parts = vehicle(FOUR).map((p) => (p.id === "wheel_1l" || p.id === "wheel_1r" ? { ...p, zone: "tail" } : p.id === "body" ? { ...p, zone: "trim" } : p));
  const plain = await gate(parts);
  assert.equal(plain.pass, false);
  assert.deepEqual(codes(plain), ["PALETTE_ZONE", "PALETTE_ZONE"], plain.text);
  assert.deepEqual(plain.violations.map((v) => v.measured), ['zone "tail" on 2 part(s)', 'zone "trim" on 1 part(s)']);
  assert.deepEqual(overrideRows(plain), []);

  const both = await gate(parts, withOverrides({ paletteZones: { value: { extra: ["tail", "trim"] }, evidence: EV } }));
  assert.equal(both.pass, true, both.text);
  assert.deepEqual(overrideRows(both).map((r) => r.part), ["paletteZones"]);

  const one = await gate(parts, withOverrides({ paletteZones: { value: { extra: ["tail"] }, evidence: EV } }));
  assert.equal(one.pass, false);
  assert.deepEqual(codes(one), ["PALETTE_ZONE"], one.text);
  assert.equal(one.violations[0].measured, 'zone "trim" on 1 part(s)');
  assert.equal(one.violations[0].limit, `one of: ${[...KEYS, "tail"].join(", ")}`);
  assert.equal(overrideRows(one).length, 1);

  // the caller's options.ruleOverrides path applies the same override
  const viaOptions = await validateParts(META, parts, LIMITS, { cls: CLS, rules: RULES, ruleOverrides: { paletteZones: { value: { extra: ["trim", "tail"] }, evidence: EV } } });
  assert.equal(viaOptions.pass, true, viaOptions.text);
});

test("WP2 wheels: a tandem (6 wheels / 3 axles) fails the class prior and passes under {count 6, axles 3}; a wrong count or axle number still fails", async () => {
  const tandem = vehicle(TANDEM);
  const plain = await gate(tandem);
  assert.deepEqual(codes(plain), ["VEH_WHEELS"], plain.text);
  assert.equal(plain.violations[0].measured, "6 wheel assemblies");
  assert.equal(plain.violations[0].limit, "4");

  const wheels = (value) => withOverrides({ wheels: { value, evidence: EV } });
  const ok = await gate(tandem, wheels({ count: 6, axles: 3, diameters: "equal" }));
  assert.equal(ok.pass, true, ok.text);
  assert.deepEqual(overrideRows(ok).map((r) => r.limit), ["VEH_WHEELS 6 wheels on 3 axles, one diameter"]);

  const wrongCount = await gate(tandem, wheels({ count: 4, axles: 2, diameters: "equal" }));
  assert.deepEqual(codes(wrongCount), ["VEH_WHEELS"], wrongCount.text);
  assert.equal(wrongCount.violations[0].measured, "6 wheel assemblies");
  const wrongAxles = await gate(tandem, wheels({ count: 6, axles: 2, diameters: "equal" }));
  assert.deepEqual(codes(wrongAxles), ["VEH_WHEELS"], wrongAxles.text);
  assert.equal(wrongAxles.violations[0].measured, "3 axle position(s) along z");
  // the tandem override on a four-wheel model fails the count the other way
  const four = await gate(vehicle(FOUR), wheels({ count: 6, axles: 3, diameters: "equal" }));
  assert.deepEqual(codes(four), ["VEH_WHEELS"], four.text);
  assert.deepEqual([four.violations[0].measured, four.violations[0].limit], ["4 wheel assemblies", "6"]);
  // without the override the four-wheel model is the class vehicle
  assert.equal((await gate(vehicle(FOUR))).pass, true);
});

test("WP2 wheels per-axle: small front / big rear wheels pass only with per-axle diameters AND the measured band", async () => {
  const tractor = vehicle(TRACTOR, TRACTOR_SIZE);
  const wheels = (value) => withOverrides({ wheels: { value, evidence: EV } });

  const plain = await gate(tractor);
  assert.deepEqual(plain.violations.map((v) => `${v.v} ${v.measured}`), ["VEH_WHEELS diameters 0.900..1.500 m", "VEH_WHEELS diameter/length 0.353"], plain.text);
  const equal = await gate(tractor, wheels({ count: 4, axles: 2, diameters: "equal", diameterFrac: [0.25, 0.47] }));
  assert.deepEqual(equal.violations.map((v) => `${v.v} ${v.measured}`), ["VEH_WHEELS diameters 0.900..1.500 m"], equal.text);
  // per-axle under the class band: each axle is measured on its own, both outside 0.1..0.2
  const noBand = await gate(tractor, wheels({ count: 4, axles: 2, diameters: "per-axle" }));
  assert.deepEqual(noBand.violations.map((v) => v.measured), ["diameter/length 0.441 on the axle at z -0.800", "diameter/length 0.265 on the axle at z 1.200"], noBand.text);
  const ok = await gate(tractor, wheels({ count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.25, 0.47] }));
  assert.equal(ok.pass, true, ok.text);
  assert.match(overrideRows(ok)[0].limit, /equal diameters within each axle; limits\.v7\.wheel_diameter_frac_of_length 0\.1\.\.0\.2 -> 0\.25\.\.0\.47 \(per axle\)/);
  // a band that misses one axle still fails that axle
  const tight = await gate(tractor, wheels({ count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.25, 0.4] }));
  assert.deepEqual(tight.violations.map((v) => v.measured), ["diameter/length 0.441 on the axle at z -0.800"], tight.text);
  // per-axle still wants equal wheels on ONE axle
  const odd = vehicle([{ z: 1.2, r: 0.45, rRight: 0.5 }, { z: -0.8, r: 0.75 }], TRACTOR_SIZE);
  const bad = await gate(odd, wheels({ count: 4, axles: 2, diameters: "per-axle", diameterFrac: [0.25, 0.47] }));
  assert.deepEqual(bad.violations.map((v) => `${v.v} ${v.part} ${v.measured}`), ["VEH_WHEELS wheel_0r diameters 0.900..1.000 m on the axle at z 1.200"], bad.text);
  // and the axle count: three axles (0.9 / 1.0 / 0.9 m) against a two-axle override
  const three = await gate(vehicle([{ z: 1.2, r: 0.45 }, { z: -0.6, r: 0.5 }, { z: -1.8, r: 0.45 }], { ...TRACTOR_SIZE, L: 4.6 }),
    wheels({ count: 6, axles: 2, diameters: "per-axle", diameterFrac: [0.05, 0.47] }));
  assert.deepEqual(three.violations.map((v) => v.measured), ["3 axle position(s) along z"], three.text);
});

test("WP2 axleClusters keeps which wheel sits on which axle (the kernel-chain clusters rule)", () => {
  assert.deepEqual(RULES.axleClusters([1.3, -0.89, 1.3, -0.89], 0.45), [{ z: -0.89, members: [1, 3] }, { z: 1.3, members: [0, 2] }]);
  assert.deepEqual(RULES.axleClusters([1.52, 1.52, -1.05, -1.05, -1.84, -1.84], 0.39).map((a) => a.members), [[4, 5], [2, 3], [0, 1]]);
  assert.deepEqual(RULES.axleClusters([0, 0.5, 1.0], 0.5).map((a) => a.members), [[0, 1, 2]]);   // single link, like clusters()
});

test("WP2: chainContext hands the override values to a single class row", () => {
  const o = { wheels: { value: { count: 6, axles: 3, diameters: "equal" }, evidence: EV } };
  const row = RULES.validators.find(([n]) => n === "VEH_WHEELS")[1];
  assert.equal(row(chainContext(META, vehicle(TANDEM), LIMITS, { cls: CLS, rules: RULES })).violations.length, 1);
  const ctx = chainContext(META, vehicle(TANDEM), LIMITS, { cls: withOverrides(o), rules: RULES });
  assert.deepEqual(ctx.overrides.wheels, o.wheels.value);
  assert.deepEqual(row(ctx).violations, []);
});
