// Rank candidate variants of ONE part by the per-part likeness score (scripts/hs/score/part_score.mjs).
//
//   node scripts/hs/search/part_search.mjs --subject <s> --part <role|object name> --variants <dir> [--jobs 4] [--force]
//        [--crop <view>:<x0>,<y0>,<x1>,<y1> ...]     (override the top.png crop box of a view, 1024 canvas px)
//        [--combine v01,v04 ...]                     (merge winners' edits of the part into x<NN>.py first; see 0.)
//        [--no-concept]                              (score the four orthos only)
//
// <dir> holds v01.py .. vNN.py: each a full copy of out/blender-hs/<s>/build.py with ONLY the part's function changed
// (and x01.py .. made by --combine).
// 0. --combine v01,v04 (repeatable; 2+ candidates each): a 3-way text merge (git merge-file) of the candidates' edits
//    against the BASELINE build.py, written to <dir>/x<NN>.py (next free number; combos.json records the sources). The
//    edits must touch different lines: a conflict writes <dir>/x<NN>.conflict.py with the markers and stops (exit 3);
//    resolve it by hand into x<NN>.py (only the part's function changed), or brief one seat to write the combination as
//    a new v<NN>.py. A combination is gated and ranked like any candidate.
// 1. BASELINE = the subject's current build.py, rendered once with HS_GUARDS=1 (part_pass.py) and cached in
//    out/search/<s>/_baseline/<sha>-g/. Every candidate is rendered with HS_GUARDS=1 too (lib.mjs GUARD_ENV), so both
//    sides use the same helper rules without editing build(); each render's GUARD_WARN lines are listed in ranking.md.
// 2. Every candidate is rendered into <dir>/vNN/ (part_pass.py, at most 4 Blender processes; a candidate whose file is
//    unchanged and already rendered is skipped; --force re-renders). Nothing is written to the subject folder.
// 3. Gate per candidate (rejected ones are not scored, so they cannot change the shared region): render ok, tris <= budget,
//    topology all zero, no ortho view > 0.04 below the subject's best pass (run_pass's own gate), same object set as the
//    baseline, no other part's pixels changed (ID pass).
// 4. All passing candidates + BASELINE are scored in ONE part_score call (shared region, baseline's registration shift).
//    |delta| < 0.004 = tie, ties go to BASELINE (PART-CALIBRATION.md). Whole-score guard: a candidate whose whole
//    likeness drops more than WHOLE_GUARD (0.005) is UNSURE at best, never PASS, and is never promoted.
//    The part score includes the concept view where its per-part alignment holds (part_score.mjs); ranking.md reports
//    the part region's mean L* (source vs candidate) so a value overshoot is visible.
// Writes <dir>/ranking.json, ranking.md, top.png (rows = views the part is visible in, columns = SOURCE | BASELINE | best 3).
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import sharp from "sharp";
import { loadCandidate, scorePart, SIGNAL_KEYS } from "../score/part_score.mjs";
import {
  ROOT, VIEWS, TIE, WHOLE_GUARD, GUARD_TAG, stampOf, guardWarnings, rel, norm, sha, readJson, rendered, renderOne, renderBaseline, baselineInfo, pool, topBlocks, changedBlocks,
  resolvePart, objectRoles, roleBBox, unionBox, turnaroundFile, cropBuf, textPng,
} from "./lib.mjs";

