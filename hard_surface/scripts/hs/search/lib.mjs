// Shared helpers of scripts/hs/search: Blender render pool (part_pass.py), baseline cache, build.py parsing, crops.
// Imports the score scripts; edits nothing outside out/search/ (callers pass the out dirs).
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import { ROOT, VIEWS } from "../score/likeness_score.mjs";

export { ROOT, VIEWS };
export const SEARCH = path.join(ROOT, "out", "search");
export const BLENDER = "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe";
export const TIE = 0.004;                 // |part delta| below this = tie, ties go to BASELINE (PART-CALIBRATION.md)
export const WHOLE_GUARD = 0.005;         // a candidate whose whole likeness drops more than this is UNSURE at best, never PASS
// Every search render (BASELINE and candidates) runs with HS_GUARDS=1 (scripts/hs/hs.py begin(): forces the helper
// guards on without editing build()), so a candidate is never compared with a baseline built under other helper rules.
// The tag is part of the baseline cache key and of each candidate's input stamp: a render made without it is stale.
export const GUARD_ENV = { HS_GUARDS: "1" };
export const GUARD_TAG = "HS_GUARDS=1";
export const rel = (p) => path.relative(ROOT, p).replace(/\\/g, "/");
export const norm = (s) => s.replace(/\r\n/g, "\n");
export const sha = (s) => crypto.createHash("sha1").update(norm(s)).digest("hex").slice(0, 12);
export const stampOf = (src) => sha(norm(src) + "\n#" + GUARD_TAG);
export const readJson = (f) => JSON.parse(fs.readFileSync(f, "utf8"));
export const baselineBuild = (subject) => path.join(ROOT, "out", "blender-hs", subject, "build.py");

// ---------- render pool ----------
/** one part_pass.py run (run_pass.py + ID pass) of `buildFile` into `outDir`; resolves {code, secs} */
export function renderOne(subject, buildFile, outDir, timeoutMs = 20 * 60 * 1000) {
  fs.mkdirSync(outDir, { recursive: true });
  return new Promise((res) => {
    const t0 = Date.now(), log = fs.openSync(path.join(outDir, "run.log"), "w");
    const p = spawn(BLENDER, ["-b", "--factory-startup", "--python-exit-code", "1", "--python", "scripts/hs/score/part_pass.py", "--",
      "--subject", subject, "--build", rel(buildFile), "--out-dir", rel(outDir)], { cwd: ROOT, stdio: ["ignore", log, log],
      env: { ...process.env, ...GUARD_ENV } });
    const to = setTimeout(() => p.kill(), timeoutMs);
    p.on("close", (code) => { clearTimeout(to); fs.closeSync(log); res({ code, secs: (Date.now() - t0) / 1000 }); });
    p.on("error", () => { clearTimeout(to); fs.closeSync(log); res({ code: -1, secs: 0 }); });
  });
}
/** "GUARD_WARN ..." lines a guarded render printed (part_pass.py prints hs.GUARD_WARN after the build) */
export function guardWarnings(dir) {
  try { return fs.readFileSync(path.join(dir, "run.log"), "utf8").split(/\r?\n/).filter((l) => l.startsWith("GUARD_WARN ")).map((l) => l.slice(11)); }
  catch { return []; }
}
/** run async task fns with at most `jobs` at a time (max 4 Blender processes) */
export async function pool(tasks, jobs = 4) {
  const out = new Array(tasks.length); let i = 0;
  await Promise.all(Array.from({ length: Math.min(4, jobs, tasks.length) }, async () => {
    while (i < tasks.length) { const k = i++; out[k] = await tasks[k](); }
  }));
  return out;
}
export const rendered = (dir) => fs.existsSync(path.join(dir, "pass0_ids.json")) && fs.existsSync(path.join(dir, "pass0_stats.json"));

