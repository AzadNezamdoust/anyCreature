// V1 — per-prim manifold: watertight, consistently wound, chi == 2 - 2*genus.
//
// A V1 failure is a COMPILER bug, never the author's: the LLM cannot write a
// vertex. PLAN.md 2 says the round aborts rather than repairs.
const QUANT = 1e6;   // 1e-6 m, i.e. a micrometre — far below any authored dim.

function key(position, i) {
  const x = Math.round(position.getX(i) * QUANT);
  const y = Math.round(position.getY(i) * QUANT);
  const z = Math.round(position.getZ(i) * QUANT);
  return `${x},${y},${z}`;
}

/**
 * @param {Array<{specId:string, prim:string, genus:number, geometry:object}>} prims
 * @param {(v:object)=>object} make violation factory from index.js
 */
export function validateV1(prims, make) {
  const violations = [];

  for (const entry of prims) {
    const position = entry.geometry.getAttribute("position");
    const triangles = position.count / 3;

    if (!Number.isInteger(triangles)) {
      violations.push(make("V1", entry.specId, `${position.count} vertices`, "multiple of 3",
        `prim "${entry.prim}" emitted ${position.count} vertices — not whole triangles (compiler bug)`));
      continue;
    }
    if (triangles % 2 !== 0) {
      violations.push(make("V1", entry.specId, `${triangles} triangles`, "even",
        `prim "${entry.prim}" has an odd triangle count (${triangles}) — a quad is unpaired (compiler bug)`));
    }

    const vertices = new Map();
    const ids = new Array(position.count);
    for (let i = 0; i < position.count; i += 1) {
      const k = key(position, i);
      if (!vertices.has(k)) vertices.set(k, vertices.size);
      ids[i] = vertices.get(k);
    }

    // Directed edges. A closed, consistently wound surface uses each undirected
    // edge exactly twice, once in each direction.
    const edges = new Map();
    let degenerate = 0;
    for (let t = 0; t < triangles; t += 1) {
      const a = ids[t * 3];
      const b = ids[t * 3 + 1];
      const c = ids[t * 3 + 2];
      if (a === b || b === c || c === a) { degenerate += 1; continue; }
      for (const [from, to] of [[a, b], [b, c], [c, a]]) {
        const k = from < to ? `${from}:${to}` : `${to}:${from}`;
        const slot = edges.get(k) ?? { fwd: 0, bwd: 0 };
        if (from < to) slot.fwd += 1; else slot.bwd += 1;
        edges.set(k, slot);
      }
    }

    let open = 0;
    let flipped = 0;
    for (const slot of edges.values()) {
      if (slot.fwd + slot.bwd !== 2) open += 1;
      else if (slot.fwd !== 1 || slot.bwd !== 1) flipped += 1;
    }

    if (degenerate > 0) {
      violations.push(make("V1", entry.specId, `${degenerate} degenerate triangles`, "0",
        `prim "${entry.prim}" emitted ${degenerate} zero-area triangles (compiler bug)`));
    }
    if (open > 0) {
      violations.push(make("V1", entry.specId, `${open} unpaired edges`, "0",
        `prim "${entry.prim}" is not watertight: ${open} edge(s) are not shared by exactly 2 triangles (compiler bug)`));
    }
    if (flipped > 0) {
      violations.push(make("V1", entry.specId, `${flipped} same-direction edges`, "0",
        `prim "${entry.prim}" has inconsistent winding on ${flipped} edge(s) (compiler bug)`));
    }

    const V = vertices.size;
    const E = edges.size;
    const F = triangles - degenerate;
    const chi = V - E + F;
    const expected = 2 - 2 * entry.genus;
    if (open === 0 && flipped === 0 && degenerate === 0 && chi !== expected) {
      violations.push(make("V1", entry.specId, `chi = ${chi}`, `${expected} (genus ${entry.genus})`,
        `prim "${entry.prim}" has Euler characteristic ${chi}, not ${expected} for declared genus ${entry.genus} (compiler bug)`));
    }
  }

  return { violations, advisories: [] };
}
