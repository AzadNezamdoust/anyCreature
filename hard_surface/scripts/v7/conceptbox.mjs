// WF v10 S1 fix — the concept-camera BOX check of a direct-class (weapon) subject: the built model's projected box
// (out/blender-hs/<s>/<s>.glb vertices through camera.json + layout.measured.json `_frame.fit`, conceptreg.mjs
// conceptRegistration's map) against the concept's foreground box. Read-only.
//
//   node scripts/v7/conceptbox.mjs --subject <s>[,<s2>...] [--glb <file>] [--layout <layout.measured.json>]
//        [--fg-max <n>] [--json <file>]
//
// Rows per subject: `stored` = the fit as registered; `unrefined` = the stored fit with its `refined.frame`
// (hull.mjs --write-frame IoU refine, scale about the quad centre + tx / ty px at 1024) inverted = the plain hull bbox
// fit; `--layout` adds `layout` = another record's fit (e.g. a scratch --write-frame --frame-fit box). Each row: the
// model box [x0, y0, x1, y1] px, width / height error vs the concept box (%), centre offset (px). |err| > 2 % = flagged.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { cameraBasis } from "../registered.mjs";
import { parseArgs } from "./lib.mjs";

const r1 = (v) => Math.round(v * 10) / 10;
const r2 = (v) => Math.round(v * 100) / 100;

/** Every POSITION vertex of a .glb in world space (node TRS / matrix applied, scene roots). -> Float64Array xyz... */
export function glbVertices(file) {
  const buf = fs.readFileSync(file);
  if (buf.readUInt32LE(0) !== 0x46546c67) throw new Error(`${file}: not a glb`);
  let off = 12, json = null, bin = null;
  while (off < buf.length) {
    const len = buf.readUInt32LE(off), type = buf.readUInt32LE(off + 4);
    const chunk = buf.subarray(off + 8, off + 8 + len);
    if (type === 0x4e4f534a) json = JSON.parse(chunk.toString("utf8")); else if (type === 0x004e4942) bin = chunk;
    off += 8 + len;
  }
  const mul = (a, b) => { const o = new Array(16).fill(0); for (let c = 0; c < 4; c += 1) for (let r = 0; r < 4; r += 1) for (let k = 0; k < 4; k += 1) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k]; return o; };
  const trs = (n) => {
    if (n.matrix) return n.matrix;
    const [x, y, z, w] = n.rotation ?? [0, 0, 0, 1], [sx, sy, sz] = n.scale ?? [1, 1, 1], [tx, ty, tz] = n.translation ?? [0, 0, 0];
    return [(1 - 2 * (y * y + z * z)) * sx, 2 * (x * y + z * w) * sx, 2 * (x * z - y * w) * sx, 0,
      2 * (x * y - z * w) * sy, (1 - 2 * (x * x + z * z)) * sy, 2 * (y * z + x * w) * sy, 0,
      2 * (x * z + y * w) * sz, 2 * (y * z - x * w) * sz, (1 - 2 * (x * x + y * y)) * sz, 0, tx, ty, tz, 1];
  };
  const out = [];
  const visit = (i, M) => {
    const n = json.nodes[i], W = mul(M, trs(n));
    if (n.mesh !== undefined) for (const p of json.meshes[n.mesh].primitives) {
      const a = json.accessors[p.attributes.POSITION], bv = json.bufferViews[a.bufferView];
      const stride = bv.byteStride ?? 12, base = (bv.byteOffset ?? 0) + (a.byteOffset ?? 0);
      for (let k = 0; k < a.count; k += 1) {
        const o = base + k * stride, x = bin.readFloatLE(o), y = bin.readFloatLE(o + 4), z = bin.readFloatLE(o + 8);
        out.push(W[0] * x + W[4] * y + W[8] * z + W[12], W[1] * x + W[5] * y + W[9] * z + W[13], W[2] * x + W[6] * y + W[10] * z + W[14]);
      }
    }
    for (const c of n.children ?? []) visit(c, W);
  };
  const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  for (const r of json.scenes[json.scene ?? 0].nodes) visit(r, I);
  return Float64Array.from(out);
}

