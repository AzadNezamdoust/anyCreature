#!/usr/bin/env node
// normalize-views.mjs — put a generated orthographic turnaround (four single-view images, or one sheet) on the canvas
// rule of the live sets (subjects/<s>/turnaround/README.md): each view scaled UNIFORMLY onto a white C x C canvas
// (C = 1024) — side: its foreground bbox length = L px (800 in the forklift / icecream_van READMEs); front / rear: bbox
// height = the normalised side's bbox height; top: bbox length = the side's L — bbox centre on the canvas centre.
//
//   node scripts/v7/normalize-views.mjs (--in <dir> | --sheet <png> [--layout 2x2] [--order side,front,rear,top])
//        --out <dir> [--like <live turnaround dir>] [--side-l <px>] [--canvas <px>] [--fg-max 235]
//        [--mirror <view,...>] [--bg-clean <t>|off] [--min-blob 30] [--margin 3] [--keep-main <px>] [--keep-rules]
//
// --in <dir>      side.png, front.png, rear.png, top.png (one raw view each; a missing file is skipped with a note).
// --sheet <png>   one image holding every view; split on its white gutters: the (rows - 1) longest empty row runs
//                 inside the foreground split the rows, then in each row band the (cols - 1) longest empty column runs
//                 split the columns. Panels are read row-major and named by --order (default side,front,rear,top
//                 = the 2 x 2 sheet: side top-left, front top-right, rear bottom-left, top bottom-right). Ruling
//                 lines (panel dividers / a frame drawn despite the prompt: thin lines running edge to edge) are painted
//                 white first and listed in the report; --keep-rules skips that.
//                 No gutter found (a drawing crosses it: rotor blades): each connected drawing goes to the quarter
//                 holding its centroid, the other quarters' drawings painted white in each panel (splitQuadrants; noted).
// --like <dir>    match a live set: L = the bbox length of its side view (views.json views.side.file, else side.png)
//                 measured with the same foreground rule, C = that image's width; its views.json families.fgMax raises
//                 the --bg-clean default (below). Live sides measure tractor 789, school_bus 848 (side_right.png), fire_truck 895,
//                 forklift / icecream_van 800 px. Without --like: --side-l (default 800) and --canvas (default 1024).
// --mirror        horizontally mirror these views before measuring (an orientation fix: a pure mirror of a view;
//                 the caller decides that it is one and records why; rotations are never corrected here).
// Foreground = darkest channel < --fg-max (default 235 = scripts/v6/ortho.mjs FG_MAX); the bbox ignores connected
// foreground blobs smaller than --min-blob px (specks); --keep-main <px> keeps only the largest blob cluster after a
// <px> dilation (drops stray marks such as text far from the drawing) — off by default, report it when used.
// Each view is cropped at its bbox + --margin px (keeps the outline anti-aliasing), resampled (lanczos3), pasted, then
// re-measured and re-scaled until its bbox hits the target (<= 4 passes) and re-centred. --bg-clean <t>: pixels with the
// darkest channel >= t connected to the canvas border become pure white (page noise off the canvas; default 240, or the
// live views.json fgMax - 2 when that is higher, so near-white paint such as the fire_truck stripe keeps its value).
// Writes <out>/{side,front,rear,top}.png + <out>/normalize.json (inputs + sha256, panels, per view: raw bbox, mirror,
// scale, output bbox, notes); with --like, a view the live views.json names differently (school_bus side_right.png) is
// also written under that name (same bytes), so a tool reading the live file names from <out> finds it.
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

export const VIEW_NAMES = ["side", "front", "rear", "top"];
export const FG_MAX_DEFAULT = 235;

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (!a.startsWith("--")) { out._.push(a); continue; }
    const name = a.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) out[name] = true;
    else { out[name] = next; i += 1; }
  }
  return out;
}

const sha256 = (file) => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");

/** file -> { data (RGB, alpha flattened on white), width, height } */
export async function readRGB(file) {
  const { data, info } = await sharp(file).flatten({ background: "#ffffff" }).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  return { data, width: info.width, height: info.height };
}

/** Foreground mask: darkest channel < fgMax. */
export function fgMask(img, fgMax) {
  const { data, width, height } = img;
  const m = new Uint8Array(width * height);
  for (let i = 0, p = 0; i < m.length; i += 1, p += 3) {
    const lo = Math.min(data[p], data[p + 1], data[p + 2]);
    if (lo < fgMax) m[i] = 1;
  }
  return m;
}

