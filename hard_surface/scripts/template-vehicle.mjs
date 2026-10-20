#!/usr/bin/env node
// WORKFLOW-V3 §6 stage S2 for the VEHICLE class — the deterministic P0 body
// template, the counterpart of scripts/template-building.mjs. Subject manifest +
// layout.json + census.json + classes/vehicle.json (and the frame convention of
// classes/vehicle.md) in, one complete kernel module (`meta` + `build()`) out.
// No seat, no randomness: the same inputs always give a byte-identical module.
//
//   node scripts/template-vehicle.mjs [--subject <id>] [--out <file>] [--through P0]
//
//   --subject  subject id (subjects/<id>/subject.json); LLMM_SUBJECT, else the default.
//   --out      where to write the module (default <subject outDir>/template.mjs).
//              Refuses to write over the subject's live module.
//   --through  the last pass whose layout keys + staged census the module must
//              satisfy (default P0). Passes that introduce detail roles (window,
//              headlight, grille, mirror) are refused: they stay with the author seat.
//
// FRAME (classes/vehicle.md): +Y up, y = 0 ground, LENGTH along Z with the nose at
// +Z, WIDTH along X centred on x = 0, meta.front "+X" (the flank faces the camera).
//
// L / W / H RULE (picked once):
//   L = CLASS_DEFAULTS.length — no key measures metres; the structural inventory
//       refs/pickup_truck.README.md gives "roughly 4.8 m long".
//   W = width.overL x L,  H = height.overL x L  (the cab roof realises H: cab.roof).
//   Every z is nose-relative: z = L/2 - fraction x L. Wheel radius = wheel.diameterOverL x L / 2.
//   Body underside baseY = max(bumper.front.top x H, wheel top + seam): the nose face
//   starts on the front bumper's top, and the body never sinks into the wheels.
//   A key that is unverified or absent falls back to a class default and is marked
//   `// MVP-STUB:` in the generated module.
//
// The generated import is relative to the subject's LIVE module location, so the
// file is copy-ready (the evidence run copies it over the live module).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { ROOT, loadSubject, subjectIdFromArgv } from "./subject.mjs";
import { TemplateRefusal, passKeys, passIndex } from "./template-building.mjs";
import { layoutRules, DETAIL_PRIORS } from "../src/validate/rules/vehicle.mjs";
import { startKnob, priorKnob, knobsBlock } from "./knobs.mjs";

export { TemplateRefusal };

/** Class construction defaults (metres unless noted). No layout key measures these. */
export const CLASS_DEFAULTS = Object.freeze({
  length: 4.8,                // refs/pickup_truck.README.md structural inventory
  seam: 0.001,                // sub-mm seating at shared faces (flush faces alone are not contact)
  tyreW: 0.3,
  sidewall: 0.06,             // MIN_FEAT
  treadT: 0.06,               // MIN_FEAT
  hubR: 0.62,                 // x wheel radius
  hubT: 0.06,
  segs: 24,
  floorT: 0.1,
  wallT: 0.08,
  // WF-V3 blind Gemini pickup P1: the target shows the far front tyre UNDER the front bumper
  // (refs/pickup_truck.png dark component x 122..237, y 691..746 px, 633 px). At the solved
  // camera a ray from that tyre's lowest front arc rises 0.795 m per metre toward the camera and
  // meets the underside of a bumper deeper than ~0.10 m (bumper bottom = bumper.front.top -
  // bumper.front.h), so 0.15 hid it; 0.06 shows it (118 px blob at 900 px, LK_VISIBLE wheel 3 of 3).
  bumperD: 0.06,
  clearance: 0.3,             // m, inside limits.v7.ground_clearance
  // fall-backs for keys that are unverified or absent (unit in the key's unit);
  // proportions from refs/pickup_truck.README.md (4.8 x 1.9 x 1.8 m) where it gives one
  keys: {
    "wheel.diameterOverL": 0.16,
    "wheel.centreFromFront": [0.2, 0.8],
    "height.overL": 0.375,
    "width.overL": 0.396,
    "cab.start": 0.33,
    "cab.end": 0.58,
    "bed.start": 0.6,
    "bed.end": 1,
    "hood.top": 0.6,
    "cab.roof": 1,
    "bedWall.top": 0.6,
    "bumper.front.top": 0.35,
    "bumper.front.h": 0.1,
    "bumper.rear.h": 0.1,
    // WF-R3 R3-B item 5: no rake measured = a vertical windshield face at cab.start
    "window.front.bottom": 0.6,
    "window.front.top": 0.9,
    "window.front.topAt": 0.33,
  },
});

/** Roles the template builds; tyre + hub come with every wheel. */
export const SUPPORTED_ROLES = Object.freeze(["chassis", "hood", "cab", "bed", "bed_wall", "tailgate", "bumper", "wheel", "tyre", "hub"]);
/** Layout keys the template reads. A due key outside this list is refused. */
export const CONSUMED_KEYS = Object.freeze([
  "wheel.diameterOverL", "wheel.centreFromFront", "wheelbase.overL", "height.overL", "width.overL",
  "cab.start", "cab.end", "bed.start", "bed.end", "hood.top", "cab.roof", "bedWall.top",
  "bumper.front.top", "bumper.front.h", "bumper.rear.h", "bumper.rear.top", "chassis.clearance",
  "window.front.bottom", "window.front.top", "window.front.topAt",
]);

const num = (n) => String(Math.round(n * 1e6) / 1e6);

/** Census keys due by pass n, the layout keys due, and the roles due (class order). */
export function stageThrough({ passes, census, cls, n }) {
  const stage = census?._pass ?? {};
  const staged = {};
  for (const [k, v] of Object.entries(census ?? {})) {
    if (!k.startsWith("_") && (stage[k] ?? 0) <= n) staged[k] = v;
  }
  const keys = [];
  const roles = new Set();
  for (let i = 0; i <= n; i += 1) {
    const text = String(passes[i].item ?? "");
    for (const k of passKeys(text)) if (!keys.includes(k)) keys.push(k);
    for (const m of text.matchAll(/\brole (\w+)/g)) if (cls.roles.includes(m[1])) roles.add(m[1]);
  }
  for (const [key, rule] of Object.entries(cls.censusRules ?? {})) {
    if (Object.hasOwn(staged, key)) roles.add(rule.role);
  }
  for (const k of keys) for (const role of layoutRules[k]?.roles ?? []) roles.add(role);
  const wheelRoles = cls.wheelRoles ?? ["wheel", "tyre", "hub"];
  if (wheelRoles.some((r) => roles.has(r))) for (const r of wheelRoles) roles.add(r);
  return { staged, keys, roles: cls.roles.filter((r) => roles.has(r)) };
}

