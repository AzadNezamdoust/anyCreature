#!/usr/bin/env node
// WORKFLOW-V3 §7 item 8 / §6 stage S2 — the deterministic building TEMPLATE.
// Replaces the first two author seats (P0 massing, P1 openings + trims) with a
// script: subject manifest + layout.json + census.json + class prior in, one
// complete kernel module (`meta` + `build()`) out. No seat, no randomness: the
// same inputs always give a byte-identical module.
//
//   node scripts/template-building.mjs [--subject <id>] [--out <file>] [--through P0|P1] [--knobs]
//
//   --knobs    WORKFLOW v4: the WHOLE building (ironwork included) as a KNOBS module
//              (generateBuildingKnobsModule); --through is ignored.
//
//   --subject  subject id (subjects/<id>/subject.json); LLMM_SUBJECT, else the default.
//   --out      where to write the module (default <subject outDir>/template.mjs).
//              Refuses to write over the subject's live module.
//   --through  the last pass whose layout keys + staged census the module must
//              satisfy (default P1). Passes that need judgement (ironwork) are
//              refused: WORKFLOW-V3 §4 keeps those with the author seat.
//
// W / H RULE (picked once, independent of --through, so a P0 and a P1 template
// share one frame):
//   H = max(H_storey, H_crown), rounded UP to 0.01 m
//       H_storey = class storey height (DEFAULT_FLOOR_H) / window.rowPitch — one
//                  measured row pitch is one storey; without the key,
//                  (census.windowRows + 1) x storey height.
//       H_crown  = (V7 parapet_h floor + margin + coping courses) / crown.height —
//                  the smallest H at which the MEASURED crown fraction still holds
//                  the gate's parapet band under the cornice; 0 without the key.
//   W = H x face.aspect — the MEASURED key (scripts/measure-target.mjs: face px /
//       cos(phi) over wall px / cos(theta) through the solved camera; 0.452 on
//       facade_brick, where the old square-bay guess gave 0.490). Only when that
//       key is absent or unverified: square bays, one measured bay pitch (mean gap
//       of window.centreX) = one measured row pitch in metres, W = rowPitch x H /
//       bayPitch; else census.bays x storey height.  Rounded to 0.001 m.
//
// The generated import is relative to the subject's LIVE module location, so
// the file is copy-ready (the evidence run copies it over the live module).
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { ROOT, loadSubject, subjectIdFromArgv } from "./subject.mjs";
import { DEFAULT_FLOOR_H, layoutRules } from "../src/validate/rules/building.mjs";
import { keyedKnob, priorKnob, knobsBlock } from "./knobs.mjs";

export class TemplateRefusal extends Error {}

/** Class construction defaults (metres unless noted). No layout key measures these. */
export const CLASS_DEFAULTS = Object.freeze({
  floorH: DEFAULT_FLOOR_H,
  wall: 0.3,
  slab: 0.08,
  capH: 0.12,                 // two coping courses of 0.06 m (MIN_FEAT)
  parapetMargin: 0.01,
  seam: 0.00075,              // sub-mm seating at shared faces
  canopyDepth: 0.9,
  awningSeat: 0.06,
  glassReveal: 0.003,     // m the glass sits behind the frame's front face: the target's panes are flush in their outlines (WF-R3-B item 8)
  grille: 0.06,
  signDepth: 0.19,
  pipeSegs: 16,
  // fall-backs for keys that are unverified or absent (unit in the key name's unit)
  keys: {
    "frame.widthRatio": 0.06,     // m (the frame member, not a ratio)
    "frame.proud": 0.06,          // m
    "cornice.projection": 0.12,   // m
    "massing.depthOverW": 0.8,
    "crown.height": 0.03,
    "window.w": 0.09,
    "window.h": 0.12,
    "window.headBelowCoping": 0.04,
    "window.rowPitch": 0.28,
    "storefront.h": 0.08,
    "door.h": 0.13,
    "awning.bottom": 0.16,
    "awning.top": 0.28,
    "awning.span": 0.9,
    "signbox.h": 0.075,
    "signbox.top": 0.37,
    // fractions from the street-right edge; most were MISSING KEYs in run 4 and are
    // measured now (scripts/measure-target.mjs, v3-backlog) — these only stand in
    // when a key is absent or unverified
    "ac.h": 0.075,
    "ac.top": 0.37,
    "ac.centreX": 0.8,
    "storefront.centreX": 0.65,
    "storefront.w": 0.45,
    "storefront.bottom": 0.037,
    "door.centreX": 0.21,
    "door.w": 0.16,
    "awning.centreX": 0.515,
    "awning.depth": 0.35,         // m
    "signbox.centreX": 0.385,
    "signbox.w": 0.61,
    "ac.w": 0.2,
    "ac.depth": 0.09,             // x W
    "roof_fixture.vent": [0.25, 0.7, 0.2, 0.055],   // [x from min x... see code, z x D, size x W, h x H]
    "roof_fixture.pipe": [0.81, 0.37, 0.016, 0.045],
  },
});

/** Roles the template can build; anything else a pass introduces is refused. */
export const SUPPORTED_ROLES = Object.freeze([
  "massing", "roof", "parapet", "cornice", "sill", "window", "storefront", "door",
  "awning", "signbox", "ac", "roof_fixture",
]);

const LIMITS = JSON.parse(fs.readFileSync(path.join(ROOT, "src", "validate", "limits.json"), "utf8"));

const num = (n) => String(Math.round(n * 1e6) / 1e6);
const ceilTo = (n, step) => Math.ceil(n / step - 1e-9) * step;

/** The "Layout keys this pass must satisfy: a, b.c, d." list of one pass item. */
export function passKeys(itemText) {
  const m = /Layout keys this pass must satisfy:\s*(.+?)\.(?:\s+[A-Z]|\s*$)/.exec(String(itemText ?? ""));
  return m ? m[1].split(",").map((s) => s.trim()).filter(Boolean) : [];
}

/** Pass index of "P1" / "1". */
export function passIndex(label, passes) {
  const i = passes.findIndex((p) => String(p.id).toUpperCase() === String(label).toUpperCase());
  if (i >= 0) return i;
  const n = Number(String(label).replace(/^P/i, ""));
  if (Number.isInteger(n) && n >= 0 && n < passes.length) return n;
  throw new TemplateRefusal(`--through "${label}" is not a pass in passes.json (${passes.map((p) => p.id).join(", ")})`);
}

/** Census keys due by pass n (census._pass staging), and the roles due by pass n. */
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
    for (const role of cls.roles) {
      if (new RegExp(`\\brole ${role}\\b`).test(text) || new RegExp(`\\b${role} for the\\b`).test(text)) roles.add(role);
    }
  }
  for (const [key, rule] of Object.entries(cls.censusRules ?? {})) {
    if ((rule.sums ?? [key]).some((k) => Object.hasOwn(staged, k))) roles.add(rule.role);
  }
  for (const k of keys) for (const role of layoutRules[k]?.roles ?? []) roles.add(role);
  return { staged, keys, roles: cls.roles.filter((r) => roles.has(r)) };
}

/** A verified numeric layout value, or null. */
function measured(layout, key) {
  const e = layout?.[key];
  if (!e || typeof e !== "object" || e.unverified === true) return null;
  if (Array.isArray(e.values) && e.values.every(Number.isFinite)) return e.values;
  return Number.isFinite(e.value) ? e.value : null;
}