/** The concept foreground box (exclusive ends): darkest channel < fgMax (= hull.mjs foregroundBox). */
export async function conceptFgBox(file, fgMax) {
  const { data, info } = await sharp(file).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  let x0 = info.width, x1 = -1, y0 = info.height, y1 = -1;
  for (let y = 0; y < info.height; y += 1) for (let x = 0; x < info.width; x += 1) {
    const j = (y * info.width + x) * info.channels;
    if (Math.min(data[j], data[j + 1], data[j + 2]) < fgMax) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  return [x0, y0, x1 + 1, y1 + 1];
}

/** The model's px box through {s, ox, oy} on basis (direct class: turn 0). */
export function modelBox(V, basis, { s, ox, oy }) {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  const R = basis.right, U = basis.up;
  for (let i = 0; i < V.length; i += 3) {
    const X = s * (V[i] * R[0] + V[i + 1] * R[1] + V[i + 2] * R[2]) + ox, Y = -s * (V[i] * U[0] + V[i + 1] * U[1] + V[i + 2] * U[2]) + oy;
    if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y;
  }
  return [x0, y0, x1, y1];
}

/** Box agreement of a model box against the concept box: {w, h (% error), dx, dy (centre px), worst (%), off (> 2 %)}. */
export function boxAgreement(mb, cb) {
  const w = ((mb[2] - mb[0]) / (cb[2] - cb[0]) - 1) * 100, h = ((mb[3] - mb[1]) / (cb[3] - cb[1]) - 1) * 100;
  const dx = (mb[0] + mb[2]) / 2 - (cb[0] + cb[2]) / 2, dy = (mb[1] + mb[3]) / 2 - (cb[1] + cb[3]) / 2;
  // centre offset counted as a share of the box size too (34 px on a 969 px box = 3.5 %)
  const cxp = (dx / (cb[2] - cb[0])) * 100, cyp = (dy / (cb[3] - cb[1])) * 100;
  const worst = Math.max(Math.abs(w), Math.abs(h), Math.abs(cxp), Math.abs(cyp));
  return { box: mb.map(r1), w: r2(w), h: r2(h), dx: r1(dx), dy: r1(dy), cx: r2(cxp), cy: r2(cyp), worst: r2(worst), off: worst > 2 };
}

/** The stored fit with its IoU refine inverted (identity when there is none). */
export function unrefinedFit(fit, quadPx, targetW = 1024) {
  const fr = fit.refined?.frame;
  if (!fr || fit.refined.identity) return { s: fit.s, ox: fit.ox, oy: fit.oy };
  const k = targetW / 1024, { scale, tx, ty } = fr;
  const cx = quadPx.reduce((a, q) => a + q[0], 0) / 4 - tx * k, cy = quadPx.reduce((a, q) => a + q[1], 0) / 4 - ty * k;
  return { s: fit.s / scale, ox: cx + (fit.ox - tx * k - cx) / scale, oy: cy + (fit.oy - ty * k - cy) / scale };
}

export async function conceptBoxReport(subject, { glb = null, layout = null, fgMax = null } = {}) {
  const S = loadSubject(subject);
  const camera = JSON.parse(fs.readFileSync(S.paths.camera, "utf8"));
  const basis = cameraBasis(camera);
  const measured = S.readJson("layoutMeasured");
  const fr = measured._frame;
  const views = path.join(ROOT, "subjects", subject, "turnaround", "views.json");
  const fm = fgMax ?? (fs.existsSync(views) ? JSON.parse(fs.readFileSync(views, "utf8")).families?.fgMax : null) ?? 235;
  const cb = await conceptFgBox(S.paths.target, fm);
  const g = glb ?? path.join(ROOT, "out", "blender-hs", subject, `${subject}.glb`);
  const V = glbVertices(g);
  const rows = {};
  rows.stored = { fit: fr.fit, ...boxAgreement(modelBox(V, basis, fr.fit), cb) };
  if (fr.fit.refined?.dropped) {   // a hand-dropped refine (it_rail_rifle polish): the pre-drop fit, for the record
    const d = fr.fit.refined.dropped.frame, cx = fr.quadPx.reduce((a, q) => a + q[0], 0) / 4, cy = fr.quadPx.reduce((a, q) => a + q[1], 0) / 4;
    const pre = { s: fr.fit.s * d.scale, ox: cx + d.scale * (fr.fit.ox - cx) + d.tx, oy: cy + d.scale * (fr.fit.oy - cy) + d.ty };
    rows.preDrop = { fit: pre, ...boxAgreement(modelBox(V, basis, pre), cb) };
  }
  const u = unrefinedFit(fr.fit, fr.quadPx);
  rows.unrefined = { fit: u, ...boxAgreement(modelBox(V, basis, u), cb) };
  if (layout) {
    const L = JSON.parse(fs.readFileSync(layout, "utf8"))._frame.fit;
    rows.layout = { fit: L, ...boxAgreement(modelBox(V, basis, L), cb) };
  }
  // the ideal: the model's own box fitted to the concept box (s = mean of x / y px per m, centres matched)
  const m1 = modelBox(V, basis, { s: 1, ox: 0, oy: 0 });
  const sx = (cb[2] - cb[0]) / (m1[2] - m1[0]), sy = (cb[3] - cb[1]) / (m1[3] - m1[1]), s = (sx + sy) / 2;
  const ideal = { s, ox: (cb[0] + cb[2]) / 2 - (s * (m1[0] + m1[2])) / 2, oy: (cb[1] + cb[3]) / 2 - (s * (m1[1] + m1[3])) / 2 };
  rows.ideal = { fit: ideal, ...boxAgreement(modelBox(V, basis, ideal), cb), xOverY: r2(sx / sy) };
  return { subject, glb: path.relative(ROOT, g).replace(/\\/g, "/"), fgMax: fm, conceptBox: cb, rows };
}

async function main() {
  const args = parseArgs(process.argv.slice(2), ["help"]);
  if (args.help || typeof args.subject !== "string") { console.log("usage: node scripts/v7/conceptbox.mjs --subject <s>[,<s2>...] [--glb <file>] [--layout <file>] [--fg-max <n>] [--json <file>]"); return args.help ? 0 : 2; }
  const all = [];
  for (const s of args.subject.split(",").filter(Boolean)) {
    const R = await conceptBoxReport(s, { glb: typeof args.glb === "string" ? path.resolve(args.glb) : null, layout: typeof args.layout === "string" ? path.resolve(args.layout) : null, fgMax: args["fg-max"] ? Number(args["fg-max"]) : null });
    all.push(R);
    const c = R.conceptBox;
    console.log(`[box] ${s} · concept fg box ${c.join(",")} (${c[2] - c[0]} x ${c[3] - c[1]} px, fgMax ${R.fgMax}) · ${R.glb}`);
    for (const [k, r] of Object.entries(R.rows)) console.log(`[box]   ${k.padEnd(9)} s ${r.fit.s.toFixed(2)} · model box ${r.box.join(",")} · w ${r.w >= 0 ? "+" : ""}${r.w}% h ${r.h >= 0 ? "+" : ""}${r.h}% · centre ${r.dx >= 0 ? "+" : ""}${r.dx} / ${r.dy >= 0 ? "+" : ""}${r.dy} px · worst ${r.worst}%${r.off ? "  OFF > 2 %" : ""}`);
  }
  if (typeof args.json === "string") { fs.mkdirSync(path.dirname(path.resolve(args.json)), { recursive: true }); fs.writeFileSync(path.resolve(args.json), `${JSON.stringify(all, null, 2)}\n`); }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]).toLowerCase() === fileURLToPath(import.meta.url).toLowerCase()) {
  main().then((c) => { process.exitCode = c ?? 0; }).catch((e) => { console.error(`[box] ERROR ${process.env.LLMM_DEBUG ? e.stack : e.message ?? e}`); process.exitCode = 1; });
}