/** A verified numeric layout value, or null. */
function measured(layout, key) {
  const e = layout?.[key];
  if (!e || typeof e !== "object" || e.unverified === true) return null;
  if (Array.isArray(e.values) && e.values.every(Number.isFinite)) return e.values;
  return Number.isFinite(e.value) ? e.value : null;
}

/**
 * Generate the module text. Pure: every input is an argument.
 * @returns {{text:string, L:number, W:number, H:number, roles:string[], keys:string[], stubs:string[], staged:object}}
 */
export function generateVehicleModule({ subjectId, cls, layout, census, passes, through = "P0", importPath = "../../src/kernel/index.mjs" }) {
  const n = passIndex(through, passes);
  const { staged, keys, roles } = stageThrough({ passes, census, cls, n });
  const unsupported = roles.filter((r) => !SUPPORTED_ROLES.includes(r));
  if (unsupported.length) {
    throw new TemplateRefusal(`${passes[n].id} introduces role(s) the template does not build: ${unsupported.join(", ")} — `
      + "details stay with the author seat; template through an earlier pass");
  }
  const body = ["chassis", "hood", "cab", "bed", "bed_wall", "tailgate", "bumper", "wheel"];
  const absent = body.filter((r) => !roles.includes(r));
  if (absent.length) throw new TemplateRefusal(`${passes[n].id} does not ask for the whole body (no ${absent.join(", ")}) — nothing to template`);
  const unknown = keys.filter((k) => !CONSUMED_KEYS.includes(k));
  if (unknown.length) throw new TemplateRefusal(`layout key(s) the template does not read: ${unknown.join(", ")}`);
  const want = cls.wheels ?? { count: 4, axles: 2 };
  const wheels = staged.wheels ?? want.count;
  if (wheels !== want.count || want.count !== 2 * want.axles || want.axles !== 2) {
    throw new TemplateRefusal(`census wheels ${wheels} on ${want.axles} axles — the template builds 4 wheels on 2 axles only`);
  }
  if ((staged.bumpers ?? 2) !== 2) throw new TemplateRefusal(`census bumpers ${staged.bumpers} — the template builds a front and a rear bumper only`);

  const D = CLASS_DEFAULTS;
  const stubs = [];
  /** `[value, comment]` for a layout key, falling back to a class default marked MVP-STUB. */
  const key = (name) => {
    const v = measured(layout, name);
    if (v !== null) return [v, `layout: ${name}`];
    const why = layout?.[name]?.unverified === true ? `unverified key ${name}` : `missing key ${name}`;
    if (!stubs.includes(why)) stubs.push(why);
    return [D.keys[name], `MVP-STUB: ${why} — class default`];
  };

  const [wOverL, wN] = key("width.overL");
  const [hOverL, hN] = key("height.overL");
  const [dia, diaN] = key("wheel.diameterOverL");
  let [centres, centresN] = key("wheel.centreFromFront");
  if (!Array.isArray(centres) || centres.length !== 2) {
    centres = D.keys["wheel.centreFromFront"];
    centresN = "MVP-STUB: wheel.centreFromFront does not list 2 axles — class default";
    stubs.push("wheel.centreFromFront axle count");
  }
  const [front, rear] = [...centres].sort((a, b) => a - b);
  const wheelbase = measured(layout, "wheelbase.overL");
  let wheelbaseN = `wheelbase.overL ${num(rear - front)} follows`;
  if (Number.isFinite(wheelbase)) {
    const tol = Number.isFinite(layout["wheelbase.overL"].tol) ? layout["wheelbase.overL"].tol : 0.02;
    wheelbaseN = Math.abs(wheelbase - (rear - front)) <= tol
      ? `wheelbase.overL ${wheelbase} agrees (${num(rear - front)})`
      : `MVP-STUB: wheelbase.overL ${wheelbase} disagrees with the centres (${num(rear - front)}) — centres win`;
    if (wheelbaseN.startsWith("MVP-STUB")) stubs.push("wheelbase.overL disagreement");
  }
  const [cs, csN] = key("cab.start");
  const [ce, ceN] = key("cab.end");
  const [bs, bsN] = key("bed.start");
  const [be, beN] = key("bed.end");
  const [ht, htN] = key("hood.top");
  const [cr, crN] = key("cab.roof");
  const [bw, bwN] = key("bedWall.top");
  const [bft, bftN] = key("bumper.front.top");
  const [bfh, bfhN] = key("bumper.front.h");
  const [brh, brhN] = key("bumper.rear.h");
  const rearTopMeasured = measured(layout, "bumper.rear.top");
  const brt = rearTopMeasured ?? bft;
  let brtN = "layout: bumper.rear.top";
  if (rearTopMeasured === null) {
    const why = layout?.["bumper.rear.top"]?.unverified === true ? "unverified key bumper.rear.top" : "missing key bumper.rear.top";
    stubs.push(why);
    brtN = `MVP-STUB: ${why} — the front bumper's top`;
  }
  const clrMeasured = measured(layout, "chassis.clearance");
  let clrExpr;
  let clrN;
  if (clrMeasured !== null) {
    clrExpr = `${clrMeasured} * H`;
    clrN = "layout: chassis.clearance";
  } else {
    const why = layout?.["chassis.clearance"]?.unverified === true ? "unverified key chassis.clearance" : "missing key chassis.clearance";
    stubs.push(why);
    clrExpr = num(D.clearance);
    clrN = `MVP-STUB: ${why} — class default (m), inside limits.v7.ground_clearance`;
  }
  if (Math.abs(cr - 1) > 1e-9) stubs.push("cab.roof below 1: H is then realised by nothing");
  const [wfb, wfbN] = key("window.front.bottom");
  const [wft, wftN] = key("window.front.top");
  const [wfa, wfaN] = key("window.front.topAt");

  const L = D.length;
  const W = Math.round(wOverL * L * 1e6) / 1e6;
  const H = Math.round(hOverL * L * 1e6) / 1e6;

  const inputHash = createHash("sha256")
    .update(JSON.stringify({ layout, census, passes: passes.slice(0, n + 1).map((p) => p.item), through: passes[n].id, roles: cls.roles }))
    .digest("hex").slice(0, 16);

  // WF-R3 R3-B item 2 — every author palette key of the class, so P1 detail helpers (glass, lamp, grille, mirror) never
  // need a palette edit; scripts/calibrate-palette.mjs rewrites each from the target.
  const zones = new Set(["body", "bed", "tyre", "tread", "hub", "bumper", ...(cls.paletteZones ?? []).filter((z) => z.closure !== true).map((z) => z.key)]);
  const zoneOrder = (cls.paletteZones ?? []).map((z) => z.key);
  const rank = (k) => (zoneOrder.includes(k) ? zoneOrder.indexOf(k) : zoneOrder.length);
  const paletteKeys = [...zones].sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));

  const header = [
    `// GENERATED by scripts/template-vehicle.mjs — subject ${subjectId}, through ${passes[n].id}, inputs ${inputHash}.`,
    "// Generated starting point; edits required by this pass or its LOOK failures are allowed.",
    "// Every dimension below is a layout.json fraction of L, W or H,",
    "// a census count, or a class default (MVP-STUB where a key is unverified or missing). Palette hex are",
    "// placeholders that scripts/calibrate-palette.mjs rewrites from the target.",
    `// Roles (class prior): ${roles.join(", ")}.`,
    `// Layout keys due: ${keys.join(", ") || "none"}.`,
    `// Census due: ${Object.entries(staged).map(([k, v]) => `${k} ${v}`).join(", ") || "none"}.`,
    `import * as K from "${importPath}";`,
    "",
    "export const meta = {",
    '  front: "+X",',
    `  class: "${cls.class}",`,
    "  seed: 1,",
    "  shade: { ao: 0, upTint: 0, sideTint: 0 },",
    "  palette: {",
    ...paletteKeys.map((k) => `    ${k}: "#808080",`),
    "  },",
    "};",
    "",
  ];
  // WF-R5 R5-A item 1 — a subject with a measured `_profile` (scripts/measure-profile.mjs) gets the PROFILE body: one
  // K.assemble.vehicleBody call whose every argument is printed here in metres from layout.json.
  if (layout._profile && typeof layout._profile === "object") {
    const text = profileBody({ header, cls, layout, D, L, W, H, cs, ce, bs, bw, ht, bft, bfh, brh, wfb, dia, front, rear, stubs });
    return { text, L, W, H, roles, keys, stubs, staged };
  }
  const out = [
    `// GENERATED by scripts/template-vehicle.mjs — subject ${subjectId}, through ${passes[n].id}, inputs ${inputHash}.`,
    "// Generated starting point; edits required by this pass or its LOOK failures are allowed.",
    "// Every dimension below is a layout.json fraction of L, W or H,",
    "// a census count, or a class default (MVP-STUB where a key is unverified or missing). Palette hex are",
    "// placeholders that scripts/calibrate-palette.mjs rewrites from the target.",
    `// Roles (class prior): ${roles.join(", ")}.`,
    `// Layout keys due: ${keys.join(", ") || "none"}.`,
    `// Census due: ${Object.entries(staged).map(([k, v]) => `${k} ${v}`).join(", ") || "none"}.`,
    `import * as K from "${importPath}";`,
    "",
    "export const meta = {",
    '  front: "+X",',
    `  class: "${cls.class}",`,
    "  seed: 1,",
    "  shade: { ao: 0, upTint: 0, sideTint: 0 },",
    "  palette: {",
    ...paletteKeys.map((k) => `    ${k}: "#808080",`),
    "  },",
    "};",
    "",
    "export function build() {",
    "  // L / W / H rule (scripts/template-vehicle.mjs header). Nose at +Z, centred on x = 0 and z = 0.",
    `  const L = ${num(L)};                   // class default body length (m), refs/pickup_truck.README.md`,
    `  const W = ${wOverL} * L;${" ".repeat(Math.max(1, 13 - String(wOverL).length))}// ${wN}`,
    `  const H = ${hOverL} * L;${" ".repeat(Math.max(1, 13 - String(hOverL).length))}// ${hN}`,
    "  const zFront = L / 2;",
    "  const fromNose = (fraction) => zFront - fraction * L;",
    `  const seam = ${D.seam};`,
    "  const parts = [];",
    "  // Contact is measured (kernel API, Contact): no part here is seated deep, so none declares touches.",
    "  const add = (id, solid, zone, role) => {",
    "    const part = { id, solid, zone, role };",
    "    parts.push(part);",
    "    return part;",
    "  };",
    "  /** A box spanning x centred on `x`, y0..y1 and z0..z1. */",
    "  const slab = (w, y0, y1, z0, z1, x = 0) => K.box([w, y1 - y0, z1 - z0]).at([x, y0, (z0 + z1) / 2]);",
    "",
    "  // ------------------------------------------------------------ wheels + chassis",
    `  const R = ${dia} * L / 2;             // ${diaN} (diameter over L)`,
    `  const axles = [["f", fromNose(${front})], ["r", fromNose(${rear})]];   // ${centresN}; ${wheelbaseN}`,
    "  // class defaults (m): tyre width, sidewall, tread depth, hub radius (x R), hub proud, facets",
    `  const tyreW = ${D.tyreW}, sidewall = ${D.sidewall}, treadT = ${D.treadT}, hubR = ${D.hubR} * R, hubT = ${D.hubT}, segs = ${D.segs};`,
    `  const bumperTop = ${bft} * H;${" ".repeat(6)}// ${bftN}`,
    "  // body underside: the nose face starts on the front bumper's top, never below the wheel tops",
    "  const baseY = Math.max(bumperTop, 2 * R + seam);",
    `  const clearance = ${clrExpr};${" ".repeat(8)}// ${clrN}`,
    "  // The chassis runs between the wheels' inner faces from the tail to the front wheels' leading edge; every body",
    "  // part rests on it. It stops short of the nose whenever the front bumper can seat on the hood instead, so the far",
    "  // front tyre shows under the front bumper at the solved camera, as in the target (classes/vehicle.json visibleInstances).",
    "  const chassisFront = bumperTop >= baseY - seam ? Math.min(zFront, axles[0][1] + R) : zFront;",
    "  const chassisRear = zFront - L;",
    '  add("chassis", K.box([W - 2 * tyreW + 2 * seam, baseY - clearance, chassisFront - chassisRear]).at([0, clearance, (chassisFront + chassisRear) / 2]), "tyre", "chassis");',
    "",
    "  // One wheel = tyre disc (sidewall + core, role wheel) + tread ring (role tyre) + hub disc (role hub).",
    "  // Profiles are [radius, axial]; revolved about Y, .rotZ(90) turns the axis onto X with the outer face at x = 0",
    "  // and the disc running toward -x. Outer face flush with the flank; the inner face seats a seam into the chassis.",
    "  const tyre = K.revolve([[0, 0], [R, 0], [R, sidewall], [R - treadT + seam, sidewall], [R - treadT + seam, tyreW], [0, tyreW]], segs).rotZ(90);",
    "  const tread = K.revolve([[R - treadT, sidewall - seam], [R, sidewall - seam], [R, tyreW], [R - treadT, tyreW]], segs).rotZ(90);",
    "  const hub = K.revolve([[0, 0], [hubR, 0], [hubR, hubT], [0, hubT]], segs).rotZ(90);",
    "  // +x is the cab's left (l); the -x partner is the exact mirror across x = 0 (VEH_MIRROR).",
    '  const sides = [["l", (solid) => solid], ["r", (solid) => solid.mirrorX()]];',
    "  for (const [axle, z] of axles) {",
    "    for (const [side, place] of sides) {",
    "      const id = `${axle}${side}`;",
    '      add(`wheel_${id}`, place(tyre.at([W / 2, R, z])), "tyre", "wheel");',
    '      add(`tread_${id}`, place(tread.at([W / 2, R, z])), "tread", "tyre");',
    '      add(`hub_${id}`, place(hub.at([W / 2 + hubT - seam, R, z])), "hub", "hub");',
    "    }",
    "  }",
    "",
    "  // ------------------------------------------------------------ hood + cab (lengths from the nose)",
    `  const cabFront = fromNose(${cs});${" ".repeat(6)}// ${csN}`,
    `  const cabRear = fromNose(${ce});${" ".repeat(7)}// ${ceN}`,
    `  const hoodTop = ${ht} * H;${" ".repeat(9)}// ${htN}`,
    `  const cabTop = ${cr} * H;${" ".repeat(12)}// ${crN} (the cab is the tallest part: it realises H)`,
    '  add("hood", slab(W, baseY - seam, hoodTop, cabFront - seam, zFront), "body", "hood");',
    "  // WF-R3 R3-B item 5 — the cab is its SIDE PROFILE (z, y) pushed across the width: the windshield face rakes back",
    "  // from its lower edge at cab.start through the measured top corner to the roof; below it the cowl steps up",
    "  // from the hood top to the windshield's lower edge (the hood step).",
    `  const wsBottom = ${wfb} * H;${" ".repeat(6)}// ${wfbN}`,
    `  const wsTop = ${wft} * H;${" ".repeat(9)}// ${wftN}`,
    `  const rakeTopZ = fromNose(${wfa});   // ${wfaN}`,
    "  const roofFront = cabFront + (rakeTopZ - cabFront) * (cabTop - wsBottom) / (wsTop - wsBottom);",
    "  /** A solid from a side profile [[z, y], ...] (clockwise seen from +x), spanning the full width in x. */",
    "  const sideProfile = (pts) => K.extrude(K.profile.poly(pts.map(([z, y]) => [-z, y]).reverse()), W).rotY(90).at([-W / 2, 0, 0]);",
    '  const cab = add("cab", sideProfile([[cabRear, baseY - seam], [cabFront, baseY - seam], [cabFront, wsBottom], [roofFront, cabTop], [cabRear, cabTop]]), "body", "cab");',
    "  void cab;                          // P1 seats the windshield and side panes in it: K.assemble.pane({ host: cab, ... })",
    "",
    "  // ------------------------------------------------------------ OPEN bed: floor, side walls, bulkhead, tailgate",
    "  // No lid: from the solved camera you see down into the floor over the near wall.",
    `  const bedFront = Math.min(fromNose(${bs}), cabRear - seam);   // ${bsN} (never into the cab)`,
    `  const bedRear = fromNose(${be});${" ".repeat(7)}// ${beN}`,
    `  const wallTop = ${bw} * H;${" ".repeat(9)}// ${bwN}`,
    `  const floorT = ${D.floorT}, wallT = ${D.wallT};     // class defaults (m)`,
    "  const wallBase = baseY + floorT - seam;",
    '  add("bed_floor", slab(W, baseY - seam, baseY + floorT, bedRear, bedFront), "bed", "bed");',
    '  add("bed_side_l", slab(wallT, wallBase, wallTop, bedRear, bedFront, (W - wallT) / 2), "body", "bed_wall");',
    '  add("bed_side_r", slab(wallT, wallBase, wallTop, bedRear, bedFront, -(W - wallT) / 2), "body", "bed_wall");',
    '  add("bed_bulkhead", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedFront - wallT, bedFront), "bed", "bed_wall");',
    '  add("tailgate", slab(W - 2 * wallT + 2 * seam, wallBase, wallTop, bedRear, bedRear + wallT), "body", "tailgate");',
    "",
    "  // ------------------------------------------------------------ bumpers across the full width",
    `  const bumperD = ${D.bumperD};${" ".repeat(10)}// class default depth (m)`,
    `  const frontH = ${bfh} * H;${" ".repeat(9)}// ${bfhN}`,
    `  const rearH = ${brh} * H;${" ".repeat(10)}// ${brhN}`,
    `  const rearTop = ${brt} * H;${" ".repeat(8)}// ${brtN}`,
    '  add("bumper_front", slab(W, bumperTop - frontH, bumperTop, zFront - seam, zFront + bumperD), "bumper", "bumper");',
    '  add("bumper_rear", slab(W, rearTop - rearH, rearTop, zFront - L - bumperD, zFront - L + seam), "bumper", "bumper");',
    "  return parts;",
    "}",
    "",
  ];
  return { text: out.join("\n"), L, W, H, roles, keys, stubs, staged };
}

