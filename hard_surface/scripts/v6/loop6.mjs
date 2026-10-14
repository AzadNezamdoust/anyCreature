// WORKFLOW v6 — V6-2: the MULTI-VIEW path of scripts/loop.mjs (runLoop calls runV6 when the subject has
// subjects/<s>/turnaround/views.json). It reuses runLoop's seat / candidate / archive machinery and replaces the
// measure, guard, stop, prompts and sheet:
//
//   START  the class template (or --from) + the frame knobs, STRETCHED to the turnaround's dimensions (each metre knob
//          scaled by the axis it moves, measured by a perturbation; the prior card's softRanges replace the ranges of
//          the knobs it names, L unlocked) -> palette calibrate -> multi-view FIT (mvfit.mjs: body, then features)
//   BUILD  one seat call: the READY CALLS of every missing feature (loop.mjs missingReady) -> multi-view re-FIT
//   LOOP   k <= K seat calls: VIEW-TAGGED residual rows (judge.mjs viewRows: "FRONT: part ... 0.12 m too far outboard")
//          + PLACEMENT rows (rules registry), ranked, ONE structural edit each; <= 6 kB
//   SHEET  every step's sheet.png = the 6-view judge sheet (reference row + model row); an image goes to the seat only
//          when the best module changed since the last one sent
// Guard (lexicographic): loads; tris in budget; gate (blocking rows, no new code); placement rows (no new row, count not
// higher; fewer accepts); per-view IoU min not lower (VIEW_EPS); weighted multi-view score >= best + SCORE_GAIN.
// Target stop: gate PASS, no placement row, every ortho IoU >= V6_TARGET.ortho, concept IoU >= V6_TARGET.concept
// (+ the V5 exactness stop when --v5-detail on). Other stops as v4: K, 2 consecutive rejects, 2 accepted gains <
// PLATEAU, the wall clock (V6_TIME_MS unless LLMM_LOOP_TIME_MS).
import fs from "node:fs";
import path from "node:path";

import { ROOT } from "../subject.mjs";
import { loadModule } from "../project.mjs";
import { addFrameKnobs, frameOf } from "../registered.mjs";
import { knobNum } from "../knobs.mjs";
import { NUMBERED_CONTRACT } from "../seat-io.mjs";
import { PROMPT_MAX, assertPromptSize, buildPrompt, calibrate, measureFixed, missingReady, numbered, placeModule, readyBlock, rejectedBlock } from "../loop.mjs";
import { AXIS_DIM, loadTurnaround, partFamilies } from "./ortho.mjs";
import { mvFit } from "./mvfit.mjs";
import { composeRows, judge, referenceTiles, sheetOrder } from "./judge.mjs";

export const V6_TIME_MS = 30 * 60 * 1000;
export const V6_TARGET = Object.freeze({ ortho: 0.92, concept: 0.96 });
export const SCORE_GAIN = 0.001;
/** MVP-STUB: per-view IoU flickers on AA; "min not lower" allows this much. */
export const VIEW_EPS = 0.002;
export const PLATEAU = 0.003;
const r4 = (v) => Math.round(v * 1e4) / 1e4;
const bytes = (s) => Buffer.byteLength(s, "utf8");

// ---------------------------------------------------------------------------
// START: template knobs stretched to the turnaround + prior soft ranges
// ---------------------------------------------------------------------------

/** Rewrite one KNOBS entry's v / min / max (and drop its `locked`). */
export function setKnob(text, name, { v, min, max }, unlock = false) {
  const num = "-?[\\d.]+(?:e-?\\d+)?";
  const re = new RegExp(`(\\n\\s*${name}:\\s*\\{\\s*)v:\\s*${num},\\s*min:\\s*${num},\\s*max:\\s*${num}`);
  let out = text.replace(re, `$1v: ${knobNum(v)}, min: ${knobNum(min)}, max: ${knobNum(max)}`);
  if (unlock) out = out.replace(new RegExp(`(\\n\\s*${name}:\\s*\\{[^\\n]*?),\\s*locked:\\s*"[^"]*"`), "$1");
  return out;
}

const boxOf = (ps) => ps.reduce((b, p) => {
  const a = p.solid.aabb();
  return { min: b.min.map((v, i) => Math.min(v, a.min[i])), max: b.max.map((v, i) => Math.max(v, a.max[i])) };
}, { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] });

