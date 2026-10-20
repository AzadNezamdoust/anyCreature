#!/usr/bin/env node
// WORKFLOW v7 — measuring on the references (scripts/v7/README.md). Any subject; run from hard_surface.
//
//   node scripts/v7/measure.mjs comps     --subject <s> [--view v] [--family f] [--min-px 40] [--top 20]
//   node scripts/v7/measure.mjs project   --subject <s> --module <m.mjs> [--frame s,tx,ty] x,y,z ...
//   node scripts/v7/measure.mjs unproject --subject <s> --module <m.mjs> [--frame s,tx,ty] X,Y,axis,value ...
//   node scripts/v7/measure.mjs sample    (--subject <s> [--view concept|<v>] | --image <png>) x,y,w,h ...
//   node scripts/v7/measure.mjs grid      (--subject <s> [--view ..] | --image <png>) x0,y0,x1,y1 --out <png> [--scale 3] [--module <m.mjs> [--diff]]
//   node scripts/v7/measure.mjs runs      (--subject <s> [--view ..] | --image <png>) row|col <index> <from> <to> [--tol 18 | --family]
//   node scripts/v7/measure.mjs profile   --subject <s> --view <ortho> [--axis row|col] [--from m] [--to m] [--step 0.05] [--module <m.mjs>]
//   node scripts/v7/measure.mjs profile   --subject <s> --view concept [--axis row|col] [--from px] [--to px] [--step 10] [--module <m.mjs>]
//
// comps: connected components of each colour family in the orthographic turnaround views, bboxes in METRES along the
// view's right / up axes (scripts/v6/ortho.mjs components). project / unproject: the concept camera (registered solve +
// the module's frameScale / frameX / frameY knobs): author point -> concept px, and concept px -> the author point on
// the plane axis = value. sample: per-channel median colour of rects. grid: crop + nearest upscale with a 10 / 50 px
// coordinate grid (image px labels); with --module (concept or an ortho view) the model's true-colour cel render of the
// same window sits to the right. runs: colour runs along a row / column (raw RGB within --tol of the run's first px, or
// --family: runs of the subject's colour families).
import path from "node:path";
import process from "node:process";

import sharp from "sharp";

import { framed, frameOf } from "../registered.mjs";
import { buildModule, meshParts, project, subjectRegistration } from "../project.mjs";
import { CEL, basisOf, classify, components, loadTurnaround, rasterOrtho, viewFamilyTable, viewMap } from "../v6/ortho.mjs";
import { judge, shadeRGB } from "../v6/judge.mjs";
import { frontRotationDeg } from "../../src/kernel/toThree.mjs";
import {
  colourRuns, conceptTarget, f3, familyTableOf, hexOf, imagePathOf, importModule, medianColour, modulePathOf, parseArgs, projectPoint,
  r3, readRaw, unprojectPoint,
} from "./lib.mjs";

const USAGE = `usage: node scripts/v7/measure.mjs <comps|project|unproject|sample|grid|runs|profile> ... (see the header / scripts/v7/README.md)`;
const [cmd, ...rest] = process.argv.slice(2);
const args = parseArgs(rest, ["family", "diff", "help"]);
const need = (name) => {
  if (!args[name] || args[name] === true) throw new Error(`--${name} is required\n${USAGE}`);
  return args[name];
};

async function comps() {
  const { reg, table } = await loadTurnaround(need("subject"));
  const minPx = Number(args["min-px"] ?? 40), top = Number(args.top ?? 20);
  const view = args.view && args.view !== "all" ? args.view : null;
  if (view && !reg.names.includes(view)) throw new Error(`no ortho view "${view}" (views: ${reg.names.join(", ")})`);
  const fw = Math.max(...table.names.slice(1).map((n) => String(n).length));
  // `--family` is a boolean for `runs`, so `comps --family glass` arrives as true + a positional "glass"
  const fam = args.family === true ? args._[0] : args.family;
  if (fam && !table.names.includes(fam)) throw new Error(`no colour family "${fam}" (families: ${table.names.slice(1).join(", ")})`);
  console.log(`# ${args.subject}: ${reg.s.toFixed(2)} px/m; families ${table.names.slice(1).join(", ")}; columns: view family px-count right(m) up(m) px-bbox`);
  for (const v of reg.names) {
    if (view && view !== v) continue;
    for (let f = 1; f < table.names.length; f += 1) {
      if (fam && fam !== table.names[f]) continue;
      for (const c of components(reg, v, f, minPx).slice(0, top)) {
        console.log(v.padEnd(5), String(table.names[f]).padEnd(fw), String(c.n).padStart(6), "right", r3(c.right[0]), r3(c.right[1]), `(w ${r3(c.right[1] - c.right[0])})`, "up", r3(c.up[0]), r3(c.up[1]), `(h ${r3(c.up[1] - c.up[0])})`, "px", c.px.join(","));
      }
    }
  }
}

