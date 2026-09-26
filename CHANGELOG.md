# CHANGELOG

## Unreleased — the output stops looking like blobby tubes

**Why it looked crude.** Four causes, all in the shipped wolf, none of them the
tessellation density:

- The shading stack's default ramp ran from `#001370` at the feet — a multiply by L 0.27
  with a strong blue chroma, stepping to grey over 8% of the height. Every quadruped's
  legs and paws shipped near-black navy, and the step read as a waterline.
- L8 blended the shipped NORMAL 90% toward the bone field, i.e. toward a CYLINDER's
  normal. A chest that swells, a thigh that tapers into a hock, a muzzle that steps down
  from the brow all shaded as the same uniform tube.
- L1 averaged every flesh vertex with everything within three median edges, own mesh
  included — a blur the width of a leg that melted the spine saddle, the belly band and
  every leg/torso value step into one mud.
- `soft_mass` counted the diagonal of every loft quad as an edge. A diagonal cannot
  crease, so the denominator was a third too big and authors cleared the floor by
  dropping `smooth_angle` to 17–20°, which facets the entire body.

**Engine (every spec)**

- `ramp` default `#8f8d8f → #dcdcdc → #fff8ec`, band 0.30 wide: a gentle grounding.
  `boost.dC` 1.25 (was 1.50, which turned every warm brown orange). `normals.flesh` 0.30.
- L1 blends a flesh vertex toward the OTHER meshes' colour, weighted by how close the
  nearest foreign vertex is — seams still fade, authored arcs stay crisp.
- `soft_mass` measures real edges only. The 10% floor is unchanged.
- `"caps": ["dome", …]` is a real dome: `cap_rings` (3) extra rings on a quarter-ellipse,
  `cap_depth` (0.8) × the end ring's smaller radius. Muzzle tips, rumps, tail ends and
  the free end of every leg stop being chopped-off discs.
- `paw` rebuilt: a rounded-box pad whose front IS the toes (default 4), each half-buried
  so AO hides the join; `"claws": true` adds a second hard-shaded mesh in `claw_material`.
- `eye` gains `"pupil": {}` — the engine seats a darker sphere on the front of the iris
  where it actually landed — and `"sink"` (fraction of the radius buried).
- `curve` segments take `"r": [rw, rh]` (elliptical section), the part takes `"roll"`
  (degrees) and `"cap": "dome"`.
- `fin` gains `"bevel"`: faces shrink toward the centroid, the full outline becomes a
  mid rim — a lens with a chamfered edge instead of a slab of card.
- A part builder may return several meshes (`<name>.<sub>`), each with its own shade
  class; `mirrorMesh` carries `shade` along.

**Output contract (`harness/glbcheck.mjs`, mirrored into `engine/core/contract.js`)**

- A file SHORTER than its header declares is now `truncated` — cut off by an interrupted
  download, upload or copy — and says which chunk the cut falls in. It used to be reported
  as `trailing_bytes` with a negative count ("-N byte(s) live outside the declared file"),
  which sends the reader hunting for a smuggled payload that is not there. `trailing_bytes`
  is kept for the carrier case: bytes BEYOND the declared length. `tools/test.sh` checks
  both codes, and a cut in the JSON and in the BIN chunk.

**Hero shot (`harness/outline.py --hero`)**

- Rasterised at 2× and averaged down (anti-aliased edges), premultiplied through the
  resize; a lower ambient with a wrapped warm key, cool fill and rim so the form models;
  a blurred contact shadow from the footprint, on the alpha channel.

**Second visual pass — the wolf that came out was a boxy olive coyote**

Reviewed against a stylised game-wolf standard: nearly monochrome olive-brown, a head
that merged into the body, hard planar corners along the flank, legs like square posts,
a sausage tail, no ruff, a long thin fox head, a pink ring round the hero's contact
shadow, and a seam at every shoulder. Four causes in the engine, one in the harness, and
the spec.