/**
 * The START stretch. The module's own dimensions (x / z: the body-family parts' box, y: the whole model's height) vs the
 * turnaround's (reg.dims at the anchor scale) give a ratio per axis; each metre knob is scaled (v, min, max) by the
 * ratio of the axis a +2 % step of it moves most (part boxes + vertex centroids); prior.softRanges {name: [min, max]} then replace those knobs' ranges
 * (v clamped, `locked` dropped). A stretch that no longer builds falls back to the soft ranges alone.
 * @returns {Promise<{text:string, ratio:number[], moved:object, fallback?:string}>}
 */
export async function priorStart(text, { subjectId, file }) {
  const { reg, prior, table } = await loadTurnaround(subjectId);
  placeModule(text, file);
  const mod = await loadModule(file);
  const parts = mod.build();
  const fam = partFamilies(parts, mod.meta.palette, table);
  const body = boxOf(parts.filter((_, i) => fam[i] === table.body));
  const all = boxOf(parts);
  const have = [body.max[0] - body.min[0], all.max[1] - Math.min(0, all.min[1]), body.max[2] - body.min[2]];
  const ratio = [0, 1, 2].map((a) => (reg.dims[AXIS_DIM[a]] && have[a] > 0 && Number.isFinite(have[a]) ? r4(reg.dims[AXIS_DIM[a]] / have[a]) : 1));
  // a part's signature: its box + its vertex centroid (a profile point inside the box moves the centroid)
  const sig = (p) => {
    const a = p.solid.aabb();
    const m = p.solid.mesh();
    const c = [0, 0, 0];
    const n = m.vertProperties.length / m.numProp;
    for (let i = 0; i < n; i += 1) for (let k = 0; k < 3; k += 1) c[k] += m.vertProperties[i * m.numProp + k] / n;
    return [...a.min, ...a.max, ...c];
  };
  const base = new Map(parts.map((p) => [p.id, sig(p)]));
  const soft = prior?.softRanges ?? {};
  const moved = {};
  const KN = mod.KNOBS ?? {};
  let out = text;
  for (const [n, k] of Object.entries(KN)) {
    if (k.unit !== "m") continue;
    const v0 = k.v;
    const mv = [0, 0, 0];
    k.v = v0 + Math.max(0.01, Math.abs(v0) * 0.02);
    try {
      for (const p of mod.build()) {
        const b = base.get(p.id);
        if (!b) continue;
        const a = sig(p);
        for (let i = 0; i < 9; i += 1) mv[i % 3] += Math.abs(a[i] - b[i]);
      }
    } catch { /* a step that breaks the build moves nothing */ }
    k.v = v0;
    const ax = mv.indexOf(Math.max(...mv));
    if (!(mv[ax] > 1e-6)) continue;
    const r = ratio[ax];
    if (Array.isArray(soft[n])) {
      const [lo, hi] = soft[n];
      out = setKnob(out, n, { v: Math.min(hi, Math.max(lo, v0 * r)), min: lo, max: hi }, true);
      moved[n] = `${"xyz"[ax]} x${r} -> soft [${lo}, ${hi}]`;
    } else if (!k.locked && k.max > k.min) {
      out = setKnob(out, n, { v: v0 * r, min: Math.min(k.min * r, k.max * r), max: Math.max(k.min * r, k.max * r) });
      moved[n] = `${"xyz"[ax]} x${r}`;
    }
  }
  placeModule(out, file);
  try {
    const m2 = await loadModule(file);
    m2.build();
    return { text: out, ratio, moved };
  } catch (error) {
    let fallback = text;
    for (const [n, k] of Object.entries(KN)) if (Array.isArray(soft[n])) fallback = setKnob(fallback, n, { v: Math.min(soft[n][1], Math.max(soft[n][0], k.v)), min: soft[n][0], max: soft[n][1] }, true);
    placeModule(fallback, file);
    return { text: fallback, ratio, moved: {}, fallback: `stretch does not build (${String(error.message).split("\n")[0]}) — soft ranges only` };
  }
}

// ---------------------------------------------------------------------------
// Measure, guard, stop
// ---------------------------------------------------------------------------

/** loop.mjs measure (gate, tris, coverage, ...) + the 6-view judge (m.v6 metrics, m.tiles). */
export async function measure6(ctx, file) {
  const m = await measureFixed(ctx, file);
  if (!m.loads) return m;
  const r = await judge({ subjectId: ctx.subjectId, built: { meta: m.mod.meta, parts: m.parts, frame: frameOf(m.mod.KNOBS) } });
  m.v6 = r.metrics;
  m.tiles = r.tiles;
  return m;
}

