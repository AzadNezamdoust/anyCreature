# Creature workflow review: a lead character artist's read (Fable 5.1, 2026-10-03)

Read: WORKFLOW.md, BRIEF.md, ART_DIRECTOR.md, REPAIR.md, RESULTS.md, refs/SHEETS.md, refs/BUILD.md,
kit/carve.py docstring, research/tpa_*.md. Looked at: gallery_c1.jpg, team_pass.jpg,
carve_detail_vs_k3.jpg, refs/concepts_v2.jpg, refs/sheets_v2.jpg, and the full packets plus
NOTES.md and program structure of abc/c1/bear (quadruped), goblin (biped), wolf, owl.
No judge key files were opened. Everything below is production judgement, not theory.

## 1. Verdict on the current output

In a studio review these would be "good blockouts, not assets". Identity reads on all 11 at
thumbnail; nothing survives a close-up or a turntable. 6/10 is the right number. The three
that come closest to shippable are owl, boar and bear; the farthest are character, wolf and crab.

### What is working

- **Identity and proportion.** Carve + detail puts the masses where the reference puts them.
  Bear az090 (5_reference) and goblin az000 land the silhouette and the stance. That is the hardest
  thing to get out of a procedural pipeline and it is solved.
- **The face kit on the goblin and owl.** Big eyes under a brow, a mouth, ears: the goblin hero
  view reads as a character, not a prop. The owl's disc and beak carry the whole model.
- **Colour maps follow the reference.** Wolf saddle/belly/tan legs, owl breast, bear muzzle and bib.
  Palettes are mostly sane in value; the owl's four browns are a good commercial palette.
- **Hygiene.** No holes, no floating pieces, no z-fighting, drift gated, three looping clips and a
  valid glTF on every build. The packet (beauty, close-ups, tech, posed, reference) is better than
  what most outsourcing vendors send.

### Why these would be rejected for a shipped stylised low-poly game

1. **The surface is decimated triangle soup, not designed planes.** Flat shading turns every
   triangle into a visible facet, so the body reads as crumpled foil. Bear back34 and az090
   (1_beauty): the flank and rump are 60+ random facets catching light at different angles.
   Goblin back34: the torso is a lumpy sack. Wolf hind-limb wire (2_closeups): triangle soup with no
   loop anywhere. The bear builder spent six rounds writing a k-means `facet()` denoiser to fake
   planes on a locked tri-mesh; that is a symptom, not a fix. A Synty/Quaternius body is 20-40
   quads per side with every edge placed on purpose.
2. **Extremities are mitts, boots and paddles.** Bear front limb (2_closeups): a boot with five
   needle claws stuck on the front. Goblin hind limb close-up: a flat paddle with cone claws. Wolf
   az000: four tan columns ending in a bevel. Owl hind limb: stick toes on a block. Character: a
   knob with a thumb. Hands and feet are the first place an art director looks after the face,
   because they are what a player sees in every animation.
3. **Fur and feathers are glued-on cards.** Wolf ruff (2_closeups, ruff piece): a scatter of flat
   shards hovering off the neck; in 4_posed attack_f016 they fly apart. Giant moss: plates on top of
   the head. In a shipped low-poly asset the ruff, mane and crest are IN the base silhouette (a zigzag
   loop on the neck), and separate pieces are reserved for 2-6 bold shapes (tusks, antlers, a tail
   tip). A card stack never reads as mass.
4. **No pose, no appeal.** Every beauty render is the rest pose with a 1.5-degree breathe. Character
   az090: a bald figure at attention. Goblin az090: hunched because the hull is hunched, not because
   anyone chose it. Wolf hero: a stuffed animal. Bear attack_f010/f020: the body rears a little; it
   does not read as a bear attacking at thumbnail. Commercial packs sell on the idle pose and the
   attack silhouette, and those are designed, not keyed as numbers at the end.
5. **Faces stop halfway.** Bear: dot eyes with no lid, no brow shelf, no mouth line (az000); it is a
   plush toy. Wolf az000: the head sinks into the ruff ("head_merged" in the builder's own orbit
   advisory for every pass). Frog: eyes are yellow boxes. Owl: the disc rim is a flat plate. The
   goblin's eyes work because a builder spent eleven rounds on them; that is the budget a face needs
   and only one creature got it.
