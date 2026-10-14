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
const { mirrorName } = require('./skeleton.js');

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
    if (host && host !== m) {
      // the ROOT bone of an attached chain: the only share of a vertex's skin
      // the blend may hand to the host (blendJunctionSkin). A twin's skin names
      // the R joints, so its root is the mirrored name.
      let root = null, along = null, rootR = 0, depth = 1, travel = 0;
      if (isVol(m)) {
        const names = spec.chains[m.chain] || [];
        if (names[0]) root = m._mirrorSrc ? mirrorName(names[0]) : names[0];
        ({ along, rootR } = alongChain(spec, m, names));
        // HOW DEEP the blend may go is set by how far the root joint actually
        // swings in the clips. A vertex the band hands to the host stays put
        // while the limb swings; the vertex a band's width further out goes the
        // whole way, 2R·sin(θ/2) for a root ring of radius R turned θ. The
        // stretch a linear ramp puts on the rings between is about
        // 1 + depth·2R·sin(θ/2)/band, and that is a property of the CLIP, not
        // of the mesh: the wolf's foreleg swings 26° at R = 0.08 (3 cm over an
        // 11 cm band, nothing to spread), the giant raises its fist 152° at
        // R = 0.42 (81 cm over a 36 cm band, 3.3x on its own, before the elbow
        // adds its bend). The depth is capped so the ramp's own share stays
        // near 1.2x; a joint that barely turns keeps the full blend.
        travel = rootTravel(spec, names[0]);
        const swing = 2 * rootR * Math.sin(Math.min(180, travel) * Math.PI / 360);
        if (swing > 0) depth = Math.min(1, JUNCTION_RAMP_STRETCH * skinBand / swing);
      }
      out.push({ m, host, band, skinBand, root, along, rootR, depth, travel,
                 amount: nsh.junction ?? 1, skin: nsh.junction_skin ?? 1 });
    }
  }
  return out;
}

// the share of edge stretch the blend ramp itself may add across the band
const JUNCTION_RAMP_STRETCH = 1.2;

// the largest rotation the clips put on a joint (degrees, all axes combined,
// conservatively — keys are the extremes, so the key values are what is read).
// A mirrored twin's joint carries the L side's tracks, so the L name is asked.
function rootTravel(spec, jn) {
  let best = 0;
  const names = new Set([jn, mirrorName(jn)]);
  for (const a of Object.values(spec.animations || {})) {
    for (const n of names) {
      const tr = (a.tracks || {})[n]; if (!tr) continue;
      const peak = ax => Math.max(0, ...(tr[ax] || []).map(k => Math.abs(k[1])));
      best = Math.max(best, Math.hypot(peak('rx'), peak('ry'), peak('rz')));
    }
  }
  return best;
}

