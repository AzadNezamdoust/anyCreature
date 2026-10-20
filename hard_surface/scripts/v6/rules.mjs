// WORKFLOW v6 — PLACEMENT RULES for attached parts + the deterministic 3D checks the 6-view judge runs, as a CLASS-KEYED
// REGISTRY (V6-2). A class entry (registerRules(cls, entry)) carries:
//   frame        { origin: {x, y, z}: "centre" | "min" | "max" } — where the author-frame origin sits on the body (ortho.mjs)
//   groups       [{ name, re, dir?: [x,y,z] (from the part toward its host), plane?: "nose"|"tail", chain?: true }]
//   checks(parts) -> { groups: [{name, parts, float, why, backed?}], clips: [{a, b, volume}], pass, ... }
//   rows(checks)  -> ["PLACEMENT: ..." rows for the seat] (default: floats + clips)
//   symmetry?    { view, exclude: RegExp } — the view mirrored about its right-axis origin (near-side-only parts excluded)
//   axisWords?   { "+z": "forward", ... } — residual-row direction words (x is always outboard / inboard, y high / low)
// Vehicle rules live here; another class registers from scripts/v6/rules-<class>.mjs (loaded on demand by rulesFor).
//
// Vehicle: a rule names the part's anchor face, the coordinates the ortho views fix, and the range any remaining
// (free-direction) coordinate comes from — never from knob bounds. The same table drives the judge's float / clip checks:
//   float  = the part is not backed by its anchor: the probe slab just behind it (toward the anchor) must be >= BACKED
//            inside the body (bumpers: behind the back face on the nose / tail plane; lamps, stop arm: behind the part);
//            a mirror head must reach the body through its arm (solid contact chain)
//   clip   = two attached groups overlap in volume, or the stop arm lies inside the mirror's swept (fold) volume grown by
//            RULES.stopArm.mirrorClear
import * as K from "../../src/kernel/index.mjs";

export const RULES = Object.freeze({
  mirror: Object.freeze({ anchor: "flank, just behind the nose-corner chamfer", armM: Object.freeze([0.25, 0.45]),
    fixes: "head x from the front ortho, head z (ahead of the nose) from the side + top orthos, head y from front + side; arm length clamped" }),
  bumper: Object.freeze({ anchor: "nose / tail face: back face flush, the face runs down to the bumper bottom (body profile)", backedMin: 0.9 }),
  stopArm: Object.freeze({ anchor: "+x flank (folded)", mirrorClear: 0.15, fixes: "z, y from the side ortho; x = the flank" }),
  lamp: Object.freeze({ anchor: "its face (nose / tail / cap)", backedMin: 0.5 }),
});

/**
 * Mirror placement (author frame, nose +z, flank +x). headOut: head inner edge outboard of the flank (m, front ortho),
 * ahead: head centre ahead of the nose (m, side/top orthos). The arm runs from the flank (just behind the corner
 * chamfer) to the head's inner edge; its length is clamped into RULES.mirror.armM by moving the head along z (the
 * coordinate the front view cannot see).
 */
export function mirrorPlacement({ W, noseZ, chamfer, centreY, headOut, ahead, headW, headH }) {
  const [lo, hi] = RULES.mirror.armM;
  const rootZ = noseZ - chamfer - 0.04;
  let dz = noseZ + ahead - rootZ;
  const len = Math.hypot(headOut, dz);
  if (len < lo) dz = Math.sqrt(Math.max(0, lo * lo - headOut * headOut));
  if (len > hi) dz = Math.sqrt(Math.max(0, hi * hi - headOut * headOut));
  return { side: W / 2, centreY, z: rootZ + dz, head: { w: headW, h: headH, round: 0.05 }, arm: headOut, armFrom: [centreY, rootZ], armLength: Math.hypot(headOut, dz) };
}

