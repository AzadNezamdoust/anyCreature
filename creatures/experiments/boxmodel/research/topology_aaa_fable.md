# Topology standard for the stage-1 cage (AAA stylised low-poly), and how to get there

Seat: senior character modeller (Fable 5.1). Evidence: `abc/c3/{goblin,wolf,bear}/blockout/` (wire,
topology, density, aspect, ROM, guide), `form_c3_locked.jpg`, each `reference/sheet.png`, the three
build programs, `kit/bmkit.py` (`topology`, `TOPO_LIMITS`, `cage_gates`), `kit/carve.py`
(`part_budget`, `ring_points`, `part_rings`), BRIEF "Topology rules".

The owner's read is right. These cages pass every gate and would be sent back by any lead on day one.
The gates measure hygiene (quads, no fans, no poles in bands, loops exist). They do not measure the
two things a lead looks for: **does the edge flow describe the anatomy** (a shoulder, a glute, a brow,
a jaw) and **do the plane breaks sit where the form breaks**. Both are absent, and both are absent for
one structural reason, not three creature-specific ones.

## 1. Verdict

### The root problem, common to all three

Every part is an N-sided ring stack lofted down a bone axis and bridged; limbs sprout out of one or two
torso faces. That construction has five consequences a professional sees at once:

1. **One side count per part, from root to tip.** A 6-sided arm has the same six lengthwise lines on
   the deltoid, the elbow, the forearm and the hand. The deltoid cannot swell as a cap, the forearm
   cannot flatten into a palm, the thigh cannot carry the glute. Side count is the only resolution knob
   the method has, and it is global.
2. **No lengthwise line crosses a part boundary.** The arm's lines stop at the socket faces; the
   torso's lines run past them. Nothing flows pec -> deltoid -> triceps, or sacrum -> glute ->
   hamstring, or trapezius -> withers -> scapula. Those diagonal/wrapping loops are what make a
   shoulder or a hip read as a shoulder or a hip; a ring stack can only make a sausage joined to a can.
3. **The socket is whatever two torso faces happened to be there.** A 1x2 block gives a 6-vert root,
   vertical on the flank (goblin, wolf). The shoulder loop should be a tilted ellipse whose top sits
   on the shoulder crest / scapula and whose bottom sits in the armpit. The current root loops pass
   over the joint only because the gate asks them to; they are not shaped.
4. **Ring vertices sit at fixed angles on a superellipse** (`ring_points`, `tring`, `sring`), not on
   the corners of the form. For a flat-shaded asset the lengthwise edges ARE the plane breaks. When they
   land at 20/42/66 degrees instead of on the brow shelf, the cheekbone, the iliac crest or the chest
   keel, the shading shows soft tubes with random facets. This is why the owner says medium-radius
   forms (head, arms, legs) are weaker than the concept even where the profile RMS passes: the
   profile is right, the planes are wrong.
5. **The face is a grid pasted inside a ring**, with eyes and mouth as 4- and 6-vert insets. A face
   needs its own loop map (eye loop, mouth loop, the mask loop joining them, a jaw line); it cannot be
   derived from a loft.

Where the current approach is fine and should be kept: tubes that are tubes (neck, shin, forearm,
tail, muzzle) are correctly made from rings sized at guide stations; the `part_budget` idea (rings
only at ends, joints, one mass per bone) is the right density rule; the ROM proxy rig is the right
test; building on the left half with a mirror seam is right.

### Goblin (1,128 tris)

- **Head / face.** Five lofted rings front to back with the brow, temple, cheekbone and jaw as fixed
  ring vertices (T/A/B/C/D/E/U): the jaw is therefore a ring of vertices going round the head, not an
  edge chain from chin to ear, so there is no jaw plane and the head reads as an egg with a face
  decal. The eye is a 4-vert inset in one quad: it can never carry a lid or a brow shelf. The mouth is
  a 6-vert sunk loop with two quads inside. No loop joins eye to mouth (the nasolabial/mask loop), so
  the cheek is a flat quad from eye corner to jaw. The nose is the one feature with its own loops and
  it is the best thing on the model. The concept's heavy brow over a hooked nose, the sunken cheeks and
  the jutting lower jaw are all missing as planes.
