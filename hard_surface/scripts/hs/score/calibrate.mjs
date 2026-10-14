// Calibration of likeness_score.mjs against the expert ground truth that exists (see CALIBRATION.md):
//   J: out/blender-hs-exp/_judge (9 builds, 3 weapons x 3 variants, Opus rubric + overall /10)
//   R: out/blender-hs/<s>/review_fable.md (one blind review per subject: likeness /10 of the reviewed pass)
// Writes out/score/items.json (ground truth + baseline agree), out/score/features.json (cached signals),
// out/score/calibration.json (correlations). Re-run with --rescore to recompute features.
//   node scripts/hs/score/calibrate.mjs [--rescore]
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { ROOT, VIEWS, SIGNALS, WEIGHTS, combine, scoreFiles } from "./likeness_score.mjs";

const OUT = path.join(ROOT, "out", "score");
fs.mkdirSync(OUT, { recursive: true });
const HS = path.join(ROOT, "out", "blender-hs"), EXP = path.join(ROOT, "out", "blender-hs-exp");
const md5 = (f) => crypto.createHash("md5").update(fs.readFileSync(f)).digest("hex");
const readJ = (f) => JSON.parse(fs.readFileSync(f, "utf8"));

function passStatsBySide(dir, sidePng) {   // the passN_stats.json whose passN_side.png is byte-identical to sidePng
  const h = md5(sidePng);
  const passes = fs.readdirSync(dir).map((f) => f.match(/^pass(\d+)_side\.png$/)).filter(Boolean).map((m) => +m[1]).sort((a, b) => b - a);
  for (const p of passes) if (md5(path.join(dir, `pass${p}_side.png`)) === h && fs.existsSync(path.join(dir, `pass${p}_stats.json`))) return { pass: p, stats: readJ(path.join(dir, `pass${p}_stats.json`)) };
  if (fs.existsSync(path.join(dir, "side.png")) && md5(path.join(dir, "side.png")) === h && fs.existsSync(path.join(dir, "stats.json"))) return { pass: "final", stats: readJ(path.join(dir, "stats.json")) };
  return null;
}
function agreeOf(stats) {
  const sc = stats.scores, o = VIEWS.map((v) => sc[v].agree);
  return { agree4: o.reduce((a, b) => a + b, 0) / 4, agreeMin4: Math.min(...o), agreeConcept: sc.concept?.agree ?? null,
    agree5: (o.reduce((a, b) => a + b, 0) + (sc.concept?.agree ?? 0)) / 5 };
}

function items() {
  const out = [];
  // J set
  const key = readJ(path.join(EXP, "_key", "key.json")), ver = readJ(path.join(EXP, "_judge", "verdict_opus.json"));
  for (const [id, who] of Object.entries(key)) {
    const [s, letter] = id.split("/"), jdir = path.join(EXP, "_judge", s, letter);
    const src = who === "existing" ? path.join(HS, s) : path.join(EXP, who, s);
    const m = passStatsBySide(src, path.join(jdir, "side.png"));
    if (!m) throw new Error(`no stats for ${id}`);
    out.push({ set: "J", id, subject: s, group: s, who, gt: ver[id].overall, rubric: ver[id].scores,
      files: Object.fromEntries(VIEWS.map((v) => [v, path.join(jdir, `${v}.png`)])), pass: m.pass, ...agreeOf(m.stats) });
  }
  // R set
  for (const s of fs.readdirSync(HS).sort()) {
    const rf = path.join(HS, s, "review_fable.md");
    if (!fs.existsSync(rf)) continue;
    const txt = fs.readFileSync(rf, "utf8"), head = txt.split("\n").slice(0, 8).join("\n");
    const lm = txt.match(/Likeness score:\**\s*\**([0-9.]+)/);
    if (!lm) continue;
    const reviewer = /fable/i.test(txt.split("\n")[0]) ? "fable" : /gpt|astra/i.test(head) ? "gpt-astra" : "unknown";
    let pass = null, how = "header";
    const pm = head.match(/keeper\s*(?:pass\s*)?:?\s*(?:pass\s*)?(\d+)/i) || head.match(/pass\s+(\d+)/i);
    if (pm) pass = +pm[1];
    if (pass == null || !fs.existsSync(path.join(HS, s, `pass${pass}_side.png`))) {   // newest pass rendered before the review
      how = "mtime"; const t = fs.statSync(rf).mtimeMs; let best = null;
      for (const f of fs.readdirSync(path.join(HS, s))) { const m = f.match(/^pass(\d+)_side\.png$/); if (!m) continue;
        const ft = fs.statSync(path.join(HS, s, f)).mtimeMs; if (ft <= t && (!best || ft > best.t)) best = { p: +m[1], t: ft }; }
      pass = best?.p ?? null;
    }
    const st = path.join(HS, s, `pass${pass}_stats.json`);
    if (pass == null || !fs.existsSync(st)) { console.error(`skip ${s}: no pass`); continue; }
    out.push({ set: "R", id: s, subject: s, group: reviewer, reviewer, gt: +lm[1], pass, passFrom: how,
      files: Object.fromEntries(VIEWS.map((v) => [v, path.join(HS, s, `pass${pass}_${v}.png`)])), ...agreeOf(readJ(st)) });
  }
  return out;
}