/** The W / H rule (see the header). Pure. */
export function pickFrame(layout, census) {
  const D = CLASS_DEFAULTS;
  const notes = [];
  const rowPitch = measured(layout, "window.rowPitch");
  let hStorey;
  if (rowPitch) {
    hStorey = D.floorH / rowPitch;
    notes.push(`H_storey = ${D.floorH} m storey / window.rowPitch ${rowPitch} = ${num(hStorey)} m`);
  } else {
    hStorey = ((census?.windowRows ?? 2) + 1) * D.floorH;
    notes.push(`MVP-STUB: missing key window.rowPitch — H_storey = (windowRows + 1) x ${D.floorH} m = ${num(hStorey)} m`);
  }
  const crown = measured(layout, "crown.height");
  const parapetMin = (LIMITS.v7?.parapet_h ?? [0, 0])[0];
  const hCrown = crown ? (parapetMin + D.parapetMargin + D.capH) / crown : 0;
  notes.push(crown
    ? `H_crown = (parapet_h ${parapetMin} + ${D.parapetMargin} + coping ${D.capH}) m / crown.height ${crown} = ${num(hCrown)} m`
    : "H_crown = 0 (no crown.height key)");
  const H = ceilTo(Math.max(hStorey, hCrown), 0.01);
  notes.push(`H = ceil_0.01(max) = ${num(H)} m`);

  let W;
  const aspect = measured(layout, "face.aspect");
  const centres = measured(layout, "window.centreX");
  if (Number.isFinite(aspect)) {
    W = H * aspect;
    notes.push(`W = H x face.aspect ${aspect} = ${num(W)} m`);
  } else if (rowPitch && Array.isArray(centres) && centres.length >= 2) {
    const sorted = [...centres].sort((a, b) => a - b);
    const bayPitch = (sorted[sorted.length - 1] - sorted[0]) / (sorted.length - 1);
    W = (rowPitch * H) / bayPitch;
    notes.push(`no face.aspect key: square bays, W = rowPitch ${rowPitch} x H / bay pitch ${num(bayPitch)} = ${num(W)} m`);
  } else {
    W = (census?.bays ?? 2) * D.floorH;
    notes.push(`MVP-STUB: no face.aspect key and no bay pitch — W = bays x ${D.floorH} m = ${num(W)} m`);
  }
  W = Math.round(W * 1000) / 1000;
  return { W, H: Math.round(H * 100) / 100, notes };
}

/**
 * Generate the module text. Pure: every input is an argument.
 * @returns {{text:string, W:number, H:number, notes:string[], roles:string[], keys:string[], stubs:string[], staged:object}}
 */