/** Placement-row keys (numbers stripped): a row is "the same" across modules when only its numbers moved. */
const placementKeys = (m) => (m.v6?.placementRows ?? []).map((t) => t.replace(/-?\d+(?:\.\d+)?/g, "#"));

/**
 * Lexicographic, strictly better (research/WF-V6-PLAN.md; V6-2 brief): loads; tris; gate; placement; per-view IoU min not
 * lower; weighted multi-view score >= best + SCORE_GAIN.
 * @returns {{accept:boolean, reasons:string[], gain:number}}
 */
export function judge6(c, b) {
  if (!c.loads) return { accept: false, reasons: [c.noEdit ? c.why : `the module does not load — ${c.why}`], gain: 0 };
  const gain = r4(c.v6.score - b.v6.score);
  if (c.tris > c.triBudget) return { accept: false, reasons: [`${c.tris} triangles, over the ${c.triBudget} budget`], gain };
  const newCodes = c.codes.filter((x) => !b.codes.includes(x));
  if (c.blocking > b.blocking || newCodes.length) return { accept: false, reasons: [`gate got worse: blocking rows ${b.blocking} -> ${c.blocking}${newCodes.length ? `, new row ${newCodes.join(", ")}` : ""}`], gain };
  if (c.blocking < b.blocking) return { accept: true, reasons: [`gate blocking rows ${b.blocking} -> ${c.blocking}`], gain };
  const kb = placementKeys(b);
  const kc = placementKeys(c);
  const added = c.v6.placementRows.filter((_, i) => !kb.includes(kc[i]));
  if (added.length || kc.length > kb.length) return { accept: false, reasons: [`placement got worse: ${added.length ? added.join("; ") : `${kb.length} -> ${kc.length} rows`}`], gain };
  if (kc.length < kb.length) return { accept: true, reasons: [`placement rows ${kb.length} -> ${kc.length}`], gain };
  const worst = (m) => Object.entries(m.v6.views).sort((p, q) => p[1].iou - q[1].iou)[0][0];
  if (c.v6.minView < b.v6.minView - VIEW_EPS) return { accept: false, reasons: [`per-view IoU min ${b.v6.minView} (${worst(b)}) -> ${c.v6.minView} (${worst(c)})`], gain };
  if (c.v6.score >= b.v6.score + SCORE_GAIN - 1e-9) return { accept: true, reasons: [`multi-view score ${b.v6.score} -> ${c.v6.score}`], gain };
  return { accept: false, reasons: [`multi-view score ${c.v6.score} is not >= best ${b.v6.score} + ${SCORE_GAIN} and no higher tier improved`], gain };
}

/** Target: gate PASS, no placement row, every ortho >= V6_TARGET.ortho, concept >= V6_TARGET.concept (+ exact). */
export function atTarget6(m, { exact = false } = {}) {
  if (!m.loads || !m.pass || !m.v6 || !m.v6.checks.pass || m.v6.placementRows.length) return false;
  if (m.v6.minOrtho < V6_TARGET.ortho || m.v6.views.concept.iou < V6_TARGET.concept) return false;
  return !exact || !!m.accuracy?.exact;
}

/** The v6 numbers a verdict / loop.json carries. */
export function summary6(m, exact = false) {
  if (!m.loads || !m.v6) return {};
  return { views: Object.fromEntries(Object.entries(m.v6.views).map(([k, v]) => [k, v.iou])), score: m.v6.score, sigma: m.v6.sigma,
    placement: m.v6.placementRows, viewRows: m.v6.viewRows.length, target: atTarget6(m, { exact }) };
}

// ---------------------------------------------------------------------------
// Prompts + sheet
// ---------------------------------------------------------------------------