/**
 * Stop-arm placement: z, y from the side ortho; x = the +x flank. The sign (+ rim) is seated on ONE surface: when it
 * would straddle the window band's lower edge it drops below it (the helper seats a sign on the outermost surface under
 * it, so a straddling sign floats a band's thickness off the bare flank).
 */
export function stopArmPlacement({ z, y, diameter, border, bandBottom }) {
  const r = diameter / 2 + border;
  const yc = y + r > bandBottom && y - r < bandBottom ? bandBottom - r - 0.005 : y;
  return { centre: [z, yc], diameter, border, dropped: Math.round((y - yc) * 1000) / 1000 };
}

// ---------------------------------------------------------------------------
// Checks
// ---------------------------------------------------------------------------

const BODY_ROLES = ["chassis", "body", "cab", "hood"];
/** Attached groups: id pattern, anchor direction (unit, from the part toward its host) or "chain" (mirror). */
export const GROUPS = Object.freeze([
  { name: "bumper_front", re: /^bumper_front$/, dir: [0, 0, -1], plane: "nose" },
  { name: "bumper_rear", re: /^bumper_rear$/, dir: [0, 0, 1], plane: "tail" },
  { name: "mirror_l", re: /^mirror_(head|arm)_l\d*$/, chain: true },
  { name: "mirror_r", re: /^mirror_(head|arm)_r\d*$/, chain: true },
  { name: "stopArm", re: /^stopArm_/, dir: [-1, 0, 0] },
  { name: "headlights", re: /^lamp_[lr]$/, dir: [0, 0, -1] },
  { name: "turn", re: /^turn_[lr]$/, dir: [0, 0, -1] },
  { name: "markers", re: /^marker_/, dir: [0, 0, -1] },
  { name: "rearLamps", re: /^rearLamp_[lr]$/, dir: [0, 0, 1] },
]);

const uni = (list) => (list.length === 1 ? list[0] : K.union(list));
/** Solid contact: overlapping volume, or face contact (volume after a 2 mm nudge along any axis). */
function touches(a, b) {
  if (vol(K.intersect(a, b)) > 1e-9) return true;
  const ab = a.aabb(), bb = b.aabb();
  if ([0, 1, 2].some((k) => ab.min[k] > bb.max[k] + 0.002 || bb.min[k] > ab.max[k] + 0.002)) return false;
  for (const d of [[0.002, 0, 0], [-0.002, 0, 0], [0, 0.002, 0], [0, -0.002, 0], [0, 0, 0.002], [0, 0, -0.002]]) if (vol(K.intersect(a, b.at(d))) > 1e-9) return true;
  return false;
}
const vol = (s) => { try { return s.volume(); } catch { return 0; } };
/** An axis-aligned box lo..hi (K.box: x and z centred on the origin, y from 0). */
const boxAt = (lo, hi) => K.box([hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]]).at([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]);

/**
 * Float / clip / arm-length checks of a built part list. Returns { groups: [{name, parts, backed?, float, why}],
 * clips: [{a, b, volume|gap}], mirror: {armLength, swept: {gap, clip}}, pass }.
 */