- **`soft_mass` was measuring the wrong thing, and the boxiness was its doing.** The
  ruler was the share of edges whose dihedral reached `smooth_angle` — the edges the
  normals SPLIT — so a well shaped mass at the default 50° scored 0 and was refused,
  while a tube of one radius with `smooth_angle` 20 creased on every longitudinal edge
  and passed. The only way to clear it was to drop `smooth_angle` under the wall angle,
  which facets the whole body into planar strips: the "designed creases" the reviewer
  saw are exactly that. The ruler now measures FORM — the share of a volume's walls
  (ring to ring, per side, dome caps excluded) that lean off the chain axis by 8° or
  more. Measured: the shipped wolves 48-51%, wolf_red 32%, their sausage twins (every
  profile row set to the middle row's radius) 2-4%; `sides` and `smooth_angle` do not
  move it. The floor stays at 10%. `calibration/red_5050.json` had dodged the old ruler
  with `smooth_angle` 20 on a near-tube; it now has a profile and is refused by
  `proportion` and nothing else, as before. The lever named in the message is the
  profile. The cards say the same.
- **`tufts` part type — fur that leaves the silhouette.** A ruff, a mane, a bushy tail,
  a cheek beard: a crown of short tapered wedges seated on a volume's surface at
  `anchor {chain, t, around:[from,to]}`, `rows` x `count`, swept along the chain,
  drooped toward the ground, with a deterministic length jitter. They are FLESH to the
  shading stack and ride the skin of the ring they grow from, so a ruff across two neck
  joints bends with the neck. A lofted tube cannot make a ruff: a fatter ring is a ring.
- **Arcs take `t: [t0, t1]`** (a band limited along the chain: a dark tail tip, a pale
  muzzle, a saddle that stops at the withers, a cream chest that does not run under the
  belly) and **`feather` / `feather_t`** (the band's weight ramps in from its edges, so a
  saddle melts into the flank instead of stopping on a ring line). Feathers narrower
  than the ring's angular step land between vertices and do nothing; the card says so.
- **Junction normals.** Where a limb enters the torso, a head the neck, a tuft the
  skin, the two surfaces cross at an angle and the crossing caught the light as a hard
  bright edge whatever the colours did, because the NORMALS stepped across it. Every
  attached flesh piece now takes its host's normal within `shading.normals.junction_band`
  (0.06 x model height) of the host surface; geometry untouched, only the shipped
  NORMAL, and only on the attached piece. `inside.js` gained `nearest()` (the closest
  surface point with its triangle) for it. The shoulder seam is gone.
- **Hero shot: the pink ring round the contact shadow** was the premultiplied picture
  rounded to 8 bits before a Lanczos resize — in the shadow's soft rim (alpha 5-20) the
  dark shadow colour premultiplied to 1-2 counts per channel, rounded unevenly, and
  came back purple from the un-premultiply. The downsample now runs in float with a box
  filter (no rounding, no Lanczos overshoot on the alpha edge).
- **Engine review fixes (from the concurrent code review of the first pass):**
  `root_containment` read the start-dome's tip instead of the root ring (`_dome0`);
  `part_overlap` warned a paw's own claws against the paw (`partName` stem); the new
  L1 left seams of OKLab 0.10-0.15 because the blend capped at 0.5 and averaged only
  the foreign mesh — it now averages every mesh in the radius and blends at full
  strength out to a third of it, so two coincident vertices land on one colour; a
  declared `shade` on an eye did not reach `eye.L` / the pupils; `part_names` refuses a
  "." in a name (the engine's own separator, a `part_spans` collision waiting to
  happen); `self_clip` keyed meshes by material@chain, so a mirrored twin shared its
  source's key and the L and R legs were never swept against each other.

**Example**

- `example/wolf.json` re-authored again: a wolf value plan (charcoal saddle, tawny
  flank, cream chest / belly / muzzle / inner leg, light cheek mask under a dark crown,
  dark ear backs and tail tip), a `tufts` ruff, cheek tufts and tail fringe, a broader
  skull with a heavier muzzle and broad-based ears, a thicker neck, rounder sections
  and the default `smooth_angle` on every volume. 6,260 triangles. The three clips are
  unchanged. `assets/hero.png` regenerated.

**Third visual pass — the tawny flank was a rectangle, and the ruff was paper**

Reviewed again: a hard-edged orange block on the flank, a pale stripe down the inside
of the front leg that looked like a bug, thin thighs and no shoulder, a ruff of paper
spikes, a black blob for a tail tip, and two `contrast_adjacent` warnings on the tail
brush. Two causes in the engine, one in the check, and the spec.

- **Every feather in the shipped spec did nothing.** `feather` is resolved by the
  vertices — a vertex colour is interpolated linearly across each wall — so a feather
  narrower than the ring step (360/sides) lands between two vertices and ships a hard
  edge. The wolf wrote 8-24° feathers on 12-14-sided volumes (26-30° steps) and 0.05-0.08
  `feather_t` on rings 0.07 apart: all of them below the step, all silent. That is the
  orange rectangle, and the leg stripe was the same thing — the authored inner-leg cream,
  a 55° band on a 12-sided leg, two vertices wide at three times its neighbours'
  brightness, with a hard edge on both sides. The ramp is now a smoothstep, and the
  compiler WARNS with the numbers whenever a feather is under the step or a `feather_t`
  under the ring spacing, and says what to write instead (2-3x, or raise `sides`). The
  card says the same. The arc code moved out of `buildVolume` into one `arcColours()`.
- **`curve` parts take `colors.arcs`** — the pale inside of an ear, the dark upper edge
  of a horn. The angle is read in the curve's own parallel-transport frame, not the
  body's, so the build prints where 0° / 90° / 180° face.
- **Tufts are clumps, not blades.** The wedge was two rings tapering straight to a
  point; a crown of them read as paper spikes because every silhouette edge was a
  straight line and every tuft was one flat colour. Each tuft now has a root ring, a
  full ring a third of the way out (`bulge` x `width`), a shoulder ring and a tip — a
  lobe that pinches — and carries a colour ramp: the ROOT takes the colour of the host's
  skin at that vertex (it never stands off the body) and the TIP takes the material, or
  `tip_color`; `root_color` overrides the root. Fewer, larger, 5-6-sided clumps read as
  fur.
- **`contrast_adjacent` leaves tufts alone.** A tail brush in the tail's own fur is fur,
  not a part that failed to separate; its read is the outline and the root-to-tip ramp.
  `brush.R` was never a bug: `"mirrored": true` on a centreline tail grows the other
  side's clumps (the `around` range covers one side), and the twin takes the `.R` name
  like any mirrored part.
- **Example:** feathers at 2-3x the step on 16-sided body / 14-sided head / 12-sided
  tail, a muted tawny (`#957757`, the chroma boost turned `#b07a44` orange) confined to
  the lower flank under a cool charcoal saddle, the inner leg a soft `#c9b894` gradient
  at 60° feather; the leg ellipse turned deep fore-aft (the old spec had the haunch
  wider side-to-side than front-to-back, i.e. a post) with a real thigh (0.165 x 0.12)
  and upper arm; the ruff 2 x 6 six-sided clumps hugging the neck, cheek and brush
  clumps to match, the brush in its own `fur_brush`, three dark `tail_tip` tufts
  extending the tail instead of a black dome; a pale inner ear; nose bridge and lower
  lip a step darker. 7,688 triangles (budget 4,000-9,000). The three clips are unchanged
  and were checked mid-motion from three angles: no stretching at shoulder or hip, no
  tufts through the body, no colour smearing.


**Review fixes (engine, found building the gallery raven-wyvern)**

- A mirrored tuft on a centre-line joint whose name starts with "L" (`Loin`) crashed the
  build: `mirrorMesh` now maps only joints that really have a twin.
- `soft_mass`'s form ruler measures radius change against axial advance and pools by wall
  area, with a bar of min(8°, one mean radius over the chain length): a twisted or
  cone-padded sausage no longer passes, and a long python no longer needs `soft`.
- Right-hand twins get junction normals (the host lookup used `_rings`, which mirrored
  volumes do not carry), the blend fades out where the host normal opposes the vertex's
  own, and hosts ship the same L8 blend as the pieces joined to them.
- `signedDistance` takes its sign from angle-weighted pseudo-normals, which removes false
  `part_overlap` warnings at corners; `part_seat` measures burial against the surface.
- `ground_clip` and effector reports name mirrored twins `<chain>.R`.

## 1.3.2 — the creature declares what its parts are for, and the engine makes it pay

**Pipeline integrity fixes (after the 1.3.2 cut)**

- `setup.sh` promised "calibrate OK" and printed "setup OK" without calibrating
  anything: `calibrate.py` had been retired with the browser. It is back as
  `harness/calibrate.py`, browser-free, and both setup scripts run it and exit
  non-zero when it fails. It now also requires each red sample to be refused for
  its OWN fault (red_5050: `proportion` and nothing else), and a crash with no
  `BLOCK:` line no longer counts as a block.
- The calibration samples had rotted: the known-good `wolf_green` was refused by five
  of the 1.3.2 checks. It now declares names, `joint_range`, `function` and
  per-volume `smooth_angle`, and its gait no longer clips — no check was relaxed.
- CI ran `harness/silmetrics.mjs`, retired above, so it failed on every push. CI now
  runs `tools/test.sh`, the whole self-check suite, and `synccheck.py` refuses any
  shipped file that names a repo path which does not exist.
- Harness bugs: `gates.py --by`, `ship.py --help`, `fit.py` litter and absolute-joint
  proportion, `round.py`/`partreads.py` from another directory, `graft.py` part-name
  clashes and membrane track renames.

**The declaration**

- `function` on each chain: `axis` / `locomotion` / `effector` / `ornament`. Manufacturing
  vocabulary only — nothing about damage, hardness or worth. A part bolted to a chain
  inherits that chain's function, so the blade on the neck is covered without naming it.
- Six checks make the declaration cost something. A label nobody verifies rots, and each
  of the six blocks a defect class the engine could not see before.

**Joint limits are declared, and the body is asked whether it agrees**

- `joint_range` on each joint: degrees per axis, in the joint's own frame, the same axis
  names the tracks use. An axis left out is LOCKED at 0; `"free"` opts one out. The L side
  is authored and the R side is generated — `ry`/`rz` negate, which swaps the interval's
  ends — because a hand-written mirror is the bug this release just finished fixing.
- The numbers are authored because a spec writer already knows a knee is a hinge and an
  elbow does not twist, and that is not computable from vertices. They are then CHECKED
  because the author does not know how thick THIS body is: every declared bound is swept
  against the geometry, and a limit the body cannot reach blocks with the angle that can.
  A gorilla's shoulder swings 60° back; a gorilla with a wrecking ball hanging off a crane
  on its back stops at 50°, and only the sweep knows that.
- Three failures with three different fixes: `undeclared` (a clip turns a joint with no
  entry), `overrun` (a track leaves its own interval), `unreachable` (the body collides
  first).

**Every part has a name, and the name reaches the file**

- `name` is required on every part and must be unique. A material is a CLASS — primitives
  merge one per material so a forty-plate body does not ship forty draw calls — so a
  material name can never say WHICH part something is. The same `paw` material sits on a
  foot pad and on a nose-leaf, and anything aggregating by material adds them together.
- `asset.extras.part_spans` records, per part, the primitive and the `[first, count]`
  vertex range it owns. Same materials, same primitives, same bytes of geometry: the
  identity simply stops being thrown away at merge time. Mirrored twins carry `.R`, an
  eye pair carries `.L`/`.R`.
- This was not cosmetic. `self_clip` keyed its meshes by material and host, so thirteen
  `steel_bolt` parts on one creature collapsed to one entry and twelve of them were never
  narrow-phase tested. With names, the check found a real interpenetration on the first
  rebuild.

**Mirroring was truncating every mirrored limb**

- `mirrorTrack` resamples instead of shifting keys. The old code mapped a key at `t=1` onto
  `t=phase`, where it collided with the key already there and the sort dropped the rest of
  the track — the mirrored limb froze partway through the cycle. **Every mirrored track was
  affected.** Fixing it also cleared `root_drive` failures that were downstream of it.

**Checks**

- `gait_footfall` — a step must land in FRONT of where it lifts, measured against the foot's
  own liftoff point, not the hip: a bird's hip sits inside the body and a hip-relative test
  calls a correct walk wrong. The contact window now expands contiguously from the foot's
  lowest frame; thresholding the whole cycle split the window the moment the pelvis bobbed.
- `effector_leads` — at the frame the attack reaches furthest forward, the declared effector
  must be the frontmost mesh. The frame that matters is peak reach, not the last frame.
- `attack_windup` — 5% back, or 15% out to the side. Either route passes; a weapon that
  cannot pull straight back without sweeping through the body goes around.
- `self_clip` — swept self-collision. Sphere proxies bound to the dominant bone for the broad
  phase, real mesh distance only for the pairs it names: 0.3–0.7 s for all three clips.
  Pairs that already touch at rest are excluded — that is `part_overlap`'s question.
- `clip_closes` — a clip that does not loop still snaps back when it ends.
- `ground_clip` — nothing below the plane the creature stands on. The receiving physics
  builds its collision proxy from the mesh; a hand under the floor lifts the whole body.

**`harness/autofix.mjs`**

- The arithmetic corrections, run before a round is spent: the ground offset onto the root's
  `ty` (chasing it with joint angles does not converge), loop closure, and compensation for
  joints that must hold their own aim while the body turns for some other purpose.
- Compensation is written as the parent's inverse rotation, not solved by iterating on
  angles — past vertical the `atan2` jumps and the correction diverges.
- **Compensation is subordinate to the purpose.** A head aimed forward pushes its muzzle out
  in front; if that overtakes the effector the strike reads as a head-butt. The share is
  solved for, not assumed.
- It never touches decisions: which way a leg swings, what the creature attacks with, how far
  it lunges. Those stay with the designer.

**The browser is gone**

- Nothing in this package launches a renderer any more. `setup.sh` installs no Chromium,
  so the class of install failures where a blocked CDN stalls setup is gone with it, and
  the harness is `three` plus numpy/pillow/scipy.
- Every number the renderer used to produce is arithmetic on the vertices, and now lives
  in ONE file: `harness/outline.py` already owned the silhouettes and the z-buffer that
  attributes part shares, so it took the rest. Part shares, the colour numbers, the clip
  and skin list, per-part bounding boxes — all of it read from the file it was already
  reading. `judge.mjs` stopped taking its own photograph of the same model and now checks
  its claims against outline's numbers.
- The colour ruler is verified, not asserted: run both ways over a reference shelf, the
  saturated-area measure agrees with the browser's at **r=0.999** and the same thresholds
  carry over untouched. `style_dark` / `style_light` deliberately changed meaning — they
  now read the creature's OWN colour instead of a studio render of it, which is what the
  designer controls; the two correlate at r≈0.96 but are not the same scale, so a
  pre-1.3.2 threshold needs re-picking once.
- `hero.png` is projected, not rendered. The entire L1–L8 shading stack is baked into the
  vertex colours at build time, so lighting it again in three.js was lighting a
  photograph. Same z-buffer, transparent background, framed to its own content.
- Two view conventions moved to the tool that survived: `side` is the LONG profile rather
  than a fixed +X camera (the old one showed a spread-winged creature edge-on and called
  it a side view), and the three-quarter view is `hero` — `tq` still resolves to it.
- Retired: `silmetrics.mjs`, `maskmetrics.py`, `hero.mjs`, `pwlaunch.mjs`, `pwprobe.mjs`,
  `calibrate.py`. The SHARED-TOOL QUEUE that named their duplicate measures now prints
  nothing. `synccheck.py` refuses any file that imports playwright or launches chromium.

**The trap list became code where it could**

- Four engine traps that were previously only written down are now the engine's own words, at the moment they happen, instead of a document
  someone has to have read:
  - a `fin` whose outline has two nearly-coincident points is refused BY NAME, with the
    two indices and the distance. It used to extrude into flipped triangles and surface
    later as a `mesh_integrity` count with no address, costing a round of bisection.
  - a `joints_R` entry written relative to itself says so, instead of "dependency cycle",
    which sends the author hunting for a loop between joints that does not exist.
  - `eye_pupil` names a lone eye sphere for what it is: a flat coloured disc, which at
    reading size is a sticker. An eye reads by the value step between iris and pupil.
  - `part_overlap` above.
- The rest of that list is process advice already covered by the cards, or notes that
  belong to the operator. It does not ship as a document.

**part_overlap was comparing boxes**

- The check that reports one part sitting inside another tested A's vertices against B's
  axis-aligned BOUNDING BOX. A box is not a shape: a 2.8 m spear's box contains any hand
  gripping it, so the check reported the hand as buried in the spear. The signal was not
  noisy, it was wrong, and acting on it removes parts that are correctly placed. Same error
  class as the sphere below.
- Measured against the real surfaces now. On a reference creature the count halved
  (32 → 16) and what disappeared was box artefact.
- Two severities, because they are different problems: COMPLETELY buried is invisible
  geometry that still costs triangles, and partial is a seam, which is usually the point.

**The signature has to say whether it is visible in black**

- Gate 1 reads a 48px silhouette, which has exactly one dimension. A feature made of
  colour, of COUNT (nine faces, one leg), of something soft, or of a face has no boundary
  in one — so betting a creature's identity on it asks Gate 1 to measure what it cannot
  see.
- `brief.py` now blocks a signature slot that does not end `silhouette: yes` or
  `silhouette: no`. It does not forbid the bet; it forbids it being an accident. "No" is
  allowed and often right — it declares that MID or HIGH carries the feature and the body
  has to carry the identity on its own, decided before the rounds are paid for.

**The trap list ships**

- `cards/PITMAP.md` — facts about this engine that are expensive to discover by trial: the
  shapes it refuses, the fields that must be declared a particular way, the corrections
  that never converge. Card 00 sends you there before you author anything.

**A volume is not a string of spheres**

- `root_containment`, `limb_clearance` and `part_attachment` all asked the same question —
  "is this point inside that volume, and if not, how far out?" — and all three answered it
  by finding the nearest ring CENTRE and comparing against a SPHERE of that ring's widest
  radius. A volume is a lofted tube, and that sphere bulges past the END CAP by a whole
  half-width. The error is therefore worst exactly where it matters most: at the end of a
  chain, which is where the next chain attaches. A torso 0.80 m wide handed out 0.4 m of
  phantom "inside" straight off the chest, so a head sitting 0.33 m in front of the last
  ring centre was declared buried while its real distance to the surface was 0.24 m — a
  floating head, attached only by two stray vertices of a foreleg.
- `engine/core/inside.js` measures against the triangles the file will actually ship, and
  all three checks now call it. The sign comes from the closest triangle's own normal, not
  from a ray cast, because an attached chain leaves its root ring open on purpose and ray
  casting needs a closed surface.
- `root_containment` now judges by the ring's MEDIAN rather than a count of points. A ring
  meets a CURVED host, so a few of its points always poke out; across a reference set of
  102 joints the median sits inside on 95 of them, and the 7 it does not are the ones you
  can see.
- The corrected distance is stricter than the sphere was hiding: the same 1.5%-of-height
  tolerance that `part_attachment` always had now sits on the 99th percentile of that set
  instead of nowhere, and it catches parts standing 4–6 cm clear of their host.

**One creature is one connected body**

- `body_islands` walks every piece, unions the ones that share material, and refuses
  anything that comes back as more than one object. The weld is 3% of model height at
  three points — two stray vertices poking in is a coincidence, not an attachment.
- It exists because the three checks above all ask a LOCAL question (is this piece seated
  in ITS host) and the failure was global, and because a silhouette cannot see it either:
  a head floating inside the outline is not a hole in the mask.
- 3% is a floor, not a target. Well-built parts sit anywhere from fully embedded to ~3% of
  height off their host and there is no gap in that distribution to put a threshold in, so
  this takes the loosest value that is still correct. The failure it exists for is 9.3% —
  three times the bar.

**Gate 1 stopped grading itself**

- `identity.py` used to ask you which rank the brief's noun reached, and one judgment
  sat under that number: *does "hound" count as "wolf"?* The only party available to make
  it was the party being graded. A brief can already carry an accepted list, and nothing
  compared the reader's words against it.
- Now you hand over the reader's words, verbatim and in order (`--guesses side="…"`), and
  the machine matches them against the brief's accepted list. Widening the family is still
  the designer's call — it just has to happen in the brief, before the geometry exists,
  instead of at r3 with a shape to defend.
- `brief.py` blocks an identity slot with no accepted list. It is one line, it costs
  nothing to write generously, and it has to be on the record.

**Housekeeping**

- `synccheck.py` refuses any file named `DEVLOG*`: a lab notebook never ships, and the
  filename is the only rule that works in every language.
- `example/wolf.json` builds green under the 1.3.2 checks: named parts, declared joint
  limits, and a stride that no longer walks the hind paw through the front one. The
  shipped example is the reference the cards point at; it has to pass its own gates.
- `outline.py` says so out loud when scipy is missing. It used to return four keys short
  — protrusions, thinnest feature, convexity, mirror symmetry — so the legibility and
  boldness gates had nothing to read and every build passed them by default.

## 1.3.1 — reads are scored, the brief is checked, and everything computable is computed

**Publishing hands back two links, and the second one is checked (2026-09-03)**

- The server answers a successful upload with a claim link as well as the one-time
  takedown code. This build matched exactly one field name, `manage_token`, so the claim
  link never reached anyone using it. `harness/publish.mjs` now reads a family of names,
  classifies each value by shape, and keeps the first link AND the first code — neither
  may shadow the other: the link lists the model under your account (Google sign-in, dies
  once used), the code removes it (one-time, cannot be re-issued, no sign-in).
- The claim link is GETted before it is handed over. `claim_link_live` is `true`, `false`
  or `null` (could not ask — which changes nothing, since the upload just succeeded through
  the same network). On `false`, `harness/ship.py` gives `claim_fallback_url` instead: the
  standing claim page, which takes the same key. Nobody is ever sent to a 404.
- `cards/04_SHIP.md` has a row for `manage_kind: both`, which is the normal case.
- Behaviour is verified against all four shapes the server can answer with.

**The blind read**

- Gate 1 is SCORED by rank and view count (`harness/identity.py`) instead of demanding one exact word: rank R passes if the noun reached R in at least R views, and the requirement loosens by one view per repair round. 3 of 4 views, the brief's identity view among them.
- A round builds TWO OPPOSITE POLES of one named axis, not one attempt and not three near-copies. `round.py` measures how far apart they sit on the mass-layout ruler and refuses to spend a reader on one design built twice (floor 0.25).
- ONE reader does a whole gate — choosing the winner AND confirming 3-of-4 — in a single batch.
- On an identity FAIL, `identity.py` names the views not yet read and requires them to be tried before a rebuild.
- The "wider or taller?" binding question is retired; the bump count and the canary remain.
- Thumbnails are letterboxed, not squashed, so the proportion the reader sees is the proportion the file records.

**Computed instead of read**

- `harness/outline.py` produces silhouettes from the GEOMETRY — no browser in the LOW loop. Same camera, same masks, same measures, plus `iou_vs_prev` and mass-layout thirds.
- `value_order` sorts every material by OKLab lightness on each build; whatever is brightest owns the eye, and anything within 0.05 L competes.
- `contrast_adjacent` compares every part against the material of the thing it sits on; under 0.10 OKLab they read as one mass.
- `thinnest_px48` is information only and no longer blocks.
- MID spends NO reader: both the isolated part read and the colour read are deleted, replaced by the two checks above.

**The brief**

- `harness/brief.py` checks the brief for PRESENCE, never content, and runs inside `round.py` at r1. Five slots plus the one exaggeration block when blank; the other four are noted.
- Slots that name parts also name their CHAINS, and the r1 spec must contain them.
- Material is not judged anywhere: no "what is it made of", no roughness words in the value plan.

**The engine**

- `soft_mass` — a volume that cannot break anywhere renders as a bean, and that is the DEFAULT. Blocked, with the fix in numbers; `"soft": true` opts a mass out.
- `gait_direction` — a planted foot must sweep BACKWARD; a forward sweep is a walk cycle playing in reverse.
- `root_drive` — a lunge must be driven on the skeleton ROOT, or the creature is nailed down by the end that did not move.
- The L1–L8 shading stack moved into the engine (`engine/core/shade.js`) and runs on every build.
- Every blocking message states the FIX with the number to apply, not just the fault.
- `<out>.checks.json` is written on refused builds too.

**The harness**

- `harness/fit.py` makes a spec LEGAL before a round is spent on it. A refused build is refused for two different reasons: DESIGN (the shape does not read) and ARITHMETIC (a root ring is not buried, two bones came out the same length, the height is off). The engine already prints the exact correction for the arithmetic ones; `fit.py` reads them back, applies them, rebuilds and repeats. It never touches `balance`, `mesh_integrity`, `touch`, `part_seat` or any style threshold — those need a decision.
- `root_containment` now names the CHAIN'S OWN root joint instead of the host joint it hangs from. Moving the host drags the chain with it, so the old advice could not converge; applying it repeatedly just walked the pair across the model.
- One command per round (`harness/round.py`): build, render, measure, pre-check, one report.
- `harness/gates.json` maps all 35 checks on five axes — enforce, when, by, kind, dept — and `gates.py` prints them. `stage` is a field: LOW/MID/HIGH are levels of refinement, not a fixed department order. `by` is A/B/C: which source produces the verdict.
- `pwlaunch.mjs` finds a cached browser under `PLAYWRIGHT_BROWSERS_PATH` before any download; a build-number mismatch is not a missing browser.
- `synccheck.py` guards the version strings, the promised features, the required files, duplicate measure definitions and the public/private boundary. Its site-specific leak words moved OUT of the script into `harness/leakwords.local.txt` (git-ignored, never packed) — a list of names you refuse to publish, written into a public file, publishes them. It also refuses a tree in which any shipped file points at a `docs/` page that stayed home: a dangling filename names the private document and no one can open it. And it refuses a tree that describes a version which is not out yet: saying a file behaves "identically to" an unreleased build announces that build, its feature set, and that it has users.
- Iron law 3 is counted by `roundcheck.py`, not self-applied; iron law 9 — one creature, one agent, the reader is the only subagent.

## 1.3.0 — the first-users release: joins verified, fresh installs survive

Field reports (first two public days) split into two classes; both are closed here.

Install class — "setup said OK, then everything broke"
- **`setup.sh` now installs the browser** (`npx playwright install chromium`; skipped when `PW_CHROMIUM_PATH` is set) **and probes a real launch** (`harness/pwprobe.mjs`) before printing "calibrate OK". The npm package alone ships no browser, calibration never needed one, so 1.2.0's setup passed on a fresh machine and the FIRST silhouette died with a Playwright stack trace.
- **All render tools share one launcher** (`harness/pwlaunch.mjs`): a missing browser now prints one actionable line — `run npx playwright install chromium` — never a stack.
- **A hero failure no longer kills the delivery**: the GLB and viewer are the deliverable; heroes degrade to a warning with the fix printed.
- `playwright` pinned (1.62.1); `setup.ps1` for Windows PowerShell; CI smoke workflow runs the whole fresh-user path (setup → build → silhouettes → delivery) on every push.
- **`harness/synccheck.py` — the ship gatekeeper**: verifies VERSION == CHANGELOG, every promised feature is present in the shipping code, every file the cards point at exists, and no forbidden string leaks. Born from a real leak: two finished features existed in one working copy but not the one that got pushed. Run it before every push; CI runs it first.

Field-report class — the first outside user, verbatim
- **`hand` part type**: palm + four fingers + an opposable thumb from one `size` number (`curl`, `spread`, `fist: true` with the thumb wrapped across); built in ONE authoritative hand frame — "issues with hands, palms, fingers and especially thumb placement" was the top quality report, and improvised sphere-and-stick hands always shipped mittens. `paw` gains `"toes": 2..5`.
- **Declared-height gate**: the spec carries `"height"` (metres); the build must land within ±15% or BLOCK, and the CLI now prints the built dimensions — "correct scaling is a skill completely missing".
- **README gains the copy-paste agent prompt** — "how do u prompt the agent to use it in his VM exactly? thats missing in your readme". Verbatim block + three field-learned rules: don't invent a workflow prompt (it skips every gate), let the agent run setup itself (don't pre-bundle node_modules), image orders become a text brief first.
- **Multi-leg gait doctrine** in HIGH: diagonal pairs for quadrupeds, alternating tripods/tetrapods for 6-8 legs, adjacent legs never in sync.
- **The output contract is ENFORCED, not documented**: every GLB is checked against it the moment the engine writes it (a violating file is deleted, never left on disk), `deliver.py` re-checks the stamped bytes, and `publish.mjs` refuses to upload a file that fails — no card instruction, no human step. The contract: two chunks, zero trailing bytes, one embedded buffer, no URIs, no images at all, no compression extensions, semantic material names, convention bone names, metres/+Z, sane accessors, no paths or markup in any string. Creature names and signatures typed by a person are CLEANED at stamping (control characters, angle brackets, 80/60 caps) rather than failing a delivery. One implementation (`harness/glbcheck.mjs`, zero-dependency `checkGLB(bytes)`, ~1.4 ms) mirrored into the engine as `engine/core/contract.js` by `tools/sync-contract.mjs`; synccheck fails the build if the two drift. Verified against five hostile fixtures — ZIP tail, extra chunk, external URI, path leak, duplicate JSON keys — plus an end-to-end hostile spec whose build is refused. `docs/OUTPUT_CONTRACT.md` writes the same rules down for the community server, which rebuilds submissions independently (`docs/HANDOVER_sanitize.md`).
- **Every GLB carries its birth certificate**: `asset.extras.source_spec` (the pristine authored spec — a second parse, since the in-memory spec is mutated by resolution) + `extras.parts` manifest (kind/type/name/material/host/join per piece). Extract → edit → recompile round-trips green. `embed_spec: false` opts out. On the CC0 community wall this makes every creature REMIXABLE by design.
- **`harness/graft.py` — spec-level organ transplant**: takes two GLBs, copies a named part (plus its palette, and for membranes the rib chains, joints, attach/mirror entries and matching animation tracks, rebased onto the new host), rescales by the two declared heights, writes a fused spec. The normal gates judge the transplant — a graft that does not seat is BLOCKED, not shipped. Never touches meshes, so AO and whole-body shading re-bake coherently on the fused creature.
- example/wolf.json now declares `"height": 1.45` (models best practice; enables graft auto-scaling).
- **Reader verification — assume every reader is lazy**: every blind read (both LOW gates, every MID part read) now carries three traps — per-image binding questions checked against measured aspect/bump counts, one known-answer canary from `harness/canary/` shuffled into every batch, and shuffled neutral image labels. Any tripped trap voids the whole read. A reader that glances at one image and confabulates the rest can no longer pass.