export function scoreboard6(ctx, m, { step, verdict }) {
  const views = Object.entries(m.v6.views).map(([v, x]) => {
    const band = v === "concept" ? V6_TARGET.concept : V6_TARGET.ortho;
    return `${v} ${x.iou}${x.iou < band ? " UNDER" : ""}`;
  }).join(", ");
  const palette = Object.keys(m.mod?.meta?.palette ?? {});
  const lines = [
    `# SCOREBOARD — ${step}`,
    "",
    `- gate: ${m.pass ? "PASS" : `FAIL, ${m.blocking} blocking row(s) ${m.codes.join(", ")}`}`,
    `- silhouette IoU per view (target: every ortho >= ${V6_TARGET.ortho}, concept >= ${V6_TARGET.concept}): ${views} | multi-view score ${m.v6.score} (best so far ${ctx.bestScore ?? m.v6.score})`,
    `- placement: ${m.v6.placementRows.length ? `${m.v6.placementRows.length} row(s) below` : "PASS"}`,
    ...(palette.length ? [`- ZONES (closed: a part's zone is one of these meta.palette keys): ${palette.join(", ")}`] : []),
    `- triangles: ${m.tris} / ${m.triBudget}`,
    `- last verdict: ${verdict}`,
  ];
  if (!m.pass) lines.push("", "```", ...String(m.gateText).split(/\r?\n/).filter((l) => l.trim()).slice(0, 6), "```");
  return lines;
}

/** The module line that builds a part / names a group (outside the KNOBS block), or -1. */
function citeLine(lines, token, inKnobs) {
  if (!token || token === "-") return -1;
  const stem = token.replace(/_[lr]\d*$|\d+$/, "");
  for (const c of [...new Set([token, stem, stem.split("_")[0]])]) {
    for (const pat of [`"${c}"`, `idPrefix: "${c}`, `assemble.${c}(`]) {
      const i = lines.findIndex((l, j) => !inKnobs(j) && l.includes(pat));
      if (i >= 0) return i;
    }
  }
  return -1;
}

export function loopPrompt6(ctx, m, { k, K: KK, verdict, ready }) {
  const lines = m.text.split(/\r?\n/);
  const kb0 = m.text.indexOf("export const KNOBS = {");
  const kb1 = kb0 >= 0 ? m.text.indexOf("\n};", kb0) : -1;
  const kl = kb0 >= 0 ? [m.text.slice(0, kb0).split("\n").length - 1, m.text.slice(0, kb1).split("\n").length] : [-1, -1];
  const inKnobs = (i) => i >= kl[0] && i <= kl[1];
  const rows = [
    ...m.v6.placementRows.map((text) => ({ text, part: /^PLACEMENT: (\S+)/.exec(text)?.[1] })),
    ...m.v6.viewRows.map((r) => ({ text: r.text, part: r.part })),
  ];
  const ret = lines.reduce((a, l, i) => (/^\s*return parts;/.test(l) ? i : a), -1);
  const make = (nRows, context, clip) => {
    const shownRows = rows.slice(0, nRows);
    const keep = new Set();
    for (const r of shownRows) {
      const c = citeLine(lines, r.part, inKnobs);
      if (c >= 0) for (let d = -context; d <= context; d += 1) if (c + d >= 0 && c + d < lines.length) keep.add(c + d);
    }
    if (ready.length && ret >= 0) keep.add(ret);
    const shown = lines.map((l) => (clip && l.length > clip ? `${l.slice(0, clip)} …` : l));
    return [
      `# LOOP ${k} of ${KK} — subject ${ctx.subjectId} (${ctx.S.klass}) — multi-view`,
      "",
      "The harness fits every KNOBS value on ALL views (turnaround orthos + concept); what is left needs STRUCTURE: a call's arguments, parts added or removed, what attaches where. Each row names its VIEW; fix row 1 first, ONE edit per row, in the call that builds the part.",
      "",
      ...scoreboard6(ctx, m, { step: `step ${k} of ${KK}`, verdict }),
      "",
      `# OPEN RESIDUALS — top ${shownRows.length} of ${rows.length} (placement first, then view rows ranked by px x metres)`,
      "",
      ...(shownRows.length ? shownRows.map((r, i) => `${i + 1}. ${r.text}`) : ["(none)"]),
      ...rejectedBlock(ctx),
      ...readyBlock(ctx, m, ready),
      "",
      `# YOUR MODULE — the cited lines ±${context}, numbered \`N| code\``,
      "",
      "```js",
      ...numbered(shown, keep),
      "```",
      "",
      NUMBERED_CONTRACT,
    ].join("\n");
  };
  for (const [nRows, context, clip] of [[8, 2, 0], [8, 1, 0], [8, 0, 0], [6, 1, 0], [6, 0, 160], [4, 0, 120], [2, 0, 100]]) {
    const text = make(nRows, context, clip);
    if (bytes(text) <= PROMPT_MAX) return text;
  }
  return make(1, 0, 80);
}