- **Neck.** Three loops at 0.25 x width: count fine. The neck leaves from the inner column of the
  top 2x2 grid: the trapezius slope and the clavicle are one quad each, so the shoulder girdle is a
  flat shelf with a stalk on it.
- **Shoulder / deltoid / scapula.** The arm is extruded from 1x2 side faces under the shoulder ring:
  six sides, a vertical socket on the flank, no deltoid cap (the first arm ring is the socket's own
  row). Twelve rings down the arm (`ARM_T`) at 0.4-0.6 x width: visibly a ring stack in the hero wire.
  No scapula: the back is a smooth superellipse.
- **Chest / belly / spine.** 16-sided superellipse rings; the belly dome is a 4 mm offset on two
  vertices. The concept has a pot belly with a clear belly plane and a chest-to-belly step, a
  sternum line and a lateral plane change; none exist as edges.
- **Hip / glute.** Leg from the bottom grid's outer column (1x2 again): six sides, the root runs
  crotch -> groin -> iliac which is the right intent, but no loop wraps the glute from the sacrum to
  the hamstring and the pelvis bottom is a flat 2x2.
- **Elbow / knee / ankle.** Three rings each, evenly spaced, square to the bone: fine for a bend test,
  but the knee is a flat-fronted 6-sided box with no patella plane and the elbow has no olecranon.
- **Hands.** The arm's rings continue, twisted 45-65 degrees and curled: a hook, not a hand. The
  concept has a broad palm, three long fingers and a thumb; at stage 1 that needs a flattened palm
  (8-ring, 4 back / 4 palm) and a thumb block, fingers later. 328 tris in the arm (29% of the body)
  are mostly spent here and in the ring stack.
- **Feet.** Five 6-sided rings forming a loaf: no ball-of-foot ring where the toes bend, no heel plane.
- **Ears.** A 4-sided blade from one temple face: fine as a blade, but the root is a single quad so
  the ear does not flow into the skull, and the inner cup of the concept's ear is absent.

### Wolf (864 tris)

