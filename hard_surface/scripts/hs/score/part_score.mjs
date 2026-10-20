// Per-part likeness score: ranks variants of ONE part of a hard-surface build against the subject's turnaround.
//
// The whole-view score (likeness_score.mjs) averages a part's change over the whole silhouette, so one part's
// variant moves it by 0.001-0.01. This score restricts the same kind of signals to the part's own region:
//
//   region  = the part's visible pixels from the build's ID pass (scripts/hs/score/part_pass.py: one flat colour per
//             ob["part"] role, same frame.json camera and sigma as the pass renders), moved by the view's silhouette
//             registration shift, closed (6 working px) + holes filled (bores, guard openings, windows), padded 4 px.
//             When several candidates are ranked, the region is the UNION of their regions, so every candidate is
//             measured over the same pixels (a scaled or moved part cannot shrink its own exam).
//   signals (inside the region, care px only):
//     sil    silhouette IoU of source vs build inside the region (a moved / scaled part shows here)
//     edge   F1 of Sobel edges (L* gradient > EDGE_T, silhouette edges included), matched within 1 working px (2 canvas)
//     ssim   SSIM on L*, 7x7 windows
//     tone   1 - mean |dL*| of 7x7-blurred L* / 25 over either silhouette (two-sided: darker and lighter cost the same)
//     value  1 - min(1, |mean L* source - mean L* build| / VALUE_SCALE), means over each image's own foreground px in
//            the region: a saturating, two-sided check of the part's overall value (an overshoot past the source's value
//            costs as much as the same undershoot). Reported per view as meanLS / meanLB (0..100).
//     open   openings, strengthened: (pixel F1 within 1 px + component F1 + area ratio) / 3 over opening maps
//            (see-through holes + notches/slots open to one side = background inside the 8-working-px closing of the
//            silhouette + dark recesses: L* < 30, < 65 % of their 21x21 surround AND < REC_REL x the median L* of that
//            image's own foreground in the region. The last term is new 2026-10-10: without it, painting a whole part
//            near-black turned its surface into "recesses" and won the open signal); a component counts as
//            found when >= 30 % of it is covered by the other map (dilated 1 px). Omitted (weight renormalised) when
//            neither image has an opening in the region.
//   part = sum_v w_v area_v * (weighted signal mean)_v / sum_v w_v area_v over the views where the part has >= MIN_PX px
//          (w = 1 for the orthos, CONCEPT_W for the concept view).
//
//   concept view (2026-10-10): the build's passN_concept.png (the judge's registered concept camera) vs the concept
//   painting (concept_cam.json "target", refs/<s>.png). The render is not pixel-aligned with the painting, so each part
//   is aligned locally (alignLocal): on the FIRST candidate (BASELINE), a scale (0.80..1.20) + translation (+-CONCEPT_R
//   working px) of the painting over the part's region dilated 8 px, by silhouette + gradient NCC with a pull toward the
//   global registration; every candidate reuses that alignment (as the ortho registration lock). The view is skipped for
//   a part when gradient NCC < CONCEPT_MIN_NCC or silhouette NCC < CONCEPT_MIN_FG, or a candidate has no concept ID pass
//   (part_pass.py before 2026-10-10).
//
//   node scripts/hs/score/part_score.mjs --subject <s> --part <role> --build <dir> [--build <dir> ...] [--prefix pass0_]
//        the first --build is the reference (BASELINE): the others reuse its registration shift (--own-shift: not)
//   node scripts/hs/score/part_score.mjs --subject <s> --build <dir> --all-parts            # own-region score per part
//
// <dir> holds <prefix>{side,front,rear,top}.png + <prefix>ids_<view>.bin + <prefix>ids.json (part_pass.py output).
// Calibration on controlled single-part variants: PART-CALIBRATION.md (part_calibrate.mjs).
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import {
  ROOT, N, VIEWS, analyse, boxMean, careMask, combine, enclosedBg, erode, loadRGB, maxFilter, normalise, shifted, sobel,
  sourceView, tolF1, iouOf, viewSignals, EDGE_T,
} from "./likeness_score.mjs";

