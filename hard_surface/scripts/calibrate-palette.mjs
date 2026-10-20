#!/usr/bin/env node
// calibrate-palette — the P4 PALETTE SEAT, replaced by a script (WF-LOOP-R2 row
// B4). The seat cost 106 s and 39 k tokens to read hex values off the target by
// eye, and the round-2 audits found it had done that correctly: what looked
// like a palette fault was the renderer darkening the populated face
// (WF-LOOP-R2 A1). So the palette is no longer authored at all. This script
// takes the median target colour of each zone and rewrites ONLY the
// `palette: { … }` block of the module. Nothing else in the file is touched,
// and the same target always gives the same hex — no seat, no judgement.
//
//   node scripts/calibrate-palette.mjs [--subject facade_brick] [--module <file>]
//                                      [--target refs/tenement-iso.png] [--dry-run]
//
// Zones are sampled from `subjects/<subject>/regions.json` (Job A, FROZEN: px
// rects per zone on the target) when that file exists. Until it does, each zone
// falls back to a single hand-placed sample POINT on refs/tenement-iso.png —
// the five in the r2 Fable audit plus five picked here and verified by colour
// (see FALLBACK below). Every run prints which of the two it used per zone.
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

import { loadSubject, subjectIdFromArgv } from "./subject.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// ---------------------------------------------------------------------------
// Minimal PNG reader: 8-bit, colour type 2 (RGB) or 6 (RGBA), no interlace —
// what the target and every capture in this repo are. Deliberately NOT `sharp`:
// sharp is only present transitively here, and the palette must not depend on a
// package the harness does not declare.
// ---------------------------------------------------------------------------
function readPng(file) {
  const buf = fs.readFileSync(file);
  const SIG = "89504e470d0a1a0a";
  if (buf.subarray(0, 8).toString("hex") !== SIG) throw new Error(`${file} is not a PNG`);
  let width = 0; let height = 0; let channels = 0;
  const idat = [];
  for (let off = 8; off + 8 <= buf.length;) {
    const len = buf.readUInt32BE(off);
    const type = buf.subarray(off + 4, off + 8).toString("ascii");
    const body = buf.subarray(off + 8, off + 8 + len);
    if (type === "IHDR") {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      const depth = body[8];
      const colour = body[9];
      if (depth !== 8 || body[12] !== 0) throw new Error(`${file}: only 8-bit non-interlaced PNGs are read here`);
      if (colour === 2) channels = 3;
      else if (colour === 6) channels = 4;
      else throw new Error(`${file}: colour type ${colour} is not RGB/RGBA`);
    } else if (type === "IDAT") idat.push(Buffer.from(body));
    else if (type === "IEND") break;
    off += 12 + len;
  }
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const out = Buffer.alloc(stride * height);
  let pos = 0;
  for (let y = 0; y < height; y += 1) {
    const filter = raw[pos];
    pos += 1;
    const line = raw.subarray(pos, pos + stride);
    pos += stride;
    const row = out.subarray(y * stride, (y + 1) * stride);
    const up = y > 0 ? out.subarray((y - 1) * stride, y * stride) : null;
    for (let i = 0; i < stride; i += 1) {
      const a = i >= channels ? row[i - channels] : 0;
      const b = up ? up[i] : 0;
      const c = up && i >= channels ? up[i - channels] : 0;
      let value = line[i];
      if (filter === 1) value += a;
      else if (filter === 2) value += b;
      else if (filter === 3) value += (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c;
        const pa = Math.abs(p - a); const pb = Math.abs(p - b); const pc = Math.abs(p - c);
        value += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      } else if (filter !== 0) throw new Error(`${file}: unknown row filter ${filter}`);
      row[i] = value & 0xff;
    }
  }
  return { data: out, width, height, channels };
}

