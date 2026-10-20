// WF v8 WP3 (research/v7/WF-V8-PLAN.md) — the pure rules of scripts/v7/step.mjs (the modeller's one-command iteration),
// doctor.mjs (the setup check) and scaffold.mjs (a start from the nearest gold). No file I/O, no rendering, no module
// builds here: every function takes plain data (module text and raw pixel buffers included) and is unit-tested in
// scripts/v7/steplib.test.mjs.
import { addFrameKnobs, borderBackground, frameKnobLines } from "../registered.mjs";
import { replaceKnobValues } from "../knobs.mjs";

/** The step rule's numbers: an agree drop that reverts; the frame-refit WARN bounds; blobs per view; the printed-line cap. */
export const STEP = Object.freeze({ drop: 0.01, frameScale: 0.01, framePx: 6, blobTop: 5, maxLines: 40, maxProbes: 15 });
/** The doctor's numbers: registration residual band, bbox band, enclosed near-white shares, body margin, centring, camera. */
export const DOCTOR = Object.freeze({ band: 0.03, bboxBand: 0.05, whiteMin: 0.001, whiteBlock: 0.005, bodyMargin: 8, centre: 0.03,
  cameraResidual: 1.0, cameraTilt: 0.5, probesMin: 6, probesMax: 15, driftMax: 0.05 });
/** Class-config gate rows (the closed class lists the WP2 `wheels` / `paletteZones` overrides close per subject). */
export const CLASS_CONFIG = Object.freeze(["PALETTE_ZONE", "VEH_WHEELS"]);
const EPS = 1e-9;

const f4 = (x) => x.toFixed(4);
const sgn = (x, d = 1) => `${x >= 0 ? "+" : ""}${x.toFixed(d)}`;

// ---------------------------------------------------------------------------------------------------------------------
// step: the KEEP / REVERT verdict
// ---------------------------------------------------------------------------------------------------------------------

/** Identity of a validator-chain violation row ({v, part}) across runs. */
export const chainKey = (row) => `${row.v}|${row.part ?? ""}`;
/** Identity of a placement clip ({a, b}), order-free. */
export const clipKey = (c) => [c.a, c.b].sort().join(" x ");
/** A view's agree (views[v].agree; the raw iou when a JSON predates WF v8). */
export const agreeOf = (m) => (m?.agree ?? m?.iou);

/**
 * The step verdict (WF-REVIEW-opus.md C4): KEEP, or REVERT naming every reason —
 *   1. check-module fails;  2. a view's agree drops by more than `drop` below the baseline's (agree masks the drift rects,
 *   so a loss inside a drift rect never counts; a raw-IoU loss hidden that way is a note);  3. a new float or a new clip
 *   (groups / clips not in the baseline's checks; none known = every one is new);  4. a new validator-chain row (keys
 *   not in the baseline's rows; baseline rows unknown = every row but a CLASS_CONFIG one, those are notes);  5. the
 *   chain errored;  6. tris over the budget.
 * @param {{checkModule:{pass:boolean, line:string}, views:object, floats:{name:string, why?:string}[], clips:{a:string, b:string}[],
 *   chainRows:{v:string, part?:string}[]|null, chainError?:string|null, tris:number, budget:number|null}} cur
 * @param {{views?:object, floats?:string[]|null, clips?:string[]|null, chainRows?:string[]|null}|null} base  null = no baseline
 * @returns {{keep:boolean, reasons:string[], notes:string[], newRows:object[], line:string}}
 */