- **Head.** Muzzle is a 6-sided tube out of the centre of the face cap: a square snout with no top
  plane / side plane break and no nose block. Eye loop absent. The brow is a ring; the cheek ruff
  (the wolf's identity mass in the concept, front and side) is not a mass with its own loops but a
  slightly wider ring. Ears are two-tier blades from single faces.
- **Neck.** Two loops at 0.28 x width on a 0.45 m neck: a head nod bends across one band of quads.
- **Shoulder / withers / chest.** Fore limb from a 1x2 lower-flank patch "facing down and out":
  the socket is on the underside of the body, so there is no scapula, no withers, no point of
  shoulder; the chest keel is the mirror seam. Torso 144 tris at density 0.73 against legs at
  1.19 / 1.26: the flank is four giant quads, the legs are dense sticks.
- **Hip / haunch.** Same patch extrusion: the thigh is a column from the flank bottom. The concept's
  broad thigh with the stifle forward and the rump curving into the tail is a tube with a collar.
  One 18:1 face behind the stifle.
- **Elbow / stifle / hock.** Three rings, tightened on the flexion side: the one topology decision in
  c3 that is actually right (the notes found folds drop when the flexor-side rings converge). Wrist two
  rings at 0.77 x width: the paw hinges on one band.
- **Paws.** Three-ring boxes with valence-3 corners: no toe row, no pad plane.
- **Tail.** 6-sided out of the rump cap's middle face: no sacrum flow, tapers like a rope where the
  concept has a brush with its mass two-thirds along.
- **Belly.** The tuck is read by ring sizes but there is no lengthwise belly line other than the seam.

### Bear (860 tris)

- **Torso.** The bear is all torso and the torso has the least topology: density 0.66, the hump is
  four quads across, the belly line is the seam. Head density 1.8 with 96 faces in the muzzle: backwards
  for this animal.
- **Head.** Three masses read (cranium, cheek step, muzzle) which is the right idea, but the cheek
  step is a ring step, the ears are missing from the cage (they are in all four reference views and
  they are the bear's silhouette cue), and the muzzle closes to a point.
- **Neck.** Two rings at 0.17 x width on a 0.56 m neck, and the join is a collar ledge.
- **Shoulder / hip.** 8-vert roots (good) closed by 5:1 to 7:1 kite quads converging on the valence-5
  poles above the shoulder and hip; in the swing pose they fan across the flank. ROM 4.3% of area,
  the worst of the three, and it is all at the roots and the armpits.
- **Limbs.** Straight columns front and side; the concept's fore limb narrows at the wrist and spreads
  into a broad paw. Elbow and wrist two rings each; paws are sloped wedges.
- **No eye or mouth loops declared.**

## 2. Target topology spec

Written as a template a program builds. Counts are for the stage-1 cage; stage 2 adds partial
loops on flats. All counts are full-body (both halves); the seam carries the odd vertex.

### 2.1 Three construction rules that replace "ring stack of tubes"

- **Cap rule.** An n-sided ring is closed by an (n/4) x (n/4) quad grid (8 -> 2x2, 12 -> 3x3,
  16 -> 4x4). Its four corner vertices are the only valence-3 poles that rule produces, and they are
  the box corners of the form (skull top, pelvis bottom, paw tip, hand tip).
- **Socket rule.** A limb, a neck, a muzzle, a tail or an ear leaves its parent through a 2x2 block
  of the parent's quads (an 8-vert boundary -> 8-sided child) or a 1x2 block (6 -> 6-sided ear /
  stub tail). Never from one face. The block's four corners become valence-5 poles ON THE PARENT, one
  face away from the child's first ring; the child's eight lengthwise lines all run on into the
  parent (flow = 1.0). The socket loop is then **shaped**: its vertices are moved on the parent's
  surface so the loop is a tilted ellipse (see per-joint layout below).
- **Corner rule.** A ring's vertices sit on the corners of the guide section at that station, found
  numerically (polyline simplification of the section to n vertices), not at fixed angles. Consecutive
  rings are matched by nearest angle with twist <= 15 degrees so the lengthwise lines stay straight.
  A named lengthwise line (sternum, lateral line, spine flank, iliac crest, chest keel, belly line,
  withers) is pinned to a named corner of the section where the section has one.

With these three rules there are no reductions in the cage: counts are reconciled by the cap rule and
the socket rule, never by diamonds or 3-to-1 kites. Reductions belong to stage 2 (partial loops
ending on flats).

### 2.2 Loop map, biped (goblin type)

Torso, 16 sides, 8 rings, bottom to top: pelvis bottom (4x4 cap, the crotch is the cap's central
column), hip socket band (2 rings), waist, belly, chest, armpit band (2 rings), shoulder crest. The
top is a 4x4 cap: its central 2x2 is the neck socket (8-sided neck), its outer columns are the
trapezius slope. Named lengthwise lines per half (8 interior + seam): sternum/belly seam, rectus edge,
pec-side corner, lateral line, back-side corner, scapula/erector line, spine flank, (seam). The
rectus edge and the pec-side corner are where the pot belly's plane and the chest step live; the
lateral line is the front/side plane break.

Shoulder: socket block = columns {pec-side corner, lateral, back-side corner} x rows {chest, armpit
band}. Shape: top of the loop raised onto the shoulder crest ring (the trapezius), bottom at the
armpit, front vertex on the pec edge, back vertex on the scapula line; loop normal 30-45 degrees off
the arm axis. Poles: valence-5 at the four block corners (clavicle, scapula top, pec-armpit,
lat-armpit). Arm, 8 sides, rings: deltoid cap (wider than the socket), upper-arm mass, elbow x3,
forearm mass, wrist x2, palm x2 (flattened: 4 back, 4 palm, width 1.6 x depth), knuckle cap 2x2.
Thumb: 4-sided from one palm-side face, 2 rings. Fingers: stage 3 pieces.

Hip: socket block on the pelvis bottom cap, columns {outer two} x rows {hip band}: the loop's top on
the iliac crest, back on the glute, inner at the crotch, front on the groin; poles at the iliac,
sacrum-glute, groin and crotch corners. The glute: the back-side corner line and the spine flank run
down into the hip band's back vertices so one edge chain goes sacrum -> glute -> hamstring. Leg, 8
sides: thigh mass, knee x3, calf mass, ankle x2, foot: the 8-ring turns horizontal: heel ring, arch,
ball ring (where the toes bend), toe cap 2x2. The ball ring is mandatory; toes are stage 3.

Neck, 8 sides, 3 rings between the trap cap and the skull socket, spacing 0.3 x width. Head: a skull
ring stack of 16 (3 rings: nape, crown, brow) closed with a 4x4 top cap, and in front of the brow ring
the **face mask**, a fixed 2D quad template (one authored connectivity, fitted per creature):
- eye loop: 8 verts, with one concentric socket loop outside it (16 verts around both eyes' sockets
  is not needed; one 8-loop per eye plus the mask loop);
- mouth loop: 8 verts (corners, upper/lower mid, two per lip);
- mask loop: brow shelf -> temple -> cheekbone -> jaw -> chin, joining the eye and mouth loops;
  this is also the jaw edge chain (dihedral 25-60 degrees for the flat-shaded jaw plane);
- nose: 8-sided (or 6 on a small nose) out of the 2x2 block between the eyes and the mouth, 3 rings
  + a tip cap, the goblin hook kept;
- poles: valence-5 at the outer eye corners (temple), valence-3 at the inner eye corners, valence-5
  at the mouth corners, one valence-3 under the chin. Head pole budget <= 12.
The mask's border has 16 verts and welds to the brow ring; below the chin the mask's bottom row and
the skull's bottom ring close with the neck socket (central 2x2 of a 4x4 under-cap).
Ears: goblin blade, 1x2 block on the temple (6-sided), 4 rings to the tip, closed by a 1x2 cap; a
cupped ear (bear) is a 1x2 block, 2 rings, with the front row pushed in for the cup.

### 2.3 Loop map, quadruped (wolf / bear type)

Torso, 12 sides (wolf) or 16 (bear, giant; anything whose body is the character), 9-10 rings,
rump to withers: rump cap (3x3 or 4x4; its central 2x2 is the tail socket for a brush tail, 1x2 for a
stub), hip band (2), loin, belly, chest, shoulder band (2), withers / neck base; the front cap's central
2x2 (or 3x3 for a 12-sided neck on the bear) is the neck socket. Named lines per half: chest keel /
belly seam, belly line (the lower flank corner: this is the big flat-shading break on every
quadruped), lateral line, back-side corner, spine flank. Rings lean: the shoulder band leans with the
scapula, the hip band with the pelvis, as the wolf already does.

Fore: socket block = columns {belly line, lateral} x rows {chest, shoulder band}, shaped so the loop's
top sits on the scapula ridge just under the withers and its bottom at the chest-belly corner: loop
normal 30-45 degrees off vertical, long axis along the scapula. Poles at scapula-top, withers-back,
chest-keel and armpit corners. Leg, 8 sides: shoulder cap (the point of shoulder, wider than the
socket), upper-arm mass, elbow x3 (converging on the flexor side), forearm mass, wrist x2, paw: the
8-ring turns horizontal, pad ring, toe ring (the toes' bend), 2x2 cap. Hind: socket block = columns
{belly line, lateral} x rows {hip band}, top on the haunch crest (ilium), bottom at the groin / belly
tuck; the back-side corner line runs rump -> haunch -> hamstring. Leg: haunch cap, thigh mass, stifle
x3, shin, hock x3, cannon, paw as fore.

Neck, 12 (wolf) / 12-16 (bear), 3-4 rings at 0.3 x width, leaning with the neck. Head: skull stack
12-16 (nape, crown, brow) + the **muzzle head** template: brow ring 16 -> 4x4 face grid; the muzzle
leaves from the central 2x2 of the grid's lower two rows (8-sided, 3 rings: stop, mid, nose block,
closed by a 2x2 cap that IS the nose plane, blunt); eyes are the two outer faces of the grid's second
row (one face each at stage 1; the 4-vert almond inset is stage 2 and is enough for a wolf); the
cheek / ruff is the grid's bottom row and the skull's bottom ring widened and dropped as a mass with
its own belly line, not a bigger ring; the mouth line is the muzzle's bottom lengthwise edge chain
(a plane break, dihedral >= 20 degrees), the mouth loop itself stage 2. Ears: 1x2 blocks on the top
cap's outer corners, 2-3 rings, 6-sided. Tail: brush 8 sides, 5 rings (root, mass at 0.6, two
tapers, cap); stub 6 sides, 2 rings.

