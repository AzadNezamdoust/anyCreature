// 2D profiles for the V2 kernel. Pure maths: no WASM, no clock, no RNG.
//
// A profile is a plain array of `[x, y]` pairs in METRES, closed implicitly
// (the last point joins the first), wound COUNTER-CLOCKWISE. Every helper here
// returns that shape, so `profile.offset()` composes with any of them and an
// author can hand-build one with `profile.poly()`.
//
// The frame is the EXTRUSION frame: x is the profile's width axis, y its
// height axis, and `K.extrude()` pushes it along +Z. Bases sit at y = 0 so a
// profile extruded and placed with `.at()` lands where the author says.

/** Every kernel failure an author can cause. Message starts with the code. */
export class KernelError extends Error {
  constructor(message) {
    super(message);
    this.name = "KernelError";
  }
}

const EPS = 1e-9;

function num(value, what) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new KernelError(`BAD_ARG: ${what} must be a finite number, got ${JSON.stringify(value)}`);
  }
  return value;
}

function positive(value, what) {
  if (num(value, what) <= 0) throw new KernelError(`BAD_ARG: ${what} must be > 0, got ${value}`);
  return value;
}

/** Twice the signed area. > 0 means counter-clockwise. */
function signedArea2(points) {
  let sum = 0;
  for (let i = 0; i < points.length; i += 1) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[(i + 1) % points.length];
    sum += x0 * y1 - x1 * y0;
  }
  return sum;
}

function cross(ax, ay, bx, by) {
  return ax * by - ay * bx;
}

/** Do the open segments p0-p1 and q0-q1 cross? Endpoint touches are allowed. */
function segmentsCross(p0, p1, q0, q1) {
  const d1 = cross(p1[0] - p0[0], p1[1] - p0[1], q0[0] - p0[0], q0[1] - p0[1]);
  const d2 = cross(p1[0] - p0[0], p1[1] - p0[1], q1[0] - p0[0], q1[1] - p0[1]);
  const d3 = cross(q1[0] - q0[0], q1[1] - q0[1], p0[0] - q0[0], p0[1] - q0[1]);
  const d4 = cross(q1[0] - q0[0], q1[1] - q0[1], p1[0] - q0[0], p1[1] - q0[1]);
  return d1 * d2 < -EPS && d3 * d4 < -EPS;
}

/**
 * Validate a raw point list and return it wound CCW.
 * Throws on < 3 points, a non-pair entry, a non-finite number, zero area, or a
 * self-intersection (O(n^2) segment sweep - profiles here are tens of points).
 */
export function poly(points) {
  if (!Array.isArray(points) || points.length < 3) {
    throw new KernelError(`BAD_PROFILE: need >= 3 points, got ${Array.isArray(points) ? points.length : typeof points}`);
  }
  const out = points.map((p, i) => {
    if (!Array.isArray(p) || p.length !== 2) throw new KernelError(`BAD_PROFILE: point ${i} is not [x, y]`);
    return [num(p[0], `point ${i}.x`), num(p[1], `point ${i}.y`)];
  });
  const n = out.length;
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 2; j < n; j += 1) {
      if (i === 0 && j === n - 1) continue;
      if (segmentsCross(out[i], out[(i + 1) % n], out[j], out[(j + 1) % n])) {
        throw new KernelError(`BAD_PROFILE: edges ${i} and ${j} cross (profile must be simple)`);
      }
    }
  }
  const area2 = signedArea2(out);
  if (Math.abs(area2) < EPS) throw new KernelError("BAD_PROFILE: zero area");
  return area2 > 0 ? out : out.reverse();
}

/** Rectangle, centred on x = 0, base at y = 0. */
export function rect({ w, h } = {}) {
  positive(w, "rect.w");
  positive(h, "rect.h");
  return [[-w / 2, 0], [w / 2, 0], [w / 2, h], [-w / 2, h]];
}

/**
 * Arched opening: a rectangle with a segmental (or half-round) head.
 * `h` is the TOTAL height to the crown and `rise` the curved part above the
 * springing line, so the straight jambs are `h - rise` tall. `rise === w / 2`
 * gives an exact semicircle. `segs` is the number of facets across the arc and
 * must be even, so one vertex lands on the crown.
 */
export function arch({ w, h, rise, segs = 12 } = {}) {
  positive(w, "arch.w");
  positive(h, "arch.h");
  positive(rise, "arch.rise");
  if (!Number.isInteger(segs) || segs < 2 || segs % 2 !== 0) {
    throw new KernelError(`BAD_ARG: arch.segs must be an even integer >= 2, got ${segs}`);
  }
  if (rise >= h) throw new KernelError(`BAD_ARG: arch.rise (${rise}) must be < arch.h (${h})`);
  if (rise > w / 2 + EPS) throw new KernelError(`BAD_ARG: arch.rise (${rise}) may not exceed w/2 (${w / 2})`);

  const spring = h - rise;
  const half = w / 2;
  const radius = (rise * rise + half * half) / (2 * rise);
  const centreY = spring - (radius - rise);
  const points = [[-half, 0], [half, 0]];
  const angleRight = Math.atan2(radius - rise, half);
  const angleLeft = Math.PI - angleRight;
  for (let i = 0; i <= segs; i += 1) {
    const t = angleRight + ((angleLeft - angleRight) * i) / segs;
    points.push([radius * Math.cos(t), centreY + radius * Math.sin(t)]);
  }
  return dedupe(points);
}