export const PART_WEIGHTS = { edge: 0.22, ssim: 0.13, tone: 0.12, value: 0.10, sil: 0.18, open: 0.25 };
export const SIGNAL_KEYS = ["sil", "edge", "ssim", "tone", "value", "open"];
const MIN_PX = 12;          // working px of the part in a view for the view to count
const CLOSE_R = 6, PAD_R = 4, CONCAVE_R = 8;
const VALUE_SCALE = 0.20;   // |mean L* difference| (0..1) at which the value signal reaches 0
const REC_REL = 0.65;       // dark recess: darker than this x the image's own foreground median L* in the region
export const CONCEPT_W = 0.5, CONCEPT_R = 40, CONCEPT_MIN_NCC = 0.30, CONCEPT_MIN_FG = 0.75;

// ---------- loading ----------
function readIds(file, w, h) {
  const b = fs.readFileSync(file);
  if (b.length !== w * h) throw new Error(`${file}: ${b.length} bytes, expected ${w * h}`);
  return b;
}
/** part masks at the working resolution: a working px belongs to a part if any of its 4 canvas px does */
function partMasks(ids, w, nParts) {
  const masks = Array.from({ length: nParts }, () => new Uint8Array(N * N));
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const i0 = 2 * y * w + 2 * x;
    for (const k of [ids[i0], ids[i0 + 1], ids[i0 + w], ids[i0 + w + 1]]) if (k) masks[k - 1][y * N + x] = 1;
  }
  return masks;
}

/** lockTo: another loaded candidate whose per-view registration shift is reused (ranking variants of one part: a
 *  small part edit can flip the whole-view silhouette shift by 1 px, which moves every part's score by ~0.005-0.01) */
export async function loadCandidate(subject, dir, prefix = "pass0_", lockTo = null) {
  const meta = JSON.parse(fs.readFileSync(path.join(dir, `${prefix}ids.json`), "utf8"));
  const views = {}, whole = {};
  for (const v of VIEWS) {
    const S = await sourceView(subject, v), care = careMask(subject, v);
    const B0 = analyse(await loadRGB(path.join(dir, `${prefix}${v}.png`)));
    const sig = viewSignals(S, B0, care);
    whole[v] = normalise(sig);
    const [dx, dy] = lockTo ? lockTo.views[v].shift : [sig.dx, sig.dy];
    const sx = dx / 2, sy = dy / 2;                      // working px
    const B = { L: shifted(B0.L, sx, sy, 1), lab: shifted(B0.lab, sx, sy, 0), fg: shifted(B0.fg, sx, sy) };
    const V = meta.views[v];
    const masks = partMasks(readIds(path.join(dir, V.file), V.w, V.h), V.w, meta.parts.length).map((m) => shifted(m, sx, sy));
    views[v] = { B, masks, shift: [dx, dy], ownShift: [sig.dx, sig.dy] };
  }
  const w = combine(whole);
  const cand = { dir, parts: meta.parts, views, whole: { likeness: w.likeness, interior: w.interior, iou: w.iou }, concept: null };
  const C = meta.views.concept, cpng = path.join(dir, `${prefix}concept.png`);
  if (C && fs.existsSync(cpng) && fs.existsSync(path.join(dir, C.file))) {
    const Bc = analyse(await loadRGB(cpng));
    cand.concept = { B: Bc, masks: partMasks(readIds(path.join(dir, C.file), C.w, C.h), C.w, meta.parts.length) };
  }
  return cand;
}