### 2.4 Side and ring counts, reconciled

| part | biped sides | quadruped sides | rings (cage) | reconciled by |
|---|---|---|---|---|
| torso | 16 | 12 / 16 | 8 / 9-10 | caps 4x4 / 3x3 at both ends |
| neck | 8 | 12 | 3 / 3-4 | central block of the torso top / front cap |
| skull | 16 | 12-16 | 3 + brow | neck socket in the under-cap |
| face | mask (16 border) | 4x4 grid | - | welded to the brow ring |
| muzzle / nose | 8 | 8 | 3 + cap | 2x2 block of the face |
| arm / fore | 8 | 8 | 11 | 2x2 socket block |
| leg / hind | 8 | 8 | 10 / 12 | 2x2 socket block |
| hand / paw | 8 (flattened) | 8 (horizontal) | 2-3 + cap | the limb's own ring |
| tail | - | 8 brush / 6 stub | 5 / 2 | 2x2 / 1x2 block of the rump cap |
| ear | 6 | 6 | 4 / 2-3 | 1x2 block |

Hinge joints: three rings. Ball joints: socket loop + cap ring + mass ring. Wrist / ankle / hock:
two rings (three at a biped ankle and a quadruped hock, which plant). Spine: one ring per spine
joint plus one mass ring per bone. Rings in a tube outside joints: spacing 0.6-1.2 x the local width.

