// ACS engine — junctions: where an attached piece meets its host.
//
// A limb chain on its `attach` host, a head on the neck, a hosted part (paw,
// ear, tuft, claw) on the chain or part it grows from. The junction band is a
// shell of `junction_band` x model height around the host's surface, and two
// things happen inside it:
//
//   NORMALS  the attached piece takes the host's shipped normal (glb.js,
//            junctionField) so the lighting runs continuously off the torso
//            and onto the leg instead of catching a hard bright edge.
//
//   SKIN     the attached piece takes the host's SKIN WEIGHTS, ramping from
//            all-host where it is buried to all-its-own at the outer edge of
//            the band (blendJunctionSkin, here).
//
// The second exists because the first did not hold up in motion. A limb's
// root ring is weighted 100% to the limb's own first joint, so when the limb
// swings, the whole root — including the rings sitting in the band, whose
// normals had been copied from the torso in bind pose — rotates rigidly with
// the limb bone. The copied normals rotate with it, the torso's do not, and
// the seam that was gone at rest reappears at every step. Blending the skin
// across the band is what every game rig does at a shoulder: the root of the
// limb deforms WITH the body, the bend is spread over the band instead of
// happening on one ring, and a normal copied from the host now travels with
// the same bones the host's own normal travels with, so the continuity holds
// mid-clip. It is the geometry that is continuous now, not only the shading.
//
// The host weights a vertex takes are the host's own skin at the closest
// surface point (interpolated over the hit triangle), not "the attach joint":
// a torso's skin near the shoulder is a blend of two body joints, and the leg
// root should follow exactly that blend.
'use strict';
const { nearest } = require('./inside.js');

// The pieces that meet a host, from the spec's attach / host declarations.
// Flesh only: the seam is a flesh problem (skin wraps bone), and a hard plate's
// facing has nothing to do with the mass it is bolted to. Requires m._cls, i.e.
// assignClasses() from shade.js has run.
function junctionPairs(spec, meshes) {
  const nsh = (spec.shading || {}).normals || {};
  const ys = meshes.flatMap(m => m.V.map(v => v[1]));
  const modelH = Math.max(1e-6, Math.max(...ys) - Math.min(...ys));
  const band = (nsh.junction_band ?? 0.06) * modelH;
  // the SKIN band is wider than the normal band: the bend needs room. Measured
  // on the wolf's foreleg (26° swing): a ramp over the 0.06 band peaks at 2.4x
  // edge stretch, over 0.09 at 2.1x, and neither folds; the pre-blend limb
  // (rigid root) peaked at 3.5x, over the 3x ceiling, once the root ring was
  // pinned to the torso by a hard step.
  const skinBand = (nsh.junction_skin_band ?? 0.09) * modelH;
  const out = [];
  if (!(band > 0)) return out;
  // A VOLUME is any mesh grown from a chain that is not a part. Mirrored twins
  // carry no _rings (mirrorMesh does not copy them), so testing _rings found
  // only the left side: the right legs had no host at all, and a right paw's
  // host fell back to the LEFT leg, 20 cm away — every right-hand junction
  // shipped without the blend, the left-hand ones with it.
  const isVol = x => !x.part && x.chain;
  const volOf = (chain, twin) => meshes.find(x => isVol(x) && x.chain === chain && !!x._mirrorSrc === twin)
                              || meshes.find(x => isVol(x) && x.chain === chain && !x._mirrorSrc);
  // the chain that OWNS the attach joint: one with a volume, and not the piece
  // itself (same rule as root_containment) — the first chain that merely lists
  // the joint may be the attached chain or a volume-less guide
  const chainOfJoint = (j, self) => Object.keys(spec.chains || {}).find(c => c !== self
    && (spec.chains[c] || []).includes(j) && meshes.some(x => isVol(x) && x.chain === c));
  for (const m of meshes) {
    if (m._cls !== 'flesh') continue;
    let host = null;
    if (isVol(m) && (spec.attach || {})[m.chain]) {
      const hc = chainOfJoint(spec.attach[m.chain], m.chain);
      if (hc) host = volOf(hc, !!m._mirrorSrc);
    } else if (m.part && m.hostPart) host = m.hostPart;          // a part seated on a part
    else if (m.part && m.hostChain) host = volOf(m.hostChain, !!m._mirrorSrc);
    if (host && host !== m)
      out.push({ m, host, band, skinBand, amount: nsh.junction ?? 1, skin: nsh.junction_skin ?? 1 });
  }
  return out;
}