// ---------- concept source + per-part local alignment ----------
const conceptCache = new Map();
export async function conceptSource(subject) {
  if (!conceptCache.has(subject)) {
    let target = `refs/${subject}.png`;
    try { target = JSON.parse(fs.readFileSync(path.join(ROOT, "out", "blender-hs", subject, "concept_cam.json"), "utf8")).target || target; } catch {}
    const f = path.join(ROOT, target);
    conceptCache.set(subject, fs.existsSync(f) ? { ...analyse(await loadRGB(f)), target } : null);
  }
  return conceptCache.get(subject);
}
const gradCache = new WeakMap();
function gradMag(img) { if (!gradCache.has(img)) gradCache.set(img, boxMean(sobel(img.L), 1)); return gradCache.get(img); }
/** best scale + translation q = c + s (p - c) + t (painting px q for build px p) over the window `win`.
 *  Objective = (NCC of the blurred silhouettes + NCC of the Sobel magnitudes) / 2 - ALIGN_REG_S |s - 1| - ALIGN_REG_T |t|/R:
 *  the silhouette term finds the part's place (robust to tone and line style), the gradient term its internal detail,
 *  and the regulariser keeps a self-similar part (a drum, a barrel cluster) near the judge's global concept registration
 *  instead of drifting to a scale bound. Coarse grid (step 4 px, every 2nd window px) then a +-3 px / +-0.02 refine.
 *  {ncc (gradient NCC), fgNcc, s, tx, ty, cx, cy, obj} or null. */
const ALIGN_REG_S = 0.5, ALIGN_REG_T = 0.05;
export function alignLocal(S, B, win) {
  const gS = gradMag(S), gB = gradMag(B), fS = fgBlur(S), fB = fgBlur(B), all = [];
  let cx = 0, cy = 0;
  for (let i = 0; i < N * N; i++) if (win[i]) { all.push(i); cx += i % N; cy += (i / N) | 0; }
  if (all.length < MIN_PX) return null;
  cx /= all.length; cy /= all.length;
  const prep = (idx) => {
    const n = idx.length, px = idx.map((i) => i % N), py = idx.map((i) => (i / N) | 0);
    const cen = (a) => { let m = 0; for (const i of idx) m += a[i]; m /= n; const d = new Float32Array(n); let v = 0;
      for (let k = 0; k < n; k++) { d[k] = a[idx[k]] - m; v += d[k] ** 2; } return { d, v }; };
    return { n, px, py, g: cen(gB), f: cen(fB) };
  };
  const coarse = prep(all.filter((_, k) => k % 2 === 0)), fine = prep(all);
  const vg = new Float32Array(all.length), vf = new Float32Array(all.length);
  const evalAt = (P, s, tx, ty) => {
    let sg = 0, sf = 0;
    for (let k = 0; k < P.n; k++) {
      const qx = Math.round(cx + s * (P.px[k] - cx) + tx), qy = Math.round(cy + s * (P.py[k] - cy) + ty);
      const j = qx >= 0 && qx < N && qy >= 0 && qy < N ? qy * N + qx : -1;
      sg += vg[k] = j >= 0 ? gS[j] : 0; sf += vf[k] = j >= 0 ? fS[j] : 0;
    }
    const mg = sg / P.n, mf = sf / P.n; let ag = 0, bg = 0, af = 0, bf = 0;
    for (let k = 0; k < P.n; k++) { const a = vg[k] - mg, b = vf[k] - mf; ag += a * P.g.d[k]; bg += a * a; af += b * P.f.d[k]; bf += b * b; }
    const ncc = bg && P.g.v ? ag / Math.sqrt(bg * P.g.v) : 0, fgNcc = bf && P.f.v ? af / Math.sqrt(bf * P.f.v) : 0;
    const obj = (ncc + fgNcc) / 2 - ALIGN_REG_S * Math.abs(s - 1) - ALIGN_REG_T * Math.hypot(tx, ty) / CONCEPT_R;
    return { ncc, fgNcc, s, tx, ty, obj };
  };
  let best = { obj: -9 };
  for (let s = 0.80; s <= 1.2001; s += 0.04)
    for (let ty = -CONCEPT_R; ty <= CONCEPT_R; ty += 4) for (let tx = -CONCEPT_R; tx <= CONCEPT_R; tx += 4) {
      const r = evalAt(coarse, s, tx, ty); if (r.obj > best.obj) best = r;
    }
  const b0 = best; best = { obj: -9 };
  for (const s of [b0.s - 0.02, b0.s, b0.s + 0.02]) for (let ty = b0.ty - 3; ty <= b0.ty + 3; ty++) for (let tx = b0.tx - 3; tx <= b0.tx + 3; tx++) {
    const r = evalAt(fine, s, tx, ty); if (r.obj > best.obj) best = r;
  }
  return { ...best, cx, cy };
}
const fgCache = new WeakMap();
function fgBlur(img) { if (!fgCache.has(img)) fgCache.set(img, boxMean(Float32Array.from(img.fg), 2)); return fgCache.get(img); }
/** the painting resampled into the build's frame by an alignLocal transform (nearest neighbour; outside = white) */
export function warpSource(S, T) {
  const L = new Float32Array(N * N).fill(1), lab = new Float32Array(N * N * 3), fg = new Uint8Array(N * N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const qx = Math.round(T.cx + T.s * (x - T.cx) + T.tx), qy = Math.round(T.cy + T.s * (y - T.cy) + T.ty), i = y * N + x;
    if (qx < 0 || qx >= N || qy < 0 || qy >= N) { lab[3 * i] = 100; continue; }
    const j = qy * N + qx;
    L[i] = S.L[j]; fg[i] = S.fg[j]; lab[3 * i] = S.lab[3 * j]; lab[3 * i + 1] = S.lab[3 * j + 1]; lab[3 * i + 2] = S.lab[3 * j + 2];
  }
  return { L, lab, fg };
}