Colour portability (a creature published to a gallery came back white-and-black)
- **The hue now lives in the material, not only in the vertices.** Until now every material shipped `baseColorFactor` white with the entire palette in COLOR_0, so any viewer that does not apply vertex colours rendered the creature pure white — reproduced here by stripping COLOR_0 from a build. The engine now splits the baked colour: `baseColorFactor` takes the per-channel MAXIMUM (the unoccluded colour) and COLOR_0 keeps the ratio (≤ 1, the AO and banding multiplier). Where COLOR_0 IS applied the result is identical — a controlled A/B measured a maximum per-channel difference of 5e-08 — and where it is not, the creature keeps its hues and loses only the shading.
- Found while implementing it: dividing the colours in place corrupted them, because one vertex-colour array can be referenced from several vertices (flat fills, crease splits) and was scaled twice. The pass now builds new arrays; the A/B above is the proof.
- **The colour ruler was blinded by the split, and is now calibrated.** The judge's albedo pass forced `baseColorFactor` to white whenever `COLOR_0` was present — correct only while the whole palette lived in the vertices. After the split it therefore measured the near-grey shading ratio alone: the wolf read 26.0% saturated before and **0.0% after**, so the standard claims sheet would have failed EVERY creature at HIGH with "the creature reads as a grey mass". Albedo is now `baseColorFactor` x `COLOR_0`, always both. The reason nothing caught it is the deeper fault: `calibrate.py` had never run the judge at all, so five colour norms shipped with no sample proving they separate anything. It now runs the colour ruler in both directions — the shipped example wolf must land inside the 10%-34% band (measured 26.3%), and a desaturated copy of that same file, meshes and vertex colours untouched, must be BLOCKED by `saturation_area`. The colour sample is `example/wolf.json`, not `calibration/wolf_green.json`: wolf_green still carries the pre-1.2.0 beige palette (0.2% saturated) and exists to exercise engine blocks, where palette is irrelevant.
- **`glbcheck` gains two portability warnings**: `flat_white_base` (a material with a white base carrying vertex colours) and `high_metal` (metalness above 0.3 — with no environment map, which is the default in most galleries and engines, metal renders near-black; this is the second half of the same field failure). Card 03 states the material limits: no textures, hue in the material, metal ≤ 0.2, roughness free.