/**
 * WF-R5 R5-A + WORKFLOW v4 V4-2 — the profile body module. Every continuous size / position is ONE knob in the
 * `export const KNOBS` block at the top (scripts/knobs.mjs): side elevation (hood rise from hood.top at the nose to the
 * cowl, the rake to the roof, the cab back and its lean, bedWall.top, body.sill, the front bumper's top), the cab
 * section (belt line + roof inset), the two measured arches, the wheels and the bumpers, in metres (4 decimals).
 * build() reads ONLY KNOBS. V5-9: a layout key gives a knob its START; every range is the class prior
 * (classes/vehicle.json knobPriors); `locked` knobs (the registration anchor, edges the solved camera cannot see) stay.
 */
function profileBody({ header, cls, layout, D, L, W, H, cs, ce, bs, bw, ht, bft, bfh, brh, wfb, dia, front, rear, stubs }) {
  const P = layout._profile;
  const pk = (k) => (P.keys?.[k] && !P.keys[k].unverified ? P.keys[k].value : null);
  const zF = L / 2;
  const z = (u) => zF - u * L;
  const priors = cls.knobPriors ?? {};
  const sizes = { L, W, H };
  const knobs = {};
  const notes = {};
  /** one knob: started at a verified layout key (else the template value), ranged by the class prior (V5-9) */
  const knob = (name, v, { key = null, toM = null, note = "", min, max, unit = "m" } = {}) => {
    const entry = key ? layout[key] : null;
    const usable = entry && typeof entry === "object" && entry.unverified !== true;
    // V5-9 evidence hierarchy: a verified key gives the START only; the RANGE is the class prior (plausibility)
    knobs[name] = usable
      ? startKnob({ v, key, prior: priors[name] ?? priors._keyed, sizes, min, max, unit })
      : priorKnob({ v, prior: priors[name] ?? (key ? priors._unverifiedKey : null), sizes, min, max, unit });
    notes[name] = note || (usable ? key : "class prior");
  };
  const yH = (f) => f * H;
  const zL = (f) => zF - f * L;

  const sill = (pk("body.sill") ?? D.keys["bumper.front.top"]) * H;
  if (pk("body.sill") === null) stubs.push("_profile body.sill");
  const hoodRear = Math.min(pk("hood.rear") ?? ht, wfb);
  const cabFront = z(cs);
  const rakeTopZ = z(layout["window.front.topAt"]?.value ?? D.keys["window.front.topAt"]);
  const wftV = layout["window.front.top"]?.value ?? D.keys["window.front.top"];
  const roofFront = cabFront + (rakeTopZ - cabFront) * (H - wfb * H) / (wftV * H - wfb * H);
  if (!Array.isArray(P.arches) || P.arches.length !== 2) throw new TemplateRefusal("_profile.arches must list the front and the rear arch");
  const belt = Math.max(...P.front.points.map((p) => p[1]).filter((v) => v > 0 && v < 1));
  const roofHalf = Math.max(...P.front.points.filter((p) => p[1] >= 1).map((p) => Math.abs(p[0])));
  const planBox = P.plan.points.every(([x, u]) => Math.abs(Math.abs(x) - 0.5) < 1e-9 && (u === 0 || u === 1));
  if (!planBox) stubs.push("_profile.plan is not the W x L box (the KNOBS body builds the box plan)");
  const rOut = pk("bumper.rear.out");
  const rTop = pk("bumper.rear.top");
  const rDepth = pk("bumper.rear.depth");
  if (rDepth === null) stubs.push("_profile bumper.rear.depth");
  const liner = P.inlays?.archLiner?.zone ?? "grille";
  const splitCowl = Math.abs(hoodRear - wfb) > 1e-6;

  knob("L", L, { note: "class default length (m), refs/pickup_truck.README.md; the registration anchor" });
  knob("W", W, { key: "width.overL", toM: (v) => v * L });
  knob("H", H, { key: "height.overL", toM: (v) => v * L, note: "height.overL (the roof)" });
  knob("hoodNoseY", ht * H, { key: "hood.top", toM: yH, note: "hood.top at the nose" });
  if (splitCowl) {
    knob("cowlY", hoodRear * H, { note: "_profile hood.rear (the cowl)" });
    knob("wsBottomY", wfb * H, { key: "window.front.bottom", toM: yH });
  } else {
    knob("cowlY", wfb * H, { key: "window.front.bottom", toM: yH, note: "window.front.bottom = _profile hood.rear (the cowl)" });
  }
  knob("roofFrontZ", roofFront, { note: "prior: the rake meets the roof (window.front.top / topAt)" });
  knob("cabFrontZ", cabFront, { key: "cab.start", toM: zL });
  knob("cabRearZ", z(ce), { key: "cab.end", toM: zL, note: "cab.end at the bed-wall top" });
  knob("cabRearTopZ", z(ce), { note: "prior: the roof corner of the cab back (its lean)" });
  knob("bedFrontZ", Math.min(z(bs), z(ce) - D.seam), { key: "bed.start", toM: zL });
  knob("bedWallTopY", bw * H, { key: "bedWall.top", toM: yH });
  knob("sillY", sill, { note: "_profile body.sill (the body's lower edge)" });
  knob("beltY", belt * H, { note: "_profile.front: the glass line the cab leans in above" });
  knob("roofInset", (0.5 - roofHalf) * W, { min: 0, note: "_profile cab.roofInset (each side)" });
  knob("clearance", D.clearance, { note: "MVP-STUB: chassis.clearance unverified — class default" });
  knob("wheelR", dia * L / 2, { key: "wheel.diameterOverL", toM: (v) => v * L / 2 });
  knob("wheelWidth", D.tyreW, { min: 0.1 });
  knob("wheelFrontZ", z(front), { key: "wheel.centreFromFront", toM: zL });
  knob("wheelRearZ", z(rear), { key: "wheel.centreFromFront", toM: zL });
  // V4-5A detail knobs (class priors, rules/vehicle.mjs DETAIL_PRIORS): the dished hub, the raised hood centre panel
  const Rw = dia * L / 2;
  knob("hubR", DETAIL_PRIORS.hub.r * Rw, { note: "MVP-STUB: hub disc radius, class prior (x R)" });
  knob("hubRing", DETAIL_PRIORS.hub.ring * Rw, { note: "MVP-STUB: hub rim-ring radial width, class prior (x R)" });
  knob("hubCap", DETAIL_PRIORS.hub.cap * Rw, { note: "MVP-STUB: hub centre-cap radius, class prior (x R)" });
  knob("hoodPanelHalfNose", DETAIL_PRIORS.hoodPanel.halfNose * W, { note: "MVP-STUB: raised hood panel half-width at the nose (x W)" });
  knob("hoodPanelHalfCowl", DETAIL_PRIORS.hoodPanel.halfCowl * W, { note: "MVP-STUB: raised hood panel half-width at the cowl (x W)" });
  knob("hoodPanelInsetNose", DETAIL_PRIORS.hoodPanel.insetNose, { note: "MVP-STUB: panel inset from the hood's nose edge" });
  knob("hoodPanelInsetCowl", DETAIL_PRIORS.hoodPanel.insetCowl, { note: "MVP-STUB: panel inset from the hood's cowl edge" });
  for (const [i, a] of P.arches.entries()) {
    const t = i === 0 ? "archF" : "archR";
    knob(`${t}Z`, z(a.zc), { note: `_profile arch.${a.name ?? t}.centre` });
    knob(`${t}Half`, a.a * L, { min: 0.1, note: "halfLength" });
    knob(`${t}Rise`, a.b * H, { min: 0.1, note: "rise over the sill" });
    knob(`${t}N`, a.n, { min: 2, unit: "exp", note: "superellipse exponent" });
  }
  knob("bumperFTop", bft * H, { key: "bumper.front.top", toM: yH });
  knob("bumperFH", bfh * H, { key: "bumper.front.h", toM: yH, min: 0.05 });
  knob("bumperFDepth", D.bumperD, { min: 0.04, note: "depth past the nose (> 0.10 hides the far-front tyre)" });
  knob("bumperFOut", 0.04, { min: 0.005, note: "proud of the flanks (wrapped bumper)" });
  knob("bumperFWrap", 0.2, { min: 0.02, note: "wrap back along the flanks" });
  knob("bumperRTop", (rTop ?? layout["bumper.rear.top"]?.value ?? bft) * H, { key: "bumper.rear.top", toM: yH, note: "bumper.rear.top (_profile, on the face's own plane)" });
  knob("bumperRH", brh * H, { key: "bumper.rear.h", toM: yH, min: 0.05 });
  knob("bumperRDepth", (rDepth ?? 0.05) * L, { min: 0.02, note: "_profile bumper.rear.depth" });
  knob("bumperROut", (rOut ?? 0) * W, { note: "_profile bumper.rear.out" });

  const at = header.indexOf("export const meta = {");
  const cowl = splitCowl ? "[k.cabFrontZ, k.cowlY], [k.cabFrontZ, k.wsBottomY]" : "[k.cabFrontZ, k.cowlY]";
  return [...header.slice(0, at),
    "// KNOBS: every continuous number of the body (metres). scripts/fit.mjs fits the unlocked ones; build() reads only these.",
    knobsBlock(knobs, notes),
    "",
    ...header.slice(at),
    "export function build() {",
    "  const k = Object.fromEntries(Object.entries(KNOBS).map(([name, o]) => [name, o.v]));",
    `  const zN = k.L / 2, zT = -k.L / 2, seam = ${D.seam};   // nose at +z, centred on x = 0 and z = 0`,
    "  const zA = Math.max(k.archFZ, k.archRZ);   // the nose face drops to the sill at the front arch",
    "  const parts = K.assemble.vehicleBody({",
    "    W: k.W, H: k.H,",
    `    side: [[zN, k.hoodNoseY], ${cowl}, [k.roofFrontZ, k.H], [k.cabRearTopZ, k.H], [k.cabRearZ, k.bedWallTopY],`,
    "      [zT, k.bedWallTopY], [zT, k.sillY], [zA, k.sillY], [zA, k.bumperFTop - seam], [zN, k.bumperFTop - seam]],   // the nose face seats a seam into the front bumper",
    "    section: [[-k.W / 2, 0], [k.W / 2, 0], [k.W / 2, k.beltY], [k.W / 2 - k.roofInset, k.H], [k.roofInset - k.W / 2, k.H], [-k.W / 2, k.beltY]],",
    "    cab: [k.cabRearZ, k.cabFrontZ],",
    "    bed: { z: [zT, k.bedFrontZ], wallTop: k.bedWallTopY },   // the floor clears the rear arch (bed.floor unverified)",
    "    sill: k.sillY, clearance: k.clearance,",
    "    wheels: { r: k.wheelR, width: k.wheelWidth, z: [k.wheelFrontZ, k.wheelRearZ], hub: { r: k.hubR, ring: k.hubRing, cap: k.hubCap }, segs: [16, 8] },   // V5-3 LOD (triBudget): 16 near facets; the far pair shows one sliver",
    "    arches: [{ z: k.archFZ, halfLength: k.archFHalf, rise: k.archFRise, n: k.archFN }, { z: k.archRZ, halfLength: k.archRHalf, rise: k.archRRise, n: k.archRN }], archSegs: [12, 8],",
    "    bumpers: [{ face: \"nose\", top: k.bumperFTop, h: k.bumperFH, depth: k.bumperFDepth, out: k.bumperFOut, wrap: k.bumperFWrap },",
    "      { face: \"tail\", top: k.bumperRTop, h: k.bumperRH, depth: k.bumperRDepth, out: k.bumperROut }],",
    `    zones: { liner: "${liner}" },   // _profile.inlays.archLiner (the wheel-well tone)`,
    "  });",
    "  // the raised hood centre panel, its edges the creases (V4-5A)",
    "  parts.push(...K.assemble.hoodPanel({ host: parts.find((p) => p.id === \"hood\"), half: [k.hoodPanelHalfNose, k.hoodPanelHalfCowl],",
    "    inset: [k.hoodPanelInsetNose, k.hoodPanelInsetCowl], idPrefix: \"hoodPanel\" }));",
    "  return parts;   // P1 seats panes, seams and handles in the part with id \"cab\"",
    "}",
    "",
  ].join("\n");
}