// ---------- region ----------
function fillHoles(m) { const h = enclosedBg(m); return m.map((v, i) => v | h[i]); }
export function partRegion(mask) {
  let n = 0; for (const v of mask) n += v;
  if (n < MIN_PX) return null;
  const closed = erode(maxFilter(mask, CLOSE_R), CLOSE_R);
  return maxFilter(fillHoles(closed.map((v, i) => v | mask[i])), PAD_R);
}

// ---------- openings ----------
const openBase = new WeakMap();
/** fg median L* of `img` inside `env` (the region) */
function regionMedian(img, env) {
  const v = []; for (let i = 0; i < N * N; i++) if (env[i] && img.fg[i]) v.push(img.L[i]);
  if (!v.length) return 0; const b = Float32Array.from(v).sort(); return b[b.length >> 1];
}
function openMap(img, env) {
  if (!openBase.has(img)) openBase.set(img, { enc: enclosedBg(img.fg), loc: boxMean(img.L, 10),
    shut: erode(maxFilter(img.fg, CONCAVE_R), CONCAVE_R) });   // shut: notches / slots open to one side
  const { enc, loc, shut } = openBase.get(img), o = new Uint8Array(N * N);
  const thr = Math.min(0.30, REC_REL * regionMedian(img, env));
  for (let i = 0; i < N * N; i++) o[i] = enc[i] || (shut[i] && !img.fg[i]) || (img.fg[i] && img.L[i] < thr && img.L[i] < 0.65 * loc[i]) ? 1 : 0;
  return o;
}
function components(m, within, minPx = 3) {
  const lab = new Int32Array(N * N), comps = [], st = new Int32Array(N * N);
  for (let s = 0; s < N * N; s++) {
    if (!m[s] || !within[s] || lab[s]) continue;
    const px = []; let sp = 0; st[sp++] = s; lab[s] = comps.length + 1;
    while (sp) { const i = st[--sp]; px.push(i); const x = i % N, y = (i / N) | 0;
      for (const j of [x ? i - 1 : -1, x < N - 1 ? i + 1 : -1, y ? i - N : -1, y < N - 1 ? i + N : -1])
        if (j >= 0 && m[j] && within[j] && !lab[j]) { lab[j] = comps.length + 1; st[sp++] = j; } }
    if (px.length >= minPx) comps.push(px); else comps.push(null);
  }
  return comps.filter(Boolean);
}
function openSignal(oS, oB, env) {
  const cS = components(oS, env), cB = components(oB, env);
  let nS = 0, nB = 0; for (let i = 0; i < N * N; i++) if (env[i]) { nS += oS[i]; nB += oB[i]; }
  if (cS.length + cB.length === 0 && nS + nB < 3) return null;
  const pix = tolF1(oS, oB, env, 1).f1 ?? 1;
  const dS = maxFilter(oS, 1), dB = maxFilter(oB, 1);
  const found = (comps, other) => comps.filter((c) => c.reduce((s, i) => s + other[i], 0) >= 0.3 * c.length).length;
  const rec = cS.length ? found(cS, dB) / cS.length : (cB.length ? 0 : 1);
  const prec = cB.length ? found(cB, dS) / cB.length : (cS.length ? 0 : 1);
  const comp = rec + prec ? (2 * rec * prec) / (rec + prec) : 0;
  const area = Math.max(nS, nB) ? Math.min(nS, nB) / Math.max(nS, nB) : 1;
  return { open: (pix + comp + area) / 3, openPix: pix, openComp: comp, openArea: area, openSrcN: cS.length, openBuildN: cB.length };
}