const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
const subject = arg("--subject"), part = arg("--part"), vdir = arg("--variants") && path.resolve(arg("--variants"));
if (!subject || !part || !vdir) {
  console.error("usage: node scripts/hs/search/part_search.mjs --subject <s> --part <role|object> --variants <dir> [--jobs 4] [--force] [--crop view:x0,y0,x1,y1]");
  process.exit(2);
}
const jobs = Math.min(4, Number(arg("--jobs")) || 4), force = argv.includes("--force");
const cropOverride = Object.fromEntries(argv.flatMap((a, i) => (a === "--crop" ? [argv[i + 1]] : [])).map((s) => {
  const [v, b] = s.split(":"); return [v, b.split(",").map(Number)];
}));
const combos = argv.flatMap((a, i) => (a === "--combine" ? [argv[i + 1].split(",").map((x) => x.trim().replace(/\.py$/, ""))] : []));
const useConcept = !argv.includes("--no-concept");
const T0 = Date.now();
const f4 = (x) => (x === null || x === undefined ? "-" : (x >= 0 ? "+" : "") + x.toFixed(4));
const f3 = (x) => (x === null || x === undefined ? "-" : x.toFixed(3));

// ---------- --combine: 3-way merge of candidates' edits into x<NN>.py ----------
if (combos.length) {
  const baseSrc = baselineInfo(subject).src, tmp = path.join(vdir, "_combine");
  fs.mkdirSync(tmp, { recursive: true });
  const cj = path.join(vdir, "combos.json"), log = fs.existsSync(cj) ? readJson(cj) : {};
  const nm = (k) => `x${String(k).padStart(2, "0")}`;
  for (const list of combos) {
    if (list.length < 2) { console.error(`--combine needs 2+ candidates: ${list}`); process.exit(2); }
    const key = list.join("+");
    let name = Object.keys(log).find((k) => log[k].from.join("+") === key);
    if (!name) { let k = 1; while (fs.existsSync(path.join(vdir, nm(k) + ".py")) || log[nm(k)]) k++; name = nm(k); }
    fs.writeFileSync(path.join(tmp, "base.py"), baseSrc);
    // each seat's "# vNN: hypothesis" line sits at the same spot (under the def) and would always conflict: drop them
    // from the merge, keep them in combos.json
    const HYP = /^[ \t]*# [vx]\d+: .*\n/gm, hyp = {};
    const readC = (n) => { const t = norm(fs.readFileSync(path.join(vdir, n + ".py"), "utf8")); hyp[n] = (t.match(HYP) || []).map((l) => l.trim()); return t.replace(HYP, ""); };
    let cur = readC(list[0]);
    for (const other of list.slice(1)) {
      fs.writeFileSync(path.join(tmp, "cur.py"), cur);
      fs.writeFileSync(path.join(tmp, "other.py"), readC(other));
      const r = spawnSync("git", ["merge-file", "-p", "-L", list[0], "-L", "BASELINE", "-L", other, "cur.py", "base.py", "other.py"], { cwd: tmp, encoding: "utf8" });
      if (r.error || r.status === null || r.status < 0) { console.error(`git merge-file failed: ${r.error ?? r.stderr}`); process.exit(2); }
      if (r.status > 0) {
        fs.writeFileSync(path.join(vdir, name + ".conflict.py"), r.stdout);
        console.error(`--combine ${key}: ${r.status} conflict(s) merging ${other}; markers in ${rel(path.join(vdir, name + ".conflict.py"))}. ` +
          `Resolve by hand into ${name}.py (keep only the part's function changed) and run again without --combine.`);
        process.exit(3);
      }
      cur = r.stdout;
    }
    const out = path.join(vdir, name + ".py");
    if (!fs.existsSync(out) || norm(fs.readFileSync(out, "utf8")) !== cur) fs.writeFileSync(out, cur);
    log[name] = { from: list, hypotheses: hyp, made: new Date().toISOString() };
    console.log(`--combine ${key} -> ${rel(out)}`);
  }
  fs.writeFileSync(cj, JSON.stringify(log, null, 1));
  fs.rmSync(tmp, { recursive: true, force: true });
}