/**
 * Stacked centred rectangles from y = 0 up - the cornice/plinth profile.
 * `steps` is ordered bottom to top; each `{w, h}` is a course.
 */
export function stepped(steps) {
  if (!Array.isArray(steps) || steps.length === 0) throw new KernelError("BAD_ARG: stepped needs >= 1 step");
  const right = [];
  let y = 0;
  for (const [i, step] of steps.entries()) {
    positive(step?.w, `stepped[${i}].w`);
    positive(step?.h, `stepped[${i}].h`);
    right.push([step.w / 2, y]);
    y += step.h;
    right.push([step.w / 2, y]);
  }
  const left = right.map(([x, yy]) => [-x, yy]).reverse();
  return dedupe([...right, ...left]);
}

/**
 * Awning section: a right triangle (horizontal leg `run`, vertical leg `h`)
 * followed by a rectangle, total width `w`, base at y = 0, left edge sloping
 * from (0, 0) up to (run, h). Extruded along +Z it is a sloped canopy.
 */
export function wedge({ w, h, run } = {}) {
  positive(w, "wedge.w");
  positive(h, "wedge.h");
  positive(run, "wedge.run");
  if (run > w + EPS) throw new KernelError(`BAD_ARG: wedge.run (${run}) may not exceed wedge.w (${w})`);
  return dedupe([[0, 0], [w, 0], [w, h], [run, h]]);
}

const MITRE_LIMIT = 4;

/**
 * Outward offset by `d` metres with mitred corners (negative `d` insets).
 * Each edge slides along its outward normal and consecutive edges are
 * intersected; a corner sharper than MITRE_LIMIT x |d| is bevelled to one
 * point instead. Concave corners may self-intersect at large `d` - that is the
 * S1 limit, and `poly()` rejects the result if they do.
 */
export function offset(profile, d) {
  const points = poly(profile);
  num(d, "offset.d");
  if (Math.abs(d) < EPS) return points;
  const n = points.length;
  const dirs = [];
  const normals = [];
  for (let i = 0; i < n; i += 1) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[(i + 1) % n];
    const len = Math.hypot(x1 - x0, y1 - y0);
    if (len < EPS) throw new KernelError(`BAD_PROFILE: duplicate point at index ${i}`);
    const dx = (x1 - x0) / len;
    const dy = (y1 - y0) / len;
    dirs.push([dx, dy]);
    normals.push([dy, -dx]);          // outward for a CCW winding
  }
  const out = [];
  for (let i = 0; i < n; i += 1) {
    const prev = (i - 1 + n) % n;
    const [pdx, pdy] = dirs[prev];
    const [ndx, ndy] = dirs[i];
    const [pnx, pny] = normals[prev];
    const [nnx, nny] = normals[i];
    const a0 = [points[i][0] + pnx * d, points[i][1] + pny * d];
    const b0 = [points[i][0] + nnx * d, points[i][1] + nny * d];
    const denom = cross(pdx, pdy, ndx, ndy);
    if (Math.abs(denom) < 1e-7) { out.push(b0); continue; }
    const t = cross(b0[0] - a0[0], b0[1] - a0[1], ndx, ndy) / denom;
    const vertex = [a0[0] + pdx * t, a0[1] + pdy * t];
    const reach = Math.hypot(vertex[0] - points[i][0], vertex[1] - points[i][1]);
    if (reach > MITRE_LIMIT * Math.abs(d)) {
      const mx = pnx + nnx;
      const my = pny + nny;
      const mlen = Math.hypot(mx, my) || 1;
      out.push([points[i][0] + (mx / mlen) * d, points[i][1] + (my / mlen) * d]);
    } else {
      out.push(vertex);
    }
  }
  return poly(dedupe(out));
}

function segCount(segs, what) {
  if (!Number.isInteger(segs) || segs < 1) throw new KernelError(`BAD_ARG: ${what} must be an integer >= 1, got ${JSON.stringify(segs)}`);
  return segs;
}

/**
 * V5-2 — round every corner of a profile with a tangent arc of radius `r` (one number, or one per input point in the
 * input's order; 0 keeps that corner sharp), `segs` facets per arc (1 = a straight chamfer). Each corner's tangent
 * length is clamped to half its shorter adjacent edge, so neighbouring arcs never overlap (the radius shrinks to fit).
 * A filleted corner becomes `segs + 1` points; collinear points are kept. Returns a CCW profile like every helper here.
 */