### 2.5 Density and budget

Cage targets: biped 1,300-1,700 tris, quadruped 1,200-1,600. The spec above lands near 1,400 for both
(biped: torso ~230, arms ~350, legs ~320, neck ~50, head ~320, ears ~80, thumbs ~40; quadruped: torso
~220, neck ~70, head ~220, legs ~700, tail ~80, ears ~50, paw caps ~30). Final with pieces (eyes,
fingers, claws, loincloth, ruff mass): biped 2,200-2,800, quadruped 1,800-2,600. The current cages at
860-1,130 are not too small by much; they spend what they have on ring stacks and hand curls instead
of sockets and faces.

Share by region (cage): biped head 25-30%, torso 15-20%, each arm+hand 12%, each leg+foot 11%;
quadruped head 15-20%, torso+neck 20-25%, each leg 12%, tail 5-8%. Density (tri share / area share)
0.7-1.6 everywhere; the head may reach 1.8 on a biped, the torso never under 0.7.

### 2.6 Silhouette-driven edges (flat shading)

One lengthwise edge chain per named plane break, continuous through >= 3 rings, dihedral 20-60
degrees, faces between breaks within 8 degrees of planar (`planarize` at the end of stage 1, not 2).
Biped: brow shelf, cheekbone -> jaw -> chin, trapezius slope, clavicle, pec-to-belly step, lateral
line, spine flank pair (the groove), iliac crest, glute-to-thigh, patella, shin ridge, ulna line,
back-of-hand plane. Quadruped: withers, scapula ridge, point of shoulder, chest keel, belly line,
haunch crest, hock point, elbow point, muzzle top plane / side plane, stop, cheek-ruff edge, pad
plane. Everything else is a soft tube and gets no extra ring for shading.