// ---------- candidates ----------
const files = fs.readdirSync(vdir).filter((f) => /^[vx]\d+\.py$/.test(f)).sort();
if (!files.length) { console.error(`no v<NN>.py in ${vdir}`); process.exit(2); }
const base = baselineInfo(subject);
const cands = files.map((f) => {
  const name = f.replace(/\.py$/, ""), dir = path.join(vdir, name), src = norm(fs.readFileSync(path.join(vdir, f), "utf8"));
  const stamp = path.join(dir, "input.sha");
  const fresh = !force && rendered(dir) && fs.existsSync(stamp) && fs.readFileSync(stamp, "utf8") === stampOf(src);
  return { name, dir, src, fresh, secs: null, row: {} };
});

// ---------- render (baseline + stale candidates, <= 4 Blender at once) ----------
const tasks = [];
if (!base.cached) tasks.push(async () => { console.log(`baseline: rendering (${base.hash})`); base.secs = await renderBaseline(base, subject); });
for (const c of cands) {
  if (c.fresh) { c.secs = fs.existsSync(path.join(c.dir, "timing.json")) ? readJson(path.join(c.dir, "timing.json")).secs : null; continue; }
  tasks.push(async () => {
    fs.rmSync(c.dir, { recursive: true, force: true });
    fs.mkdirSync(c.dir, { recursive: true });
    fs.writeFileSync(path.join(c.dir, "build.py"), c.src);
    const r = await renderOne(subject, path.join(c.dir, "build.py"), c.dir);
    c.secs = r.secs; c.exit = r.code;
    fs.writeFileSync(path.join(c.dir, "timing.json"), JSON.stringify({ secs: r.secs }));
    if (r.code === 0 && rendered(c.dir)) fs.writeFileSync(path.join(c.dir, "input.sha"), stampOf(c.src));
    console.log(`${c.name}: render exit ${r.code} ${r.secs.toFixed(0)} s`);
  });
}
console.log(`${tasks.length} render(s), ${jobs} Blender at a time (${cands.filter((c) => c.fresh).length} candidate(s) cached)`);
const tRender0 = Date.now();
await pool(tasks, jobs);
const renderWall = (Date.now() - tRender0) / 1000;
const baseDir = base.dir;
if (!base.secs && fs.existsSync(path.join(baseDir, "timing.json"))) base.secs = readJson(path.join(baseDir, "timing.json")).secs;

// ---------- resolve the part ----------
const baseMeta = readJson(path.join(baseDir, "pass0_ids.json"));
const P = resolvePart(base.src, part, baseMeta.parts);
const role = P.role;
const roleOfObj = objectRoles(base.src);
const baseStats = readJson(path.join(baseDir, "pass0_stats.json"));
const baseObjs = Object.keys(baseStats.topology.objects).sort();

