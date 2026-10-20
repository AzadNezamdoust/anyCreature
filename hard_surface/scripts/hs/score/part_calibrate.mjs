// Calibrates part_score.mjs on the controlled single-part variants of variants.mjs (each known-worse than BASELINE).
//
//   node scripts/hs/score/part_calibrate.mjs [--subjects pistol,pump_shotgun,gatling_gun]
//
// For each variant: candidates {base_a, base_b, variant} scored on the edited part over their shared region.
//   partDelta  = part(variant) - mean(part(base_a), part(base_b))      (< 0 = ranked correctly)
//   noise      = |part(base_a) - part(base_b)| (two independent renders of the same build.py)
//   wholeDelta = likeness(variant) - mean(likeness(bases))             (likeness_score.mjs, whole views)
//   otherMax   = max over the OTHER parts of |part(variant) - part(base_a)| (spill-over / effective noise floor)
// --own-shift: every candidate keeps its own whole-view registration (default: reuse base_a's).
// Writes out/score/part_calibration.json (or part_calibration_ownshift / _noconcept / _notonematch.json) and prints a markdown table.
import fs from "node:fs";
import path from "node:path";
import { loadCandidate, partRegion, scorePart as scorePart0, OPTS } from "./part_score.mjs";
import { VARIANTS, VDIR } from "./variants.mjs";
import { ROOT, VIEWS } from "./likeness_score.mjs";

const argv = process.argv.slice(2), ai = argv.indexOf("--subjects");
const LOCK = !argv.includes("--own-shift");   // default: variants reuse base_a's registration (as part_score.mjs's CLI)
// --no-concept: orthos only; --no-tone-match: structure signals on the raw build L* (ablations, 2026-10-10)
const CONCEPT = !argv.includes("--no-concept");
OPTS.toneMatch = !argv.includes("--no-tone-match");
const scorePart = (s, c, p) => scorePart0(s, c, p, { concept: CONCEPT });
const SUFFIX = (LOCK ? "" : "_ownshift") + (CONCEPT ? "" : "_noconcept") + (OPTS.toneMatch ? "" : "_notonematch");
const OUT = path.join(ROOT, "out", "score", `part_calibration${SUFFIX}.json`);
const subjects = ai >= 0 ? argv[ai + 1].split(",") : Object.keys(VARIANTS);
const rows = [], noise = {};
const f4 = (x) => (x >= 0 ? "+" : "") + x.toFixed(4);

for (const s of subjects) {
  const A = await loadCandidate(s, path.join(VDIR, s, "base_a"));
  const B = await loadCandidate(s, path.join(VDIR, s, "base_b"), "pass0_", LOCK ? A : null);
  noise[s] = { whole: Math.abs(A.whole.likeness - B.whole.likeness), parts: {} };
  for (const p of A.parts) {
    const [a, b] = await scorePart(s, [A, B], p);
    if (a.score !== null) noise[s].parts[p] = Math.abs(a.score - b.score);
  }
  for (const [k, v] of Object.entries(VARIANTS[s])) {
    const dir = path.join(VDIR, s, k);
    if (!fs.existsSync(path.join(dir, "pass0_ids.json"))) { console.error(`skip ${s}/${k}: not rendered`); continue; }
    const C = await loadCandidate(s, dir, "pass0_", LOCK ? A : null);
    const shiftFlip = VIEWS.some((w) => C.views[w].ownShift.join() !== A.views[w].ownShift.join());
    const [a, b, c] = await scorePart(s, [A, B, C], v.part);
    const base = (a.score + b.score) / 2, wbase = (A.whole.likeness + B.whole.likeness) / 2;
    const sig = (k2) => (a[k2] === null || c[k2] === null ? null : c[k2] - (a[k2] + b[k2]) / 2);
    const eqOf = (r) => { const vs = Object.values(r.views); return vs.length ? vs.reduce((t, x) => t + x.score, 0) / vs.length : null; };
    const regionOf = (p) => Object.fromEntries(VIEWS.map((w) => {
      const k = A.parts.indexOf(p); if (k < 0) return [w, null];
      const ra = partRegion(A.views[w].masks[k]), rc = partRegion(C.views[w].masks[k]);
      return [w, ra && rc ? ra.map((x, i) => x | rc[i]) : ra ?? rc];
    }));
    const own = regionOf(v.part);
    let otherMax = 0, otherPart = null;
    const others = [];
    for (const p of A.parts) {
      if (p === v.part) continue;
      const [x, y] = await scorePart(s, [A, C], p);
      if (x.score === null) continue;
      const d = Math.abs(y.score - x.score), rg = regionOf(p);
      const overlap = VIEWS.some((w) => own[w] && rg[w] && own[w].some((q, i) => q & rg[w][i]));
      others.push({ part: p, d, overlap });
      if (d > otherMax) { otherMax = d; otherPart = p; }
    }
    const row = { subject: s, key: k, part: v.part, what: v.what, wholeDelta: C.whole.likeness - wbase,
      partBase: base, partVar: c.score, partDelta: c.score - base, noise: Math.abs(a.score - b.score),
      partEqDelta: eqOf(c) - (eqOf(a) + eqOf(b)) / 2,
      views: Object.fromEntries(Object.keys(c.views).map((w) => [w, { px: c.views[w].px, delta: c.views[w].score - (a.views[w].score + b.views[w].score) / 2 }])),
      signals: { sil: sig("sil"), edge: sig("edge"), ssim: sig("ssim"), tone: sig("tone"), value: sig("value"), open: sig("open") },
      concept: c.concept?.used ? { ncc: c.concept.align.ncc, delta: c.views.concept.score - (a.views.concept.score + b.views.concept.score) / 2 } : { used: false, reason: c.concept?.reason },
      otherMax, otherPart, others, shiftFlip };
    rows.push(row);
    console.error(`${s}/${k}: part ${f4(row.partDelta)} eq ${f4(row.partEqDelta)} whole ${f4(row.wholeDelta)} other ${otherMax.toFixed(4)} (${otherPart})`);
  }
}

