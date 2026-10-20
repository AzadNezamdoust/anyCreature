// WORKFLOW v4 — V4-5A: the zone-aware stop and the detail helpers (dished hub, raised hood panel, cab-relative door
// seam, rounded-rect mirror heads, flush lamps). Hermetic: the fitted body is the frozen FIT output
// test/fixtures/v4/fitted-pickup.mjs (the template start after FIT); refs/, subjects/ and classes/ are read only.
process.env.LLMM_SUBJECT = "pickup";
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import * as K from "../src/kernel/index.mjs";
import { validateParts, gateConfig } from "../src/validate/kernel-chain.mjs";
import * as RULES from "../src/validate/rules/vehicle.mjs";
import { loadSubject } from "../scripts/subject.mjs";
import { loadModule } from "../scripts/project.mjs";
import { residuals } from "../scripts/residuals.mjs";
import { moduleFrame } from "../scripts/seat-io.mjs";
import { atTarget, judge, zoneResiduals, applyReply } from "../scripts/loop.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FITTED = "test/fixtures/v4/fitted-pickup.mjs";
const WORK = "test/fixtures/v4/work-pickup.mjs";
const TMP = path.join(ROOT, "test", `.tmp-wf-v45a-${process.pid}`, "m");
test.after(() => fs.rmSync(path.dirname(TMP), { recursive: true, force: true }));
const S = loadSubject("pickup");
const LAYOUT = S.readJson("layout");
const CENSUS = Object.fromEntries(Object.entries(S.readJson("census")).filter(([k]) => !k.startsWith("_")));
let n = 0;

/** The fitted module with `lines` inserted before `return parts;` (and an optional KNOBS edit), written + loaded. */
async function withCalls(lines, edit = (t) => t) {
  const text = edit(fs.readFileSync(path.join(ROOT, FITTED), "utf8"));
  const ins = lines.length ? applyReply(text, ["```js", 'const cab = parts.find((p) => p.id === "cab");', ...lines, "```"].join("\n")).text : text;
  n += 1;
  const file = path.join(TMP, `m${n}.mjs`);
  fs.mkdirSync(TMP, { recursive: true });
  fs.writeFileSync(file, ins);
  return loadModule(path.relative(ROOT, file));
}

async function gate(mod, census) {
  await K.init();
  if (K.assemble?.ready) await K.assemble.ready;
  K.configure(gateConfig(S.cls));
  const parts = mod.build();
  assert.deepEqual(K.checkParts(mod.meta, parts), []);
  const report = await validateParts(mod.meta, parts, undefined, { cls: S.cls, rules: RULES, layout: LAYOUT, census });
  return { parts, report };
}

async function readyOnFitted() {
  const mod = await loadModule(FITTED);
  await K.init();
  if (K.assemble?.ready) await K.assemble.ready;
  K.configure(gateConfig(S.cls));
  const frame = await moduleFrame(mod.build(), S);
  return frame.ready(LAYOUT, null, gateConfig(S.cls).minFeat ?? 0.04);
}