### 2.7 Deformation layout per joint (1-2 influences)

- **Hinge** (elbow, knee, stifle, hock, finger-less wrist): three rings; the middle ring on the
  joint's bisector plane within 0.1 x width of the joint; extensor-side spacing 0.45-0.55 x width,
  flexor-side spacing 0.2-0.3 x width (the rings converge on the inside of the bend, the olecranon /
  patella / hock point stands out on the outside). Weights: outer rings 100/0 and 0/100, middle 50/50.
  At 110 degrees the flexor faces compress (acceptable) and never cross (gate).
- **Ball** (shoulder, hip): socket loop weight 70 parent / 30 limb; cap ring 30/70; mass ring 100
  limb. The socket loop's long axis is along the muscle that wraps the joint (deltoid / glute), so a
  60-degree swing rotates the cap inside a loop that holds its place on the body.
- **Neck**: base ring 100 chest, middle 50/50, top 100 head; three rings minimum.
- **Spine**: one ring per spine bone boundary at 50/50, mass rings 100.
- **Wrist / ankle / hock**: two rings 0.25-0.35 x width apart (three when the joint plants); the
  hand / paw ring beyond is 100 hand.
- **Tail**: one ring per bone, 50/50 at the bone boundary.
- **Jaw**: the mask's jaw chain is 100 head in stage 1; a jaw bone (stage 4) takes the mouth loop
  and the chin at 100 jaw and the cheek chain at 50/50.

## 3. Method

**Change it: a kit-owned topology template per body type, fitted onto the guide.** Not a free loft,
not an SDF, not a shrink-wrapped generic base mesh, not patch-then-subdivide.

What the program does now: invents connectivity per creature (the goblin's torso faces, crotch grids
and head rings are hand-written as vertex lists), sizes rings from `part_rings`, bridges. Every
creature re-derives sockets, caps and the face, and gets them wrong in a different way, and no measure
can say "the shoulder loop is the wrong shape" because the shoulder loop has no identity.

What it should do:

1. `body_template(kind, counts)` in the kit builds the whole half-body **connectivity** from the
   rules in 2.1-2.3: ring stacks with named lines, caps by the cap rule, socket blocks at named
   positions, the face mask / muzzle head, ears and tail. Every vertex carries a name
   (`torso.ring[5].line['lateral']`, `arm.socket[3]`, `face.eye.loop[0]`, `leg.knee.mid[2]`) and
   every loop and chain is a named set. The template is authored once per body type (biped,
   quadruped; later avian, serpent) and parametrised only by counts (sides per part, rings per bone).
2. `fit_template(bm, guide, J, plan, pins)` places the vertices: ring stations from `part_rings`,
   ring vertices from the **corner rule** (`section_corners`: the guide section at the station,
   simplified to n vertices with named corners pinned to named lines), socket loops shaped by the
   per-joint tilt rules, the mask's landmark vertices pinned to `META['landmarks']` (eye centre,
   mouth corners, nose tip, chin, brow), then a few iterations of surface Laplacian relax with
   projection (`fit_to_guide` already exists) with pins fixed and ring planes preserved.
3. The creature program shrinks to: `J`, `PLAN`, counts, landmarks, named-line overrides (where a
   corner should go when the guide is ambiguous) and intended deviations. Secondary vertex moves,
   flattens and partial loops stay in stage 2 exactly as now.

