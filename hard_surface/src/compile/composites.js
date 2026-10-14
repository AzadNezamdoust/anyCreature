// Composite prims — expansion of `src/parts/lib/*.json` spec fragments into
// ordinary parts (PLAN 1.1, 08:A2).
//
// A composite is NOT a new kind of geometry. It is a versioned spec fragment
// authored once by a human, parameterised by `$w/$h/$d` (the composite part's
// own dims) plus its own named params. Expansion happens BEFORE the attach
// solver runs, so every validator downstream sees ordinary parts and nothing in
// the compiler has to learn what a railing is.
//
// Rules, all enforced here and mirrored in `dsl/SPEC.md`:
//   * sub-part ids are `<compositeId>.<subId>`;
//   * `parts[0]` is the ROOT: it carries the composite part's `attach` (or its
//     `ground: true`), plus any `repeat`/`mirror` the author put on it;
//   * every other sub-part attaches to an EARLIER sub-part by its bare sub id,
//     which is rewritten to the qualified id, so the DAG-in-file-order rule that
//     V0 enforces still holds after expansion;
//   * a sub-part inherits the composite's `zone` unless it names a `zoneKey`,
//     which the author fills in through the composite part's `zones` map;
//   * a composite may itself use a composite (landing -> railing); expansion
//     recurses, capped at MAX_DEPTH so a malformed library cannot spin.
import { isComposite, loadComposite, COMPOSITE_SCHEMA } from "../prims.js";

const MAX_DEPTH = 4;

/** Fields copied verbatim from a library sub-part onto the emitted part. */
// `prim`, `role` and `axis` are copied VERBATIM; every other entry is a number
// or an expression in the composite's params.
const PASSTHROUGH = ["prim", "role", "bevel", "sides", "steps", "wall", "axis"];
const VERBATIM = new Set(["prim", "role", "axis"]);

// ---------------------------------------------------------------------------
// The tiny expression evaluator.
//
// Grammar: expr = term (('+'|'-') term)* ; term = unary (('*'|'/') unary)* ;
// unary = '-'? atom ; atom = number | '$' ident | '(' expr ')'.
// No function calls, no comparison, no property access — a library file cannot
// reach anything but its own params.
// ---------------------------------------------------------------------------

const TOKEN = /\s*(\d+\.?\d*|\$[A-Za-z_][A-Za-z0-9_]*|[-+*/()])/y;

function tokenize(source) {
  const tokens = [];
  let index = 0;
  while (index < source.length) {
    TOKEN.lastIndex = index;
    const match = TOKEN.exec(source);
    if (!match) throw new Error(`cannot parse "${source}" at offset ${index}`);
    tokens.push(match[1]);
    index = TOKEN.lastIndex;
  }
  return tokens;
}

/**
 * Evaluate one expression string against a params object.
 * @param {string} source e.g. "$h - 2 * $railThickness"
 * @param {Record<string, number>} params
 */
export function evaluateExpression(source, params) {
  const tokens = tokenize(source);
  let at = 0;
  const peek = () => tokens[at];
  const take = () => tokens[at++];

  const atom = () => {
    const token = take();
    if (token === undefined) throw new Error(`unexpected end of "${source}"`);
    if (token === "(") {
      const value = expr();
      if (take() !== ")") throw new Error(`unbalanced "(" in "${source}"`);
      return value;
    }
    if (token === "-") return -atom();
    if (token.startsWith("$")) {
      const name = token.slice(1);
      if (!Object.hasOwn(params, name)) throw new Error(`unknown param "$${name}" in "${source}"`);
      const value = Number(params[name]);
      if (!Number.isFinite(value)) throw new Error(`param "$${name}" is not a finite number`);
      return value;
    }
    const value = Number(token);
    if (!Number.isFinite(value)) throw new Error(`"${token}" is not a number in "${source}"`);
    return value;
  };

  const term = () => {
    let value = atom();
    while (peek() === "*" || peek() === "/") {
      const op = take();
      const rhs = atom();
      value = op === "*" ? value * rhs : value / rhs;
    }
    return value;
  };

  function expr() {
    let value = term();
    while (peek() === "+" || peek() === "-") {
      const op = take();
      const rhs = term();
      value = op === "+" ? value + rhs : value - rhs;
    }
    return value;
  }

  const result = expr();
  if (at !== tokens.length) throw new Error(`trailing "${tokens.slice(at).join(" ")}" in "${source}"`);
  if (!Number.isFinite(result)) throw new Error(`"${source}" evaluated to ${result}`);
  return result;
}