async function sheet6(ctx, m, out) {
  const { reg } = await loadTurnaround(ctx.subjectId);
  ctx.refTiles ??= await referenceTiles(ctx.subjectId);
  const v = m.v6;
  const ck = v.checks;
  const floats = (ck.groups ?? []).filter((g) => g.float).map((g) => g.name);
  const label = `MODEL — ${reg.names.map((n) => `${n} ${v.views[n].iou.toFixed(3)}`).join(" · ")} · concept ${v.views.concept.iou.toFixed(3)} · score ${v.score} · float [${floats.join(", ")}] · clips ${(ck.clips ?? []).length}`;
  const notes = Object.fromEntries(reg.names.map((n) => [n, `IoU ${v.views[n].iou.toFixed(3)}`]));
  notes.frontLeft = `concept IoU ${v.views.concept.iou.toFixed(3)}`;
  await composeRows([{ label: `REFERENCE — ${ctx.subjectId}: turnaround ${reg.names.join(" / ")}, concept (front-left), rear-right: none`, tiles: ctx.refTiles },
    { label, tiles: m.tiles, notes }], out, 220, sheetOrder(reg));
  return out;
}

// ---------------------------------------------------------------------------
// The v6 run (inside runLoop's try: its helpers, record and stops)
// ---------------------------------------------------------------------------

/**
 * @param {{ctx:object, record:object, out:string, from:string|null, K:number, images:boolean, log:Function, archive:Function,
 *   callSeat:Function, candidateFrom:Function, accept:Function, remember:Function, featureFile:Function, setBest:Function}} h
 */