Why this is the right call for an LLM writing bmesh without a viewport:
- Connectivity is where the LLM fails blind; vertex placement is where it succeeds (it already does
  station-driven sizing well). The template moves the hard part into reviewed kit code with named
  loops, and leaves the LLM the part it can reason about numerically.
- Named loops make the gates meaningful: "socket loop normal angle", "flexor/extensor spacing
  ratio", "jaw chain dihedral" become one-line measures on named sets instead of the current
  rail-cutting search in `topology()` that has to rediscover what a ring is.
- This is how a character team works: one base mesh per body type, re-fitted per character; nobody
  retopologises a shoulder from scratch per creature.

Alternatives, and why not:
- *Keep the loft, add rules.* Rules cannot give a loft a tilted socket or a face mask; three rounds
  of rules got c3 to "basic passes".
- *Patch layout then Catmull-Clark.* Soft forms, plane breaks lost, no control of where the lines
  land; wrong for flat shading.
- *Separate overlapping limb parts (PS1 style).* Removes socket topology at the cost of the
  shoulder and hip reading; fine at 300 tris, not at this bar, and it leaves visible intersections
  in motion.
- *Shrink-wrap a generic base mesh.* The same as the template but without counts control and
  without named lines; the fit is harder to check.

## 4. Measures and gates

Change `TOPO_LIMITS` and `topology()`; measure on named sets once the template exists, on the rail
search until then. Gates (block the lock) unless marked warn.

Form on the cage (replaces IoU as the medium-form measure; IoU stays for the silhouette):
- **Section fidelity** per ring: Hausdorff distance between the ring polygon and the guide section
  <= 3% of the section width; polygon area / section area 0.92-1.05.
- **Corner share** per ring: >= 60% of ring vertices within 2% of width of a section corner
  (polyline-simplification vertex). This is the number behind "planes in the right place".
- **Twist** between consecutive rings <= 15 degrees.
- **Planarity** after `planarize`: every quad within 8 degrees (warn at 5).
- **Plane-break chains**: each named break present as a chain of >= 3 edges with dihedral 20-60
  degrees (list per body type in the template).

Topology:
- **Socket**: root loop vertex count == limb sides (8); loop centre within 0.15 x width of the joint;
  loop normal 25-50 degrees off the limb axis (biped shoulder, quadruped fore and hind); flow (limb
  lines running on into the parent) >= 0.9 (now a 0.3 warn).
- **Hinge rings**: exactly 3 rings inside the band; middle ring within 0.1 x width of the joint;
  flexor spacing / extensor spacing 0.4-0.7 (converging). Wrist / ankle: 2 (3 when planting).
- **Neck**: >= 3 rings, spacing 0.25-0.4 x width. **Tail**: rings == bones + 1.
- **Caps**: every open end closed by the cap rule; no end closed by a fan, a triangle or a pole of
  valence >= 6 (now only checked at limb roots).
- **Poles**: total <= 0.10 x verts (goblin is 0.13); none in a joint band (keep); none on a limb's
  first ring; socket corners exactly 4 per socket; head <= 12; every pole on a face whose guide mean
  curvature is below the part's 60th percentile ("on the flat").
- **Face**: eye loop >= 8 verts with a concentric outer loop, mouth loop >= 8, mask loop present and
  joining both, jaw chain dihedral >= 25 degrees (biped). Quadruped: muzzle 8-sided with a 2x2 nose
  cap, mouth edge chain dihedral >= 20 degrees, ears present when the sheet shows them.
- **Size**: edge p90/p10 <= 2.5 per region (now 4), <= 4 body-wide (now 6); faces over 3:1 <= 8%
  (gate, now a 20% warn); over 5:1 = 0 (now 5%).