// ---------- gate ----------
function idPixelsOutside(cDir, cMeta) {
  // pixels whose visible role changed where neither the baseline nor the candidate shows the edited role: another part moved
  const k0 = baseMeta.parts.indexOf(role) + 1, k1 = cMeta.parts.indexOf(role) + 1, hit = {};
  let n = 0;
  for (const v of VIEWS) {
    const a = fs.readFileSync(path.join(baseDir, baseMeta.views[v].file)), b = fs.readFileSync(path.join(cDir, cMeta.views[v].file));
    if (a.length !== b.length) return { n: 1e9, roles: ["(size)"] };
    for (let i = 0; i < a.length; i++) {
      if (a[i] === b[i] || a[i] === k0 || b[i] === k1) continue;
      n++; const r = a[i] ? baseMeta.parts[a[i] - 1] : "(bg)"; hit[r] = (hit[r] || 0) + 1;
    }
  }
  return { n, roles: Object.keys(hit) };
}
for (const c of cands) {
  const reasons = [];
  if (!rendered(c.dir)) {
    let tail = "";
    try { tail = fs.readFileSync(path.join(c.dir, "run.log"), "utf8").trim().split("\n").filter((l) => /Error|error|Traceback|assert/i.test(l)).slice(-2).join(" | "); } catch {}
    reasons.push(`render failed${c.exit !== undefined ? ` (exit ${c.exit})` : ""}${tail ? `: ${tail.slice(0, 160)}` : ""}`);
    c.gate = { pass: false, reasons }; continue;
  }
  const st = readJson(path.join(c.dir, "pass0_stats.json")), meta = readJson(path.join(c.dir, "pass0_ids.json"));
  const g = st.gate || {};
  if (!(st.tris <= st.budget)) reasons.push(`tris ${st.tris} > budget ${st.budget}`);
  if (!st.topology_clean) reasons.push(`topology ${JSON.stringify(Object.fromEntries(Object.entries(st.topology.totals).filter(([, v]) => v)))}`);
  if (g.below_best_earlier && Object.keys(g.below_best_earlier).length) reasons.push(`ortho view drop > 0.04: ${JSON.stringify(g.below_best_earlier)}`);
  const objs = Object.keys(st.topology.objects).sort();
  if (objs.join() !== baseObjs.join()) reasons.push(`object set changed (+${objs.filter((o) => !baseObjs.includes(o))} -${baseObjs.filter((o) => !objs.includes(o))})`);
  if (!meta.parts.includes(role)) reasons.push(`role ${role} missing`);
  const changedObjs = objs.filter((o) => baseStats.topology.objects[o] && baseStats.topology.objects[o].tris !== st.topology.objects[o].tris);
  const out = reasons.length ? { n: 0, roles: [] } : idPixelsOutside(c.dir, meta);
  if (out.n > 8) reasons.push(`other parts changed: ${out.roles.join(",")} (${out.n} px)`);
  const blocks = changedBlocks(base.src, c.src), fnOfPart = new Set(P.fns);
  c.gate = { pass: reasons.length === 0, reasons, tris: st.tris, trisDelta: st.tris - baseStats.tris, changedObjects: changedObjs, changedBlocks: blocks,
    outsideEdit: blocks.filter((b) => !fnOfPart.has(b)) };
}

// ---------- score (one call: baseline + every passing candidate) ----------
const passing = cands.filter((c) => c.gate.pass);
const B = await loadCandidate(subject, baseDir);
for (const c of passing) c.loaded = await loadCandidate(subject, c.dir, "pass0_", B);
const scored = await scorePart(subject, [B, ...passing.map((c) => c.loaded)], role, { concept: useConcept });
if (scored[0].score === null) throw new Error(`role ${role}: no visible pixels in the baseline`);
const bs = scored[0];
passing.forEach((c, i) => { c.s = scored[i + 1]; });

const viewWeights = (s) => Object.fromEntries(Object.entries(s.views).map(([v, x]) => [v, x.px]));
const rows = cands.map((c) => {
  const r = { candidate: c.name, file: rel(path.join(vdir, c.name + ".py")), gate: c.gate.pass ? "ok" : "REJECT", gateReasons: c.gate.reasons,
    tris: c.gate.tris ?? null, changedObjects: c.gate.changedObjects ?? [], changedBlocks: c.gate.changedBlocks ?? [], renderSecs: c.secs };
  r.guardWarn = rendered(c.dir) ? guardWarnings(c.dir) : [];
  if (c.gate.outsideEdit?.length) r.warn = `changed outside the part's function(s) (${P.fns.join(",")}): ${c.gate.outsideEdit.join(", ")}`;
  if (c.s) {
    const d = c.s.score - bs.score;
    const wd = c.s.whole - bs.whole, wholeGuard = d >= TIE && wd < -WHOLE_GUARD;
    Object.assign(r, { score: c.s.score, delta: d, wholeDelta: wd, tie: Math.abs(d) < TIE, wholeGuard,
      verdict: wholeGuard ? "UNSURE" : d >= TIE ? "PASS" : d <= -TIE ? "FAIL" : "UNSURE",
      meanLS: c.s.meanLS, meanLB: c.s.meanLB,
      signals: Object.fromEntries(SIGNAL_KEYS.map((k) => [k, c.s[k] === null || bs[k] === null ? null : c.s[k] - bs[k]])),
      views: Object.fromEntries(Object.entries(c.s.views).map(([v, x]) => [v, { score: x.score, delta: x.score - bs.views[v].score, regionPx: x.px,
        weight: x.weight, meanLS: x.meanLS, meanLB: x.meanLB }])) });
  } else r.verdict = "FAIL";
  return r;
});
// rank: ties collapse onto the baseline's score (baseline first among equals), rejected last
const eff = (r) => (r.score === undefined ? -Infinity : r.tie || r.wholeGuard ? bs.score : r.score);
const order = [{ candidate: "BASELINE", score: bs.score, delta: 0, wholeDelta: 0, tie: false, gate: "ok", base: true }, ...rows]
  .sort((a, b) => eff(b) - eff(a) || (b.base ? 1 : 0) - (a.base ? 1 : 0) || (b.score ?? -9) - (a.score ?? -9));