/** Numbers pass through; strings are expressions; arrays map elementwise. */
function resolveValue(value, params) {
  if (typeof value === "number") return value;
  if (typeof value === "string") return evaluateExpression(value, params);
  if (Array.isArray(value)) return value.map((entry) => resolveValue(entry, params));
  throw new Error(`cannot resolve ${JSON.stringify(value)} to a number`);
}

// ---------------------------------------------------------------------------
// Expansion
// ---------------------------------------------------------------------------

/** Params for one composite instance: library defaults <- author overrides. */
export function compositeParams(part, fragment) {
  const params = { ...(fragment.params ?? {}) };
  for (const [key, value] of Object.entries(part.params ?? {})) params[key] = value;
  const dims = Array.isArray(part.dims) ? part.dims : [1, 1, 1];
  params.w = Number(dims[0]);
  params.h = Number(dims[1]);
  params.d = Number(dims[2]);
  if (Array.isArray(fragment.dims)) {
    const derived = fragment.dims.map((entry) => resolveValue(entry, params));
    [params.w, params.h, params.d] = derived;
  }
  return params;
}

/** The dims a composite part actually occupies, after any library override. */
export function compositeDims(part) {
  const fragment = loadComposite(part.prim);
  if (!fragment) return part.dims;
  const params = compositeParams(part, fragment);
  return [params.w, params.h, params.d];
}

function expandOne(part, depth, roots) {
  const fragment = loadComposite(part.prim);
  if (!fragment) throw new Error(`expandComposites: "${part.prim}" is not a composite`);
  if (fragment.schema !== COMPOSITE_SCHEMA) {
    throw new Error(`composite "${part.prim}" has schema "${fragment.schema}", expected "${COMPOSITE_SCHEMA}"`);
  }
  if (depth > MAX_DEPTH) throw new Error(`composite "${part.prim}" nests deeper than ${MAX_DEPTH}`);

  const params = compositeParams(part, fragment);
  const zones = part.zones ?? {};
  const out = [];

  fragment.parts.forEach((sub, index) => {
    const id = `${part.id}.${sub.id}`;
    const emitted = { id, dims: resolveValue(sub.dims, params) };
    for (const key of PASSTHROUGH) {
      if (sub[key] === undefined) continue;
      emitted[key] = VERBATIM.has(key) ? sub[key] : resolveValue(sub[key], params);
    }
    emitted.zone = sub.zoneKey ? (zones[sub.zoneKey] ?? part.zone) : part.zone;

    // A nested composite (landing -> railing) gets its own params resolved here
    // and inherits the outer `zones` map so a deep zoneKey still resolves.
    if (isComposite(sub.prim)) {
      emitted.zones = zones;
      if (sub.params) {
        emitted.params = {};
        for (const [key, value] of Object.entries(sub.params)) emitted.params[key] = resolveValue(value, params);
      }
    }

    if (index === 0) {
      // The root inherits the composite's own placement verbatim.
      if (part.ground === true) emitted.ground = true;
      if (part.attach) emitted.attach = { ...part.attach };
      if (part.repeat) emitted.repeat = { ...part.repeat };
      if (part.mirror !== undefined) emitted.mirror = part.mirror;
    } else {
      if (!sub.attach) throw new Error(`composite "${part.prim}" sub-part "${sub.id}" needs an attach`);
      emitted.attach = {
        ...sub.attach,
        to: `${part.id}.${sub.attach.to}`,
        ...(sub.attach.uv === undefined ? {} : { uv: resolveValue(sub.attach.uv, params) }),
        ...(sub.attach.embed === undefined ? {} : { embed: resolveValue(sub.attach.embed, params) }),
        ...(sub.attach.rot === undefined ? {} : { rot: resolveValue(sub.attach.rot, params) }),
      };
      if (sub.repeat) {
        emitted.repeat = {
          axis: sub.repeat.axis,
          count: Math.round(resolveValue(sub.repeat.count, params)),
          pitch: resolveValue(sub.repeat.pitch, params),
        };
      }
      if (sub.mirror !== undefined) emitted.mirror = sub.mirror;
    }

    out.push(emitted);
  });

  // Recurse: a landing's railings are composites in their own right.
  const flat = [];
  for (const emitted of out) {
    if (isComposite(emitted.prim)) flat.push(...expandOne(emitted, depth + 1, roots));
    else flat.push(emitted);
  }
  // M6 gap 1: the composite id itself survives expansion as a NAME. `flat[0]`
  // is the transitive root (out[0] is the root sub-part, and if that is itself
  // a composite its own root is the first thing its expansion emits), so
  // `attach.to: "<compositeId>"` can be rewritten to an ordinary part below.
  if (flat.length > 0) roots.set(part.id, flat[0].id);
  return flat;
}