- **Density**: 0.7-1.6 per region (gate, now a 0.5-2.0 warn); torso >= 0.7 always.
- **Spacing**: outside joint bands every consecutive ring pair at 0.6-1.2 x width (the stack gate
  only catches runs of three).
- **ROM**: folded area <= 1.0% total (bear 4.3, wolf 2.3, goblin 0.85) and <= 0.3% at any one joint;
  no face normal flip; min interior angle >= 15 degrees in every pose; add two poses: head turn 45
  degrees + neck pitch 30, and a torso twist of 20 degrees at the waist. Report the socket loop's
  drift (mean vertex move) in the swing pose: <= 0.15 x limb width.
- **Consistency**: `joint_loops` (the stage-1 gate) and `topology()['joints']['rings']` disagree
  (goblin wrist 2 vs 5, bear knee 3 vs 2). Keep one: closed face-loop rails in the band, counted once.
- **Budget**: cage tris within the band of 2.5 (gate), region shares within 2.5's table +-5 points
  (warn).

## 5. Order of work

Smallest set, biggest jump, in order. Each step lands with its gate so the next review has a number.

1. **Corner rule for ring vertices.** `kit/carve.py`: add `section_corners(guide, station, n,
   pins)` (guide section polygon via `hull_sections` -> polyline simplification to n vertices ->
   named-corner pinning -> twist-match to the previous ring); make `ring_points()` use it whenever a
   guide is present and keep the superellipse as the fallback. Gate: corner share, section fidelity,
   twist (`topology()`, `TOPO_LIMITS`). No connectivity change; every part's planes move onto the
   form at once. This alone addresses the owner's "medium forms weaker than the concept".
2. **Sockets and hinges as kit operations.** `kit/bmkit.py`: `socket_block(bm, block_faces, sides,
   tilt)` (delete a 2x2 / 1x2 block, shape the boundary loop to the tilted ellipse, return the loop
   with named vertices), `limb_rings(J, chain, width_fn, hinge='converge')` (the ring stations with
   the 3-ring converging layout at hinges, 2 at wrists, caps by the cap rule), `cap_grid(bm, ring)`.
   Rewrite the three programs' `limb()` / `ring6` / `FOOT` on top of them (goblin and wolf to 8-sided
   limbs from 2x2 blocks; the bear's kite closures go away). Gates: socket, hinge rings, caps, flow
   0.9, ROM 1%.
3. **Body templates.** `kit/bmkit.py` (or a new `kit/template.py`): `body_template('biped' |
   'quadruped', counts)` + `fit_template(...)` with named vertex sets; `topology()` measures on
   named sets when present. Programs shrink to J / PLAN / counts / landmarks / overrides. Gates: pole
   budget and placement, plane-break chains, spacing, size and density at the new limits.
4. **Face mask and muzzle head.** `kit/parts.py`: `face_mask(landmarks)` (the authored 2D quad
   template with 8-vert eye and mouth loops, mask loop, nose block; fitted to the guide's face) and
   `muzzle_head(counts, landmarks)` (brow ring, 4x4 face grid, 8-sided muzzle with a nose-plane cap,
   ruff row, ear blocks). Both are template sub-parts and are the heads of step 3's templates. Gate:
   the face block in section 4.
5. **Gate consolidation.** `TOPO_LIMITS` to the numbers in section 4; `cage_gates()` promotes the
   named warns to gates; `rom_poses()` gains the head-turn and waist-twist poses; `joint_loops` is
   dropped in favour of the ring count. `BRIEF.md` "Topology rules" replaced by sections 2.1-2.7 of
   this note; `ART_DIRECTOR.md` topology review gets the loop-map checklist (socket shape, hinge
   convergence, jaw chain, plane-break chains) so the eye and the numbers agree.

Do not do: more rings per part (the goblin's 12-ring arm shows where that goes); more sides on
limbs beyond 8 before the sockets exist; eye detail before the mask exists; raising the triangle
budget; per-creature hand-written socket faces ever again.