export function stepVerdict(cur, base, { drop = STEP.drop } = {}) {
  const reasons = [];
  const notes = [];
  if (!cur.checkModule?.pass) reasons.push(`check-module FAIL${cur.checkModule?.line ? `: ${cur.checkModule.line}` : ""}`);
  for (const [v, m] of Object.entries(base?.views ?? {})) {
    const c = cur.views?.[v];
    if (!c) continue;
    const b = agreeOf(m), a = agreeOf(c);
    if (a < b - drop - EPS) reasons.push(`${v} agree ${f4(a)} < base ${f4(b)} - ${drop}`);
    else if (c.iou < m.iou - drop - EPS) notes.push(`${v} raw iou ${f4(c.iou)} < base ${f4(m.iou)} - ${drop} inside the drift rects`);
  }
  const baseFloats = new Set(base?.floats ?? []);
  for (const g of cur.floats ?? []) if (!baseFloats.has(g.name)) reasons.push(`new float ${g.name}${g.why ? ` (${g.why})` : ""}`);
  const baseClips = new Set(base?.clips ?? []);
  for (const c of cur.clips ?? []) if (!baseClips.has(clipKey(c))) reasons.push(`new clip ${clipKey(c)}`);
  let newRows = [];
  const rows = [...new Map((cur.chainRows ?? []).map((r) => [chainKey(r), r])).values()];   // one row per (rule, part)
  if (cur.chainError) reasons.push(`chain error: ${cur.chainError}`);
  else if (base?.chainRows) {
    const known = new Set(base.chainRows);
    newRows = rows.filter((r) => !known.has(chainKey(r)));
    for (const r of newRows) reasons.push(`new chain row ${r.v}${r.part ? ` ${r.part}` : ""}`);
  } else {
    for (const r of rows) {
      if (CLASS_CONFIG.includes(r.v)) { notes.push(`chain row ${r.v}${r.part ? ` ${r.part}` : ""} (class-config; no baseline rows)`); continue; }
      newRows.push(r);
      reasons.push(`chain row ${r.v}${r.part ? ` ${r.part}` : ""} (no baseline rows)`);
    }
  }
  if (Number.isFinite(cur.budget) && cur.tris > cur.budget) reasons.push(`tris ${cur.tris} > budget ${cur.budget}`);
  return { keep: reasons.length === 0, reasons, notes, newRows, line: reasons.length ? `REVERT: ${reasons.join("; ")}` : "KEEP" };
}

/**
 * The baseline's comparable parts from a view JSON (scripts/v6/view.mjs), a step JSON (step.mjs --json / steps.jsonl) or a
 * state.json `baseline` {views}: {views, floats, clips, chainRows} (null where the source does not carry them).
 */
export function baselineOf(json) {
  if (!json) return null;
  const ck = json.checks;
  return {
    views: json.views ?? {},
    floats: ck ? (ck.groups ?? []).filter((g) => g.float).map((g) => g.name) : null,
    clips: ck ? (ck.clips ?? []).map(clipKey) : null,
    chainRows: Array.isArray(json.chain?.rows) ? json.chain.rows.map(chainKey) : null,
  };
}

/**
 * The concept frame refit (lib.mjs fitFrame, no grid) against the module's knob frame: {dScale (relative), dx, dy (px at a
 * 1024 px target), warn} — warn when the scale moves more than `scale` or a shift more than `px` (the frame is absorbing a
 * proportion change: check the geometry, not the registration).
 */
export function frameMove(knob, fit, { scale = STEP.frameScale, px = STEP.framePx } = {}) {
  const dScale = fit.scale / knob.scale - 1, dx = fit.tx - knob.tx, dy = fit.ty - knob.ty;
  const bits = [];
  if (Math.abs(dScale) > scale + EPS) bits.push(`scale ${sgn(dScale * 100, 2)} % (> ${scale * 100} %)`);
  if (Math.abs(dx) > px + EPS || Math.abs(dy) > px + EPS) bits.push(`shift ${sgn(dx)} / ${sgn(dy)} px (> ${px} px)`);
  return { dScale, dx, dy, warn: bits.length ? `WARN frame refit moved: ${bits.join(", ")}` : null };
}

// ---------------------------------------------------------------------------------------------------------------------
// probes: subjects/<s>/probes.json — named scan lines through landmarks, reference vs model edges
// ---------------------------------------------------------------------------------------------------------------------

/**
 * subjects/<s>/probes.json: `[{id, view, axis: "row" | "col", index, from, to, what?}]` (or `{"probes": [...]}` with notes
 * beside it). `view` = a turnaround view name or "concept"; px of that image: a row probe runs x = from..to on y = index,
 * a col probe y = from..to on x = index (inclusive). Throws naming the first bad probe.
 * @param {any} json  the parsed file
 * @param {string[]} views  the subject's image names (turnaround views + "concept")
 */