/**
 * Sub-part ids a composite prim declares, in library order. `parts[0]` is its
 * root. Used by V0 to check an `attach.to` of the form `composite.sub` BEFORE
 * expansion has happened.
 * @param {string} prim a composite name
 * @returns {string[]}
 */
export function compositeSubIds(prim) {
  const fragment = loadComposite(prim);
  if (!fragment) return [];
  return fragment.parts.map((sub) => sub.id);
}

/**
 * Does `path` ("deck", or "rail_front.bot" for a nested composite) name a
 * sub-part of `prim`? Recurses through nested composites, capped like expansion.
 * @param {string} prim
 * @param {string} path dot-separated sub ids
 */
export function hasCompositeSub(prim, path, depth = 1) {
  if (depth > MAX_DEPTH) return false;
  const fragment = loadComposite(prim);
  if (!fragment) return false;
  const [head, ...rest] = String(path).split(".");
  const sub = fragment.parts.find((entry) => entry.id === head);
  if (!sub) return false;
  if (rest.length === 0) return true;
  return isComposite(sub.prim) && hasCompositeSub(sub.prim, rest.join("."), depth + 1);
}

/**
 * Expand every composite in a part list, in place in the list order.
 * @param {Array<object>} parts
 * @returns {{parts:Array<object>, composites:Array<object>}} `composites` keeps
 *   the authored composite parts (id, prim, role, dims, zone, attach) so V7 can
 *   still apply its role table to "the railing", which after expansion is four
 *   sub-parts none of which is 0.95 m tall.
 */
export function expandParts(parts, roots = new Map()) {
  const out = [];
  const composites = [];
  for (const part of parts ?? []) {
    if (!isComposite(part.prim)) { out.push(part); continue; }
    composites.push({ ...part, dims: compositeDims(part) });
    out.push(...expandOne(part, 1, roots));
  }
  // M6 gap 1: every reference to a composite id — the author's, and the one a
  // nested library fragment wrote — becomes a reference to that composite's
  // root sub-part, so `solve()` and V2/V3/V6 downstream only ever see ordinary
  // parts. `roots` is threaded in by the caller so the facade-derived pass can
  // still name a composite the authored pass expanded.
  const rewritten = out.map((part) => {
    const to = part.attach ? roots.get(part.attach.to) : undefined;
    return to === undefined ? part : { ...part, attach: { ...part.attach, to } };
  });
  return { parts: rewritten, composites, roots };
}