/** BASELINE = the subject's current out/blender-hs/<s>/build.py, rendered with HS_GUARDS=1; cached in
 *  out/search/<s>/_baseline/<sha>-g/ and reused while build.py is unchanged (the older unguarded <sha>/ caches are not
 *  used any more). {dir, hash, src, cached}; renderBaseline() fills it when !cached. */
export function baselineInfo(subject) {
  const src = norm(fs.readFileSync(baselineBuild(subject), "utf8")), h = sha(src);
  const dir = path.join(SEARCH, subject, "_baseline", `${h}-g`);
  return { dir, hash: h, src, cached: rendered(dir) };
}
export async function renderBaseline(info, subject) {
  fs.mkdirSync(info.dir, { recursive: true });
  fs.writeFileSync(path.join(info.dir, "build.py"), info.src);
  const r = await renderOne(subject, path.join(info.dir, "build.py"), info.dir);
  if (r.code !== 0 || !rendered(info.dir)) throw new Error(`baseline render failed (exit ${r.code}); see ${rel(path.join(info.dir, "run.log"))}`);
  fs.writeFileSync(path.join(info.dir, "timing.json"), JSON.stringify({ secs: r.secs }));
  return r.secs;
}
export async function ensureBaseline(subject, log = console.log) {
  const info = baselineInfo(subject);
  if (!info.cached) { log(`baseline: rendering ${subject} build.py (${info.hash}) ...`); info.secs = await renderBaseline(info, subject); }
  else info.secs = fs.existsSync(path.join(info.dir, "timing.json")) ? readJson(path.join(info.dir, "timing.json")).secs : null;
  return info;
}

// ---------- build.py parsing ----------
/** finish(bm, "<object name>", [mats], "<role>") calls -> [{name, role, fn}] (fn = enclosing top-level def, if any) */
export function finishCalls(src) {
  src = norm(src);
  const out = [], re = /finish\(\s*\w+\s*,\s*["']([^"']+)["']\s*,\s*\[[^\]]*\]\s*,\s*["']([^"']+)["']/g;
  const blocks = topBlocks(src);
  let m;
  while ((m = re.exec(src))) {
    const b = blocks.find((x) => m.index >= x.start && m.index < x.end);
    out.push({ name: m[1], role: m[2], fn: b && b.kind === "def" ? b.name : null });
  }
  return out;
}
/** top-level blocks of a python file: {name, kind: def|class|assign|other, text, start, end}. Continuation = indented /
 *  closing-bracket / blank lines and triple-quoted strings. */