// ---------------------------------------------------------------------------
// Zones come from the class prior (`classes/<class>.json` paletteZones,
// WORKFLOW-V3 §7.5): `key` is the palette key an authored module uses, `region`
// the zone name in regions.json (Job A / WF-LOOP-R2 A3), `point`/`radius` the
// fallback sample on the target with the colour it reads there. Aliases (trim,
// parapet, metal) live in the same list.
// ---------------------------------------------------------------------------
const zonesOf = (cls) => Object.freeze((cls.paletteZones ?? [])
  .map((z) => [z.key, z.region, z.point, z.radius, z.reads, z.source]));

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const hex = (rgb) => `#${rgb.map((v) => v.toString(16).padStart(2, "0")).join("")}`;

/** Per-channel median of the collected samples. */
function medianHex(samples) {
  const mid = (values) => values.sort((a, b) => a - b)[Math.floor(values.length / 2)];
  return hex([0, 1, 2].map((k) => mid(samples.map((s) => s[k]))));
}

function pixel(png, x, y) {
  const i = (y * png.width + x) * png.channels;
  return [png.data[i], png.data[i + 1], png.data[i + 2]];
}

function samplePoint(png, [x, y], radius) {
  const samples = [];
  for (let dy = -radius; dy <= radius; dy += 1) {
    for (let dx = -radius; dx <= radius; dx += 1) {
      samples.push(pixel(png, clamp(x + dx, 0, png.width - 1), clamp(y + dy, 0, png.height - 1)));
    }
  }
  return samples;
}

/**
 * A zone entry in regions.json is `{rects: [[x, y, w, h], …]}` (Job A's shape,
 * origin top-left), and a bare rect or a list of them is accepted too.
 */
function rects(entry) {
  const one = (r) => {
    if (Array.isArray(r) && r.length === 4 && r.every(Number.isFinite)) return { x0: r[0], y0: r[1], x1: r[0] + r[2] - 1, y1: r[1] + r[3] - 1 };
    if (r && Number.isFinite(r.x) && Number.isFinite(r.w)) return { x0: r.x, y0: r.y, x1: r.x + r.w - 1, y1: r.y + r.h - 1 };
    if (r && Number.isFinite(r.x0) && Number.isFinite(r.x1)) return { x0: r.x0, y0: r.y0, x1: r.x1, y1: r.y1 };
    return null;
  };
  const inner = entry && !Array.isArray(entry) && Array.isArray(entry.rects) ? entry.rects : entry;
  const list = Array.isArray(inner) && !Number.isFinite(inner[0]) ? inner : [inner];
  return list.map(one).filter(Boolean);
}

/** regions.json keeps its zones under `zones`; a flat file is read too. */
function regionEntry(regions, name) {
  if (!regions) return null;
  const found = regions.zones?.[name] ?? regions[name];
  return found === undefined ? null : found;
}

function sampleRegion(png, entry) {
  const samples = [];
  for (const r of rects(entry)) {
    for (let y = Math.round(r.y0); y <= Math.round(r.y1); y += 1) {
      for (let x = Math.round(r.x0); x <= Math.round(r.x1); x += 1) {
        if (x < 0 || y < 0 || x >= png.width || y >= png.height) continue;
        samples.push(pixel(png, x, y));
      }
    }
  }
  return samples;
}

/** The `palette: { … }` block, located by brace counting from the one `palette:`. */
function paletteBlock(source) {
  const head = /palette\s*:\s*\{/g;
  const first = head.exec(source);
  if (!first) throw new Error("the module has no `palette: {` block");
  if (head.exec(source)) throw new Error("the module has more than one `palette: {` block");
  const open = first.index + first[0].length - 1;
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === "{") depth += 1;
    else if (source[i] === "}") {
      depth -= 1;
      if (depth === 0) return { start: first.index, open, end: i + 1 };
    }
  }
  throw new Error("the module's `palette: {` block is never closed");
}