/**
 * V4-7 — the BUS body module (classes/vehicle.json variants.bus): one flat-nosed box, role cab from the nose to the
 * tail (K.assemble.vehicleBody hood: false, bed: null), its side elevation from _profile (nose face to nose.top, the
 * front cap back to roof.front, the sill and the two measured arches), the chamfered front corners (_profile plan),
 * the black bumpers and four wheels. Every continuous number is one KNOBS entry (scripts/knobs.mjs): started at a layout key,
 * ranged (V5-9) by the class prior (classes/vehicle.json knobPriors + variants.bus.overrides.knobPriors). No passes: the
 * details (split windshield, window band + pane row, lamps, mirrors, stop arm) are READY calls (rules/vehicle.mjs
 * busReadyCalls) the BUILD seat pastes.
 */
export function generateBusModule({ subjectId, cls, layout, census, importPath = "../../src/kernel/index.mjs" }) {
  const D = CLASS_DEFAULTS;
  const P = layout?._profile;
  if (!P || P.variant !== "bus") throw new TemplateRefusal(`subject ${subjectId} has no bus _profile (scripts/measure-profile.mjs --freeze)`);
  if (!Array.isArray(P.arches) || P.arches.length !== 2) throw new TemplateRefusal("_profile.arches must list the front and the rear arch");
  const want = cls.wheels ?? { count: 4, axles: 2 };
  if ((census?.wheels ?? want.count) !== 4 || want.axles !== 2) throw new TemplateRefusal(`census wheels ${census?.wheels} — the template builds 4 wheels on 2 axles only`);
  if ((census?.bumpers ?? 2) !== 2) throw new TemplateRefusal(`census bumpers ${census?.bumpers} — the template builds a front and a rear bumper only`);
  const stubs = [];
  const val = (k) => (layout[k] && !layout[k].unverified && Number.isFinite(layout[k].value) ? layout[k].value : null);
  const need = (k) => { const v = val(k); if (v === null) throw new TemplateRefusal(`the bus body needs the verified layout key ${k}`); return v; };
  const pk = (k) => (P.keys?.[k] && !P.keys[k].unverified ? P.keys[k].value : null);
  const L = D.length;
  const W = Math.round(need("width.overL") * L * 1e6) / 1e6;
  const H = Math.round(need("height.overL") * L * 1e6) / 1e6;
  const zF = L / 2;
  const z = (u) => zF - u * L;
  const [front, rear] = [...layout["wheel.centreFromFront"].values].sort((a, b) => a - b);
  const dia = need("wheel.diameterOverL");
  const bft = need("bumper.front.top");
  const bfh = need("bumper.front.h");
  const brt = val("bumper.rear.top") ?? bft;
  if (val("bumper.rear.top") === null) stubs.push("bumper.rear.top unverified: the front bumper's top");
  const brh = val("bumper.rear.h") ?? bfh;
  if (val("bumper.rear.h") === null) stubs.push("bumper.rear.h unverified: the front bumper's h");
  const lim = JSON.parse(fs.readFileSync(path.join(ROOT, "src", "validate", "limits.json"), "utf8"));
  const floorY = lim.styleFloor?.[cls.styleFloorKey] ?? 0.04;   // MIN_FEAT of the class style floor
  const priors = cls.knobPriors ?? {};
  const sizes = { L, W, H };
  const knobs = {};
  const notes = {};
  const knob = (name, v, { key = null, toM = null, note = "", min, max, unit = "m" } = {}) => {
    const entry = key ? layout[key] : null;
    const usable = entry && typeof entry === "object" && entry.unverified !== true;
    // V5-9 evidence hierarchy: a verified key gives the START only; the RANGE is the class prior (plausibility)
    knobs[name] = usable
      ? startKnob({ v, key, prior: priors[name] ?? priors._keyed, sizes, min, max, unit })
      : priorKnob({ v, prior: priors[name] ?? (key ? priors._unverifiedKey : null), sizes, min, max, unit });
    notes[name] = note || (usable ? key : "class prior");
  };
  const yH = (f) => f * H;
  const zL = (f) => zF - f * L;
  const Rw = dia * L / 2;
  knob("L", L, { note: "class default length (m), the registration anchor (scripts/registered.mjs)" });
  knob("W", W, { key: "width.overL", toM: (v) => v * L });
  knob("H", H, { key: "height.overL", toM: (v) => v * L, note: "height.overL (the flank top = the roof)" });
  knob("noseTopY", (pk("nose.top") ?? need("window.front.top")) * H, { note: "_profile nose.top (the flat nose face ends, the front cap begins)" });
  knob("roofFrontZ", z(pk("roof.front") ?? 0), { note: "_profile roof.front (the cap meets the roof)" });
  knob("chamfer", (pk("corner.chamfer") ?? 0) * W, { min: 0.005, note: "_profile corner.chamfer (the rounded vertical front corners, each side)" });
  knob("sillY", (pk("body.sill") ?? bft) * H, { note: "_profile body.sill (the body's lower edge between the arches)" });
  knob("clearance", D.clearance, { note: "MVP-STUB: chassis.clearance unverified — class default" });
  knob("wheelR", Rw, { key: "wheel.diameterOverL", toM: (v) => v * L / 2 });
  knob("wheelWidth", D.tyreW, { min: 0.1 });
  knob("wheelFrontZ", z(front), { key: "wheel.centreFromFront", toM: zL });
  knob("wheelRearZ", z(rear), { key: "wheel.centreFromFront", toM: zL });
  // V5-6: the bus hub is ONE flat grey disc (refs/school_bus.png: no rim ring, no centre cap)
  knob("hubR", DETAIL_PRIORS.hub.r * Rw, { note: "MVP-STUB: hub disc radius, class prior (x R)" });
  for (const [i, a] of P.arches.entries()) {
    const t = i === 0 ? "archF" : "archR";
    knob(`${t}Z`, z(a.zc), { note: `_profile arch.${a.name ?? t}.centre` });
    knob(`${t}Half`, a.a * L, { min: 0.1, note: "halfLength" });
    knob(`${t}Rise`, a.b * H, { min: 0.1, note: "rise over the sill" });
    knob(`${t}N`, a.n, { min: 2, unit: "exp", note: "superellipse exponent" });
  }
  // no part but the wheels reaches the ground: a bumper's bottom stays >= MIN_FEAT (the class style floor) above it
  knob("bumperFTop", bft * H, { key: "bumper.front.top", toM: yH });
  knob("bumperFH", Math.min(bfh * H, bft * H - floorY), { key: "bumper.front.h", toM: yH, min: 0.05, max: bft * H - floorY, note: "bumper.front.h, its bottom kept >= MIN_FEAT off the ground" });
  knob("bumperFDepth", D.bumperD, { min: 0.04, note: "class default depth past the nose" });
  knob("bumperFOut", 0.04, { min: 0.005, note: "proud of the flanks (wrapped bumper)" });
  const wrapM = pk("bumper.front.wrap");
  knob("bumperFWrap", wrapM !== null ? Math.max(0.02, Math.round(wrapM * L * 1e4) / 1e4) : 0.2, { min: 0.02, note: wrapM !== null ? "_profile bumper.front.wrap (the black run back along the flank)" : "wrap back along the flanks" });
  knob("bumperRTop", brt * H, { key: "bumper.rear.top", toM: yH });
  knob("bumperRH", Math.min(brh * H, brt * H - floorY), { key: "bumper.rear.h", toM: yH, min: 0.05, max: brt * H - floorY, note: "bumper.rear.h, its bottom kept >= MIN_FEAT off the ground" });
  knob("bumperRDepth", D.bumperD, { min: 0.02, note: "class default depth past the tail" });
  // V5-6: a measured rear wrap (the block round the rear corner, _profile bumper.rear.wrap) stands proud like the front
  const wrapR = pk("bumper.rear.wrap");
  knob("bumperROut", wrapR !== null ? 0.04 : 0, { note: wrapR !== null ? "proud of the flanks (wrapped rear bumper)" : "proud of the flanks" });
  if (wrapR !== null) knob("bumperRWrap", Math.max(0.02, Math.round(wrapR * L * 1e4) / 1e4), { min: 0.02, note: "_profile bumper.rear.wrap (the black run forward along the flank)" });
  // V5-2 rounding (start 0 = the sharp box; FIT opens them inside the class prior range)
  knob("roofR", 0, { min: 0, note: "section top-corner radius (the roof edge, both sides)" });
  knob("capR", 0, { min: 0, note: "side-profile arc over the nose->roof cap (nose-top and roof-front corners)" });
  knob("cornerR", 0, { min: 0, note: "plan corner radius (the vertical body corners)" });

  const inputHash = createHash("sha256").update(JSON.stringify({ layout, census, variant: "bus", roles: cls.roles })).digest("hex").slice(0, 16);
  // V5-3 colour: ONE body tone unless a split is measured — the lit roof (_profile roof.upTint, linear-light ratio of the
  // roof and flank paint) is the renderer's up-facing lift (src/geom.js upTint); under 3 % it is one tone
  const upM = pk("roof.upTint");
  const upTint = upM !== null && Math.abs(upM) > 0.03 ? Math.round(upM * 1000) / 1000 : 0;
  const paletteKeys = (cls.paletteZones ?? []).filter((z0) => z0.closure !== true).map((z0) => z0.key);
  const text = [
    `// GENERATED by scripts/template-vehicle.mjs — subject ${subjectId}, variant bus, inputs ${inputHash}.`,
    "// Generated starting point; edits required by the loop's residual rows are allowed.",
    "// Every dimension below is a layout.json fraction of L, W or H (or its _profile), a census count, or a class",
    "// default (MVP-STUB). Palette hex are placeholders that scripts/calibrate-palette.mjs rewrites from the target.",
    "// Roles: cab (the whole box), chassis, body (arch liners), bumper, wheel, tyre, hub.",
    `// Census due: wheels ${census?.wheels ?? 4}, bumpers ${census?.bumpers ?? 2}.`,
    `import * as K from "${importPath}";`,
    "",
    "// KNOBS: every continuous number of the body (metres). scripts/fit.mjs fits the unlocked ones; build() reads only these.",
    knobsBlock(knobs, notes),
    "",
    "export const meta = {",
    '  front: "+X",',
    `  class: "${cls.class}",`,
    "  seed: 1,",
    `  shade: { ao: 0, upTint: ${upTint}, sideTint: 0 },`,
    "  palette: {",
    ...paletteKeys.map((k) => `    ${k}: "#808080",`),
    "  },",
    "};",
    "",
    "export function build() {",
    "  const k = Object.fromEntries(Object.entries(KNOBS).map(([name, o]) => [name, o.v]));",
    `  const zN = k.L / 2, zT = -k.L / 2, seam = ${D.seam};   // nose at +z, centred on x = 0 and z = 0`,
    "  const zA = Math.max(k.archFZ, k.archRZ) + (k.archFZ > k.archRZ ? k.archFHalf : k.archRHalf);   // the nose block drops to the bumper ahead of the front arch",
    "  const parts = K.assemble.vehicleBody({",
    "    W: k.W, H: k.H, hood: false, bed: null,",
    "    side: [[zN, k.noseTopY], [k.roofFrontZ, k.H], [zT, k.H], [zT, k.sillY], [zA, k.sillY], [zA, k.bumperFTop - seam], [zN, k.bumperFTop - seam]],",
    "    section: [[-k.W / 2, 0], [k.W / 2, 0], [k.W / 2, k.H], [-k.W / 2, k.H]],",
    "    plan: [[-k.W / 2, zT], [k.W / 2, zT], [k.W / 2, zN - k.chamfer], [k.W / 2 - k.chamfer, zN], [k.chamfer - k.W / 2, zN], [-k.W / 2, zN - k.chamfer]],",
    "    cab: [zT, zN], chassisFront: zA,   // the chassis ends where the nose block drops below the sill",
    "    roofR: k.roofR, capR: k.capR, cornerR: k.cornerR,   // V5-2 rounding (0 = sharp)",
    "    roundSegs: 2,   // V5-3: 2 facets per rounded edge (every inlay on a rounded face follows its facets: triBudget)",
    "    liner: false,   // V5-6: no arch liner — the target's wheel well is an unlabelled shade, not black paint",
    "    sill: k.sillY, clearance: k.clearance,",
    "    wheels: { r: k.wheelR, width: k.wheelWidth, z: [k.wheelFrontZ, k.wheelRearZ], hub: { r: k.hubR }, segs: [16, 8], hubSegs: [8, 4], tread: false },   // V5-3 LOD: the -x pair is hidden; V5-6 one tyre solid, plain hub",
    "    arches: [{ z: k.archFZ, halfLength: k.archFHalf, rise: k.archFRise, n: k.archFN }, { z: k.archRZ, halfLength: k.archRHalf, rise: k.archRRise, n: k.archRN }], archSegs: [12, 8],",
    "    bumpers: [{ face: \"nose\", top: k.bumperFTop, h: k.bumperFH, depth: k.bumperFDepth, out: k.bumperFOut, wrap: k.bumperFWrap },",
    `      { face: "tail", top: k.bumperRTop, h: k.bumperRH, depth: k.bumperRDepth, out: k.bumperROut${wrapR !== null ? ", wrap: k.bumperRWrap" : ""} }],`,
    "    zones: { body: \"body\", tyre: \"tyre\", tread: \"tyre\", hub: \"hub\", bumper: \"black\", liner: \"black\" },",
    "  });",
    "  return parts;   // the BUILD seat pastes the READY calls (windshield, windowRow, lamps, mirrors, stopArm) here; host: the part with id \"cab\"",
    "}",
    "",
  ].join("\n");
  const roles = ["chassis", "body", "cab", "bumper", "wheel", "tyre", "hub"];
  return { text, L, W, H, roles, keys: Object.keys(layout).filter((k0) => !k0.startsWith("_")), stubs, staged: { wheels: census?.wheels ?? 4, bumpers: census?.bumpers ?? 2 } };
}

