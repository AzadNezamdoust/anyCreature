// WF-R3 Job R3-B (research/WF-R3-PLAN.md) — vehicle + prompt: H2 own-assembly visibility, the vehicle detail helpers
// (K.assemble.pane / lamp / grille / mirror, K.span), metre bounds per key (rule inverses, ready calls), the raked
// windshield + LK_SILHOUETTE, and the prompt diet. Fixtures under test/fixtures/vehicle/ are FROZEN: the Luna P1 id
// pass that ended on "wheel covered by hub_rl", and the box-cab (old start-P1) and raked-template id passes.
process.env.LLMM_SUBJECT = "pickup";            // pass.mjs S(): the prompt tests assemble pickup prompts
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, chainContext } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { ROOT, moduleFrame, assemblePrompt, assembleRepairPrompt, applyLineEdits, autoFixPaletteZones, authorReadme, gateTokens, resolveItem, REPAIR_SHARE } from "../scripts/pass.mjs";
import { acceptanceBlock } from "../scripts/likeness.mjs";
import { shallowLateral } from "../src/validate/kernel-chain.mjs";
import { maskFromIdpass, ownLabels, lostInstances, silhouetteHull, silhouetteIoU } from "../scripts/likeness.mjs";

await K.init();
await K.assemble.ready;

const sharp = createRequire(import.meta.url)("sharp");
const PICKUP = loadSubject("pickup");
const LAYOUT = PICKUP.readJson("layout");
const P1 = PICKUP.readJson("passes").find((p) => p.id === "P1");
const FIX = path.join(ROOT, "test", "fixtures", "vehicle");
const TMP = path.join(ROOT, "test", `.tmp-wf-r3b-${process.pid}`);
test.after(() => fs.rmSync(TMP, { recursive: true, force: true }));
let seq = 0;
async function importText(text) {
  fs.mkdirSync(TMP, { recursive: true });
  const file = path.join(TMP, `module_${seq += 1}.mjs`);
  fs.writeFileSync(file, text);
  return import(pathToFileURL(file).href);
}
const readImage = async (file) => {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, w: info.width, h: info.height, c: info.channels };
};
const opts = () => ({ cls: PICKUP.cls, rules: RULES, layout: LAYOUT, census: PICKUP.readJson("census") });
const START = fs.readFileSync(path.join(FIX, "silhouette-rake.mjs"), "utf8");
// WF-R5 R5-A: the P1 start is the profile body (frozen copy of out/blind/pickup/start-P1.mjs); the rake fixture stays for the silhouette rows.
const START_R5 = fs.readFileSync(path.join(FIX, "start-r5a.mjs"), "utf8");

/** The raked start + the harness's READY calls = what a P1 author pastes. */
async function helperP1(layout = LAYOUT) {
  const start = await importText(START_R5);
  const frame = await moduleFrame(start.build(), PICKUP);
  const calls = RULES.readyCalls(layout, frame.F, { cited: P1.requiredLayoutKeys, minFeat: 0.04 });
  const text = START_R5.replace("  return parts;\n}", `  ${calls.map((c) => c.call).join("\n  ")}\n  return parts;\n}`);
  const mod = await importText(text);
  return { mod, parts: mod.build(), calls, frame };
}

