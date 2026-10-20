// The validator chain — V0, V1, V2, V3, V4, V5, V6, V7, V10, V9, in that order.
// V9 runs last because it is advisory-only (PLAN 2) and there is nothing to say
// about a model's symmetry until it is a model at all.
//
// Contract (PLAN.md 1.3, 2):
//   report = {pass, violations:[{v, part, measured, limit, hint, blocking}],
//             advisories:[…], text}
// `text` is <= 8 lines and every hint states the MOVE IN METRES, because that
// text is the only thing the REPAIR seat is ever shown. Zero LLM tokens.
//
// The chain stops at the first validator that produces a BLOCKING violation —
// there is no point measuring a stability hull for a model whose parts are not
// where the program says they are — but advisories from the validators that did
// run are always kept.
import { compile, solve } from "../compile/build.js";
import { buildPrim, PRIM_GENUS, PRIM_OPTIONS } from "../prims.js";
import { validateV0 } from "./v0.js";
import { validateV1 } from "./v1.js";
import { validateV2 } from "./v2.js";
import { validateV3 } from "./v3.js";
import { validateV4 } from "./v4.js";
import { validateV5 } from "./v5.js";
import { validateV6 } from "./v6.js";
import { validateV7 } from "./v7.js";
import { validateV9 } from "./v9.js";
import { validateV10 } from "./v10.js";
import DEFAULT_LIMITS from "./limits.json" with { type: "json" };

export { DEFAULT_LIMITS };

const make = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: true });
const advise = (v, part, measured, limit, hint) => ({ v, part, measured, limit, hint, blocking: false });

/**
 * Per-prim geometry for V1, deduplicated by prim + dims + bevel. Built here and
 * not in compile() because V1 reads the prim BEFORE the world matrix, which is
 * the only frame in which "watertight" is a property of the prim library.
 */