// ---------- signals in a region ----------
const edgeCache = new WeakMap();
function edgeMap(img) {
  if (!edgeCache.has(img)) { const g = sobel(img.L); edgeCache.set(img, g.map((v) => (v > EDGE_T ? 1 : 0))); }
  return edgeCache.get(img);
}
const blurCache = new WeakMap();
function blurL(img) { if (!blurCache.has(img)) blurCache.set(img, boxMean(img.L, 3)); return blurCache.get(img); }
const ssimCache = new WeakMap();
function ssimMap(S, B) {     // per-px SSIM of S vs B (cached per (S, B))
  if (!ssimCache.has(B)) ssimCache.set(B, new WeakMap());
  let m = ssimCache.get(B).get(S); if (m) return m;
  const r = 3, mS = boxMean(S.L, r), mB = boxMean(B.L, r);
  const sSS = boxMean(S.L.map((v) => v * v), r), sBB = boxMean(B.L.map((v) => v * v), r), sSB = boxMean(S.L.map((v, i) => v * B.L[i]), r);
  const C1 = 0.01 ** 2, C2 = 0.03 ** 2; m = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) {
    const vs = sSS[i] - mS[i] ** 2, vb = sBB[i] - mB[i] ** 2, cv = sSB[i] - mS[i] * mB[i];
    m[i] = ((2 * mS[i] * mB[i] + C1) * (2 * cv + C2)) / ((mS[i] ** 2 + mB[i] ** 2 + C1) * (vs + vb + C2));
  }
  ssimCache.get(B).set(S, m); return m;
}
/** the build's L* inside the region mapped affinely onto the source's (fg mean and spread over env; gain clamped to
 *  0.5..2): the STRUCTURE signals (edge, ssim, open) compare shapes on this tone-matched image, so painting a part darker
 *  or lighter cannot buy edges / recesses; tone and value still compare the raw L*. Background px are left as they are. */