/** Load everything off disk for one subject and generate. */
export function generateForSubject(subjectId, { through = "P0", overrides = {} } = {}) {
  const S = loadSubject(subjectId);
  if (S.cls.class !== "vehicle") throw new TemplateRefusal(`subject ${subjectId} is class ${S.cls.class}, not vehicle`);
  const layout = { ...(S.readJson("layout") ?? {}), ...(overrides.layout ?? {}) };
  const census = overrides.census ?? S.readJson("census") ?? {};
  const moduleDir0 = path.dirname(S.paths.module);
  const importPath0 = path.relative(moduleDir0, path.join(ROOT, "src", "kernel", "index.mjs")).replace(/\\/g, "/");
  // V4-7: the bus variant has no passes (v4 builds details from READY calls)
  if (S.subject.variant === "bus") return { S, ...generateBusModule({ subjectId, cls: S.cls, layout, census, importPath: importPath0.startsWith(".") ? importPath0 : `./${importPath0}` }) };
  const passes = S.readJson("passes");
  if (!Array.isArray(passes)) throw new TemplateRefusal(`subject ${subjectId} has no passes.json`);
  const moduleDir = path.dirname(S.paths.module);
  const importPath = path.relative(moduleDir, path.join(ROOT, "src", "kernel", "index.mjs")).replace(/\\/g, "/");
  return { S, ...generateVehicleModule({ subjectId, cls: S.cls, layout, census, passes, through, importPath: importPath.startsWith(".") ? importPath : `./${importPath}` }) };
}