export function buildPrims(spec) {
  const seen = new Set();
  const prims = [];
  for (const part of spec.parts ?? []) {
    if (!PRIM_GENUS[part.prim] && PRIM_GENUS[part.prim] !== 0) continue;
    if (!Array.isArray(part.dims) || part.dims.length !== 3) continue;
    const key = `${part.prim}|${part.dims.join(",")}|${PRIM_OPTIONS.map((o) => part[o] ?? "").join("|")}|${part.debugGeometry ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);

    let geometry = buildPrim(part.prim, part.dims, part);
    // MVP-STUB: test-only geometry break. V1 otherwise only ever fires on a
    // compiler bug, so `test/fixtures/broken/v1-*.json` has no other way to
    // exist. Never set `debugGeometry` in a real spec; nothing else reads it.
    if (part.debugGeometry === "open") geometry = dropLastTriangle(geometry);
    prims.push({ specId: part.id, prim: part.prim, genus: PRIM_GENUS[part.prim] ?? 0, geometry });
  }
  return prims;
}

function dropLastTriangle(geometry) {
  const position = geometry.getAttribute("position");
  const kept = position.array.slice(0, position.array.length - 9);
  const clone = geometry.clone();
  clone.setAttribute("position", new position.constructor(kept, 3));
  return clone;
}

/** specId -> every specId above it in the attach chain. */
function ancestorMap(spec) {
  const direct = new Map();
  for (const part of spec.parts ?? []) direct.set(part.id, part.attach?.to ?? null);
  const ancestors = new Map();
  for (const id of direct.keys()) {
    const set = new Set();
    let cursor = direct.get(id);
    while (cursor && !set.has(cursor)) { set.add(cursor); cursor = direct.get(cursor); }
    ancestors.set(id, set);
  }
  return ancestors;
}

/**
 * @param {object} spec pg/1 spec
 * @param {object} solved compile().solved
 * @param {{geometry:object, prims?:Array}} geometryInfo compile().geometry + optional prim list
 * @param {object} [limits] limits.json
 */
export function validate(spec, solved, geometryInfo, limits = DEFAULT_LIMITS) {
  const violations = [];
  const advisories = [];

  const v0 = validateV0(spec);
  if (!v0.pass) {
    for (const item of v0.violations) violations.push({ ...item, blocking: true });
    return finish(violations, advisories);
  }

  const bounds = solved.bounds;
  const diagonal = Math.hypot(bounds.w, bounds.h, bounds.d);
  const EPS = Math.max(limits.epsAbs, limits.epsRel * diagonal);
  const PX = (bounds.h / limits.fill) / limits.captureSize;
  const cls = Object.hasOwn(limits.triBudget, spec.class ?? "") ? spec.class : "prop";
  const MIN_FEAT = Math.max(limits.styleFloor[cls] ?? limits.styleFloor.prop, limits.minFeaturePx * PX);

  const byId = new Map();
  for (const part of solved.parts) if (!byId.has(part.specId)) byId.set(part.specId, part);

  const ctx = {
    spec,
    solved,
    geometryInfo,
    limits,
    parts: solved.parts,
    byId,
    ancestors: ancestorMap(spec),
    cls,
    EPS,
    PX,
    MIN_FEAT,
    diagonal,
  };

  const prims = geometryInfo.prims ?? buildPrims(spec);
  const chain = [
    () => validateV1(prims, make),
    () => validateV2(ctx, make),
    () => validateV3(ctx, adviseOrMake),
    () => validateV4(ctx, make),
    () => validateV5(ctx, make),
    () => validateV6(ctx, make),
    () => validateV7(ctx, make),
    () => validateV10(ctx, make),
    () => validateV9(ctx, advise),
  ];

  let measurements = new Map();
  for (const step of chain) {
    const result = step();
    if (result.measurements) measurements = result.measurements;
    for (const item of result.advisories ?? []) advisories.push(item);
    if (result.violations.length > 0) {
      for (const item of result.violations) violations.push(item);
      break;
    }
  }

  const report = finish(violations, advisories);
  report.measurements = measurements;
  report.context = { EPS, PX, MIN_FEAT, cls, diagonal };
  return report;
}

// V3 hands its deferred manifold cross-check through the same factory it uses
// for violations; only that one line is non-blocking.
function adviseOrMake(v, part, measured, limit, hint) {
  return measured === "not run" ? advise(v, part, measured, limit, hint) : make(v, part, measured, limit, hint);
}

function finish(violations, advisories) {
  const blocking = violations.filter((x) => x.blocking !== false);
  return {
    pass: blocking.length === 0,
    violations: blocking,
    advisories: [...advisories, ...violations.filter((x) => x.blocking === false)],
    text: reportText(blocking),
  };
}

/** <= 8 lines. The REPAIR seat sees this and nothing else. */
export function reportText(violations) {
  if (violations.length === 0) return "PASS: V0-V7 + V10 clean.";
  const codes = [...new Set(violations.map((x) => x.v))].join(", ");
  const lines = [`FAIL: ${violations.length} violation(s) [${codes}].`];
  for (const item of violations.slice(0, 7)) {
    lines.push(`- ${item.v}${item.part ? ` ${item.part}` : ""}: ${item.hint} (measured ${item.measured}, limit ${item.limit})`);
  }
  if (violations.length > 7) lines[7] = `- … and ${violations.length - 6} more of the same class.`;
  return lines.join("\n");
}

/** Compile, then validate. The entry point for scripts, tests and repair. */
export function validateSpec(spec, limits = DEFAULT_LIMITS) {
  const v0 = validateV0(spec);
  if (!v0.pass) {
    const violations = v0.violations.map((item) => ({ ...item, blocking: true }));
    const report = finish(violations, []);
    report.measurements = new Map();
    return report;
  }
  // Everything after the schema check measures the EFFECTIVE spec — composites
  // expanded, facade parts derived — because that is what the compiler built
  // and what the capture will show. V0 above already read the file as written.
  const { solved, geometry, spec: effective } = compile(spec);
  return validate(effective, solved, { geometry, prims: buildPrims(effective) }, limits);
}

export { solve };