export function parseProbes(json, views) {
  const list = Array.isArray(json) ? json : json?.probes;
  if (!Array.isArray(list)) throw new Error('probes.json must be [{id, view, axis, index, from, to}] or {"probes": [...]}');
  const ids = new Set();
  return list.map((p, i) => {
    const where = `probes.json[${i}]${p?.id ? ` (${p.id})` : ""}`;
    if (!p || typeof p !== "object") throw new Error(`${where} is not an object`);
    if (typeof p.id !== "string" || !p.id) throw new Error(`${where}: id must be a non-empty string`);
    if (ids.has(p.id)) throw new Error(`${where}: duplicate id ${p.id}`);
    ids.add(p.id);
    if (!views.includes(p.view)) throw new Error(`${where}: view "${p.view}" is not one of ${views.join(", ")}`);
    if (p.axis !== "row" && p.axis !== "col") throw new Error(`${where}: axis must be "row" or "col"`);
    for (const k of ["index", "from", "to"]) if (!Number.isInteger(p[k]) || p[k] < 0) throw new Error(`${where}: ${k} must be an integer px >= 0`);
    if (!(p.to > p.from)) throw new Error(`${where}: to must be > from`);
    return { id: p.id, view: p.view, axis: p.axis, index: p.index, from: p.from, to: p.to, ...(p.what ? { what: String(p.what) } : {}) };
  });
}

/** Runs of set px along one line, i = from..to inclusive: [[start, end]] (end inclusive), runs shorter than minRun dropped. */
export function lineRuns(isSet, from, to, minRun = 2) {
  const out = [];
  let start = -1;
  for (let i = from; i <= to + 1; i += 1) {
    const on = i <= to && isSet(i);
    if (on && start < 0) start = i;
    if (!on && start >= 0) { if (i - start >= minRun) out.push([start, i - 1]); start = -1; }
  }
  return out;
}

/**
 * Reference vs model runs of one probe: the edge deltas (model - reference, px) — per run pair when both have the same
 * number of runs, else only the outer edges (first start, last end); null when either side is empty.
 * @returns {{same:boolean, deltas:number[][]|null, outer:number[]|null}}
 */
export function probeCompare(ref, model) {
  if (!ref.length || !model.length) return { same: ref.length === model.length, deltas: null, outer: null };
  const outer = [model[0][0] - ref[0][0], model[model.length - 1][1] - ref[ref.length - 1][1]];
  const same = ref.length === model.length;
  return { same, deltas: same ? ref.map((r, i) => [model[i][0] - r[0], model[i][1] - r[1]]) : null, outer };
}

/** One printed probe line. */
export function probeLine(p, ref, model) {
  const runs = (rs) => (rs.length ? rs.map(([a, b]) => `${a}..${b}`).join(" ") : "-");
  const c = probeCompare(ref, model);
  const d = (x) => sgn(x, 0);
  const tail = !c.outer ? "" : c.same ? ` | d ${c.deltas.map(([a, b]) => `${d(a)}/${d(b)}`).join(" ")}` : ` | runs ${ref.length}/${model.length}, outer d ${d(c.outer[0])}/${d(c.outer[1])}`;
  return `probe ${p.id} ${p.view} ${p.axis} ${p.index} [${p.from}..${p.to}]${p.what ? ` (${p.what})` : ""}: ref ${runs(ref)} | model ${runs(model)}${tail}`;
}

// ---------------------------------------------------------------------------------------------------------------------
// doctor: the setup rules
// ---------------------------------------------------------------------------------------------------------------------

const pct = (x) => `${sgn(x * 100, 1)} %`;
/** The per-view entries of one reg.residuals dimension (meanPx / maxAbs are summaries). */
const perView = (rec) => Object.entries(rec ?? {}).filter(([k]) => k !== "meanPx" && k !== "maxAbs");

/**
 * Registration residual rows (ortho.mjs registerViews reg.residuals: {W | L | H | Wbbox | Lbbox: {<view>: px / mean - 1,
 * meanPx, maxAbs}}): a W / L / H view beyond +-band -> one BLOCK row per dimension naming the views (regenerate the view
 * with measured proportions, add a measured shift / scale, or an owner ruling); Wbbox / Lbbox beyond +-bboxBand -> WARN;
 * else one PASS row with the largest residual.
 * @returns {{level:"PASS"|"WARN"|"BLOCK", id:string, text:string, data?:object}[]}
 */