/** The concept registration framed by the module's frame knobs, or by `--frame scale,tx,ty` (e.g. a variants.mjs row). */
async function conceptReg() {
  const mod = await importModule(need("module"));
  let frame = frameOf(mod.KNOBS);
  if (args.frame) {
    const [scale, tx, ty] = String(args.frame).split(",").map(Number);
    if (![scale, tx, ty].every(Number.isFinite)) throw new Error(`bad --frame "${args.frame}" (want scale,tx,ty)`);
    frame = { scale, tx, ty };
  }
  const reg = framed(subjectRegistration(need("subject")), frame);
  console.log("s", reg.s.toFixed(3), "ox", reg.ox.toFixed(2), "oy", reg.oy.toFixed(2), "R", f3(reg.basis.right), "U", f3(reg.basis.up));
  return reg;
}

async function projectCmd() {
  const reg = await conceptReg();
  if (!args._.length) throw new Error("give one or more author points x,y,z");
  for (const q of args._) {
    const p = q.split(",").map(Number);
    if (p.length !== 3 || !p.every(Number.isFinite)) throw new Error(`bad point "${q}" (want x,y,z)`);
    console.log("p", f3(p), "->", f3(projectPoint(reg, p)));
  }
}

async function unprojectCmd() {
  const reg = await conceptReg();
  if (!args._.length) throw new Error("give one or more X,Y,axis,value (concept px, plane axis x|y|z = value in metres)");
  for (const q of args._) {
    const a = q.split(",");
    if (a.length !== 4) throw new Error(`bad query "${q}" (want X,Y,axis,value)`);
    console.log("u", a.join(","), "->", f3(unprojectPoint(reg, +a[0], +a[1], a[2], +a[3])));
  }
}

/** The family table that classifies the image being read: a turnaround view's own (views.json families.viewTable), else the subject's. */
async function imageTable() {
  const table = await familyTableOf(args.subject);
  const v = args.view && args.view !== true ? args.view : null;
  if (!table || !v || v === "concept" || (args.image && args.image !== true)) return table;
  return viewFamilyTable(table, (await loadTurnaround(args.subject)).spec.families, v);
}

async function sample() {
  const file = imagePathOf(args);
  const img = await readRaw(file);
  console.log(`# ${path.relative(process.cwd(), file)} ${img.width}x${img.height}`);
  const table = await imageTable();
  for (const r of args._) {
    const rect = r.split(",").map(Number);
    if (rect.length !== 4 || !rect.every(Number.isFinite)) throw new Error(`bad rect "${r}" (want x,y,w,h)`);
    const med = medianColour(img.data, img.width, img.channels, rect);
    console.log(r, hexOf(med), med.join(","), table ? `family ${table.names[classify(table, ...med)]}` : "");
  }
}

/**
 * The model's true-colour cel render at the full resolution of the concept or of one ortho view; `fg` = the model's
 * silhouette, `refFg` = the judged reference foreground (concept: the three-state target, occluded counted as fg;
 * ortho: the view's family raster) at the same resolution.
 */
