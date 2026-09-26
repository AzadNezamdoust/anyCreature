// ACS engine — spec compiler (M1: static geometry). Author: Ariescar.
// Agent-first: input is plain JSON. Joints are explicit 3D points (the agent
// does the proportional reasoning; the engine does the meshing).
//
// spec = {
//   name, height?,
//   palette: { material: {color:'#rrggbb', rough?, metal?} },
//   joints: { JointName: [x,y,z], ... },
//   chains: { chainName: [JointName, ...], ... },
//   volumes: [ { chain, material, profile: [[t, w, h], ...], frame?: 'auto'|'up'|'ground',
//               caps?: [start,end]  // 'fan'|'ngon'|'none'  } ],
//   parts: [
//     { type:'spike', host:JointName, offset:[x,y,z], dir:[x,y,z],
//       segments:[{len, r}...], material },
//     { type:'eye', host:JointName, forward:[x,y,z], spread, up?, size, material }
//       // eyes are first-class: ALWAYS placed on the forward hemisphere of the host.
//   ],
//   mirror?: [chainName...]   // chains to duplicate across X (names prefixed L/R)
// }
'use strict';
const G = require('./geometry.js');

// compiler narration. A spec declares intent; the geometry that comes out is
// the resolved result, and the two diverge quietly. Every place the engine
// resolves something the author did not state exactly — the realized bend of a
// curve, the angle a plate was turned to meet its surface — it says so here.
const INFO = [];
function drainInfo() { const out = INFO.slice(); INFO.length = 0; return out; }
function dirName(v) {
  const p = [];
  if (v[1] > 0.4) p.push('up'); if (v[1] < -0.4) p.push('down');
  if (v[2] > 0.4) p.push('fwd'); if (v[2] < -0.4) p.push('back');
  if (Math.abs(v[0]) > 0.4) p.push('side');
  return p.join('-') || 'level';
}

// value noise (deterministic, no Date/random)
function hash3(x, y, z) {
  let h = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return h - Math.floor(h);
}
function vnoise(p, scale) {
  const q = p.map(v => v / scale);
  const f = q.map(v => v - Math.floor(v)), i = q.map(Math.floor);
  const sm = f.map(v => v * v * (3 - 2 * v));
  let acc = 0;
  for (let dx = 0; dx <= 1; dx++) for (let dy = 0; dy <= 1; dy++) for (let dz = 0; dz <= 1; dz++) {
    const w = (dx ? sm[0] : 1 - sm[0]) * (dy ? sm[1] : 1 - sm[1]) * (dz ? sm[2] : 1 - sm[2]);
    acc += w * hash3(i[0] + dx, i[1] + dy, i[2] + dz);
  }
  return acc; // 0..1
}
// sRGB hex → LINEAR. COLOR_0 is defined as linear by glTF, and ao.js / glb.js
// have always linearised; this one used to skip the transfer function, so any
// volume carrying a `colors` block shipped ~1.5x too bright and its value steps
// collapsed (wolf's spine-vs-base contrast fell from 5.3x to 2.1x).
function hex2lin(h) {
  const x = parseInt(h.replace('#', ''), 16);
  const s = c => Math.pow(c / 255, 2.2);
  return [s((x >> 16) & 255), s((x >> 8) & 255), s(x & 255)];
}

function lerpProfile(profile, t) { // rows [t, w, h, {exp,bias,roll}?]
  const row = (r) => [r[1], r[2], r[3] || null];
  if (t <= profile[0][0]) return row(profile[0]);
  for (let i = 0; i < profile.length - 1; i++) {
    const [t0, w0, h0] = profile[i], [t1, w1, h1] = profile[i + 1];
    if (t <= t1) {
      const f = (t - t0) / (t1 - t0 || 1);
      const s0 = profile[i][3] || {}, s1 = profile[i + 1][3] || {};
      const mix = (a, b, d) => (a ?? d) + ((b ?? d) - (a ?? d)) * f;
      return [w0 + (w1 - w0) * f, h0 + (h1 - h0) * f,
        { exp: mix(s0.exp, s1.exp, 2), bias: mix(s0.bias, s1.bias, 0), roll: mix(s0.roll, s1.roll, 0),
          section: f < 0.5 ? s0.section : s1.section }];
    }
  }
  const last = profile[profile.length - 1]; return row(last);
}

function chainPoints(spec, chainName) {
  const names = spec.chains[chainName];
  if (!names) throw new Error(`unknown chain "${chainName}"`);
  return names.map(n => {
    const p = spec.joints[n];
    if (!p) throw new Error(`chain "${chainName}" references missing joint "${n}"`);
    return p.slice();
  });
}

// Catmull-Rom through profile rows: fat, ROUND masses instead of straight frustums
function crProfile(profile, t) {
  const n = profile.length;
  if (t <= profile[0][0]) return lerpProfile(profile, t);
  if (t >= profile[n - 1][0]) return lerpProfile(profile, t);
  let i = 0; while (i < n - 2 && t > profile[i + 1][0]) i++;
  const P = k => profile[Math.min(n - 1, Math.max(0, k))];
  const [p0, p1, p2, p3] = [P(i - 1), P(i), P(i + 1), P(i + 2)];
  const sharpAt = r => r[3] && r[3].sharp;
  if (sharpAt(p1) || sharpAt(p2)) return lerpProfile(profile, t); // hard silhouette break
  const f = (t - p1[0]) / (p2[0] - p1[0] || 1);
  const cr = (a, b, c, d) => {
    const f2 = f * f, f3 = f2 * f;
    return 0.5 * ((2 * b) + (-a + c) * f + (2 * a - 5 * b + 4 * c - d) * f2 + (-a + 3 * b - 3 * c + d) * f3);
  };
  const sec = lerpProfile(profile, t)[2]; // sections stay linear
  return [Math.max(0.004, cr(p0[1], p1[1], p2[1], p3[1])),
          Math.max(0.004, cr(p0[2], p1[2], p2[2], p3[2])), sec];
}

// ── arc colours: bands around a ring-built mesh ─────────────────────────────
// Shared by volumes and curves. An arc is a band [from, to] in degrees from
// the section's top (0 = +W: the spine on a body chain, 180 = belly), applied
// in order, later ones over earlier ones, on top of the material colour.
//
// An arc may also be limited ALONG the chain: "t": [t0, t1] (fractions of
// the chain, default the whole of it). A saddle that stops at the withers,
// a pale muzzle on a dark head, a dark tail tip, a cream chest that does not
// run under the belly — none of these are a band around the whole chain, and
// without a t range the only way to get them was to cut the chain in two.
// The dome cap rings sit at t just outside [0, 1] and belong to the end row
// they extend.
//
// "feather" (degrees, default 0) softens the arc's angular edges and
// "feather_t" (a fraction of the chain, default 0) its t edges: the band's
// weight ramps from 0 at the edge to 1 that far inside it, so a saddle can
// melt into the flank instead of stopping on a ring line. Where the ramps
// overlap the arc is only partly applied — the seam-blend pass (L1) will not
// soften an edge inside one mass, so this is the only lever for that.
//
// The ramp is a smoothstep, and it is RESOLVED BY THE VERTICES: a vertex
// colour is interpolated linearly across each wall, so a feather narrower
// than the ring step (360/sides) lands between two vertices and does nothing,
// and one just wider than it puts ONE vertex on the ramp — a single kink, not
// a gradient. A gradient needs two or three vertices inside the ramp: 2-3x
// the step. The compiler says so when a feather is under the step, because
// the symptom — a hard-edged block where a soft band was written — looks like
// a colour bug and is not.
function arcColours(label, part, sides, ringT, rolls, base, colSpec, vIndex) {
  const arcs = (colSpec.arcs || []).map(a => {
    if (a.t !== undefined && !(Array.isArray(a.t) && a.t.length === 2))
      throw new Error(`${label}: an arc's "t" is [t0, t1] along the chain, got ${JSON.stringify(a.t)}`);
    if (!a.color) throw new Error(`${label}: an arc needs a "color"`);
    return { from: a.from ?? 0, to: a.to ?? 180, t0: a.t ? a.t[0] : 0, t1: a.t ? a.t[1] : 1, c: hex2lin(a.color),
             fa: Math.max(0, a.feather || 0), ft: Math.max(0, a.feather_t || 0) };
  });
  const step = 360 / sides;
  // ring spacing along t: the median gap between consecutive rings inside [0,1]
  const gaps = [];
  for (let i = 1; i < ringT.length; i++) {
    const g = ringT[i] - ringT[i - 1];
    if (g > 1e-9 && ringT[i] <= 1 + 1e-9 && ringT[i - 1] >= -1e-9) gaps.push(g);
  }
  gaps.sort((x, y) => x - y);
  const tStep = gaps.length ? gaps[gaps.length >> 1] : 1;
  for (const a of arcs) {
    const edged = (a.from > 0 && a.fa > 0) || (a.to < 180 && a.fa > 0);
    if (edged && a.fa < step)
      INFO.push(`WARN ${label}: arc ${a.from}..${a.to}° has "feather": ${a.fa} but the ring step is `
        + `${step.toFixed(1)}° (${sides} sides) — a feather narrower than the step lands between two `
        + `vertices and does nothing; the band ships with a hard edge. Write it at 2-3x the step `
        + `(${Math.round(step * 2)}-${Math.round(step * 3)}°) for a gradient, or raise "sides".`);
    const tEdged = (a.t0 > 0 || a.t1 < 1) && a.ft > 0;
    if (tEdged && a.ft < tStep)
      INFO.push(`WARN ${label}: arc t ${a.t0}..${a.t1} has "feather_t": ${a.ft} but the rings are `
        + `${tStep.toFixed(3)} apart in t — a feather narrower than the ring spacing lands between `
        + `two rings and does nothing. Write it at 2-3x the spacing (${(tStep * 2).toFixed(2)}-`
        + `${(tStep * 3).toFixed(2)}), or lower "ring_step".`);
  }
  // 1 inside, 0 outside, smoothstep over f inside each CLOSED edge. A band
  // touching 0 or 180 (or t 0 or 1) is open on that side: nothing to feather.
  const edgeW = (x, lo, hi, f, openLo, openHi) => {
    if (x < lo - 1e-9 || x > hi + 1e-9) return 0;
    if (!(f > 0)) return 1;
    let u = 1;
    if (!openLo) u = Math.min(u, (x - lo) / f);
    if (!openHi) u = Math.min(u, (hi - x) / f);
    u = Math.max(0, Math.min(1, u));
    return u * u * (3 - 2 * u);
  };
  const C = part.v.map(() => null);
  part.rings.forEach((ring, s2) => {
    const tt = Math.min(1, Math.max(0, ringT[s2]));
    const roll = (rolls && rolls[s2]) || 0;
    ring.forEach((pnt, k) => {
      const vi = vIndex.get(pnt);
      const aDeg = ((360 * k / sides + roll * 180 / Math.PI) % 360 + 360) % 360;
      const fromTop = (450 - aDeg) % 360;                 // 0=top(+W), 180=bottom
      const sym = fromTop > 180 ? 360 - fromTop : fromTop; // symmetric 0..180
      let c = base;
      for (const a of arcs) {
        const wa = edgeW(sym, a.from, a.to, a.fa, a.from <= 0, a.to >= 180);
        const wt = edgeW(tt, a.t0, a.t1, a.ft, a.t0 <= 0, a.t1 >= 1);
        const w = wa * wt;
        if (w > 0) c = [c[0] + (a.c[0] - c[0]) * w, c[1] + (a.c[1] - c[1]) * w, c[2] + (a.c[2] - c[2]) * w];
      }
      C[vi] = c.slice();
    });
  });
  for (let i = 0; i < C.length; i++) if (!C[i]) C[i] = base.slice();
  return C;
}

