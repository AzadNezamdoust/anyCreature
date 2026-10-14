// WF v10 — the concept camera of a DIRECT-class subject (weapon), solved from the installed turnaround's visual hull.
//
//   node scripts/v7/solve-camera-hull.mjs --subject <s> [--dry] [--views-dir <dir>]
//
// A handheld object has no ground quad, so scripts/solve-camera.mjs (two ground-edge slopes) has nothing to measure and
// `gold.mjs new --class weapon` writes the style's fixed isometric (30 deg elevation, 45 deg azimuth) as camera.json. The
// image generator does not hold those angles (assault_rifle: the barrel runs at 18.6 deg on screen, the fixed isometric
// says 26.6 deg), so after `turnaround.mjs install` the two angles are fitted: the visual hull of the registered views
// (hull.mjs buildHull) is splatted through an orthographic camera (elevation theta, azimuth phi, no roll: vertical edges
// stay vertical, as every style text demands), scale / offset from its bbox on the concept's foreground bbox, and the
// (theta, phi) with the best silhouette IoU against the concept target wins — coarse 5 deg grid, then 1 deg, then 0.25.
// Writes subjects/<s>/camera.json (the fixed isometric's IoU kept in it for comparison). Then: hull.mjs --write-frame.
// Refused for a class registered.mjs solves itself (vehicle / building: scripts/solve-camera.mjs).
//
//   node scripts/v7/solve-camera-hull.mjs --subject <s> --from-parts --boxes <passN_parts.json | passN_stats.json> [--write]
//
// --from-parts (research/PRECISION-VEHICLE-VS-DIRECT.md step 5): fit theta / phi / scale / offset on PART CENTRES
// instead of the hull silhouette (an item's hull IoU landscape is flat: it_thumper 0.67-0.72 over theta 10..55): each
// subjects/<s>/parts.json part with a hero_rect gives its rect centre (hero px); the build's object(s) it matches give
// the author-metre bbox centre (part_boxes.py output of a block-out: run_pass.py --dump-part-boxes). Per (theta, phi)
// on a 1 deg grid (then 0.1 deg) scale / offset are the linear least-squares fit; the smallest RMS px residual wins.
// Needs >= 4 parts. Prints the fit and the per-part residuals; writes camera.json (method parts, the old record under
// `previous`) only with --write — the camera is critical lane, the orchestrator decides. Known bias: the hero is a
// perspective image and a rect centre is the VISIBLE extent's centre (a part half hidden shifts it).
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ROOT, loadSubject } from "../subject.mjs";
import { FG_MAX, SUBJECT, cameraBasis, iou, readRGB, targetState } from "../registered.mjs";
import { maskOptions } from "../v6/ortho.mjs";
import { buildHull, cameraExtent, frameQuad, hullPoints, loadViewSet, splatHull } from "./hull.mjs";
import { FIXED_ISO, isDirectClass } from "./conceptreg.mjs";
import { conceptTarget, parseArgs } from "./lib.mjs";

const r3 = (v) => Math.round(v * 1e3) / 1e3;

/** Fit (theta, phi) of the concept camera to the hull. -> {theta_deg, phi_deg, iou, fixed: {…, iou}, evals} */
export async function solveCameraHull(subject, { viewsDir = null } = {}) {
  const S = loadSubject(subject);
  if (!isDirectClass(S)) throw new Error(`solve-camera-hull: ${subject} is class ${S.klass} — its camera is solved by scripts/solve-camera.mjs (ground edges)`);
  const set = await loadViewSet(subject, { viewsDir });
  const hull = buildHull(set.reg, { res: 0.03 });
  const P = hullPoints(hull, "fine");
  const stride = Math.max(1, Math.floor(P.n / 20000));
  const pts = [];
  for (let i = 0; i < P.n; i += stride) pts.push([P.x[i], P.y[i], P.z[i]]);
  // Before install the live view files do not exist. Use the candidate's table
  // for the same concept mask instead of conceptTarget loading live images.
  const { img, T } = viewsDir ? await (async () => {
    const img = await readRGB(S.paths.target);
    return { img, T: targetState(S, img, set.table.fgMax ?? FG_MAX, maskOptions(set.table, "concept")) };
  })() : await conceptTarget(subject);
  const W = img.w, H = img.h;
  let x0 = W, x1 = -1, y0 = H, y1 = -1;
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) if (T[y * W + x] === SUBJECT) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  if (x1 < 0) throw new Error("solve-camera-hull: the concept has no foreground");
  const bbox = [x0, y0, x1 + 1, y1 + 1];
  const id = (p) => p;
  let evals = 0;
  const score = (theta, phi) => {
    evals += 1;
    const basis = cameraBasis({ theta_deg: theta, phi_deg: phi });
    const fit = frameQuad({ ext: cameraExtent(pts, basis, id, [P.step / 2, P.step / 2]), bbox, corners: [], basis, turn: id });
    const map = { ax: basis.right.map((c) => fit.s * c), bx: fit.ox, ay: basis.up.map((c) => -fit.s * c), by: fit.oy };
    return iou(T, splatHull(hull, map, W, H));
  };
  let best = { theta: FIXED_ISO.theta_deg, phi: FIXED_ISO.phi_deg, v: score(FIXED_ISO.theta_deg, FIXED_ISO.phi_deg) };
  const fixed = { ...FIXED_ISO, iou: r3(best.v) };
  const scan = (ts, ps) => { for (const t of ts) for (const p of ps) { const v = score(t, p); if (v > best.v + 1e-9) best = { theta: t, phi: p, v }; } };
  const range = (a, b, d) => Array.from({ length: Math.round((b - a) / d) + 1 }, (_, i) => a + i * d);
  scan(range(5, 55, 5), range(10, 80, 5));
  scan(range(Math.max(2, best.theta - 4), best.theta + 4, 1), range(Math.max(5, best.phi - 4), best.phi + 4, 1));
  scan(range(best.theta - 0.75, best.theta + 0.75, 0.25), range(best.phi - 0.75, best.phi + 0.75, 0.25));
  return { S, theta_deg: best.theta, phi_deg: best.phi, iou: r3(best.v), fixed, evals, set: set.set, points: P.n };
}