export function attachmentChecks(parts, groupsIn = GROUPS) {
  const body = parts.filter((p) => BODY_ROLES.includes(p.role) && K.isSolid(p.solid));
  const bodyU = uni(body.map((p) => p.solid));
  // nose / tail planes and flanks from the painted shell (the "cab" part; inlays such as the windshield frame stand proud)
  const shell = parts.find((p) => p.id === "cab") ?? body[0];
  const bb = shell.solid.aabb();
  const groups = [];
  for (const g of groupsIn) {
    const ps = parts.filter((p) => g.re.test(p.id));
    if (!ps.length) continue;
    const rec = { name: g.name, parts: ps.map((p) => p.id) };
    if (g.chain) {
      // every part reaches the body through solid contact (seats overlap by a seat depth)
      const reached = new Set();
      let grew = true;
      while (grew) {
        grew = false;
        for (const p of ps) {
          if (reached.has(p.id)) continue;
          const hosts = [bodyU, ...ps.filter((q) => reached.has(q.id)).map((q) => q.solid)];
          if (hosts.some((h) => touches(p.solid, h))) { reached.add(p.id); grew = true; }
        }
      }
      rec.float = reached.size < ps.length;
      rec.why = rec.float ? `not reached: ${ps.filter((p) => !reached.has(p.id)).map((p) => p.id).join(", ")}` : "chain ok";
    } else {
      const fr = [];
      for (const p of ps) {
        const a = p.solid.aabb();
        const ax = g.dir.findIndex((c) => c !== 0);
        const sgn = g.dir[ax];
        const lo = [...a.min];
        const hi = [...a.max];
        // footprint: the part's box across the two other axes, shrunk 10 % (bumpers: inside the body's flanks)
        for (let k = 0; k < 3; k += 1) {
          if (k === ax) continue;
          let l = a.min[k], h = a.max[k];
          if (g.plane) { l = Math.max(l, bb.min[k] + 0.05); h = Math.min(h, bb.max[k] - 0.05); }
          const pad = 0.1 * (h - l) / 2;
          lo[k] = l + pad; hi[k] = h - pad;
        }
        // the probe slab (1 cm, from 2 mm) just behind the part's host-ward face (bumpers: on the nose / tail plane)
        const back = g.plane ? (g.plane === "nose" ? bb.max[2] : bb.min[2]) : (sgn < 0 ? a.min[ax] : a.max[ax]);
        const inner = back + sgn * 0.002;
        const outer = back + sgn * 0.012;
        lo[ax] = Math.min(inner, outer); hi[ax] = Math.max(inner, outer);
        if (!(hi[0] > lo[0] && hi[1] > lo[1] && hi[2] > lo[2])) { fr.push(0); continue; }
        const probe = boxAt(lo, hi);
        const pv = vol(probe);
        // backing = the body + the group's other parts (a sign seated on its rim, the rim on the flank)
        const others = ps.filter((q) => q !== p).map((q) => q.solid);
        const backing = others.length ? uni([bodyU, ...others]) : bodyU;
        fr.push(pv > 0 ? vol(K.intersect(probe, backing)) / pv : 0);
      }
      rec.backed = Math.round(Math.min(...fr) * 1000) / 1000;
      const min = g.name.startsWith("bumper") ? RULES.bumper.backedMin : RULES.lamp.backedMin;
      rec.float = rec.backed < min;
      rec.why = `min backed fraction ${rec.backed} (rule >= ${min})`;
    }
    groups.push(rec);
  }
  // clips: volume overlap between different attached groups
  const clips = [];
  const solids = groups.map((g) => ({ name: g.name, s: uni(parts.filter((p) => g.parts.includes(p.id)).map((p) => p.solid)) }));
  for (let i = 0; i < solids.length; i += 1) for (let j = i + 1; j < solids.length; j += 1) {
    const v = vol(K.intersect(solids[i].s, solids[j].s));
    if (v > 1e-7) clips.push({ a: solids[i].name, b: solids[j].name, volume: Math.round(v * 1e7) / 1e7 });
  }
  // mirror swept (fold) volume vs the stop arm: the head folds about the arm root (y axis); reach = root -> far head corner
  let mirror = null;
  const head = parts.find((p) => p.id === "mirror_head_l");
  const arm = parts.find((p) => /^mirror_arm_l/.test(p.id));
  const stop = parts.filter((p) => /^stopArm_/.test(p.id));
  if (head && arm) {
    const h = head.solid.aabb();
    const am = arm.solid.aabb();
    // the arm root = its flank end (min x); its z = the arm end farther from the head centre
    const hz = (h.min[2] + h.max[2]) / 2;
    const rz = Math.abs(am.min[2] - hz) > Math.abs(am.max[2] - hz) ? am.min[2] : am.max[2];
    const root = [am.min[0], rz];
    const corners = [[h.max[0], h.min[2]], [h.max[0], h.max[2]], [h.min[0], h.min[2]], [h.min[0], h.max[2]]];
    const reach = Math.max(...corners.map(([x, z]) => Math.hypot(x - root[0], z - root[1])));
    const armLength = Math.hypot(h.min[0] - am.min[0], (h.min[2] + h.max[2]) / 2 - rz);
    mirror = { armLength: Math.round(armLength * 1000) / 1000, reach: Math.round(reach * 1000) / 1000 };
    if (stop.length) {
      const s = uni(stop.map((p) => p.solid)).aabb();
      const yOverlap = s.min[1] < h.max[1] && s.max[1] > h.min[1];
      const dx = Math.max(s.min[0] - root[0], 0, root[0] - s.max[0]);
      const dz = Math.max(s.min[2] - root[1], 0, root[1] - s.max[2]);
      const gap = Math.hypot(dx, dz) - reach;
      mirror.swept = { gap: Math.round(gap * 1000) / 1000, yOverlap, clip: yOverlap && gap < RULES.stopArm.mirrorClear };
    }
    mirror.armOk = armLength >= RULES.mirror.armM[0] - 1e-3 && armLength <= RULES.mirror.armM[1] + 1e-3;
  }
  const pass = groups.every((g) => !g.float) && clips.length === 0 && !(mirror?.swept?.clip) && (mirror ? mirror.armOk : true);
  return { groups, clips, mirror, pass };
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

const REGISTRY = new Map();
const DEFAULT_FRAME = Object.freeze({ origin: Object.freeze({ x: "centre", y: "min", z: "centre" }) });

/** Generic placement rows: every floating group and every clip. */
export function defaultRows(c) {
  const out = [];
  for (const g of c.groups ?? []) if (g.float) out.push(`PLACEMENT: ${g.name} floats (${g.why}) — seat it on its anchor face`);
  for (const k of c.clips ?? []) out.push(`PLACEMENT: ${k.a} clips ${k.b} (${k.volume} m3 overlap) — separate them`);
  return out;
}

/** Register (or replace) a class's rules. */
export function registerRules(cls, entry) {
  REGISTRY.set(cls, Object.freeze({ frame: DEFAULT_FRAME, groups: [], rows: defaultRows, symmetry: null, axisWords: {}, ...entry }));
}

/** The frame convention of a class (sync; the default origin when the class registered nothing yet). */
export const classFrame = (cls) => REGISTRY.get(cls)?.frame ?? DEFAULT_FRAME;

/**
 * The rules of a class: registered, else scripts/v6/rules-<cls>.mjs is imported (it calls registerRules), else a
 * no-rule entry (no groups, checks pass).
 */
export async function rulesFor(cls) {
  if (!REGISTRY.has(cls)) {
    try { await import(`./rules-${cls}.mjs`); } catch (error) { if (error.code !== "ERR_MODULE_NOT_FOUND") throw error; }
    if (!REGISTRY.has(cls)) registerRules(cls, { checks: () => ({ groups: [], clips: [], pass: true }) });
  }
  return REGISTRY.get(cls);
}

registerRules("vehicle", {
  frame: { origin: { x: "centre", y: "min", z: "centre" } },   // nose +z, near flank +x, y up; ground y = 0
  groups: GROUPS,
  checks: (parts) => attachmentChecks(parts, GROUPS),
  rows: (c) => {
    const out = defaultRows(c);
    const m = c.mirror;
    if (m && !m.armOk) out.push(`PLACEMENT: mirror arm ${m.armLength} m outside ${RULES.mirror.armM[0]}-${RULES.mirror.armM[1]} m — move the head along z (mirrorPlacement)`);
    if (m?.swept?.clip) out.push(`PLACEMENT: stop arm inside the mirror's fold sweep (gap ${m.swept.gap} m < ${RULES.stopArm.mirrorClear}) — move one of them`);
    return out;
  },
  symmetry: { view: "front", exclude: /^(stopArm_|door_)/ },
  axisWords: { "+z": "forward", "-z": "rearward" },
});