function buildVolume(spec, vol) {
  const sides = vol.sides || 12;
  const joints = chainPoints(spec, vol.chain);
  // arc-length table over the joint polyline
  const jArc = [0];
  for (let i = 1; i < joints.length; i++) jArc.push(jArc[i - 1] + G.len(G.sub(joints[i], joints[i - 1])));
  const total = jArc[jArc.length - 1] || 1;
  // DENSE resample: ring every ~step of arc, joints no longer dictate density
  const step = vol.ring_step || Math.max(0.035, total / 36);
  const M = Math.max(joints.length, Math.min(48, Math.round(total / step)));
  const pts = []; const ringT = []; const ringSkin = [];
  const names = spec.chains[vol.chain];
  for (let m = 0; m <= M; m++) {
    const a = (m / M) * total;
    let i = 0; while (i < jArc.length - 2 && a > jArc[i + 1]) i++;
    const f = (a - jArc[i]) / (jArc[i + 1] - jArc[i] || 1);
    pts.push(G.add(G.mul(joints[i], 1 - f), G.mul(joints[i + 1], f)));
    ringT.push(a / total);
    // snap-style skinning: blend the two bracketing joints, smoothstep for soft bends
    const sf = f * f * (3 - 2 * f);
    ringSkin.push(sf < 0.001 ? [[names[i], 1]] : sf > 0.999 ? [[names[i + 1], 1]]
      : [[names[i], 1 - sf], [names[i + 1], sf]]);
  }
  let prof = ringT.map(t => crProfile(vol.profile, t));
  // corner bevel-skip: at sharp path corners, rings inside the compression
  // zone (r·tan(θ/2)) would interpenetrate on the inner side — drop them and
  // let one span bridge the corner. Kills the fold class at any bend.
  {
    const keep = pts.map(() => true);
    for (let m = 1; m < pts.length - 1; m++) {
      const d0 = G.nrm(G.sub(pts[m], pts[m - 1])), d1 = G.nrm(G.sub(pts[m + 1], pts[m]));
      const cosA = Math.max(-1, Math.min(1, G.dot(d0, d1)));
      const th = Math.acos(cosA);
      if (th < 0.17) continue; // <10°: harmless
      const r = Math.max(prof[m][0], prof[m][1]);
      const ex = r * Math.tan(th / 2) * 1.2;
      for (let k = 1; k < pts.length - 1; k++) {
        if (k === m || !keep[k]) continue;
        const d = G.len(G.sub(pts[k], pts[m]));
        if (d < ex) keep[k] = false;
      }
    }
    const f = (arr) => arr.filter((_, i) => keep[i]);
    const pts2 = f(pts), prof2 = f(prof), rt2 = f(ringT), rs2 = f(ringSkin);
    pts.length = 0; pts.push(...pts2);
    prof = prof2; ringT.length = 0; ringT.push(...rt2);
    ringSkin.length = 0; ringSkin.push(...rs2);
  }
  // profile slope warning — the precursor to the fold class. `ring_step` sets how
  // far apart rings sit; the profile sets how fast the radius changes. When the
  // radius moves further between two rings than the rings are apart, the surface
  // turns more than 45° in one span and the next bend flips triangles. Scaling a
  // volume up without scaling `ring_step` with it is the usual way in — and the
  // failure surfaces much later, as "N flipped tris" during an animation.
  {
    let worst = 0, at = 0;
    for (let m = 1; m < pts.length; m++) {
      const ds = G.len(G.sub(pts[m], pts[m - 1]));
      if (ds < 1e-6) continue;
      const dr = Math.max(Math.abs(prof[m][0] - prof[m - 1][0]), Math.abs(prof[m][1] - prof[m - 1][1]));
      const slope = dr / ds;
      if (slope > worst) { worst = slope; at = ringT[m]; }
    }
    if (worst > 0.8) {
      const r = Math.max(prof[0][0], prof[0][1]);
      INFO.push(`WARN volume "${vol.chain}": profile slope ${worst.toFixed(2)} at t=${at.toFixed(2)} `
        + `(ring spacing ${(vol.ring_step || Math.max(0.035, total / 36)).toFixed(3)} vs radius ~${r.toFixed(3)}) `
        + `— rings are crowded relative to how fast the radius changes; this is the shape that flips `
        + `triangles once it bends. Raise "ring_step" on this volume, or soften the profile row there.`);
    }
  }

  const frame = vol.frame === 'up' ? true : vol.frame === 'ground' ? 'ground' : false;
  const resolveSec = (s) => {
    if (!s) return {};
    if (typeof s === 'string') s = { section: s };
    if (s.section) {
      const pp = (spec.sections || {})[s.section];
      if (!pp) throw new Error(`unknown named section "${s.section}"`);
      return { ...s, pts: pp };
    }
    return s;
  };
  const secs = prof.map(r => resolveSec(r[2] || vol.section));
  const rr = prof.map(r => [r[0], r[1]]);
  const rings = require('./section.js').chainRingsRich(pts, rr, sides, frame, secs);
  // ── dome caps are REAL domes ──────────────────────────────────────────────
  // A "dome" used to be a fan cap with its centre pushed out by 15% of the ring
  // radius: a lid, not a dome. Every tube ended in a chopped-off disc — muzzle
  // tips, rumps, tail ends, the free end of every leg — and the lid's rim was a
  // hard silhouette corner on an organic mass. Now the end ring is followed by
  // `cap_rings` (default 3) shrinking rings lifted along the chain axis on a
  // quarter-ellipse, and the fan closes only the small final ring. The dome's
  // depth is `cap_depth` (default 0.8) times the end ring's smaller radius, so
  // an elliptical section gets a correspondingly flattened dome. Everything
  // downstream that walks rings — skinning, arc colours, anchors, UV islands,
  // the containment checks — sees the extra rings as ordinary rings: same
  // bracketing joints, t just outside [0,1] so anchor lookups are untouched.
  const wantCaps = (vol.caps || ['ngon', 'ngon']).slice();
  let dome0 = 0;                     // rings a START dome prepended; rings[dome0] is the root ring
  const domeD = Math.max(1, Math.min(6, vol.cap_rings ?? 3)) | 0;
  const domeDepth = k => {
    const d = Array.isArray(vol.cap_depth) ? vol.cap_depth[k] : vol.cap_depth;
    return Math.max(0.05, Math.min(1.5, d ?? 0.8));
  };
  for (const end of [0, 1]) {
    if (wantCaps[end] !== 'dome' || pts.length < 2) continue;
    const s = end ? pts.length - 1 : 0;
    const c = pts[s], nb = pts[end ? s - 1 : 1];
    const ax = G.nrm(G.sub(c, nb));
    const rmin = Math.min(prof[s][0], prof[s][1]);
    const depth = domeDepth(end) * rmin;
    const extra = [], ec = [], et = [];
    for (let j = 1; j <= domeD; j++) {
      const phi = (j / (domeD + 1)) * Math.PI / 2;
      const sc = Math.cos(phi), lift = Math.sin(phi) * depth;
      extra.push(rings[s].map(q => G.add(G.add(c, G.mul(G.sub(q, c), sc)), G.mul(ax, lift))));
      ec.push(G.add(c, G.mul(ax, lift)));
      et.push(ringT[s] + (end ? 1 : -1) * lift / total);
    }
    const sk = () => ringSkin[s].map(x => x.slice());
    if (end) {
      rings.push(...extra); pts.push(...ec); ringT.push(...et);
      for (let j = 0; j < domeD; j++) { ringSkin.push(sk()); secs.push(secs[s]); prof.push(prof[s]); }
    } else {
      rings.unshift(...extra.reverse()); pts.unshift(...ec.reverse()); ringT.unshift(...et.reverse());
      for (let j = 0; j < domeD; j++) { ringSkin.unshift(sk()); secs.unshift(secs[s]); prof.unshift(prof[s]); }
      dome0 = domeD;
    }
    wantCaps[end] = 'fan';
  }
  const caps = wantCaps;
  const part = G.partFromRings(rings, sides, caps[0], caps[1], pts);
  // snap skinning: each ring blends its two bracketing joints
  const vIndex = new Map(); part.v.forEach((p, i) => vIndex.set(p, i));
  const skin = part.v.map(() => null);
  part.rings.forEach((ring, s) => {
    for (const p of ring) skin[vIndex.get(p)] = ringSkin[s].map(x => x.slice());
  });
  part.v.forEach((p, i) => {
    if (skin[i]) return;
    const d0 = G.len(G.sub(p, pts[0])), d1 = G.len(G.sub(p, pts[pts.length - 1]));
    skin[i] = [[d0 < d1 ? names[0] : names[names.length - 1], 1]];
  });
  // ── vertex colours: arc bands (0°=spine, 180°=belly) ─────────────────────
  const colSpec = vol.colors || {};
  const base = hex2lin((spec.palette[vol.material] || {}).color || '#888888');
  const C = arcColours(`volume "${vol.chain}"`, part, sides, ringT, secs.map(s2 => (s2 && s2.roll) || 0),
    base, colSpec, vIndex);
  // gradient and noise are NOT applied here any more — they are one whole-body
  // pass in applyShading() below, so every mesh (paws, ears, eyes included)
  // shares one top-to-bottom ramp and one grain size. Arc bands stay local.
  if (colSpec.gradient || colSpec.noise)
    INFO.push(`volume "${vol.chain}": colors.gradient/noise are ignored — shading is one spec-level pass now (see "shading")`);
  return { material: vol.material, V: part.v, F: part.fq, skin, C, chain: vol.chain,
    faceted: vol.faceted,
    _rings: part.rings, _pts: pts, _sides: sides, _ringT: ringT.slice(), _dome0: dome0,
    _open: [caps[0] === 'none', caps[1] === 'none'],   // which end rings are left open (the open_end check)
    _ringIdx: part.rings.map(ring => ring.map(p => vIndex.get(p))) };
}

// surface point of a built volume at (t along chain, angle from top in degrees).
// Rings are indexed by their true arc-length t (_ringT), NOT by array position —
// bevel-skip drops rings, so index-proportional lookup lands on the wrong ring.
function surfacePoint(builtVols, anchor) {
  const bv = builtVols[anchor.chain];
  if (!bv) throw new Error(`anchor chain "${anchor.chain}" has no built volume`);
  const rt = bv._ringT; const n = rt.length;
  let s1 = 0; while (s1 < n - 1 && rt[s1] < anchor.t) s1++;
  const s0 = Math.max(0, s1 - 1);
  const span = rt[s1] - rt[s0];
  const f0 = span > 1e-9 ? Math.min(1, Math.max(0, (anchor.t - rt[s0]) / span)) : 0;
  const N = bv._sides;
  const fromTop = ((anchor.around % 360) + 360) % 360;
  const aDeg = (450 - fromTop) % 360;
  const kf = (aDeg / 360) * N;
  const k0 = Math.floor(kf) % N, k1 = (k0 + 1) % N, f = kf - Math.floor(kf);
  const at = s => G.add(G.mul(bv._rings[s][k0], 1 - f), G.mul(bv._rings[s][k1], f));
  const p = G.add(G.mul(at(s0), 1 - f0), G.mul(at(s1), f0));
  const c = G.add(G.mul(bv._pts[s0], 1 - f0), G.mul(bv._pts[s1], f0));
  const out = G.nrm(G.sub(p, c));
  return { p, out, center: c };
}

