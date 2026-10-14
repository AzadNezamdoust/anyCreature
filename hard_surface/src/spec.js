// Spec-level helpers shared by node (tests, bench) and the browser (capture).
//
// Nothing here may reach for fs, fetch, crypto or the DOM: both runtimes import
// this file and both must agree bit for bit.
import { hash32 } from "./geom.js";

export const DSL_VERSION = "pg/1";

/** Canonical JSON: keys sorted at every depth, no whitespace. */
export function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(",")}}`;
}

/**
 * Stable identity of a spec, for the capture manifest and the spec cache.
 * MVP-STUB: FNV-1a 32 bits (`geom.js:45`), not sha256 — SubtleCrypto is async
 * and node:crypto is not importable in the capture page, and a 32-bit tag is
 * enough to tell two hand-authored M0 specs apart. Widen at M3 when the cache
 * keys real generations.
 */
export function specHash(spec) {
  return `h32:${hash32(canonicalJson(spec)).toString(16).padStart(8, "0")}`;
}