6. **Colour borders zigzag and the palette is sampled from a lit render.** Bear hind leg sock
   (az090, before the team pass), frog spots, raven wings: borders cross triangles. `colour_from_sheet`
   samples a shaded image, so the clusters carry lighting and come out grey (bear dark fur #403832,
   fixed by hand to #4a3222). Borders must sit on loops cut for them, and the palette must come from
   the concept, not from pixels.
7. **Deformation has no edge flow.** Joints bend across whatever triangles the decimator left.
   Goblin 4_posed attack_f006: the arm folds at the shoulder with no loop; 6 rounds went into weight
   hacks (`arm_clean`, `smooth_weights`) because the hand was fused to the knee by the hull. A rigger
   would send this back before touching it: three loops per joint, in the base, before weights.

The owner is right that it is "not perfect yet", and the measured 6/10 plateau is not a repair
problem. The thing being repaired is the wrong mesh.

## 2. Where the workflow is wrong or wasteful compared with a real character team

**The order of operations skips retopo.** A real pipeline is: blockout (proportions, joints) →
form (primary/secondary masses) → retopo (quads, loops at joints, plane breaks where anatomy turns,
borders where colour changes) → colour/UV → rig → animation. Here the carved hull IS the final
topology. Stage 2 then tries to design planes on a triangle soup with vertex moves and bisect cuts,
and stage 3 compensates for missing secondary form with pieces. The retopo step is where the
hand-made look is made; it does not exist.

**The lock protects the wrong thing.** `stage1_lock.json` hashes connectivity of a decimated hull.
In production you lock proportions and silhouette (a signed-off blockout), and topology stays free
until retopo is signed off. The IoU > 0.9 against stage 1 then forbids exactly the secondary work
a sculptor does next (the wolf legs, the crab legs, the bear's "no silhouette room left"). Three
repair passes were spent fighting a gate that protects a shape nobody signed off as a design.

**Sign-off happens too late and on the wrong material.** The art director sees the model first
after stage 4, in colour, rigged, posed. By then a note about the hind leg costs a stage-1 unlock, a
re-carve, a re-run of stages 2-4 and a drift fix. A lead signs off three times: grey blockout
(silhouette + proportion, 3/4 view, turntable), grey retopo wire (plane design, loop placement,
budget), then colour + pose. Each gate is cheap and each catches a class of error before it
compounds. Nothing in the kit asks "does the grey model look designed?" before colour.

**The reference is used as a silhouette, not as a design.** The GPT sheet is itself a smooth-shaded
render with sub-D-style faceting; the carve copies its inflation (goblin's sack torso, bear's blobby
thighs) and its disagreements (wolf: six legs from staggered legs; goblin: ears read from the side
view swept back). No 3/4 view is ever referenced; no plane study; no real anatomy reference for
hocks, knuckles, lips. A concept artist would deliver a model sheet with plane breaks drawn on it.

**No primary / secondary / tertiary pass.** Primary comes from the carve. Secondary (muscle masses,
the stop, the brow shelf, the hock, the knuckle row, the ruff mass) has no stage; it is spread over
stage-2 nudges and stage-3 cards. Tertiary (claws, teeth, eyes) is done well but sits on an
unfinished secondary, which is why claws on a boot read worse than no claws.

**Hands, feet and faces have no construction method.** Each builder reinvents a paw. The goblin
builder spent 11 rounds on eyes, 8 on hands; the bear builder got dot eyes in 2. A team has a
template: paw = wrist block, palm wedge, toe row of 3-5 boxes, claw per toe; face = brow ridge,
socket, stop, nose block, jaw line, mouth cut. These are the same on every creature of a body plan.

**Colour blocking is after the fact.** Borders are cut into a locked tri-mesh with `bisect_plane`;
the palette is clustered from a lit image. Colour blocking belongs on the retopo wire (the loop IS the
border) with the palette taken from the concept in flat light.

**Pose and animation are an afterthought.** The rig is built from `J` after the model is done; clips
are FK degree tables typed by hand (bear.py stage4: `A, H = 14, 12`); no foot planting, no
anticipation/hit/recover on attack, no idle that shows character. The beauty render is "idle frame 1",
which is rest. The hero pose is never designed, and it is what sells the asset.

**The review loop measures the wrong thing and over-trusts numbers.** Twelve tech gates, every one
useful for hygiene, zero for appeal. Reviews go to a repair round that moves claws and tongues
(RESULTS: "trade one flaw for another") while the base stays locked. Scores from two models with no
anchor drift by a point between seats. Builders over-claim; a verifier was added, correctly, but it
checks notes, not look.

**Waste, in order of cost:** stage-1 overruns fighting the hull (goblin: head replaced by hand, 15
rounds; wolf: 14 rounds, one lock withdrawn); weight hacks for topology defects (goblin 6 rounds);
repair rounds 2 and 3 (measured at +0.05); the team pass on good builds (-1 point on crab, frog,
stag); and `facet()`-style denoisers written per creature.

## 3. Ranked changes (max 10). Stars mark the three to do first.

| # | change | why (production) | who / where | visual gain | cost | verify |
|---|---|---|---|---|---|---|
| **1 ★** | **Add a retopo stage between carve and lock.** The carved hull becomes a shrink-wrap target only. A kit function `cage(J, plan)` builds a quad cage from the joint table (torso 6-8 sided rings, limbs 4-6, 3 loops per joint, a zigzag loop where a ruff/mane/crest sits, a face block with brow/stop/jaw rows), shrink-wraps it to the hull, and that cage is what gets locked. | Every hand-made low-poly asset is a quad cage with intentional edges; flat shading shows the cage. Decimation can never produce a designed plane. Everything in finding 1, 3 and 7 is this one missing step. | new kit module `kit/cage.py`; BRIEF stage 1 = carve → cage → lock; builder adds body-plan loops | largest available: removes "crumpled foil", gives planes, loops for weights and colour borders | 3-4 days kit, then builds get shorter (no `facet()`, no weight hacks) | quad share > 85% of base faces; dihedral histogram: < 10% of edge length in the 4-18° "speckle" band (the bear's own `speckle()` measure); wire close-up reads as a cage; weights need no post-fix |
| **2 ★** | **Blockout sign-off gate before the lock, in grey, from hero 3/4 + side + front + turntable.** One art-director seat answers three things: identity, proportions vs reference, "is this a design or a scan?". Go/no-go. Replace the IoU-vs-stage-1 gate with IoU-vs-reference plus a signed list of permitted deviations (e.g. "legs may widen 15%"). | The cheapest moment to kill a bad base is before anything is built on it. Every "blocked by the IoU floor" item in RESULTS is this gate missing. | WORKFLOW step 3a; `run.py --signoff` renders the grey sheet; AD contract gets a 10-line blockout section | removes the plateau cause: bases that nobody designed get rebuilt at a few minutes, not 3 passes | 0.5 day kit + one AD call per creature | no creature reaches stage 2 without a logged PASS; stage-1 unlocks after sign-off drop to zero |
| **3 ★** | **Construction templates for extremities and faces (`kit/parts.py`).** `paw(wrist, toes, claws)`, `hand(wrist, fingers, thumb)`, `foot(ankle, toes)`, `eye(socket, r, depth≤1.3r)`, `face_block(brow, stop, nose, jaw, mouth)`. Low-poly (4-6 sided), parameterised, built in the cage so they are base topology, not pieces. | Hands, feet and faces are where reviewers look second and third; today each builder reinvents them and most run out of rounds. A team has one way to build a paw. | kit; BRIEF stage 1 says use them; builder sets parameters | high: mitts/boots/paddles disappear on every creature at once | 2-3 days | close-up packet: a toe row and a palm plane on every limb; eye front within 1.3r of skin; a mouth line on every face; AD "extremity" notes drop to minor |
| 4 | **Design the idle and attack poses before stage 3, and review in them.** Builder writes a one-line pose intent per clip (weight, lean, head, what the attack is), keys the extremes first, and the beauty render uses the designed idle. Add a posed-silhouette thumbnail (black on white) to the packet. | Commercial packs sell on the pose. Rest pose plus a breathe is what reviewers score as "procedural". | BRIEF stage 4 moved to "4a pose intent" after the lock, "4b clips" last; packet gets `6_silhouette.jpg` | medium-high on appeal, the owner's stated axis | 0.5 day kit, 1-2 builder rounds | AD scores the posed silhouette tile; attack reads at 128 px |
| 5 | **Fur, feathers and crests go into the cage silhouette; cards capped at 6 pieces per creature.** The zigzag loop in #1 carries the ruff/mane/disc rim; pieces are reserved for tusks, antlers, tail tip, horns. | The wolf lost blind votes to its own ruff shards twice. Mass reads from the base outline, never from cards. | BRIEF stage 3 rule; a kit count gate on piece shells | medium; fixes the wolf, raven, giant, owl disc | 0 kit (after #1) | piece count ≤ 6 (excluding eyes/claws/teeth); ruff reads in grey silhouette with pieces hidden |
| 6 | **Palette from the concept, borders on cage loops, a three-value plan.** Drop `colour_from_sheet` clustering as the source; sample the concept in flat regions by hand (builder picks 5-7 hex values with a note: light/mid/dark + accent), and the cage has a loop at each border. | Sampled-from-render palettes go grey; zigzag borders are the second most visible tell after facets. | BRIEF stage 3; kit `paint_by_loop()` | medium, cheap | 0.5 day | no border crosses a face (kit check); palette value spread ≥ 40% L between light and dark |
| 7 | **Plane-design contract per body plan, with a plane-map render.** A checklist of required plane breaks (brow, cheek, jaw, shoulder blade, rib cage, belly tuck, hip, knee/hock, hock-to-cannon) and a packet tile that colours faces by plane cluster, so a reviewer sees planes, not shading. | Planning planes is the craft of low poly; today it is one line in BRIEF §2 with no check. | BRIEF stage 2 table; `run.py --review` adds `7_planes.jpg` | medium | 1 day | each required break is a visible dihedral > 20° in the plane map; AD "form" notes drop |
| 8 | **Gait and attack generators with a foot-slide gate.** `gait_clip(rig, J, plan)` plants feet (IK, baked to FK), `attack_clip(style)` with anticipation/hit/recover; techqa adds foot slide and ground penetration. (The tpa_opus_transfer.md plan 3.1 is right; keep it after the mesh is fixed.) | Hand-typed FK degree tables never plant a foot; animators reject sliding feet first. | kit `gait.py`; BRIEF stage 4 | medium on clips, low on stills | 2-3 days | foot slide < 2% of leg length in stance; attack extreme differs from idle by a silhouette IoU < 0.8 |
| 9 | **Calibrate the review.** Give each AD seat an anchor board (three CC0 Quaternius/Synty creatures at 8, one shipped engine creature at 4) and make the score relative. Collapse the tech readout in the packet to one PASS line. Reviews ask two questions first at thumbnail: "what is it" and "would you buy it". | Uncalibrated scores drifted a point between seats; reviewers were reading heatmaps as geometry. Leads review the picture, QA reviews the numbers. | ART_DIRECTOR.md; `judge/anchors/` | reliability of the gate, not the asset | 0.5 day | seat agreement within 0.5 on the anchor board before a real review |
| 10 | **Fix the reference brief, not the carve.** Ask the sheet generator for a 3/4 hero view and a side view with plane breaks drawn ("low-poly, flat-shaded, 300 triangles, visible facets"); reject sheets with sub-D smoothness or view disagreement > 20%; keep the 2x2 only for the carve. | The current sheets are smooth renders; the carve copies their inflation. A model sheet shows planes. | `refs/gen_refs.py` prompt + `accept.py` rule | medium on torso and face planes | 0.5 day + a sheet batch | sheets_v3 pass a blind "is this a low-poly model" read; carve IoU unchanged, retopo rounds drop |

Do #1, #2, #3 together on three creatures (bear, goblin, wolf) and run the existing blind A/B
against c1. Expect 6 → 7.5 on those three; if it does not clear 7, stop and look at the wire, not
the notes.

## 4. Revised workflow, as I would run the team

1. **Brief + concept (unchanged).** Add the pose intent line for idle and attack, and the three
   values of the palette, to the brief before any image exists.
2. **Reference sheet.** 2x2 for the carve, plus one 3/4 hero in flat shading with plane breaks
   (#10). Fit and direction audit as now. Reject on view disagreement.
3. **Blockout = carve + joints.** `carve_base` for the hull; builder writes `J` with a source note
   per joint and overlays it on side/front (`--joints`). Grey only.
4. **Blockout sign-off (gate A).** AD seat, grey, hero 3/4 + side + front + turntable: identity,
   proportions vs reference, design-vs-scan. Permitted-deviation list written here. Nothing proceeds
   on a FAIL; a FAIL costs one re-carve or a hand-edited mask, both minutes.
5. **Retopo = cage.** `cage(J, plan)` quad cage, shrink-wrapped to the hull; builder places loops for
   joints, plane breaks from the body-plan checklist, border loops for colour, a zigzag loop for fur
   mass, extremity and face templates (#3). This is the stage that gets most builder rounds (8-12).
6. **Retopo sign-off (gate B).** Grey wire + plane map, close-ups of face, a hand/paw, a foot. Quad
   share, speckle share, loop-at-joint count, triangle budget. AD answers: "are the planes designed,
   will it deform?" This is the lock. Hash the cage.
7. **Secondary + colour.** Vertex moves and flattens on the cage; palette from the concept; paint by
   loop. Pieces capped at 6, in the signed-off silhouette.
8. **Pose.** Rig from `J`; key the designed idle and the attack extreme first; render the posed
   silhouette tile. Quick look by the orchestrator: does the attack read at 128 px?
9. **Clips.** Gait generator for move, attack with anticipation/hit/recover, idle with weight shift.
   Tech QA runs here, one PASS line in the packet.
10. **Look review (gate C).** Two calibrated seats, blind, anchored, thumbnail first. Verdict SHIP/
    FIX with at most 5 notes, each tagged to gate A, B or stage 7-9. A note tagged A or B means the
    creature goes back to that gate, not to a repair round.
11. **One repair round, then stop.** Verified by the independent check (keep the Sonnet verifier).
    Residual to the owner. No K=2, no team pass unless the look score is ≤ 5.
12. **Promote.** Any note that both seats raise on three creatures becomes a checklist item at gate A
    or B, not a new techqa gate.

Budget guide per creature: carve 2 rounds, cage 8-12, secondary + colour 4, pose + clips 4, repair
≤ 6. Roughly today's total, with the rounds moved from fighting the hull to designing the cage.

## 5. What NOT to do

- **More repair rounds on the current meshes.** Measured: round 2 is +0.05. The base is the limit.
- **More tech gates.** Twelve gates all pass and the score is 6. The next gate will not move the look.
  Promote findings into the sign-off checklists instead.
- **Per-creature denoisers, "facet()" k-means, bilateral normal smoothing on a tri-soup.** They
  fake planes by shading and cannot be seen in the wire; a cage makes them unnecessary.
- **Fur cards, shard ruffs, moss plates as the fix for missing mass.** They read as glued on at every
  angle and fly apart in poses. Mass goes into the silhouette.
- **Metaballs, SDF unions, remeshed smooth bases, decimating a high-res mesh.** All of them produce
  the lofted-tube or crumpled-foil look the owner rejected; planes come from a cage, not from a filter.
- **Chasing higher IoU against the GPT sheet.** The sheet is a smooth render with disagreeing views;
  past 0.9 you are copying its mistakes (goblin's sack torso, wolf's six legs).
- **Three-model team passes on builds that already score 7.** Measured: -1 on crab, frog and stag.
  Use it only below 5, and compare before/after blind as now.
- **Colour clustering from a lit image.** Grey palettes, lighting bands split into clusters. Pick
  hex values from the concept.
- **Scoring at full resolution first.** Reviewers start reading triangles. Thumbnail first, then
  close-ups for defects.
- **Letting builders self-report "done".** Three passes out of three had false dones. Keep the
  independent check; make it look at the packet, never at the notes.
- **Spending kit time on animation quality (IK, gait tables) before the mesh has edge loops.** A gait
  generator on a tri-soup still folds the shoulder; do #1 first, #8 after.
- **Growing BRIEF.md.** It is 360 lines and builders run out of rounds. Move the checklists into the
  two sign-off gates and keep the brief to the contract.