function buildSpike(spec, p) {
  const host = spec.joints[p.host];
  if (!host) throw new Error(`spike host joint "${p.host}" missing`);
  const dir = G.nrm(p.dir); const pts = [G.add(host, p.offset || [0, 0, 0])];
  const radii = [p.segments[0].r];
  for (const s of p.segments) { pts.push(G.add(pts[pts.length - 1], G.mul(dir, s.len))); radii.push(Math.max(s.r * 0.35, 0.004)); }
  const rings = G.chainRings(pts, radii, p.sides || 6, false);
  const part = G.partFromRings(rings, p.sides || 6, 'ngon', 'fan', pts);
  return { material: p.material, V: part.v, F: part.fq, join: p.join,
    _seatIdx: Array.from({ length: p.sides || 6 }, (_, i) => i),  // base ring = the part's socket
    _path: pts.map(q => q.slice()),                               // the centreline, for a part seated on this one
    skin: part.v.map(() => [[p.host, 1]]) };
}

function buildEye(spec, p, builtVols) {
  // First-class eyes: placed on the FORWARD hemisphere of the host joint,
  // spread apart on ±X, always looking along `forward` (default +Z).
  const host = spec.joints[p.host];
  if (!host) throw new Error(`eye host joint "${p.host}" missing`);
  const fwd = G.nrm(p.forward || [0, 0, 1]);
  const up = G.nrm(p.up || [0, 1, 0]);
  const side = G.nrm(G.cross(up, fwd));
  const out = [];
  for (const sx of [1, -1]) {
    let c;
    if (p.anchor) { // ride ON the volume surface, bulging out
      // "sink": how much of the radius is buried (default 0.35). A skull that
      // narrows toward the brow lets the far eye poke out past the silhouette
      // at 0.35; 0.5 keeps it a bulge instead of a bead.
      const sp = surfacePoint(builtVols, { ...p.anchor, around: p.anchor.around * sx });
      c = G.add(sp.p, G.mul(sp.out, -(p.size ?? 0.05) * (p.sink ?? 0.35)));
    } else {
      c = G.add(G.add(G.add(host, G.mul(fwd, p.face ?? 0.9 * (p.dist ?? 0.3))),
        G.mul(side, sx * (p.spread ?? 0.15))), G.mul(up, p.height ?? 0));
    }
    const r = p.size ?? 0.05;
    const iris = sphereMesh(c, r, p.subdiv ?? 1);
    out.push({ material: p.material || 'eye', V: iris.V, F: iris.F, side: sx > 0 ? 'L' : 'R',
      skin: iris.V.map(() => [[p.host, 1]]) });
    // ── the pupil, placed by the engine ─────────────────────────────────────
    // An eye reads because of the value step between iris and pupil, not
    // because of the iris colour; a lone sphere is a sticker. "pupil": {} on the
    // eye entry puts a smaller, darker sphere on the FRONT of the iris — where
    // the iris actually landed, seated so it neither buries nor floats. Options:
    // material (default "pupil"), size (fraction of the iris, default 0.55),
    // look ([x,y,z] world direction the pupil sits toward; default is the
    // surface normal blended toward forward, i.e. the creature looks ahead).
    if (p.pupil) {
      const pp = typeof p.pupil === 'object' ? p.pupil : {};
      const rp = r * (pp.size ?? 0.55);
      let look;
      if (pp.look) look = G.nrm([pp.look[0] * sx, pp.look[1], pp.look[2]]);
      else if (p.anchor) {
        const sp = surfacePoint(builtVols, { ...p.anchor, around: p.anchor.around * sx });
        look = G.nrm(G.add(sp.out, G.mul(fwd, 0.9)));
      } else look = fwd;
      const pc = G.add(c, G.mul(look, r - rp * 0.45));
      const pm = sphereMesh(pc, rp, 1);
      out.push({ material: pp.material || 'pupil', V: pm.V, F: pm.F, side: sx > 0 ? 'L' : 'R',
        sub: 'pupil', skin: pm.V.map(() => [[p.host, 1]]) });
    }
  }
  return out;
}

// octahedron subdivided `sub` times and projected to a sphere of radius r at c
function sphereMesh(c, r, sub) {
  let V = [[0,1,0],[0,-1,0],[1,0,0],[-1,0,0],[0,0,1],[0,0,-1]];
  let F = [[0,4,2],[0,2,5],[0,5,3],[0,3,4],[1,2,4],[1,5,2],[1,3,5],[1,4,3]];
  for (let s = 0; s < Math.max(1, sub | 0); s++) {
    const cache = new Map(); const NF = [];
    const mid = (a, b) => {
      const k = a < b ? a + '_' + b : b + '_' + a;
      if (cache.has(k)) return cache.get(k);
      V.push(G.nrm(G.add(V[a], V[b]))); cache.set(k, V.length - 1); return V.length - 1;
    };
    for (const [a, b, d] of F) {
      const ab = mid(a, b), bd = mid(b, d), da = mid(d, a);
      NF.push([a, ab, da], [ab, b, bd], [da, bd, d], [ab, bd, da]);
    }
    F = NF;
  }
  return { V: V.map(v => G.add(c, G.mul(v, r))), F };
}

function buildCurve(spec, p) {
  // Curved tapering tube — horns, tusks, trunks, tentacles. Each segment's
  // steering is applied on top of the heading it inherits, so bends ADD UP
  // down the chain: `rise`/`fall`/`ahead`/`behind` pull the heading that many
  // degrees toward the matching world axis, and `coil` swings it in the plane
  // carried along with the tube, which is what produces rings and spirals.
  // Because they accumulate, four mild segments can end up pointing somewhere
  // nobody predicted, so the realized path is reported as one info line rather
  // than discovered in the render.
  const host = spec.joints[p.host];
  if (!host) throw new Error(`curve host joint "${p.host}" missing`);
  let t = G.nrm(p.dir || [0, 0, 1]);
  let side = Math.abs(t[1]) < 0.9 ? G.nrm(G.cross([0, 1, 0], t)) : [1, 0, 0];
  const rad = d => d * Math.PI / 180;
  const pts = [G.add(host, p.offset || [0, 0, 0])];
  // a segment's "r" may be [rw, rh] — an ELLIPTICAL section, which is what an
  // ear, a flattened tail or a paddle-shaped tusk needs; "roll" (degrees) turns
  // the section in its plane. taper pinches whichever form was given.
  const rOf = (r, k) => Array.isArray(r) ? r.map(x => Math.max(x * k, 0.004)) : Math.max(r * k, 0.004);
  const radii = [rOf(p.segments[0].r, 1)];
  const AX = { rise: [0, 1, 0], fall: [0, -1, 0], ahead: [0, 0, 1], behind: [0, 0, -1] };
  for (const seg of p.segments) {
    for (const [k, dv] of Object.entries(AX)) {
      if (!seg[k]) continue;
      const ax = G.cross(t, dv), l = G.len(ax);
      if (l < 1e-6) continue;
      const axn = G.mul(ax, 1 / l);
      t = G.nrm(G.rod(t, axn, rad(seg[k])));
      side = G.nrm(G.rod(side, axn, rad(seg[k])));
    }
    if (seg.coil) t = G.nrm(G.rod(t, side, rad(seg.coil)));
    pts.push(G.add(pts[pts.length - 1], G.mul(t, seg.len)));
    radii.push(rOf(seg.r, seg.taper ? 0.3 : 1));
  }
  const sides = p.sides || 8;
  const roll = rad(p.roll || 0);
  const rings = roll
    ? require('./section.js').chainRingsRich(pts, radii, sides, false, radii.map(() => ({ roll })))
    : G.chainRings(pts, radii, sides, false);
  const path = pts.map(q => q.slice());   // the centreline before any dome rings: what a hosted part seats on
  // "cap": "dome" rounds the far end the way volumes do (a horn tip is sharp,
  // an ear or a tongue is not); default stays the flat fan.
  if (p.cap === 'dome' && pts.length >= 2) {
    const s = pts.length - 1, c = pts[s], ax = G.nrm(G.sub(c, pts[s - 1]));
    const rr = Array.isArray(radii[s]) ? Math.min(...radii[s]) : radii[s];
    const D = 2;
    for (let j = 1; j <= D; j++) {
      const phi = (j / (D + 1)) * Math.PI / 2;
      const sc = Math.cos(phi), lift = Math.sin(phi) * rr * (p.cap_depth ?? 0.8);
      rings.push(rings[s].map(q => G.add(G.add(c, G.mul(G.sub(q, c), sc)), G.mul(ax, lift))));
      pts.push(G.add(c, G.mul(ax, lift)));
    }
  }
  const part = G.partFromRings(rings, sides, 'ngon', 'fan', pts);
  const d0 = G.nrm(p.dir || [0, 0, 1]);
  const bend = Math.acos(Math.max(-1, Math.min(1, G.dot(d0, t)))) * 180 / Math.PI;
  const dy = pts[pts.length - 1][1] - pts[0][1];
  if (bend > 15) INFO.push(`curve '${p.name || p.host}': steering accumulated to ${bend.toFixed(0)}° — starts ${dirName(d0)}, finishes ${dirName(t)}, far end ${dy >= 0 ? '+' : ''}${dy.toFixed(2)} in y`);
  // A curve takes "colors": {"arcs": [...]} like a volume: t runs 0 at the root
  // to 1 at the far end, and the angle is read in the curve's OWN frame, which
  // is a parallel-transport frame off its first heading — not the body's
  // spine/belly. So where 0° faces is printed (the pale inside of an ear, the
  // dark upper edge of a horn: read that line, do not reason from the body).
  let C;
  if (p.colors && p.colors.arcs && p.colors.arcs.length) {
    const arc = [0]; for (let i = 1; i < pts.length; i++) arc.push(arc[i - 1] + G.len(G.sub(pts[i], pts[i - 1])));
    const total = arc[arc.length - 1] || 1;
    const ringT = arc.map(a => a / total);
    const vIndex = new Map(); part.v.forEach((q, i) => vIndex.set(q, i));
    const base = hex2lin((spec.palette[p.material] || {}).color || '#888888');
    C = arcColours(`curve "${p.name || p.host}"`, part, sides, ringT, rings.map(() => roll), base, p.colors, vIndex);
    const { fr } = G.framesOf(pts.slice(0, Math.max(2, pts.length)), false);
    const W = fr[0][1], U = fr[0][0];
    INFO.push(`curve '${p.name || p.host}': colours — 0° faces ${dirName(W)} (world ${W.map(x => x.toFixed(2)).join(',')}), `
      + `90° faces ${dirName(U)} (world ${U.map(x => x.toFixed(2)).join(',')}), 180° faces ${dirName(G.mul(W, -1))}`);
  }
  return { material: p.material, V: part.v, F: part.fq, faceted: p.faceted, join: p.join, C,
    _seatIdx: Array.from({ length: sides }, (_, i) => i),  // base ring = the part's socket
    _path: path,
    skin: part.v.map(() => [[p.host, 1]]) };
}