export async function runV6(h) {
  const { ctx, record, out, from, K: KK, images, log, archive, callSeat, candidateFrom, remember, featureFile, setBest } = h;
  const { subjectId, S } = ctx;
  const exact = ctx.exactStop;
  ctx.v6 = { measure: (f) => measure6(ctx, f), sheet: (m, file) => sheet6(ctx, m, file), summary: (m) => summary6(m, exact) };
  const accept = (m) => { h.accept(m); ctx.bestScore = m.v6.score; setBest(m); return m; };
  const stop = (reason) => { record.stop = reason; log(`[loop] STOP: ${reason}`); };
  const cur = ctx.cur;
  const cand = path.join(path.dirname(cur), "cand.mjs");
  const dirOf = (name) => { const d = path.join(out, String(name)); fs.mkdirSync(d, { recursive: true }); return d; };
  const fit6 = async (file, name) => {
    if (!ctx.fitEnabled) return { skipped: "fit disabled" };
    if ((await loadModule(file)).KNOBS === undefined) return { skipped: "no KNOBS block" };
    try {
      const r = await mvFit({ subjectId, modulePath: file, out: file, log: path.join(dirOf(name), "mvfit.json"), deadline: ctx.deadlineAt });
      return { stages: r.stages.map((s) => `${s.stage} ${s.start.score} -> ${s.end.score} (${s.evals} evals, ${s.accepted} kept)`), ms: r.ms };
    } catch (error) {
      return { skipped: `multi-view FIT refused: ${error.message}` };
    }
  };
  const fitLine = (f) => (f.skipped ? f.skipped : `${f.stages.join("; ")}, ${Math.round(f.ms / 1000)} s`);

  // ---- START + multi-view FIT
  let text = from ? fs.readFileSync(path.resolve(ROOT, from), "utf8") : null;
  if (text === null) {
    text = S.klass === "building"
      ? (await import("../template-building.mjs")).generateForSubject(subjectId, { knobs: true }).text
      : (await import("../template-vehicle.mjs")).generateForSubject(subjectId).text;
  }
  text = addFrameKnobs(text);
  placeModule(text, cur);
  await calibrate(ctx, cur);   // the family of each zone (the stretch's body box) reads the calibrated palette
  const st = await priorStart(fs.readFileSync(cur, "utf8"), { subjectId, file: cur });
  log(`[loop] v6 START stretch x/y/z ${st.ratio.join(" / ")} (${Object.keys(st.moved).length} knobs)${st.fallback ? ` — ${st.fallback}` : ""}`);
  const f0 = await fit6(cur, "start");
  const ff0 = !f0.skipped && ctx.featureFit ? await featureFile(cur, "start") : null;   // --v5-detail on
  if (ctx.facePalette) await calibrate(ctx, cur);
  let best = accept(await measure6(ctx, cur));
  if (!best.loads) throw new Error(`loop: the v6 start module does not load — ${best.why}`);
  log(`[loop] START + multi-view FIT ${fitLine(f0)}: ${JSON.stringify(summary6(best).views)} score ${best.v6.score}, gate ${best.pass ? "PASS" : best.codes.join(",")}, placement ${best.v6.placementRows.length}`);
  let bestSheet = await archive("start", best, "START + multi-view FIT", { stretch: st, fit: f0.skipped ?? f0.stages, ...(ff0 ? { features: ff0 } : {}), v6: summary6(best, exact) });
  let sentFor = null;
  const imgs = () => {
    if (!images || !bestSheet || sentFor === best.hash) return [];
    sentFor = best.hash;
    return [bestSheet];
  };

  let verdict = "START + multi-view FIT";
  if (atTarget6(best, { exact })) stop("target");
  else if (ctx.late()) stop("time (during START FIT)");
  else {
    // ---- BUILD (+ multi-view re-FIT)
    const ready = await missingReady(ctx, best);
    if (ready.length) {
      const prompt = buildPrompt(ctx, best, ready, scoreboard6);
      const promptBytes = assertPromptSize(prompt, "BUILD");
      const s = await callSeat(prompt, imgs(), "build");
      const c = await candidateFrom(best, s, "build");
      let refit = null;
      if (c.m.loads) {
        refit = await fit6(cand, "build");
        if (!refit.skipped && ctx.featureFit) await featureFile(cand, "build");
        await calibrate(ctx, cand);
        c.m = await measure6(ctx, cand);
      }
      const j = judge6(c.m, best);
      verdict = `BUILD ${j.accept ? "ACCEPTED" : "REJECTED"} — ${j.reasons.join("; ")}${c.how ? ` (${c.how}${c.added.length ? `, ${c.added.length} knob(s) added` : ""})` : ""}`;
      log(`[loop] ${verdict}${refit ? ` · re-FIT ${fitLine(refit)}` : ""}`);
      const sheet = await archive("build", c.m, verdict, { accepted: j.accept, gain: j.gain, promptBytes, seatSeconds: r4((s.seconds ?? 0) + c.seconds), knobsAdded: c.added, refit: refit ? (refit.skipped ?? refit.stages) : null, v6: summary6(c.m, exact) });
      if (j.accept) { best = accept(c.m); bestSheet = sheet ?? bestSheet; } else { remember("build", best, c, j.reasons.join("; ")); verdict += " — reverted to the fitted start"; }
    } else {
      verdict = "BUILD skipped: no missing feature has a READY call";
      log(`[loop] ${verdict}`);
    }
    if (atTarget6(best, { exact })) stop("target");
  }

  // ---- LOOP. MVP-STUB: no multi-view re-FIT of a LOOP candidate (the seat's structural edit is judged as sent)
  let rejects = 0;
  let small = 0;
  for (let k = 1; !record.stop && k <= KK; k += 1) {
    if (ctx.late()) { stop("time"); break; }
    const ready = await missingReady(ctx, best);
    const prompt = loopPrompt6(ctx, best, { k, K: KK, verdict, ready });
    const promptBytes = assertPromptSize(prompt, `LOOP ${k}`);
    const s = await callSeat(prompt, imgs(), k);
    const c = await candidateFrom(best, s, k);
    const j = judge6(c.m, best);
    verdict = `${j.accept ? "ACCEPTED" : "REJECTED"} — ${j.reasons.join("; ")}${j.accept ? "" : " — the module was reverted to the best one"}`;
    log(`[loop] ${k}/${KK}: ${verdict}`);
    const sheet = await archive(k, c.m, verdict, { accepted: j.accept, gain: j.gain, promptBytes, seatSeconds: r4((s.seconds ?? 0) + c.seconds), how: c.how, knobsAdded: c.added, v6: summary6(c.m, exact) });
    if (j.accept) {
      best = accept(c.m);
      bestSheet = sheet ?? bestSheet;
      rejects = 0;
      small = j.gain < PLATEAU ? small + 1 : 0;
      if (atTarget6(best, { exact })) stop("target");
      else if (small >= 2) stop(`plateau (2 accepted gains < ${PLATEAU})`);
    } else {
      remember(k, best, c, j.reasons.join("; "));
      rejects += 1;
      if (rejects >= 2) stop("2 consecutive rejects");
    }
    if (!record.stop && k === KK) stop(`K (${KK} loop steps)`);
  }
  if (!record.stop) stop(KK === 0 ? "K (0 loop steps)" : "K");
  return best;
}