// ---------- statistics ----------
function ranks(a) {
  const idx = a.map((v, i) => [v, i]).sort((x, y) => x[0] - y[0]), r = new Array(a.length);
  for (let i = 0; i < idx.length;) { let j = i; while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
    for (let k = i; k <= j; k++) r[idx[k][1]] = (i + j) / 2 + 1; i = j + 1; }
  return r;
}
function pearson(x, y) {
  const n = x.length, mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0, syy = 0; for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; }
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : 0;
}
const spearman = (x, y) => pearson(ranks(x), ranks(y));
/** exact-ish permutation p (two-sided) for spearman, deterministic LCG */
function permP(x, y, iters = 20000) {
  const r0 = Math.abs(spearman(x, y)); let seed = 12345, hit = 0; const yy = [...y];
  const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  for (let t = 0; t < iters; t++) { for (let i = yy.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [yy[i], yy[j]] = [yy[j], yy[i]]; }
    if (Math.abs(spearman(x, yy)) >= r0 - 1e-12) hit++; }
  return (hit + 1) / (iters + 1);
}
/** within-group pairwise concordance: pairs inside each group with distinct gt, how many the metric orders the same way */
function concordance(items, f) {
  const g = {}; for (const it of items) (g[it.group] ??= []).push(it);
  let c = 0, d = 0, t = 0;
  for (const list of Object.values(g)) for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
    const a = list[i], b = list[j]; if (a.gt === b.gt) continue;
    const s = Math.sign((f(a) - f(b)) * (a.gt - b.gt)); if (s > 0) c++; else if (s < 0) d++; else t++; }
  return { concordant: c, discordant: d, tied: t };
}

// ---------- main ----------
const argv = process.argv.slice(2);
const list = items();
fs.writeFileSync(path.join(OUT, "items.json"), JSON.stringify(list, null, 1));
const fcache = path.join(OUT, "features.json");
let feats = fs.existsSync(fcache) && !argv.includes("--rescore") ? readJ(fcache) : {};
for (const it of list) {
  const k = `${it.set}:${it.id}`;
  if (feats[k]) continue;
  const c0 = process.cpuUsage();
  const r = await scoreFiles(it.subject, it.files);
  const c = process.cpuUsage(c0);
  feats[k] = { views: r.views, cpuMs: (c.user + c.system) / 1000 };
  console.error(`${k} cpu ${(feats[k].cpuMs / 1000).toFixed(2)} s`);
  fs.writeFileSync(fcache, JSON.stringify(feats));
}

// candidate scalars per item
const VIEW_SIG = [...SIGNALS, "edgeRecall", "edgePrecision", "openRecall", "openPrecision", "iou", "iou0"];
function scalars(it) {
  const v = feats[`${it.set}:${it.id}`].views, o = { agree4: it.agree4, agreeMin4: it.agreeMin4, agree5: it.agree5 };
  for (const s of VIEW_SIG) { const xs = VIEWS.map((w) => v[w][s] ?? 0); o[s] = xs.reduce((a, b) => a + b, 0) / 4; o[`${s}_min`] = Math.min(...xs); o[`${s}_side`] = v.side[s] ?? 0; }
  const cmb = combine(v);
  o.interior = cmb.interior; o.interiorEq = cmb.interiorEq; o.likeness = cmb.likeness;
  o.likeness_x_agree = cmb.interior * it.agree4;
  return o;
}
const rows = list.map((it) => ({ it, x: scalars(it) }));
const metrics = Object.keys(rows[0].x);
const sets = { J: rows.filter((r) => r.it.set === "J"), R: rows.filter((r) => r.it.set === "R"),
  R_fable: rows.filter((r) => r.it.set === "R" && r.it.reviewer === "fable"), R_gpt: rows.filter((r) => r.it.set === "R" && r.it.reviewer === "gpt-astra") };
const table = {};
for (const m of metrics) {
  table[m] = {};
  for (const [name, rs] of Object.entries(sets)) {
    const x = rs.map((r) => r.x[m]), y = rs.map((r) => r.it.gt);
    table[m][name] = { n: rs.length, rho: spearman(x, y), p: permP(x, y, 5000) };
  }
  table[m].J_within = concordance(sets.J.map((r) => ({ ...r.it, x: r.x })), (a) => a.x[m]);
}