order.forEach((r, i) => { r.rank = r.score === undefined ? null : i + 1; });
const top3 = order.filter((r) => !r.base && r.score !== undefined).sort((a, b) => b.score - a.score).slice(0, 3);
const best = order.filter((r) => !r.base && r.verdict === "PASS").sort((a, b) => b.score - a.score)[0] ?? null;
const wall = (Date.now() - T0) / 1000, nRendered = tasks.length;
const summary = {
  subject, part, role, partObjects: P.objects, partFunctions: P.fns, tieThreshold: TIE, baselineHash: base.hash,
  guards: GUARD_TAG, wholeGuard: WHOLE_GUARD, concept: bs.concept,
  baseline: { score: bs.score, whole: bs.whole, regionPx: bs.regionPx, viewPx: viewWeights(bs), renderSecs: base.secs,
    meanLS: bs.meanLS, meanLB: bs.meanLB, guardWarn: guardWarnings(baseDir) },
  best: best ? { candidate: best.candidate, delta: best.delta } : null,
  decision: best ? `PROMOTE ${best.candidate} (part ${f4(best.delta)}, whole ${f4(best.wholeDelta)} vs baseline)`
    : `KEEP BASELINE (no candidate beat it by >= ${TIE} without a whole drop > ${WHOLE_GUARD})`,
  wallSecs: wall, renderWallSecs: renderWall, rendersRun: nRendered,
  perCandidateSecs: null,
  rows: order,
};
const rsecs = cands.map((c) => c.secs).filter(Boolean);
summary.perCandidateSecs = rsecs.length ? { mean: rsecs.reduce((a, b) => a + b, 0) / rsecs.length, max: Math.max(...rsecs) } : null;
fs.writeFileSync(path.join(vdir, "ranking.json"), JSON.stringify(summary, (k, v) => (typeof v === "number" ? Math.round(v * 1e5) / 1e5 : v), 1));

// ---------- ranking.md ----------
const md = [];
md.push(`# part_search: ${subject} / ${part}${part !== role ? ` (role ${role})` : ""}`, "",
  `Role \`${role}\` = objects ${P.objects.join(", ")} (functions ${P.fns.join(", ") || "?"}). Baseline part score ${f3(bs.score)}, whole likeness ${f3(bs.whole)}. ` +
  `Tie = |part delta| < ${TIE} (ties go to BASELINE); a whole delta < -${WHOLE_GUARD} caps the verdict at UNSURE. ` +
  `Registration shift = the baseline's for every candidate. Renders: ${GUARD_TAG} (baseline and candidates).`, "",
  `Concept view: ${bs.concept?.used ? `used, weight ${(bs.concept.weight / bs.regionPx).toFixed(2)} of the part score (local alignment on BASELINE: NCC ${bs.concept.align.ncc.toFixed(2)}, scale ${bs.concept.align.s.toFixed(2)}, shift ${bs.concept.align.tx},${bs.concept.align.ty} working px)` : `not used (${bs.concept?.reason ?? "-"})`}.`, "",
  "Mean L* (0..100) = the part region's mean lightness over each image's own foreground px, views weighted as the score; source first.", "",
  "| rank | candidate | part score | part delta | whole delta | mean L* src / cand | gate | tie | verdict |", "|---|---|---|---|---|---|---|---|---|");