// ── a part seated on a part ────────────────────────────────────────────────
// "host_part": "<name>" seats a part on another part instead of on a joint —
// a claw on a curve toe, a barb on a spine, a bell on a tentacle. It used to
// be refused: part_seat and part_attachment measured only against VOLUMES, so
// a claw seated 12 mm deep in a curve toe read as floating, and the only way
// round it was to make every toe a chain with its own joints.
//
//   host_part  the name of an EARLIER part in the list (it has to exist to be
//              seated on)
//   at         0..1 along the host's centreline (a curve or a spike), default
//              1 = the far end; the part's origin lands there, plus "offset"
//   dir        defaults to the host centreline's tangent at that point
//   host       defaults to the host part's own joint — only the fallback
//
// The seated part's skin weights are INHERITED from the host part (each vertex
// takes the weights of the host's nearest vertex), so it moves with whatever
// the host moves with, and the checks measure it against the host part's own
// surface. A host with no centreline (a fin, a paw, a hand) seats the part at
// its joint + offset, and "dir" is then required.
function resolveHostPart(spec, p, byName) {
  const hp = byName.get(p.host_part);
  if (!hp) {
    const later = (spec.parts || []).some(x => x.name === p.host_part);
    throw new Error(`part "${p.name || p.type}": host_part "${p.host_part}" ${later
      ? 'is listed AFTER this part — a part can only be seated on one that already exists; move it up the list'
      : 'names no part in this spec'}`);
  }
  const { mesh: hm, spec: hs } = hp;
  const hostJoint = p.host || hs.host;
  if (!hostJoint || !spec.joints[hostJoint])
    throw new Error(`part "${p.name || p.type}": host_part "${p.host_part}" has no host joint to fall back on — give this part a "host"`);
  let seat, tangent = null;
  if (hm._path && hm._path.length >= 2) {
    const path = hm._path, arc = [0];
    for (let i = 1; i < path.length; i++) arc.push(arc[i - 1] + G.len(G.sub(path[i], path[i - 1])));
    const L = arc[arc.length - 1] || 1;
    const at = Math.min(1, Math.max(0, p.at ?? 1)) * L;
    let i = 0; while (i < arc.length - 2 && at > arc[i + 1]) i++;
    const f = (at - arc[i]) / (arc[i + 1] - arc[i] || 1);
    seat = G.add(G.mul(path[i], 1 - f), G.mul(path[i + 1], f));
    tangent = G.nrm(G.sub(path[i + 1], path[i]));
  } else {
    if (p.at !== undefined)
      INFO.push(`WARN part '${p.name}': host_part "${p.host_part}" is a ${hs.type} with no centreline, so "at" does nothing — the seat is the host's joint + "offset"`);
    if (!p.dir) throw new Error(`part "${p.name || p.type}": host_part "${p.host_part}" is a ${hs.type} with no centreline to take a direction from — give this part a "dir"`);
    seat = G.add(spec.joints[hs.host], hs.offset || [0, 0, 0]);
  }
  const origin = G.add(seat, p.offset || [0, 0, 0]);
  const p2 = { ...p, host: hostJoint, offset: G.sub(origin, spec.joints[hostJoint]), dir: p.dir || tangent };
  INFO.push(`part '${p.name}': seated on part "${p.host_part}"${tangent ? ` at ${(p.at ?? 1).toFixed(2)} of its length` : ''}`
    + ` [${origin.map(x => x.toFixed(3)).join(', ')}]${p.dir ? '' : tangent ? `, pointing along it (${dirName(tangent)})` : ''}`
    + `; skin inherited from it`);
  return { p2, hostMesh: hm };
}

// every vertex takes the skin of the host's nearest vertex
function inheritSkin(m, host) {
  if (!host.skin || !host.V.length) return;
  m.skin = m.V.map(v => {
    let best = Infinity, bi = 0;
    for (let i = 0; i < host.V.length; i++) {
      const q = host.V[i];
      const d = (v[0] - q[0]) ** 2 + (v[1] - q[1]) ** 2 + (v[2] - q[2]) ** 2;
      if (d < best) { best = d; bi = i; }
    }
    return host.skin[bi].map(x => x.slice());
  });
}

function buildMembrane(spec, p) {
  // Membrane stretched between rib joint-chains — wings, frills, sails, webbed feet.
  // What the viewer reads is the enclosed silhouette, not the ribs inside it, so
  // ribs are listed leading edge → trailing edge and the last one has to come back
  // to the body. A last rib left out at the far end leaves the shape unenclosed:
  // it reads as spread fingers rather than one sheet. The compiler measures the
  // root gap and says so.
  const ribs = p.ribs.map(r => {
    const names = r.chain ? spec.chains[r.chain] : r.joints;
    if (!names) throw new Error(`membrane rib references unknown chain "${r.chain}"`);
    return names.map(n => {
      const q = spec.joints[n];
      if (!q) throw new Error(`membrane rib joint "${n}" missing`);
      return { n, p: q };
    });
  });
  const S = p.along || 8, U = p.across || 3;
  const sampled = ribs.map((rib, ri) => {
    const pl = rib.map(x => x.p);
    const arc = [0];
    for (let i = 1; i < pl.length; i++) arc.push(arc[i - 1] + G.len(G.sub(pl[i], pl[i - 1])));
    const L = arc[arc.length - 1] || 1;
    const t1 = 1 - (p.ribs[ri].shorten || 0);
    const out = [];
    for (let sI = 0; sI <= S; sI++) {
      const tt = (t1 * sI / S) * L;
      let i = 0; while (i < arc.length - 2 && tt > arc[i + 1]) i++;
      const f = (tt - arc[i]) / (arc[i + 1] - arc[i] || 1);
      out.push({
        p: G.add(G.mul(pl[i], 1 - f), G.mul(pl[i + 1], f)),
        skin: f < 0.01 ? [[rib[i].n, 1]] : f > 0.99 ? [[rib[i + 1].n, 1]]
          : [[rib[i].n, 1 - f], [rib[i + 1].n, f]],
      });
    }
    return out;
  });
  const C = (ribs.length - 1) * U + 1;   // grid columns
  const V = [], skin = [], F = [];
  const colPt = (j, sI) => {
    const r = Math.min(ribs.length - 2, Math.floor(j / U));
    const u = (j - r * U) / U;
    const a = sampled[r][sI], b = sampled[r + 1][sI];
    let pnt = G.add(G.mul(a.p, 1 - u), G.mul(b.p, u));
    if (sI === S && u > 0 && u < 1 && (p.trailing || 'cusp') === 'cusp') {
      const rootMid = G.mul(G.add(sampled[r][0].p, sampled[r + 1][0].p), 0.5);
      const tipMid = G.mul(G.add(sampled[r][S].p, sampled[r + 1][S].p), 0.5);
      const outDir = G.nrm(G.sub(tipMid, rootMid));
      const span = G.len(G.sub(sampled[r + 1][S].p, sampled[r][S].p));
      pnt = G.sub(pnt, G.mul(outDir, (p.cusp ?? 0.25) * span * Math.sin(Math.PI * u)));
    }
    const w = [];
    for (const [jn, ww] of a.skin) w.push([jn, ww * (1 - u)]);
    for (const [jn, ww] of b.skin) w.push([jn, ww * u]);
    return { pnt, w: w.filter(x => x[1] > 0.001) };
  };
  for (let j = 0; j < C; j++) for (let sI = 0; sI <= S; sI++) {
    const { pnt, w } = colPt(j, sI);
    V.push(pnt); skin.push(w);
  }
  const idx = (j, sI) => j * (S + 1) + sI;
  for (let j = 0; j < C - 1; j++) for (let sI = 0; sI < S; sI++)
    F.push([idx(j, sI), idx(j + 1, sI), idx(j + 1, sI + 1), idx(j, sI + 1)]);
  if (ribs.length >= 3) {
    const gap = G.len(G.sub(sampled[0][0].p, sampled[sampled.length - 1][0].p));
    let reach = 0;
    for (const col of sampled) for (const q of col) reach = Math.max(reach, G.len(G.sub(q.p, sampled[0][0].p)));
    if (gap > 0.35 * reach)
      INFO.push(`WARN membrane '${p.name || 'membrane'}': root gap ${gap.toFixed(2)} between the leading and trailing ribs, ${Math.round(100 * gap / reach)}% of this membrane's own reach. Nothing brings the trailing rib home, so the silhouette stays unenclosed and reads as spread fingers instead of one sheet — end the rib list back at the body.`);
  }
  const Cc = p.colors ? membraneColours(spec, p, V, C, S, U, ribs.length) : undefined;
  return { material: p.material, V, F, skin, doubleSided: true, faceted: p.faceted, C: Cc };
}

