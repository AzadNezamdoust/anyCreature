#!/usr/bin/env node
// WORKFLOW v6 — the MODELLER'S EYES: one sheet of a module against its subject's turnaround (any subject with
// subjects/<s>/turnaround/views.json).
//
//   node scripts/v6/view.mjs --subject <s> --module <file.mjs> [--out <dir>] [--zoom [px]]
//
// Row 1 the references (turnaround views + the concept), row 2 the module TRUE-COLOUR CEL rendered in the SAME views at
// the SAME framing (orthos: the turnaround registration with one uniform model scale sigma; concept: the solved,
// registered concept camera with the module's frame knobs), row 3 outline overlays (reference blue, model red) with the
// per-view IoU, plus the placement check lines. Writes <out>/<module>-view.png + <module>-view.json (default out
// out/v6/view-<s>/) and prints the numbers. WF v8: views.json drift rects are hatched green on the overlay and diff tiles
// and the notes add agree / drift; the JSON carries per view agree + drift, minAgree and the BLOB TABLE (metrics.blobs,
// printed as `[view] blob ...` lines last) — not the v6 loop's viewRows.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

import { ROOT, loadSubject } from "../subject.mjs";
import { foregroundMask } from "../registered.mjs";
import { CEL, driftRects, loadTurnaround, maskOptions } from "./ortho.mjs";
import { blobLine, composeRows, cropOf, driftWarnings, judge, referenceTiles, shadeRGB } from "./judge.mjs";

const PAD = 30;
const BLUE = [0, 90, 255];
const RED = [230, 0, 0];
const GREEN = [0, 150, 70];

/** Boundary px of a 0/1 mask (a fg px with a bg 4-neighbour or on the edge), dilated to 2 px. */
function outline(mask, w, h) {
  const edge = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) {
    const i = y * w + x;
    if (!mask[i]) continue;
    if (x === 0 || y === 0 || x === w - 1 || y === h - 1 || !mask[i - 1] || !mask[i + 1] || !mask[i - w] || !mask[i + w]) {
      edge[i] = 1;
      if (x + 1 < w) edge[i + 1] = 1;
      if (y + 1 < h) edge[i + w] = 1;
    }
  }
  return edge;
}

/** Overlay tile: the reference faded to 25 %, its outline blue, the model's outline red. */
function overlay(refRGB, refFg, modelFg, w, h) {
  const out = Buffer.alloc(w * h * 3);
  for (let i = 0; i < w * h * 3; i += 1) out[i] = Math.round(255 - 0.25 * (255 - refRGB[i]));
  const paint = (edge, c) => { for (let i = 0; i < w * h; i += 1) if (edge[i]) { out[i * 3] = c[0]; out[i * 3 + 1] = c[1]; out[i * 3 + 2] = c[2]; } };
  paint(outline(refFg, w, h), BLUE);
  paint(outline(modelFg, w, h), RED);
  return { rgb: out, w, h };
}

/** Diff tile: the shared silhouette = the reference faded to 35 %, reference-only px blue (missing on the model), model-only px red (extra). */
function diffTile(refRGB, refFg, modelFg, w, h) {
  const out = Buffer.alloc(w * h * 3);
  for (let i = 0; i < w * h; i += 1) {
    const c = refFg[i] && !modelFg[i] ? BLUE : !refFg[i] && modelFg[i] ? RED : null;
    for (let k = 0; k < 3; k += 1) out[i * 3 + k] = c ? c[k] : Math.round(255 - 0.35 * (255 - refRGB[i * 3 + k]));
  }
  return { rgb: out, w, h };
}

/**
 * WF v8: hatch drift rects ([x0, y0, x1, y1], image px; the tile is that image cropped at ox, oy) on an RGB tile in place:
 * a green border + 45 deg green stripes (the drift is not scored by agree). Stripe period and widths scale with the tile
 * height so they survive the sheet's downscale.
 */
function hatch(tile, rects, ox = 0, oy = 0) {
  if (!rects?.length) return tile;
  const { rgb, w, h } = tile;
  const P = Math.max(6, Math.round(h / 45));
  const S = Math.max(1, Math.round(P / 3));
  const B = Math.max(1, Math.round(h / 240));
  for (const [rx0, ry0, rx1, ry1] of rects) {
    // the tile px inside the rect (a px X is inside when x0 <= X + 0.5 < x1, as registered.mjs careMask)
    const a0 = Math.ceil(rx0 - ox - 0.5), a1 = Math.ceil(rx1 - ox - 0.5), b0 = Math.ceil(ry0 - oy - 0.5), b1 = Math.ceil(ry1 - oy - 0.5);
    for (let y = Math.max(0, b0); y < Math.min(h, b1); y += 1) {
      for (let x = Math.max(0, a0); x < Math.min(w, a1); x += 1) {
        const edge = x < a0 + B || x >= a1 - B || y < b0 + B || y >= b1 - B;
        if (!edge && (x + y) % P >= S) continue;
        const i = (y * w + x) * 3;
        rgb[i] = GREEN[0]; rgb[i + 1] = GREEN[1]; rgb[i + 2] = GREEN[2];
      }
    }
  }
  return tile;
}