async function modelRGB(view) {
  const subjectId = need("subject");
  const built = await buildModule(modulePathOf(args.module));
  if (view === "concept") {
    const proj = await project({ subjectId, frame: "target", built });
    const W = proj.w, H = proj.h;
    const shade = new Float32Array(W * H);
    for (let i = 0; i < W * H; i += 1) shade[i] = proj.face[i] === 0 ? CEL.top : proj.face[i] === 3 ? CEL.bottom : CEL.facing;
    const { T } = await conceptTarget(subjectId);
    return { rgb: shadeRGB(built.parts, built.meta.palette, proj.partId, shade, proj.face, W, H), W, H,
      fg: (i) => proj.partId[i] >= 0, refFg: (i) => T[i] !== 0 };
  }
  // ortho: the judge's uniform model scale sigma, at the reference's own resolution (judge.mjs orthoTiles framing)
  const { reg } = await loadTurnaround(subjectId);
  const { sigma } = await judge({ subjectId, built, tiles: false });
  const { meshes } = meshParts(built.parts, 0);
  const M = viewMap(reg, view, reg.views[view].img.w);
  const R = rasterOrtho(meshes, basisOf(reg.views[view].spec), { k: M.k * sigma, bx: M.bx, by: M.by }, M.w, M.h, frontRotationDeg(built.meta.front));
  const { img } = reg.views[view];
  if (img.w !== M.w || img.h !== M.h) throw new Error(`ortho raster ${M.w}x${M.h} != reference ${img.w}x${img.h}`);
  return { rgb: shadeRGB(built.parts, built.meta.palette, R.partId, R.shade, R.face, M.w, M.h), W: M.w, H: M.h,
    fg: (i) => R.partId[i] >= 0, refFg: (i) => img.fam[i] !== 0 };
}

/** view.mjs's diff tile at full resolution: shared silhouette = the reference faded to 35 %, reference only blue, model only red. */
function diffRGB(refRaw, m) {
  const out = Buffer.alloc(m.W * m.H * 3);
  for (let i = 0; i < m.W * m.H; i += 1) {
    const r = m.refFg(i), q = m.fg(i);
    const c = r && !q ? [0, 90, 255] : !r && q ? [230, 0, 0] : null;
    for (let k = 0; k < 3; k += 1) out[i * 3 + k] = c ? c[k] : Math.round(255 - 0.35 * (255 - refRaw.data[i * refRaw.channels + k]));
  }
  return out;
}

async function grid() {
  const file = imagePathOf(args);
  const out = path.resolve(need("out"));
  const win = (args._[0] ?? "").split(",").map(Number);
  if (win.length !== 4 || !win.every(Number.isFinite)) throw new Error("give the window x0,y0,x1,y1 (image px)");
  const [x0, y0, x1, y1] = win, s = Number(args.scale ?? 3);
  const w = x1 - x0, h = y1 - y0, W = Math.round(w * s), H = Math.round(h * s);
  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">`;
  for (let x = Math.ceil(x0 / 10) * 10; x < x1; x += 10) { const X = (x - x0) * s; const strong = x % 50 === 0; svg += `<line x1="${X}" y1="0" x2="${X}" y2="${H}" stroke="#00a0ff" stroke-opacity="${strong ? 0.8 : 0.25}" stroke-width="1"/>`; if (strong) svg += `<text x="${X + 2}" y="12" font-size="11" fill="#0060c0">${x}</text>`; }
  for (let y = Math.ceil(y0 / 10) * 10; y < y1; y += 10) { const Y = (y - y0) * s; const strong = y % 50 === 0; svg += `<line x1="0" y1="${Y}" x2="${W}" y2="${Y}" stroke="#00a0ff" stroke-opacity="${strong ? 0.8 : 0.25}" stroke-width="1"/>`; if (strong) svg += `<text x="2" y="${Y - 2}" font-size="11" fill="#0060c0">${y}</text>`; }
  svg += "</svg>";
  const gridded = async (img) => sharp(await img.extract({ left: x0, top: y0, width: w, height: h }).resize(W, H, { kernel: "nearest" }).png().toBuffer())
    .composite([{ input: Buffer.from(svg), left: 0, top: 0 }]).png().toBuffer();
  const A = await gridded(sharp(file).removeAlpha());
  if (!args.module) {
    await sharp(A).toFile(out);
  } else {
    const view = args.image ? "concept" : (args.view && args.view !== true ? args.view : "concept");
    if (args.diff && args.image) throw new Error("--diff needs --subject (the judged reference mask), not --image");
    const m = await modelRGB(view);
    const B = await gridded(sharp(m.rgb, { raw: { width: m.W, height: m.H, channels: 3 } }));
    const tiles = [{ input: A, left: 0, top: 0 }, { input: B, left: W + 10, top: 0 }];
    if (args.diff) {   // a third panel: the filled silhouette diff at full resolution (view.mjs colours)
      const raw = await readRaw(file);
      if (raw.width !== m.W || raw.height !== m.H) throw new Error(`reference ${raw.width}x${raw.height} != model raster ${m.W}x${m.H}`);
      tiles.push({ input: await gridded(sharp(diffRGB(raw, m), { raw: { width: m.W, height: m.H, channels: 3 } })), left: 2 * (W + 10), top: 0 });
    }
    await sharp({ create: { width: tiles.length * (W + 10) - 10, height: H, channels: 3, background: { r: 200, g: 200, b: 200 } } })
      .composite(tiles).png().toFile(out);
  }
  console.log("wrote", out, `(${args.module ? `reference | model${args.diff ? " | diff (blue = reference only, red = model only)" : ""}` : "reference"}, window ${x0},${y0}-${x1},${y1} x${s})`);
}

