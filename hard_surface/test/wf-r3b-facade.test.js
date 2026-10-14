// WF-R3-B item 8 (carried from R3-A H3) — the building template passes its OWN P1 likeness.
// storefront.h was a column median under the sloped awning (44 px, 0.08 H): the template's whole shop pane
// sat under the canopy and its lip hid the rest, so template P1 read LK_AREA glass 0.58x. The fix is measured,
// not banded: storefront.h is the pane's EXTENT at its tallest (un-clipped) columns, the canopy lip is lifted by
// its own projection (_frame.proudDrop) so it lands on awning.bottom, door/storefront glass is the measured glass
// height, and the glass sits nearly flush in its frame. Hermetic: every input is a frozen copy under
// test/fixtures/building/r3b-template-p1/ (plus the frozen TARGET refs/tenement-iso.png).
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts } from "../src/validate/kernel-chain.mjs";
import * as rules from "../src/validate/rules/building.mjs";
import { generateBuildingModule, CLASS_DEFAULTS } from "../scripts/template-building.mjs";
import { SCAN } from "../scripts/measure-target.mjs";
import { measureLikeness, resolveTargetQuad, dueVisibleParts, familyOwners, stageResult } from "../scripts/likeness.mjs";

const require = createRequire(import.meta.url);
const sharp = require("sharp");

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FIX = path.join(ROOT, "test", "fixtures", "building", "r3b-template-p1");
const json = (name) => JSON.parse(fs.readFileSync(path.join(FIX, name), "utf8"));
const cls = JSON.parse(fs.readFileSync(path.join(ROOT, "classes", "building.json"), "utf8"));
const layout = json("layout.json");
const census = json("census.json");
const passes = json("passes.json");
const meta = json("meta.json");
// Two levels under ROOT, like subjects/<id>/, so the generated relative kernel import resolves.
const TMP = path.join(ROOT, "test", `.tmp-r3b-facade-${process.pid}`);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));