function toneMatched(S, B, env) {
  const st = (img) => { let n = 0, s1 = 0, s2 = 0; for (let i = 0; i < N * N; i++) if (env[i] && img.fg[i]) { n++; s1 += img.L[i]; s2 += img.L[i] ** 2; }
    const m = n ? s1 / n : 0; return { n, m, sd: n ? Math.sqrt(Math.max(0, s2 / n - m * m)) : 0 }; };
  const a = st(S), b = st(B);
  if (!a.n || !b.n) return B;
  const g = b.sd > 1e-4 ? Math.min(2, Math.max(0.5, a.sd / b.sd)) : 1, L = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) L[i] = B.fg[i] ? Math.min(1, Math.max(0, a.m + (B.L[i] - b.m) * g)) : B.L[i];
  return { L, lab: B.lab, fg: B.fg };
}
export const OPTS = { toneMatch: true };   // ablation switch (PART-CALIBRATION.md, 2026-10-10 section)
export function regionSignals(S, B, env) {
  const Bm = OPTS.toneMatch ? toneMatched(S, B, env) : B;
  let n = 0, ss = 0, dl = 0, nt = 0, nS = 0, lS = 0, nB = 0, lB = 0;
  const sm = ssimMap(S, Bm), bS = blurL(S), bB = blurL(B);
  for (let i = 0; i < N * N; i++) { if (!env[i]) continue; n++; ss += sm[i];
    if (S.fg[i]) { nS++; lS += S.L[i]; } if (B.fg[i]) { nB++; lB += B.L[i]; }
    if (S.fg[i] | B.fg[i]) { nt++; dl += Math.abs(bS[i] - bB[i]) * 100; } }
  const mS = nS ? lS / nS : null, mB = nB ? lB / nB : null;
  const out = {
    px: n,
    sil: iouOf(S.fg, B.fg, env),
    edge: tolF1(edgeMap(S), edgeMap(Bm), env, 1).f1 ?? 1,
    ssim: n ? ss / n : 0,
    tone: Math.max(0, 1 - (nt ? dl / nt : 0) / 25),
    value: mS === null || mB === null ? null : Math.max(0, 1 - Math.abs(mS - mB) / VALUE_SCALE),
    meanLS: mS === null ? null : 100 * mS, meanLB: mB === null ? null : 100 * mB,
  };
  const o = openSignal(openMap(S, env), openMap(Bm, env), env);
  Object.assign(out, o ?? { open: null });
  let t = 0, ws = 0;
  for (const [k, w] of Object.entries(PART_WEIGHTS)) if (out[k] !== null && out[k] !== undefined) { t += w * out[k]; ws += w; }
  out.score = t / ws;
  return out;
}

/** score `part` for every candidate over the SAME region (union of the candidates' regions); returns one row each.
 *  opts.concept (default true): add the concept view (weight CONCEPT_W x region area) when every candidate has a concept
 *  ID pass and the local alignment found on cands[0] is trustworthy (row.concept says what happened). */