/** 8-connected components of a mask: { labels (Int32Array, 0 = none), sizes: [0, n1, n2, ...] }. */
export function components(mask, width, height) {
  const labels = new Int32Array(width * height);
  const sizes = [0];
  const stack = new Int32Array(width * height);
  let next = 0;
  for (let start = 0; start < mask.length; start += 1) {
    if (!mask[start] || labels[start]) continue;
    next += 1;
    let top = 0; stack[top++] = start; labels[start] = next; let n = 0;
    while (top) {
      const i = stack[--top]; n += 1;
      const x = i % width; const y = (i - x) / width;
      for (let dy = -1; dy <= 1; dy += 1) {
        const yy = y + dy; if (yy < 0 || yy >= height) continue;
        for (let dx = -1; dx <= 1; dx += 1) {
          const xx = x + dx; if (xx < 0 || xx >= width) continue;
          const j = yy * width + xx;
          if (mask[j] && !labels[j]) { labels[j] = next; stack[top++] = j; }
        }
      }
    }
    sizes.push(n);
  }
  return { labels, sizes };
}

/** Square dilation of a mask by r px (separable max). */
function dilate(mask, width, height, r) {
  const tmp = new Uint8Array(mask.length);
  const out = new Uint8Array(mask.length);
  for (let y = 0; y < height; y += 1) {
    // forward then backward pass: within r px of the nearest set px on this row
    let prev = -Infinity;
    for (let x = 0; x < width; x += 1) { if (mask[y * width + x]) prev = x; if (x - prev <= r) tmp[y * width + x] = 1; }
    prev = Infinity;
    for (let x = width - 1; x >= 0; x -= 1) { if (mask[y * width + x]) prev = x; if (prev - x <= r) tmp[y * width + x] = 1; }
  }
  for (let x = 0; x < width; x += 1) {
    let prev = -Infinity;
    for (let y = 0; y < height; y += 1) { if (tmp[y * width + x]) prev = y; if (y - prev <= r) out[y * width + x] = 1; }
    prev = Infinity;
    for (let y = height - 1; y >= 0; y -= 1) { if (tmp[y * width + x]) prev = y; if (prev - y <= r) out[y * width + x] = 1; }
  }
  return out;
}

/**
 * The drawing's mask for bbox purposes: foreground minus blobs < minBlob px; with keepMain, only the blob cluster that
 * is largest after a keepMain-px dilation. -> { mask, dropped: {blobs, px} }
 */
export function drawingMask(img, { fgMax = FG_MAX_DEFAULT, minBlob = 30, keepMain = 0 } = {}) {
  const { width, height } = img;
  const fg = fgMask(img, fgMax);
  const { labels, sizes } = components(fg, width, height);
  const mask = new Uint8Array(fg.length);
  let droppedBlobs = 0; let droppedPx = 0;
  for (let i = 0; i < fg.length; i += 1) {
    if (!fg[i]) continue;
    if (sizes[labels[i]] >= minBlob) mask[i] = 1; else droppedPx += 1;
  }
  for (let k = 1; k < sizes.length; k += 1) if (sizes[k] < minBlob) droppedBlobs += 1;
  if (keepMain > 0) {
    const d = dilate(mask, width, height, keepMain);
    const cc = components(d, width, height);
    let best = 0; let bestN = 0;
    const count = new Array(cc.sizes.length).fill(0);
    for (let i = 0; i < mask.length; i += 1) if (mask[i]) count[cc.labels[i]] += 1;
    for (let k = 1; k < count.length; k += 1) if (count[k] > bestN) { bestN = count[k]; best = k; }
    for (let i = 0; i < mask.length; i += 1) {
      if (mask[i] && cc.labels[i] !== best) { mask[i] = 0; droppedPx += 1; }
    }
    droppedBlobs += Math.max(0, count.filter((n, k) => k > 0 && n > 0).length - 1);
  }
  return { mask, dropped: { blobs: droppedBlobs, px: droppedPx } };
}