const generate = () => generateBuildingModule({ subjectId: "facade_brick", cls, layout, census, passes, through: "P1" });
async function build(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${createHash("sha256").update(text).digest("hex").slice(0, 12)}.mjs`);
  fs.writeFileSync(file, text);
  await K.init();
  const mod = await import(pathToFileURL(file).href);
  return { mod, parts: mod.build() };
}
const staged = (raw, n) => Object.fromEntries(Object.entries(raw).filter(([k]) => !k.startsWith("_") && (raw._pass?.[k] ?? 0) <= n));

test("R3-B 8: storefront.h is the pane's extent at its tallest columns, not the median under the awning", () => {
  const e = layout["storefront.h"];
  assert.equal(e.value, 0.111);
  assert.equal(SCAN.paneTallCols, 3);
  assert.match(e.evidence.scan, /3 TALLEST columns/);
  assert.match(e.evidence.px, /^61\/550 px at x 578, 579, 580 \(61, 61, 60 px\); median over all 84 columns 44 px under the awning$/);
  // The un-clipped pane reaches past the canopy lip: the r3 median (0.08 H) stopped the pane under it.
  assert.ok(layout["storefront.bottom"].value + e.value > layout["awning.bottom"].value);
  assert.ok(layout["storefront.bottom"].value + 0.08 < layout["awning.bottom"].value);
  // The camera constant lives in _frame (no V12 rule measures a camera), with its own evidence.
  assert.equal(layout._frame.proudDrop, 0.355);
  assert.match(layout._frame.proudDropFit, /\(m \+ mZ\) x tan\(phi\) x Wpx \/ Hpx/);
  assert.ok(!Object.hasOwn(layout, "proud.drop"));
});

test("R3-B 8: the template's pane runs up to the canopy lip, and the lip PROJECTS onto awning.bottom", async () => {
  const gen = generate();
  const { parts } = await build(gen.text);
  const box = (id) => parts.find((p) => p.id === id).solid.aabb();
  const awning = box("shop_awning");
  const depth = CLASS_DEFAULTS.keys["awning.depth"];
  // Lip lifted by its own projection: seen at the solved camera it sits on the measured band.
  const projected = awning.min[1] / gen.H - layout._frame.proudDrop * depth / gen.W;
  assert.ok(Math.abs(projected - layout["awning.bottom"].value) < 1e-6, `lip projects to ${projected} H`);
  // The storefront frame's head meets the lip (no clash, no gap), the glass starts on storefront.bottom.
  const frame = box("storefront_0_frame");
  const glass = box("storefront_0_glass");
  assert.ok(Math.abs(frame.max[1] - awning.min[1]) < 1e-6, `frame head ${frame.max[1]} vs lip ${awning.min[1]}`);
  assert.ok(Math.abs(glass.min[1] + 0.00075 - layout["storefront.bottom"].value * gen.H) < 1e-6);
  // door.h is a GLASS measurement (like window.h): the door glass is door.h x H, the frame stands outside it.
  const door = box("door_0_glass");
  assert.ok(Math.abs(door.max[1] - door.min[1] - (layout["door.h"].value * gen.H + 2 * 0.00075)) < 1e-6);
  // The glass sits CLASS_DEFAULTS.glassReveal behind the frame's front face, not a frame depth behind it.
  const wframe = box("window_0_0_frame");
  const wglass = box("window_0_0_glass");
  assert.ok(Math.abs(wglass.min[2] - wframe.min[2] - CLASS_DEFAULTS.glassReveal) < 1e-6);
});

test("R3-B 8: the template P1 passes the gate (census staged to P1, frozen layout) — zero violations", async () => {
  const { mod, parts } = await build(generate().text);
  const report = await validateParts(mod.meta, parts, undefined, { census: staged(census, 1), layout, cls, rules });
  assert.equal(report.pass, true, report.text);
});

test("R3-B 8: the frozen capture is of THIS template (bytes bound by sha256)", () => {
  const text = generate().text;
  assert.equal(createHash("sha256").update(text).digest("hex"), meta.templateSha256,
    "template bytes changed: re-take the P1 gate-only capture into test/fixtures/building/r3b-template-p1/");
  const rendered = fs.readFileSync(path.join(FIX, "rendered-module.mjs.txt"), "utf8");
  assert.equal(createHash("sha256").update(rendered).digest("hex"), meta.renderedSha256);
  // gate-only recalibrates the palette in `meta` only: build() is the template's, byte for byte.
  const body = (t) => t.slice(t.indexOf("export function build()"));
  assert.equal(body(rendered), body(text));
});

test("R3-B 8: template P1 gate-only likeness is clean — every LK row, LK_AREA glass and grey inside the band", async () => {
  const read = async (file) => {
    const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
    return { data, w: info.width, h: info.height, c: info.channels };
  };
  const regions = json("regions.json");
  const manifest = json("target.png.json").manifest;
  const idManifest = json("idpass.png.json").manifest;
  const [target, still, idImage] = await Promise.all([
    read(path.join(ROOT, meta.target)), read(path.join(FIX, "target.png")), read(path.join(FIX, "idpass.png"))]);
  const renderQuad = manifest.frontQuad;
  const raw = measureLikeness({
    regions, target, still, idpass: { image: idImage, idColours: idManifest.idColours }, palette: manifest.palette ?? null,
    targetQuad: resolveTargetQuad(json("layout.measured.json"), renderQuad, "layout.measured.json"), renderQuad,
    census, prior: cls.likeness,
  });
  const due = dueVisibleParts({ prior: cls.likeness, census, regions, n: 1 });
  const owners = familyOwners({ prior: cls.likeness, census, regions, passes });
  const result = stageResult(raw, false, due, { n: 1, owners });
  assert.deepEqual(result.violations.map((v) => `${v.v} ${v.part}: ${v.measured}`), []);
  assert.equal(result.pass, true);
  // The P1 families' shares, the way stageResult judges them (glass was 0.58x before item 8).
  const fam = raw.areaFamilies;
  const owned = Object.keys(owners).filter((f) => owners[f] <= 1);
  const share = (counts, f) => counts[f] / owned.reduce((s, g) => s + (counts[g] ?? 0), 0);
  const ratio = (f) => share(fam.render.counts, f) / share(fam.target.counts, f);
  for (const f of ["glass", "grey"]) {
    assert.ok(owned.includes(f), `${f} is judged at P1`);
    assert.ok(Math.abs(ratio(f) - 1) <= 0.3, `${f} P1 share ${ratio(f).toFixed(3)}x`);
  }
  assert.ok(ratio("glass") >= 0.72, `glass ${ratio("glass").toFixed(3)}x keeps its margin over the 0.70x floor`);
});