export function residualRows(residuals, { band = DOCTOR.band, bboxBand = DOCTOR.bboxBand } = {}) {
  const rows = [];
  let worst = null;
  for (const D of ["W", "L", "H"]) {
    const out = [];
    for (const [v, r] of perView(residuals?.[D])) {
      if (!worst || Math.abs(r) > Math.abs(worst.r)) worst = { D, v, r };
      if (Math.abs(r) > band + EPS) out.push([v, r]);
    }
    if (out.length) {
      rows.push({ level: "BLOCK", id: `residual-${D}`, data: Object.fromEntries(out),
        text: `registration ${D}: ${out.map(([v, r]) => `${v} ${pct(r)}`).join(", ")} (band +-${band * 100} %) — regenerate the view with measured proportions, add a measured shift / scale, or an owner ruling` });
    }
  }
  for (const D of ["Wbbox", "Lbbox"]) {
    const out = perView(residuals?.[D]).filter(([, r]) => Math.abs(r) > bboxBand + EPS);
    if (out.length) rows.push({ level: "WARN", id: `residual-${D}`, data: Object.fromEntries(out), text: `overall ${D}: ${out.map(([v, r]) => `${v} ${pct(r)}`).join(", ")} (> +-${bboxBand * 100} %: mirrors / bumpers / attachments drawn differently)` });
  }
  if (!rows.some((r) => r.level === "BLOCK")) rows.unshift({ level: "PASS", id: "residuals", text: `registration W / L / H within +-${band * 100} %${worst ? ` (largest ${worst.D} ${worst.v} ${pct(worst.r)})` : ""}` });
  return rows;
}

/**
 * Enclosed near-white of one RGB image (WF-REVIEW-opus.md C3): near-white = darkest channel >= fgMax; the near-white
 * 4-connected to the border or to a hole seed is background (registered.mjs borderBackground, the one flood fill the mask
 * rule uses); every other near-white 4-component of at least minShare of the image's foreground (darkest channel <
 * fgMax) is a candidate: a white PART (views.json families.enclosedFg) or a see-through opening (families.holes).
 * @returns {{fg:number, total:number, comps:{n:number, share:number, bbox:number[]}[]}}  total = the candidates' share; bbox
 *   [x0, y0, x1, y1] px (x1, y1 exclusive), largest first
 */
export function enclosedWhite(data, w, h, c, fgMax, { holes = null, minShare = DOCTOR.whiteMin } = {}) {
  const n = w * h;
  const label = new Uint8Array(n);   // 0 = near-white (borderBackground's bg candidates), 1 = foreground
  let fg = 0;
  for (let i = 0, j = 0; i < n; i += 1, j += c) {
    const a = data[j], b = data[j + 1], d = data[j + 2];
    if (Math.min(a, b, d) < fgMax) { label[i] = 1; fg += 1; }
  }
  const bg = borderBackground(label, w, h, holes);
  const seen = new Uint8Array(n);
  const stack = new Int32Array(n);
  const comps = [];
  for (let i = 0; i < n; i += 1) {
    if (label[i] || bg[i] || seen[i]) continue;
    let top = 0, cnt = 0, x0 = w, y0 = h, x1 = -1, y1 = -1;
    seen[i] = 1; stack[top++] = i;
    while (top) {
      const k = stack[--top];
      const x = k % w, y = (k - x) / w;
      cnt += 1; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      for (const q of [x > 0 ? k - 1 : -1, x < w - 1 ? k + 1 : -1, k >= w ? k - w : -1, k < n - w ? k + w : -1]) {
        if (q >= 0 && !seen[q] && !label[q] && !bg[q]) { seen[q] = 1; stack[top++] = q; }
      }
    }
    if (fg && cnt / fg >= minShare) comps.push({ n: cnt, share: cnt / fg, bbox: [x0, y0, x1 + 1, y1 + 1] });
  }
  comps.sort((a, b) => b.n - a.n);
  return { fg, total: comps.reduce((s, k) => s + k.share, 0), comps };
}

/**
 * The enclosed near-white decision rows: per image `{image, total, comps}` (enclosedWhite) and the subject's
 * families.enclosedFg (undefined = never decided). Undecided with an image at >= block -> BLOCK naming the images; decided
 * -> PASS listing what the rule does with them; nothing enclosed -> PASS.
 */