export function generateBuildingModule({ subjectId, cls, layout, census, passes, through = "P1", importPath = "../../src/kernel/index.mjs" }) {
  const n = passIndex(through, passes);
  const { staged, keys, roles } = stageThrough({ passes, census, cls, n });
  const unsupported = roles.filter((r) => !SUPPORTED_ROLES.includes(r));
  if (unsupported.length) {
    throw new TemplateRefusal(`${passes[n].id} introduces role(s) the template does not build: ${unsupported.join(", ")} — `
      + "judgement stays with the author seat (WORKFLOW-V3 §4); template through an earlier pass");
  }
  if (!roles.includes("massing")) throw new TemplateRefusal("no massing role due — nothing to template");
  for (const r of roles) if (!cls.roles.includes(r)) throw new TemplateRefusal(`role ${r} is not in the class prior`);
  const has = (r) => roles.includes(r);
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

  const { W, H, notes } = pickFrame(layout, census);
  /** The awning lip: awning.bottom lifted by proud.drop x canopy depth / W (one calculation for the pane head and the canopy). */
  const canopyLip = () => {
    const [bottom, bottomN] = key("awning.bottom");
    const frameDrop = layout?._frame?.proudDrop;
    const drop = Number.isFinite(frameDrop) ? frameDrop : 0;
    const dropN = Number.isFinite(frameDrop) ? "layout: _frame.proudDrop" : "no _frame.proudDrop — lip unlifted";
    if (!Number.isFinite(frameDrop) && !stubs.includes("missing _frame.proudDrop")) stubs.push("missing _frame.proudDrop");
    const [depth, depthNote] = key("awning.depth");
    return { bottom, drop, depth, depthNote, note: `${bottomN}; ${dropN}` };
  };
  const L = [];
  const push = (...lines) => L.push(...lines);

  const inputHash = createHash("sha256")
    .update(JSON.stringify({ layout, census, passes: passes.slice(0, n + 1).map((p) => p.item), through: passes[n].id, roles: cls.roles }))
    .digest("hex").slice(0, 16);

  // ------------------------------------------------------------------ header
  push(
    `// GENERATED by scripts/template-building.mjs — subject ${subjectId}, through ${passes[n].id}, inputs ${inputHash}.`,
    "// Generated starting point; edits required by this pass or its LOOK failures are allowed.",
    "// Every dimension below is a layout.json fraction of W or H,",
    "// a census count, or a class default marked MVP-STUB. Palette hex are placeholders that",
    "// scripts/calibrate-palette.mjs rewrites from the target.",
    `// Roles (class prior): ${roles.join(", ")}.`,
    `// Layout keys due: ${keys.join(", ") || "none"}.`,
    `// Census due: ${Object.entries(staged).map(([k, v]) => `${k} ${v}`).join(", ") || "none"}.`,
    `import * as K from "${importPath}";`,
    "",
  );

  const zones = new Set(["brick"]);
  if (has("roof")) zones.add("roof");
  if (has("parapet") || has("cornice")) zones.add("coping");
  const openingsRoles = ["window", "storefront", "door"].filter(has);
  if (openingsRoles.length) { zones.add("frame"); zones.add("glass"); }
  if (has("sill") && has("window")) zones.add("sill");
  if (has("awning")) zones.add("awning");
  if (has("signbox")) zones.add("signbox");
  if (has("ac")) zones.add("ac");
  if (has("roof_fixture")) zones.add("fixture");   // WF-BLIND-R2 C4: the `metal` alias calibrated fixtures to the AC case
  const zoneOrder = (cls.paletteZones ?? []).map((z) => z.key);
  const paletteKeys = [...zones].sort((a, b) => zoneOrder.indexOf(a) - zoneOrder.indexOf(b));

  push(
    "export const meta = {",
    '  front: "-Z",',
    `  class: "${cls.class}",`,
    "  seed: 1,",
    "  shade: { ao: 0.08, upTint: 0.12 },",
    "  palette: {",
    ...paletteKeys.map((k) => `    ${k}: "#808080",`),
    "  },",
    "};",
    "",
    "export function build() {",
    "  // W / H rule (scripts/template-building.mjs header):",
    ...notes.map((t) => `  //   ${t}`),
    `  const W = ${num(W)}, H = ${num(H)};`,
  );
  const [depth, depthNote] = key("massing.depthOverW");
  push(`  const D = ${depth} * W;${" ".repeat(8)}// ${depthNote}`);
  const [crown, crownNote] = has("parapet") ? key("crown.height") : [null, null];
  if (has("parapet")) push(`  const crownH = ${crown} * H;${" ".repeat(3)}// ${crownNote}`);
  push(
    "  // class construction defaults (m): wall, roof slab, coping courses, seating seam",
    `  const T = ${D.wall}, slabT = ${D.slab}, capH = ${D.capH}, seam = ${D.seam};`,
    "  const parts = [];",
    "  // Contact is measured (kernel API, Contact); `seatedIn` names the host of a part seated DEEP inside it,",
    "  // and is always declared as touches + embed together.",
    "  const add = (id, solid, zone, role, seatedIn) => {",
    "    const part = { id, solid, zone, role };",
    "    if (seatedIn) { part.touches = seatedIn; part.embed = true; }",
    "    parts.push(part);",
    "  };",
    "",
  );

  // --------------------------------------------------------------- openings
  const hasOpenings = openingsRoles.length > 0;
  if (hasOpenings) {
    const [frame, frameNote] = key("frame.widthRatio");
    const [proud, proudNote] = key("frame.proud");
    push(
      `  const frame = ${frame};${" ".repeat(10)}// ${frameNote}`,
      `  const proud = ${proud};${" ".repeat(10)}// ${proudNote}`,
      "  const openings = [];",
    );
  }
  if (has("window")) {
    const rows = staged.windowRows ?? 1;
    const bays = staged.bays ?? 1;
    const count = staged.windows ?? rows * bays;
    const [pw, pwN] = key("window.w");
    const [ph, phN] = key("window.h");
    const [head, headN] = key("window.headBelowCoping");
    const [pitch, pitchN] = key("window.rowPitch");
    let [centres, centresN] = key("window.centreX");
    if (!Array.isArray(centres) || centres.length !== bays) {
      centres = Array.from({ length: bays }, (_, i) => Math.round(((i + 0.5) / bays) * 1000) / 1000);
      centresN = `MVP-STUB: window.centreX does not list ${bays} bays — evenly spaced`;
      stubs.push("window.centreX bay count");
    }
    push(
      `  const paneW = ${pw} * W;${" ".repeat(9)}// ${pwN}`,
      `  const paneH = ${ph} * H;${" ".repeat(9)}// ${phN}`,
      `  const headGap = ${head} * H;${" ".repeat(7)}// ${headN}`,
      `  const rowPitch = ${pitch} * H;${" ".repeat(6)}// ${pitchN}`,
      `  const bayX = [${centres.join(", ")}];${" ".repeat(2)}// ${centresN} (from the street-right edge, min x)`,
      `  // census: windowRows ${rows}, bays ${bays}, windows ${count}`,
    );
    if (count !== rows * bays) {
      stubs.push("windows != windowRows x bays");
      push(`  // MVP-STUB: census windows ${count} != rows x bays ${rows * bays} — first ${count} placed, top row first`);
    }
    push(
      "  {",
      "    let placed = 0;",
      `    for (let row = 0; row < ${rows}; row += 1) {`,
      "      for (const [bay, fraction] of bayX.entries()) {",
      `        if (placed >= ${count}) break;`,
      "        placed += 1;",
      '        openings.push({ id: `window_${bay}_${row}`, role: "window", x: -W / 2 + fraction * W,',
      "          y: H - headGap - row * rowPitch - frame - paneH, w: paneW, h: paneH });",
      "      }",
      "    }",
      "  }",
    );
  }
  if (has("storefront")) {
    const count = staged.storefront ?? 1;
    const [sh, shN] = key("storefront.h");
    const [sx, sxN] = key("storefront.centreX");
    const [sw, swN] = key("storefront.w");
    const [sb, sbN] = key("storefront.bottom");
    // WF-R3-B item 8 — storefront.h is the pane's EXTENT (its un-clipped columns run up behind the canopy); under an
    // awning the pane's head stops at the canopy lip, which is lifted off awning.bottom by its own projection.
    const head = has("awning") ? canopyLip() : null;
    push(`  // storefront x${count}: ${shN}; ${sxN}; ${swN}; ${sbN}`);
    if (head) {
      push(
        `  // The pane runs up behind the canopy and stops under its lip (${head.note}).`,
        `  const shopHead = (${head.bottom} + ${head.drop} * ${head.depth} / W) * H;`,
      );
    }
    // storefront.h / door.h are GLASS measurements (per-column height of the glass component), like window.h: the
    // glass is the key and the frame stands outside it (the r3 template subtracted the frame from the glass).
    const paneH = head ? `Math.min(${sh} * H, shopHead - frame - ${sb} * H)` : `${sh} * H`;
    push(
      `  for (let i = 0; i < ${count}; i += 1) {`,
      `    openings.push({ id: \`storefront_\${i}\`, role: "storefront", x: -W / 2 + (${sx} - i * ${sw + 0.05}) * W,`,
      `      y: ${sb} * H, w: ${sw} * W / ${count}, h: ${paneH} });`,
      "  }",
    );
    if (count > 1) stubs.push("storefront count > 1 spacing");
  }
  if (has("door")) {
    const count = staged.doors ?? 1;
    const [dh, dhN] = key("door.h");
    const [dx, dxN] = key("door.centreX");
    const [dw, dwN] = key("door.w");
    push(
      `  // door x${count}: ${dhN}; ${dxN}; ${dwN}`,
      `  for (let i = 0; i < ${count}; i += 1) {`,
      `    openings.push({ id: \`door_\${i}\`, role: "door", x: -W / 2 + (${dx} - i * ${dw + 0.05}) * W,`,
      `      y: frame, w: ${dw} * W, h: ${dh} * H });   // door.h is the glass height (see storefront)`,
      "  }",
    );
    if (count > 1) stubs.push("door count > 1 spacing");
  }
  if (hasOpenings) {
    push(
      "  // Through-cut tools: a seam narrower than the frame so each frame seats in the brick;",
      "  // a door tool runs a seam below the ground.",
      "  const openingTools = K.union(openings.map((o) => {",
      '    const door = o.role === "door";',
      "    return K.box([o.w + 2 * frame - 2 * seam, o.h + 2 * frame + (door ? 2 * seam : -2 * seam), T + 2 * proud])",
      "      .at([o.x, o.y - frame + (door ? -seam : seam), T / 2]);",
      "  }));",
    );
  }

  // ---------------------------------------------------------------- massing
  const coreH = has("roof") ? "H - slabT + seam" : "H";
  push(
    "",
    "  // Closed block: full-depth side walls, back wall, a solid core for bearing. The core,",
    "  // slab, parapet and roof fixtures are seated a sub-mm seam into what carries them: flush",
    "  // coplanar faces alone do not register as contact (run 4 P2 block_core fix).",
    `  const front = K.box([W - 2 * T, H, T]).at([0, 0, T / 2]);`,
    `  add("wall_front", ${hasOpenings ? "K.cut(front, openingTools)" : "front"}, "brick", "massing");`,
    '  add("wall_back", K.box([W - 2 * T, H, T]).at([0, 0, D - T / 2]), "brick", "massing");',
    '  add("wall_left", K.box([T, H, D]).at([(W - T) / 2, 0, D / 2]), "brick", "massing");',
    '  add("wall_right", K.box([T, H, D]).at([-(W - T) / 2, 0, D / 2]), "brick", "massing");',
    `  add("block_core", K.box([W - 2 * T + 2 * seam, ${coreH}, D - 2 * T + 2 * seam]).at([0, 0, D / 2]), "brick", "massing");`,
  );
  if (has("roof")) {
    push('  add("roof_slab", K.box([W - 2 * T + 2 * seam, slabT, D - 2 * T + 2 * seam]).at([0, H - slabT, D / 2]), "roof", "roof");');
  }
  if (has("parapet")) {
    push(
      "",
      "  // Perimeter parapet on the wall tops; the crown key is its top (plus the coping when built).",
      `  const parapetH = crownH${has("cornice") ? " - capH" : ""};`,
      "  const ring = K.cut(K.box([W, parapetH + seam, D]), K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]));",
      '  add("parapet", ring.at([0, H - seam, D / 2]), "coping", "parapet");',
    );
  }
  if (has("cornice")) {
    const [proj, projN] = key("cornice.projection");
    push(
      "",
      "  // Stepped coping section extruded ALONG each parapet run, bearing on the parapet top.",
      `  const cornice = ${proj};${" ".repeat(8)}// ${projN}`,
      "  const capProfile = K.profile.stepped([{ w: T, h: capH / 2 }, { w: T + cornice, h: capH / 2 }]);",
      `  const capY = H + ${has("parapet") ? "parapetH" : "0"};`,
      "  const capEnd = T + cornice / 2;",
      '  for (const [name, z] of [["front", T / 2], ["back", D - T / 2]]) {',
      "    add(`coping_${name}`, K.extrude(capProfile, W + cornice).rotY(90).at([-(W + cornice) / 2, capY, z]),",
      '      "coping", "cornice");',
      "  }",
      '  for (const [name, x] of [["left", (W - T) / 2], ["right", -(W - T) / 2]]) {',
      '    add(`coping_${name}`, K.extrude(capProfile, D - 2 * capEnd).at([x, capY, capEnd]), "coping", "cornice");',
      "  }",
    );
  }

  // ------------------------------------------------------ frames, glass, sills
  if (hasOpenings) {
    push(
      "",
      "  // Proud frame + glass `reveal` behind the frame's front face, for every opening. WF-R3-B item 8: a frame-deep",
      "  // (0.06 m) reveal hid ~2 px of every pane's head and side at the solved camera; the target's panes sit nearly",
      "  // flush in their outlines.",
      `  const reveal = ${D.glassReveal};   // class construction default (m)`,
      "  for (const o of openings) {",
      "    const surround = K.extrude(K.profile.rect({ w: o.w + 2 * frame, h: o.h + 2 * frame }), T + proud,",
      "      { holes: [K.profile.rect({ w: o.w, h: o.h }).map(([x, y]) => [x, y + frame])] }).at([o.x, o.y - frame, -proud]);",
      '    add(`${o.id}_frame`, surround, "frame", o.role);',
      "    const glassFront = -proud + reveal;",
      "    add(`${o.id}_glass`, K.box([o.w + 2 * seam, o.h + 2 * seam, T - glassFront]).at([o.x, o.y - seam, (T + glassFront) / 2]),",
      '      "glass", o.role);',
    );
    if (has("window")) {
      push(
        '    if (o.role !== "window") continue;',
        "    // Sash: MIN_FEAT deep, half seated in the near-flush glass (a sash wholly inside it is a V6 duplicate).",
        "    add(`${o.id}_sash`, K.box([o.w + 2 * seam, frame, frame]).at([o.x, o.y + (o.h - frame) / 2, glassFront]),",
        '      "frame", "window", [`${o.id}_frame`, `${o.id}_glass`]);',
      );
      if (has("sill")) {
        push(
          "    // Sill under each upper window, projecting `proud` off the brick, tail seated in it.",
          "    add(`${o.id}_sill`, K.box([o.w + 4 * frame, frame, T / 2 + proud]).at([o.x, o.y - 2 * frame, (T / 2 - proud) / 2]),",
          '      "sill", "sill", ["wall_front", `${o.id}_frame`]);',
        );
      }
    }
    push("  }");
  }

  // ------------------------------------------------- ground-floor shop bands
  if (has("awning") || has("signbox") || has("ac")) {
    push("", "  // Separate ground-floor bands: awning, then sign box + AC above it.");
  }
  if (has("awning")) {
    const lip = canopyLip();
    const [at, atN] = key("awning.top");
    const [as, asN] = key("awning.span");
    const [ax, axN] = key("awning.centreX");
    push(
      `  const canopyDepth = ${lip.depth};${" ".repeat(6)}// ${lip.depthNote} (m)`,
      `  // awning.bottom is the lowest green px, i.e. the canopy LIP seen canopyDepth proud of the face: lift the lip by`,
      "  // its projection so it lands on the band (WF-R3-B item 8; unlifted, the lip hid 0.02 H of the shop pane).",
      `  const awningBottom = (${lip.bottom} + ${lip.drop} * canopyDepth / W) * H;   // ${lip.note}`,
      `  const awningTop = ${at} * H;${" ".repeat(5)}// ${atN}`,
      `  const awningSpan = ${as} * W;${" ".repeat(4)}// ${asN}`,
      `  const awningX = -W / 2 + ${ax} * W;   // ${axN}`,
      `  const awningSeat = ${D.awningSeat};`,
      "  const awningTouches = [\"wall_front\"];",
      '  if (awningX + awningSpan / 2 > W / 2 - T) awningTouches.push("wall_left");',
      '  if (awningX - awningSpan / 2 < -(W / 2 - T)) awningTouches.push("wall_right");',
      "  add(\"shop_awning\", K.extrude(K.profile.wedge({ w: canopyDepth + awningSeat, h: awningTop - awningBottom, run: canopyDepth }), awningSpan)",
      "    .rotY(-90).at([awningX + awningSpan / 2, awningBottom, -canopyDepth]), \"awning\", \"awning\", awningTouches);",
      "  // ^ the canopy's back runs awningSeat into the brick, ~12 % of its volume — over inferredContactFrac, so the",
      "  //   seat is DECLARED (touches + embed), not left to inference (v3-proof P2 spent its repair on this).",
    );
  }
  if (has("signbox") || has("ac")) {
    const [st, stN] = key("signbox.top");
    const [sh, shN] = key("signbox.h");
    const [sx, sxN] = key("signbox.centreX");
    const [sw, swN] = key("signbox.w");
    push(
      `  const signTop = ${st} * H;${" ".repeat(7)}// ${stN}`,
      `  const signH = ${sh} * H;${" ".repeat(9)}// ${shN}`,
      `  const signX = -W / 2 + ${sx} * W;     // ${sxN}`,
      `  const signW = ${sw} * W;${" ".repeat(9)}// ${swN}`,
      `  const signD = ${D.signDepth};`,
    );
  }
  if (has("signbox")) {
    const count = staged.signbox ?? 1;
    push(
      `  for (let i = 0; i < ${count}; i += 1) {`,
      "    add(`shop_sign_${i}`, K.box([signW / " + count + ", signH, signD]).at([signX - signW / 2 + (i + 0.5) * signW / " + count + ", signTop - signH, -signD / 2]),",
      '      "signbox", "signbox");',
      "  }",
    );
  }
  if (has("ac")) {
    const count = staged.ac ?? 1;
    const [aw, awN] = key("ac.w");
    const [adp, adpN] = key("ac.depth");
    const [ah, ahN] = key("ac.h");
    const [atop, atopN] = key("ac.top");
    const [ax, axN] = key("ac.centreX");
    const onSign = has("signbox");
    push(
      `  // AC case: ${onSign ? "stands on the sign box's front face (the target's AC hangs in front of the sign), its back seated a seam into it" : "on the brick, its back seated a seam into the wall"}.`,
      `  const acW = ${aw} * W;${" ".repeat(11)}// ${awN}`,
      `  const acD = ${adp} * W;${" ".repeat(11)}// ${adpN}`,
      `  const acH = ${ah} * H;${" ".repeat(11)}// ${ahN}`,
      `  const acTop = ${atop} * H;${" ".repeat(8)}// ${atopN}`,
      `  const acX0 = -W / 2 + ${ax} * W;   // ${axN}`,
      `  const acBack = ${onSign ? "-signD + seam" : "seam"};`,
      `  const grille = ${D.grille};`,
      `  for (let i = 0; i < ${count}; i += 1) {`,
      "    const acX = acX0 + i * (acW + grille);",
      `    add(\`shop_ac_\${i}\`, K.box([acW, acH, acD]).at([acX, acTop - acH, acBack - acD / 2]), "ac", "ac");`,
      "    // Fan grille: one dark square on the front face, 0.75 of the case height, in the dark frame colour (WF-R3 H3:",
      "    // the target AC is a fan box, and a case-grey slat field read 1.52x the target's grey share).",
      "    const fan = 0.75 * acH;",
      '    add(`ac_${i}_fan`, K.box([fan, fan, grille]).at([acX, acTop - acH + (acH - fan) / 2, acBack - acD - grille / 2 + seam]), "frame", "ac");',
      "  }",
    );
    if (count > 1) stubs.push("ac count > 1 spacing");
  }

  // ---------------------------------------------------------- roof fixtures
  if (has("roof_fixture")) {
    const vents = staged.vent ?? 0;
    const pipes = staged.pipes ?? 0;
    stubs.push("missing key roof_fixture.size/position");
    const [vx, vz, vs, vh] = D.keys["roof_fixture.vent"];
    const [px, pz, pr, phh] = D.keys["roof_fixture.pipe"];
    push(
      "",
      `  // Roof fixtures: census vent ${vents}, pipes ${pipes}.`,
      "  // MVP-STUB: missing key roof_fixture.size, roof_fixture.position — class default fractions",
      "  const roofY = H - seam;",
      `  for (let i = 0; i < ${vents}; i += 1) {`,
      `    add(\`vent_\${i}\`, K.box([${vs} * W, ${vh} * H, ${vs} * W]).at([-W / 2 + (${vx} + i * ${vs + 0.05}) * W, roofY, ${vz} * D]),`,
      '      "fixture", "roof_fixture");',
      "  }",
      "  const pipe = (radius, height) => {",
      "    const section = K.profile.rect({ w: radius, h: height });",
      "    for (const point of section) point[0] += radius / 2;   // onto the non-negative radial half-plane",
      `    return K.revolve(section, ${D.pipeSegs});`,
      "  };",
      `  for (let i = 0; i < ${pipes}; i += 1) {`,
      `    add(\`pipe_\${i}\`, pipe(${pr} * W, ${phh} * H * (1 - 0.18 * (i % 2))).at([-W / 2 + ${px} * W, roofY, (${pz} - 0.13 * i) * D]),`,
      '      "fixture", "roof_fixture");',
      "  }",
    );
  }

  push("  return parts;", "}", "");
  return { text: L.join("\n"), W, H, notes, roles, keys, stubs, staged };
}