function main() {
  const argv = process.argv.slice(2);
  const flag = (name, fallback) => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : fallback;
  };
  const subjectId = subjectIdFromArgv(argv);
  const through = flag("through", "P0");
  const result = generateForSubject(subjectId, { through });
  const out = path.resolve(flag("out", path.join(ROOT, result.S.subject.outDir, "template.mjs")));
  if (path.resolve(result.S.paths.module).toLowerCase() === out.toLowerCase()) {
    throw new TemplateRefusal(`refusing to overwrite the live module ${result.S.rel.module} — pass --out elsewhere`);
  }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, result.text);
  const sha = createHash("sha256").update(result.text).digest("hex").slice(0, 16);
  console.log(`[template] ${subjectId} through ${through}: L ${result.L} m, W ${result.W} m, H ${result.H} m; roles ${result.roles.join(", ")}`);
  console.log(`  ${result.stubs.length} MVP-STUB default(s): ${result.stubs.join("; ") || "none"}`);
  console.log(`[template] wrote ${path.relative(ROOT, out).replace(/\\/g, "/")} (sha256 ${sha})`);
}

const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  try {
    main();
  } catch (error) {
    console.error(`template: ${error instanceof TemplateRefusal ? "REFUSED — " : ""}${error.message}`);
    process.exitCode = error instanceof TemplateRefusal ? 3 : 1;
  }
}