export function whiteRows(images, enclosedFg, { block = DOCTOR.whiteBlock } = {}) {
  const list = images.filter((m) => m.comps.length);
  const fmt = (m) => `${m.image} ${(m.total * 100).toFixed(2)} % [${m.comps.slice(0, 3).map((k) => `${k.bbox.join(",")} ${(k.share * 100).toFixed(2)} %`).join("; ")}${m.comps.length > 3 ? `; +${m.comps.length - 3}` : ""}]`;
  if (!list.length) return [{ level: "PASS", id: "white", text: "no enclosed near-white region >= 0.1 % of the foreground" }];
  const big = list.filter((m) => m.total >= block - EPS);
  if (enclosedFg === undefined && big.length) {
    return [{ level: "BLOCK", id: "white", data: list, text: `enclosed near-white, families.enclosedFg undecided: ${big.map(fmt).join(" · ")} — classify each: a white part (enclosedFg true) or a see-through opening (holes seeds / enclosedFg false)` }];
  }
  return [{ level: "PASS", id: "white", data: list, text: `enclosed near-white ${enclosedFg === undefined ? "(< 0.5 % each)" : `decided (enclosedFg ${enclosedFg}: ${enclosedFg ? "foreground unless a holes seed" : "background"})`}: ${list.map(fmt).join(" · ")}` }];
}