const cropRGB = (rgb, W, c) => {
  const w = c.x1 - c.x0, h = c.y1 - c.y0;
  const out = Buffer.alloc(w * h * 3);
  for (let y = 0; y < h; y += 1) rgb.copy(out, y * w * 3, ((y + c.y0) * W + c.x0) * 3, ((y + c.y0) * W + c.x1) * 3);
  return out;
};
const cropMask = (m, W, c) => {
  const w = c.x1 - c.x0, h = c.y1 - c.y0;
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y += 1) for (let x = 0; x < w; x += 1) out[y * w + x] = m[(y + c.y0) * W + x + c.x0] ? 1 : 0;
  return out;
};

/**
 * zoom > 0 also writes one CRITIC PAGE per view (<module>-<view>.png, tiles zoom px high): reference, model and a filled
 * silhouette diff (blue = reference only, red = model only) — the sheet's tiles at their native resolution.
 * WF v8 WP3 (scripts/v7/step.mjs --pages): `judged` = a judge({tiles: true, blobs: true}) result of this module to draw
 * instead of judging it again; `pages` = the views (and / or "concept") whose pages to write (null = all).
 * @returns {Promise<{png:string, json:string, metrics:object, zoomed:string[]}>}
 */
export async function viewSheet({ subjectId, modulePath, outDir = null, zoom = 0, judged = null, pages = null }) {
  const S = loadSubject(subjectId);
  const { reg, table } = await loadTurnaround(subjectId);
  const { metrics, tiles, proj, parts, meta } = judged ?? await judge({ subjectId, modulePath, blobs: true });
  const ref = await referenceTiles(subjectId);
  const cols = [...reg.names, "concept"];
  // concept: the registered render (cel by face: tops 105 % unless measured, bottoms 70 %, flank / nose 100 %)
  const { data, info } = await sharp(S.paths.target).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const W = info.width, H = info.height;
  const shade = new Float32Array(W * H);
  for (let i = 0; i < W * H; i += 1) shade[i] = proj.face[i] === 0 ? CEL.top : proj.face[i] === 3 ? CEL.bottom : CEL.facing;
  const rgb = shadeRGB(parts, meta.palette, proj.partId, shade, proj.face, W, H);
  const tFg = foregroundMask({ data, w: W, h: H, c: info.channels }, table.fgMax, maskOptions(table, "concept"));
  const mFg = new Uint8Array(W * H);
  let x0 = W, y0 = H, x1 = 0, y1 = 0;
  for (let y = 0; y < H; y += 1) for (let x = 0; x < W; x += 1) {
    const i = y * W + x;
    mFg[i] = proj.partId[i] >= 0 ? 1 : 0;
    if (tFg[i] || mFg[i]) { x0 = Math.min(x0, x); x1 = Math.max(x1, x + 1); y0 = Math.min(y0, y); y1 = Math.max(y1, y + 1); }
  }
  const c = { x0: Math.max(0, x0 - PAD), x1: Math.min(W, x1 + PAD), y0: Math.max(0, y0 - PAD), y1: Math.min(H, y1 + PAD) };
  const cw = c.x1 - c.x0, ch = c.y1 - c.y0;
  const conceptRef = { rgb: cropRGB(data, W, c), w: cw, h: ch };
  const row1 = { label: `REFERENCE — ${subjectId}: turnaround ${reg.names.join(" / ")} + concept`, tiles: { ...Object.fromEntries(reg.names.map((v) => [v, ref[v]])), concept: conceptRef } };
  const row2 = { label: `MODEL — ${path.basename(modulePath)} · same views, same framing (orthos: uniform scale sigma ${metrics.sigma}; concept: registered camera)`,
    tiles: { ...Object.fromEntries(reg.names.map((v) => [v, tiles[v]])), concept: { rgb: cropRGB(rgb, W, c), w: cw, h: ch } } };
  const ovl = {};
  const masks = {};
  const crops = { concept: c };
  const drift = Object.fromEntries(cols.map((v) => [v, driftRects(table, v)]));   // WF v8: null = no rects
  for (const v of reg.names) {
    const { img } = reg.views[v];
    const cc = cropOf(reg, v);
    crops[v] = cc;
    const refFg = cropMask(img.fam, img.w, cc);
    masks[v] = { refFg, modelFg: tiles[v].fg };
    ovl[v] = hatch(overlay(ref[v].rgb, refFg, tiles[v].fg, tiles[v].w, tiles[v].h), drift[v], cc.x0, cc.y0);
  }
  masks.concept = { refFg: cropMask(tFg, W, c), modelFg: cropMask(mFg, W, c) };
  ovl.concept = hatch(overlay(conceptRef.rgb, masks.concept.refFg, masks.concept.modelFg, cw, ch), drift.concept, c.x0, c.y0);
  const anyDrift = cols.some((v) => drift[v]);
  const f3 = (x) => x.toFixed(3);
  const f3s = (x) => f3(x).replace(/^0(?=\.)/, "");
  // tile note: `IoU 0.918` (unchanged) — with drift rects `IoU .918 · agree .962 · drift 3.1 %`
  const noteOf = (v) => {
    const m = metrics.views[v];
    return drift[v] ? `IoU ${f3s(m.iou)} · agree ${f3s(m.agree)} · drift ${(m.drift * 100).toFixed(1)} %` : `IoU ${f3(m.iou)}`;
  };
  const ck = metrics.checks;
  const floats = (ck.groups ?? []).filter((g) => g.float).map((g) => g.name);
  const lines = [
    `checks: ${ck.pass ? "PASS" : "FAIL"} · float [${floats.join(", ")}] · clips ${(ck.clips ?? []).map((k) => `${k.a}x${k.b}`).join(", ") || "none"}${ck.mirror ? ` · mirror arm ${ck.mirror.armLength} m${ck.mirror.swept?.clip ? " SWEPT-CLIP" : ""}` : ""}${metrics.symmetry !== undefined ? ` · symmetry ${metrics.symmetry}` : ""} · score ${metrics.score} · tris ${metrics.tris}`,
    ...metrics.placementRows,
  ];
  const row3 = { label: `OVERLAY — reference outline blue, model outline red${anyDrift ? " · green hatch = drift (not scored by agree)" : ""}`, lines, tiles: ovl,
    notes: Object.fromEntries(cols.map((v) => [v, noteOf(v)])) };
  const dir = path.resolve(ROOT, outDir ?? path.join("out", "v6", `view-${subjectId}`));
  const base = path.basename(modulePath).replace(/\.mjs$/, "");
  const png = path.join(dir, `${base}-view.png`);
  const json = path.join(dir, `${base}-view.json`);
  await composeRows([row1, row2, row3], png, 240, cols);
  const { viewRows: _v6LoopOnly, ...shown } = metrics;   // WF v8: the family-matching rows feed the v6 loop only
  fs.writeFileSync(json, `${JSON.stringify(shown, null, 2)}\n`);
  const zoomed = [];
  for (const v of zoom > 0 ? cols.filter((c) => !pages || pages.includes(c)) : []) {
    const r = row1.tiles[v];
    const d = hatch(diffTile(r.rgb, masks[v].refFg, masks[v].modelFg, r.w, r.h), drift[v], crops[v].x0, crops[v].y0);
    const key = `blue = reference only (missing on the model), red = model only (extra) · ${noteOf(v)}`;
    const hatchKey = drift[v] ? { lines: ["green hatch = drift (views.json drift rects): not scored by agree"] } : {};
    const file = path.join(dir, `${base}-${v}.png`);
    if (r.w / r.h > 1.3) {   // wide view: reference / model / diff stacked
      await composeRows([{ label: `REFERENCE ${v}`, tiles: { [v]: r } }, { label: `MODEL ${v}`, tiles: { [v]: row2.tiles[v] } },
        { label: `DIFF ${v}: ${key}`, ...hatchKey, tiles: { [v]: d } }], file, zoom, [v]);
    } else {
      await composeRows([{ label: `${v}: reference | model | diff — ${key}`, ...hatchKey, tiles: { ref: r, model: row2.tiles[v], diff: d } }], file, zoom, ["ref", "model", "diff"]);
    }
    zoomed.push(file);
  }
  // WF v8 stdout extras: agree / drift / WARN lines (only with drift rects), then the blob table
  const agreeLines = anyDrift ? [
    `agree ${cols.map((v) => `${v} ${f3(metrics.views[v].agree)}`).join(" · ")} · min ${f3(metrics.minAgree)}`,
    `drift ${cols.filter((v) => drift[v]).map((v) => `${v} ${(metrics.views[v].drift * 100).toFixed(1)} % (${drift[v].length} rect${drift[v].length > 1 ? "s" : ""})`).join(" · ")}`,
    ...driftWarnings(metrics),
  ] : [];
  const blobLines = cols.flatMap((v) => (metrics.blobs?.[v] ?? []).map((b) => blobLine(v, b)));
  return { png, json, metrics, lines, zoomed, agreeLines, blobLines };
}

const arg = (name, fallback = null) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--") ? process.argv[i + 1] : fallback;
};

async function main() {
  const subjectId = arg("subject");
  const modulePath = arg("module");
  if (!subjectId || !modulePath) { console.error("usage: node scripts/v6/view.mjs --subject <s> --module <file.mjs> [--out <dir>] [--zoom [px]]"); return 3; }
  const zoom = process.argv.includes("--zoom") ? Number(arg("zoom", "520")) : 0;
  const { png, metrics, lines, zoomed, agreeLines, blobLines } = await viewSheet({ subjectId, modulePath, outDir: arg("out"), zoom });
  console.log(`[view] ${Object.entries(metrics.views).map(([v, m]) => `${v} ${m.iou.toFixed(3)}`).join(" · ")} · sigma ${metrics.sigma} · score ${metrics.score}`);
  for (const l of agreeLines) console.log(`[view] ${l}`);
  for (const l of lines) console.log(`[view] ${l}`);
  for (const f of [png, ...zoomed]) console.log(`[view] ${path.relative(ROOT, f).replace(/\\/g, "/")}`);
  for (const l of blobLines) console.log(`[view] ${l}`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = await main();
}