Bypass
- **MANUAL.md opens with a stop sign**: you do not need to build a GLB writer, a renderer, a screenshot tool or a modelling script — they are all here, they work, and starting one means you have already left the pipeline. Also corrects the header (1.3.0) and the interview line (exactly ONE question, not two).
- **Delivery refuses a GLB this engine did not build.** Observed twice in the field (an outside user on Reddit, then a 1.3.0 test run): an agent given the package skips the cards, writes its own GLB generator and its own render pipeline, and arrives at delivery with a file that passed no gate — no blind reads, no `attack_reach`, no `part_seat`, no output contract. `deliver.py` now checks `asset.extras.harness` and stops there: the gates ARE the product, and a file that skipped them cannot carry the stamp. The refusal names the two commands that constitute the real pipeline.

Thin orders
- **The customer is asked exactly ONE question, and asking it is MANDATORY** (skipping it is as wrong as asking five: picking a direction is what makes the creature theirs — one that simply arrived never gets shown to anyone) (report: a test run stopped to ask which delivery format to use and whether to add the result to a local gallery — both are the harness's decisions, and both read as incompetence to a non-designer). Card 01 branches on the order instead of interrogating: a thin order gets three directions to point at (diverging on mass / weaponised part / broken anatomy — never three colours of one idea, no answer = take the first), a specific order gets "which of the things you named should people notice first?" (that answer becomes the signature part, and with no answer the most unusual one wins). Size, temperament, proportion, palette and animations are decided silently. Card 00 adds the forbidden-question list: never ask about delivery format, file type, triangle count, folders, whether to run a check, whether to list the result anywhere, or whether the expansion is acceptable.
- **A recoloured example is refused (`example_copy`)**: a thin order tempts the shortest path — open `example/wolf.json`, change the colours, ship it — and the customer who asked for a dragon receives a wolf that reads as a fox. The engine BLOCKs any build whose joints are a shipped reference spec's with the numbers barely moved (≥90% of joints identical in name AND position within 2% of height); building the reference specs themselves is exempt, so calibration is untouched. Templates were deleted from this harness for this exact disease; this stops the example becoming the last template. Card 01 also makes the identity verdict explicit: the blind reader's noun must BE the brief's noun — "a fox" when the order said dragon is a failed gate, not a near miss.
- **The brief is now derived from the rulers, and expanded without asking.** A thin order ("a dragon") is an UNDECLARED order: every empty slot is one no gate can test, so it drifts to the trope. Card 01 lists the nine slots that downstream machinery actually reads — identity, feel, height, signature part + carrying view, mass hierarchy, the two focals, stance, the attack, the value plan — each traced to the check or claim that consumes it. The session fills them itself, in one pass, and never shows the expansion for approval (a confirmation step is a lost customer, and the gates already catch a wrong guess). Two rules keep the expansion from converging: discard the first three ideas (they are the tropes), and commit to ONE exaggeration that distorts every other slot.

Closing & community (server contract re-checked against gobkit.com/docs)
- **One command closes the job — `harness/ship.py`**: package, or package AND publish with `--publish`. The old flow was two commands taking the same arguments twice, so the signature drifted between the file and the listing and the upload got skipped when the second command was forgotten. Ask the person once (name / signature / share?), run one command, read one JSON line back. The signature is remembered in `~/.anyCreature.json`.
- **Uploads survive a flaky network**: the publisher retries twice with a backoff on transport errors and 5xx before declaring the network blocked — a submission lost to one cold start is a creature that never reaches the wall. Verified against a server that fails the first attempt.
- **`--upload-only`**: publish an already-packaged creature without rebuilding or re-stamping it — for the person who said no and changed their mind, or whose upload failed. Card 04 requires offering it in one line.
- **The server's one-time `manage_token` is no longer discarded** — it is the only way a person can ever take their own model down, and the API issues it exactly once. `publish.mjs` now saves it to `delivery/manage_token.txt` and returns it; card 04 requires it to be read out in the same message as the share link. Also accepts a bare `slug` (the server no longer always sends `share_url`) and builds the URL from it.
- **A successful upload is no longer reported as an error.** The server renamed its own success state (`published` → `visible`) and `publish.mjs`, which matched the literal word, printed `{"status":"error"}` on a HTTP 201 and dropped the one-time `manage_token` on the floor — the user was told their upload failed and lost the only takedown key they will ever be issued. Success is no longer a magic word: any 2xx the server acknowledges (`ok !== false`) that carries a `share_url`, `slug` or `url` and does not name a review state IS published; a review state (`/pending|review|queue/i`) is `pending_review`; an acknowledged response with nothing to link to is also treated as uploaded, not refused. `manage_token` is now saved and returned on EVERY branch, refusals included, because a refusal can still carry the token for an earlier upload. Verified against a mock server across six responses (`visible`, `pending_review`, `queued_for_moderation`, a 400 refusal carrying a token, a relative `share_url`, and a bare `{"ok":true}`).
- **`KHR_materials_anisotropy` on a mesh with no UVs or tangents is a BLOCK** (`anisotropy_without_direction`). Reported from the server side: a brushed-metal attempt came out a flat white smear, and dropping the strength from 0.9 to 0.15 changed nothing — anisotropy stretches the highlight ALONG THE TANGENT, so what was missing is a direction, not an amount. With no `TANGENT` and no `TEXCOORD_0` to derive one from, every renderer invents its own and the model is correct in none. Untunable by definition, therefore refused rather than warned; a primitive that has one of the two gets `anisotropy_derived_tangent` (viewers will disagree on the direction). The fix is to unwrap first (`"keep_uv": true`) or to get the look from geometry and vertex colour.
- **Role presets removed — every creature is judged at boss standard.** `harness/presets/{minion,npc,boss}.json` collapse into one `harness/claims.json`; a cheaper creature is not a different ruler, it is the same ruler with a smaller `tri_budget`. Interview Q2 changes from "which role?" to "how big is it in the real world?", which feeds the height gate and graft scaling.

Quality class — "parts don't stick to the body"
- **`part_seat` check + declared joins**: every hosted `curve`/`spike` carries its base ring; the spec declares HOW the part meets the body — `"join":"insert"` (base ring ≥60% buried or BLOCK), `"extrude"` (base centre inside a body or BLOCK), `"snap"` (must ride an anchor or BLOCK), `"place"` (deliberately free). Undeclared roots under 50% buried warn. Kills the exposed-root class: tusks starting in mid-air, beaks hovering off the face, trunks reading as bolted-on objects.
- Card 02 adds the four join verbs and the colour-continuity rule (flesh parts continue the host colour at the base); card 01's pit-map gains the join line; SYNTAX shows `"join"` on the curve example.


> **Version renumber (at 1.2.0).** 1.2.0 is the FIRST PUBLIC RELEASE. All
> earlier development versions were renumbered to 0.3.0–0.12.0 in release order
> (old 0.1.0→0.3.0 … old 1.7.0→0.12.0); the full mapping lives in the
> version-library README. Entries below keep their original content; their old
> numbers are shown with the new number in front.

## 1.2.0 — smooth bodies, one shading pass, saturation measured

Stage cards
- **HIGH gains a fifth colour norm — `saturation_area`, band 10%–34%**: the share of the view whose colour carries HSV saturation ≥ 0.50, Verified: the UNLIT baked vertex colour so brightness, AO and lighting cannot skew it. Below the floor the creature reads as a grey mass; above the ceiling saturation stops working as a spotlight. It rules AMOUNT, never LOCATION — the designer picks which surfaces carry the colour. The reshipped wolf measures 26.0%; the previous wolf measured 0.2% and would fail. The accent norm now reads as a cap on the ACCENT alone (<5%), not on total saturated area.
- **MID's fold-and-carve vocabulary no longer offers `faceted` for masses**: concave sections, `sharp` profile rows and a lower per-volume `smooth_angle` instead; parts may still be faceted freely.
- SYNTAX.md gains `shading`, `smooth_angle` and `build`, marks `faceted` parts-only, and drops `colors.gradient`/`colors.noise` from the volume example. 04_SHIP's gate.json example lists `faceted_body` and `saturation_area`.

Engine
- **Vertex normals are ANGLE-weighted and carry a smoothing angle** — `smooth_angle`, spec-level default 50, overridable per volume and per part. Faces meeting at a vertex average when their normals sit within the angle; the vertex is duplicated only where it genuinely carries two smoothing groups, so creases cost a handful of vertices instead of tripling the mesh. `"faceted": true` is now exactly `smooth_angle: 0`. Area weighting let one big skinny triangle drag a normal off by tens of degrees — and AO bakes from those normals.
- **`faceted: true` on a VOLUME now BLOCKs (`faceted_body`)**: two real runs came back 89% and 93% hard-edged because the model set `faceted` on the big masses; an 800-triangle torso became 800 shards, and since AO bakes from those normals the mess ships inside COLOR_0 where relighting cannot reach it. The right tools for a hard break on a body are `"sharp": true` on the profile row or a lower `smooth_angle` on that volume. Escape hatch for robots, constructs, golems and vehicles: `"build": "rigid"` at spec level. Parts (fin/spike/curve/paw/membrane) may still be faceted freely.
- **Shading moved from per-volume to spec-level**: `"shading": {"gradient":{"top":0.30,"bottom":-0.88}, "noise":{"size":0.018,"amount":0.26}}` (the defaults). The ramp is measured over the WHOLE body's Y range and applied to EVERY mesh — volumes, paws, ears, eyes, horns. Each volume used to ramp over its own bbox, so the same numbers meant different things on an upright leg and a horizontal torso (the old wolf wrote bottom -0.16 on legs and -0.04 on the torso to fake one consistent light), and parts received no shading at all, so paws read as stickers. `noise.size` is a FRACTION OF THE MODEL DIAGONAL, not an absolute distance: an absolute cell keeps its world size as the creature scales, so the same spec on a 5x larger creature produced grain finer than the vertex spacing and aliased into banding. `colors.arcs` stays per volume; `colors.gradient`/`colors.noise` are ignored and emit an `info:` line.
- **Gamma bug fixed**: `hex2lin` in compile.js applies the sRGB transfer function, as ao.js and glb.js always did. Before, any volume with a `colors` block shipped about 1.5x too bright with its value steps collapsed — the wolf's spine-band-to-base contrast fell from 5.3x to 2.1x, so the arc bands were effectively invisible.
- **AO defaults retuned**: samples 14 → 16, strength 0.75 → 0.59, radius 0.35 → 0.60 of the model diagonal. One AO pass only; there is no second crevice pass and none is planned.

Harness & fixes
- **`saturation_area` claim** in judge.mjs — `{"type":"saturation_area","view":"tq","min":0.14,"max":0.34}` — added at stage HIGH to all three role presets (minion/npc/boss) and to `specs/_TEMPLATE.json`.
- `setup.sh` installs scipy: harness/maskmetrics.py imports `scipy.ndimage`, and setup used to print "calibrate OK" then blow up mid-LOW.
- `proportion` decides limb exemption from `spec.mirror` instead of the chain name's first letter — renaming a chain "axis" to "Laxis" used to bypass the 50:50 ruler entirely.
- example/README.md rewritten accurate: the wolf is the reference example (high-saturation area 26.0%), not a copy of the `templates/` anchor removed in 1.2.0, and it ships with UV off.

## 1.2.0 — first public release: MID/HIGH doctrine + Gobkit delivery

Stage cards
- **MID = whitelist part blind-reads, identity only**: face (always) + signature part + order-named parts are rendered ALONE (`qa_isolate` builds) and shown 4-view to a context-free reader with one question — "what is this?" A face that reads as "a ball" fails. Edit vocabulary: swap local shapes / fold-carve / bend the pose (elbows are MID); no naked sphere/cube/cone on whitelisted parts. Silhouette share demoted to a budget check.
- **HIGH = free colour under four norms** (one high-sat main on the signature, one secondary, accent <5%, brightness floor Verified: the render) + three animations always (idle/move/attack).
- **04_SHIP (new card)**: gate stamp (real results only) → name + signature questions (ownership first; signature remembered in ~/.anyCreature.json) → scripted delivery → the share ask LAST, CC0 in one sentence → publish only on an explicit yes. Never auto-upload, never background, ask every time.

Engine
- **Per-vertex AO bakes at compile** into COLOR_0 (hemisphere rays, grid-accelerated, deterministic) — the "solid" look ships in the file; `"ao":false` is debug-only.
- **`attack_reach` check**: attack clips must drive some part ≥ half the body span past the bind front or the build BLOCKs — kills the in-place-wave class.
- **`touch` declarations**: chains declared connected must overlap or BLOCK (the floating-snake-body class).
- **`part_overlap` warn**: measures gross part-into-part interpenetration (the self-intersecting-fist class) — a measure, not a law.
- **`joints_R` pose overrides**: mirrored pairs grow symmetric, bind pose staggers; the mirrored skin follows its joints.
- **Public bone naming**: exported limb bones follow `^[LR][A-Z][A-Za-z]*\d+[A-Z][a-z]$` (LArm1Sh, RFrontLeg1Kn) natively — no `.l/.r` suffixes, no rename pass; mesh `creature`, skin `creature_rig`; internal spec names never leak.
- **Primitive merge**: one primitive + one material per palette entry (kills the 67-material class from mirrored parts) — semantic part names survive as material names.
- **UV atlas now opt-in** (`keep_uv`): without textures TEXCOORD_0 was dead weight; AO no longer needs it.
- Language cleanup: part types settled on `curve` and `membrane`, and the surface-snapping switch on anchored parts settled on `conform`.
- Harness stamp in `asset`: generator `anyCreature v1.2.0`, `extras.harness/.harness_version/.spec`; delivery adds `extras.monster` + `asset.copyright` (user's name + signature travel INSIDE the file); publish adds `extras.license: CC0-1.0` at consent time.

Engine correctness — the "invisible until a human looks" class
- **`part_attachment` (new BLOCK): parts were never checked for being attached to
  anything.** `root_containment` walks `spec.attach`, whose candidates must carry
  both `_rings` and `chain` — curve / fin / eye / paw / spike / membrane have
  neither, so no part ever entered the loop. Real runs shipped a tusk whose whole
  root ring stood 0.031 clear of the skull, a trunk 6/15 outside, a forehead plate
  0.050 above the surface, all reported all green and all caught by eye in the most
  expensive repair round. A part must now come within 1.5% of model height of its
  host's surface. Deliberately generous: eyes and conformed plates sit ON the
  surface and pass; something hanging in the air does not. Mirrored twins are
  skipped — the source carries the verdict for both.
- **`mirror_distortion` (new BLOCK + warn): `joints_R` shears the twin instead of
  posing it.** The mirrored mesh is grown along the LEFT bone path and then dragged
  onto the right joints by weighted TRANSLATION, so a large offset squashes the
  volume. Verified: the wolf: offsets up to 10% of limb length are clean, 16%
  costs 12% of a dimension, 24% costs 19%, 39% costs 31% and blocks. A reported
  case had a right thigh 0.152 deep against 0.381 on the left with its width intact
  — invisible from the left, invisible in the log. Warn past 12% deviation, BLOCK
  past 30%. Doctrine added to SYNTAX and MID: `joints_R` is for a few centimetres
  of stagger; a genuinely different pose belongs in its own chain outside `mirror`.
- **`attack_reach` no longer demands a whole-body lunge.** It required half a body
  span PAST the bind front, which rejected every stand-and-swing design. Now either
  route passes: REACH (≥15% of span past the front) or SWING (a part travels forward
  ≥45% of ITS OWN length — the limb's travel is bounded by the limb, not the body;
  the old rule was a dimensional error). Verified: ±20° twitch blocked, ±35° foreleg
  swing passes, forward tail slam passes, sideways sweep blocked, full lunge passes.
- **`anim_integrity` says WHERE.** It is ~83% of all blocks in practice and used to
  report only `"move" @0.5 folds mesh (10 flipped tris)`, forcing a binary search.
  It now names the worst mesh for folds, and the mesh plus the driving joint for
  stretches, with the three fixes that actually apply.
- **Profile-slope warning at compile.** Scaling a volume without scaling `ring_step`
  crowds rings relative to how fast the radius changes; past a slope of ~0.8 the
  next bend flips triangles. The engine now warns with the number and the location,
  instead of letting it surface later as flipped tris during an animation.
- **Anchored parts narrate the world direction they actually face.** `around` is
  read in the host section's frame; the documented 0=spine / 90=side / 180=belly is
  the BODY chain's frame. On a leg: 0=inner, 90=FRONT, 180=OUTER, 270=back
  — so a plate aimed at the outside of a thigh with 90 silently lands on its front.
- **`deliver.py` refuses a self-contradicting gate stamp.** A delivered model was
  found carrying `"passed": true` with `mid_face_blindread` failed in the same
  object, and it had already been published. The stamp travels inside the GLB
  forever; delivery now stops unless the aggregate matches the checks.

Security & open-sourcing
- **Arbitrary file read in `judge.mjs` closed (the one real vulnerability).** The
  static handler did `path.join(base, urlPath)` with no containment check, and the
  listener bound to `0.0.0.0`. A raw request line carrying `/../../../../etc/passwd`
  (a socket does not normalise it the way `fetch` does) escaped every base and the
  file was served — `/proc/self/environ` included, which is where credentials live.
  Any host on the same network could read any file, for as long as a judge run
  lasted. Now: resolve then require containment, serve only `.js .mjs .map .json
  .wasm`, and listen on `127.0.0.1`.
- **`silmetrics.mjs` and `hero.mjs` bind to `127.0.0.1` on an OS-assigned port**
  instead of `0.0.0.0:8961` / `0.0.0.0:8963`. Their handlers were already
  whitelisted so nothing leaked beyond the model, but the pages and models were
  network-visible during a run, and two concurrent runs collided on the port.
- **Creature names and signatures are HTML-escaped** before they go into the
  delivered viewer (`deliver.py`). A creature named `</h1><script>…` executed in
  the page; the same string also rides in the GLB to the community wall, so
  SECURITY.md states plainly that the server must escape it independently too.
- **Chromium keeps its OS sandbox.** `--no-sandbox` was unconditional in
  `judge.mjs`; it is now opt-in via `PW_NO_SANDBOX=1`. The hardcoded
  `/opt/pw-browsers/chromium` path is gone from all three render tools — Playwright
  locates its own browser, `PW_CHROMIUM_PATH` pins one. That path made every clone
  fail on macOS and Windows.
- **Licensing corrected.** MANUAL claimed "no third-party code is bundled"; it does
  bundle three.js (MIT) as `harness/assets/three-bundle.js`. The upstream notice was
  always preserved in the file, so nothing was ever out of compliance — the sentence
  was simply wrong. Added `THIRD-PARTY-NOTICES.md` with the full MIT text plus the
  licences of everything `setup.sh` installs.
- **Added `LICENSE` (MIT, © 2026 Alsomind Tech Co., Ltd.), `README.md`, `SECURITY.md` and `.gitignore`**; `gobkit.json`'s `_key_label` now says
  the key is public by design and that rotation cannot retract what is already in
  git history.

Delivery & publish
- **Showroom viewer redesigned and moved out of the Python** into
  `harness/assets/showroom.html` (placeholders `__TITLE__` `__BYLINE__`
  `__BUNDLE__` `__B64__`), so the room can be restyled without touching
  `deliver.py`. Gallery room: radial backdrop, floor wash, vignette, a
  small-caps name plate reading `<signature> · anyCreature <version>`, and three
  tool buttons — cycle the file's own animation clips, turntable, hard-edge clay
  with a wireframe overlay. Shadow-casting key light over a ShadowMaterial
  ground; camera auto-framed to the bounding sphere and the model rested on the
  floor. Fully offline: three.js inlined, model base64'd, no CDN and no webfont
  (system serif stack) — double-click and it runs.
- **`publish.mjs`: try the upload, always.** New doctrine written into the
  script header and card 04 — never pre-judge the environment as offline.
  Cloud sandboxes and Cowork sessions frequently do have egress; run the command
  and answer from what it prints. Saying "in a sandbox you can only upload by
  hand" without attempting is now explicitly wrong.
- **`offline` renamed to `blocked`, and 403 is classified as network filtering,
  not a key problem.** The submit endpoint always answers in JSON, so an HTTP
  403 or any non-JSON body means an intermediary replied — a proxy, captive
  portal or corporate filter. `blocked` is a normal outcome, reported as the
  next step ("the pack is ready, drag it into the page") rather than an error.
  Nothing tells the user to fetch or change a key.
- **hero.png is now required in practice**: a submission without a thumbnail is
  accepted but never lists automatically — it waits for a human reviewer, and
  that is the one common post-upload stall. `publish.mjs` warns loudly when the
  file is missing and reports `thumb` in its JSON line.

- `deliver.py` v2: stamped GLB + showroom viewer (studio backdrop, title card, animation pills) + `hero.mjs` auto-framed hero.png (1024² transparent 45°, ≥8% margins, idle mid-frame) / hero.jpg + backup upload pack.
- `publish.mjs`: multipart POST to gobkit.com/api/community (fields model/thumb/title/creator_name/channel/key) with three scripted outcomes — published (echo the SERVER's title/creator + share link), pending_review (one calm line), offline (backup path: drag delivery/upload/creature.glb into gobkit.com/community/upload).

## 0.12.0 (was 1.7.0) — clean painter, strict inspector (validated by 7 head-to-head experiments)

Architecture
- **Creation side stripped to a pit-map**: no design doctrine upfront — free design won or tied every duel where part character mattered; doctrine text taxed boldness. Design knowledge now lives in gates and rulers only.
- **Two gates, four views each, read by context-free agents** (self-grading shipped the worst failure in project history): Gate 1 RECOGNISED — any stick/slab view kills; Gate 2 PUNCHIER — after identity passes, rounds may only exaggerate, judged prev-vs-curr; compliance-only edits forbidden. LOW's deliverable is an exaggerated silhouette.
- **Stop-loss**: same symptom failed twice → concept restart, never a third tweak (verdict-driven micro-repair oscillated: human→bell, trousers→rooster).
- **Signature parts get real geometry at LOW** (a fist is fingers and knuckles, not a sphere); 6:3:1 governs geometry budget, not just screen share.
- Scale calibration: 24px = feel, 48px = identity (control reads on the approved standard proved single-scale gates miscalibrated). Front view alone may be symmetric; paired features still stagger.
- Templates removed entirely (anchor became a topology prison — a giant order produced a wolf skeleton).

Engine wave-1 (~+250 lines; required reading stays ~1 page)
- `curve`: curved horns/tusks/trunks — per-segment steering that accumulates down the chain (`rise`/`fall`/`ahead`/`behind`/`coil`); the mammoth-tusk class of failure was a vocabulary gap, not a design gap.
- `membrane`: skin between rib chains with blend skinning, a scooped trailing edge, and the root-gap warning — the bat-wing failure class, where a shape that never encloses reads as spread fingers.
- Named sections incl. CONCAVE outlines (`"sections"`): bark flutes, crescents — relief is geometry.
- `faceted` hard-edge shading; anchored parts snap onto the host surface normal by default (`conform:false` opts out).
- Compiler narration: `info:` lines report the accumulated bend of a curve and how far a plate was rotated to meet its surface.
- Membranes exempt from the closed-surface fold check (saddle regions are legitimate).
- maskmetrics dullness flags: `sq_fill` (1:1-frame volume), `mirror_sym`, `straight_max` (plank detector) — measures only, judgment stays with the reader/LLM.

## 0.11.0 (was 1.6.0) — method over conclusions (cards + silmetrics)

Constitutional rule added: **cards carry method and rulers, never instance conclusions** — a specific creature's ratio numbers or 24px phrases are per-order products; baking them in anchors every future creature to one answer and pollutes context. Accordingly:
- Ratio table (design 2c) rewritten method-only: the session decomposes the order's creature-noun itself — picks WHICH 3–5 ratios carry the identity, justifies each against the temperament. The giant's worked numbers are gone.
- New general art direction: **ratios checked in all three orthographic views** (one-view drama = cardboard); **per-axis decomposition** (a mass's elongation axis is identity information); **colour philosophy** in HIGH (value-first 70/25/5, saturation as spotlight, one temperature story, pattern follows form).
- silmetrics now renders **side + front + top** and reports per-view aspect/fill.
- Instance residue swept from 1.5.0's cards (giant example lines, magic numbers).

## 0.10.0 (was 1.5.0) — doctrine patch: the giant lessons (cards only; engine unchanged from 1.4.0)

Distilled from an approved no-harness mountain-giant build — the reasoning that made it work, sedimented into the cards:
- **Ratio table** (design 2c): the identity noun translates DIRECTLY into a mass-allocation table vs a baseline; scaling up ≠ giant, changed ratios = giant. The exaggeration vector is the table's extreme rows.
- **Three contour layers** (LOWRES): primary masses (3–5, = 80% of silhouette, verified FIRST) → breakers (straight lines & sharp angles on the contour) → details. Order never reverses.
- **Blob-pile trap + the glue**: elongate ~1.7×, overlap seams, and the decisive fix — a hard plate spanning ≥2 masses fuses them into one structure (why pauldrons span shoulder+arm).
- **Negative space, pose, curve-vs-hard coexistence** added to the silhouette declarations; **≥3 read points** and a ~15° asymmetry nudge added to the stage-1 human checklist.

## 0.9.0 (was 1.4.0) — the big-form release (core competence: silhouette tension)

Engine
- **Relational joints**: `{"from":X,"fwd/up/side":d}`, `{"from":X,"dir":[..],"len":d}`, `"ground":y` for feet — specs think in proportions again; absolute coords stay legal. Verified bit-identical against the absolute wolf spec.
- **Game-ready UVs**: automatic unwrap (cylindrical tubes + planar caps, box unwrap for parts), seam-vertex duplication, one non-overlapping world-density atlas (`TEXCOORD_0`); overlap audit 0.2% (corner texels only) → AO/lightmap bakeable.
- Fixed inverted normals in `paw` (winding) and `fin` (outline now canonicalised CCW, rim rewound).
- Fixed floating surface anchors (eyes/ears): lookup by true arc-length `ringT` instead of ring index (bevel-skip had shifted indices).
- `proportion` gate aligned to the styling rule: 0.96 → **0.923** (the 0.92–0.96 blind band caught nothing); minor-segment filter now relative to mean segment length (checks 6–7 pairs on a 9-joint spine, was 1).
- `limb_clearance` exposed-test gets a 5% seam tolerance (groin-seam verts are host geometry, not exposed limbs).
- Wolf: head split into its own volume (rooted inside the neck), slab thighs (`exp` 2.2–2.6), eyes moved to the head's side (`around` 62).

Harness
- **silmetrics.mjs**: side+front silhouettes, 24px thumbnail, and the numbers — `W_over_H, fill, mass_thirds, torso_depth, mass_contrast, leg_fraction, turn_count, zigzag_alignment, iou_vs_prev`.
- Calibration: green = the bred wolf; red = legacy broken wolf **plus** `red_5050.json`, which violates ONLY the 50:50 rule — proving that specific ruler bites.

Doctrine (cards, all-English rewrite)
- 24px contract (identity phrase / per-part features / signature survival) + blind-read gate with recall scoring and signature veto.
- Exaggeration vector + character axes: declared tension, verified by the loop; floors-are-not-goals iron law.
- Knob table (symptom → spec knob) distilled from the wolf's measured convergence.
- `templates/` library with breeding pipeline: in-house references only, human sign-off mandatory; ships `quadruped_light`.
- Docs/cards no longer reference the retired pre-0.8 spec language or its tooling; syntax quick-refs show the real JSON.

## 0.8.0 (was 1.2.0) — engine swap: original ACS engine v2 (author Ariescar, zero foreign code), six built-in checks, JSON spec, wolf example.
## 0.7.0 (was 1.2.0) — one-shot pipeline for non-designers: 2-question interview, 3/2/1 rounds, five stage cards, staged judging, scripted delivery.
## 0.6.0 (was 1.1.0) — engine renamed ACS; two quantified claims added; 10-round budget.
## 0.5.0 (was 1.0.0) — generic engine + styling rules + embedded compiler + example + manual.
## 0.4.0 (was 0.2.0) — engine/spec split, generic harness.
## 0.3.0 (was 0.1.0) — first two gates, dragon-specific thresholds.
