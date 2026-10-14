// WORKFLOW-V3 §7.5 Job D1 — the class prior is DATA, the subject paths come from
// the manifest, and no generic file keeps a subject literal.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { instanceCount, familyShares, resolveTargetQuad } from "../scripts/likeness.mjs";
import { generateForSubject } from "../scripts/template-building.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BUILDING = JSON.parse(fs.readFileSync(path.join(ROOT, "classes/building.json"), "utf8"));

test("classes/building.json has every lifted table and no TODO-LIFT left", () => {
  assert.ok(!JSON.stringify(BUILDING).includes("TODO-LIFT"));
  for (const key of ["roles", "bearingRoles", "triBudget", "censusRules", "roleIdColours", "likeness", "paletteZones", "rules"]) {
    assert.ok(BUILDING[key] !== undefined, `building.json lacks ${key}`);
  }
});

test("the class tables are closed over the class's own roles", () => {
  const roles = new Set(BUILDING.roles);
  assert.deepEqual(Object.keys(BUILDING.roleIdColours).sort(), [...roles].sort(), "one id colour per role, no more");
  assert.equal(new Set(Object.values(BUILDING.roleIdColours)).size, roles.size, "id colours must be distinct");
  for (const role of BUILDING.bearingRoles) assert.ok(roles.has(role), `bearing role ${role}`);
  for (const rule of Object.values(BUILDING.censusRules)) assert.ok(roles.has(rule.role), `census role ${rule.role}`);
  const lk = BUILDING.likeness;
  for (const role of [...lk.censusRoles, ...lk.ironRoles, ...lk.overlapRoles, ...lk.thinRoles]) assert.ok(roles.has(role), `likeness role ${role}`);
  for (const role of Object.keys(lk.censusInstances)) assert.ok(lk.censusRoles.includes(role), `instances for ${role}`);
  for (const z of BUILDING.paletteZones) assert.ok(z.key && z.region && Array.isArray(z.point), JSON.stringify(z));
});

test("palette closure: every regions zone named by a module palette key or a likeness family has a paletteZones entry", () => {
  // Module palette keys from the deterministic template (P0 + P1), never the live facade module a pass rewrites.
  const keysOf = (text) => [...text.match(/palette: \{([\s\S]*?)\}/)[1].matchAll(/^\s*(\w+):/gm)].map((m) => m[1]);
  const moduleKeys = new Set([...keysOf(generateForSubject("facade_brick", { through: "P0" }).text), ...keysOf(generateForSubject("facade_brick").text)]);
  const regions = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/facade_brick/regions.json"), "utf8"));
  const families = new Set(Object.values(BUILDING.likeness.areaFamilies).flat());
  const mapped = new Set(BUILDING.paletteZones.map((z) => z.region));
  const due = Object.keys(regions.zones).filter((zone) => moduleKeys.has(zone) || families.has(zone));
  assert.ok(due.length >= 10, due.join(", "));
  for (const zone of due) assert.ok(mapped.has(zone), `regions zone ${zone} has no paletteZones entry in classes/building.json`);
});

test("census instances are data: a key, or the SUM of keys", () => {
  const census = { windows: 12, vent: 1, pipes: 2 };
  assert.equal(instanceCount(BUILDING.likeness, "window", census), 12);
  assert.equal(instanceCount(BUILDING.likeness, "roof_fixture", census), 3);
  assert.equal(instanceCount(BUILDING.likeness, "door", census), undefined);
  assert.equal(instanceCount(BUILDING.likeness, "massing", census), undefined);
});

test("family shares are taken over the families the prior names", () => {
  const { share, total } = familyShares({ brick_front: 30, glass: 10, roof: 999 }, { brick: ["brick_front"], glass: ["glass"] });
  assert.equal(total, 40);
  assert.equal(share.brick, 0.75);
});

test("the target quad's provenance names the subject's own measured-layout path", () => {
  const quad = resolveTargetQuad({ _frame: { quadPx: [[0, 0], [1, 0], [1, 1], [0, 1]] } }, null, "subjects/x/layout.measured.json");
  assert.equal(quad.provenance, "subjects/x/layout.measured.json (measured face quad)");
});

/** Source with comments removed: block comments, then `//` comments at line start or after whitespace. */
function code(file) {
  return fs.readFileSync(path.join(ROOT, file), "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .split("\n").map((line) => line.replace(/(^|\s)\/\/.*$/, "$1")).join("\n");
}

test("no subject literal and no absolute repo path survives in the Job D1 files", () => {
  const files = ["classes/building.json", "src/validate/kernel-chain.mjs", "src/validate/rules/building.mjs",
    "scripts/likeness.mjs", "scripts/calibrate-palette.mjs", "scripts/compare-still.mjs", "scripts/capture2.mjs",
    "scripts/measure-target.mjs", "src/app.js"];
  for (const file of files) {
    const lines = code(file).split("\n");
    for (const line of lines) {
      if (/^const DEFAULT_SUBJECT = "facade_brick";$/.test(line.trim()) && file === "src/app.js") continue;   // owner default
      assert.ok(!/facade_brick|tenement-iso/.test(line), `${file}: subject literal in code: ${line.trim()}`);
      assert.ok(!/[A-Z]:\/Git\//.test(line), `${file}: absolute repo path in code: ${line.trim()}`);
    }
  }
});

test("kernel-chain.mjs carries no building role word outside comments and its fallback imports", () => {
  const words = /\b(massing|roof|parapet|cornice|sill|window|storefront|door|awning|signbox|landing|stringer|railing|baluster|ladder|rung|brick|facade)\b/;
  for (const line of code("src/validate/kernel-chain.mjs").split("\n")) {
    if (/^import .*building/.test(line.trim())) continue;
    assert.ok(!words.test(line), `building word in kernel-chain code: ${line.trim()}`);
  }
});
