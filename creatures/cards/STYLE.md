# STYLE — the art direction every creature is modelled to

The target is a **stylised game asset**: clean, readable, chunky shapes;
appealing stylisation; slightly larger heads; confident simple forms; a strong
big-medium-small shape language; an expressive face; nothing uncanny. It is the
standard the owner chose after the realistic-proportion builds "looked very
weird" (a bird on stilts with a rod tail and a thin S-neck, a sad face, a T-pose
from behind). Apply it while you design (card 01 §3), not as a repair.

Numbers here are starting points taken from the shipped gallery, not gates. The
engine does not check them; the reader and the owner do.

## 1. Big – medium – small

Every creature is ONE big mass, one or two medium masses, and small detail.

- **Big**: the torso. Compact and deep, never long and thin. Length : depth
  about 1.5 : 1 for a biped, 2 : 1 for a quadruped. Give it a profile (a chest
  that swells, a waist), and a section that is not a circle: a keel (`taper`
  0.3-0.45 on the chest rows, the section wider at the shoulders than at the
  breastbone), a belly (`bias` -0.15 to -0.2).
- **Medium**: the head, and one signature (fists, wings, a mane). The head is
  the medium mass people look at first — size it UP.
- **Small**: digits, claws, brows, crest blades, tufts. Few and bold. Small
  things that are under 3 px on the 48 px thumbnail (`thinnest_px48`) are not
  small detail, they are noise.

If two masses are the same size, one of them is wrong.

## 2. Head : body

| class | head height : standing height | head width : torso width | head share of the orbit (best view) |
|---|---|---|---|
| biped / bird / small flyer | 1 : 3 to 1 : 4 | 0.7 - 0.8 | 20 - 30% |
| quadruped (dog, cat, deer) | head length : body length 1 : 2.5 to 1 : 3 | 0.55 - 0.7 | 20 - 30% |
| brute / giant | 1 : 5 to 1 : 6 (a small head reads as power) | 0.35 - 0.5 | 6 - 12% — never under 5% (`head_small`) |

The raven-wyvern went from a 13-17% head share to 25-29% with the head 1.3x
larger on a neck half as long, and read as a character instead of a bird on a
pole. The neck is at least the head's half-width thick and at most one head
length long; a thin S-neck reads as a snake or a stilt.

## 3. Limbs

- **A real thigh.** The thigh root is 0.4-0.5x the torso's half-width and
  tapers into the knee; the shank is at least 0.4x the thigh (`profile` rows
  0.10 → 0.11 → 0.065 → 0.045 on the raven). A shank thinner than a third of
  the thigh is a stilt.
- **Short and sturdy.** Legs from hip to ground about 0.8-1.1x the torso's
  depth for a chunky biped. Long legs are a deliberate design choice (a heron,
  a strider), never the default.
- **Separate digits.** Toes and fingers are their own `curve` parts (or a `paw`
  / `hand`), three or four of them, each with a claw in a dark hard material
  (`host_part` on the toe). Mitten feet and a foot as one lump read as clubs.
- **Tail = part of the body.** The root is 0.8-0.9x the body's rear radius and
  continues the back line; it tapers over its length and is no longer than the
  body. A constant-radius tail longer than the body is a rod. Feathers or fur
  on it (`tufts`) make it read as a mass, not a wire.
- **Wings at rest are folded**, back and down: the wrist just above the
  shoulder, the tip sweeping back past the tail root. The membrane is still a
  big designed shape from the side (a sail), and from behind the creature has
  folded wings, not a T. Raised arms or spread wings in the bind pose are a
  T-pose from az180.

## 4. The face

- **Eye**: big. Iris radius about 0.3x the skull's half-width (raven 0.054 on
  0.175). A value step against the skull of 0.3 or more (gold on slate). The
  pupil is 0.5-0.6 of the iris, and **always** a `highlight` — the wet eye is
  what makes it alive.
- **Lid**: shallow (`angle` 36-46) with a lower lid (`lower` 20-30) for a
  confident squint. 55+ reads sleepy. The lid leans with the skull's surface
  normal, so on a wedge head it leans BACK and the eye reads sad. Do not let
  the lid carry the expression.
- **Brow**: the expression. A separate `curve` in a dark or accent material,
  `join: extrude`, `shade: hard` (a flesh-shaded brow is blended into the skull
  by the seam pass and disappears), starting buried behind the eye and running
  forward over the top of it.
  - front end LOWER than the back, cutting into the top of the iris →
    determined, confident, a hero;
  - level → calm;
  - front end HIGHER → worried, sad. Only on purpose.
- **Muzzle / beak**: confident and simple — one wedge, a clean hook, a clear
  mouth line. Its root is narrower than the face it grows from, buried, so it
  grows out of the head instead of sitting on it like a box.
- **Pupil direction**: ahead and slightly down (the default). A pupil on the
  raw surface normal stares at the sky.

## 5. Stance and clips

- The bind pose is symmetric left/right. A stride or a weight shift baked into
  the bind pose (`joints_R` offsets) rides through every clip: the walk then
  has one foot ahead the whole cycle. Put the stance in `idle` (hand-written
  L and R hip tracks — an explicit R track overrides the automatic mirror —
  with the ankles levelling the feet), and let `move` mirror at `mirror_phase`
  0.5.
- Plant the weight: knees slightly bent, the body forward of the hips for a
  biped, the head up.

## 6. Avoid list — the uncanny and the crude

- stilt legs, rod tails, S-necks thinner than the head's half-width
- a torso longer than twice its depth; a round barrel chest with no keel or waist
- a small head on a biped hero (under 1 : 5), a head sunk between the shoulders
- bead eyes (no pupil, no highlight), a pupil staring up, the lid alone as brow
- a beak or muzzle that is a box stuck on the face (root as wide as the head)
- a T-pose, raised arms or spread wings in the bind pose
- one flat colour per mass: every mass gets a value plan (a darker saddle,
  a paler breast, a darker tip)
- many thin identical spikes (a gear) instead of a few bold clumps
- realism in proportion with toy detail, or the reverse: pick stylised and
  commit to it everywhere

Check the result on the orbit sheet AND the hero shot — by eye. The metrics are
secondary: a creature can clear every number and still look wrong.
