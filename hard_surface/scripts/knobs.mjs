// WORKFLOW v4 — V4-2: the KNOBS block every template emits (research/WF-V4-PLAN.md S1 START).
//
//   export const KNOBS = {
//     name: { v: <metres>, min, max, key: "<layout key>"?, unit: "m", locked: "<why>"? },   // comment
//   };
//
// One knob per continuous size / position; geometry reads ONLY KNOBS. keyedKnob: a knob with a `key` takes its range
// from that layout key's V12 tolerance (value +/- tol, in metres) — buildings; startKnob (V5-9, vehicles): the key is
// the START only, the range is the class prior; every other knob takes a class prior range (classes/<c>.json
// knobPriors). `locked` knobs (edges the solved camera cannot see, or the registration anchor) are never fitted.
// scripts/fit.mjs rewrites only the `v:` numbers inside this block.

const r4 = (v) => Math.round(v * 1e4) / 1e4;
export const knobNum = (v) => String(r4(v));

/**
 * A knob from a layout key: range = value +/- tol, both converted to metres by `toM` (a key in H over the H the
 * template builds, ...). The start value is widened into the range if the template placed it outside.
 */
export function keyedKnob({ v, key, entry, toM, unit = "m", min = -Infinity, max = Infinity }) {
  const tol = Number.isFinite(entry?.tol) ? entry.tol : 0.05;
  const centre = Array.isArray(entry?.values) ? null : entry?.value;
  const base = Number.isFinite(centre) ? toM(centre) : v;
  const half = Math.abs(toM(tol) - toM(0));
  return clampKnob({ v, min: Math.max(min, Math.min(base - half, v)), max: Math.min(max, Math.max(base + half, v)), key, unit });
}

/** A knob from a class prior: {span, of: "L"|"W"|"H"|"m"} (v +/- span x size), or explicit {min, max}; {locked}. */
export function priorKnob({ v, prior, sizes, unit = "m", min = -Infinity, max = Infinity }) {
  if (!prior) throw new Error("knob has neither a layout key nor a class knobPrior (classes/<c>.json knobPriors)");
  if (prior.locked) return { v: r4(v), min: r4(v), max: r4(v), unit, locked: prior.locked };
  let lo = prior.min;
  let hi = prior.max;
  if (Number.isFinite(prior.span)) {
    const size = prior.of === "m" || !prior.of ? 1 : sizes[prior.of];
    lo = v - prior.span * size;
    hi = v + prior.span * size;
  }
  return clampKnob({ v, min: Math.max(min, Math.min(lo, v)), max: Math.min(max, Math.max(hi, v)), unit });
}

/**
 * V5-9 EVIDENCE HIERARCHY (orchestrator ruling): a knob whose START comes from a layout key takes its RANGE from the
 * class prior (plausibility), never from the key's V12 tolerance — the per-feature accuracy measurement (full res,
 * per item) outranks the older, lower-resolution layout keys, so FIT must be able to leave the key's band. The key is
 * kept on the knob as its provenance. `prior` = classes/<c>.json knobPriors[name] ?? knobPriors._keyed.
 */
export function startKnob({ v, key, prior, sizes, unit = "m", min = -Infinity, max = Infinity }) {
  const k = priorKnob({ v, prior, sizes, unit, min, max });
  return k.locked ? k : { ...k, ...(key ? { key } : {}), unit: k.unit };
}

function clampKnob(k) {
  return { v: r4(k.v), min: r4(Math.min(k.min, k.v)), max: r4(Math.max(k.max, k.v)), ...(k.key ? { key: k.key } : {}), unit: k.unit };
}

/** The KNOBS block text: one line per knob, `// comment` after it. */
export function knobsBlock(knobs, comments = {}) {
  const width = Math.max(...Object.keys(knobs).map((n) => n.length));
  const lines = ["export const KNOBS = {"];
  for (const [name, k] of Object.entries(knobs)) {
    const fields = [`v: ${knobNum(k.v)}`, `min: ${knobNum(k.min)}`, `max: ${knobNum(k.max)}`];
    if (k.key) fields.push(`key: "${k.key}"`);
    fields.push(`unit: "${k.unit}"`);
    if (k.locked) fields.push(`locked: "${k.locked}"`);
    const c = comments[name] ? `   // ${comments[name]}` : "";
    lines.push(`  ${`${name}:`.padEnd(width + 1)} { ${fields.join(", ")} },${c}`);
  }
  lines.push("};");
  return lines.join("\n");
}

/** Replace the `v:` of each named knob inside the module's KNOBS block; nothing outside the block changes. */
export function replaceKnobValues(text, values) {
  const start = text.indexOf("export const KNOBS = {");
  if (start < 0) throw new Error("module has no `export const KNOBS = {` block");
  const end = text.indexOf("\n};", start);
  if (end < 0) throw new Error("KNOBS block is not closed by a `};` line");
  let block = text.slice(start, end);
  for (const [name, v] of Object.entries(values)) {
    const re = new RegExp(`(\\n\\s*${name}:\\s*\\{\\s*v:\\s*)(-?[\\d.]+(?:e-?\\d+)?)`);
    if (!re.test(block)) throw new Error(`KNOBS block has no knob "${name}"`);
    block = block.replace(re, `$1${knobNum(v)}`);
  }
  return text.slice(0, start) + block + text.slice(end);
}