test("V4-5A zone stop: a zone under its class band blocks the target stop and becomes a shown ZONE row with a proposal", async () => {
  const bands = S.cls.zoneIouMin;
  assert.deepEqual(Object.keys(bands).sort(), ["body", "dark", "glass", "lamp", "light"]);
  // the Opus reference (the calibration source) clears every band: no ZONE row
  const r = await residuals({ subjectId: "pickup", modulePath: WORK });
  for (const [f, b] of Object.entries(bands)) assert.ok(r.familyIoU[f] >= b, `${f} ${r.familyIoU[f]} >= ${b}`);
  assert.deepEqual(zoneResiduals(r, bands, S.cls.zoneProposals), []);
  // one band above the reference's dark IoU -> one ZONE row, sized by the family's wrong px, naming its knobs
  const rows = zoneResiduals(r, { ...bands, dark: r.familyIoU.dark + 0.05 }, S.cls.zoneProposals);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].kind, "ZONE");
  assert.equal(rows[0].family, "dark");
  assert.equal(rows[0].areaPx, r.familyPx.dark.U - r.familyPx.dark.I);
  // V4-6 items 2/3: the family is labelled "<f>-family" (never printed as a zone) and the row carries ONE proposal
  assert.match(rows[0].text, /^RESIDUAL dark-family ZONE IoU 0\.\d+ < band 0\.\d+ \(\d+ px wrong\) — worst part "[^"]+" .* — proposal: (push|pull|move|grow|shrink|remove|add) /);
  assert.ok(rows[0].knobPrefixes.includes("wheelR"));
  const m = { loads: true, pass: true, coverage: { frac: 1 }, iou: 0.99, shown: [], zoneRows: [] };
  assert.equal(atTarget(m, null, 0.97), true);
  assert.equal(atTarget({ ...m, zoneRows: rows, shown: rows }, null, 0.97), false, "a zone under band blocks the stop");
  // the guard: fewer zones under band is strictly better, more is a reject
  const base = { loads: true, iou: 0.97, blocking: 0, codes: [], coverage: { frac: 1, have: 5, total: 5, missing: [] }, minZone: 0.7, tris: 1, triBudget: 9 };
  assert.equal(judge({ ...base, zoneRows: [] }, { ...base, zoneRows: rows }).accept, true);
  assert.equal(judge({ ...base, iou: 0.99, zoneRows: rows }, { ...base, zoneRows: [] }).accept, false);
});

test("V4-5A template details: dished hubs (ring + cap) and the raised hood panel pass the full chain on the fitted body, KNOBS move them", async () => {
  const mod = await loadModule(FITTED);
  for (const k of ["hubR", "hubRing", "hubCap", "hoodPanelHalfNose", "hoodPanelHalfCowl", "hoodPanelInsetNose", "hoodPanelInsetCowl"]) {
    assert.ok(mod.KNOBS[k] && mod.KNOBS[k].max > mod.KNOBS[k].min, `${k} is a free knob`);
  }
  const { parts, report } = await gate(mod, { wheels: 4, bumpers: 2 });
  assert.equal(report.pass, true, report.text);
  for (const id of ["hubring_fl", "hubcap_fl", "hubring_rr", "hubcap_rr", "hoodPanel"]) {
    assert.ok(parts.some((p) => p.id === id), id);
  }
  const hub = parts.find((p) => p.id === "hub_fl").solid.aabb();
  const ring = parts.find((p) => p.id === "hubring_fl").solid.aabb();
  const cap = parts.find((p) => p.id === "hubcap_fl").solid.aabb();
  assert.ok(ring.max[0] > hub.max[0] + 0.03 && cap.max[0] > hub.max[0] + 0.03, "ring and cap stand proud of the hub face");
  assert.ok(Math.abs((ring.max[1] - ring.min[1]) - (hub.max[1] - hub.min[1])) < 0.01, "the ring is the hub's rim");
  assert.ok(cap.max[1] - cap.min[1] < ring.max[1] - ring.min[1] - 0.1, "the cap sits inside the ring");
  const hood = parts.find((p) => p.id === "hood").solid.aabb();
  const panel = parts.find((p) => p.id === "hoodPanel").solid.aabb();
  assert.ok(panel.max[1] > hood.max[1] + 0.03, "the panel is raised over the hood top");
  assert.ok(panel.max[0] - panel.min[0] < hood.max[0] - hood.min[0] - 0.2, "the panel is a centre panel");
  // a knob moves its detail (FIT can tune it)
  const v0 = mod.KNOBS.hubCap.v;
  mod.KNOBS.hubCap.v = v0 - 0.03;
  try {
    const cap2 = mod.build().find((p) => p.id === "hubcap_fl").solid.aabb();
    assert.ok(cap2.max[1] - cap2.min[1] < cap.max[1] - cap.min[1] - 0.04);
  } finally { mod.KNOBS.hubCap.v = v0; }
});