export async function scorePart(subject, cands, part, opts = {}) {
  const useConcept = opts.concept ?? true;
  const res = cands.map(() => ({ views: {}, score: null }));
  const keys = ["score", ...SIGNAL_KEYS, "meanLS", "meanLB"];
  const sums = cands.map(() => Object.fromEntries(keys.flatMap((k) => [[k, 0], [k + "_w", 0]])));
  const add = (j, s, a) => { for (const k of keys) if (s[k] !== null && s[k] !== undefined) { sums[j][k] += a * s[k]; sums[j][k + "_w"] += a; } };
  const unionRegion = (masksOf) => {
    let U = null;
    for (const c of cands) {
      const k = c.parts.indexOf(part); if (k < 0) continue;
      const m = masksOf(c); if (!m) continue;
      const r = partRegion(m[k]); if (!r) continue;
      U = U ? U.map((x, i) => x | r[i]) : r;
    }
    return U;
  };
  let A = 0;
  for (const v of VIEWS) {
    const S = await sourceView(subject, v), care = careMask(subject, v);
    const U = unionRegion((c) => c.views[v].masks);
    if (!U) continue;
    const env = U.map((x, i) => x & care[i]);
    let a = 0; for (const x of env) a += x;
    if (a < MIN_PX) continue;
    A += a;
    cands.forEach((c, j) => { const s = regionSignals(S, c.views[v].B, env); s.px = a; s.weight = a; res[j].views[v] = s; add(j, s, a); });
  }
  let concept = { used: false, reason: "off" };
  if (useConcept) {
    const Sc = cands.every((c) => c.concept) ? await conceptSource(subject) : null;
    const U = Sc ? unionRegion((c) => c.concept.masks) : null;
    if (!Sc) concept = { used: false, reason: cands.every((c) => c.concept) ? "no concept painting" : "no concept ID pass" };
    else if (!U) concept = { used: false, reason: "part not visible in the concept view" };
    else {
      const ref = cands[0];
      ref.conceptAlign ??= {};
      const T = (ref.conceptAlign[part] ??= alignLocal(Sc, ref.concept.B, maxFilter(U, 8)));
      let a = 0; for (const x of U) a += x;
      concept = { used: !!(T && T.ncc >= CONCEPT_MIN_NCC && T.fgNcc >= CONCEPT_MIN_FG && a >= MIN_PX), px: a, align: T && { ncc: T.ncc, fgNcc: T.fgNcc, s: T.s, tx: T.tx, ty: T.ty, cx: T.cx, cy: T.cy }, target: Sc.target };
      if (!concept.used) concept.reason = `alignment too weak: gradient NCC ${T ? T.ncc.toFixed(2) : "-"} (min ${CONCEPT_MIN_NCC}), silhouette NCC ${T ? T.fgNcc.toFixed(2) : "-"} (min ${CONCEPT_MIN_FG})`;
      else {
        const Sw = warpSource(Sc, T), w = CONCEPT_W * a;
        concept.weight = w;
        A += w;
        cands.forEach((c, j) => { const s = regionSignals(Sw, c.concept.B, U); s.px = a; s.weight = w; res[j].views.concept = s; add(j, s, w); });
      }
    }
  }
  cands.forEach((c, j) => {
    if (!A) return;
    const s = sums[j], m = (k) => (s[k + "_w"] ? s[k] / s[k + "_w"] : null);
    Object.assign(res[j], { score: s.score / A, ...Object.fromEntries([...SIGNAL_KEYS, "meanLS", "meanLB"].map((k) => [k, m(k)])),
      regionPx: A, whole: c.whole.likeness, dir: c.dir, concept });
  });
  return res;
}

// ---------- cli ----------
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const argv = process.argv.slice(2), arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
  const all = (n) => argv.flatMap((a, i) => (a === n ? [argv[i + 1]] : []));
  const subject = arg("--subject"), part = arg("--part"), dirs = all("--build"), prefix = arg("--prefix") ?? "pass0_";
  if (!subject || !dirs.length || (!part && !argv.includes("--all-parts"))) {
    console.error("usage: node part_score.mjs --subject <s> (--part <role> --build <dir> [--build <dir> ...] | --build <dir> --all-parts) [--prefix pass0_] [--json]");
    process.exit(2);
  }
  const cands = [];
  // the first --build is the reference: every other candidate reuses its registration (--own-shift: each its own)
  for (const d of dirs) cands.push(await loadCandidate(subject, path.resolve(d), prefix, argv.includes("--own-shift") ? null : cands[0] ?? null));
  const r3 = (x) => (typeof x === "number" ? x.toFixed(3) : "  -  ");
  const parts = part ? [part] : cands[0].parts;
  const out = {};
  for (const p of parts) {
    out[p] = await scorePart(subject, part ? cands : [cands[0]], p);
    if (argv.includes("--json")) continue;
    console.log(`${subject} / ${p}`);
    console.log("  part   sil   edge  ssim  tone  value open  | meanL src build | whole  build | concept");
    out[p].forEach((r) => console.log(`  ${r3(r.score)} ${r3(r.sil)} ${r3(r.edge)} ${r3(r.ssim)} ${r3(r.tone)} ${r3(r.value)} ${r3(r.open)} | ${r.meanLS?.toFixed(1)} ${r.meanLB?.toFixed(1)} | ${r3(r.whole)}  ${path.relative(process.cwd(), r.dir ?? "")} | ${r.concept?.used ? `used ncc ${r.concept.align.ncc.toFixed(2)}` : r.concept?.reason}`));
  }
  if (argv.includes("--json")) console.log(JSON.stringify(out, (k, v) => (k === "views" ? undefined : typeof v === "number" ? Math.round(v * 1e5) / 1e5 : v)));
}