const fL = (x) => (typeof x === "number" ? x.toFixed(1) : "-");
for (const r of order) {
  const mL = r.base ? `${fL(bs.meanLS)} / ${fL(bs.meanLB)}` : r.score === undefined ? "-" : `${fL(r.meanLS)} / ${fL(r.meanLB)}`;
  md.push(`| ${r.rank ?? "-"} | ${r.candidate} | ${f3(r.score)} | ${r.base ? "0 (baseline)" : f4(r.delta)} | ${r.base ? "0" : f4(r.wholeDelta)} | ${mL} | ${r.gate}${r.gate === "REJECT" ? ": " + r.gateReasons.join("; ").split("|").join("/") : ""} | ${r.base ? "-" : r.tie === undefined ? "-" : r.tie ? "tie" : "no"} | ${r.base ? "-" : r.verdict}${r.wholeGuard ? " (whole guard)" : ""} |`);
}
md.push("", `Decision: **${summary.decision}**.`, "");
const withViews = order.filter((r) => r.views);
if (withViews.length) {
  const VV = [...VIEWS, ...(bs.views.concept ? ["concept"] : [])];
  md.push("Per-view part delta (views weighted by region area, the concept by CONCEPT_W x area; a mixed sign means the source views disagree):", "",
    `| candidate | ${VV.join(" | ")} |`, `|---|${VV.map(() => "---").join("|")}|`);
  md.push(`| (mean L* src / BASELINE) | ${VV.map((v) => (bs.views[v] ? `${fL(bs.views[v].meanLS)} / ${fL(bs.views[v].meanLB)}` : "-")).join(" | ")} |`);
  for (const r of withViews) md.push(`| ${r.candidate} | ${VV.map((v) => (r.views[v] ? `${f4(r.views[v].delta)} (L* ${fL(r.views[v].meanLB)})` : "-")).join(" | ")} |`);
  md.push("", `Signal deltas (${SIGNAL_KEYS.join(", ")}):`, "");
  for (const r of withViews) md.push(`- ${r.candidate}: ${Object.entries(r.signals).map(([k, x]) => `${k} ${f3(x)}`).join(", ")}`);
  md.push("");
}
const warns = rows.filter((r) => r.warn || r.tris !== null);
md.push("Candidates: tris / changed objects / changed blocks / render time", "");
for (const r of rows) md.push(`- ${r.candidate}: tris ${r.tris ?? "-"} (baseline ${baseStats.tris}), objects [${r.changedObjects.join(", ")}], blocks [${r.changedBlocks.join(", ")}], ${r.renderSecs ? r.renderSecs.toFixed(0) + " s" : "cached"}${r.warn ? ` WARN ${r.warn}` : ""}${r.guardWarn?.length ? ` GUARD_WARN x${r.guardWarn.length}: ${r.guardWarn.slice(0, 3).join(" / ")}` : ""}`);
if (summary.baseline.guardWarn.length) md.push(`- BASELINE GUARD_WARN x${summary.baseline.guardWarn.length}: ${summary.baseline.guardWarn.slice(0, 3).join(" / ")}`);
md.push("", `Runtime: ${wall.toFixed(0)} s wall; ${nRendered} Blender render(s) in ${renderWall.toFixed(0)} s wall (${summary.perCandidateSecs ? `${summary.perCandidateSecs.mean.toFixed(0)} s mean per render, max ${summary.perCandidateSecs.max.toFixed(0)} s` : "all cached"}).`, "top.png: rows = views (concept: the painting under the part's local alignment), columns = SOURCE | BASELINE | best 3 by part score.");
fs.writeFileSync(path.join(vdir, "ranking.md"), md.join("\n") + "\n");