export function topBlocks(src) {
  src = norm(src);
  const lines = src.split("\n"), blocks = []; let cur = null, off = 0, inTri = false;
  const open = (name, kind, i, o) => { cur = { name, kind, start: o, lines: [] }; blocks.push(cur); cur.lines.push(lines[i]); };
  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i], o = off; off += ln.length + 1;
    let started = false;
    if (!inTri) {
      let m;
      if ((m = /^(?:async\s+)?def\s+(\w+)/.exec(ln))) { open(m[1], "def", i, o); started = true; }
      else if ((m = /^class\s+(\w+)/.exec(ln))) { open(m[1], "class", i, o); started = true; }
      else if ((m = /^([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*=[^=]/.exec(ln))) { open(m[1].replace(/\s+/g, ""), "assign", i, o); started = true; }
      else if (/^[^\s)\]}#]/.test(ln)) { open(`<${blocks.length}>`, "other", i, o); started = true; }
    }
    if (!started && cur) cur.lines.push(ln);
    const n = (ln.match(/"""|'''/g) || []).length;
    if (n % 2) inTri = !inTri;
  }
  for (const b of blocks) { b.text = b.lines.join("\n").replace(/\n+$/, ""); b.end = b.start + b.text.length; delete b.lines; }
  return blocks;
}
/** names of top-level blocks that differ between two build sources */
export function changedBlocks(baseSrc, candSrc) {
  const a = new Map(topBlocks(baseSrc).map((b) => [b.name, b.text])), c = new Map(topBlocks(candSrc).map((b) => [b.name, b.text]));
  const out = [];
  for (const [k, t] of c) if (!a.has(k) || a.get(k) !== t) out.push(k);
  for (const k of a.keys()) if (!c.has(k)) out.push(k);
  return out;
}
/** part (role or object name) -> {role, objects:[names], fns:[def names]} using the baseline source */
export function resolvePart(src, part, roles) {
  const calls = finishCalls(src);
  let role = roles.includes(part) ? part : null;
  if (!role) { const c = calls.find((x) => x.name === part); if (c) role = c.role; }
  if (!role) throw new Error(`part "${part}" is neither a role (${roles.join(", ")}) nor an object name (${[...new Set(calls.map((c) => c.name))].join(", ")})`);
  const mine = calls.filter((c) => c.role === role);
  return { role, objects: [...new Set(mine.map((c) => c.name))], fns: [...new Set(mine.map((c) => c.fn).filter(Boolean))] };
}
export function objectRoles(src) { return Object.fromEntries(finishCalls(src).map((c) => [c.name, c.role])); }

// ---------- ID maps / crops ----------
const IDW = 1024;
/** canvas-px bbox [x0,y0,x1,y1] of a role's visible pixels in each view of the ID pass, concept included (null when absent) */
export function roleBBox(dir, role) {
  const meta = readJson(path.join(dir, "pass0_ids.json")), k = meta.parts.indexOf(role) + 1, out = {};
  for (const v of Object.keys(meta.views)) {
    out[v] = null; if (!k) continue;
    const V = meta.views[v], b = fs.readFileSync(path.join(dir, V.file));
    let x0 = V.w, y0 = V.h, x1 = -1, y1 = -1, n = 0;
    for (let y = 0; y < V.h; y++) for (let x = 0; x < V.w; x++) if (b[y * V.w + x] === k) { n++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    if (n >= 48) out[v] = [x0, y0, x1, y1];
  }
  return out;
}
export const unionBox = (boxes) => boxes.filter(Boolean).reduce((a, b) => a ? [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])] : b, null);
export const turnaroundFile = (subject, v) => path.join(ROOT, "subjects", subject, "turnaround", `${v}.png`);

/** crop `file` at canvas box [x0,y0,x1,y1] (+pad), flatten on white, scale to fit maxDim -> PNG buffer {buf,w,h} */
export async function cropBuf(file, box, shift = [0, 0], pad = 12, maxDim = 420, minScale = 1, maxScale = 6) {
  const x0 = Math.max(0, Math.min(IDW - 2, box[0] - pad + shift[0])), y0 = Math.max(0, Math.min(IDW - 2, box[1] - pad + shift[1]));
  const x1 = Math.min(IDW - 1, box[2] + pad + shift[0]), y1 = Math.min(IDW - 1, box[3] + pad + shift[1]);
  const w = x1 - x0 + 1, h = y1 - y0 + 1, sc = Math.max(minScale, Math.min(maxScale, maxDim / Math.max(w, h)));
  const W = Math.max(1, Math.round(w * sc)), H = Math.max(1, Math.round(h * sc));
  const buf = await sharp(file).flatten({ background: "#ffffff" }).extract({ left: x0, top: y0, width: w, height: h })
    .resize(W, H, { kernel: "lanczos3" }).png().toBuffer();
  return { buf, w: W, h: H, scale: sc };
}
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
export function label(text, w, h, { size = 15, fill = "#111", bg = "#eceff3", bold = false } = {}) {
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="${bg}"/>` +
    `<text x="6" y="${Math.round(h / 2 + size * 0.35)}" font-family="Arial, Segoe UI, sans-serif" font-size="${size}" font-weight="${bold ? 700 : 400}" fill="${fill}">${esc(text)}</text></svg>`);
}
export async function textPng(text, w, h, opts) { return sharp(label(text, w, h, opts)).png().toBuffer(); }
