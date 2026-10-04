# Artist review of the box-model workflow (Opus 5.5 seat, lead character artist view)

Read: WORKFLOW, BRIEF, ART_DIRECTOR, REPAIR, RESULTS, refs/SHEETS, refs/BUILD, carve.py, research/tpa_*.
Looked at: gallery_c1, team_pass, carve_detail_vs_k3, concepts_v2, sheets_v2, and the full packets of
giant, wolf, goblin and stag (abc/c1), plus giant.py / NOTES of giant and wolf.

## 1. Verdict on the current output

Grade as a lead: **greybox-plus, not shippable.** These are recognisable creatures with correct colour
zones. They are not designed low-poly assets. I would send all 11 back at the blockout review, not at the
polish review, and that is the core finding: the pipeline polishes models that never passed a blockout.

**Working**

- Identity reads in one glance on all 11 (gallery_c1). That is real and it came from the sheets.
- Overall mass and proportion of the big bodies: bear, boar, frog, owl torso (gallery_c1 hero views).
- Colour zoning follows the concept and borders sit on edges (stag rump patch and socks, owl bib, boar
  crest).
- Technical cleanliness: no pass-through, no floating pieces. An outsourcer would be glad of these gates.
- Honest history. RESULTS.md shows exactly where the loop stops paying (6.5).

**Why I would reject them (ranked)**

1. **The surface is triangle noise, not plane design.** The carved base is a decimated hull. Every
   triangle sits at a slightly different angle, so flat shading draws a random crackle over forms that
   should be three or four big planes. Giant 1_beauty hero: the chest and upper arm are fans of long
   triangles radiating from one vertex. Wolf 2_closeups front limb wire: the shoulder is a scatter. Frog
   gallery back34: dark green confetti. A human low-poly model has large coplanar quads and a hard break
   where the anatomy turns. The hand-built k3 bear (carve_detail_vs_k3, left) has cleaner planes than the
   c1 bear even though c1 scored higher.
2. **No topology for deformation.** No loops at shoulder, elbow, knee, hock, neck. Giant 4_posed
   attack_f010: the raised arm becomes one collapsed wedge. Giant 3_tech: purple fold-overs at both
   armpits and slivers across the chest. Wolf and stag 4_posed: the move frames lift a leg as a rigid
   stick from the hip; no knee, no hock action. Animators would refuse these.
3. **Limbs are not constructed.** Giant az090 and "hind limb" close-up: the two legs are one fused block
   with a plank foot; there is no thigh, knee or shin. Wolf az090: forelegs are straight tan posts, hind
   leg has a hint of hock only. Stag 2_closeups: columns with a dark sock, no knee or fetlock, the hoof
   is a wedge. Goblin az090: the reference's bent digitigrade crouch became a straight post on a slab
   foot. Character: tube arms and legs with no elbow or knee landmark.
4. **Faces have no appeal.** Eyes are the first thing a player looks at and they are the weakest part.
   Giant: a small amber chip in a black hole. Wolf: an orange flake with no socket or brow, reads blind
   from az000. Stag: a black slit. Goblin: round googly eyes with no brow, where the concept sells the
   whole character with an angry brow line and a long hooked nose (5_reference front pair). No model
   has an expression.
5. **Proportions drift from the concept towards "average".** Wolf 5_reference: head smaller, ruff a
   third of the reference volume, legs thinner, tail a thin blade instead of a brush; front view the
   model is a narrow pillar. Stag: neck mane gone flat, antlers are thin rods with identical nail tines.
   Goblin: ears and nose shortened, hands shrunk to claw fans. Each loss is small; together they remove
   the charm. Nobody checks proportion against the concept as a number.
6. **Fur, moss and feathers are stuck-on shards.** Wolf ruff (2_closeups ruff): about forty loose
   triangular cards. Wolf tail: fringe spikes. Giant moss: pebbles on a cap. Stag mane: tabs. In a
   shipped low-poly asset fur is the silhouette of the main mass: five to seven big stepped clumps
   modelled into the body, not cards.