// ---------- top.png ----------
{
  const cols = [{ title: "SOURCE", dir: null }, { title: `BASELINE ${f3(bs.score)}`, dir: baseDir },
    ...top3.map((r, i) => ({ title: `#${i + 1} ${r.candidate} ${f4(r.delta)}${r.wholeGuard ? " (whole guard)" : ""}`, dir: path.join(vdir, r.candidate) }))];
  const LAB = 96, GAP = 6, HEAD = 26, rowsImg = [];
  const T = bs.concept?.used ? bs.concept.align : null;
  for (const v of [...VIEWS, ...(T ? ["concept"] : [])]) {
    const box = cropOverride[v] ?? unionBox([roleBBox(baseDir, role)[v], ...top3.map((r) => roleBBox(path.join(vdir, r.candidate), role)[v])]);
    if (!box) continue;
    const cells = [];
    if (v === "concept") {   // painting px = 2c + s (P - 2c) + 2t (canvas px) for build px P
      const q = (X, cc, t) => 2 * cc + T.s * (X - 2 * cc) + 2 * t;
      const sb = [q(box[0], T.cx, T.tx), q(box[1], T.cy, T.ty), q(box[2], T.cx, T.tx), q(box[3], T.cy, T.ty)].map(Math.round);
      for (const c of cols) cells.push(c.dir ? await cropBuf(path.join(c.dir, "pass0_concept.png"), box, [0, 0], 10, 380)
        : await cropBuf(path.join(ROOT, bs.concept.target ?? `refs/${subject}.png`), sb, [0, 0], Math.round(10 * T.s), 380));
    } else {
      const sh = B.views[v].shift;       // the source is drawn at the build's pixel + the registration shift
      for (const c of cols) cells.push(await cropBuf(c.dir ? path.join(c.dir, `pass0_${v}.png`) : turnaroundFile(subject, v), box, c.dir ? [0, 0] : sh, 10, 380));
    }
    const h = Math.max(84, ...cells.map((c) => c.h));
    const lab = await sharp({ create: { width: LAB, height: h, channels: 3, background: "#eceff3" } }).composite([
      { input: await textPng(v, LAB, 22, { bold: true }), top: 4, left: 0 }, { input: await textPng("part delta:", LAB, 18, { size: 12 }), top: 28, left: 0 },
      ...(await Promise.all(top3.map(async (r, i) => ({ input: await textPng(`#${i + 1} ${r.views[v] ? f4(r.views[v].delta) : "-"}`, LAB, 18, { size: 12 }), top: 46 + 18 * i, left: 0 })))),
    ]).png().toBuffer();
    rowsImg.push({ cells, h, lab });
  }
  if (rowsImg.length) {
    const pitch = Math.max(...rowsImg.flatMap((r) => r.cells.map((c) => c.w))) + GAP;
    const W = LAB + pitch * cols.length, H = HEAD + rowsImg.reduce((a, r) => a + r.h + GAP, 0), comp = [];
    for (let i = 0; i < cols.length; i++) comp.push({ input: await textPng(cols[i].title, pitch - GAP, HEAD - 2, { size: 13, bold: true }), left: LAB + i * pitch, top: 0 });
    let y = HEAD;
    for (const r of rowsImg) {
      comp.push({ input: r.lab, left: 0, top: y });
      r.cells.forEach((c, i) => comp.push({ input: c.buf, left: LAB + i * pitch, top: y }));
      y += r.h + GAP;
    }
    await sharp({ create: { width: W, height: H, channels: 3, background: "#ffffff" } }).composite(comp).png().toFile(path.join(vdir, "top.png"));
  }
}

console.log(fs.readFileSync(path.join(vdir, "ranking.md"), "utf8"));
console.log(`wrote ${rel(path.join(vdir, "ranking.json"))}, ranking.md, top.png`);