// ── membrane colours: bands in the sheet's own (u, t) frame ────────────────
// A membrane used to ship one flat colour: `colors.arcs` is a band AROUND a
// ring-built mesh and a sheet has no rings. What a wing wants is written in
// the sheet's own two coordinates instead — u ACROSS the sheet, 0 at the
// leading rib and 1 at the trailing rib; t ALONG it, 0 at the root and 1 at
// the tip — and the compiler prints which rib is which so nobody guesses.
//
//   "colors": {
//     "arcs":  [ {"u":[0,0.2], "t":[0,1], "color":"#...", "feather_u":0.2, "feather_t":0} ],
//     "veins": {"color":"#...", "width":0.35} }
//
// arcs   bands, later over earlier, on the material colour: a darker leading
//        edge is u [0, 0.2]; a pale root fading to the tip is t [0, 0.5] with
//        feather_t 0.5; the whole sheet warmer at the tip is t [0.5, 1].
// veins  a darkening centred on each rib column, `width` wide as a fraction of
//        the rib-to-rib spacing (default 0.35), smoothstepped to 0 — the ribs
//        show through the skin the way a bat's fingers do.
//
// Resolved by the vertices, like every arc: `across` columns sit between two
// ribs, so a feather_u narrower than 1 / ((ribs - 1) x across) and a vein
// narrower than 1 / across land between two vertices and ship a hard edge;
// the compiler says so with the numbers.
function membraneColours(spec, p, V, C, S, U, nRibs) {
  const label = `membrane "${p.name || 'membrane'}"`;
  const cs = p.colors || {};
  const base = hex2lin((spec.palette[p.material] || {}).color || '#888888');
  const uStep = 1 / Math.max(1, C - 1), tStep = 1 / Math.max(1, S);
  const arcs = (cs.arcs || []).map(a => {
    for (const k of ['u', 't']) if (a[k] !== undefined && !(Array.isArray(a[k]) && a[k].length === 2))
      throw new Error(`${label}: an arc's "${k}" is [${k}0, ${k}1] across (u) or along (t) the sheet, got ${JSON.stringify(a[k])}`);
    if (a.from !== undefined || a.to !== undefined)
      throw new Error(`${label}: a membrane arc is written in "u" (across: 0 leading rib, 1 trailing rib) and "t" (along: 0 root, 1 tip), not in degrees — there is no ring to go around`);
    if (!a.color) throw new Error(`${label}: an arc needs a "color"`);
    return { u0: a.u ? a.u[0] : 0, u1: a.u ? a.u[1] : 1, t0: a.t ? a.t[0] : 0, t1: a.t ? a.t[1] : 1,
             fu: Math.max(0, a.feather_u || 0), ft: Math.max(0, a.feather_t || 0), c: hex2lin(a.color) };
  });
  for (const a of arcs) {
    if ((a.u0 > 0 || a.u1 < 1) && a.fu > 0 && a.fu < uStep)
      INFO.push(`WARN ${label}: arc u ${a.u0}..${a.u1} has "feather_u": ${a.fu} but the columns are ${uStep.toFixed(3)} apart in u `
        + `(${nRibs} ribs x "across" ${U}) — a feather narrower than the column step lands between two vertices and does nothing. `
        + `Write it at 2-3x the step (${(uStep * 2).toFixed(2)}-${(uStep * 3).toFixed(2)}), or raise "across".`);
    if ((a.t0 > 0 || a.t1 < 1) && a.ft > 0 && a.ft < tStep)
      INFO.push(`WARN ${label}: arc t ${a.t0}..${a.t1} has "feather_t": ${a.ft} but the rows are ${tStep.toFixed(3)} apart in t `
        + `("along" ${S}) — a feather narrower than the row step lands between two vertices and does nothing. `
        + `Write it at 2-3x the step (${(tStep * 2).toFixed(2)}-${(tStep * 3).toFixed(2)}), or raise "along".`);
  }
  let veins = null;
  if (cs.veins) {
    if (!cs.veins.color) throw new Error(`${label}: "veins" needs a "color"`);
    veins = { c: hex2lin(cs.veins.color), w: Math.max(0.01, Math.min(0.5, cs.veins.width ?? 0.35)) };
    if (veins.w < 1 / U)
      INFO.push(`WARN ${label}: "veins" width ${veins.w} is under one column (1/${U} = ${(1 / U).toFixed(2)} of the rib spacing) — `
        + `only the rib column itself takes the colour and it ships as a hard stripe. Write it at 2-3 columns `
        + `(${(2 / U).toFixed(2)}-${(3 / U).toFixed(2)}), or raise "across".`);
  }
  const edgeW = (x, lo, hi, f, openLo, openHi) => {
    if (x < lo - 1e-9 || x > hi + 1e-9) return 0;
    if (!(f > 0)) return 1;
    let u = 1;
    if (!openLo) u = Math.min(u, (x - lo) / f);
    if (!openHi) u = Math.min(u, (hi - x) / f);
    u = Math.max(0, Math.min(1, u));
    return u * u * (3 - 2 * u);
  };
  const out = V.map(() => base.slice());
  for (let j = 0; j < C; j++) {
    const u = j * uStep;
    const dj = Math.abs(j / U - Math.round(j / U));          // distance to the nearest rib, in rib spacings
    for (let sI = 0; sI <= S; sI++) {
      const t = sI * tStep;
      let c = base;
      for (const a of arcs) {
        const w = edgeW(u, a.u0, a.u1, a.fu, a.u0 <= 0, a.u1 >= 1) * edgeW(t, a.t0, a.t1, a.ft, a.t0 <= 0, a.t1 >= 1);
        if (w > 0) c = [c[0] + (a.c[0] - c[0]) * w, c[1] + (a.c[1] - c[1]) * w, c[2] + (a.c[2] - c[2]) * w];
      }
      if (veins) {
        const x = Math.min(1, dj / veins.w), w = 1 - x * x * (3 - 2 * x);
        if (w > 0) c = [c[0] + (veins.c[0] - c[0]) * w, c[1] + (veins.c[1] - c[1]) * w, c[2] + (veins.c[2] - c[2]) * w];
      }
      out[j * (S + 1) + sI] = c.slice();
    }
  }
  const ribName = i => p.ribs[i].chain || (p.ribs[i].joints || []).join('>');
  INFO.push(`${label}: colours — u 0 is the leading rib (${ribName(0)}), u 1 the trailing rib (${ribName(nRibs - 1)}); `
    + `t 0 is the root, 1 the tip; ${arcs.length} arc(s)${veins ? `, veins ${(veins.w * 100).toFixed(0)}% of the rib spacing` : ''}`);
  return out;
}


