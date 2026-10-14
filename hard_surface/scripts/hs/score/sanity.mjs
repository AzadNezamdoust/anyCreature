// Game-resistance / sanity probes for likeness_score.mjs. Builds synthetic "renders" from a subject's own turnaround
// and scores them: a perfect copy must score ~1, and cheats that keep the outline perfect must lose the interior.
//   node scripts/hs/score/sanity.mjs [--subject pistol,gatling_gun,apc_8x8]
// Writes out/score/sanity/<s>/<probe>_<view>.png and out/score/sanity.json.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";
import { ROOT, VIEWS, scoreFiles } from "./likeness_score.mjs";

const argv = process.argv.slice(2), arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
const subjects = (arg("--subject") ?? "pistol,gatling_gun,apc_8x8").split(",");
const OUT = path.join(ROOT, "out", "score", "sanity");

async function raw(f) { const { data, info } = await sharp(f).removeAlpha().raw().toBuffer({ resolveWithObject: true }); return { data, w: info.width, h: info.height }; }
const save = (f, d, w, h) => sharp(Buffer.from(d), { raw: { width: w, height: h, channels: 3 } }).png().toFile(f);
const isFg = (d, i) => Math.min(d[i], d[i + 1], d[i + 2]) < 215;

const PROBES = {
  identity: async (src) => src.data,
  // perfect outline, interior = one flat fill of the source's median foreground colour (the outline score's blind spot)
  flat_fill: async (src) => { const d = Buffer.from(src.data), ls = [];
    for (let i = 0; i < d.length; i += 3) if (isFg(d, i)) ls.push([d[i] + d[i + 1] + d[i + 2], i]);
    ls.sort((a, b) => a[0] - b[0]); const m = ls[ls.length >> 1][1], c = [d[m], d[m + 1], d[m + 2]];
    for (let i = 0; i < d.length; i += 3) if (isFg(d, i)) { d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; } return d; },
  // perfect outline + perfect tones, interior detail smeared (blur 6 px inside the silhouette)
  blur_interior: async (src, file) => { const b = await sharp(file).removeAlpha().blur(6).raw().toBuffer(), d = Buffer.from(src.data);
    for (let i = 0; i < d.length; i += 3) if (isFg(d, i)) for (let c = 0; c < 3; c++) d[i + c] = b[i + c]; return d; },
  // tone shift: every foreground px 25 levels lighter (a value miss reviewers flag, "housing 10-25 levels too light")
  lighter_25: async (src) => { const d = Buffer.from(src.data);
    for (let i = 0; i < d.length; i += 3) if (isFg(d, i)) for (let c = 0; c < 3; c++) d[i + c] = Math.min(214, d[i + c] + 25); return d; },
  // openings closed: every very dark px (bores, slots) painted with the mean of its non-dark 15x15 surround
  close_openings: async (src) => { const d = Buffer.from(src.data), { w } = src, L = (i) => (d[i] + d[i + 1] + d[i + 2]) / 3;
    const dark = []; for (let i = 0; i < d.length; i += 3) if (isFg(d, i) && L(i) < 30) dark.push(i);
    const o = Buffer.from(d);
    for (const i of dark) { const p = i / 3, x = p % w, y = (p / w) | 0; let s = [0, 0, 0], k = 0;
      for (let yy = y - 7; yy <= y + 7; yy++) for (let xx = x - 7; xx <= x + 7; xx++) { const j = (yy * w + xx) * 3; if (j < 0 || j >= d.length) continue;
        if (isFg(d, j) && L(j) >= 30) { s[0] += d[j]; s[1] += d[j + 1]; s[2] += d[j + 2]; k++; } }
      if (k) for (let c = 0; c < 3; c++) o[i + c] = Math.round(s[c] / k); }
    return o; },
  // whole image moved 8 px (a registration offset the score is meant to forgive)
  shift_8px: async (src) => { const { data: d, w, h } = src, o = Buffer.alloc(d.length, 255);
    for (let y = 0; y < h; y++) for (let x = 0; x < w - 8; x++) for (let c = 0; c < 3; c++) o[(y * w + x + 8) * 3 + c] = d[(y * w + x) * 3 + c]; return o; },
};

const res = {};
for (const s of subjects) {
  fs.mkdirSync(path.join(OUT, s), { recursive: true });
  res[s] = {};
  for (const [name, fn] of Object.entries(PROBES)) {
    const files = {};
    for (const v of VIEWS) { const f = path.join(ROOT, "subjects", s, "turnaround", `${v}.png`), src = await raw(f);
      files[v] = path.join(OUT, s, `${name}_${v}.png`); await save(files[v], await fn(src, f), src.w, src.h); }
    const r = await scoreFiles(s, files);
    res[s][name] = { likeness: r.likeness, interior: r.interior, iou: r.iou, edgeF1: r.edgeF1, ssim: r.ssim, toneSim: r.toneSim, colourSim: r.colourSim, openF1: r.openF1 };
    console.log(`${s.padEnd(14)} ${name.padEnd(15)} likeness ${r.likeness.toFixed(3)} interior ${r.interior.toFixed(3)} iou ${r.iou.toFixed(3)} edge ${r.edgeF1.toFixed(3)} ssim ${r.ssim.toFixed(3)} tone ${r.toneSim.toFixed(3)} col ${r.colourSim.toFixed(3)} open ${r.openF1.toFixed(3)}`);
  }
}
fs.writeFileSync(path.join(ROOT, "out", "score", "sanity.json"), JSON.stringify(res, null, 1));