/** V5-7: +/- px (target face frame) a pane size measured straight off target px may move under FIT. */
export const PX_TOL = 2;

/** Construction numbers of the KNOBS module no layout key or gate row measures (metres). */
export const KNOBS_CONSTRUCTION = Object.freeze({
  wall: CLASS_DEFAULTS.wall, slab: CLASS_DEFAULTS.slab, capH: CLASS_DEFAULTS.capH, seam: CLASS_DEFAULTS.seam,
  reveal: CLASS_DEFAULTS.glassReveal, awningSeat: CLASS_DEFAULTS.awningSeat, grille: CLASS_DEFAULTS.grille,
  pipeSegs: CLASS_DEFAULTS.pipeSegs,
  // class starts for knobs no key measures (each knob's RANGE is classes/building.json knobPriors)
  signDepth: CLASS_DEFAULTS.signDepth, deckDepth: 1.4, ladderWidth: 0.5,
});

/**
 * WORKFLOW v4 V4-5B — the WHOLE building (P0 + P1 + P2 ironwork) as a KNOBS module (scripts/knobs.mjs): every
 * continuous size / position is one knob in metres, author frame (x centred, front face z = 0, ground y = 0); build()
 * reads only KNOBS (+ the KNOBS_CONSTRUCTION literals). A knob with a verified layout key ranges over that key's V12
 * tolerance; the rest over classes/building.json knobPriors. W / H / D START at pickFrame (the registration anchor,
 * scripts/registered.mjs anchorFace) and are fitted (V5-1 item 2: aspect fitted, scale = the frameScale similarity). The fire escape is ONE K.assemble.fireEscape call and the roof ladder one
 * K.assemble.ladder call, so V11 holds by construction. Pure: every input is an argument.
 * @returns {{text:string, W:number, H:number, D:number, knobs:object, notes:string[], stubs:string[]}}
 */
