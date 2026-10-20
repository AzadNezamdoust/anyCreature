// The `--runner fake` module: {seat, tier, attempt} -> canned response.
//
// It stands in for five real seat calls with no API key and no login. The canned tiers are a
// partition of the hand BASELINE (`subjects/tenement_block/spec.json`, read-only here):
//
//   A  the six massing parts (3 masses + 3 parapets)
//   B  four of the seven facades, plus `balcony_2` as the occluder the grammar must see —
//      DELIBERATELY BROKEN on the first call with `repeat {axis:"+Y", count:2, pitch:18}`,
//      which walks `balcony_2#1` 12.2 m off the building: a V3 orphan, which auto-repair is
//      forbidden to touch (a logic error must reach the ledger, 02:T3) so it reaches REPAIR.
//   C  the remaining 33 attached props and composites.
//
// The REPAIR seat returns the same fragment with the runaway `repeat` removed.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const BASELINE = JSON.parse(fs.readFileSync(path.join(ROOT, "subjects/tenement_block/spec.json"), "utf8"));

const TIER_A_COUNT = 6;
const TIER_B_FACADES = new Set(["fac_l_front", "fac_m_shop", "fac_m_upper", "fac_r_upper"]);
const OCCLUDER = "balcony_2";

const clone = (value) => JSON.parse(JSON.stringify(value));
const fence = (value) => `Here is the fragment.\n\n\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\`\n`;

const fragmentA = () => ({
  class: BASELINE.class,
  unit: clone(BASELINE.unit),
  palette: clone(BASELINE.palette),
  parts: clone(BASELINE.parts.slice(0, TIER_A_COUNT)),
  facades: [],
});

function fragmentB({ broken }) {
  const balcony = clone(BASELINE.parts.find((p) => p.id === OCCLUDER));
  if (broken) balcony.repeat = { axis: "+Y", count: 2, pitch: 18 };
  return { parts: [balcony], facades: clone(BASELINE.facades.filter((f) => TIER_B_FACADES.has(f.id))) };
}

const fragmentC = () => ({
  parts: clone(BASELINE.parts.slice(TIER_A_COUNT).filter((p) => p.id !== OCCLUDER)),
  facades: [],
});

const LISTER = {
  parts: [
    { name: "mass_left", parent: "root", attach_face: "+y", rel_size: 1.0, count_uncertain: false },
    { name: "mass_middle", parent: "mass_left", attach_face: "+x", rel_size: 1.0, count_uncertain: false },
    { name: "mass_right", parent: "mass_middle", attach_face: "+x", rel_size: 1.0, count_uncertain: false },
    { name: "parapet_left", parent: "mass_left", attach_face: "+y", rel_size: 0.6, count_uncertain: false },
    { name: "stoop_stairs", parent: "mass_left", attach_face: "+z", rel_size: 0.18, count_uncertain: false },
    { name: "door_front", parent: "mass_left", attach_face: "+z", rel_size: 0.2, count_uncertain: false },
    { name: "fire_escape", parent: "mass_middle", attach_face: "+z", rel_size: 0.55, count_uncertain: true },
    { name: "awning", parent: "mass_middle", attach_face: "+z", rel_size: 0.3, count_uncertain: false },
    { name: "balcony_2", parent: "mass_right", attach_face: "+z", rel_size: 0.22, count_uncertain: false },
    { name: "balcony_3", parent: "mass_right", attach_face: "+z", rel_size: 0.22, count_uncertain: false },
    { name: "trashcan", parent: "mass_right", attach_face: "+z", rel_size: 0.09, count_uncertain: false },
    { name: "crates", parent: "mass_right", attach_face: "+z", rel_size: 0.08, count_uncertain: true },
    { name: "clothesline", parent: "mass_middle", attach_face: "+z", rel_size: 0.5, count_uncertain: true },
  ],
  unit: { name: "door_front", unit_m: 2.0 },
};

/** Every call this module served, in order. The test asserts a cache hit adds none. */
export const calls = [];

export default function fakeRunner({ seat, tier, attempt }) {
  calls.push({ seat, tier, attempt });

  let payload;
  if (seat === "lister") payload = LISTER;
  else if (seat === "builder-a") payload = fragmentA();
  else if (seat === "builder-b") payload = fragmentB({ broken: true });
  else if (seat === "builder-c") payload = fragmentC();
  else if (seat === "repair" && tier === "B") payload = fragmentB({ broken: false });
  else throw new Error(`fake-runner: no canned response for seat "${seat}" tier "${tier}" attempt ${attempt}`);

  const text = seat === "lister" ? fence(payload) : JSON.stringify(payload);
  return { text, tokensIn: 4000, tokensOut: Math.ceil(text.length / 4), ms: 1 };
}
