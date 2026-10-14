// ACS engine — cross-section vocabulary. Author: Ariescar.
// Rich ring generation on top of the frame math (framesOf lineage):
//   exp  — superellipse exponent: 2 = ellipse, 3-6 = boxy slab, 1.2-1.6 = diamond-ish
//   bias — vertical asymmetry: +0.3 = egg (fuller on top), -0.3 = keel (fuller below)
//   roll — rotate the section in its plane (radians)
//   taper — WEDGE: the half-width scales with height, +0.3 = wider at the top
//           (brow / cheekbones) and narrower below (jaw), -0.3 the reverse (a
//           heavy jowl). This is the plane a head is missing when it reads as
//           a cone or a tube from 45°: an ellipse has no cheek and no jaw.
//   cup  — CRESCENT: the section is bent along its width, +0.5 lifts both
//           edges toward +H so the face at 0° is concave (a cupped ear, a
//           scooped fin); negative cups the other way. The mid-line stays put.
// Per-ring overrides allowed via the profile row: [t, w, h, {exp,bias,roll,taper,cup}]
'use strict';
const G = require('./geometry.js');

function sectionPoint(a, rw, rh, exp, bias, taper, cup) {
  const c = Math.cos(a), s = Math.sin(a);
  const e = 2 / (exp || 2);
  let x = Math.sign(c) * Math.pow(Math.abs(c), e) * rw;
  let y = Math.sign(s) * Math.pow(Math.abs(s), e) * rh;
  if (bias) y *= s > 0 ? (1 + bias) : (1 - bias);
  // wedge: width follows height (y/rh in -1..1); clamped so a large taper
  // never folds the lower edge through the centre line
  if (taper) x *= Math.max(0.15, 1 + taper * (rh ? y / rh : 0));
  // crescent: both edges lift with the square of the width position
  if (cup) y += cup * rh * ((rw ? x / rw : 0) ** 2 - 0.5);
  return [x, y];
}

// named custom section: closed 2D polygon [[x,y]...] in ~unit space, sampled
// by angle position around the list. Concave relief — bark flutes, crescents,
// star sections — has to be built as real geometry: a texture can darken a
// groove but never moves the silhouette, and the silhouette is what gets read.
function polyPoint(pts, a, rw, rh) {
  const n = pts.length;
  const f = (((a / (2 * Math.PI)) % 1) + 1) % 1 * n;
  const i = Math.floor(f) % n, j = (i + 1) % n, t = f - Math.floor(f);
  return [(pts[i][0] + (pts[j][0] - pts[i][0]) * t) * rw,
          (pts[i][1] + (pts[j][1] - pts[i][1]) * t) * rh];
}

// pts: chain joints; radii: [[rw,rh],...] per joint; secs: [{exp,bias,roll}] per joint
// twist (radians, optional): every ring's frame is turned about its tangent by
// this much before the section is laid on it — a REAL rotation of the section
// (`roll` only re-phases the vertices around an unchanged ellipse), which is
// how a curve's "face" aims its 0° side at a world direction.
function chainRingsRich(pts, radii, N, frame, secs, twist = 0) {
  const { fr, tan } = require('./geometry.js').framesOf
    ? require('./geometry.js').framesOf(pts, frame)
    : (() => { throw new Error('framesOf missing'); })();
  const rings = [];
  for (let s = 0; s < pts.length; s++) {
    let [U, W] = fr[s];
    if (twist) {
      const c = Math.cos(twist), sn = Math.sin(twist);
      const W2 = G.nrm(G.add(G.mul(W, c), G.mul(U, sn)));
      U = G.nrm(G.cross(W2, tan[s])); W = W2;
      if (G.dot(G.cross(U, W), tan[s]) < 0) U = G.mul(U, -1);
    }
    const [rw, rh] = Array.isArray(radii[s]) ? radii[s] : [radii[s], radii[s]];
    const sec = secs[s] || {};
    const ring = [];
    for (let k = 0; k < N; k++) {
      const a = 2 * Math.PI * k / N + (sec.roll || 0);
      const [x, y] = sec.pts ? polyPoint(sec.pts, a, rw, rh)
                             : sectionPoint(a, rw, rh, sec.exp, sec.bias, sec.taper, sec.cup);
      ring.push(G.add(pts[s], G.add(G.mul(U, x), G.mul(W, y))));
    }
    rings.push(ring);
  }
  return rings;
}

module.exports = { chainRingsRich, sectionPoint, polyPoint };