export function generateBuildingKnobsModule({ subjectId, cls, layout, census, importPath = "../../src/kernel/index.mjs" }) {
  const D0 = CLASS_DEFAULTS;
  const C = KNOBS_CONSTRUCTION;
  const stubs = [];
  const val = (name) => {
    const v = measured(layout, name);
    if (v !== null) return v;
    const why = layout?.[name]?.unverified === true ? `unverified key ${name}` : `missing key ${name}`;
    if (!stubs.includes(why)) stubs.push(why);
    return D0.keys[name];
  };
  const rows = census.windowRows ?? 1;
  const bays = census.bays ?? 1;
  const windows = census.windows ?? rows * bays;
  const levels = census.landings ?? 0;
  if (windows !== rows * bays) throw new TemplateRefusal(`census windows ${windows} != windowRows x bays ${rows * bays} — the KNOBS template builds a full grid`);
  if ((census.storefront ?? 1) !== 1 || (census.doors ?? 1) !== 1 || (census.signbox ?? 1) !== 1 || (census.ac ?? 1) !== 1) {
    throw new TemplateRefusal("the KNOBS template builds one storefront, door, sign box and AC");   // MVP-STUB
  }
  if (levels !== 2 || (census.flights ?? 1) !== 1 || (census.ladders ?? 2) !== 2 || levels > rows) {
    throw new TemplateRefusal(`census landings ${levels}, flights ${census.flights}, ladders ${census.ladders} — the KNOBS template builds 2 decks, 1 flight, a drop ladder and a roof ladder`);   // MVP-STUB
  }
  const { W, H, notes } = pickFrame(layout, census);
  const D = Math.round(val("massing.depthOverW") * W * 1e4) / 1e4;
  const priors = cls.knobPriors ?? {};
  const sizes = { W, H, m: 1 };
  const knobs = {};
  const cmt = {};
  // V5-7: a SIZE measured straight off target px (a pane's width / height) ranges +/- PX_TOL px of the face frame, not
  // the key's feature tol (+/- 17 % let FIT grow the panes 12 px past the target's)
  const frameW = layout?._frame?.W, frameH = layout?._frame?.H;
  const pxBand = (axis, v) => {
    const px = axis === "W" ? frameW : frameH;
    const size = axis === "W" ? W : H;
    return Number.isFinite(px) && px > 0 ? { min: v - (PX_TOL * size) / px, max: v + (PX_TOL * size) / px } : {};
  };
  const knob = (name, v, { key = null, toM = null, note = "", min, max, px = null } = {}) => {
    if (px) { const band = pxBand(px, v); if (band.min !== undefined) { min = band.min; max = band.max; } }
    const entry = key ? layout?.[key] : null;
    const usable = entry && typeof entry === "object" && entry.unverified !== true && (Number.isFinite(entry.value) || Array.isArray(entry.values));
    knobs[name] = usable
      ? keyedKnob({ v, key, entry, toM, min, max })
      : priorKnob({ v, prior: priors[name] ?? (key ? priors._unverifiedKey : null), sizes, min, max });
    cmt[name] = note || (usable ? key : `class prior${key ? ` (${key} ${entry?.unverified ? "unverified" : "missing"})` : ""}`);
  };
  const yH = (f) => f * H;
  const xW = (f) => -W / 2 + f * W;
  const lenW = (f) => f * W;

  // ---- massing (V5-1: fitted; starts at the registration anchor) + crown
  // V5-1 item 2: W / H / D start at pickFrame and are FITTED (aspect); absolute scale is the fitted similarity frameScale
  knob("W", W, { note: `pickFrame start: ${notes[notes.length - 1]}; fitted (aspect)` });
  knob("H", H, { note: "pickFrame start H; fitted (scale = frameScale)" });
  knob("D", D, { note: "massing.depthOverW x W start; fitted (the side return)" });
  const crownH = val("crown.height") * H;
  knob("crownH", crownH, { key: "crown.height", toM: yH, note: "crown.height: parapet + coping over the wall top" });
  knob("cornice", val("cornice.projection"), { key: "cornice.projection", toM: lenW, min: 0 });
  // ---- openings
  const frame = val("frame.widthRatio");
  knob("frame", frame, { key: "frame.widthRatio", min: 0.06 });
  knob("proud", val("frame.proud"), { key: "frame.proud", min: 0.03 });
  const winW = val("window.w") * W;
  const winH = val("window.h") * H;
  const winHead = val("window.headBelowCoping") * H;
  const rowPitch = val("window.rowPitch") * H;
  knob("winW", winW, { key: "window.w", toM: lenW, px: "W" });
  knob("winH", winH, { key: "window.h", toM: yH, px: "H" });
  knob("winHead", winHead, { key: "window.headBelowCoping", toM: yH, min: 0 });
  knob("rowPitch", rowPitch, { key: "window.rowPitch", toM: yH });
  let centres = measured(layout, "window.centreX");
  if (!Array.isArray(centres) || centres.length !== bays) {
    centres = Array.from({ length: bays }, (_, i) => (i + 0.5) / bays);
    stubs.push("window.centreX bay count");
  }
  centres.forEach((c, i) => knob(`bayX${i}`, xW(c), { key: "window.centreX", toM: xW, note: `window.centreX[${i}] (x = -W/2 + value x W)` }));
  const awningTop = val("awning.top") * H;
  const canopyDepth = val("awning.depth");
  const drop = Number.isFinite(layout?._frame?.proudDrop) ? layout._frame.proudDrop : 0;
  const awningBottom = (val("awning.bottom") + drop * canopyDepth / W) * H;
  knob("shopX", xW(val("storefront.centreX")), { key: "storefront.centreX", toM: xW });
  knob("shopW", val("storefront.w") * W, { key: "storefront.w", toM: lenW, px: "W" });
  knob("shopBottom", val("storefront.bottom") * H, { key: "storefront.bottom", toM: yH, min: 0.06 });
  knob("shopH", val("storefront.h") * H, { key: "storefront.h", toM: yH, min: 0.06, note: "storefront.h (the pane stops under the canopy lip)" });
  knob("doorX", xW(val("door.centreX")), { key: "door.centreX", toM: xW });
  knob("doorW", val("door.w") * W, { key: "door.w", toM: lenW, px: "W" });
  knob("doorH", val("door.h") * H, { key: "door.h", toM: yH, px: "H", note: "door.h (the glass; the frame stands outside it)" });
  // ---- shop bands
  knob("awningBottom", awningBottom, { key: "awning.bottom", toM: yH, note: "awning.bottom, the lip lifted by _frame.proudDrop x depth / W" });
  knob("awningTop", awningTop, { key: "awning.top", toM: yH });
  knob("awningSpan", val("awning.span") * W, { key: "awning.span", toM: lenW });
  knob("awningX", xW(val("awning.centreX")), { key: "awning.centreX", toM: xW });
  knob("canopyDepth", canopyDepth, { key: "awning.depth" });
  knob("signTop", val("signbox.top") * H, { key: "signbox.top", toM: yH });
  knob("signH", val("signbox.h") * H, { key: "signbox.h", toM: yH, min: 0.06 });
  knob("signX", xW(val("signbox.centreX")), { key: "signbox.centreX", toM: xW });
  knob("signW", val("signbox.w") * W, { key: "signbox.w", toM: lenW });
  knob("signD", C.signDepth, { note: "class prior: sign box depth" });
  knob("acW", val("ac.w") * W, { key: "ac.w", toM: lenW, min: 0.06 });
  knob("acH", val("ac.h") * H, { key: "ac.h", toM: yH, min: 0.08 });
  knob("acTop", val("ac.top") * H, { key: "ac.top", toM: yH });
  knob("acX", xW(val("ac.centreX")), { key: "ac.centreX", toM: xW });
  knob("acD", val("ac.depth") * W, { key: "ac.depth", toM: lenW, min: 0.06 });
  // ---- fire escape (K.assemble.fireEscape): deck tops hang off the window rows (landing.rowY), bottom level first
  const rowBottom = (row) => H - winHead - row * rowPitch - frame - winH - frame;
  const rowY = measured(layout, "landing.rowY") ?? -0.072;
  for (let i = 0; i < levels; i += 1) {
    const b = rowBottom(rows - 1 - i);
    knob(`feY${i}`, b + rowY * H, { key: "landing.rowY", toM: (v) => b + v * H, note: `landing.rowY: deck ${i} top = window row ${rows - 1 - i} bottom + value x H` });
  }
  knob("feX", xW(val("landing.centreX")), { key: "landing.centreX", toM: xW });
  knob("feSpan", val("landing.span") * W, { key: "landing.span", toM: lenW });
  knob("feDepth", C.deckDepth, { key: "landing.depth", toM: lenW });
  knob("dropBottom", awningTop + 0.01, { note: "class prior: drop-ladder foot, just over the awning top (V11_DROP_LADDER)" });
  // V5-7: the measured baluster pitch (plate decks, balusters on the front run and both returns)
  const balusterPitch = measured(layout, "landing.balusterPitch");
  // a member PITCH sets a COUNT: locked at the measurement (a silhouette FIT would trade the count for IoU)
  if (balusterPitch !== null) knob("feBaluster", balusterPitch * W, { key: "landing.balusterPitch", toM: lenW, min: balusterPitch * W, max: balusterPitch * W, note: "landing.balusterPitch (front-run baluster ink profile); locked" });
  // ---- roof ladder (K.assemble.ladder on the street-left side wall)
  const copingTop = H + crownH;
  knob("ladderZ", val("ladder.roof.backFromCorner") * W, { key: "ladder.roof.backFromCorner", toM: lenW, note: "ladder.roof.backFromCorner (z behind the front face)" });
  knob("ladderBottom", val("ladder.roof.bottom") * H, { key: "ladder.roof.bottom", toM: yH });
  knob("ladderTop", copingTop - val("ladder.topBelowCoping") * H, { key: "ladder.topBelowCoping", toM: (v) => copingTop - v * H, note: "ladder.topBelowCoping (coping top - value x H)" });
  knob("ladderW", C.ladderWidth, { note: "class prior: stile spacing" });
  const rungPitch = measured(layout, "ladder.roof.rungPitch");
  if (rungPitch !== null) knob("ladderRung", rungPitch * H, { key: "ladder.roof.rungPitch", toM: yH, min: rungPitch * H, max: rungPitch * H, note: "ladder.roof.rungPitch (rung ink profile between the stiles); locked" });
  // ---- roof fixtures (no key: roof fixture shapes are deferredByRuling)
  const [vx, vz, vs, vh] = D0.keys["roof_fixture.vent"];
  const [px, pz, pr, ph] = D0.keys["roof_fixture.pipe"];
  stubs.push("missing key roof_fixture.size/position");
  knob("ventX", xW(vx), { note: "MVP-STUB: class prior (no roof_fixture key)" });
  knob("ventZ", vz * D, { note: "MVP-STUB: class prior" });
  knob("ventS", vs * W, { note: "MVP-STUB: class prior" });
  knob("ventH", vh * H, { note: "MVP-STUB: class prior" });
  knob("pipeX", xW(px), { note: "MVP-STUB: class prior" });
  knob("pipeZ", pz * D, { note: "MVP-STUB: class prior" });
  knob("pipeR", pr * W, { note: "MVP-STUB: class prior" });
  knob("pipeH", ph * H, { note: "MVP-STUB: class prior" });

  const vents = census.vent ?? 0;
  const pipes = census.pipes ?? 0;
  const inputHash = createHash("sha256").update(JSON.stringify({ layout, census, roles: cls.roles, knobs: true })).digest("hex").slice(0, 16);
  const zoneOrder = (cls.paletteZones ?? []).map((z) => z.key);
  const paletteKeys = ["brick", "roof", "coping", "frame", "sill", "glass", "iron", "awning", "signbox", "ac", "fixture"]
    .sort((a, b) => zoneOrder.indexOf(a) - zoneOrder.indexOf(b));
  const text = [
    `// GENERATED by scripts/template-building.mjs --knobs — subject ${subjectId}, the whole building, inputs ${inputHash}.`,
    "// WORKFLOW v4 (research/WF-V4-PLAN.md S1 START): every continuous number is one KNOB (metres, author frame: x centred,",
    "// front face z = 0 facing -Z, ground y = 0). scripts/fit.mjs fits the unlocked ones; build() reads only KNOBS.",
    "// Palette hex are placeholders that scripts/calibrate-palette.mjs rewrites from the target.",
    `// Census: ${Object.entries(census).filter(([k]) => !k.startsWith("_")).map(([k, v]) => `${k} ${v}`).join(", ")}.`,
    `// MVP-STUB defaults: ${stubs.join("; ") || "none"}.`,
    `import * as K from "${importPath}";`,
    "",
    "// KNOBS: W / H / D start at the registration anchor (template pickFrame + massing.depthOverW) and are fitted (V5-1).",
    knobsBlock(knobs, cmt),
    "",
    "export const meta = {",
    '  front: "-Z",',
    `  class: "${cls.class}",`,
    "  seed: 1,",
    "  shade: { ao: 0.08, upTint: 0.12 },",
    "  palette: {",
    ...paletteKeys.map((k) => `    ${k}: "#808080",`),
    "  },",
    "};",
    "",
    "export function build() {",
    "  const k = Object.fromEntries(Object.entries(KNOBS).map(([name, o]) => [name, o.v]));",
    "  const { W, H, D, frame, proud } = k;",
    "  // construction (m) no key or gate row measures: wall, roof slab, coping courses, seating seam, glass reveal, awning seat, AC grille",
    `  const T = ${C.wall}, slabT = ${C.slab}, capH = ${C.capH}, seam = ${C.seam}, reveal = ${C.reveal}, awningSeat = ${C.awningSeat}, grille = ${C.grille};`,
    "  const parts = [];",
    "  // Contact is measured (kernel API, Contact); `seatedIn` names the host of a part seated DEEP inside it (touches + embed).",
    "  const add = (id, solid, zone, role, seatedIn) => {",
    "    const part = { id, solid, zone, role };",
    "    if (seatedIn) { part.touches = seatedIn; part.embed = true; }",
    "    parts.push(part);",
    "  };",
    "",
    `  // Openings: ${rows} rows x ${bays} bays of windows (head winHead under the wall top, rows rowPitch apart), the shop pane`,
    "  // (its head stops under the canopy lip) and the door.",
    "  const openings = [];",
    `  const bayX = [${centres.map((_, i) => `k.bayX${i}`).join(", ")}];`,
    `  for (let row = 0; row < ${rows}; row += 1) {`,
    "    for (const [bay, x] of bayX.entries()) {",
    '      openings.push({ id: `window_${bay}_${row}`, role: "window", x, y: H - k.winHead - row * k.rowPitch - frame - k.winH, w: k.winW, h: k.winH });',
    "    }",
    "  }",
    '  openings.push({ id: "storefront_0", role: "storefront", x: k.shopX, y: k.shopBottom, w: k.shopW, h: Math.min(k.shopH, k.awningBottom - frame - k.shopBottom) });',
    '  openings.push({ id: "door_0", role: "door", x: k.doorX, y: frame, w: k.doorW, h: k.doorH });',
    "  // Through-cut tools: a seam narrower than the frame so each frame seats in the brick; a door tool runs a seam below the ground.",
    "  const openingTools = K.union(openings.map((o) => {",
    '    const door = o.role === "door";',
    "    return K.box([o.w + 2 * frame - 2 * seam, o.h + 2 * frame + (door ? 2 * seam : -2 * seam), T + 2 * proud])",
    "      .at([o.x, o.y - frame + (door ? -seam : seam), T / 2]);",
    "  }));",
    "",
    "  // Closed block: full-depth side walls, back wall, a solid core for bearing, the roof slab, the perimeter parapet.",
    '  add("wall_front", K.cut(K.box([W - 2 * T, H, T]).at([0, 0, T / 2]), openingTools), "brick", "massing");',
    '  add("wall_back", K.box([W - 2 * T, H, T]).at([0, 0, D - T / 2]), "brick", "massing");',
    '  add("wall_left", K.box([T, H, D]).at([(W - T) / 2, 0, D / 2]), "brick", "massing");',
    '  add("wall_right", K.box([T, H, D]).at([-(W - T) / 2, 0, D / 2]), "brick", "massing");',
    '  add("block_core", K.box([W - 2 * T + 2 * seam, H - slabT + seam, D - 2 * T + 2 * seam]).at([0, 0, D / 2]), "brick", "massing");',
    '  add("roof_slab", K.box([W - 2 * T + 2 * seam, slabT, D - 2 * T + 2 * seam]).at([0, H - slabT, D / 2]), "roof", "roof");',
    "  const parapetH = k.crownH - capH;",
    "  const ring = K.cut(K.box([W, parapetH + seam, D]), K.box([W - 2 * T, parapetH * 3, D - 2 * T]).at([0, -parapetH, 0]));",
    '  add("parapet", ring.at([0, H - seam, D / 2]), "coping", "parapet");',
    "  // Stepped coping section extruded ALONG each parapet run, bearing on the parapet top.",
    "  const capProfile = K.profile.stepped([{ w: T, h: capH / 2 }, { w: T + k.cornice, h: capH / 2 }]);",
    "  const capY = H + parapetH;",
    "  const capEnd = T + k.cornice / 2;",
    '  for (const [name, z] of [["front", T / 2], ["back", D - T / 2]]) {',
    '    add(`coping_${name}`, K.extrude(capProfile, W + k.cornice).rotY(90).at([-(W + k.cornice) / 2, capY, z]), "coping", "cornice");',
    "  }",
    '  for (const [name, x] of [["left", (W - T) / 2], ["right", -(W - T) / 2]]) {',
    '    add(`coping_${name}`, K.extrude(capProfile, D - 2 * capEnd).at([x, capY, capEnd]), "coping", "cornice");',
    "  }",
    "",
    "  // Proud frame + glass `reveal` behind the frame's front face; sash and sill on every window.",
    "  for (const o of openings) {",
    "    const surround = K.extrude(K.profile.rect({ w: o.w + 2 * frame, h: o.h + 2 * frame }), T + proud,",
    "      { holes: [K.profile.rect({ w: o.w, h: o.h }).map(([x, y]) => [x, y + frame])] }).at([o.x, o.y - frame, -proud]);",
    '    add(`${o.id}_frame`, surround, "frame", o.role);',
    "    const glassFront = -proud + reveal;",
    '    add(`${o.id}_glass`, K.box([o.w + 2 * seam, o.h + 2 * seam, T - glassFront]).at([o.x, o.y - seam, (T + glassFront) / 2]), "glass", o.role);',
    '    if (o.role !== "window") continue;',
    '    add(`${o.id}_sash`, K.box([o.w + 2 * seam, frame, frame]).at([o.x, o.y + (o.h - frame) / 2, glassFront]), "frame", "window", [`${o.id}_frame`, `${o.id}_glass`]);',
    '    add(`${o.id}_sill`, K.box([o.w + 4 * frame, frame, T / 2 + proud]).at([o.x, o.y - 2 * frame, (T / 2 - proud) / 2]), "sill", "sill", ["wall_front", `${o.id}_frame`]);',
    "  }",
    "",
    "  // Ground-floor bands: the awning (its back seated awningSeat into the brick, declared), the sign box, the AC on the sign's front.",
    '  const awningTouches = ["wall_front"];',
    '  if (k.awningX + k.awningSpan / 2 > W / 2 - T) awningTouches.push("wall_left");',
    '  if (k.awningX - k.awningSpan / 2 < -(W / 2 - T)) awningTouches.push("wall_right");',
    "  add(\"shop_awning\", K.extrude(K.profile.wedge({ w: k.canopyDepth + awningSeat, h: k.awningTop - k.awningBottom, run: k.canopyDepth }), k.awningSpan)",
    '    .rotY(-90).at([k.awningX + k.awningSpan / 2, k.awningBottom, -k.canopyDepth]), "awning", "awning", awningTouches);',
    '  add("shop_sign_0", K.box([k.signW, k.signH, k.signD]).at([k.signX, k.signTop - k.signH, -k.signD / 2]), "signbox", "signbox");',
    "  const acBack = -k.signD + seam;",
    '  add("shop_ac_0", K.box([k.acW, k.acH, k.acD]).at([k.acX, k.acTop - k.acH, acBack - k.acD / 2]), "ac", "ac");',
    "  const fan = 0.75 * k.acH;   // one dark fan square on the case front (WF-R3 H3)",
    '  add("ac_0_fan", K.box([fan, fan, grille]).at([k.acX, k.acTop - k.acH + (k.acH - fan) / 2, acBack - k.acD - grille / 2 + seam]), "frame", "ac");',
    "",
    `  // Roof fixtures: census vent ${vents}, pipes ${pipes} (MVP-STUB: shapes deferredByRuling; extra instances offset from the first).`,
    "  const roofY = H - seam;",
    `  for (let i = 0; i < ${vents}; i += 1) {`,
    '    add(`vent_${i}`, K.box([k.ventS, k.ventH, k.ventS]).at([k.ventX + i * (k.ventS + 0.05 * W), roofY, k.ventZ]), "fixture", "roof_fixture");',
    "  }",
    "  const pipe = (radius, height) => {",
    "    const section = K.profile.rect({ w: radius, h: height });",
    "    for (const point of section) point[0] += radius / 2;   // onto the non-negative radial half-plane",
    `    return K.revolve(section, ${C.pipeSegs});`,
    "  };",
    `  for (let i = 0; i < ${pipes}; i += 1) {`,
    '    add(`pipe_${i}`, pipe(k.pipeR, k.pipeH * (1 - 0.18 * (i % 2))).at([k.pipeX, roofY, k.pipeZ - 0.13 * i * D]), "fixture", "roof_fixture");',
    "  }",
    "",
    "  // Ironwork: ONE fireEscape call (decks, the flight ON them, the drop ladder and its gate) and ONE roof ladder on the",
    "  // street-left side wall — V11 by construction.",
    `  parts.push(...K.assemble.fireEscape({ wall: parts, centreX: k.feX, span: k.feSpan, depth: k.feDepth, levels: [${Array.from({ length: levels }, (_, i) => `k.feY${i}`).join(", ")}],`,
    `    dropLadder: { bottom: k.dropBottom${rungPitch !== null ? ", rungPitch: k.ladderRung" : ""} }, idPrefix: "fe"${balusterPitch !== null ? ", deck: \"plate\", balusterPitch: k.feBaluster" : ""} }));`,
    "  const planes = K.assemble.wallPlanes(parts);",
    "  parts.push(...K.assemble.ladder({ face: \"side\", base: [planes.streetLeft, k.ladderBottom, k.ladderZ], height: k.ladderTop - k.ladderBottom,",
    `    width: k.ladderW, idPrefix: "roof"${rungPitch !== null ? ", rungPitch: k.ladderRung" : ""} }));`,
    "  return parts;",
    "}",
    "",
  ].join("\n");
  return { text, W, H, D, knobs, notes, stubs };
}