// leave-one-out fitted weights over the 5 interior signals (non-negative grid, simplex step 0.1), objective = spearman
// on the training fold of the pooled J+R set; reports the held-out prediction's rank correlation
function grid(k, step = 0.1) { const out = []; const rec = (pre, left) => { if (pre.length === k - 1) { out.push([...pre, left]); return; }
  for (let w = 0; w <= left + 1e-9; w += step) rec([...pre, Math.round(w * 10) / 10], Math.round((left - w) * 10) / 10); }; rec([], 1); return out; }
const G = grid(SIGNALS.length);
const wscore = (r, w) => { const v = feats[`${r.it.set}:${r.it.id}`].views; const o = {}; SIGNALS.forEach((s, i) => (o[s] = w[i])); return combine(v, o).interior * r.it.agree4; };
function loo(rs) {
  const pred = [];
  for (let i = 0; i < rs.length; i++) {
    const tr = rs.filter((_, j) => j !== i);
    let best = null; for (const w of G) { if (w.every((x) => x === 0)) continue; const rho = spearman(tr.map((r) => wscore(r, w)), tr.map((r) => r.it.gt)); if (!best || rho > best.rho) best = { rho, w }; }
    pred.push({ i, w: best.w });
  }
  // held-out: rank of each item's score under its own fold's weights, compared on the common scale (z within fold is
  // not available for a single item, so the raw score is used — all folds share the same formula family)
  const x = pred.map((p) => wscore(rs[p.i], p.w)), y = rs.map((r) => r.it.gt);
  return { rho: spearman(x, y), p: permP(x, y, 5000), weights: pred.map((p) => p.w) };
}
const pooled = [...sets.J, ...sets.R];
const fitAll = (() => { let best = null; for (const w of G) { if (w.every((x) => x === 0)) continue; const rho = spearman(pooled.map((r) => wscore(r, w)), pooled.map((r) => r.it.gt)); if (!best || rho > best.rho) best = { rho, w }; } return best; })();
const looRes = loo(pooled);

const res = { n: Object.fromEntries(Object.entries(sets).map(([k, v]) => [k, v.length])), apriori_weights: WEIGHTS, table,
  fit_in_sample: { signals: SIGNALS, ...fitAll }, loo_pooled: { rho: looRes.rho, p: looRes.p, weight_spread: SIGNALS.map((_, k) => [Math.min(...looRes.weights.map((w) => w[k])), Math.max(...looRes.weights.map((w) => w[k]))]) },
  items: rows.map((r) => ({ id: `${r.it.set}:${r.it.id}`, who: r.it.who ?? r.it.reviewer, pass: r.it.pass, passFrom: r.it.passFrom, gt: r.it.gt,
    agree4: r.x.agree4, likeness: r.x.likeness, interior: r.x.interior, edgeF1: r.x.edgeF1, ssim: r.x.ssim, toneSim: r.x.toneSim, colourSim: r.x.colourSim, openF1: r.x.openF1 })),
  cpuMsPerBuild: Object.values(feats).map((f) => f.cpuMs) };
fs.writeFileSync(path.join(OUT, "calibration.json"), JSON.stringify(res, (k, v) => (typeof v === "number" ? Math.round(v * 1e4) / 1e4 : v), 1));

const f2 = (x) => (x >= 0 ? " " : "") + x.toFixed(2);
console.log(`n: ${JSON.stringify(res.n)}`);
console.log("metric                 J rho (p)      R rho (p)      R_fable        R_gpt          J within c/d");
const show = ["agree4", "agreeMin4", "agree5", "iou", "iou0", "likeness", "likeness_x_agree", "interior", "interiorEq", ...SIGNALS, "edgeRecall", "edgePrecision", "openRecall", "openPrecision",
  ...SIGNALS.map((s) => `${s}_min`), ...SIGNALS.map((s) => `${s}_side`)];
for (const m of show) { const t = table[m];
  console.log(`${m.padEnd(22)} ${["J", "R", "R_fable", "R_gpt"].map((k) => `${f2(t[k].rho)} (${t[k].p.toFixed(2)})`).join("   ")}   ${t.J_within.concordant}/${t.J_within.discordant}`); }
console.log(`fit in-sample (pooled J+R, interior*agree4): rho ${fitAll.rho.toFixed(3)} w ${JSON.stringify(fitAll.w)} (${SIGNALS.join(",")})`);
console.log(`LOO pooled: rho ${looRes.rho.toFixed(3)} p ${looRes.p.toFixed(3)}  weight ranges ${JSON.stringify(res.loo_pooled.weight_spread)}`);