// ---------------------------------------------------------------------------------------------------- item 1 (H2)
test("H2: a wheel's own tyre and hub count toward it — the frozen Luna P1 render reads wheel 3 of 3 (2 of 3 on the wheel label alone)", async () => {
  const image = await readImage(path.join(FIX, "idpass-luna-p1.png"));
  const { idColours } = JSON.parse(fs.readFileSync(path.join(FIX, "idpass-luna-p1.json"), "utf8"));
  const mask = maskFromIdpass(image, idColours);
  const prior = PICKUP.cls.likeness;
  assert.deepEqual(prior.instanceRoles.wheel, ["wheel", "tyre", "hub"]);
  const blobs = (labels) => {
    const seen = new Uint8Array(mask.label.length);
    let n = 0;
    for (let s = 0; s < mask.label.length; s += 1) {
      if (seen[s] || !labels.has(mask.label[s])) continue;
      let px = 0;
      const stack = [s];
      seen[s] = 1;
      while (stack.length) {
        const i = stack.pop();
        px += 1;
        const x = i % image.w;
        for (const [j, ok] of [[i - 1, x > 0], [i + 1, x + 1 < image.w], [i - image.w, i >= image.w], [i + image.w, i + image.w < mask.label.length]]) {
          if (ok && !seen[j] && labels.has(mask.label[j])) { seen[j] = 1; stack.push(j); }
        }
      }
      if (px >= 50) n += 1;
    }
    return n;
  };
  assert.equal(blobs(new Set([mask.roles.indexOf("wheel")])), 2, "the old count: the far-front sliver is tyre only");
  assert.equal(blobs(ownLabels(prior, "wheel", mask)), 3);
  // lostInstances never names the instance's own hub as its occluder
  const lost = lostInstances({ occlusion: { previous: { image, idColours }, label: "P0" }, mask, role: "wheel", w: image.w, h: image.h, ownRoles: prior.instanceRoles.wheel });
  assert.deepEqual(lost, []);
});

// ---------------------------------------------------------------------------------------------------- item 2
test("K.span sorts and checks its bounds", () => {
  assert.deepEqual(K.span({ x: [1, -1], y: [0, 2] }), { x: [-1, 1], y: [0, 2] });
  assert.throws(() => K.span({ x: [1, 1] }), /BAD_ARG: span x .* has no extent/);
  assert.throws(() => K.span({}), /BAD_ARG: span needs at least one of x, y, z/);
  assert.throws(() => K.span({ z: [0, "a"] }), /BAD_ARG/);
});

test("a P1 module built only from the helpers + measured keys passes the full chain, V12 on every P1 key, no VEH_HANDBUILT", async () => {
  const { mod, parts, calls } = await helperP1();
  assert.equal(calls.length, 8, calls.map((c) => c.what).join(", "));   // V5-3: + the hood crease
  const report = await validateParts(mod.meta, parts, undefined, opts());
  assert.equal(report.pass, true, report.text);
  const ctx = chainContext(mod.meta, parts, undefined, opts());
  const F = RULES.layoutFrame(ctx);
  for (const key of P1.requiredLayoutKeys) {
    const got = RULES.layoutRules[key].measure(ctx, F);
    assert.ok(got.length > 0, `${key} measured`);
  }
  assert.ok(!report.violations.some((v) => v.v === "V12_LAYOUT"));
  assert.ok(!report.advisories.some((a) => a.v === "VEH_HANDBUILT"));
  for (const p of parts.filter((q) => ["window", "headlight", "grille", "mirror"].includes(q.role))) assert.equal(p.solid.decompose().length, 1, p.id);
});

test("item 3: inverse -> measure returns the value (within a quarter tol); value +- 2 tol fails V12 for that key", async () => {
  const { mod, parts } = await helperP1();
  const ctx = chainContext(mod.meta, parts, undefined, opts());
  const F = RULES.layoutFrame(ctx);
  for (const key of P1.requiredLayoutKeys) {
    const e = LAYOUT[key];
    const rule = RULES.layoutRules[key];
    assert.ok(rule.inverse, `${key} has an inverse`);
    const want = Array.isArray(e.values) ? [...e.values].sort((a, b) => a - b) : null;
    const got = rule.measure(ctx, F).map((m) => m.measured).sort((a, b) => a - b);
    for (let i = 0; i < got.length; i += 1) {
      const v = want ? want[i] : e.value;
      assert.ok(Math.abs(got[i] - v) <= 0.25 * e.tol + 1e-9, `${key} measured ${got[i]} vs ${v} (tol ${e.tol})`);
      assert.ok(Math.abs(rule.inverse(rule.inverse.axis === "z" ? (F.zFront - rule.inverse(v, F)) / F.L : v, F) - rule.inverse(v, F)) < 1e-9);
    }
    if (e.unit === "count" || want) continue;
    for (const sign of [1, -1]) {
      const moved = { ...LAYOUT, [key]: { ...e, value: e.value + sign * 2 * e.tol } };
      const report = await validateParts(mod.meta, parts, undefined, { ...opts(), layout: moved });
      assert.ok(report.violations.some((v) => v.v === "V12_LAYOUT" && v.measured.startsWith(key)), `${key} ${sign > 0 ? "+" : "-"}2 tol fails`);
    }
  }
});

