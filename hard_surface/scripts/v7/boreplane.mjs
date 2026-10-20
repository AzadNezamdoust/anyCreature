// WF v10 S1 fix — the BORE PLANE of a direct-class (weapon) turnaround: x = 0 on the weapon's symmetry plane, not on
// the centre of the whole silhouette.
//
//   node scripts/v7/boreplane.mjs --subject <s> [--write] [--max-mm 40]
//
// Why: scripts/v6/ortho.mjs registerViews puts each view's x origin at the centre of its body-family span, and a weapon
// has ONE family (classes/weapon.json), so the span is the whole foreground. A part that sticks out of one flank only
// (facts.json `asymmetric[].protrudes`: a line drum, a belt clip, a side magazine) drags that centre toward its flank,
// and the bore plane lands at x != 0 (pistol 2-3 mm, harpoon 8, flare pistol 10, line gun 18.5 mm). classes/weapon.md
// asks x = 0 on the bore plane; a builder then either shifts the model off it or loses agree.
//
// The fix uses the registration's existing contract, views.json per-view `shift: {right | up}` (m, measured, with
// evidence; ortho.mjs registerViews moves that view's origin so what the span rule put there becomes 0): the views
// that see x (right or up = +-x: front, rear, top) are measured for their MIRROR-SYMMETRY axis (the axis c maximising
// IoU(mask, mirror_c(mask)) of the view's foreground; the bilateral body / barrel / grip outweigh a one-flank part), and
// that axis in metres becomes the view's shift. Every consumer of the registration follows without code changes: the
// judge (judge_mesh.mjs / judge.mjs: loadTurnaround), the hull and hence the concept frame (hull.mjs --write-frame),
// frame.json (dump_frame.mjs), the HS renders. dims / s are unchanged (spans are not moved, only origins).
//
// Gate: a subject is proposed for the fix only when facts.json lists a protruding asymmetric part (else the symmetry
// axis IS the bbox centre to within the measurement and nothing is written). Read-only unless --write (then views.json
// gets the shifts + `_boreplane` evidence; default every x-seeing view takes the front / rear mean, --per-view each its own; re-run hull.mjs --write-frame, dump_frame.mjs, dump_concept_cam.mjs after).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ROOT } from "../subject.mjs";
import { loadTurnaround } from "../v6/ortho.mjs";
import { parseArgs } from "./lib.mjs";

const r1 = (v) => Math.round(v * 10) / 10;
const r5 = (v) => Math.round(v * 1e5) / 1e5;

/** Mirror-symmetry axis (px, image axis "x" or "y") of a foreground mask: argmax over half-px c of IoU(M, mirror_c(M)). */
export function mirrorAxis(fg, W, H, axis) {
  // per-line runs: count pixels per (line, coord) -> for each candidate c, the overlap of each line with its mirror
  const n = axis === "x" ? W : H, m = axis === "x" ? H : W;
  const at = axis === "x" ? (line, k) => fg[line * W + k] : (line, k) => fg[k * W + line];
  let lo = n, hi = -1, total = 0;
  for (let l = 0; l < m; l += 1) for (let k = 0; k < n; k += 1) if (at(l, k)) { total += 1; if (k < lo) lo = k; if (k > hi) hi = k; }
  if (hi < 0) throw new Error("boreplane: empty view");
  const bboxC = (lo + hi + 1) / 2, reach = 0.25 * (hi + 1 - lo);
  const L = [], K = [];
  for (let l = 0; l < m; l += 1) for (let k = lo; k <= hi; k += 1) if (at(l, k)) { L.push(l); K.push(k); }
  let best = { c: bboxC, v: -1 };
  // c = mirror line in px coordinates (k + 0.5 centres): k -> 2c - 1 - k; c on half-px steps within +-25 % of the bbox
  for (let c2 = Math.ceil(2 * (bboxC - reach)); c2 <= Math.floor(2 * (bboxC + reach)); c2 += 1) {
    let I = 0;
    for (let i = 0; i < L.length; i += 1) { const k2 = c2 - 1 - K[i]; if (k2 >= 0 && k2 < n && at(L[i], k2)) I += 1; }
    const v = I / (2 * total - I);
    if (v > best.v) best = { c: c2 / 2, v };
  }
  return { c: best.c, iou: best.v, bboxC, lo, hi: hi + 1 };
}

/** The bore plane per x-seeing view: {view: {axis, sign, cPx, bboxPx, iou, xM (bore x in the bbox-centred frame), shift}}. */
export async function borePlane(subject) {
  const { reg, spec } = await loadTurnaround(subject);
  const out = {};
  for (const v of reg.names) {
    const V = reg.views[v], sp = spec.views[v];
    const rx = Math.abs(sp.right[0]) === 1 ? sp.right[0] : 0, ux = Math.abs(sp.up[0]) === 1 ? sp.up[0] : 0;
    if (!rx && !ux) continue;
    const fg = new Uint8Array(V.img.w * V.img.h);
    for (let i = 0; i < fg.length; i += 1) fg[i] = V.img.fam[i] !== 0 ? 1 : 0;
    const imgAxis = rx ? "x" : "y";
    const a = mirrorAxis(fg, V.img.w, V.img.h, imgAxis);
    // metres along the view axis of the symmetry line (registered origin, current shift included), then author x
    const k = rx ? reg.s * (V.kr ?? 1) : reg.s * (V.ku ?? 1);
    const along = rx ? (a.c - V.ox) / k : (V.oy - a.c) / k;
    const xM = along * (rx || ux);
    const old = rx ? sp.shift?.right ?? 0 : sp.shift?.up ?? 0;
    out[v] = { axis: rx ? "right" : "up", imgAxis, sign: rx || ux, along, cPx: a.c, bboxCPx: a.bboxC, offPx: r1(a.c - a.bboxC), mirrorIoU: Math.round(a.iou * 1e4) / 1e4,
      xM: r5(xM), shift: r5(old + along) };
  }
  // the bore x every view gets: the mean of the END views (front / rear: the barrel's own circle, the cleanest mirror)
  // when the set has them, else each view its own (--per-view: each view its own regardless)
  const ends = ["front", "rear"].filter((v) => out[v]);
  const shared = ends.length ? ends.reduce((a, v) => a + out[v].xM, 0) / ends.length : null;
  for (const r of Object.values(out)) {
    r.sharedXM = shared === null ? null : r5(shared);
    // the shift that puts the SHARED bore x on 0 in this view: along = x / sign (sign = the view axis' x component)
    if (shared !== null) r.sharedShift = r5(r.shift - r.along + shared * r.sign);
  }
  return { reg, spec, views: out, shared };
}