/** bbox of a mask: {x0, y0, x1, y1, w, h, cx, cy} (inclusive px) or null. */
export function bboxOf(mask, width, height) {
  let x0 = width; let y0 = height; let x1 = -1; let y1 = -1;
  for (let y = 0; y < height; y += 1) {
    const row = y * width;
    for (let x = 0; x < width; x += 1) {
      if (!mask[row + x]) continue;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
  }
  if (x1 < 0) return null;
  return { x0, y0, x1, y1, w: x1 - x0 + 1, h: y1 - y0 + 1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
}

/** Empty runs [a, b] (inclusive) of a 0/1 occupancy profile strictly inside its first..last occupied index. */
export function innerGaps(occ) {
  let first = -1; let last = -1;
  for (let i = 0; i < occ.length; i += 1) if (occ[i]) { if (first < 0) first = i; last = i; }
  const gaps = [];
  if (first < 0) return { first, last, gaps };
  let start = -1;
  for (let i = first; i <= last; i += 1) {
    if (!occ[i]) { if (start < 0) start = i; } else if (start >= 0) { gaps.push([start, i - 1]); start = -1; }
  }
  return { first, last, gaps };
}

/** Split positions: the (parts - 1) longest inner gaps, as cut indices (gap centres), sorted. */
export function splitCuts(occ, parts) {
  const { first, last, gaps } = innerGaps(occ);
  if (parts <= 1) return { first, last, cuts: [], gaps: [] };
  const chosen = [...gaps].sort((a, b) => (b[1] - b[0]) - (a[1] - a[0]) || a[0] - b[0]).slice(0, parts - 1);
  if (chosen.length < parts - 1) throw new Error(`found ${gaps.length} white gutter(s), need ${parts - 1}`);
  chosen.sort((a, b) => a[0] - b[0]);
  return { first, last, cuts: chosen.map(([a, b]) => Math.floor((a + b) / 2)), gaps: chosen };
}

/** Longest foreground run of a line of 0/1 values, bridging gaps <= gap px -> [start, end] or null. */
function longestRun(get, n, gap = 2) {
  let best = null; let start = -1; let last = -2;
  for (let i = 0; i < n; i += 1) {
    if (!get(i)) continue;
    if (start < 0 || i - last - 1 > gap) start = i;
    last = i;
    if (!best || i - start > best[1] - best[0]) best = [start, i];
  }
  return best;
}

/** Group sorted indices into consecutive [a, b] ranges. */
function ranges(idx) {
  const out = [];
  for (const i of idx) {
    if (out.length && i === out[out.length - 1][1] + 1) out[out.length - 1][1] = i; else out.push([i, i]);
  }
  return out;
}

/**
 * Ruling lines of a sheet (panel dividers / frames drawn despite "white gutters"): thin (<= maxThick px) straight
 * foreground lines that run edge to edge — horizontal: from within 3 % of the left edge to within 3 % of the right
 * edge; vertical: >= 20 % of the height, each end at the image edge (3 %) or on a horizontal ruling line. A drawing
 * never touches the sheet border, so this never takes part of a view. Returns a copy with the lines (+-1 px) painted
 * white and the list of lines.
 */
export function removeRules(img, fgMax, maxThick = 12) {
  const { width: W, height: H } = img;
  const fg = fgMask(img, fgMax);
  const hRows = [];
  for (let y = 0; y < H; y += 1) {
    const r = longestRun((x) => fg[y * W + x], W);
    if (r && r[0] <= 0.03 * W && r[1] >= 0.97 * W) hRows.push(y);
  }
  const hLines = ranges(hRows).filter(([a, b]) => b - a + 1 <= maxThick);
  const nearH = (y) => hLines.some(([a, b]) => y >= a - 4 && y <= b + 4);
  const vCols = new Map();
  for (let x = 0; x < W; x += 1) {
    // every run of this column, gaps <= 2 px bridged
    let start = -1; let last = -2;
    const flush = () => {
      if (start < 0) return;
      const okStart = start <= 0.03 * H || nearH(start);
      const okEnd = last >= 0.97 * H || nearH(last);
      if (okStart && okEnd && last - start + 1 >= 0.2 * H) { if (!vCols.has(x)) vCols.set(x, []); vCols.get(x).push([start, last]); }
    };
    for (let y = 0; y < H; y += 1) {
      if (!fg[y * W + x]) continue;
      if (start < 0 || y - last - 1 > 2) { flush(); start = y; }
      last = y;
    }
    flush();
  }
  const vLines = [];
  for (const [a, b] of ranges([...vCols.keys()].sort((p, q) => p - q))) {
    if (b - a + 1 > maxThick) continue;
    const ys = [...Array(b - a + 1).keys()].flatMap((k) => vCols.get(a + k));
    vLines.push({ x: [a, b], y: [Math.min(...ys.map((r) => r[0])), Math.max(...ys.map((r) => r[1]))] });
  }
  const data = Buffer.from(img.data);
  const paint = (x, y) => { if (x >= 0 && x < W && y >= 0 && y < H) { const p = (y * W + x) * 3; data[p] = 255; data[p + 1] = 255; data[p + 2] = 255; } };
  for (const [a, b] of hLines) for (let y = a - 1; y <= b + 1; y += 1) for (let x = 0; x < W; x += 1) paint(x, y);
  for (const v of vLines) for (let x = v.x[0] - 1; x <= v.x[1] + 1; x += 1) for (let y = v.y[0]; y <= v.y[1]; y += 1) paint(x, y);
  const rules = [...hLines.map(([a, b]) => ({ dir: "h", y: [a, b] })), ...vLines.map((v) => ({ dir: "v", ...v }))];
  return { img: { data, width: W, height: H }, rules };
}

/** Split a sheet into rows x cols panels on its white gutters -> [{x, y, w, h}] row-major (panel rects in sheet px). */
export function splitSheet(img, mask, rows, cols) {
  const { width, height } = img;
  const tolRow = Math.max(1, Math.round(width * 0.0005));
  const rowOcc = new Uint8Array(height);
  for (let y = 0; y < height; y += 1) {
    let n = 0; const row = y * width;
    for (let x = 0; x < width; x += 1) n += mask[row + x];
    rowOcc[y] = n > tolRow ? 1 : 0;
  }
  const r = splitCuts(rowOcc, rows);
  const rowEdges = [0, ...r.cuts.map((c) => c + 1), height];
  const panels = [];
  const gutters = { rows: r.gaps, cols: [] };
  for (let ri = 0; ri < rows; ri += 1) {
    const ya = rowEdges[ri]; const yb = rowEdges[ri + 1];
    const tolCol = Math.max(1, Math.round((yb - ya) * 0.0005));
    const colOcc = new Uint8Array(width);
    for (let x = 0; x < width; x += 1) {
      let n = 0;
      for (let y = ya; y < yb; y += 1) n += mask[y * width + x];
      colOcc[x] = n > tolCol ? 1 : 0;
    }
    const c = splitCuts(colOcc, cols);
    gutters.cols.push(c.gaps);
    const colEdges = [0, ...c.cuts.map((k) => k + 1), width];
    for (let ci = 0; ci < cols; ci += 1) panels.push({ x: colEdges[ci], y: ya, w: colEdges[ci + 1] - colEdges[ci], h: yb - ya });
  }
  return { panels, gutters };
}

/** Crop an RGB image (with white outside). */
/**
 * The gutter split's fallback (a drawing crosses a gutter: a helicopter's rotor blade over the column gutter): every
 * connected component of the drawing mask goes to the grid cell (rows x cols equal quarters of the sheet) holding its
 * centroid; each cell must hold a major component (>= minShare of the drawing), else it throws (a sheet off the 2 x 2
 * layout still fails). -> { panels: [{x, y, w, h}] row-major (the cell's components' bbox), images: [RGB] (the panel
 * crop with every other cell's drawing painted white), cells: [{components, px}] }
 */
export function splitQuadrants(img, mask, rows, cols, { minShare = 0.02 } = {}) {
  const { width, height } = img;
  const { labels, sizes } = components(mask, width, height);
  const n = sizes.length;
  const sx = new Float64Array(n); const sy = new Float64Array(n);
  for (let i = 0; i < mask.length; i += 1) { const k = labels[i]; if (!k) continue; const x = i % width; sx[k] += x; sy[k] += (i - x) / width; }
  const total = sizes.reduce((a, b) => a + b, 0);
  const cellOf = new Int32Array(n).fill(-1);
  const cells = Array.from({ length: rows * cols }, () => ({ components: 0, px: 0, major: 0, x0: Infinity, y0: Infinity, x1: -1, y1: -1 }));
  for (let k = 1; k < n; k += 1) {
    const r = Math.min(rows - 1, Math.floor((sy[k] / sizes[k]) / (height / rows)));
    const c = Math.min(cols - 1, Math.floor((sx[k] / sizes[k]) / (width / cols)));
    cellOf[k] = r * cols + c;
    const cell = cells[cellOf[k]];
    cell.components += 1; cell.px += sizes[k];
    if (sizes[k] >= minShare * total) cell.major += 1;
  }
  for (let i = 0; i < mask.length; i += 1) {
    const k = labels[i]; if (!k) continue;
    const cell = cells[cellOf[k]]; const x = i % width; const y = (i - x) / width;
    if (x < cell.x0) cell.x0 = x; if (x > cell.x1) cell.x1 = x; if (y < cell.y0) cell.y0 = y; if (y > cell.y1) cell.y1 = y;
  }
  const empty = cells.map((c, i) => (c.major ? null : i)).filter((i) => i !== null);
  if (empty.length) throw new Error(`quadrant split: cell(s) ${empty.join(", ")} (row-major) hold no drawing >= ${minShare * 100} % — not a ${rows} x ${cols} sheet`);
  const pad = 4;
  const panels = cells.map((c) => {
    const x = Math.max(0, c.x0 - pad); const y = Math.max(0, c.y0 - pad);
    return { x, y, w: Math.min(width - 1, c.x1 + pad) - x + 1, h: Math.min(height - 1, c.y1 + pad) - y + 1 };
  });
  const images = panels.map((p, ci) => {
    const out = crop(img, p.x, p.y, p.w, p.h);
    for (let yy = 0; yy < p.h; yy += 1) {
      for (let xx = 0; xx < p.w; xx += 1) {
        const k = labels[(p.y + yy) * width + (p.x + xx)];
        if (k && cellOf[k] !== ci) { const d = (yy * p.w + xx) * 3; out.data[d] = 255; out.data[d + 1] = 255; out.data[d + 2] = 255; }
      }
    }
    return out;
  });
  return { panels, images, cells: cells.map((c) => ({ components: c.components, px: c.px })) };
}

function crop(img, x, y, w, h) {
  const out = Buffer.alloc(w * h * 3, 255);
  for (let yy = 0; yy < h; yy += 1) {
    const sy = y + yy; if (sy < 0 || sy >= img.height) continue;
    for (let xx = 0; xx < w; xx += 1) {
      const sx = x + xx; if (sx < 0 || sx >= img.width) continue;
      const s = (sy * img.width + sx) * 3; const d = (yy * w + xx) * 3;
      out[d] = img.data[s]; out[d + 1] = img.data[s + 1]; out[d + 2] = img.data[s + 2];
    }
  }
  return { data: out, width: w, height: h };
}

function mirrorX(img) {
  const out = Buffer.alloc(img.data.length);
  for (let y = 0; y < img.height; y += 1) {
    for (let x = 0; x < img.width; x += 1) {
      const s = (y * img.width + x) * 3; const d = (y * img.width + (img.width - 1 - x)) * 3;
      out[d] = img.data[s]; out[d + 1] = img.data[s + 1]; out[d + 2] = img.data[s + 2];
    }
  }
  return { data: out, width: img.width, height: img.height };
}

/** Pixels with darkest channel >= t connected (4-conn.) to the image border -> pure white. Returns px changed. */
export function cleanBackground(img, t) {
  const { data, width, height } = img;
  const seen = new Uint8Array(width * height);
  const stack = new Int32Array(width * height);
  let top = 0; let changed = 0;
  const light = (i) => Math.min(data[i * 3], data[i * 3 + 1], data[i * 3 + 2]) >= t;
  const push = (i) => { if (!seen[i] && light(i)) { seen[i] = 1; stack[top++] = i; } };
  for (let x = 0; x < width; x += 1) { push(x); push((height - 1) * width + x); }
  for (let y = 0; y < height; y += 1) { push(y * width); push(y * width + width - 1); }
  while (top) {
    const i = stack[--top];
    const p = i * 3;
    if (data[p] !== 255 || data[p + 1] !== 255 || data[p + 2] !== 255) { data[p] = 255; data[p + 1] = 255; data[p + 2] = 255; changed += 1; }
    const x = i % width; const y = (i - x) / width;
    if (x > 0) push(i - 1); if (x < width - 1) push(i + 1);
    if (y > 0) push(i - width); if (y < height - 1) push(i + width);
  }
  return changed;
}

/** Scale the drawing (crop around bbox) by s and paste it centred on a white C x C canvas. */
async function render(view, bb, s, C, margin) {
  const mr = Math.max(1, Math.ceil(margin / Math.max(s, 1e-6)));
  const src = crop(view, bb.x0 - mr, bb.y0 - mr, bb.w + 2 * mr, bb.h + 2 * mr);
  const tw = Math.max(1, Math.round(src.width * s)); const th = Math.max(1, Math.round(src.height * s));
  const { data } = await sharp(src.data, { raw: { width: src.width, height: src.height, channels: 3 } })
    .resize(tw, th, { kernel: "lanczos3", fit: "fill" }).raw().toBuffer({ resolveWithObject: true });
  const sx = tw / src.width; const sy = th / src.height;
  // where the bbox centre lands inside the resized crop -> offset that puts it on the canvas centre
  const bcx = (mr + (bb.w - 1) / 2 + 0.5) * sx - 0.5; const bcy = (mr + (bb.h - 1) / 2 + 0.5) * sy - 0.5;
  const ox = Math.round((C - 1) / 2 - bcx); const oy = Math.round((C - 1) / 2 - bcy);
  const canvas = Buffer.alloc(C * C * 3, 255);
  let clipped = false;
  for (let y = 0; y < th; y += 1) {
    const cy = y + oy;
    for (let x = 0; x < tw; x += 1) {
      const cx = x + ox; const s3 = (y * tw + x) * 3;
      if (cy < 0 || cy >= C || cx < 0 || cx >= C) {
        if (Math.min(data[s3], data[s3 + 1], data[s3 + 2]) < 250) clipped = true;
        continue;
      }
      const d = (cy * C + cx) * 3;
      canvas[d] = data[s3]; canvas[d + 1] = data[s3 + 1]; canvas[d + 2] = data[s3 + 2];
    }
  }
  return { img: { data: canvas, width: C, height: C }, clipped };
}

/** Shift a canvas image by integer (dx, dy), white fill. */
function shift(img, dx, dy) {
  if (!dx && !dy) return img;
  const { width: W, height: H } = img;
  const out = Buffer.alloc(img.data.length, 255);
  for (let y = 0; y < H; y += 1) {
    const sy = y - dy; if (sy < 0 || sy >= H) continue;
    for (let x = 0; x < W; x += 1) {
      const sx = x - dx; if (sx < 0 || sx >= W) continue;
      const s = (sy * W + sx) * 3; const d = (y * W + x) * 3;
      out[d] = img.data[s]; out[d + 1] = img.data[s + 1]; out[d + 2] = img.data[s + 2];
    }
  }
  return { data: out, width: W, height: H };
}

/**
 * Normalise one view: scale so that bbox[axis] = target px, centre, clean. -> { img, scale, out bbox, notes }
 * axis "w" (side, top) or "h" (front, rear).
 */
export async function normalizeView(view, { axis, target, C, fgMax, minBlob, keepMain, margin, bgClean }) {
  const dm = drawingMask(view, { fgMax, minBlob, keepMain });
  const bb = bboxOf(dm.mask, view.width, view.height);
  if (!bb) throw new Error("no foreground");
  let s = target / bb[axis];
  let best = null;
  // specks grow with the resample: the output-side speck filter scales with s^2 (same specks ignored on both sides)
  const minOut = (sc) => Math.max(minBlob, Math.round(minBlob * sc * sc));
  for (let pass = 0; pass < 4; pass += 1) {
    const r = await render(view, bb, s, C, margin);
    if (bgClean !== null) cleanBackground(r.img, bgClean);
    const m = drawingMask(r.img, { fgMax, minBlob: minOut(s), keepMain: keepMain ? Math.round(keepMain * s) : 0 }).mask;
    const ob = bboxOf(m, C, C);
    const err = ob ? ob[axis] - target : Infinity;
    if (!best || Math.abs(err) < Math.abs(best.err)) best = { r, ob, err, s };
    if (err === 0 || !ob) break;
    s *= target / ob[axis];
  }
  // re-centre the bbox on the canvas centre (integer shift), then measure the result
  const want = (C - 1) / 2;
  const dx = Math.round(want - best.ob.cx); const dy = Math.round(want - best.ob.cy);
  const img = shift(best.r.img, dx, dy);
  const ob = bboxOf(drawingMask(img, { fgMax, minBlob: minOut(best.s), keepMain: keepMain ? Math.round(keepMain * best.s) : 0 }).mask, C, C);
  const notes = [];
  if (best.r.clipped || ob.x0 === 0 || ob.y0 === 0 || ob.x1 === C - 1 || ob.y1 === C - 1) notes.push(`drawing clipped by the ${C} px canvas`);
  if (best.err !== 0) notes.push(`bbox ${axis} ${best.ob[axis]} vs target ${target} (${best.err > 0 ? "+" : ""}${best.err} px after 4 passes)`);
  if (dm.dropped.blobs) notes.push(`${dm.dropped.blobs} blob(s) / ${dm.dropped.px} px ignored for the bbox (< ${minBlob} px${keepMain ? ` or outside the main cluster at ${keepMain} px` : ""})`);
  return { img, scale: +best.s.toFixed(5), raw: bb, out: ob, notes };
}

/** A live turnaround's side view: { file, L, H, canvas, fgMaxLive, files: {view: views.json file name} } */
export async function liveSide(dir, fgMax) {
  let file = "side.png"; let fgMaxLive = null; const files = {};
  const vj = path.join(dir, "views.json");
  if (fs.existsSync(vj)) {
    const spec = JSON.parse(fs.readFileSync(vj, "utf8"));
    if (spec.views?.side?.file) file = spec.views.side.file;
    if (Number.isFinite(spec.families?.fgMax)) fgMaxLive = spec.families.fgMax;
    for (const [v, e] of Object.entries(spec.views || {})) if (e?.file) files[v] = e.file;
  }
  const full = path.join(dir, file);
  const img = await readRGB(full);
  const bb = bboxOf(drawingMask(img, { fgMax }).mask, img.width, img.height);
  return { file: full, L: bb.w, H: bb.h, canvas: img.width, fgMaxLive, files };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if ((!args.in && !args.sheet) || !args.out || args.in === true || args.sheet === true || args.out === true) {
    console.error("usage: node scripts/v7/normalize-views.mjs (--in <dir> | --sheet <png> [--layout 2x2] [--order side,front,rear,top]) --out <dir> [--like <live turnaround dir>] [--side-l 800] [--canvas 1024] [--fg-max 235] [--mirror <view,...>] [--bg-clean <t>|off] [--min-blob 30] [--margin 3] [--keep-main <px>] [--keep-rules]");
    process.exit(2);
  }
  const fgMax = Number(args["fg-max"] ?? FG_MAX_DEFAULT);
  const minBlob = Number(args["min-blob"] ?? 30);
  const margin = Number(args.margin ?? 3);
  const keepMain = Number(args["keep-main"] ?? 0);
  const mirror = typeof args.mirror === "string" ? args.mirror.split(",").map((v) => v.trim()).filter(Boolean) : [];
  const order = typeof args.order === "string" ? args.order.split(",").map((v) => v.trim()) : VIEW_NAMES;
  for (const v of [...mirror, ...order]) if (!VIEW_NAMES.includes(v)) throw new Error(`unknown view "${v}" (views: ${VIEW_NAMES.join(", ")})`);

  let L = Number(args["side-l"] ?? 800);
  let C = Number(args.canvas ?? 1024);
  let like = null;
  let bgDefault = 240;
  if (typeof args.like === "string") {
    like = await liveSide(path.resolve(args.like), fgMax);
    if (args["side-l"] === undefined) L = like.L;
    if (args.canvas === undefined) C = like.canvas;
    if (like.fgMaxLive && like.fgMaxLive - 2 > bgDefault) bgDefault = like.fgMaxLive - 2;
  }
  const bgClean = args["bg-clean"] === "off" ? null : Number(args["bg-clean"] ?? bgDefault);

  // inputs -> { view: RGB image }, provenance
  const inputs = {};
  const report = { tool: "scripts/v7/normalize-views.mjs", date: new Date().toISOString(), rule: "side bbox L = target; front / rear bbox height = the side's; top bbox length = the side's L; bbox centre on the canvas centre", fgMax, minBlob, keepMain: keepMain || null, margin, bgClean, canvas: C, sideL: L, like: like ? { dir: path.resolve(args.like), sideFile: like.file, sideL: like.L, sideH: like.H, canvas: like.canvas, fgMaxLive: like.fgMaxLive } : null, mirror, source: null, views: {}, notes: [] };
  if (typeof args.sheet === "string") {
    const file = path.resolve(args.sheet);
    const [rows, cols] = String(args.layout ?? "2x2").split("x").map(Number);
    if (order.length !== rows * cols) throw new Error(`--order names ${order.length} views; layout ${rows}x${cols} has ${rows * cols} panels`);
    const raw = await readRGB(file);
    const { img, rules } = args["keep-rules"] ? { img: raw, rules: [] } : removeRules(raw, fgMax);
    if (rules.length) report.notes.push(`sheet: ${rules.length} ruling line(s) (panel dividers / frame) painted white before the split: ${rules.map((r) => (r.dir === "h" ? `h y ${r.y[0]}..${r.y[1]}` : `v x ${r.x[0]}..${r.x[1]} y ${r.y[0]}..${r.y[1]}`)).join("; ")}`);
    const dm = drawingMask(img, { fgMax, minBlob });
    let split;
    try {
      split = splitSheet(img, dm.mask, rows, cols);
    } catch (e) {
      if (!/white gutter/.test(e.message)) throw e;
      // a drawing crosses a gutter (rotor blades): each connected drawing goes to the quarter holding its centroid
      const q = splitQuadrants(img, dm.mask, rows, cols);
      split = { panels: q.panels, gutters: null, images: q.images, quadrants: q.cells };
      report.notes.push(`sheet: ${e.message} — split by quadrant instead (each connected drawing to the quarter of its centroid; other quarters' drawings painted white in each panel): ${q.cells.map((c, i) => `${order[i]} ${c.components} component(s) ${c.px} px`).join("; ")}`);
    }
    const { panels, gutters } = split;
    report.source = { sheet: file, sha256: sha256(file), width: img.width, height: img.height, layout: `${rows}x${cols}`, order, rules, panels: Object.fromEntries(panels.map((p, i) => [order[i], p])), gutters, ...(split.quadrants ? { split: "quadrants" } : {}) };
    panels.forEach((p, i) => { inputs[order[i]] = split.images ? split.images[i] : crop(img, p.x, p.y, p.w, p.h); });
  } else {
    const dir = path.resolve(args.in);
    report.source = { dir, files: {} };
    for (const v of VIEW_NAMES) {
      const file = path.join(dir, `${v}.png`);
      if (!fs.existsSync(file)) { report.notes.push(`${v}: no ${v}.png in --in`); continue; }
      const img = await readRGB(file);
      inputs[v] = img;
      report.source.files[v] = { file, sha256: sha256(file), width: img.width, height: img.height };
    }
  }
  for (const v of mirror) if (inputs[v]) inputs[v] = mirrorX(inputs[v]);

  const outDir = path.resolve(args.out);
  fs.mkdirSync(outDir, { recursive: true });
  const opts = { C, fgMax, minBlob, keepMain, margin, bgClean };
  const results = {};
  // the side first: its normalised bbox height is the front / rear target
  if (inputs.side) results.side = await normalizeView(inputs.side, { ...opts, axis: "w", target: L });
  const sideH = results.side ? results.side.out.h : null;
  for (const v of ["front", "rear"]) {
    if (!inputs[v]) continue;
    if (!sideH) { report.notes.push(`${v}: no side view -> no height target; skipped`); continue; }
    results[v] = await normalizeView(inputs[v], { ...opts, axis: "h", target: sideH });
  }
  if (inputs.top) results.top = await normalizeView(inputs.top, { ...opts, axis: "w", target: L });

  for (const [v, r] of Object.entries(results)) {
    const file = path.join(outDir, `${v}.png`);
    await sharp(r.img.data, { raw: { width: C, height: C, channels: 3 } }).png().toFile(file);
    // a live set that names this view differently (school_bus side_right.png): the same bytes under that name too, so
    // tools reading the live views.json file names from this folder (hull.mjs --views-dir) find every view
    const alias = like?.files?.[v] && like.files[v] !== `${v}.png` ? like.files[v] : null;
    if (alias) fs.copyFileSync(file, path.join(outDir, alias));
    report.views[v] = { file, alias, sha256: sha256(file), mirrored: mirror.includes(v), axis: v === "front" || v === "rear" ? "h" : "w", target: v === "front" || v === "rear" ? sideH : L, scale: r.scale, rawBbox: r.raw, outBbox: r.out, notes: r.notes };
    const o = r.out;
    console.log(`${v.padEnd(5)} raw bbox ${r.raw.w}x${r.raw.h} -> x${r.scale.toFixed(4)} -> ${o.w}x${o.h} at ${o.cx},${o.cy}${mirror.includes(v) ? " (mirrored)" : ""}${report.views[v].alias ? ` (+ ${report.views[v].alias})` : ""}${r.notes.length ? "  NOTE " + r.notes.join("; ") : ""}`);
  }
  for (const n of report.notes) console.log(`NOTE ${n}`);
  fs.writeFileSync(path.join(outDir, "normalize.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(`wrote ${Object.keys(results).map((v) => `${v}.png`).join(", ")} + normalize.json -> ${outDir} (L ${L} px, canvas ${C}${like ? `, like ${path.basename(path.dirname(like.file))}/${path.basename(like.file)}` : ""})`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((err) => { console.error(err.stack || String(err)); process.exit(1); });
}
