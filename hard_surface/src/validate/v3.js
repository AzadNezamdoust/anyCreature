// V3 — contact graph: connected, and every part reaches a `ground` part.
//
// This is the validator that answers "is anything floating" without a VLM
// (02:T4). It reads every SOLVED instance, so a `repeat` that walks a chimney
// off the roof is caught here even though V2 saw only the anchor.
//
// DEFERRED: manifold-3d cross-check (union -> split() component count == 1).
// PLAN.md 2 keeps it flagged until M1 fixtures can promote it; the advisory
// below is the flag.
import { partBox, boxGap } from "./obb.js";

export function validateV3(ctx, make) {
  const { parts, EPS } = ctx;
  const violations = [];
  const advisories = [make("V3", null, "not run", "manifold-3d union split() == 1",
    "cross-check against a real boolean union is deferred; V3 is box-contact only")];

  const boxes = parts.map(partBox);
  const parent = parts.map((_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  const union = (a, b) => { const ra = find(a); const rb = find(b); if (ra !== rb) parent[ra] = rb; };

  for (let i = 0; i < parts.length; i += 1) {
    for (let j = i + 1; j < parts.length; j += 1) {
      if (!aabbNear(parts[i], parts[j], EPS)) continue;           // prefilter
      if (boxGap(boxes[i], boxes[j]) <= EPS) union(i, j);
    }
  }

  const clusters = new Map();
  for (let i = 0; i < parts.length; i += 1) {
    const root = find(i);
    if (!clusters.has(root)) clusters.set(root, []);
    clusters.get(root).push(i);
  }

  const rooted = new Set();
  for (const [root, members] of clusters) {
    if (members.some((i) => parts[i].contact === "ground")) rooted.add(root);
  }

  for (const [root, members] of clusters) {
    if (rooted.has(root)) continue;
    const { gap, near, from } = nearestRooted(members, boxes, parts, rooted, find);
    const names = members.map((i) => parts[i].id);
    const what = members.length === 1
      ? `orphan "${names[0]}"`
      : `orphan cluster of ${members.length} (${names.slice(0, 3).join(", ")}${names.length > 3 ? ", …" : ""})`;
    const violation = make("V3", names[0], `gap ${fmt(gap)} m to "${near}"`, `<= ${fmt(EPS)} m`,
      `${what} never reaches a ground part — attach ${from} to ${near}, ${fmt(gap)} m away`);
    violation.overlayIds = names;   // the studio overlay tints every member red
    violations.push(violation);
  }

  if (violations.length === 0 && clusters.size > 1) {
    violations.push(make("V3", null, `${clusters.size} components`, "1 connected component",
      `the contact graph splits into ${clusters.size} pieces; every part must touch the same solid`));
  }

  return { violations, advisories };
}

function aabbNear(a, b, eps) {
  for (let i = 0; i < 3; i += 1) {
    if (a.aabb.min[i] - eps > b.aabb.max[i] || b.aabb.min[i] - eps > a.aabb.max[i]) return false;
  }
  return true;
}

/** Closest part outside the cluster, with the gap, so the hint names a move. */
function nearestRooted(members, boxes, parts, rooted, find) {
  const inside = new Set(members);
  let gap = Infinity;
  let near = "(nothing)";
  let from = parts[members[0]].id;
  for (const i of members) {
    for (let j = 0; j < parts.length; j += 1) {
      if (inside.has(j)) continue;
      if (!rooted.has(find(j))) continue;
      const d = boxGap(boxes[i], boxes[j]);
      if (d < gap) { gap = d; near = parts[j].id; from = parts[i].id; }
    }
  }
  return { gap: Number.isFinite(gap) ? Math.max(gap, 0) : 0, near, from };
}

function fmt(value) {
  return (Math.round(value * 1000) / 1000).toFixed(3);
}