async function runs() {
  const file = imagePathOf(args);
  const [mode, idxS, aS, bS] = args._;
  if (!["row", "col"].includes(mode) || [idxS, aS, bS].some((v) => !Number.isFinite(Number(v)))) throw new Error("give row|col <index> <from> <to>");
  const img = await readRaw(file);
  const idx = +idxS, a = +aS, b = +bS;
  const px = [];
  for (let i = a; i <= b; i += 1) {
    const [x, y] = mode === "row" ? [i, idx] : [idx, i];
    const j = (y * img.width + x) * img.channels;
    px.push([img.data[j], img.data[j + 1], img.data[j + 2]]);
  }
  const table = await imageTable();
  if (args.family && !table) throw new Error("--family needs a --subject with a turnaround (its colour families)");
  const name = (c) => String(table.names[classify(table, ...c)]);
  const out = colourRuns(px, a, args.family ? { label: name } : { tol: Number(args.tol ?? 18) });
  for (const r of out) console.log(`${r.s}-${r.e}`.padEnd(10), `(${r.e - r.s + 1} px)`.padEnd(9), r.c.join(","), table ? name(r.c) : "");
}

/** Foreground extents per row (--axis row, the default: metres along the view's up axis) or per column (--axis col:
 * metres along its right axis) of one ortho view, as runs in metres along the other axis; with --module the model's
 * silhouette at the judge's sigma on the same line. Runs shorter than --min-run px (2) are dropped (ink specks). */