// How far ALONG its chain each vertex of a volume sits, in metres from the root
// ring (dome rings before it count as 0), and the root ring's radius. The
// rings carry their arc-length t; a cap fan's apex takes the distance to the
// nearer chain end.
function alongChain(spec, m, names) {
  const J = names.map(n => spec.joints[n]).filter(Boolean);
  let L = 0;
  for (let i = 1; i < J.length; i++) L += Math.hypot(J[i][0] - J[i - 1][0], J[i][1] - J[i - 1][1], J[i][2] - J[i - 1][2]);
  const along = new Array(m.V.length).fill(null);
  if (m._ringIdx && m._ringT) m._ringIdx.forEach((ring, k) => {
    const a = Math.max(0, (m._ringT[k] ?? 0)) * L;
    for (const vi of ring) if (vi !== undefined) along[vi] = a;
  });
  const root = J[0], tip = J[J.length - 1];
  const sx = m._mirrorSrc ? -1 : 1;
  for (let vi = 0; vi < along.length; vi++) {
    if (along[vi] !== null || !root) continue;
    const v = m.V[vi];
    const d0 = Math.hypot(v[0] - sx * root[0], v[1] - root[1], v[2] - root[2]);
    const d1 = tip ? Math.hypot(v[0] - sx * tip[0], v[1] - tip[1], v[2] - tip[2]) : Infinity;
    along[vi] = d0 <= d1 ? 0 : L;
  }
  let rootR = 0;
  if (m._ringIdx && root) {
    const ring = m._ringIdx[m._dome0 || 0] || [];
    for (const vi of ring) if (vi !== undefined) {
      const v = m.V[vi];
      rootR = Math.max(rootR, Math.hypot(v[0] - sx * root[0], v[1] - root[1], v[2] - root[2]));
    }
  }
  return { along, rootR };
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
  for (const { m, host, band, skinBand, skin, root, along, rootR, depth, travel } of pairs) {
    if (!(skin > 0) || !m.skin || !host.skin) continue;
    const near = nearField(m, host, Math.max(band, skinBand));
    let n = 0;
    m.V.forEach((v, vi) => {
      const r = near.get(v);
      if (!r || !m.skin[vi]) return;
      // The ramp variable is the distance to the host's surface — OR how far
      // along the limb the vertex is past its root ring's own radius, whichever
      // is larger. A limb that leaves its host squarely never sees the second
      // term (a ring one radius along is already about one radius clear of
      // the surface). A limb that hangs ALONG its host does: the giant's upper
      // arm lies against a torso 2 m wide with its inner wall buried to the
      // elbow, and by surface distance alone rings half-way down the arm read
      // as "at the junction" and were pinned to the spine.
      let d = r.d;
      if (along && along[vi] !== null) d = Math.max(d, along[vi] - rootR);
      // LINEAR over the skin band, not a smoothstep: a smoothstep puts half the
      // swing between two rings in the middle of the band and the wall there
      // shears past its neighbour (the wolf's foreleg folded 3 triangles at
      // move@0.2). A constant slope spreads the bend evenly over the rings.
      const t = d <= 0 ? 1 : Math.max(0, 1 - d / skinBand);
      const s = Math.min(1, skin * t) * (depth ?? 1);
      if (!(s > 0)) return;
      // ONLY THE ROOT BONE'S SHARE goes to the host. The band is measured from
      // the host's surface, and a limb that hangs along its host (the giant's
      // arm against a torso 2 m wide) has vertices inside the band half-way to
      // the elbow, already weighted to the SECOND joint. Handing those to the
      // torso's skin pinned the elbow to the spine: with the shoulder raised
      // 152° and the elbow bent 100° the pinned vertex stayed while its ring
      // neighbours left, an edge stretched 5.5x and six triangles folded. What
      // the blend is for is the root of the limb deforming with the body, and
      // the root is the share of a vertex that follows the chain's first joint
      // rigidly; a share that already follows a deeper joint is past the
      // shoulder however near the torso it lies, and stays with its bone.
      let rs = 1;
      if (root) { rs = 0; for (const [jn, w] of m.skin[vi]) if (jn === root) rs += w; }
      const give = s * rs;                       // the share of the vertex that moves to the host
      if (!(give > 1e-4)) return;
      const hw = hostWeightsAt(host, r);
      if (!hw.size) return;
      const acc = new Map();
      // a volume keeps every non-root influence whole; a part (skin inherited
      // from its host, no chain root) blends all of it as before
      for (const [jn, w] of m.skin[vi]) acc.set(jn, (acc.get(jn) || 0) + (root && jn !== root ? w : w * (1 - s)));
      for (const [jn, w] of hw) acc.set(jn, (acc.get(jn) || 0) + w * give);
      // four influences is what the file carries (JOINTS_0 / WEIGHTS_0 are VEC4)
      const list = [...acc].filter(x => x[1] > 1e-4).sort((x, y) => y[1] - x[1]).slice(0, 4);
      const tot = list.reduce((a2, x) => a2 + x[1], 0) || 1;
      m.skin[vi] = list.map(([jn, w]) => [jn, w / tot]);
      n++;
    });
    const label = m.part || (m.chain && m._mirrorSrc ? m.chain + '.R' : m.chain);
    if (n) moved.push([label, n]);
    if (n && depth < 0.999 && INFO)
      INFO.push(`junction skin: "${label}" blends only ${Math.round(depth * 100)}% of the way to its host — `
        + `${root} turns ${Math.round(travel)}° in the clips, and a root ring of radius ${rootR.toFixed(2)} `
        + `swung that far moves ${(2 * rootR * Math.sin(Math.min(180, travel) * Math.PI / 360)).toFixed(2)} m `
        + `across a ${skinBand.toFixed(2)} m band; a full blend would tear the rings between`);
  }
  if (INFO && moved.length) {
    const tot = moved.reduce((a, r) => a + r[1], 0);
    INFO.push(`junction skin: ${tot} vertices on ${moved.length} attached pieces blend their skin weights `
      + `toward the host across the junction band (${moved.map(r => r[0]).join(', ')})`);
  }
  return moved;
}

module.exports = { junctionPairs, blendJunctionSkin, nearField, hostWeightsAt };