/** Load everything off disk for one subject and generate (`knobs: true` = the v4 KNOBS module, the whole building). */
export function generateForSubject(subjectId, { through = "P1", overrides = {}, knobs = false } = {}) {
  const S = loadSubject(subjectId);
  if (S.cls.class !== "building") throw new TemplateRefusal(`subject ${subjectId} is class ${S.cls.class}, not building`);
  const layout = { ...(S.readJson("layout") ?? {}), ...(overrides.layout ?? {}) };
  const census = overrides.census ?? S.readJson("census") ?? {};
  const moduleDir = path.dirname(S.paths.module);
  const importPath = path.relative(moduleDir, path.join(ROOT, "src", "kernel", "index.mjs")).replace(/\\/g, "/");
  const imp = importPath.startsWith(".") ? importPath : `./${importPath}`;
  if (knobs) return { S, ...generateBuildingKnobsModule({ subjectId, cls: S.cls, layout, census, importPath: imp }) };
  const passes = S.readJson("passes");
  if (!Array.isArray(passes)) throw new TemplateRefusal(`subject ${subjectId} has no passes.json`);
  return { S, ...generateBuildingModule({ subjectId, cls: S.cls, layout, census, passes, through, importPath: imp }) };
}

function main() {
  const argv = process.argv.slice(2);
  const flag = (name, fallback) => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : fallback;
  };
  const subjectId = subjectIdFromArgv(argv);
  const through = flag("through", "P1");
  const knobs = argv.includes("--knobs");
  const result = generateForSubject(subjectId, { through, knobs });
  const out = path.resolve(flag("out", path.join(ROOT, result.S.subject.outDir, "template.mjs")));
  if (path.resolve(result.S.paths.module).toLowerCase() === out.toLowerCase()) {
    throw new TemplateRefusal(`refusing to overwrite the live module ${result.S.rel.module} — pass --out elsewhere`);
  }
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, result.text);
  const sha = createHash("sha256").update(result.text).digest("hex").slice(0, 16);
  if (knobs) {
    const free = Object.values(result.knobs).filter((k) => !k.locked && k.max > k.min).length;
    console.log(`[template] ${subjectId} KNOBS module: W ${result.W} m, H ${result.H} m, D ${result.D} m; ${Object.keys(result.knobs).length} knobs (${free} free)`);
  } else console.log(`[template] ${subjectId} through ${through}: W ${result.W} m, H ${result.H} m; roles ${result.roles.join(", ")}`);
  for (const note of result.notes) console.log(`  ${note}`);
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