7. **Triangles are spent in the wrong place.** Wolf: 1,286 body, about 800 in ruff, tail cards and 16
   claws. Giant: 2,994 total with a dense belt and loincloth fan (2_closeups belt wire) over a body with
   no knees. Goblin: skull is a fine dense dome while the forearm is a single plank.
8. **Colour is correct but dull or off.** Wolf lost the dark saddle contrast and reads beige. Goblin
   and frog are a saturated lime that the concept does not have. The giant is one mid-grey value from
   head to foot. No value grouping, no accent, eyes aside.
9. **Stiff presentation.** Every beauty shot is the bind pose. A-pose bipeds and square-standing
   quadrupeds with no attitude read as unfinished even when the model is fine.

## 2. Where the workflow is wrong or wasteful

1. **The carve is used as the mesh. It should be used as the sculpt.** A real team treats a hull, scan
   or sculpt as a guide and retopologises a clean cage over it. Decimate is the worst retopo there is:
   no loops, no planes, slivers. Giant NOTES r07-r18 is twelve rounds of booleans, sliver repair and
   seven re-locks fighting that mesh. Reasons 1, 2 and 3 above all come from this one decision.
2. **Nothing is signed off at blockout.** The only stage-1 checks are IoU, closed shell and a blind
   identity read. "Reads as a wolf" is a far lower bar than "is the wolf in the concept, with knees".
   The art director first sees the creature after stage 4, when rig and clips exist and every fix is
   expensive. In production the lead approves the grey blockout, with proxy colour, in a pose, before
   anyone details anything.
3. **The review order is upside down.** ART_DIRECTOR.md says look first at technical errors at close
   range, then silhouette. The result is visible in the notes: the giant's must-fix #1 to #3 are the
   belt, the moss tint and the loincloth thickness, on a creature with no legs. Close-ups make reviewers
   write tertiary notes. A lead reviews in this order: silhouette and proportion at thumbnail, primary
   forms, limb and face construction, colour blocking, pose, then details, then tech.
4. **The lock protects the wrong thing.** Stage 1 is frozen by vertex hash and stage 2 is held to IoU
   > 0.9 against stage 1. So a wrong base is protected from the fixes it needs (RESULTS: wolf legs, crab
   legs, bear, "blocked by the locked base, not by effort"). What a team locks is the approved
   silhouette and proportion, measured against the reference. Topology stays free until the rig test.
5. **The concept is not designed for the budget or for the build.** concepts_v2 are attractive, but
   they are "AI low-poly": naturalistic animals covered in hundreds of small facets, layered fur
   shards (wolf, stag mane), feather tiers (owl), spines and membranes (wyvern), five-finger hands
   (giant, goblin). That is a 6-10k triangle look. Asking a 1,500-triangle model to match it guarantees
   either shards or loss. It also contradicts BRIEF §1 (chunky, bigger head, thick limbs): the wolf,
   stag, bear and boar are realistic proportions.
6. **The sheets are not in a bind pose and are lit.** Giant and goblin sheets have arms hanging against
   the body and a hunched side view; the hull fuses arm to flank and both legs into a block. The wolf
   sheet's staggered legs carved six legs. Shading in the sheet contaminates the sampled palette.
   sheets_v2 still shows the giant and goblin with hanging arms.
7. **Hands, feet, eyes are reinvented per creature.** RESULTS says mitt fists, boot paws and bead eyes
   survived three repair passes. No studio models a paw from scratch for every quadruped; there is a
   parts library.