// nuisance floor: how much an edit moves the score of a part whose region it does not touch (renders are
// deterministic, so re-render noise is 0; this is the honest noise for "is this delta about this part?")
const pct = (a, q) => { const b = [...a].sort((x, y) => x - y); return b.length ? b[Math.min(b.length - 1, Math.floor(q * b.length))] : 0; };
const farD = rows.flatMap((r) => r.others.filter((o) => !o.overlap).map((o) => o.d));
const nearD = rows.flatMap((r) => r.others.filter((o) => o.overlap).map((o) => o.d));
const FLOOR = pct(farD, 0.95);
for (const r of rows) { r.correct = r.partDelta < 0; r.significant = r.partDelta < -FLOOR; r.eqSignificant = r.partEqDelta < -FLOOR; r.wholeSignificant = r.wholeDelta < -FLOOR; }
const n = rows.length, ok = rows.filter((r) => r.correct).length, wok = rows.filter((r) => r.wholeDelta < 0).length;
const cnt = (f) => rows.filter(f).length;
const med = (a) => { const b = [...a].sort((x, y) => x - y); return b.length ? (b[(b.length - 1) >> 1] + b[b.length >> 1]) / 2 : null; };
const summary = {
  n, partCorrect: ok, wholeCorrect: wok,
  partDeltaMedian: med(rows.map((r) => r.partDelta)), wholeDeltaMedian: med(rows.map((r) => r.wholeDelta)),
  partDeltaWorst: Math.max(...rows.map((r) => r.partDelta)),
  rerenderNoiseMax: Math.max(...rows.map((r) => r.noise), ...Object.values(noise).flatMap((x) => Object.values(x.parts))),
  otherMaxMedian: med(rows.map((r) => r.otherMax)), otherMaxMax: Math.max(...rows.map((r) => r.otherMax)),
  nuisanceFloorP95: FLOOR, nuisanceFarN: farD.length, nuisanceFarMax: Math.max(...farD), nuisanceNearMedian: med(nearD),
  partSignificant: cnt((r) => r.significant), partEqSignificant: cnt((r) => r.eqSignificant), wholeSignificant: cnt((r) => r.wholeSignificant),
  partEqCorrect: cnt((r) => r.partEqDelta < 0), partEqDeltaMedian: med(rows.map((r) => r.partEqDelta)),
};
fs.mkdirSync(path.join(ROOT, "out", "score"), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify({ lockShift: LOCK, summary, noise, rows }, null, 1));

console.log(`nuisance floor (p95 |Δ| of non-touching parts, n ${farD.length}): ${FLOOR.toFixed(4)}\n`);
console.log("| subject | variant (expected worse) | part | whole Δ | part Δ (area views) | part Δ (equal views) | re-render noise | max other-part \\|Δ\\| | correct (dir / beyond floor) |");
console.log("|---|---|---|---|---|---|---|---|---|");
for (const r of rows)
  console.log(`| ${r.subject} | ${r.key}: ${r.what} | ${r.part} | ${f4(r.wholeDelta)} | ${f4(r.partDelta)} | ${f4(r.partEqDelta)} | ${r.noise.toFixed(4)} | ${r.otherMax.toFixed(4)} (${r.otherPart}) | ${r.correct ? "y" : "**n**"} / ${r.significant ? "y" : "**n**"}${r.shiftFlip ? " (shift flip)" : ""} |`);
console.log("\nper-view part deltas:");
for (const r of rows) console.log(`${r.subject}/${r.key}: ` + Object.entries(r.views).map(([w, x]) => `${w} ${f4(x.delta)} (${x.px} px)`).join("  "));
console.log("\nsignal deltas (variant - base):");
for (const r of rows) console.log(`${r.subject}/${r.key}: ` + Object.entries(r.signals).map(([k, v]) => `${k} ${v === null ? "-" : f4(v)}`).join("  "));
console.log("\n" + JSON.stringify(summary, null, 1));
