// WF-R3 H4 test shim — the frozen blind P2 modules call K.assemble.landing({ gateFor }) with a flight that never
// arrives on the deck, which the kernel now REFUSES. To measure the archived GEOMETRY with the new rows, the test swaps
// that call for this one: the same gates the archived kernel cut (gateSpans of every ladder / stringer head in
// gateFor, passed as declared gateAt with the slack the declaration adds taken back off).
export const SHIM = `
function landingAsArchived(o) {
  const { gateFor, ...rest } = o;
  if (!gateFor || gateFor.length === 0) return K.assemble.landing(rest);
  const bars = K.assemble.landing(rest).filter((p) => p.role === "landing").map((p) => p.solid.aabb());
  const box = { min: [0, 1, 2].map((i) => Math.min(...bars.map((b) => b.min[i]))), max: [0, 1, 2].map((i) => Math.max(...bars.map((b) => b.max[i]))) };
  const heads = gateFor.filter((p) => p.role === "ladder" || p.role === "stringer").map((p) => p.solid);
  const { spans } = K.assemble.gateSpans({ box, heads, reach: 0.15, slack: 0.3, headBand: 1.1 });
  return K.assemble.landing({ ...rest, gateAt: spans.front.map(([a, b]) => [a + 0.3, b - 0.3]) });
}
`;
/** The archived module text with its landing calls re-pointed at the shim (inserted after the kernel import). */
export const archived = (text) => text.replace(/K\.assemble\.landing\(/g, "landingAsArchived(")
  .replace(/(import \* as K from "[^"]+";\r?\n)/, (m) => m + SHIM);