test("item 3: H comes from the body box — a part above the roof cannot move H; a position tol is capped at 0.25 x the feature", async () => {
  const start = await importText(START_R5);
  const parts = start.build();
  const before = RULES.layoutFrame(chainContext(start.meta, parts, undefined, opts())).H;
  parts.push({ id: "aerial", role: "prop", zone: "tyre", solid: K.box([0.05, 1, 0.05]).at([0, 2.6, 0]) });
  assert.equal(RULES.layoutFrame(chainContext(start.meta, parts, undefined, opts())).H, before);
  const ext = RULES.layoutRules["window.side.start"].extent(LAYOUT);
  assert.ok(Math.abs(ext - (LAYOUT["window.side.end"].value - LAYOUT["window.side.start"].value)) < 1e-9);
  assert.ok(RULES.POSITION_TOL_SHARE * ext < LAYOUT["window.side.start"].tol, "the cap is tighter than the scan tol here");
});

test("helpers on every face pass V3/V5/V6; nose parts refuse proud depth beyond the bumper's; hand-placed details get VEH_HANDBUILT", async () => {
  const meta = { front: "+X", class: "vehicle", seed: 1, palette: { body: "#808080", glass: "#808080", lamp: "#808080", grille: "#808080", mirror: "#808080", bumper: "#808080", tyre: "#808080" } };
  const build = (bumperD) => {
    const cab = { id: "cab", role: "cab", zone: "body", solid: K.box([2, 2.1, 4]) };
    const parts = [cab,
      { id: "bumper_f", role: "bumper", zone: "bumper", solid: K.box([2, 0.2, bumperD + 0.001]).at([0, 0.3, 2 + bumperD / 2 - 0.0005]) },
      { id: "bumper_r", role: "bumper", zone: "bumper", solid: K.box([2, 0.2, bumperD + 0.001]).at([0, 0.3, -2 - bumperD / 2 + 0.0005]) }];
    for (const face of ["+x", "-x"]) parts.push(...K.assemble.pane({ host: cab, face, bounds: K.span({ z: [-1, 1], y: [1.2, 1.9] }), idPrefix: `side${face}` }));
    for (const face of ["+z", "-z"]) parts.push(...K.assemble.pane({ host: cab, face, bounds: K.span({ x: [-0.8, 0.8], y: [1.3, 1.9] }), idPrefix: `end${face}` }));
    parts.push(...K.assemble.lamp({ body: parts, face: "nose", centre: [0.6, 0.9], diameter: 0.25 }));
    parts.push(...K.assemble.lamp({ body: parts, face: "tail", centre: [0.6, 0.9], diameter: 0.2, idPrefix: "tail_lamp" }));
    parts.push(...K.assemble.grille({ body: parts, face: "tail", bounds: K.span({ x: [-0.3, 0.3], y: [0.7, 1.0] }), slots: 2 }));
    parts.push(...K.assemble.mirror({ body: parts, side: 1, centreY: 1.5, z: 1.2, head: { w: 0.2, h: 0.3 }, arm: 0.1 }));
    return parts;
  };
  const parts = build(0.08);
  const report = await validateParts(meta, parts, undefined, { cls: PICKUP.cls, rules: RULES, census: false, layout: false });
  const bad = report.violations.filter((v) => /^(V3|V5|V6)/.test(v.v));
  assert.deepEqual(bad.map((v) => `${v.v} ${v.part}`), [], report.text);
  assert.throws(() => build(0.03), /BAD_ARG: lamp stands 0\.040 m proud, deeper than the bumper's 0\.030 m/);
  parts.push({ id: "hand_pane", role: "window", zone: "glass", solid: K.box([0.5, 0.3, 0.04]).at([0, 1.4, -2.02]) });
  const hand = RULES.validators.find(([n]) => n === "VEH_HANDBUILT")[1](chainContext(meta, parts, undefined, { cls: PICKUP.cls, rules: RULES }));
  assert.equal(hand.advisories.length, 1);
  assert.match(hand.advisories[0].measured, /^1 detail part\(s\) not built by K\.assemble/);
  assert.throws(() => K.assemble.pane({ host: parts[0], face: "+x", bounds: K.span({ z: [-1, 1], y: [1.2, 2.6] }) }), /leave host "cab"/);
});

// ---------------------------------------------------------------------------------------------------- item 5
test("item 5: LK_SILHOUETTE — the frozen box-cab render fails the band, the raked template passes", async () => {
  const target = await readImage(path.join(ROOT, PICKUP.rel.target));
  const band = PICKUP.cls.likeness.silhouette.iouMin;
  const out = {};
  for (const name of ["box", "rake"]) {
    const { manifest } = JSON.parse(fs.readFileSync(path.join(FIX, `silhouette-${name}.json`), "utf8"));
    const image = await readImage(path.join(FIX, `silhouette-${name}.png`));
    const mod = await importText(fs.readFileSync(path.join(FIX, `silhouette-${name}.mjs`), "utf8"));
    const records = mod.build().map((p) => ({ id: p.id, role: p.role, aabb: p.solid.aabb() }));
    const hull = silhouetteHull(RULES.silhouetteBox(LAYOUT, records, PICKUP.cls), manifest);
    out[name] = silhouetteIoU({ target, mask: maskFromIdpass(image, manifest.idColours), w: image.w, h: image.h, hull,
      renderQuad: manifest.frontQuad.px, targetQuad: LAYOUT._frame.quadPx }).iou;
  }
  assert.ok(out.box < band, `box cab IoU ${out.box.toFixed(3)} < ${band}`);
  assert.ok(out.rake >= band, `raked template IoU ${out.rake.toFixed(3)} >= ${band}`);
  // the template reads the measured rake: the cab's front face leans back from cab.start
  const cab = (await importText(START)).build().find((p) => p.id === "cab").solid.aabb();
  assert.ok(Math.abs(cab.max[2] - (2.4 - LAYOUT["cab.start"].value * 4.8)) < 1e-6);
});

// ---------------------------------------------------------------------------------------------------- item 4
test("item 4: a PALETTE_ZONE row with one suggested key is rewritten by the harness; a lateral margin beside a shallow groove is no V5_THIN", async () => {
  const { mod, parts } = await helperP1();
  const text = fs.readFileSync(path.join(TMP, `module_${seq}.mjs`), "utf8").replace(/, o\.zone \?\? T\.zones\.lamp/, "");
  const bad = text.replace("  return parts;\n}", "  for (const p of parts) if (p.role === \"headlight\") p.zone = \"headlight\";\n  return parts;\n}")
    .replace("    lamp: \"#808080\",", "    headlight: \"#808080\",");
  const broken = await importText(bad);
  const before = await validateParts(broken.meta, broken.build(), undefined, opts());
  assert.deepEqual(before.violations.map((v) => v.v), ["PALETTE_ZONE"], before.text);
  // the rewrite handles `zone: "headlight"` literals and the palette key; this module assigns zone in code, so check the literal form
  const literal = autoFixPaletteZones('export const meta = { palette: {\n    headlight: "#808080",\n  } };\nconst a = { zone: "headlight", role: "headlight" };', before.violations);
  assert.deepEqual(literal.fixes, [{ from: "headlight", to: "lamp" }]);
  assert.match(literal.text, /lamp: "#808080"/);
  assert.match(literal.text, /zone: "lamp", role: "headlight"/);
  assert.deepEqual(autoFixPaletteZones("x", [{ v: "PALETTE_ZONE", measured: 'zone "paint" on 1 part(s)', hint: "use the key of that material" }]).fixes, []);
  void mod; void parts;
  // V5_THIN: a 0.015 m groove 0.02 m from a panel edge (lateral) is fine; the same margin beside a 0.05 m pocket is not
  const target = { min: [0, 0, 0], max: [1, 0.5, 0.1] };
  assert.equal(shallowLateral({ side: "x-", target, tool: { min: [0.02, 0.1, 0.085], max: [0.9, 0.4, 0.2] } }, 0.02), true);
  assert.equal(shallowLateral({ side: "z-", target, tool: { min: [0.02, 0.1, 0.085], max: [0.9, 0.4, 0.2] } }, 0.02), false);
  assert.equal(shallowLateral({ side: "x-", target, tool: { min: [0.02, 0.1, 0.05], max: [0.9, 0.4, 0.2] } }, 0.02), false);
});

// ---------------------------------------------------------------------------------------------------- item 6
async function firstPrompt() {
  const start = await importText(START_R5);
  const frame = await moduleFrame(start.build(), PICKUP);
  const tokens = gateTokens(PICKUP.cls);
  const item = resolveItem(P1, tokens);
  const acceptance = acceptanceBlock({ prior: PICKUP.cls.likeness, census: PICKUP.readJson("census"), regions: PICKUP.readJson("regions"), n: 1, final: true, passes: PICKUP.readJson("passes") });
  const text = assemblePrompt({ options: { seatMode: "text", label: "P1", n: 1, dry: false }, item, moduleText: START_R5, readme: authorReadme(tokens, PICKUP, "P1"),
    previousReview: null, repairReport: null, acceptance, frame, budget: { used: 2044, cap: 4000 } });
  return { text, item, frame };
}

test("item 6: the pickup P1 prompt is <= 12 kB, carries READY CALLS instead of key restatements, no profile catalogue, no LK_AREA lamp", async () => {
  const { text } = await firstPrompt();
  const bytes = Buffer.byteLength(text, "utf8");
  assert.ok(bytes <= 12 * 1024, `P1 prompt ${bytes} bytes`);
  assert.match(text, /READY CALLS/);
  for (const h of ["pane", "lamp", "grille", "mirror"]) assert.ok(text.includes(`K.assemble.${h}({`), h);
  assert.doesNotMatch(text, /K\.profile\.(arch|stepped|wedge|offset)/);
  assert.doesNotMatch(text, /- window\.side\.start:/, "a key carried by a ready call is not restated");
  assert.doesNotMatch(text, /lamp \(headlight/);
  assert.match(text, /LK_SILHOUETTE/);
  assert.doesNotMatch(text, /# CONSTRUCTION DEFAULTS/);
});

test("item 6: the repair prompt is <= 0.6 x the first (failing rows, ready calls, numbered local lines); line edits apply", async () => {
  const { text: first } = await firstPrompt();
  const { calls } = await helperP1();
  const moduleText = START_R5.replace("  return parts;\n}", `  ${calls.map((c) => c.call).join("\n  ")}\n  parts.push({ id: "stray_box", role: "body", zone: "body", solid: K.box([0.2, 0.2, 0.2]).at([0, 2.8, 0]) });\n  return parts;\n}`);
  const mod = await importText(moduleText);
  const report = await validateParts(mod.meta, mod.build(), undefined, opts());
  assert.equal(report.pass, false);
  const repair = assembleRepairPrompt({ options: { label: "P1" }, item: P1, moduleText, moduleBefore: START_R5, report, likeness: null, ready: calls,
    firstBytes: Buffer.byteLength(first, "utf8") });
  const bytes = Buffer.byteLength(repair, "utf8");
  assert.ok(bytes <= REPAIR_SHARE * Buffer.byteLength(first, "utf8"), `repair ${bytes} vs first ${Buffer.byteLength(first, "utf8")}`);
  assert.match(repair, /# FAILING ROWS/);
  assert.match(repair, /V3_FLOAT/);
  const lineNo = moduleText.split("\n").findIndex((l) => l.includes("stray_box")) + 1;
  assert.ok(repair.split(/\r?\n/).some((l) => l.trim().startsWith(`${lineNo}| `) && l.includes("stray_box")), "the stray line is shown numbered");
  assert.doesNotMatch(repair, /# KERNEL API/);
  const fixed = applyLineEdits(moduleText, `\`\`\`js replace ${lineNo}-${lineNo}\n\`\`\`\nCHANGE: removed the stray box`);
  assert.equal(fixed.edits, 1);
  const again = await importText(fixed.text);
  assert.equal((await validateParts(again.meta, again.build(), undefined, opts())).pass, true);
  assert.match(applyLineEdits(moduleText, "```js replace 5-3\nx\n```").error ?? "", /outside/);
  assert.equal(applyLineEdits(moduleText, "```js\nwhole module\n```").text, null);
});