async function main() {
  const args = parseArgs(process.argv.slice(2), ["write", "help", "force", "per-view"]);
  if (args.help || typeof args.subject !== "string") { console.log("usage: node scripts/v7/boreplane.mjs --subject <s> [--write] [--per-view] [--force] [--max-mm 40]"); return args.help ? 0 : 2; }
  const s = args.subject;
  const factsFile = path.join(ROOT, "subjects", s, "turnaround", "facts.json");
  const facts = fs.existsSync(factsFile) ? JSON.parse(fs.readFileSync(factsFile, "utf8")) : {};
  const prot = (facts.asymmetric ?? []).filter((p) => p.protrudes);
  const R = await borePlane(s);
  const xs = Object.values(R.views).map((r) => r.xM);
  const mean = xs.reduce((a, b) => a + b, 0) / xs.length, spread = Math.max(...xs) - Math.min(...xs);
  console.log(`[bore] ${s} · facts.asymmetric protruding: ${prot.length ? prot.map((p) => `${p.part} (${p.flank})`).join("; ") : "none"}`);
  for (const [v, r] of Object.entries(R.views)) console.log(`[bore]   ${v.padEnd(5)} mirror axis ${r.cPx} px (bbox centre ${r.bboxCPx}, ${r.offPx >= 0 ? "+" : ""}${r.offPx} px) · mirror IoU ${r.mirrorIoU} · bore x ${(r.xM * 1000).toFixed(1)} mm · shift.${r.axis} ${r.shift}`);
  console.log(`[bore]   bore plane x ${(mean * 1000).toFixed(1)} mm in the bbox-centred frame (views spread ${(spread * 1000).toFixed(1)} mm)${R.shared !== null ? ` · shared (front / rear mean) ${(R.shared * 1000).toFixed(1)} mm` : ""}`);
  const maxMm = Number(args["max-mm"] ?? 40);
  if (!args.write) { console.log("[bore] read-only (--write puts the shifts into views.json)"); return 0; }
  if (!prot.length && !args.force) { console.log("[bore] facts.json lists no protruding asymmetric part: nothing written (--force to write anyway)"); return 0; }
  if (Math.abs(mean) * 1000 > maxMm || spread * 1000 > 6) { console.error(`[bore] REFUSED: |bore x| ${(mean * 1000).toFixed(1)} mm > ${maxMm} or views spread ${(spread * 1000).toFixed(1)} mm > 6 mm — check the views by eye`); return 1; }
  const file = path.join(ROOT, "subjects", s, "turnaround", "views.json");
  const spec = JSON.parse(fs.readFileSync(file, "utf8"));
  const perView = !!args["per-view"] || R.shared === null;
  const pick = (r) => (perView ? r.shift : r.sharedShift);
  for (const [v, r] of Object.entries(R.views)) spec.views[v].shift = { ...(spec.views[v].shift ?? {}), [r.axis]: pick(r) };
  spec._boreplane = { at: new Date().toISOString().slice(0, 10), by: "scripts/v7/boreplane.mjs --write",
    why: `x = 0 on the bore plane (classes/weapon.md): the views' x origin moved from the silhouette bbox centre to its mirror-symmetry axis (protruding one-flank parts: ${prot.map((p) => p.part).join("; ") || "forced"})`,
    mode: perView ? "per-view (each view its own mirror axis)" : "shared (the mean of the front / rear mirror axes, every x-seeing view)",
    boreXmm: r1((perView ? mean : R.shared) * 1000), views: Object.fromEntries(Object.entries(R.views).map(([v, r]) => [v, { mirrorAxisPx: r.cPx, bboxCentrePx: r.bboxCPx, mirrorIoU: r.mirrorIoU, ownBoreXmm: r1(r.xM * 1000), [`shift.${r.axis}`]: pick(r) }])) };
  fs.writeFileSync(file, `${JSON.stringify(spec, null, 2)}\n`);
  console.log(`[bore] wrote ${path.relative(ROOT, file)} shifts · NEXT: node scripts/v7/hull.mjs --subject ${s} --write-frame --frame-refine off; node scripts/hs/dump_frame.mjs --subject ${s}; node scripts/hs/dump_concept_cam.mjs --subject ${s}`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) {
  main().then((c) => { process.exitCode = c ?? 0; }).catch((e) => { console.error(`[bore] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 1; });
}