8. **No primary / secondary / tertiary discipline in practice.** The stages are named that way, but
   stage 1 already contains moss-border cuts and colour bisects (giant r11, wolf r03), and stage 3
   pieces are asked to supply secondary mass (the wolf's ruff). Secondary mass belongs in the body.
9. **Colour is never blocked early.** Palette appears in stage 3. A lead looks at a flat-colour
   blockout at thumbnail size on day one; value grouping decides whether the creature reads.
10. **Animation is judged in wireframe for fold-overs only.** Nobody judges pose appeal: the attack
    silhouette, the stride, the idle attitude. And the joints were never tested before detail went on.
11. **Scores are unanchored.** Absolute 1-10 from model judges moved 5.7 to 6.6 to 5.8 to 6.0 across
    different seats and packets. That is noise. A team compares against a target asset on the wall.
12. **Repair rounds and the team pass polish tertiary detail.** RESULTS already measured it: round 2
    adds 0.05, the team pass costs good builds a point. That effort belongs before the lock.

## 3. Ranked changes

**The three to do first are 1, 2 and 3.**

### 1. Retopologise over the carve: clean cage, carve as guide  [FIRST]
- **Change:** `carve_base` output becomes a hidden guide object. Stage 1 is a box-modelled cage built
  on the `J` skeleton with `ring/bridge/extrude` (as the k3 builds were), then fitted to the guide.
  Quads, 4-6 sided limbs, 6-8 sided torso, two to three loops at every joint, loops round eye and mouth.
- **Why:** This is how every sculpt becomes a game mesh. The k3 builds had usable topology and weak
  proportions; c1 has good proportions and unusable topology. Fitting the first to the second takes both.
- **How:** kit. (a) `hull_sections(guide, J)`: slice the guide at stations along each bone and print
  width, depth and centre per station, so the builder places rings from numbers instead of guessing.
  (b) `fit_to_guide(verts, guide, max_move)`: shrinkwrap along the ring's own plane. (c) gate: silhouette
  IoU of the cage against the sheet views, and a loop count per joint read from `J`.
- **Gain:** large. Clean planes, limbs with joints, deformation that works. Fixes rejection reasons 1-3.
- **Cost:** two kit functions and a rewritten stage-1 section of BRIEF; builds take about the k3 round
  count. Removes the boolean and sliver-repair rounds.
- **Verify:** rebuild giant, wolf, goblin, stag. Blind A/B against current c1 on beauty plus posed colour
  frames. Posed fold-overs and slivers should fall to near zero without repair code.

### 2. A blockout sign-off gate, and flip the review order  [FIRST]
- **Change:** new gate after stage 1, before any stage 2-4 work. Packet: grey and flat-colour-blocked
  model at 256 px thumbnail in four views, black silhouettes next to the concept's silhouettes, a
  proportion table, and three range-of-motion poses on a proxy rig. The reviewer may note only primary
  things: proportion, silhouette, mass separation, limb construction, head size, stance. Rewrite
  ART_DIRECTOR.md "look in this order" to: silhouette and proportion, primary forms, limbs and face
  construction, colour and value, pose, pieces, tech last.
- **Why:** Ninety percent of rejections are decided at blockout. A wrong blockout costs minutes to fix;
  the same error after rigging costs the whole build.
- **How:** review gate plus kit. `proportions(body, J)` prints head height / body height, leg length /
  body height, neck width / head width, limb thickness / length, and the same ratios measured from the
  sheet masks. Gate: each within 10% of the sheet, or a logged, intended exaggeration.
- **Gain:** large. Stops proportion drift (reason 5) and stops unbuilt limbs reaching detail.
- **Cost:** one kit function, one packet mode, one contract edit. One extra review seat per creature.
- **Verify:** the proportion table of the finished model stays within tolerance; final review notes no
  longer contain stage-1 items.

### 3. A parts library for faces, hands and feet  [FIRST]
- **Change:** kit generators with a few parameters each, authored once and approved once by the owner:
  eye set (socket, upper lid/brow wedge, eyeball, pupil, catchlight facet; brow angle is the expression
  control), canine paw, cat/bear paw with toe row, cloven hoof with fetlock, bird foot, three-finger
  hand, fist with a knuckle step, ear cup, horn/antler beam with tapered tines, tooth row.
- **Why:** These parts carry appeal and they are the parts the LLM fails at pass after pass. Teams reuse
  them across a whole roster; that reuse is also what makes a roster look like one game.
- **How:** kit functions (`parts.py`), attached to the cage's open limb ends or socket faces; builder
  picks parameters. tpa_opus_transfer §3.4-3.5 already describes the mechanics.
- **Gain:** large on close-ups and on the face at thumbnail size.
- **Cost:** the biggest authoring job here, about ten generators; each needs an owner taste pass.
- **Verify:** head and paw crops, blind A/B old against new; the "mitt", "boot", "bead eye" notes vanish.

### 4. Concepts designed to the budget, in bind pose, unlit
- **Change:** prompt and accept rules for concept and sheet: chunky proportions per STYLE.md; big flat
  planes, "about 800 triangles"; fur as five to seven large clumps; flat unlit colour, no shading or
  shadow; biped in A-pose with arms 40 degrees off the body, fingers apart, feet apart; quadruped
  standing square with near and far legs aligned; mouth closed; true orthographic.
- **Why:** The model can only be as good as the target. A concept that needs 8k triangles and a sheet in
  a relaxed pose create every downstream fight in giant NOTES and wolf NOTES.
- **How:** `gen_refs.py` prompt, plus `accept.py` checks: arm-to-torso gap in the front mask, leg count
  in the side mask, shading variance inside a colour region. Reject and regenerate.
- **Gain:** medium to large; also makes 1 and 6 simpler.
- **Cost:** prompt work and regeneration. Do it before building v2: the v2 giant and goblin fail the pose
  rule as they stand.
- **Verify:** carve needs no mask redraws or arm-gap booleans; sampled palette has no shading clusters.

### 5. Secondary mass in the body; hard caps on pieces
- **Change:** ruff, mane, tail brush, moss mantle, feather tiers are modelled into the cage as stepped
  clumps (extrude and offset of body faces), not as cards. Pieces are for hard, separate things: eyes,
  teeth, claws, horns, belts. Caps: body at least 70% of triangles, at most 12 piece shells besides
  repeated claws/teeth, no single-triangle cards.
- **Why:** Cards read as shards from every angle but one, and they flap rigidly in animation. Stepped
  mass is how every shipped low-poly wolf does a ruff.
- **How:** builder instruction plus a techqa count gate.
- **Gain:** medium to large on wolf, stag, boar, giant, owl, wyvern.
- **Cost:** small. **Verify:** wolf hero and az000 against the reference ruff volume; triangle share.

### 6. Colour blocking at blockout, value-checked, palette from the concept
- **Change:** palette taken from the unlit concept, then adjusted by rule: three value groups (dark,
  mid, light) with the head/face holding the highest contrast; one saturated accent; neighbours differ
  by a set minimum in value. Shown as a greyscale thumbnail in the blockout packet.
- **Why:** Value reads before hue. The giant is one value; the wolf's saddle disappeared.
- **How:** kit check in `paint` (value spread, neighbour contrast), reviewed in gate 2. Final palette
  choice remains an owner taste gate.
- **Gain:** medium. **Cost:** small. **Verify:** greyscale thumbnails still separate the masses.

### 7. Planar regions and angle-based normals
- **Change:** `planarize(body, angle)`: grow regions of faces within a small angle and flatten each to
  one plane (keeping seam and joint loops), and export custom normals that weld across edges under
  about 15 degrees and stay hard above. Big planes render as one facet.
- **Why:** Flat shading punishes any non-coplanar quad with a visible diagonal. Modellers flatten quads
  by hand for exactly this reason.
- **How:** kit function at the end of stage 2; becomes minor once change 1 lands, still useful.
- **Gain:** medium now, small after 1. **Cost:** small.
- **Verify:** facet count visible in the beauty render drops; blind A/B same mesh with and without.

### 8. Range-of-motion test at blockout, then generated clips with pose review in colour
- **Change:** proxy rig on the stage-1 cage; five fixed test poses (limb up 90, limb back, elbow/knee
  full bend, neck down, neck turn) gated on fold-over and volume loss before stage 2. Clips come from
  the gait and attack generator in tpa_opus_transfer §3.1. The packet shows the three key poses in
  colour and in black silhouette, not only wire.
- **Why:** Riggers test joints on the blockout so topology can still change. Animation appeal is judged
  on silhouette at the extreme frame.
- **How:** kit (`rom_test`), review packet change, one generator.
- **Gain:** medium for looks, large for motion. **Cost:** medium.
- **Verify:** attack extreme readable as a black silhouette; no rigid-stick legs in the move frames.

### 9. A presentation pose and one fixed look-dev
- **Change:** beauty shots use a hero pose (weight on one side, head turned 15-20 degrees, tail and
  ears off-centre), a warm key with a cool fill and a contact shadow on a mid-value ground, and a
  game-camera thumbnail row.
- **Why:** The owner judges by eye from the gallery. Bind poses on grey look unfinished.
- **How:** kit: `hero_pose` per body type in stage 4, lighting preset in `render_glb.py`. Do it once.
- **Gain:** medium, cheap. **Cost:** small. **Verify:** owner's eye on old against new gallery.

### 10. Anchored judging; lock proportion, not vertices
- **Change:** (a) replace absolute scores with pairwise comparison against a fixed set of anchor
  assets rendered in the same look-dev, plus a per-category pass/fail checklist; have the owner rank
  the current 11 once and check the judges agree with that ranking. (b) Proposal for the owner, since
  the 0.9 floor is owner-ratified: measure stage-2 IoU against the reference sheet, not against stage 1,
  and drop the stage-1 hash lock once the blockout is signed off.
- **Why:** A score that moves a point with the seat cannot steer. A lock that protects errors costs
  passes.
- **How:** judge harness and gate change. **Gain:** indirect but it stops wasted rounds. **Cost:** small.
- **Verify:** judge ranking correlates with the owner's ranking; no "blocked by the lock" residuals.

## 4. Revised workflow

0. **Style target on the wall.** Three to five anchor assets and STYLE.md proportions. Fixed look-dev.
1. **Brief.** Identity words, role, size, three clips, detail budget (primary masses, secondary clumps,
   pieces) written before any image.
2. **Concept** designed to the budget (change 4). Owner picks. Taste gate.
3. **Model sheet:** orthographic, bind pose, unlit flat colour. `accept.py` checks pose, leg count,
   view agreement. Reject and regenerate.
4. **Skeleton first.** `J` placed on the sheet; bone list fixed.
5. **Carve the guide** from the sheet. Print `hull_sections` and the sheet proportion table.
6. **Blockout cage** on the skeleton, fitted to the guide. Primary and secondary masses only, limbs
   with joints, fur masses stepped in. Parts library ends attached as proxies. Flat colour blocking.
7. **Blockout gate** (change 2): thumbnails, silhouettes against concept, proportion table, greyscale
   value check, range-of-motion test. One art-director seat, primary notes only. Up to two fix rounds
   here; this is where rounds are cheap. Sign-off locks proportion and silhouette.
8. **Plane pass.** Face planes, anatomy breaks, `planarize`. Loops only where a joint or a plane break
   needs one.
9. **Parts and pieces.** Final eyes, paws, hands, horns from the library; few hard pieces within caps.
10. **Colour.** Final regions on edges, value-checked. Owner taste gate if the palette moved.
11. **Rig, skin, generated clips, hero pose.** Posed review in colour and silhouette.
12. **Tech gates** (existing techqa, unchanged).
13. **Final review** in the new order, pairwise against anchors and against the concept. One repair
    round, pieces and colour only. Anything primary means the blockout gate failed: fix the gate.
14. **Owner packet:** gallery in look-dev, thumbnails, residual list.

## 5. What not to do

- **No more repair rounds or team passes on finished builds.** Measured: +0.05 and minus a point on
  good builds. Tertiary polish on a wrong blockout is the classic production waste.
- **No more tech gates.** The kit already catches more than most outsource QA. The problem is looks.
- **Do not tune carve parameters, sliver repair or booleans further.** Stop using the hull as the mesh.
- **Do not raise the triangle budget.** Shipped assets in this style sit at 800-1,500. More triangles
  give more noise, not more design.
- **Do not chase the concept's small facets, fur shards or feather tiers.** Simplify the concept.
- **Do not add more judge seats or more score decimals.** Anchor the comparison and ask the owner once.
- **Do not hand-build hands, paws and eyes per creature again.** Three passes proved it does not land.
- **Do not animate before the blockout is signed off,** and do not judge animation from wireframes.
- **Do not start the v2 builds on the current pipeline.** Change 1, 2 and the sheet pose rule first;
  otherwise v2 repeats c1 with nicer pictures beside it.
- **Do not adopt a spline/SDF loft generator for bodies.** It brings back the tube look the owner
  already rejected; take only its clip generator and part generators.
