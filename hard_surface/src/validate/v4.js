// V4 — ground plane and static stability.
//
// DEVIATION (M1): the brief reads "2D hull of GROUND parts' xz AABBs". Taken
// literally the M0 massing fails: only `mass_l` carries ground:true, while
// mass_m and mass_r are attached flush at align:bottom and stand on the same
// y = 0 plane, so the hull would be one 6 m building and the centre of mass of
// a 17 m terrace sits 5.4 m outside it. The footprint here is every part whose
// world AABB touches y = 0 — the parts actually carrying the load — which is
// what "ground-contact footprint" means in 02:T2. The `ground:true` parts are
// still the ones whose min-y is pinned to 0.
export function validateV4(ctx, make) {
  const { parts, EPS } = ctx;
  const violations = [];

  for (const part of parts) {
    if (part.contact !== "ground") continue;
    const minY = part.aabb.min[1];
    if (Math.abs(minY) > EPS) {
      violations.push(make("V4", part.id, `min y = ${fmt(minY)} m`, `0 +- ${fmt(EPS)} m`,
        `ground part "${part.id}" floats ${fmt(Math.abs(minY))} m off the ground plane — drop it to y = 0`));
    }
  }

  let mass = 0;
  let cx = 0;
  let cz = 0;
  const footprint = [];
  for (const part of parts) {
    const volume = part.dims[0] * part.dims[1] * part.dims[2];
    mass += volume;
    cx += volume * (part.aabb.min[0] + part.aabb.max[0]) / 2;
    cz += volume * (part.aabb.min[2] + part.aabb.max[2]) / 2;
    if (part.aabb.min[1] <= EPS) {
      footprint.push([part.aabb.min[0], part.aabb.min[2]], [part.aabb.max[0], part.aabb.min[2]],
        [part.aabb.max[0], part.aabb.max[2]], [part.aabb.min[0], part.aabb.max[2]]);
    }
  }
  if (mass <= 0 || footprint.length === 0) return { violations, advisories: [] };

  const com = [cx / mass, cz / mass];
  const hull = convexHull(footprint);
  const outside = distanceOutside(hull, com);
  if (outside > EPS) {
    violations.push(make("V4", null, `centre of mass ${fmt(outside)} m outside the footprint`, `inside +- ${fmt(EPS)} m`,
      `the model tips: centre of mass at x ${fmt(com[0])}, z ${fmt(com[1])} is ${fmt(outside)} m outside the ground-contact hull — widen the base or move mass inboard`));
  }

  return { violations, advisories: [] };
}

/** Andrew monotone chain, counter-clockwise. */
function convexHull(points) {
  const pts = [...points].sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  if (pts.length < 3) return pts;
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const build = (list) => {
    const out = [];
    for (const p of list) {
      while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) out.pop();
      out.push(p);
    }
    out.pop();
    return out;
  };
  return [...build(pts), ...build([...pts].reverse())];
}

/** 0 when inside; otherwise the distance to the nearest hull edge. */
function distanceOutside(hull, p) {
  if (hull.length < 3) return 0;
  let worst = -Infinity;
  for (let i = 0; i < hull.length; i += 1) {
    const a = hull[i];
    const b = hull[(i + 1) % hull.length];
    const ex = b[0] - a[0];
    const ez = b[1] - a[1];
    const length = Math.hypot(ex, ez);
    if (length < 1e-12) continue;
    const signed = ((p[0] - a[0]) * ez - (p[1] - a[1]) * ex) / length;   // > 0 = outside (CCW hull)
    if (signed > worst) worst = signed;
  }
  return Math.max(0, worst);
}

function fmt(value) {
  return (Math.round(value * 1000) / 1000).toFixed(3);
}