/** --from-parts: [{id, hero:[x,y], p:[x,y,z]}] -> best {theta, phi, s, ox, oy, rms, res[]} (orthographic, no roll). */
export function solveFromParts(pairs) {
  if (pairs.length < 4) throw new Error(`--from-parts needs >= 4 matched parts with a hero_rect (got ${pairs.length})`);
  const fit = (theta, phi) => {
    const B = cameraBasis({ theta_deg: theta, phi_deg: phi });
    // px = s a + ox, py = s b + oy with a = p.R, b = -p.U: least squares in (s, ox, oy)
    const n = pairs.length;
    let sa = 0, sb = 0, saa = 0, sx = 0, sy = 0, sax = 0, sby = 0;
    const ab = pairs.map(({ p }) => [p[0] * B.right[0] + p[1] * B.right[1] + p[2] * B.right[2], -(p[0] * B.up[0] + p[1] * B.up[1] + p[2] * B.up[2])]);
    pairs.forEach(({ hero }, i) => { const [a, b] = ab[i]; sa += a; sb += b; saa += a * a + b * b; sx += hero[0]; sy += hero[1]; sax += a * hero[0]; sby += b * hero[1]; });
    const s = (sax + sby - (sa * sx + sb * sy) / n) / (saa - (sa * sa + sb * sb) / n);
    const ox = (sx - s * sa) / n, oy = (sy - s * sb) / n;
    const res = pairs.map(({ id, hero }, i) => ({ id, dx: s * ab[i][0] + ox - hero[0], dy: s * ab[i][1] + oy - hero[1] }));
    const rms = Math.sqrt(res.reduce((q, r) => q + r.dx * r.dx + r.dy * r.dy, 0) / n);
    return { theta, phi, s, ox, oy, rms, res };
  };
  let best = null;
  for (let th = 0; th <= 70; th += 1) for (let ph = -90; ph <= 90; ph += 1) { const f = fit(th, ph); if (!best || f.rms < best.rms) best = f; }
  const c = best;
  for (let th = c.theta - 1; th <= c.theta + 1 + 1e-9; th += 0.1) for (let ph = c.phi - 1; ph <= c.phi + 1 + 1e-9; ph += 0.1) { const f = fit(+th.toFixed(2), +ph.toFixed(2)); if (f.rms < best.rms) best = f; }
  return best;
}