export function fillet(points, r, segs = 3) {
  const pts = poly(points);
  segCount(segs, "fillet.segs");
  const n = pts.length;
  let radii;
  if (Array.isArray(r)) {
    if (r.length !== n) throw new KernelError(`BAD_ARG: fillet r[] needs one radius per point (${n}), got ${r.length}`);
    radii = r.map((v, i) => num(v, `fillet r[${i}]`));
    if (signedArea2(points) < 0) radii.reverse();      // poly() reversed a clockwise input: keep r[i] on point i
  } else {
    radii = new Array(n).fill(num(r, "fillet r"));
  }
  if (radii.some((v) => v < 0)) throw new KernelError("BAD_ARG: fillet r must be >= 0");
  const out = [];
  for (let i = 0; i < n; i += 1) {
    const prev = pts[(i - 1 + n) % n];
    const cur = pts[i];
    const next = pts[(i + 1) % n];
    const lenIn = Math.hypot(cur[0] - prev[0], cur[1] - prev[1]);
    const lenOut = Math.hypot(next[0] - cur[0], next[1] - cur[1]);
    if (lenIn < EPS || lenOut < EPS) throw new KernelError(`BAD_PROFILE: duplicate point at index ${i}`);
    const din = [(cur[0] - prev[0]) / lenIn, (cur[1] - prev[1]) / lenIn];
    const dout = [(next[0] - cur[0]) / lenOut, (next[1] - cur[1]) / lenOut];
    const turnSin = cross(din[0], din[1], dout[0], dout[1]);
    const phi = Math.atan2(Math.abs(turnSin), din[0] * dout[0] + din[1] * dout[1]);   // turning angle, 0..pi
    if (radii[i] <= EPS || phi < 1e-6) { out.push(cur); continue; }
    const tanHalf = Math.tan(phi / 2);
    const t = Math.min(radii[i] * tanHalf, Math.min(lenIn, lenOut) / 2);
    const rr = t / tanHalf;
    const t1 = [cur[0] - din[0] * t, cur[1] - din[1] * t];
    const t2 = [cur[0] + dout[0] * t, cur[1] + dout[1] * t];
    const sgn = turnSin > 0 ? 1 : -1;                   // left turn = convex corner of a CCW profile
    const c = [t1[0] - sgn * din[1] * rr, t1[1] + sgn * din[0] * rr];
    const a1 = Math.atan2(t1[1] - c[1], t1[0] - c[0]);
    out.push(t1);
    for (let j = 1; j < segs; j += 1) {
      const a = a1 + (sgn * phi * j) / segs;
      out.push([c[0] + rr * Math.cos(a), c[1] + rr * Math.sin(a)]);
    }
    out.push(t2);
  }
  return poly(dedupe(out));
}

/**
 * V5-2 — rounded rectangle, CCW, corner radius `r` (clamped to half the shorter side; 0 = sharp) with `segs` facets
 * per corner. Frame: `{ w, h }` centred on x = 0 with its base at y = 0 like `rect`, or explicit bounds
 * `{ x: [x0, x1], y: [y0, y1] }`. `4 * (segs + 1)` points when rounded (fewer where two arcs meet at a side's middle).
 */
export function roundRect({ w, h, x, y, r = 0, segs = 3 } = {}) {
  let x0, x1, y0, y1;
  if (x !== undefined || y !== undefined) {
    const pair = (v, what) => {
      if (!Array.isArray(v) || v.length !== 2) throw new KernelError(`BAD_ARG: roundRect.${what} must be [lo, hi]`);
      const [a, b] = [num(v[0], `roundRect.${what}[0]`), num(v[1], `roundRect.${what}[1]`)];
      if (!(b > a)) throw new KernelError(`BAD_ARG: roundRect.${what} must have hi > lo`);
      return [a, b];
    };
    [x0, x1] = pair(x, "x");
    [y0, y1] = pair(y, "y");
  } else {
    positive(w, "roundRect.w");
    positive(h, "roundRect.h");
    [x0, x1, y0, y1] = [-w / 2, w / 2, 0, h];
  }
  num(r, "roundRect.r");
  if (r < 0) throw new KernelError("BAD_ARG: roundRect.r must be >= 0");
  const k = segCount(segs, "roundRect.segs");
  const rr = Math.min(r, (x1 - x0) / 2, (y1 - y0) / 2);
  if (rr <= EPS) return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
  const pts = [];
  for (const [cx, cy, a0] of [[x1 - rr, y0 + rr, -90], [x1 - rr, y1 - rr, 0], [x0 + rr, y1 - rr, 90], [x0 + rr, y0 + rr, 180]]) {
    for (let j = 0; j <= k; j += 1) {
      const a = ((a0 + (90 * j) / k) * Math.PI) / 180;
      pts.push([cx + rr * Math.cos(a), cy + rr * Math.sin(a)]);
    }
  }
  return dedupe(pts);
}

function dedupe(points) {
  const out = [];
  for (const p of points) {
    const last = out[out.length - 1];
    if (last && Math.abs(last[0] - p[0]) < EPS && Math.abs(last[1] - p[1]) < EPS) continue;
    out.push(p);
  }
  while (out.length > 1) {
    const first = out[0];
    const last = out[out.length - 1];
    if (Math.abs(first[0] - last[0]) < EPS && Math.abs(first[1] - last[1]) < EPS) out.pop();
    else break;
  }
  return out;
}