/** Body colours too close to the background rule (darkest channel >= fgMax - margin: the mask erases the body) -> BLOCK. */
export function bodyColourRows(bodyRgb, fgMax, { margin = DOCTOR.bodyMargin } = {}) {
  const hex = (c) => `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
  const bad = (bodyRgb ?? []).filter((c) => Math.min(...c) >= fgMax - margin);
  return bad.length
    ? [{ level: "BLOCK", id: "body-colour", text: `body colour ${bad.map((c) => `${hex(c)} (darkest ${Math.min(...c)})`).join(", ")} >= fgMax ${fgMax} - ${margin}: the background rule eats the body — set families.fgMax above it (+${margin}) or enclosedFg true` }]
    : [{ level: "PASS", id: "body-colour", text: `body colours ${(bodyRgb ?? []).map(hex).join(", ")} clear of fgMax ${fgMax} by > ${margin}` }];
}

/**
 * Symmetric-axis centring of one view axis (a vehicle's x): the body-colour span centre (where the span rule puts the
 * origin) vs the foreground bbox centre and the foreground mass centre, metres along the image axis. Both off by more
 * than `tol` on the same side, no `shift` -> WARN "shift candidate" (the mean of the two); a set shift -> PASS, or WARN
 * when it lies more than 2 tol from that candidate.
 */
export function centringRow({ view, axis, dBox, dMass, shift = null, tol = DOCTOR.centre }) {
  const off = Math.abs(dBox) > tol + EPS && Math.abs(dMass) > tol + EPS && Math.sign(dBox) === Math.sign(dMass);
  const cand = (dBox + dMass) / 2;
  const at = `${view} ${axis}: fg bbox centre ${sgn(dBox, 3)} m, mass ${sgn(dMass, 3)} m from the body span centre`;
  if (shift !== null && shift !== undefined) {
    // a set shift far from what the masses say (> 2 tol) is worth a second look (it may use another rule)
    const far = Math.abs(shift - cand) > 2 * tol + EPS;
    return { level: far ? "WARN" : "PASS", id: `centring-${view}`, text: `${at} (shift ${sgn(shift, 3)} set${far ? `; the fg centres say ${sgn(cand, 3)}: re-measure it` : ""})` };
  }
  return off ? { level: "WARN", id: `centring-${view}`, data: { dBox, dMass }, text: `${at} — shift candidate ${sgn(cand, 3)} m (measure it, views.json ${view}.shift.${axis})` }
    : { level: "PASS", id: `centring-${view}`, text: at };
}

/** camera.json checks: provisional, residual_px >= 1.0, vertical_tilt_deg > 0.5 -> WARN each. */
export function cameraRows(camera, { residual = DOCTOR.cameraResidual, tilt = DOCTOR.cameraTilt } = {}) {
  const rows = [];
  if (!camera) return [{ level: "BLOCK", id: "camera", text: "no camera.json" }];
  if (camera.provisional !== false) rows.push({ level: "WARN", id: "camera", text: `camera.json provisional (${JSON.stringify(camera.provisional)}): solve it (scripts/solve-camera.mjs)` });
  if (Number.isFinite(camera.residual_px) && camera.residual_px >= residual) rows.push({ level: "WARN", id: "camera", text: `camera.json residual_px ${camera.residual_px} >= ${residual}` });
  if (Number.isFinite(camera.vertical_tilt_deg) && Math.abs(camera.vertical_tilt_deg) > tilt) rows.push({ level: "WARN", id: "camera", text: `camera world-up ${camera.vertical_tilt_deg} deg off vertical (> ${tilt})` });
  return rows.length ? rows : [{ level: "PASS", id: "camera", text: `camera solved (residual ${camera.residual_px ?? "?"} px${Number.isFinite(camera.vertical_tilt_deg) ? `, tilt ${camera.vertical_tilt_deg} deg` : ""})` }];
}

/** The gate on start.mjs: CLASS_CONFIG violations -> WARN (until the subject's WP2 overrides exist), any other -> BLOCK. */
export function gateRows(chain) {
  if (chain.error) return [{ level: "BLOCK", id: "gate", text: `chain on start.mjs threw: ${chain.error}` }];
  const cc = chain.violations.filter((v) => CLASS_CONFIG.includes(v.v));
  const other = chain.violations.filter((v) => !CLASS_CONFIG.includes(v.v));
  const fmt = (list) => list.slice(0, 6).map((v) => `${v.v}${v.part ? ` ${v.part}` : ""}`).join(", ") + (list.length > 6 ? `, +${list.length - 6}` : "");
  const rows = [];
  if (other.length) rows.push({ level: "BLOCK", id: "gate", text: `chain on start.mjs: ${fmt(other)}` });
  if (cc.length) rows.push({ level: "WARN", id: "gate-class", text: `chain class-config rows on start.mjs: ${fmt(cc)} — add the measured subject.json ruleOverrides (wheels / paletteZones, WP2)` });
  if (!rows.length) rows.push({ level: "PASS", id: "gate", text: `chain on start.mjs: pass ${chain.pass}, tris ${chain.tris}/${chain.budget}` });
  return rows;
}

/** The overall doctor verdict: BLOCK if any row blocks, WARN if any warns, else PASS. */
export function doctorVerdict(rows) {
  const n = (l) => rows.filter((r) => r.level === l).length;
  const level = n("BLOCK") ? "BLOCK" : n("WARN") ? "WARN" : "PASS";
  return { level, blocks: n("BLOCK"), warns: n("WARN") };
}

// ---------------------------------------------------------------------------------------------------------------------
// scaffold: dims and palette of a start taken from a gold module
// ---------------------------------------------------------------------------------------------------------------------

const DIM_KEYS = Object.freeze({ L: ["L"], W: ["W"], H: ["H"], R: ["wheelR", "R"] });
const r4 = (v) => Math.round(v * 1e4) / 1e4;

/**
 * The dimension values a scaffold sets (research/v7/WF-REVIEW-fable.md C10): the module's KNOBS L / W / H / wheelR (or R)
 * `.v`, else its top-level numeric DEFAULTS L / W / H / R, else a `const L = <n>;` the build derives the rest from
 * (`consts`, the pickup). Each keeps its own meaning (a taxi H is the roof over the sill): new = old x the target / source
 * ratio of that registered dimension (ortho.mjs reg.dims); the wheel radius from the target prior (stylisation.wheelDoverH
 * x H / 2) when it has one, else x the H ratio. A module with none keeps its size (absolute-metre golds: the frame and the
 * judge's sigma absorb a uniform scale, not proportion).
 * @returns {{where:"KNOBS"|"DEFAULTS"|"const", key:string, from:number, to:number, why:string}[]}
 */
export function dimsPlan({ knobs = null, defaults = null, consts = null, srcDims, dstDims, prior = null }) {
  const out = [];
  const val = (where, key) => (where === "KNOBS" ? knobs?.[key]?.v : where === "DEFAULTS" ? defaults?.[key] : consts?.[key]);
  for (const [D, keys] of Object.entries(DIM_KEYS)) {
    for (const where of ["KNOBS", "DEFAULTS", "const"]) {
      const key = keys.find((k) => Number.isFinite(val(where, k)));
      if (!key) continue;
      const from = val(where, key);
      let to, why;
      if (D === "R") {
        const dOverH = prior?.stylisation?.wheelDoverH;
        if (Number.isFinite(dOverH) && Number.isFinite(dstDims.H)) { to = dOverH * dstDims.H / 2; why = `prior stylisation.wheelDoverH ${dOverH} x H ${r4(dstDims.H)} / 2`; }
        else { to = from * dstDims.H / srcDims.H; why = `x H ratio ${r4(dstDims.H / srcDims.H)}`; }
      } else {
        to = from * dstDims[D] / srcDims[D];
        why = `x ${D} ratio ${r4(dstDims[D] / srcDims[D])} (turnaround ${r4(srcDims[D])} -> ${r4(dstDims[D])} m)`;
      }
      out.push({ where, key, from, to: r4(to), why });
      break;   // KNOBS win over DEFAULTS for the same dimension
    }
  }
  return out;
}

const hexRGB = (h) => [1, 3, 5].map((i) => parseInt(String(h).slice(i, i + 2), 16));
const rgbHex = (c) => `#${c.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("")}`;
const d2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;

/** The family (name, its colour list index) nearest a colour in a family table ({names, rgb}: ortho.mjs familyTable). */
function nearestFamily(table, c) {
  let best = null, bd = Infinity;
  for (let f = 1; f < table.names.length; f += 1) for (const q of table.rgb[f] ?? []) { const d = d2(c, q); if (d < bd) { bd = d; best = { name: table.names[f], base: q }; } }
  return best;
}

/**
 * One colour of a gold palette in a subject's colours: its nearest family in the SOURCE subject's table -> the target
 * table's family of the same name (its first colour), the offset from the source family colour kept per channel (cel
 * tones survive); a family the target lacks keeps the colour. A function of the hex alone (scaffold.mjs rewrites every hex
 * of the palette block with it).
 * @returns {{hex:string, family:string|null, moved:boolean}}
 */
export function remapColour(hex, srcTable, dstTable) {
  const c = hexRGB(hex);
  const src = nearestFamily(srcTable, c);
  const fi = src ? dstTable.names.indexOf(src.name) : -1;
  if (!src || fi < 1 || fi >= dstTable.names.length - 1 || !dstTable.rgb[fi]?.length) return { hex, family: src?.name ?? null, moved: false };
  const t = dstTable.rgb[fi][0];
  return { hex: rgbHex(c.map((v, k) => t[k] + (v - src.base[k]))), family: src.name, moved: true };
}

// ---------------------------------------------------------------------------------------------------------------------
// scaffold: module-text edits (the module stays hand-readable: values change in place, nothing is regenerated)
// ---------------------------------------------------------------------------------------------------------------------

/**
 * The module text with the concept frame knobs set to `fr` {scale, tx, ty} (step.mjs --save, scaffold.mjs): the KNOBS block
 * gains frameScale / frameX / frameY when it lacks them; a module without a KNOBS block gets one before its first export.
 */
export function withFrameKnobs(text, fr) {
  let t = text;
  if (!/\n\s*frameScale:\s*\{/.test(t)) {
    if (t.includes("export const KNOBS = {")) t = addFrameKnobs(t);
    else {
      const at = t.search(/^export /m);
      const block = `// concept-view similarity (scripts/registered.mjs framed): fitted by scripts/v7/frame.mjs / step.mjs\nexport const KNOBS = {\n${frameKnobLines().join("\n")}\n};\n\n`;
      t = at >= 0 ? t.slice(0, at) + block + t.slice(at) : `${t}\n${block}`;
    }
  }
  return replaceKnobValues(t, { frameScale: fr.scale, frameX: fr.tx, frameY: fr.ty });
}

/** [open, close] indices of the `{ ... }` whose `{` is the first one at or after `from` (strings and comments skipped). */
export function braceRange(text, from) {
  const open = text.indexOf("{", from);
  if (open < 0) return null;
  let depth = 0;
  for (let i = open; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === "/" && text[i + 1] === "/") { i = text.indexOf("\n", i); if (i < 0) return null; continue; }
    if (ch === "/" && text[i + 1] === "*") { i = text.indexOf("*/", i + 2) + 1; if (i <= 0) return null; continue; }
    if (ch === '"' || ch === "'" || ch === "`") { for (i += 1; i < text.length && text[i] !== ch; i += text[i] === "\\" ? 2 : 1); continue; }
    if (ch === "{" || ch === "[" || ch === "(") depth += 1;
    else if (ch === "}" || ch === "]" || ch === ")") { depth -= 1; if (depth === 0) return [open, i]; }
  }
  return null;
}

/**
 * Set top-level numeric entries (`key: <number>`) of the object literal that starts at `marker` (e.g. "export const
 * DEFAULTS = {"); nested objects are left alone. Throws when the block or a key is missing.
 */
export function setTopLevelValues(text, marker, values, fmt = (v) => String(Math.round(v * 1e4) / 1e4)) {
  const at = text.indexOf(marker);
  const range = at >= 0 ? braceRange(text, at) : null;
  if (!range) throw new Error(`no \`${marker}\` block`);
  let out = text;
  for (const [key, v] of Object.entries(values)) {
    const [open, close] = braceRange(out, at);
    let depth = 0, hit = -1;
    for (let i = open + 1; i < close && hit < 0; i += 1) {
      const ch = out[i];
      if (ch === "/" && out[i + 1] === "/") { i = out.indexOf("\n", i); continue; }
      if (ch === '"' || ch === "'" || ch === "`") { for (i += 1; i < close && out[i] !== ch; i += out[i] === "\\" ? 2 : 1); continue; }
      if (ch === "{" || ch === "[" || ch === "(") depth += 1;
      else if (ch === "}" || ch === "]" || ch === ")") depth -= 1;
      else if (depth === 0 && out.startsWith(key, i) && !/[\w$]/.test(out[i - 1]) && /^\s*:\s*-?[\d.]/.test(out.slice(i + key.length, i + key.length + 12))) hit = i;
    }
    if (hit < 0) throw new Error(`\`${marker}\` has no top-level numeric ${key}`);
    const m = /^(\s*:\s*)(-?[\d.]+(?:e-?\d+)?)/.exec(out.slice(hit + key.length));
    const s0 = hit + key.length + m[1].length;
    out = out.slice(0, s0) + fmt(v) + out.slice(s0 + m[2].length);
  }
  return out;
}

/** Every "#rrggbb" string literal inside [from, to) mapped through fn(hex) -> hex. */
export function mapHexIn(text, [from, to], fn) {
  return text.slice(0, from) + text.slice(from, to).replace(/(["'])#([0-9a-fA-F]{6})\1/g, (m, q, h) => `${q}${fn(`#${h.toLowerCase()}`)}${q}`) + text.slice(to);
}

/** The module text without its leading comment block (the `//` lines and blank lines before the first code line). */
export function stripHeader(text) {
  const lines = text.split(/\r?\n/);
  let i = 0;
  while (i < lines.length && (/^\s*\/\//.test(lines[i]) || !lines[i].trim())) i += 1;
  return lines.slice(i).join("\n");
}

/**
 * Remap a gold module's palette to a subject's colours (remapColour per zone colour; per-face entries per face).
 * @returns {{palette:object, rows:{zone:string, family:string|null, from:string, to:string}[]}}
 */
export function remapPalette(palette, srcTable, dstTable) {
  const rows = [];
  const map = (hex) => remapColour(hex, srcTable, dstTable);
  const out = {};
  for (const [zone, e] of Object.entries(palette ?? {})) {
    if (typeof e === "string") {
      const m = map(e);
      out[zone] = m.hex;
      rows.push({ zone, family: m.family, from: e, to: m.hex });
    } else if (e && typeof e === "object") {
      out[zone] = Object.fromEntries(Object.entries(e).map(([face, hex]) => [face, typeof hex === "string" ? map(hex).hex : hex]));
      const first = Object.values(e).find((x) => typeof x === "string");
      rows.push({ zone, family: first ? map(first).family : null, from: JSON.stringify(e), to: JSON.stringify(out[zone]) });
    } else out[zone] = e;
  }
  return { palette: out, rows };
}