async function fromParts(args) {
  const s = args.subject;
  const S = loadSubject(s);
  const spec = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects", s, "parts.json"), "utf8"));
  if (typeof args.boxes !== "string") throw new Error("--from-parts needs --boxes <passN_parts.json | passN_stats.json> (run_pass.py --dump-part-boxes on the block-out)");
  const raw = JSON.parse(fs.readFileSync(path.resolve(args.boxes), "utf8"));
  const boxes = raw.parts?.parts ? raw.parts : raw;
  const objs = Object.entries(boxes.parts ?? {});
  const pairs = [];
  for (const P of spec.parts ?? []) {
    if (!P.hero_rect) continue;
    const re = new RegExp(P.match);
    let hit = objs.filter(([n]) => re.test(n));
    if (!hit.length) hit = objs.filter(([, p]) => re.test(String(p.role ?? "")));
    if (!hit.length) continue;
    const lo = [0, 1, 2].map((k) => Math.min(...hit.map(([, p]) => p.author.min[k]))), hi = [0, 1, 2].map((k) => Math.max(...hit.map(([, p]) => p.author.max[k])));
    pairs.push({ id: P.id, hero: [(P.hero_rect[0] + P.hero_rect[2]) / 2, (P.hero_rect[1] + P.hero_rect[3]) / 2], p: lo.map((v, k) => (v + hi[k]) / 2) });
  }
  const b = solveFromParts(pairs);
  const old = fs.existsSync(S.paths.camera) ? JSON.parse(fs.readFileSync(S.paths.camera, "utf8")) : null;
  console.log(`[camera] ${s} --from-parts: theta ${b.theta.toFixed(1)} deg, phi ${b.phi.toFixed(1)} deg, s ${b.s.toFixed(1)} px/m · RMS ${b.rms.toFixed(1)} px over ${pairs.length} part centres${old ? ` (camera.json now: theta ${old.theta_deg}, phi ${old.phi_deg})` : ""}`);
  for (const r of b.res) console.log(`[camera]   ${r.id.padEnd(16)} dx ${r.dx.toFixed(1).padStart(6)}  dy ${r.dy.toFixed(1).padStart(6)} px`);
  if (!args.write) { console.log("[camera] nothing written (--write writes camera.json with method parts)"); return 0; }
  const rec = {
    theta_deg: +b.theta.toFixed(2), phi_deg: +b.phi.toFixed(2), slopes: null, residual_px: +b.rms.toFixed(2), vertical_tilt_deg: null,
    source: S.rel.target, sha256: crypto.createHash("sha256").update(fs.readFileSync(S.paths.target)).digest("hex"),
    solved: new Date().toISOString(), provisional: false,
    method: `parts: fitted on ${pairs.length} part centres (subjects/${s}/parts.json hero_rect centres vs ${path.relative(ROOT, path.resolve(args.boxes)).split(path.sep).join("/")} author bbox centres; scripts/v7/solve-camera-hull.mjs --from-parts), orthographic, no roll, RMS ${b.rms.toFixed(1)} px`,
    iou: null, ...(old?.fixedIsometric ? { fixedIsometric: old.fixedIsometric } : {}), ...(old ? { previous: old } : {}),
  };
  fs.writeFileSync(S.paths.camera, `${JSON.stringify(rec, null, 2)}
`);
  console.log(`[camera] wrote ${S.rel.camera} · NEXT: node scripts/v7/hull.mjs --subject ${s} --write-frame; node scripts/hs/dump_concept_cam.mjs --subject ${s}`);
  return 0;
}

async function main() {
  const args = parseArgs(process.argv.slice(2), ["dry", "help", "from-parts", "write"]);
  if (args["from-parts"] && typeof args.subject === "string") return fromParts(args);
  if (args.help || typeof args.subject !== "string") { console.log("usage: node scripts/v7/solve-camera-hull.mjs --subject <s> [--dry] [--views-dir <dir>]"); return args.help ? 0 : 2; }
  const s = args.subject;
  const r = await solveCameraHull(s, { viewsDir: typeof args["views-dir"] === "string" ? path.resolve(args["views-dir"]) : null });
  const { S } = r;
  console.log(`[camera] ${s}: theta ${r.theta_deg} deg, phi ${r.phi_deg} deg · hull silhouette IoU ${r.iou} (fixed isometric ${r.fixed.theta_deg} / ${r.fixed.phi_deg}: ${r.fixed.iou}) · ${r.evals} evals · ${r.points} hull points`);
  if (args.dry) { console.log("[camera] --dry: nothing written"); return 0; }
  const rec = {
    theta_deg: r.theta_deg, phi_deg: r.phi_deg, slopes: null, residual_px: null, vertical_tilt_deg: null,
    source: S.rel.target, sha256: crypto.createHash("sha256").update(fs.readFileSync(S.paths.target)).digest("hex"),
    solved: new Date().toISOString(), provisional: false,
    method: "hull silhouette fit (scripts/v7/solve-camera-hull.mjs, WF v10): the registered turnaround's visual hull through an orthographic camera without roll, scale / offset from the bbox, best IoU against the concept target",
    iou: r.iou, fixedIsometric: r.fixed,
  };
  fs.writeFileSync(S.paths.camera, `${JSON.stringify(rec, null, 2)}\n`);
  console.log(`[camera] wrote ${S.rel.camera} · NEXT: node scripts/v7/hull.mjs --subject ${s} --write-frame`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) {
  main().then((c) => { process.exitCode = c ?? 0; }).catch((e) => { console.error(`[camera] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 1; });
}
void ROOT;