test("V4-5A READY details: flush lamps, rounded mirror heads and the door seam build on the fitted body; the whole set passes the full chain", async () => {
  const ready = await readyOnFitted();
  const call = (re) => { const c = ready.find((x) => re.test(x.what)); assert.ok(c, `READY call ${re}`); return c.call; };
  assert.match(call(/^headlights/), /flush: true/);
  assert.match(call(/^mirrors/), /round: \d/);
  assert.match(call(/^door seams/), /door: \{ front: [\d.]+, rear: [\d.]+, bottom: [\d.]+, knee: [\d.]+, top: [\d.]+, rake: [\d.-]+ \}/);
  // V5-3: the fixture predates the template's far-side LOD (wheel / arch facets); the READY set (frame, crease, raked
  // mirror arms) is budgeted against the current template, so the fixture gets the same LOD
  const lod = (t) => t.replace("hub: { r: k.hubR, ring: k.hubRing, cap: k.hubCap } },", "hub: { r: k.hubR, ring: k.hubRing, cap: k.hubCap }, segs: [16, 8] }, archSegs: [12, 8],");
  const mod = await withCalls(ready.filter((c) => !/^hood panel/.test(c.what)).map((c) => c.call), lod);
  const { parts, report } = await gate(mod, CENSUS);
  assert.equal(report.pass, true, report.text);
  // flush lamp: the lens sits in a recess, its back under the nose face by the groove depth
  const nose = Math.max(...parts.filter((p) => p.role === "hood" && p.assembly?.helper !== "hoodPanel").map((p) => p.solid.aabb().max[2]));
  const lens = parts.find((p) => p.id === "lamp_l").solid.aabb();
  assert.ok(lens.min[2] < nose - 0.015, `lens back ${lens.min[2]} under the nose ${nose}`);
  assert.ok(lens.max[2] - nose < 0.03, "stands < 0.03 m proud");
  // rounded head: less volume than its box
  const head = parts.find((p) => p.id === "mirror_head_l").solid;
  const hb = head.aabb();
  assert.ok(head.volume() < 0.99 * (hb.max[0] - hb.min[0]) * (hb.max[1] - hb.min[1]) * (hb.max[2] - hb.min[2]), "the head's corners are rounded");
  for (const id of ["door_l", "door_r"]) assert.ok(parts.some((p) => p.id === id), id);
});

test("V4-5A door seam follows the fitted cab: never dropped, inside the cab when FIT moves the cab's ends", async () => {
  const ready = await readyOnFitted();
  const seam = ready.find((c) => /^door seams/.test(c.what));
  assert.ok(seam, "the door seam is offered");
  // the blind Luna run's drop: FIT moved cab.end 0.028 m past door.end (seam path z -0.278 outside the cab's -0.250)
  for (const [dRear, dFront] of [[0, 0], [0.1, 0], [0.25, 0], [0.2, -0.05]]) {
    const mod = await withCalls([seam.call], (t) => t
      .replace(/(\n\s*cabRearZ:\s*\{\s*v:\s*)(-?[\d.]+)/, (m, a, v) => `${a}${Number(v) + dRear}`)
      .replace(/(\n\s*cabFrontZ:\s*\{\s*v:\s*)(-?[\d.]+)/, (m, a, v) => `${a}${Number(v) + dFront}`));
    const { parts, report } = await gate(mod, { wheels: 4, bumpers: 2 });
    assert.equal(report.pass, true, `cab moved ${dRear} / ${dFront}: ${report.text}`);
    const cab = parts.find((p) => p.id === "cab").solid.aabb();
    const door = parts.find((p) => p.id === "door_l").solid.aabb();
    assert.ok(door.min[2] >= cab.min[2] - 1e-6 && door.max[2] <= cab.max[2] + 1e-6, `door z ${door.min[2]}..${door.max[2]} in cab ${cab.min[2]}..${cab.max[2]}`);
  }
});