function buildHand(spec, p) {
  // A REAL hand: palm slab + four fingers + an OPPOSABLE thumb — the anatomy
  // the field kept failing to improvise from spheres and sticks. Everything
  // scales from `size` (palm length, wrist to knuckles). Build the LEFT hand;
  // `mirrored: true` makes the right one (the thumb lands correctly by the
  // mirror). All verts ride the host joint; `curl` 0..1 relaxes/folds the
  // fingers, `fist: true` is a full fold with the thumb wrapped across.
  //
  // ONE frame rules everything. The palm slab is hand-rolled IN THE HAND'S
  // LOCAL FRAME (fingers +z, width x, thickness y) and only then mapped to
  // world — an auto-framed tube would pick its own ring orientation and the
  // thumb, placed in the hand frame, would miss the palm it belongs to.
  const host = spec.joints[p.host];
  if (!host) throw new Error(`hand host joint "${p.host}" missing`);
  const S = p.size ?? 0.16;                       // palm length
  const fist = !!p.fist;
  const curl = fist ? 1.0 : (p.curl ?? 0.35);
  const spread = p.spread ?? 0.5;
  const F = G.nrm(p.dir || [0, -0.35, 1]);        // knuckle direction
  let U = p.up || [0, 1, 0];
  U = G.nrm(G.sub(U, G.mul(F, G.dot(U, F))));
  const Sx = G.cross(U, F);
  const o = G.add(host, p.offset || [0, 0, 0]);
  const toW = (q) => [o[0] + Sx[0]*q[0] + U[0]*q[1] + F[0]*q[2],
                      o[1] + Sx[1]*q[0] + U[1]*q[1] + F[1]*q[2],
                      o[2] + Sx[2]*q[0] + U[2]*q[1] + F[2]*q[2]];
  const V = [], Fq = [];

  // ── palm: boxy elliptical slab, rings authored in the LOCAL frame ──
  const halfW = S * 0.44, thick = S * 0.17, PS = 10;
  {
    // stations: [z, widthScale, thickScale, yDrop]
    const st = [[-0.22, 0.86, 0.88, 0], [0.10, 1.0, 1.0, 0], [0.45, 1.04, 0.98, -0.01],
                [0.75, 1.0, 0.92, -0.03], [0.98, 0.92, 0.82, -0.05]];
    const ring0 = V.length;
    for (const [z, ws, ts, yd] of st) {
      for (let k = 0; k < PS; k++) {
        const a = (k / PS) * Math.PI * 2;
        const cs = Math.cos(a), sn = Math.sin(a);
        const bx = Math.sign(cs) * Math.pow(Math.abs(cs), 0.55);  // superellipse: boxy
        const by = Math.sign(sn) * Math.pow(Math.abs(sn), 0.55);
        V.push(toW([bx * halfW * ws, by * thick * ts + yd * S, z * S]));
      }
    }
    for (let r = 0; r < st.length - 1; r++)
      for (let k = 0; k < PS; k++)
        Fq.push([ring0 + r*PS + k, ring0 + r*PS + (k+1)%PS,
                 ring0 + (r+1)*PS + (k+1)%PS, ring0 + (r+1)*PS + k]);
    const c0 = V.length; V.push(toW([0, 0, -0.22 * S]));
    for (let k = 0; k < PS; k++) Fq.push([ring0 + (k+1)%PS, ring0 + k, c0]);
    const c1 = V.length; V.push(toW([0, -0.05 * S, 0.98 * S]));
    const last = ring0 + (st.length - 1) * PS;
    for (let k = 0; k < PS; k++) Fq.push([last + k, last + (k+1)%PS, c1]);
  }

  // local circular tube (fingers/thumb) — rings framed in the LOCAL space too
  const tube = (pts, radii, sides) => {
    const base = V.length;
    for (let i = 0; i < pts.length; i++) {
      const q = pts[i];
      const tn = i === 0 ? G.nrm(G.sub(pts[1], pts[0]))
        : i === pts.length - 1 ? G.nrm(G.sub(pts[i], pts[i-1]))
        : G.nrm(G.add(G.nrm(G.sub(pts[i], pts[i-1])), G.nrm(G.sub(pts[i+1], pts[i]))));
      let ax = Math.abs(tn[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
      let u1 = G.nrm(G.cross(tn, ax));
      const u2 = G.cross(tn, u1);
      for (let k = 0; k < sides; k++) {
        const a = (k / sides) * Math.PI * 2;
        const r = radii[i];
        V.push(toW([q[0] + (u1[0]*Math.cos(a) + u2[0]*Math.sin(a)) * r,
                    q[1] + (u1[1]*Math.cos(a) + u2[1]*Math.sin(a)) * r,
                    q[2] + (u1[2]*Math.cos(a) + u2[2]*Math.sin(a)) * r]));
      }
    }
    for (let i = 0; i < pts.length - 1; i++)
      for (let k = 0; k < sides; k++)
        Fq.push([base + i*sides + k, base + i*sides + (k+1)%sides,
                 base + (i+1)*sides + (k+1)%sides, base + (i+1)*sides + k]);
    const cb = V.length; V.push(toW(pts[0]));
    for (let k = 0; k < sides; k++) Fq.push([base + (k+1)%sides, base + k, cb]);
    const ct = V.length; V.push(toW(pts[pts.length - 1]));
    const lastR = base + (pts.length - 1) * sides;
    for (let k = 0; k < sides; k++) Fq.push([lastR + k, lastR + (k+1)%sides, ct]);
  };

  // ── four fingers off the knuckle edge (roots sunk INTO the palm) ──
  const lens = [0.78, 0.94, 1.0, 0.90];            // pinky → index
  const nf = p.fingers ?? 4;
  for (let i = 0; i < nf; i++) {
    const t = nf === 1 ? 0 : (i / (nf - 1)) * 2 - 1;
    const x0 = -t * halfW * 0.72;                  // pinky at -x … index at +x (left hand)
    const L = S * 0.80 * lens[Math.min(i, 3)];
    const r = Math.min(S * 0.088, halfW * 0.72 / Math.max(nf - 1, 1) * 0.95);
    const fan = t * spread * 0.20;
    const segA = [0.42, 0.33, 0.25];
    const pts = [[x0, -S*0.02, S*0.80]];           // root buried in the palm
    let ang = curl * 0.5;
    for (const sa of segA) {
      const q = pts[pts.length - 1];
      const d = G.nrm([fan, -Math.sin(ang) - 0.10, Math.cos(ang)]);
      pts.push([q[0] + d[0]*L*sa, q[1] + d[1]*L*sa, q[2] + d[2]*L*sa]);
      ang += curl * 0.85;
    }
    tube(pts, [r, r*0.92, r*0.78, r*0.5], 7);
  }

  // ── the thumb: root INSIDE the index-side palm edge, opposed, lower ──
  if (p.thumb !== false) {
    const L = S * 0.66, r = S * 0.105;
    const root = [halfW * 0.62, -thick * 0.35, S * 0.30];     // sunk into the slab
    const d1 = G.nrm(fist ? [0.55, -0.42, 0.72] : [0.66, -0.48, 0.58]);
    const mid = [root[0] + d1[0]*L*0.55, root[1] + d1[1]*L*0.55, root[2] + d1[2]*L*0.55];
    const d2 = G.nrm(fist ? [-0.80, -0.30, 0.52] : [0.28, -0.22, 0.93]);  // fist: folds across
    const tip = [mid[0] + d2[0]*L*0.5, mid[1] + d2[1]*L*0.5, mid[2] + d2[2]*L*0.5];
    tube([root, mid, tip], [r, r*0.88, r*0.58], 7);
  }

  return { material: p.material, V, F: Fq, join: p.join,
    _seatIdx: Array.from({ length: PS }, (_, i) => i),        // palm base ring = the wrist socket
    skin: V.map(() => [[p.host, 1]]) };
}

// A rounded, flat-soled half-superellipsoid: the building block of a paw. The
// plan is a superellipse (exponent `e`, 2 = ellipse, higher = boxier), the
// height profile is fuller at the sides than a sphere, and the sole is a fan.
// Everything is written in a local frame (x width, y up, z forward) and mapped
// through `toW`, so the same block makes the pad and each toe.
function padBlock(V, F, toW, c, L, W, H, e, N1, N2) {
  const base = V.length;
  for (let j = 0; j < N2; j++) {                          // rings; the top is one vertex
    const phi = (j / N2) * Math.PI / 2;
    const plan = Math.pow(Math.cos(phi), 0.65);           // fuller than a sphere
    const y = H * Math.pow(Math.sin(phi), 0.8);
    for (let k = 0; k < N1; k++) {
      const th = 2 * Math.PI * k / N1;
      const cs = Math.cos(th), sn = Math.sin(th);
      const x = Math.sign(cs) * Math.pow(Math.abs(cs), 2 / e) * W / 2 * plan;
      const z = Math.sign(sn) * Math.pow(Math.abs(sn), 2 / e) * L / 2 * plan;
      V.push(toW([c[0] + x, c[1] + y, c[2] + z]));
    }
  }
  for (let j = 0; j < N2 - 1; j++) for (let k = 0; k < N1; k++)
    F.push([base + j * N1 + k, base + (j + 1) * N1 + k,
            base + (j + 1) * N1 + (k + 1) % N1, base + j * N1 + (k + 1) % N1]);
  const top = V.length; V.push(toW([c[0], c[1] + H, c[2]]));
  const last = base + (N2 - 1) * N1;
  for (let k = 0; k < N1; k++) F.push([last + (k + 1) % N1, last + k, top]);
  const ci = V.length; V.push(toW([c[0], c[1], c[2]]));
  for (let k = 0; k < N1; k++) F.push([base + k, base + (k + 1) % N1, ci]);
}

function buildPaw(spec, p) {
  // A paw with anatomy: a rounded-box pad with a FLAT sole, and toes that make
  // the front edge (default 4 — "toes": 0 for a plain pad, 2..5 otherwise), each
  // a smaller rounded block half-buried in the pad so the joins vanish under AO.
  // Optional claws ("claws": true, "claw_material": a palette key, default the
  // paw's own) are a second mesh — dark claws on a light foot are what make a
  // foot read as a foot at thumbnail size. size = [length(fwd), width, height].
  // "dir" (default +z) turns the whole paw in the ground plane.
  const host = spec.joints[p.host];
  if (!host) throw new Error(`paw host joint "${p.host}" missing`);
  const [L, W2, H] = p.size || [0.14, 0.10, 0.07];
  const c0 = G.add(host, p.offset || [0, H * 0.45 - host[1], L * 0.18]); // sole on ground
  // local frame: fingers +z (or `dir` flattened to the ground), width x, up y
  let Fz = p.dir ? [p.dir[0], 0, p.dir[2]] : [0, 0, 1];
  if (G.len(Fz) < 1e-6) Fz = [0, 0, 1];
  Fz = G.nrm(Fz);
  const Sx = G.cross([0, 1, 0], Fz);
  const toW = q => [c0[0] + Sx[0] * q[0] + Fz[0] * q[2], c0[1] + q[1], c0[2] + Sx[2] * q[0] + Fz[2] * q[2]];
  const V = []; const F = [];
  const N1 = p.sides || 12, N2 = 4;
  const nt = p.toes === undefined ? 4 : (p.toes | 0);
  const e = p.exp ?? 2.6;
  if (nt >= 2) {
    // pad sits back, toes complete the front: the pad ends where the toes begin
    const padL = L * 0.72;
    padBlock(V, F, toW, [0, 0, -L * 0.5 + padL * 0.5], padL, W2, H, e, N1, N2);
    const tw = W2 / nt * 1.08, tl = L * 0.46, th = H * 0.82;
    for (let k = 0; k < nt; k++) {
      const u = nt === 1 ? 0 : (k / (nt - 1)) * 2 - 1;
      const tx = u * (W2 / 2 - tw * 0.5);
      // outer toes sit a little further back, the way a paw print is drawn
      const tz = L * 0.5 - tl * 0.5 - Math.abs(u) * L * 0.06;
      padBlock(V, F, toW, [tx, 0, tz], tl, tw, th * (1 - 0.08 * Math.abs(u)), e, 8, 3);
    }
  } else {
    padBlock(V, F, toW, [0, 0, 0], L, W2, H, e, N1, N2);
  }
  const paw = { material: p.material, V, F, skin: V.map(() => [[p.host, 1]]) };
  if (!p.claws || nt < 2) return paw;
  // claws: short tapered cones off each toe tip, angled down to the ground
  const CV = [], CF = [];
  const tw = W2 / nt * 1.08, tl = L * 0.46, th = H * 0.82;
  const cr = Math.min(tw, th) * 0.22, cl = L * 0.16;
  for (let k = 0; k < nt; k++) {
    const u = nt === 1 ? 0 : (k / (nt - 1)) * 2 - 1;
    const tx = u * (W2 / 2 - tw * 0.5);
    const tz = L * 0.5 - Math.abs(u) * L * 0.06;
    const root = toW([tx, th * 0.42, tz - tl * 0.25]);          // buried in the toe
    const tip = toW([tx + u * cl * 0.15, th * 0.08, tz + cl]);
    const wp = [root, tip];
    const rings = G.chainRings(wp, [cr, cr * 0.25], 6, false);
    const part = G.partFromRings(rings, 6, 'ngon', 'fan', wp);
    const b0 = CV.length;
    CV.push(...part.v);
    for (const f of part.fq) CF.push(f.map(i => i + b0));
  }
  const claws = { material: p.claw_material || p.material, V: CV, F: CF, sub: 'claws',
    join: 'place', shade: 'hard', skin: CV.map(() => [[p.host, 1]]) };
  return [paw, claws];
}

// ── tufts: fur that leaves the silhouette ──────────────────────────────────
// A ruff, a mane, a bushy tail, a cheek beard, a fetlock: the wolf signature is
// a neck ruff, and a lofted tube cannot make one — a fatter ring is still a
// ring. A "tufts" part seats a crown of short tapered wedges on a volume's
// surface, each rooted under the skin and pointing out, swept along the chain
// and drooped toward the ground, with a deterministic length jitter so the
// edge reads as fur and not as a gear. It is FLESH to the shading stack (it
// takes the seam blend and the body light), so it belongs to the mass it
// grows from rather than sitting on it like a plate.
//
//   anchor:  {chain, t, around}  around is [from, to] in degrees (the section's
//            frame: 0 spine, 90 side, 180 belly) or one angle for a single column
//   rows     rings of tufts (default 1), spread over "span" along t (default 0)
//   count    tufts per row across the around range (default 6)
//   length / width / thick   the wedge (defaults 0.1 / 0.04 / 0.025)
//   sweep    along the chain: +1 toward the chain's end, -1 back toward its start
//   droop    toward world down (default 0.3);  flare  along the surface normal (1)
//   jitter   ±fraction of length, alternating per tuft (default 0.3)
//   sides    ring sides (default 4: a diamond wedge; 6 for a rounder tuft)
//   bulge    the clump's full width as a multiple of `width`, a third of the
//            way out (default 1.0; 0.6 makes a blade, 1.3 a pom)
//   root_color / tip_color   the colour ramp along each tuft (see below)
//
// A tuft is a CLUMP, not a blade. The first version was a two-ring wedge that
// tapered straight from the root to a point, and a crown of those read as
// paper spikes: every silhouette edge was a straight line and every tuft was
// the same flat colour as its neighbour. Now each tuft has a root ring under
// the skin, a full ring a third of the way out (the clump's belly), a shoulder
// ring at three quarters and a tip, so the outline is a lobe that pinches to a
// point, and it carries its own colour ramp: the root takes the colour of the
// skin it grows from (so it never stands off the body), and the tip takes the
// part's material — cream tips over a grey neck is what a ruff looks like.
// `root_color` / `tip_color` override either end.
function buildTufts(spec, p, builtVols) {
  if (p.host && !spec.joints[p.host]) throw new Error(`tufts host joint "${p.host}" missing`);
  const an = p.anchor;
  if (!an || !an.chain) throw new Error(`tufts "${p.name || p.host}" need an "anchor": {chain, t, around}`);
  const bv = builtVols[an.chain];
  if (!bv) throw new Error(`tufts "${p.name || p.host}": anchor chain "${an.chain}" has no built volume`);
  const rangeA = Array.isArray(an.around) ? an.around : [an.around ?? 90, an.around ?? 90];
  const rows = Math.max(1, (p.rows ?? 1) | 0), count = Math.max(1, (p.count ?? 6) | 0);
  const span = p.span ?? 0, sides = Math.max(3, (p.sides ?? 4) | 0);
  const L0 = p.length ?? 0.1, W = p.width ?? 0.04, TH = p.thick ?? 0.025;
  const sweep = p.sweep ?? 0, droop = p.droop ?? 0.3, flare = p.flare ?? 1, jit = p.jitter ?? 0.3;
  const bulge = Math.max(0.2, p.bulge ?? 1.0);
  const tipC = hex2lin(p.tip_color || (spec.palette[p.material] || {}).color || '#888888');
  const rootOverride = p.root_color ? hex2lin(p.root_color) : null;
  const V = [], F = [], skin = [], C = [];
  // local chain tangent at t, from the ring table (bevel-skip drops rings, so
  // look the bracketing rings up by their true t, as surfacePoint does)
  const ringAt = t => {
    const rt = bv._ringT, n = rt.length;
    let s1 = 0; while (s1 < n - 1 && rt[s1] < t) s1++;
    return [Math.max(0, s1 - 1), s1];
  };
  const tangentAt = t => {
    const [s0, s1] = ringAt(t);
    const d = G.sub(bv._pts[Math.min(bv._pts.length - 1, s1 + (s1 === s0 ? 1 : 0))], bv._pts[s0]);
    return G.len(d) > 1e-9 ? G.nrm(d) : [0, 0, 1];
  };
  // A tuft rides the SKIN it grows from: it takes the weights of the nearest
  // vertex of the host ring, so a ruff across two neck joints bends with the
  // neck instead of hanging off whichever single joint was named. "host" is
  // then only the fallback for a chain with no skin (it never is), and may be
  // left out.
  const hostVertex = (t, aroundDeg) => {
    const [s0, s1] = ringAt(t);
    const s = Math.abs(bv._ringT[s0] - t) < Math.abs(bv._ringT[s1] - t) ? s0 : s1;
    const N = bv._sides, fromTop = ((aroundDeg % 360) + 360) % 360;
    const k = Math.round(((450 - fromTop) % 360) / 360 * N) % N;
    return bv._ringIdx[s][k];
  };
  const skinAt = (t, aroundDeg) => {
    const w = bv.skin && bv.skin[hostVertex(t, aroundDeg)];
    return w ? w.map(x => x.slice()) : [[p.host, 1]];
  };
  // the colour of the skin under the tuft: the host's arc colour at that vertex
  const rootAt = (t, aroundDeg) => rootOverride
    || (bv.C && bv.C[hostVertex(t, aroundDeg)]) || tipC;
  let made = 0;
  for (let r = 0; r < rows; r++) {
    const t = Math.min(1, Math.max(0, (an.t ?? 0.5) + (rows > 1 ? (r / (rows - 1) - 0.5) * span : 0)));
    const tan = tangentAt(t);
    for (let i = 0; i < count; i++) {
      const a = count === 1 ? (rangeA[0] + rangeA[1]) / 2
        : rangeA[0] + (rangeA[1] - rangeA[0]) * (i + 0.5 + (r % 2) * 0.25) / count;
      const sp = surfacePoint(builtVols, { chain: an.chain, t, around: a });
      let d = G.add(G.add(G.mul(sp.out, flare), G.mul(tan, sweep)), [0, -droop, 0]);
      if (G.len(d) < 1e-6) d = sp.out.slice();
      d = G.nrm(d);
      // width runs around the ring (perpendicular to the normal and the chain)
      let u1 = G.cross(sp.out, tan);
      if (G.len(u1) < 1e-6) u1 = G.cross(sp.out, [0, 1, 0]);
      u1 = G.nrm(G.sub(u1, G.mul(d, G.dot(u1, d))));
      const u2 = G.nrm(G.cross(d, u1));
      const L = L0 * (1 + jit * ((i + r) % 2 ? 0.5 : -0.5) * 2 * (0.6 + 0.4 * hash3(i, r, made)));
      const base = G.sub(sp.p, G.mul(sp.out, TH * 0.9));            // rooted under the skin
      const tip = G.add(G.add(base, G.mul(d, L)), [0, -droop * L * 0.15, 0]);
      const rootC = rootAt(t, a);
      const cAt = f => [rootC[0] + (tipC[0] - rootC[0]) * f, rootC[1] + (tipC[1] - rootC[1]) * f,
                        rootC[2] + (tipC[2] - rootC[2]) * f];
      // stations along the tuft: [fraction of L, half-width, half-thickness, colour mix]
      const stations = [
        [0.00, W * 0.32, TH * 0.36, 0.00],                 // root, under the skin
        [0.34, W * 0.5 * bulge, TH * 0.5 * bulge, 0.45],   // the clump's belly
        [0.74, W * 0.27, TH * 0.24, 0.85],                 // shoulder
      ];
      const b0 = V.length;
      for (const [f, rw, rh, cf] of stations) {
        const c = G.add(base, G.mul(d, L * f));
        const col = cAt(cf);
        for (let k = 0; k < sides; k++) {
          const th = 2 * Math.PI * k / sides;
          V.push(G.add(c, G.add(G.mul(u1, Math.cos(th) * rw), G.mul(u2, Math.sin(th) * rh))));
          C.push(col.slice());
        }
      }
      const ti = V.length; V.push(tip); C.push(cAt(1));
      const w = skinAt(t, a);
      while (skin.length < V.length) skin.push(w.map(x => x.slice()));
      const nS = stations.length;
      for (let s = 0; s < nS - 1; s++)
        for (let k = 0; k < sides; k++) {
          const k1 = (k + 1) % sides, r0 = b0 + s * sides, r1 = r0 + sides;
          F.push([r0 + k, r0 + k1, r1 + k1, r1 + k]);
        }
      const last = b0 + (nS - 1) * sides;
      for (let k = 0; k < sides; k++) F.push([last + k, last + (k + 1) % sides, ti]);
      for (let k = 1; k < sides - 1; k++) F.push([b0, b0 + k + 1, b0 + k]);   // base, buried
      made++;
    }
  }
  INFO.push(`tufts '${p.name || p.host}': ${made} tufts on "${an.chain}" at t=${(an.t ?? 0.5).toFixed(2)}`
    + `${rows > 1 ? ` ±${(span / 2).toFixed(2)}` : ''}, around ${rangeA[0]}..${rangeA[1]}°`);
  return { material: p.material, V, F, C, join: p.join || 'insert', shade: p.shade || 'flesh', skin };
}

const { mirrorName } = require('./skeleton.js');
function buildFin(spec, p, builtVols) {
  // Flat plate with thickness: outline points [[u,v],...] in a plane at host,
  // plane axes given by udir/vdir (world), extruded ±thickness/2 along normal.
  const host = spec.joints[p.host];
  if (!host) throw new Error(`fin host joint "${p.host}" missing`);
  // TWO NEARLY-COINCIDENT OUTLINE POINTS make a degenerate sliver, which extrudes
  // into flipped triangles. The build then fails on mesh_integrity, which counts
  // flipped tris across the WHOLE model and cannot say which part made them — so
  // the author bisects by hand for a round. It is visible right here, before a
  // single triangle exists, so it is said right here.
  if (Array.isArray(p.points) && p.points.length > 2) {
    const span = Math.max(...p.points.map(a =>
      Math.max(...p.points.map(b => Math.hypot(a[0] - b[0], a[1] - b[1])))));
    for (let i = 0; i < p.points.length; i++) {
      const j = (i + 1) % p.points.length;
      const d = Math.hypot(p.points[i][0] - p.points[j][0], p.points[i][1] - p.points[j][1]);
      if (span > 0 && d < span * 0.02)
        throw new Error(`fin "${p.name || p.host}": outline points ${i} and ${j} are `
          + `${d.toFixed(4)} apart, under 2% of the shape's own size (${span.toFixed(3)}). Two points `
          + `that close make a sliver, and extruding a sliver makes flipped triangles that show up `
          + `later as a mesh_integrity count with no address. Merge them, or move one; 5-6 `
          + `well-separated points is the shape this builder wants.`);
    }
  }
  let U = G.nrm(p.udir || [0, 0, 1]), Vv = G.nrm(p.vdir || [0, 1, 0]);
  let Nn = G.nrm(G.cross(U, Vv));
  let o = G.add(host, p.offset || [0, 0, 0]);
  if (p.anchor) {
    const sp = surfacePoint(builtVols, p.anchor);
    o = sp.p;
    // `around` is expressed in the host section's own frame. On a body chain that
    // frame gives the documented 0=spine / 90=side / 180=belly. On a chain that
    // runs vertically (a leg) the same numbers point somewhere else entirely —
    // 90 comes out FRONT, 180 comes out OUTER — so a plate aimed at the outside
    // of a thigh silently lands on its front. Say where it actually went.
    INFO.push(`fin '${p.name || p.host}' anchored on "${p.anchor.chain}" at around=${p.anchor.around ?? 0}`
      + ` faces ${dirName(sp.out)} (world normal ${sp.out.map(x => x.toFixed(2)).join(',')})`
      + ` — "around" is read in the host section's frame, NOT in world space; verify this is the side you meant`);
    if (p.conform !== false) {
      // Default behaviour: the host surface wins. The plate's normal is snapped
      // onto the surface normal at the landing point, and whatever direction the
      // spec asked for is kept only as a measured difference. Opt out per part.
      const dev = Math.acos(Math.max(-1, Math.min(1, G.dot(Nn, sp.out)))) * 180 / Math.PI;
      const U2 = G.sub(U, G.mul(sp.out, G.dot(U, sp.out)));
      if (G.len(U2) > 1e-4) {
        Nn = sp.out.slice();
        U = G.nrm(U2);
        Vv = G.nrm(G.cross(Nn, U));
        if (dev > 25) INFO.push(`fin '${p.name || p.host}': the host surface rotated this plate ${dev.toFixed(0)}° off the direction the spec asked for. If that written direction was the point, set "conform": false on this part.`);
      }
    }
  }
  const th = (p.thickness ?? 0.03) / 2;
  const pOutline = p.points; if (!pOutline || pOutline.length < 3) throw new Error('fin needs >=3 outline points');
  // canonicalise outline to CCW in (u,v) — makes every winding below deterministic
  let area2 = 0;
  for (let i = 0; i < pOutline.length; i++) {
    const [u0, v0] = pOutline[i], [u1, v1] = pOutline[(i + 1) % pOutline.length];
    area2 += u0 * v1 - u1 * v0;
  }
  const poly = area2 < 0 ? pOutline.slice().reverse() : pOutline;
  const ring = poly.map(([u, v]) => G.add(o, G.add(G.mul(U, u), G.mul(Vv, v))));
  const n = ring.length; const V = []; const F = [];
  // "bevel": 0..1 — the two faces shrink toward the outline's centroid by that
  // fraction and the full outline becomes a mid rim, so the plate is a lens
  // with a chamfered edge instead of a slab of card. Ears, scales, leaves and
  // shields all read as having thickness; a slab reads as paper.
  const bev = Math.max(0, Math.min(0.9, p.bevel || 0));
  if (bev > 0) {
    const cen = ring.reduce((a, q) => G.add(a, q), [0, 0, 0]).map(x => x / n);
    const shrunk = ring.map(q => G.add(cen, G.mul(G.sub(q, cen), 1 - bev)));
    for (const q of shrunk) V.push(G.add(q, G.mul(Nn, th)));          // 0..n-1  front
    for (const q of shrunk) V.push(G.sub(q, G.mul(Nn, th)));          // n..2n-1 back
    for (const q of ring) V.push(q);                                  // 2n..3n-1 rim
    for (let i = 1; i < n - 1; i++) F.push([0, i, i + 1]);
    for (let i = 1; i < n - 1; i++) F.push([n, n + i + 1, n + i]);
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      F.push([2 * n + i, 2 * n + j, j, i]);                           // rim → front
      F.push([n + i, n + j, 2 * n + j, 2 * n + i]);                   // back → rim
    }
    return { material: p.material, V, F, skin: V.map(() => [[p.host, 1]]) };
  }
  for (const q of ring) V.push(G.add(q, G.mul(Nn, th)));
  for (const q of ring) V.push(G.sub(q, G.mul(Nn, th)));
  for (let i = 1; i < n - 1; i++) F.push([0, i, i + 1]);            // front fan (+N)
  for (let i = 1; i < n - 1; i++) F.push([n, n + i + 1, n + i]);    // back fan (−N)
  for (let i = 0; i < n; i++) F.push([n + i, n + (i + 1) % n, (i + 1) % n, i]); // rim (outward)
  return { material: p.material, V, F, skin: V.map(() => [[p.host, 1]]) };
}

function mirrorMesh(m, rDelta, mj = mirrorName) { // duplicate across X with flipped winding + L→R joints
  // mj maps a joint to its twin. It must leave a CENTRE-LINE joint alone even when
  // its name starts with "L" ("Loin", "Lip", "Lumbar"): a tuft inherits the body
  // ring's weights, and the bare prefix rule sent "Loin" to a "Roin" that does not
  // exist — skinVerts() then died with a TypeError instead of a BLOCK.
  // rDelta: per-R-joint translation from "joints_R" pose overrides — verts follow
  // their joints by skin weight, so a staggered right side carries its skin along
  const shift = (v, infl) => {
    if (!rDelta || !infl) return v;
    let dx = 0, dy = 0, dz = 0;
    for (const [j, w] of infl) {
      const d = rDelta[mj(j)];
      if (d) { dx += w * d[0]; dy += w * d[1]; dz += w * d[2]; }
    }
    return [v[0] + dx, v[1] + dy, v[2] + dz];
  };
  // `chain` has to come along. A mirrored VOLUME used to arrive with no chain
  // name at all (compile() re-labels mirrored PARTS afterwards, volumes it
  // does not), so the twin was anonymous to anything that identifies a mesh by
  // the chain it was grown from — the shading stack read a right leg declared
  // `"shade": "hard"` as flesh, because the declaration is keyed by chain and
  // the twin no longer had one.
  return { material: m.material, faceted: m.faceted, smoothAngle: m.smoothAngle,
    join: m.join, _seatIdx: m._seatIdx, chain: m.chain,
    doubleSided: m.doubleSided,
    V: m.V.map((v, i) => shift([-v[0], v[1], v[2]], m.skin && m.skin[i])),
    F: m.F.map(f => f.slice().reverse()),
    C: m.C ? m.C.map(c => c.slice()) : undefined,
    skin: m.skin ? m.skin.map(infl => infl.map(([j, w]) => [mj(j), w])) : undefined,
    // index-based ring topology survives mirroring → mirrored volumes still get
    // proper cylindrical UVs (their own atlas island, required for AO bakes)
    _ringIdx: m._ringIdx, _ringT: m._ringT, _sides: m._sides, _dome0: m._dome0, _open: m._open,
    _pts: m._pts ? m._pts.map(p => [-p[0], p[1], p[2]]) : undefined };
}

function rPoseDeltas(spec) {   // joints_R override − default mirror = per-joint shift
  if (!spec.joints_R) return null;
  const d = {};
  for (const [rn, pos] of Object.entries(spec.joints_R)) {
    const lp = spec.joints['L' + rn.slice(1)];
    if (!lp) continue;
    d[rn] = [pos[0] + lp[0], pos[1] - lp[1], pos[2] - lp[2]];  // default was [-lx, ly, lz]
  }
  return d;
}

function compile(spec) {
  const meshes = []; const builtVols = {}; const rd = rPoseDeltas(spec);
  // the joints that really HAVE a right twin — the same rule skeleton.js uses to
  // make them: every joint of a mirrored chain, and loose L* joints
  const twinned = new Set();
  for (const cn of spec.mirror || []) for (const j of spec.chains[cn] || []) twinned.add(j);
  {
    const inChains = new Set(Object.values(spec.chains || {}).flat());
    for (const n of Object.keys(spec.joints || {})) if (!inChains.has(n) && n.startsWith('L')) twinned.add(n);
  }
  const mj = j => (twinned.has(j) ? mirrorName(j) : j);
  // smoothing angle: spec-level default (50°), overridable per volume/part.
  // mirrorMesh copies it along with everything else it carries.
  const defSmooth = spec.smooth_angle ?? 50;
  for (const vol of spec.volumes || []) {
    const m = buildVolume(spec, vol);
    m.smoothAngle = vol.smooth_angle ?? defSmooth;
    builtVols[vol.chain] = m;
    meshes.push(m);
    if ((spec.mirror || []).includes(vol.chain)) {
      const t = mirrorMesh(m, rd, mj);
      t._mirrorSrc = m;      // lets checks compare the twin's shape against the original
      meshes.push(t);
    }
  }
  const BUILDERS = { spike: buildSpike, curve: buildCurve, membrane: buildMembrane, hand: buildHand,
    paw: buildPaw, fin: (s2, p2) => buildFin(s2, p2, builtVols),
    tufts: (s2, p2) => buildTufts(s2, p2, builtVols) };
  // the parts built so far, by name: what a later part may be seated on
  // (host_part). The value is the part's PRIMARY mesh and its twin, if any.
  const byName = new Map();
  for (const p0 of spec.parts || []) {
    let p = p0;
    const label = p.name || `${p.type}@${p.host || p.host_part || 'ribs'}`;
    const sa = p.smooth_angle ?? defSmooth;
    let hostMesh = null;
    if (p.host_part) {
      if (p.type === 'eye' || p.type === 'membrane' || p.type === 'tufts')
        throw new Error(`part "${label}": a ${p.type} cannot be seated with host_part — it places itself (an eye by anchor, a membrane by its ribs, tufts by their anchor)`);
      ({ p2: p, hostMesh } = resolveHostPart(spec, p, byName));
    }
    // which volume is this part supposed to be growing out of? Either declared
    // via anchor.chain, or the chain that owns its host joint. checks.js needs
    // it to tell "buried in the host" from "floating next to the host". A part
    // seated on a part inherits its host's chain and carries the host mesh too.
    const hostChain = hostMesh ? (hostMesh.hostChain || null)
      : (p.anchor && p.anchor.chain)
      || (p.host && Object.keys(spec.chains || {}).find(c => (spec.chains[c] || []).includes(p.host)))
      || null;
    if (p.type === 'eye') {
      // an eye part is a PAIR of meshes; they are two objects and get two names
      for (const m of buildEye(spec, p, builtVols)) {
        m.part = label + (m.sub ? '.' + m.sub : '') + '.' + m.side; m.partName = label; m.smoothAngle = sa; m.partType = p.type;
        m.hostChain = hostChain; meshes.push(m); }
    } else if (BUILDERS[p.type]) {
      // a builder may return several meshes (a paw and its claws): the first is
      // the part itself, the rest are named `<part>.<sub>` and carry their own
      // shade class / join when the builder says so
      const built = BUILDERS[p.type](spec, p);
      let first = true;
      for (const m of Array.isArray(built) ? built : [built]) {
        const lbl = m.sub ? label + '.' + m.sub : label;
        m.part = lbl; m.partName = label; m.smoothAngle = sa; m.partType = p.type; m.hostChain = hostChain;
        if (hostMesh) { m.hostPart = hostMesh; inheritSkin(m, hostMesh); }
        meshes.push(m);
        let t = null;
        if (p.mirrored) { t = mirrorMesh(m, rd, mj); t.part = lbl + '.R'; t.partName = label; t._mirrorSrc = m;
          t.partType = p.type; t.hostChain = hostChain; t.shade = m.shade;
          // the twin sits on the host's twin when the host was mirrored too,
          // else on the same (centre-line) host
          if (hostMesh) t.hostPart = (byName.get(p0.host_part) || {}).twin || hostMesh;
          meshes.push(t); }
        if (first) { byName.set(label, { mesh: m, twin: t, spec: p0 }); first = false; }
      }
    } else throw new Error(`unknown part type "${p.type}"`);
  }
  // attach material colors
  for (const m of meshes) {
    const pal = (spec.palette || {})[m.material];
    if (!pal) throw new Error(`material "${m.material}" not in palette`);
    m.color = pal.color; m.rough = pal.rough; m.metal = pal.metal;
  }
  applyShading(spec, meshes);
  return meshes;
}

// Which shading pass owns this build. `"shading": {"stack": false}` falls back
// to the 1.2.0 ramp-and-grain for a spec that was tuned against it.
function useStack(spec) {
  const sh = spec.shading || {};
  return sh.stack !== false;
}

// ── whole-body shading pass ────────────────────────────────────────────────
// ONE top-to-bottom value ramp and ONE grain size across the entire creature,
// applied to EVERY mesh — volumes, paws, ears, eyes, horns alike. Two reasons
// it lives here instead of inside each volume:
//   · the ramp is measured over the WHOLE body's Y range, so the same numbers
//     mean the same thing on an upright leg and a horizontal torso (per-volume
//     ranges forced the wolf to write bottom -0.16 on legs and -0.04 on the
//     torso to fake one consistent light);
//   · parts have no `colors` block at all, so under the old scheme paws, ears
//     and claws never received any shading and read as stickers on the body.
// Noise size is a FRACTION OF THE MODEL DIAGONAL, not an absolute distance:
// an absolute cell keeps its world size as the creature scales, so the same
// spec on a giant produced grain finer than the vertex spacing and aliased.
function applyShading(spec, meshes) {
  const sh = spec.shading || {};
  // The L1-L8 stack supersedes this pass and runs LATER (it needs AO and vertex
  // normals as inputs, and those do not exist until ao.js has run). When it is
  // active this whole function is a no-op — running both would apply two
  // top-to-bottom ramps to the same vertices.
  if (useStack(spec)) return;
  const grad = sh.gradient === undefined ? { top: 0.30, bottom: -0.88 } : sh.gradient;
  const nz = sh.noise === undefined ? { size: 0.018, amount: 0.26 } : sh.noise;
  if (!meshes.length) return;

  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const m of meshes) for (const v of m.V) for (let k = 0; k < 3; k++) {
    if (v[k] < lo[k]) lo[k] = v[k];
    if (v[k] > hi[k]) hi[k] = v[k];
  }
  const y0 = lo[1], y1 = hi[1] > lo[1] ? hi[1] : lo[1] + 1e-6;
  const diag = Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]) || 1;
  const cell = nz && nz.amount ? (nz.size ?? 0.018) * diag : 0;
  const cl = x => Math.min(1, Math.max(0, x));

  for (const m of meshes) {
    if (!m.C) m.C = m.V.map(() => hex2lin(m.color || '#888888'));
    m.V.forEach((v, i) => {
      let c = m.C[i];
      if (grad) {
        const f = (v[1] - y0) / (y1 - y0);
        const k = 1 + (grad.top ?? 0) * f + (grad.bottom ?? 0) * (1 - f);
        c = [cl(c[0] * k), cl(c[1] * k), cl(c[2] * k)];
      }
      if (cell) {
        const k = 1 + (vnoise(v, cell) - 0.5) * 2 * nz.amount;
        c = [cl(c[0] * k), cl(c[1] * k), cl(c[2] * k)];
      }
      m.C[i] = c;
    });
  }
  INFO.push(`shading: body-Y ramp top ${(grad && grad.top) ?? 0} / bottom ${(grad && grad.bottom) ?? 0}`
    + (cell ? `, grain ${(cell).toFixed(4)} (${((nz.size ?? 0.018) * 100).toFixed(1)}% of the ${diag.toFixed(2)} diagonal)` : ', no grain')
    + ` — applied to all ${meshes.length} meshes`);
}

module.exports = { compile, drainInfo, useStack };