async function profile() {
  const subjectId = need("subject");
  const view = need("view");
  if (view === "concept") return conceptProfile(subjectId);
  const { reg } = await loadTurnaround(subjectId);
  if (!reg.names.includes(view)) throw new Error(`no ortho view "${view}" (views: ${reg.names.join(", ")})`);
  const V = reg.views[view], { w, h } = V.img, s = reg.s;
  const sr = s * (V.kr ?? 1);   // px per metre along the view's right axis (views.json `scale: {right}`, WF v8 WP3)
  const su = s * (V.ku ?? 1);   // px per metre along its up axis (views.json `scale: {up}`)
  const col = args.axis === "col";
  let model = null, sigma = null;
  if (args.module) {
    const built = await buildModule(modulePathOf(args.module));
    ({ sigma } = await judge({ subjectId, built, tiles: false }));
    const { meshes } = meshParts(built.parts, 0);
    const M = viewMap(reg, view, w);
    model = rasterOrtho(meshes, basisOf(V.spec), { k: M.k * sigma, bx: M.bx, by: M.by }, M.w, M.h, frontRotationDeg(built.meta.front)).partId;
  }
  const minRun = Number(args["min-run"] ?? 2), step = Number(args.step ?? 0.05);
  const lo = Number(args.from ?? (col ? -(V.ox / sr) : (V.oy - h) / su)), hi = Number(args.to ?? (col ? (w - V.ox) / sr : V.oy / su));
  const fmt = (runs) => (runs.length ? runs.map(([a, b]) => `${r3(a)}..${r3(b)}`).join(" ") : "-");
  const runsOf = (isFg, n, toM) => {
    const out = [];
    let start = -1;
    for (let i = 0; i <= n; i += 1) {
      const on = i < n && isFg(i);
      if (on && start < 0) start = i;
      if (!on && start >= 0) { if (i - start >= minRun) out.push([toM(start), toM(i)]); start = -1; }
    }
    return out;
  };
  console.log(`# ${subjectId} ${view}: ${col ? "per column (right m) -> up runs (m)" : "per row (up m) -> right runs (m)"}; ref${model ? ` | model (sigma ${sigma.toFixed(4)})` : ""}`);
  for (let m = lo; m <= hi + 1e-9; m += step) {
    const idx = Math.round(col ? V.ox + sr * m - 0.5 : V.oy - su * m - 0.5);
    if (idx < 0 || idx >= (col ? w : h)) continue;
    const n = col ? h : w;
    const at = (i) => (col ? i * w + idx : idx * w + i);
    // along a column the up axis runs against the image rows: report runs low..high in metres
    const toM = col ? (i) => (V.oy - i) / su : (i) => (i - V.ox) / sr;
    const fix = (runs) => (col ? runs.map(([a, b]) => [b, a]).reverse() : runs);
    const ref = fix(runsOf((i) => V.img.fam[at(i)] !== 0, n, toM));
    const mod = model ? fix(runsOf((i) => model[at(i)] >= 0, n, toM)) : null;
    console.log(`${col ? "right" : "up"} ${m.toFixed(3).padStart(7)}  ref ${fmt(ref)}${mod ? `  | model ${fmt(mod)}` : ""}`);
  }
}

/** profile --view concept: the same runs in concept PIXELS (--from / --to / --step in px; rows by default, --axis col
 * for columns): the judged three-state target (occluded counted as foreground) and, with --module, the model's
 * silhouette through its frame knobs (added by a modeller, round 4: tyre bottoms, roof corners and other silhouette
 * landmarks read off both images at once). */
async function conceptProfile(subjectId) {
  const col = args.axis === "col";
  let W, H, refFg, fg = null;
  if (args.module) ({ W, H, refFg, fg } = await modelRGB("concept"));
  else { const { img, T } = await conceptTarget(subjectId); W = img.w; H = img.h; refFg = (i) => T[i] !== 0; }
  const minRun = Number(args["min-run"] ?? 2), step = Number(args.step ?? 10);
  const lo = Number(args.from ?? 0), hi = Number(args.to ?? (col ? W - 1 : H - 1));
  const runsOf = (isFg, n) => {
    const out = [];
    let start = -1;
    for (let i = 0; i <= n; i += 1) {
      const on = i < n && isFg(i);
      if (on && start < 0) start = i;
      if (!on && start >= 0) { if (i - start >= minRun) out.push(`${start}..${i - 1}`); start = -1; }
    }
    return out.length ? out.join(" ") : "-";
  };
  console.log(`# ${subjectId} concept ${W}x${H}: per ${col ? "column -> row" : "row -> column"} runs (px); ref${fg ? " | model" : ""}`);
  for (let k = lo; k <= hi; k += step) {
    const n = col ? H : W;
    const at = (i) => (col ? i * W + k : k * W + i);
    console.log(`${col ? "col" : "row"} ${String(k).padStart(5)}  ref ${runsOf((i) => refFg(at(i)), n)}${fg ? `  | model ${runsOf((i) => fg(at(i)), n)}` : ""}`);
  }
}

const COMMANDS = { comps, project: projectCmd, unproject: unprojectCmd, sample, grid, runs, profile };
if (!COMMANDS[cmd] || args.help) {
  console.log(USAGE);
  process.exit(cmd && !args.help ? 3 : 0);
}
COMMANDS[cmd]().catch((e) => { console.error(e.message ?? e); process.exit(1); });