// the closest host surface point for every vertex of m inside the band, cached
// on the mesh (keyed by the point object, which survives the crease split in
// glb.js) so the skin pass and the normal pass share one search
function nearField(m, host, band) {
  if (m._jNear && m._jNearHost === host && m._jNearBand >= band) return m._jNear;
  const out = new Map();
  for (const v of m.V) {
    const r = nearest(v, host);
    if (!r || r.d >= band) continue;
    out.set(v, r);
  }
  Object.defineProperty(m, '_jNear', { value: out, enumerable: false, writable: true, configurable: true });
  Object.defineProperty(m, '_jNearHost', { value: host, enumerable: false, writable: true, configurable: true });
  Object.defineProperty(m, '_jNearBand', { value: band, enumerable: false, writable: true, configurable: true });
  return out;
}

// the host's skin weights at the hit point, interpolated over the triangle by
// inverse distance to its corners (the same rule junctionField uses for the
// normal, so the two ramps agree)
function hostWeightsAt(host, r) {
  const { a, b, c, i } = r.tri;
  const ws = [a, b, c].map(q => 1 / (1e-6 + Math.hypot(r.q[0] - q[0], r.q[1] - q[1], r.q[2] - q[2])));
  const tot = ws[0] + ws[1] + ws[2];
  const acc = new Map();
  for (let k = 0; k < 3; k++) {
    const infl = host.skin && host.skin[i[k]];
    if (!infl) continue;
    for (const [jn, w] of infl) acc.set(jn, (acc.get(jn) || 0) + w * ws[k] / tot);
  }
  return acc;
}

// Blend each attached piece's skin toward its host's across the band. Returns
// [[label, movedCount], ...] for the build narration. Runs BEFORE the checks,
// so anim_integrity, self_clip and ground_clip see the skin that ships.
function blendJunctionSkin(pairs, INFO) {
  const moved = [];
  for (const { m, host, band, skinBand, skin } of pairs) {
    if (!(skin > 0) || !m.skin || !host.skin) continue;
    const near = nearField(m, host, Math.max(band, skinBand));
    let n = 0;
    m.V.forEach((v, vi) => {
      const r = near.get(v);
      if (!r || !m.skin[vi]) return;
      // LINEAR over the skin band, not a smoothstep: a smoothstep puts half the
      // swing between two rings in the middle of the band and the wall there
      // shears past its neighbour (the wolf's foreleg folded 3 triangles at
      // move@0.2). A constant slope spreads the bend evenly over the rings.
      const t = r.d <= 0 ? 1 : Math.max(0, 1 - r.d / skinBand);
      const s = Math.min(1, skin * t);
      if (!(s > 0)) return;
      const hw = hostWeightsAt(host, r);
      if (!hw.size) return;
      const acc = new Map();
      for (const [jn, w] of m.skin[vi]) acc.set(jn, (acc.get(jn) || 0) + w * (1 - s));
      for (const [jn, w] of hw) acc.set(jn, (acc.get(jn) || 0) + w * s);
      // four influences is what the file carries (JOINTS_0 / WEIGHTS_0 are VEC4)
      const list = [...acc].filter(x => x[1] > 1e-4).sort((x, y) => y[1] - x[1]).slice(0, 4);
      const tot = list.reduce((a2, x) => a2 + x[1], 0) || 1;
      m.skin[vi] = list.map(([jn, w]) => [jn, w / tot]);
      n++;
    });
    if (n) moved.push([m.part || (m.chain && m._mirrorSrc ? m.chain + '.R' : m.chain), n]);
  }
  if (INFO && moved.length) {
    const tot = moved.reduce((a, r) => a + r[1], 0);
    INFO.push(`junction skin: ${tot} vertices on ${moved.length} attached pieces blend their skin weights `
      + `toward the host across the junction band (${moved.map(r => r[0]).join(', ')})`);
  }
  return moved;
}

module.exports = { junctionPairs, blendJunctionSkin, nearField, hostWeightsAt };