function existingKeys(body) {
  // V5-4 item 3: a per-face entry `key: { top: "#..", front: "#..", side: "#.." }` is a key too (in body order)
  return [...body.matchAll(/["']?([A-Za-z_][\w]*)["']?\s*:\s*(?:["']#[0-9a-fA-F]{3,8}["']|\{[^{}]*\})/g)].map((m) => m[1]);
}

/** V5-4 item 3: the per-face entries of a palette body, key -> its `{ ... }` source text (kept verbatim). */
function faceEntries(body) {
  return new Map([...body.matchAll(/["']?([A-Za-z_][\w]*)["']?\s*:\s*(\{[^{}]*\})/g)].map((m) => [m[1], m[2].replace(/\s+/g, " ")]));
}

function main() {
  const argv = process.argv.slice(2);
  const flag = (name, fallback) => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
  };
  const dryRun = argv.includes("--dry-run");
  const S = loadSubject(subjectIdFromArgv(argv));
  const ZONES = zonesOf(S.cls);
  const moduleRel = flag("module", S.rel.module);
  const targetRel = flag("target", S.rel.target);
  const regionsRel = flag("regions", S.rel.regions);

  const png = readPng(path.resolve(ROOT, targetRel));
  const regionsFile = path.resolve(ROOT, regionsRel);
  const regions = fs.existsSync(regionsFile) ? JSON.parse(fs.readFileSync(regionsFile, "utf8")) : null;
  console.log(`[palette] target ${targetRel} ${png.width}x${png.height}; regions ${regions ? regionsRel : "MISSING — falling back to the audit sample points"}`);

  const modulePath = path.resolve(ROOT, moduleRel);
  const source = fs.readFileSync(modulePath, "utf8");
  const block = paletteBlock(source);
  const body = source.slice(block.open + 1, block.end - 1);
  const before = new Map([...body.matchAll(/["']?([A-Za-z_][\w]*)["']?\s*:\s*["'](#[0-9a-fA-F]{3,8})["']/g)].map((m) => [m[1], m[2]]));

  // Deterministic order: the keys the module already has, in their order, then
  // any zone it does not have yet, in the ZONES order.
  const order = [...existingKeys(body)];
  for (const [key] of ZONES) if (!order.includes(key)) order.push(key);
  const unmapped = existingKeys(body).filter((key) => !ZONES.some(([k]) => k === key));
  if (unmapped.length) {
    console.log(`[palette] WARNING: module palette key(s) with no paletteZones entry in classes/${S.klass}.json (never calibrated): ${unmapped.join(", ")}`);
  }

  const rows = [];
  const palette = new Map();
  const perFace = faceEntries(body);
  for (const key of order) {
    // V5-4 item 3: a per-face entry was sampled per face in the registered frame (calibrateFaces) — never flattened here
    if (perFace.has(key)) { palette.set(key, perFace.get(key)); rows.push([key, "kept (per-face entry)", perFace.get(key), perFace.get(key)]); continue; }
    const zone = ZONES.find(([k]) => k === key);
    if (!zone) {                                     // a zone this script does not sample
      palette.set(key, before.get(key) ?? "#000000");
      rows.push([key, "kept (no target zone)", palette.get(key), before.get(key) ?? "-"]);
      continue;
    }
    const [, region, point, radius] = zone;
    const entry = regionEntry(regions, region);
    const samples = entry ? sampleRegion(png, entry) : samplePoint(png, point, radius);
    if (samples.length < 1) throw new Error(`zone "${key}": region "${region}" sampled 0 pixels`);
    if (entry && samples.length < 25) throw new Error(`zone "${key}": region "${region}" has ${samples.length} interior px, under the 25 px floor (WF-LOOP-R2 A3)`);
    const colour = medianHex(samples);
    palette.set(key, colour);
    rows.push([key, entry ? `regions.json ${region} (${samples.length} px)` : `point ${point[0]},${point[1]} r${radius}`, colour, before.get(key) ?? "-"]);
  }

  const width = Math.max(...rows.map((r) => r[0].length));
  for (const [key, src, now, was] of rows) {
    console.log(`  ${key.padEnd(width)}  ${now}  ${now === was ? "(unchanged)" : `was ${was}`}  <- ${src}`);
  }

  const indent = (source.slice(0, block.start).match(/(^|\n)([ \t]*)$/)?.[2]) ?? "  ";
  const inner = `${indent}  `;
  const rendered = `palette: {\n${[...palette].map(([k, v]) => `${inner}${k}: ${String(v).startsWith("{") ? v : `"${v}"`},`).join("\n")}\n${indent}}`;
  let next = source.slice(0, block.start) + rendered + source.slice(block.end);

  // WORKFLOW-V3 §7.3 — the side/front value step is a MEASUREMENT, so a seat
  // never tunes it. shade multiplies LINEAR colour (src/geom.js SHADE.sideTint)
  // while the capture shows sRGB, so solve in linear light: the side's brightest
  // channel must land at the target's on-screen side/front ratio.
  // WORKFLOW-V3 §7.10 — the two flat face zones are class data (buildings: brick_front / brick_side_strip).
  const FACE = S.cls.likeness?.faceZones ?? { front: "brick_front", side: "brick_side_strip" };
  const front = regions ? regionEntry(regions, FACE.front) : null;
  const side = regions ? regionEntry(regions, FACE.side) : null;
  if (front && side) {
    const toRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
    const lin = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    const f = Math.max(...toRgb(medianHex(sampleRegion(png, front))));
    const s = Math.max(...toRgb(medianHex(sampleRegion(png, side))));
    const tint = Math.round((lin(s) / lin(f) - 1) * 1000) / 1000;
    const hit = /shade\s*:\s*\{([^}]*)\}/.exec(next);
    if (hit) {
      const body = /sideTint\s*:/.test(hit[1])
        ? hit[1].replace(/sideTint\s*:\s*-?[\d.]+/, "sideTint: " + tint)
        : hit[1].replace(/\s*$/, "") + ", sideTint: " + tint + " ";
      next = next.slice(0, hit.index) + "shade: {" + body + "}" + next.slice(hit.index + hit[0].length);
    } else {
      const at = next.indexOf("palette: {");
      next = next.slice(0, at) + "shade: { ao: 0.08, upTint: 0.12, sideTint: " + tint + " },\n" + indent + next.slice(at);
    }
    console.log("  sideTint  " + tint + "  <- screen side/front " + (s / f).toFixed(3)
      + " (regions " + FACE.side + " / " + FACE.front + "), solved in linear light");
  }
  if (next === source) { console.log("[palette] no change."); return; }
  if (dryRun) { console.log("[palette] --dry-run: not written."); return; }
  fs.writeFileSync(modulePath, next);
  console.log(`[palette] rewrote the palette block of ${moduleRel} (${palette.size} zones); nothing else in the file was touched.`);
}

// ---------------------------------------------------------------------------
// V5-4 item 3 — EXACT PALETTE PER ZONE PER FACE. The module is projected into the REGISTERED frame (scripts/project.mjs,
// target px, full resolution) with its face-orientation id pass; for every palette zone and every face {top, front,
// side} (bottom counts as side) the target px under that zone's parts on that face are sampled — SUBJECT px only, the
// target px classified to the zone's own colour family or to none (shading variants), eroded FACE_ERODE px inside the
// same zone + face (no anti-aliased edge, no neighbour) — and the per-channel median is that face's colour. A zone whose
// sampled faces differ by more than SPLIT_DE (CIEDE2000) gets a per-face entry {top, front, side} (src/app.js paints it
// by face normal, the flat capture and accuracy.mjs read it by face); otherwise one hex, the median of every sample.
// A face under FACE_MIN_SAMPLES px is not sampled (the entry falls back front -> side -> top); a zone with no sample
// keeps its entry.
// ---------------------------------------------------------------------------

export const FACE_ERODE = 2;
export const FACE_MIN_SAMPLES = 25;
export const SPLIT_DE = 2;
/** Fewest px of EACH face of a per-face entry (a thin, misaligned part must not split its zone on a few edge px). */
export const SPLIT_MIN_SAMPLES = 100;

/**
 * @param {{subjectId:string, modulePath:string, write?:boolean}} o
 * @returns {Promise<{zones:object, changed:boolean, text:string}>}
 */
export async function calibrateFaces({ subjectId, modulePath, write = true }) {
  const { project, FACES, NO_FACE } = await import("./project.mjs");
  const { readRGB, SUBJECT } = await import("./registered.mjs");
  const { targetOf, deltaE2000, hexRGB } = await import("./accuracy.mjs");
  const { partFamilies } = await import("./residuals.mjs");
  const S = loadSubject(subjectId);
  const img = await readRGB(S.paths.target);
  const file = path.resolve(ROOT, modulePath);
  const source = fs.readFileSync(file, "utf8");
  const proj = await project({ subjectId, modulePath, frame: "target", size: img.w });
  const T = targetOf(S, img);
  const pf = partFamilies(S, proj.parts, T);
  const { w, h, partId, face } = proj;
  const fk = (i) => (face[i] === NO_FACE ? -1 : face[i] === 3 ? 2 : face[i]);
  const zoneOf = proj.parts.map((q) => q.zone);
  const ok = (i) => {
    const p = partId[i];
    if (p < 0 || T.state[i] !== SUBJECT) return false;
    const tf = T.fam[i];
    return tf === pf[p] || tf === -2;   // V5-5 item 5: ink-opened px (accuracy INK = -3) are never sampled
  };
  const samples = new Map();   // zone -> [[], [], []] per face
  const r = FACE_ERODE;
  for (let y = r; y < h - r; y += 1) {
    for (let x = r; x < w - r; x += 1) {
      const i = y * w + x;
      if (!ok(i)) continue;
      const z = zoneOf[partId[i]];
      const f = fk(i);
      if (f < 0) continue;
      let inside = true;
      for (let dy = -r; dy <= r && inside; dy += 1) {
        for (let dx = -r; dx <= r; dx += 1) {
          const j = i + dy * w + dx;
          if (!ok(j) || zoneOf[partId[j]] !== z || fk(j) !== f) { inside = false; break; }
        }
      }
      if (!inside) continue;
      if (!samples.has(z)) samples.set(z, [[], [], []]);
      samples.get(z)[f].push([img.data[i * img.c], img.data[i * img.c + 1], img.data[i * img.c + 2]]);
    }
  }
  const block = paletteBlock(source);
  const body = source.slice(block.open + 1, block.end - 1);
  const keys = existingKeys(body);
  const perFace = faceEntries(body);
  const hexes = new Map([...body.matchAll(/["']?([A-Za-z_][\w]*)["']?\s*:\s*["'](#[0-9a-fA-F]{3,8})["']/g)].map((m) => [m[1], m[2]]));
  // a sampled colour is used only if the target's own classifier puts it in the zone's family (a sample of a misaligned
  // part reads its neighbour); a per-face entry needs every face >= SPLIT_MIN_SAMPLES px and one face in the family
  const regions = S.readJson("regions");
  // the classifier's own medians (likeness classifyTargetPixels: _measured, else the rects' median on the target)
  const medians = Object.entries(regions.zones).map(([name, z]) => [name, z._measured ?? hexRGB(medianHex(sampleRegion({ data: img.data, width: img.w, height: img.h, channels: img.c }, z)))]);
  const tol2 = (regions.areaTolerance ?? 32) ** 2;
  const familyOfHex = (hex) => {
    const rgb = hexRGB(hex);
    let best = null;
    let bestD = Infinity;
    for (const [name, m] of medians) { const d = (m[0] - rgb[0]) ** 2 + (m[1] - rgb[1]) ** 2 + (m[2] - rgb[2]) ** 2; if (d < bestD) { bestD = d; best = name; } }
    return bestD <= tol2 ? T.famOfZone[T.zoneNames.indexOf(best)] : -1;
  };
  const regionOfKey = Object.fromEntries((S.cls.paletteZones ?? []).map((z) => [z.key, z.region]));
  const famOfRegion = (region) => (T.zoneNames.includes(region) ? T.famOfZone[T.zoneNames.indexOf(region)] : -9);
  const famOfKey = (key) => { const q = proj.parts.findIndex((x) => x.zone === key); return q >= 0 ? pf[q] : -1; };
  const zones = {};
  const entries = new Map();
  for (const key of keys) {
    const got = samples.get(key) ?? [[], [], []];
    const faces = {};
    got.forEach((list, f) => { if (list.length >= FACE_MIN_SAMPLES) faces[FACES[f]] = { hex: medianHex(list), n: list.length }; });
    const names = Object.keys(faces);
    let entry = perFace.get(key) ?? `"${hexes.get(key)}"`;
    let split = 0;
    let why = null;
    if (names.length) {
      const fam = famOfKey(key);
      for (const a of names) for (const b of names) split = Math.max(split, deltaE2000(hexRGB(faces[a].hex), hexRGB(faces[b].hex)));
      const big = names.filter((n) => faces[n].n >= SPLIT_MIN_SAMPLES);
      const pooled = medianHex(got.flat());
      if (big.length >= 2 && split > SPLIT_DE && big.some((n) => familyOfHex(faces[n].hex) === fam)) {
        entry = `{ ${big.map((n) => `${n}: "${faces[n].hex}"`).join(", ")} }`;
      } else if (familyOfHex(pooled) === fam) entry = `"${pooled}"`;
      else why = `sample ${pooled} does not classify to the zone's family — kept`;
    }
    // no usable sample and a colour the classifier puts in ANOTHER family (an uncalibrated "#808080" frame reads as iron
    // or roof): the zone's own region median, so the flat render never paints one zone as another
    const hexNow = /^"(#[0-9a-f]{6})"$/i.exec(entry)?.[1];
    const region = regionOfKey[key];
    const own = medians.find(([n]) => n === region);
    if (hexNow && own && familyOfHex(hexNow) !== famOfRegion(region)) {
      entry = `"${hex(own[1])}"`;
      why = `${hexNow} classifies outside the zone's family — the region median ${region}`;
    }
    entries.set(key, entry);
    zones[key] = { faces, splitDE: Math.round(split * 100) / 100, entry, ...(why ? { why } : {}) };
  }
  const indent = (source.slice(0, block.start).match(/(^|\n)([ \t]*)$/)?.[2]) ?? "  ";
  const rendered = `palette: {\n${[...entries].map(([k, v]) => `${indent}  ${k}: ${v},`).join("\n")}\n${indent}}`;
  const text = source.slice(0, block.start) + rendered + source.slice(block.end);
  const changed = text !== source;
  if (write && changed) fs.writeFileSync(file, text);
  return { zones, changed, text };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
  // V5-4 item 3: --faces then samples every zone per face in the registered frame (after the regions medians)
  if (process.argv.includes("--faces")) {
    const argv = process.argv.slice(2);
    const S = loadSubject(subjectIdFromArgv(argv));
    const i = argv.indexOf("--module");
    const r = await calibrateFaces({ subjectId: S.id ?? S.subject.id, modulePath: i >= 0 ? argv[i + 1] : S.rel.module, write: !argv.includes("--dry-run") });
    for (const [k, z] of Object.entries(r.zones)) console.log(`  ${k.padEnd(12)} ${z.entry}  (faces ${Object.entries(z.faces).map(([f, v]) => `${f} ${v.n}`).join(", ") || "none sampled"}; split dE ${z.splitDE})`);
  }
}
