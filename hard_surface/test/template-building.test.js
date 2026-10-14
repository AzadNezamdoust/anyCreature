// WORKFLOW-V3 §7 item 8 — the building template is deterministic, passes the
// gate at P1 with the frozen census + layout, and follows the layout it reads.
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, KERNEL_LIMIT_DEFAULTS } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/building.mjs";
import { generateForSubject, passKeys } from "../scripts/template-building.mjs";
import { loadSubject } from "../scripts/subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SUBJECT = "facade_brick";
// Two levels under ROOT, like subjects/<id>/, so the generated relative kernel import resolves.
const TMP = path.join(ROOT, "test", `.tmp-template-${process.pid}`);

let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return { file, mod: await import(pathToFileURL(file).href) };
}

function stagedCensus(raw, n) {
  return Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("_") && (raw._pass?.[k] ?? 0) <= n));
}

test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

test("generation is deterministic (in-process twice, and the CLI writes the same bytes)", () => {
  const a = generateForSubject(SUBJECT).text;
  const b = generateForSubject(SUBJECT).text;
  assert.equal(a, b);
  fs.mkdirSync(TMP, { recursive: true });
  const out = path.join(TMP, "cli.mjs");
  const r = spawnSync(process.execPath, [path.join(ROOT, "scripts", "template-building.mjs"), "--subject", SUBJECT, "--out", out], { cwd: ROOT, encoding: "utf8" });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(fs.readFileSync(out, "utf8"), a);
  assert.ok(!/Math\.random|\bDate\b/.test(a));
});

test("the CLI refuses to overwrite the live module and refuses the ironwork pass", () => {
  const S = loadSubject(SUBJECT);
  const live = spawnSync(process.execPath, [path.join(ROOT, "scripts", "template-building.mjs"), "--subject", SUBJECT, "--out", S.paths.module], { cwd: ROOT, encoding: "utf8" });
  assert.equal(live.status, 3);
  assert.throws(() => generateForSubject(SUBJECT, { through: "P2" }), /does not build: landing/);
});

test("P1 template passes check-module and validateParts with census staged to P1 and the layout", async () => {
  const S = loadSubject(SUBJECT);
  const gen = generateForSubject(SUBJECT);
  const { file, mod } = await importText(gen.text);
  const check = spawnSync(process.execPath, [path.join(ROOT, "scripts", "check-module.mjs"), file], { cwd: ROOT, encoding: "utf8" });
  assert.equal(check.status, 0, check.stdout);

  const layout = S.readJson("layout");
  await K.init();
  const parts = mod.build();
  const report = await validateParts(mod.meta, parts, undefined, { census: stagedCensus(S.readJson("census"), 1), layout, cls: S.cls, rules });
  assert.equal(report.pass, true, report.text);
  assert.equal(report.measurements.layout, "applied");
  assert.equal(report.measurements.census, "applied");

  // Every P0/P1 key is verified here and must have been MEASURED, not stood down.
  const passes = S.readJson("passes");
  const keys = [...new Set([...passKeys(passes[0].item), ...passKeys(passes[1].item)])];
  assert.ok(keys.length >= 14, `parsed ${keys.length} keys`);
  const roles = new Set(parts.map((p) => p.role));
  for (const k of keys) {
    assert.ok(layout[k] && !layout[k].unverified, `${k} is a verified key`);
    for (const role of rules.layoutRules[k].roles) assert.ok(roles.has(role), `${k}: role ${role} built, so V12_LAYOUT measured it`);
  }
  for (const role of roles) assert.ok(S.cls.roles.includes(role), `role ${role} from the class prior`);
  // Unverified keys the template consumed carry the greppable stub marker.
  for (const k of ["frame.widthRatio", "frame.proud", "cornice.projection"]) {
    assert.ok(gen.text.includes(`// MVP-STUB: unverified key ${k}`), k);
  }
});

test("the template declares its own seats: zero V6 rows, and every pair past inferredContactFrac is touches + embed", async () => {
  const S = loadSubject(SUBJECT);
  const { mod } = await importText(generateForSubject(SUBJECT).text);
  await K.init();
  const parts = mod.build();
  const report = await validateParts(mod.meta, parts, undefined, { census: stagedCensus(S.readJson("census"), 1), layout: S.readJson("layout"), cls: S.cls, rules });
  assert.deepEqual(report.violations.filter((v) => v.v.startsWith("V6")), [], report.text);
  const frac = KERNEL_LIMIT_DEFAULTS.inferredContactFrac;
  const overlaps = (a, b) => [0, 1, 2].every((i) => a.min[i] < b.max[i] && b.min[i] < a.max[i]);
  let seats = 0;
  for (let i = 0; i < parts.length; i += 1) {
    for (let j = i + 1; j < parts.length; j += 1) {
      const [a, b] = [parts[i], parts[j]];
      if (!overlaps(a.solid.aabb(), b.solid.aabb())) continue;
      const ratio = K.intersect(a.solid, b.solid).volume() / Math.min(a.solid.volume(), b.solid.volume());
      if (ratio <= frac) continue;
      seats += 1;
      const declared = (a.touches ?? []).includes(b.id) || (b.touches ?? []).includes(a.id);
      assert.ok(declared && (a.embed === true || b.embed === true),
        `${a.id} is seated ${(100 * ratio).toFixed(1)} % into ${b.id} without touches + embed`);
    }
  }
  assert.ok(seats >= 5, `expected the 4 sills and the awning to be seated, found ${seats}`);
});

test("changing one layout value changes the corresponding part dimension", async () => {
  const S = loadSubject(SUBJECT);
  const base = S.readJson("layout");
  const before = generateForSubject(SUBJECT);
  const after = generateForSubject(SUBJECT, { overrides: { layout: { "window.w": { ...base["window.w"], value: 0.12 } } } });
  assert.notEqual(before.text, after.text);
  assert.equal(after.W, before.W);
  await K.init();
  const width = async (text) => {
    const { mod } = await importText(text);
    const glass = mod.build().find((p) => p.id === "window_0_0_glass");
    const box = glass.solid.aabb();
    return box.max[0] - box.min[0];
  };
  const seam = 0.00075;
  assert.ok(Math.abs(await width(before.text) - (0.089 * before.W + 2 * seam)) < 1e-6);
  assert.ok(Math.abs(await width(after.text) - (0.12 * after.W + 2 * seam)) < 1e-6);
});
