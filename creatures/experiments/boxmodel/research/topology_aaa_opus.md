# Topology standard for the stage-1 cage (senior modeller review)

Scope: `abc/c3/goblin`, `abc/c3/wolf`, `abc/c3/bear` blockout packets (grey, wire, topology, aspect, density,
range of motion, profiles, guide), their build programs, `kit/bmkit.py` (`topology`, `cage_gates`, `TOPO_LIMITS`,
`PROFILE_LIMITS`, `part_profiles`) and `kit/carve.py` (`part_guide`, `part_budget`, `part_rings`, `ring_points`).

Short version: the cages are clean ring-lofted tubes that pass every gate and still read as a first-day blockout.
The gates measure hygiene (quad share, aspect, pole positions relative to joints). They do not measure the things a
character lead looks for: whether edges sit on the planes of the design, whether the junctions (shoulder, hip, neck,
face) have a designed layout, and whether density follows interest. The fix is not more rings. It is a fixed,
designed patch layout per body type, fitted to the guide, with the form coming from named section points and named
plane-break edges instead of superellipse rings.

---

## 1. Verdict

### What is wrong in all three (the root problem)

1. **Every part is a stack of rings square to a bone.** An edge in these cages is either "a ring" or "a rail".
   No edge follows a form: no scapula edge, no ribcage arch, no thigh front edge, no jaw line, no brow line, no
   belly/flank break. On a flat-shaded model every edge is a visible crease, so rings square to the bone print the
   construction method on the surface. The wolf's ruff and the bear's trunk are striped like barrels for exactly this
   reason.
2. **Sections are symmetric by construction.** `ring_points` puts `sides` points on a superellipse from one width
   and one depth. A forearm, a calf, a thigh, a deltoid are not symmetric about their bone; their character is in
   where the mass sits off-axis (calf to the back, thigh to the front, deltoid up and out). A 6-point symmetric ring
   cannot carry that. This is the direct cause of "form on medium-radius parts is weaker than the concept". The
   profile gate (`part_profiles`: taper and RMS of width and depth) is satisfied by a symmetric tube with the right
   two diameters, so it cannot see the fault.
3. **Junctions are what is left over after lofting.** Limbs are grown from a 1 x 2 patch of whatever faces the
   torso rings happened to put there. The pole positions, the root loop shape and the faces around the root are
   by-products. On a character the junctions are the first thing designed and the tubes are what is left over.
4. **The guide is the ceiling, and the guide is a volume proxy.** `0_guide.jpg` is a smooth blended swept solid: no
   hands (a spike), slab feet, no brow, no jaw, no scapula. Fitting a cage to it more closely cannot give designed
   planes. The guide is right for position, length and girth. Planes have to come from the template.
5. **The budget is unused and evenly spread.** 860 to 1128 triangles of a 3000 allowance, with density nearly flat
   (wolf: torso 0.73, head 1.02, limbs 1.2). The concept sheets spend their facets on the head, ruff, hands and
   paws.

### Goblin (1128 triangles)

- **Head / face.** Cranium is a lathe of 8-sided rings; the face is whatever the ring stack left. The eye is a
  single inset quad: a diamond with four valence-5 corners and four valence-3 inner corners, none of them placed.
  No brow line (the concept's whole expression is the heavy angled brow), no cheek plane, no jaw line, no chin
  mass. The nose is a 4-sided tube stuck on the face with no bridge flowing into the brow. The mouth is a notch,
  not a loop. The gate reports "eye absent".
- **Ears.** A flat 4-sided strip of five long quads with no root loop. The concept ear is a cupped shell with a
  thick root and a front/back plane pair. Fine as a silhouette card, wrong as a form, and it will shade as one
  plane.
- **Neck.** Three rings buried under the head. Acceptable for this design, but the head-to-neck join has poles
  scattered on the jaw underside by accident.
- **Shoulder.** The arm is a 6-sided tube leaving the side of a barrel. No deltoid cap, no trapezius slope, no
  clavicle line, no pectoral edge running into the arm, no scapula on the back. The root loop exists only as the
  border of the extrusion patch. In the back view the upper back is a plain grid.
- **Torso.** A 12-column barrel with evenly spaced rows. The concept has a narrow ribcage over a pot belly with a
  clear belly plane and a waist under the belt. No row is placed on the rib/belly break, the navel bulge or the
  belt line.
- **Hip / legs.** Two valence-5 poles on the front of the crotch, no crotch strip, no glute mass, legs are 6-sided
  ring stacks (the leg has about twelve near-equal rings, a ring stack by eye even though the gap rule passes it).
  Knee and ankle are three even rings: no fan to the extension side.
- **Elbow / wrist.** Same: even rings. The arm is about fourteen rings of equal spacing; that is density spent on
  nothing.
- **Hands / feet.** Mitten wedge with no thumb; the concept's read is the long clawed fingers. Feet are a slab with
  a cluster of valence-3 corners. These are the two places a biped needs budget after the face.

### Wolf (864 triangles)

- **Head.** A 6-sided muzzle pushed out of the face cap. No stop (forehead-to-muzzle break) as a designed edge, no
  brow, no cheek/ruff edge, no jaw line, eye absent. Ears are two-tier wedges with a clump of valence-3 poles on
  the tips and no root loop. The top view shows four valence-3 poles in a square around each ear root.
- **Neck / ruff.** The largest form in the concept and the weakest part of the cage: a slanted ring stack with
  faces three to four times the size of the muzzle quads next to them. The ruff in the concept is a layered mass
  with a hard lower edge against the chest and a point at the withers. Here it is a collar of parallel stripes.
- **Shoulder / scapula.** The fore leg hangs under the body from a 1 x 2 lower-flank patch. There is no shoulder
  mass on the side of the ribcage at all; the leg starts at the elbow line as a column. The valence-5 pole sits in
  the middle of the flank with long kite quads running to it.
- **Chest / spine / belly.** Trunk rows are unevenly bunched behind the shoulder and stretched over the loin. No
  brisket (chest keel) plane, no tuck-up line; the belly line is whatever the ring bottoms give.
- **Hip / haunch.** The thigh is the concept's second-largest plane (a broad flat shield from croup to stifle).
  In the cage the hind leg is a narrow tube with a kink; the haunch does not exist as a mass on the body. Pole and
  kites on the croup as on the shoulder.
- **Hock / stifle / wrist.** Ring counts are right, layout is not: even rings, no fan. The hock on a digitigrade
  leg bends the opposite way to the stifle and needs its support loops on the back; here both are identical stacks.
- **Paws.** A bent box. No toe block separated from the pastern, no pad plane.
- **Tail.** Acceptable as a tapering 6-sided tube; needs the top ridge and underside as named edges and a root
  loop on the rump.

### Bear (860 triangles)

- **Head.** The opposite density fault: the muzzle is a fine regular grid (about a hundred faces) on an animal
  whose head is a simple wedge, next to a trunk of huge quads. Grid density with no feature flow: no brow, no
  cheek, no jaw line, no eye loop. The muzzle tip closes to a point.
- **Neck.** Collar ring crowded against the skull (the sliver ring already noted in the cage review), then one
  huge face row.
- **Shoulder and hip.** The worst region of the three cages. Each limb root is closed with long kite quads that
  converge on a valence-5 pole on the back line: the zigzag "V" faces in the side view. They are 5:1 to 7:1, they
  cut across the scapula and haunch masses, and in the swing and crouch poses they tear into fans across the flank.
  That is most of the 4.3% folded area. No scapula hump edge, no haunch edge.
- **Trunk.** The hump is four quads across; flank faces are 4:1 vertical strips; the belly line zigzags because it
  is made of ring bottoms and limb-patch borders. In the top view the trunk is a row of barrel hoops.
- **Limbs.** Columns. The fore limb has no wrist narrowing and no forearm mass; the hind limb has no thigh. Elbow
  has two rings, wrist two, placed evenly.
- **Paws.** A wedge extruded from the last ring. A bear paw is a broad block wider than the wrist with a flat sole.

### Where "ring stack of tubes" is specifically the cause

| Fault | Why the ring loft produces it |
|---|---|
| Striped trunk, ruff, hump | rings are the only cross edges, and they are square to the bone |
| Kite quads and flank poles at limb roots | a limb patch is cut into a ring grid that was not laid out for it |
| No scapula, haunch, deltoid, glute | those masses lie across the junction between two "parts"; no part owns them |
| Tube limbs | one width and one depth per ring, symmetric points |
| No face flow | the head is a part with rings; features are insets into a ring grid |
| Flat density | `part_budget` gives each part the same side count and one mass ring per bone |

---

## 2. Target topology

The standard below is for a stylised flat-shaded creature with a 3000-triangle ceiling. Counts are full
circumference; the cage is built as a half with the mirror seam on x = 0.

### 2.0 Rules common to both body types

1. **Roots are inset, then extruded.** Every limb, neck, tail, ear, muzzle and nose leaves its parent through a
   patch of faces that is first inset (one quad ring) and then extruded. The inset ring is the named root loop
   (shoulder loop, hip loop, neck loop, ear loop, muzzle loop). All its inner vertices are valence 4. The only poles
   are the outer corners of the patch (valence 5), which sit one face ring away from the crease.
2. **Counts are reconciled by patch perimeter, not by reduction rows.** A branch has as many sides as its patch has
   border edges (a 2 x 2 patch gives 8, a 1 x 2 patch gives 6, a 1 x 1 patch gives 4). Reductions inside a part are
   avoided; where one is needed it is the 3-to-1 quad pattern (two valence-3 and two valence-5 vertices), placed
   mid-bone on the flat that faces the body, never within a joint band. Triangles are allowed only as a loop
   terminator on a non-deforming flat (sole, ear back, tail tip), at most 4% of faces.
3. **Pole budget.** Valence 3 and 5 only. Per half body: at most 4 per branch root (the patch corners), at most 4
   per eye, at most 2 per mouth corner, 4 per closed tip (finger, toe block, ear tip, tail tip), plus the box
   corners of torso and head that are not absorbed by a patch. Anything else is a defect. No pole within
   0.35 x the limb width of a joint centre and none on a silhouette ridge.
4. **Limbs have 8 named section points**, not a superellipse: front, front-outer, outer, back-outer, back,
   back-inner, inner, front-inner. Each point has its own radius. 8 is the minimum that holds an off-axis mass and a
   flat front and back at once. 6 is kept for tails, fingers as a group, and thin ears; 4 for single fingers, claws
   and thin tips.
5. **Three kinds of edge are named in the template**: closed loops (root loops, joint rings, eye, mouth), flow
   lines (open edge paths that carry a form edge), and plane breaks (edges that must be a hard crease). The kit
   checks each kind by name (section 4).

### 2.1 Biped (goblin class)

**Polycube.** Torso box 6 (across) x 2 (deep) x 7 (rows): 16 around. Head box 4 (across) x 3 (deep) x 5 (rows):
14 around. Both are fitted round, the box only fixes the count and the patch addresses.

| Branch | Patch on the parent | Sides | Rings along the part |
|---|---|---|---|
| Neck | torso top face, middle 2 x 2; head bottom face, rear-middle 2 x 2; bridged | 8 | 3 |
| Arm | torso side face (2 wide), rows 5 and 6 of 7 | 8 | 10 to 11 |
| Leg | torso bottom face, outer 2 x 2 of each half | 8 | 10 to 11 |
| Crotch strip | torso bottom face, centre 2 x 2 (one column per half) stays | - | - |
| Hand | wrist ring closed by a 3 x 1 end; 3 fingers from the 3 end quads, thumb from 1 inner-front palm quad | 4 each | 2 to 3 per finger |
| Foot | ankle ring; foot is an extrusion of the 2 front quads forward (toe block), heel from the back 2 | 6 | 3 forward, sole flat |
| Ear | head side face, 1 x 2 patch at eye-to-brow height | 6 | 4 to 5 |
| Nose | head front, centre 2 x 1 patch on the nose row (spans the seam) | 6 | 4 |

**Torso rows (bottom to top):** crotch, hip (widest point of the pelvis), belt/waist, belly peak, rib edge (the
belly/ribcage break), chest (armpit level), shoulder top. Rows are placed on those landmarks, not evenly.

**Loop and flow map.**

- *Shoulder loop*: the inset ring of the arm patch. Its top edge lies on the trapezius slope, its front on the
  outer pectoral, its back on the scapula, its bottom one face above the armpit crease. Corner poles (valence 5):
  front-top at the clavicle end, back-top on the scapula spine, front-bottom on the lower pectoral edge, back-bottom
  on the latissimus edge. The two bottom poles must lie on the torso side, outside the armpit crease.
- *Deltoid ring*: the first arm ring, at the deltoid's widest point, with front-outer, outer and back-outer points
  pushed out and inner points pulled in.
- *Pectoral flow line*: the chest row runs from the sternum across the pectoral into the arm's front rail.
  *Scapula flow line*: the same row on the back runs across the scapula into the arm's back rail. These two make
  the "shoulder loop into chest and back".
- *Spine line and sternum line*: the seam edges front and back. *Flank line*: the side column edge from armpit to
  hip, continuing as the leg's outer rail.
- *Hip loop*: inset ring of the leg patch; its back half sits under the glute, its front on the groin crease.
  Corner poles: front on the lower belly beside the crotch strip, outer-front on the hip point, outer-back on the
  glute side, back beside the crotch strip under the glute.
- *Glute*: back column, rows crotch to belt, pushed back; the row at the glute's lower edge is a plane break.
- *Neck loop*: inset ring on the torso top and its twin on the head underside.
- *Jaw line*: the head box's bottom border, a closed loop from ear root under the chin to the other ear root. Plane
  break.
- *Brow line*: the edge between the eye row and the brow row across the whole front of the head, continuing round
  the temple to the ear root. Plane break.
- *Eye loop*: the outer front quad of the eye row, inset once (the loop, 4 quads at stage 1, 8 edges after stage-2
  refinement), then pushed in for the socket so the inner corners become valence 4. Corner poles land on: brow
  line outer end, nose bridge, cheek, temple.
- *Mouth loop*: the centre 2 x 1 patch of the mouth row, inset (loop of 6 quads across the seam), pushed in. The
  mouth corner edge continues back as the *cheek line* to the jaw angle. The loop must be closed and must not share
  a face with the eye loop: at least one quad row (the cheek row) lies between.
- *Nose bridge*: the nose root loop's top edge is on the brow line, so the bridge planes run into the brow.

**Hinge layout:** see 2.4.

### 2.2 Quadruped (wolf, bear class)

**Polycube.** Trunk box 4 (across) x 3 (high) along the body: 14 around. Half-ring columns from the top seam:
c0 back, c1 back edge, c2 upper flank, c3 mid flank, c4 lower flank, c5 belly side, c6 belly. Head box
4 (across) x 2 (high) x 3 (long): 12 around.

| Branch | Patch on the parent | Sides | Rings along the part |
|---|---|---|---|
| Neck | trunk front face, upper 4 x 2 (the lower row stays as the brisket plane) | 12 | 3 to 4 (5 with a ruff) |
| Head | neck end ring 12 continues as the head box | 12 | 3 cranium rows |
| Muzzle | head front face, middle 2 x 2 | 8 | 4 (bear 3) |
| Ear | head top face, one quad (wolf: the outer-rear quad) | 4 | 3, tip closed with one quad |
| Fore limb | trunk side, columns c3 and c4, two rows long at the shoulder | 8 | 11 to 12 including paw |
| Hind limb | trunk side, columns c3 and c4, two rows long at the hip | 8 | 12 to 13 including paw |
| Tail | trunk rear face, middle 2 wide x top row | 6 | wolf 6, bear 2 (stub) |
| Paw | last limb ring; toe block from the 3 front quads, heel/pad from the back | 8 | 2 forward |

**Trunk rows (rear to front), eleven:** rump, croup, hip rear, hip front, loin, waist (tuck-up), rear rib, mid rib,
shoulder rear, shoulder front, point of shoulder. One row lies on each spine joint of `J`. Row spacing 0.5 to 0.8 x
the trunk depth, closer at the two limb roots.

**Loop and flow map.**

- *Scapula loop*: inset ring of the fore-limb patch. It outlines the shoulder mass on the side of the ribcage: top
  edge on c2 (the scapula's upper border, below the withers), front edge on the point of shoulder, rear edge behind
  the elbow, bottom edge on the chest's lower corner. The first limb extrusion is short and goes outward: this is
  the scapula and upper-arm mass as a raised plane on the flank. The second turns down to the elbow.
- *Haunch loop*: the same at the hip. Top edge on c2 under the croup, front edge on the flank fold ahead of the
  stifle, rear edge on the buttock. The first extrusion is the thigh shield: broad, flat, 1.5 to 2 x as long
  (front to back) as it is thick.
- *Corner poles* of both loops (valence 5): two on c2 (upper flank, flat, weighted fully to the spine) and two on
  the lower flank / belly-side corner, outside the armpit and groin crease by one face.
- *Topline*: c0 seam edge, rump to occiput. *Back edge*: the c1/c2 edge: a continuous flow line from the croup
  over the loin and the withers into the neck's upper side rail and on to the ear root. On the bear it carries the
  hump; on the wolf the ruff's upper edge.
- *Upper flank line*: the c2/c3 edge, shoulder to haunch, passing along the top of both root loops. This is the
  line the bear lacks and the reason its flank tears.
- *Belly line*: the c5/c6 edge from brisket through the tuck-up to the groin, uninterrupted by limb patches.
  *Keel*: the bottom seam.
- *Brisket plane*: the trunk front face's lower row, between the fore limbs under the neck.
- *Neck loop*: inset ring at the trunk front. With a ruff (wolf), the ruff is two neck rings whose lower-side
  points are pushed out and down, and the ring behind them is a plane break (the ruff's hard rear edge).
- *Stop*: the head box's front-top border above the muzzle patch: plane break between forehead and muzzle top.
- *Muzzle loop*: inset ring of the muzzle patch. The muzzle's 8 points: top 2, upper-lip side, lip line, lower-jaw
  side (each side), bottom 2. The *mouth line* is the lip-line rail of the muzzle, running back past the muzzle
  loop along the cheek to the jaw angle. Stage 2 can open the mouth along it without new topology.
- *Jaw line*: head box bottom border from jaw angle to chin, continuing as the muzzle's lower side rail.
- *Eye loop*: the upper-outer quad of the head's front-most cranium row, inset and sunk as on the biped. *Brow
  line*: the edge above it, from the stop to the ear root.
- *Ear loop*: inset ring on the head top.
- *Tail loop*: inset ring on the rump.

### 2.3 Density and triangle targets

| | Stage-1 cage | Final (body + pieces) |
|---|---|---|
| Biped | 1500 to 2000 triangles | 2600 to 3000 |
| Quadruped | 1400 to 1900 triangles | 2500 to 3000 |

The cage gate in `BRIEF.md` (400 to 1500) should move to 1200 to 2200. Stage 2 adds loops on the face, hands and
plane breaks; stage 3 pieces (claws, teeth, eyes, belt, fur tufts) get 10 to 15%.

Triangle share by region (stage-1 cage):

| Biped | share | Quadruped | share |
|---|---|---|---|
| Head, ears, nose | 28 to 32% | Head, ears, muzzle | 20 to 24% |
| Torso | 18 to 22% | Neck / ruff | 8 to 12% |
| Arms | 14 to 16% | Trunk | 22 to 26% |
| Hands | 9 to 12% | Fore limbs with paws | 16 to 18% |
| Legs | 14 to 16% | Hind limbs with paws | 18 to 20% |
| Feet | 6 to 8% | Tail | 4 to 6% (stub 1 to 2%) |

Density (triangle share / area share): head 1.5 to 2.5, hands and paws 1.5 to 2.5, limbs 0.9 to 1.4, torso or
trunk 0.6 to 0.9. Within a region, faces are near-square and one size (edge p90/p10 at most 3); between
neighbouring regions the face edge length changes by at most 1.6 x across any one ring (the bear's muzzle-to-neck
jump is about 3 x).

### 2.4 Deformation layout (1 to 2 bone influences)

| Joint | Layout |
|---|---|
| Hinge: elbow, knee/stifle, hock | 3 rings. Centre ring in the bisector plane of the two bones. Outer rings tilted so the three fan out from the flexion side: spacing 0.30 to 0.40 x limb width on the extension side, 0.12 to 0.18 x on the flexion side. Weights: centre 50/50, outer rings 100% to their own bone. |
| Hock on a digitigrade leg | as a hinge, with the fan opening to the back (the point of the hock), the reverse of the stifle |
| Wrist, ankle, pastern | 2 rings, 0.20 to 0.25 x width either side of the joint; 3 if the range passes 60 degrees |
| Ball: shoulder, hip | root loop on the parent (100% parent), first limb ring 0.25 to 0.40 x width out (50/50), second ring at the mass peak (100% limb). No pole inside the root loop. |
| Neck | 3 rings minimum, even, at least 0.20 x neck width apart; root loop on the trunk, root loop on the skull |
| Spine | one row on each joint, one between; never a pole on a row that is on a joint |
| Tail | one ring per joint and one between; the two nearest the root 0.3 x width apart |
| Fingers / toes at this budget | one ring at the knuckle only |

Acceptance in range of motion: folded area at most 1.0% of the surface in every pose, at most 0.5% in any one
joint band; no face in a joint band changes area by more than 60% between rest and pose.

### 2.5 Edges placed for the flat-shaded look

On a flat-shaded mesh a dihedral under about 8 degrees reads as one plane, over about 25 degrees as a designed
break, and the range between reads as mush. The target is to push edges out of the middle band.

- **Planes** (dihedral under 8 degrees inside the plane, quads planar within 5 degrees so the export diagonal does
  not show): forehead, muzzle top, muzzle side, cheek, thigh shield, scapula plate, limb front and limb back, sole,
  ear front and back, belly patch.
- **Plane breaks** (dihedral 25 to 60 degrees, named in the template): brow line, stop, jaw line, cheek-to-ruff
  edge, ruff rear edge, back edge (c1/c2) over withers and hump, scapula loop top and front, haunch loop front,
  rib-to-belly break and tuck-up, brisket edges, glute lower edge, limb front-outer and back-outer rails (so a limb
  reads as a faceted box-with-chamfers, not a pipe), paw top / toe-block edge, sole border.
- **Silhouette points**: each of the four reference views gets vertices on its outline extrema per part: at least
  one section point at the widest and one at the narrowest station of every bone, and a vertex within 1.5% of body
  height of every outline corner sharper than 30 degrees (ear tip, nose tip, hock point, elbow point, heel, withers,
  chin).
- **Diagonals**: for every non-planar quad the export diagonal is chosen to be the ridge (convex) one, and on a
  mirrored pair the two diagonals mirror. This is set in the program, not left to the exporter.

---

## 3. Method

### Recommendation: a hand-authored patch template per body type, built by box operations, fitted to the guide

Drop "loft rings per part and bridge". Keep the guide, the joint table `J`, `part_rings` as a station reader, and
`fit_to_guide`.

**Why not keep lofting.** The loft makes topology a function of the creature: every build invents its own
junctions, and the model writing the program cannot see them. The c3 programs show the cost: `wolf.py` carries its
own `Tab`, `sring`, `lring`, `limb`, `between` helpers to hand-stitch what the loft leaves open, and the result
still has accidental poles. Topology quality should be a property of the kit that is verified once, and form should
be the only thing that varies per creature.

**Why not shrink-wrap a dense base mesh.** A shrink-fitted fixed mesh slides: named loops drift off their
landmarks, and the guide has no landmarks for most of them (it has no scapula, brow or jaw). The fit has to be
parametric, by part station and section point, not by nearest surface.

**Why not separate overlapping parts.** Acceptable for hard pieces (stage 3). For the body it throws away the
shoulder and hip, which are exactly the regions that need designed flow, and the owner's direction is one shell.

**The method.**

1. **Template = a short list of box operations with named addresses.** For each body type the kit holds a function
   that builds the polycube of section 2: a segmented box, then for each branch `inset(patch)` and
   `extrude(patch)` a fixed number of times. Nothing else creates topology. Every vertex gets a stable name from
   its address: `(part, ring index, section index)`, e.g. `('fore', 3, 'front-outer')`, `('trunk', 'mid rib',
   'c2')`. Loops, flow lines and plane breaks are lists of those names, declared in the template. This is box
   modelling in the literal sense and uses only `extrude`, `inset`, `loopcut`, `place`, which the kit already has.
2. **Fit = each named vertex is computed, not projected.** Position = part station (centre, u, w from
   `part_rings` at the ring's t) + section direction x radius. The radius for each of the 8 section directions is
   read from the guide by a ray from the station centre in that direction (a new `section_radii`), not from the
   superellipse. Trunk and head vertices: the same with their own column angles. Root-loop vertices: the parent
   surface under the branch's first ring, offset outward by the loop width.
3. **Design layer = named offsets on top of the fit.** The guide gives volume. The planes come from a small table
   per creature of signed offsets on named loops and section points, in units of the local width: "scapula loop
   top +0.10 out", "thigh ring 1 front +0.15, back-inner -0.10", "brow line +0.06 forward", "calf back +0.12".
   This is what the model writing the program edits, and the only thing it edits besides `J`, ring t values and
   optional loop counts. Each offset is clamped (at most 0.25 x local width) and silhouette IoU is re-checked.
4. **Refine = named loop insertions only.** Extra density is added by `loopcut` on a named edge ring ("trunk row
   between loin and waist", "arm between deltoid ring and elbow fan"), never by free edits. Counts per region have
   allowed ranges in the template so density targets can be met without changing the layout.
5. **Planarise and set diagonals.** `planarize` on the faces of each declared plane; set the diagonal rule of 2.5.
6. **Verify by signature.** The template's topology signature (vertex count, valence histogram, the set of named
   loops with their lengths, branch side counts) is computed once when the template is authored and reviewed, and
   stored. Every creature build must reproduce the signature of its template plus its declared loop cuts. A build
   that fails the signature has done something outside the method.

This is reliable for a model without a viewport because the hard part (which faces exist and how they connect) is
fixed code that has been looked at once by a person, and what remains per creature is numbers with ranges and
numeric feedback: station positions, section radii, offsets.

What a human still has to do once per body type: look at the template on a neutral guide in wire and in the three
range-of-motion poses, and sign it off. That sign-off is the owner gate; after it, per-creature topology is
measured, not judged.

---

## 4. Measures and gates

The current gates stay as hygiene. Add the following to `topology()` / `TOPO_LIMITS` / `cage_gates` so that the
three c3 cages fail and a cage to the standard passes.

| # | Measure | How | Limit |
|---|---|---|---|
| 1 | **Template signature** | valence histogram, branch side counts, named loop lengths against the stored template | exact match (plus declared loop cuts) |
| 2 | **Named loops closed** | every declared closed loop is a closed edge loop of its declared length: shoulder/scapula, hip/haunch, neck x2, muzzle or nose, eye, mouth, ear, tail, jaw line | all present; the eye and mouth become gates, not warnings |
| 3 | **Flow lines continuous** | each declared flow line is an unbroken edge path through valence-4 vertices between its end landmarks | all present; at most the declared poles on the path |
| 4 | **Pole budget and placement** | count by site against 2.0 rule 3; distance of each pole from the nearest joint centre and from the nearest fold | count within budget; distance at least 0.35 x limb width; no pole inside a root loop; no pole on a declared plane break except a declared corner |
| 5 | **Root collar** | faces between a root loop and the first limb ring are quads with all-valence-4 inner vertices | 100%; aspect of faces touching a root loop at most 2.5:1 (the bear's kites are 5 to 7:1) |
| 6 | **Section asymmetry** | per limb station, the 8 radii of the cage against the guide's 8 radii (replaces width/depth only) | RMS at most 4% of local width; and the cage's off-axis centroid shift within 25% of the guide's or of the declared offset |
| 7 | **Tube score** | per bone: (max - min girth) / mean girth, and number of stations whose section is within 5% of a scaled copy of its neighbour | a bone longer than 1.5 x its width has at least one station that is not a scaled copy; flags the pipe limbs |
| 8 | **Hinge fan** | per hinge: ring spacing on the extension side / spacing on the flexion side | 1.8 to 3.0; centre ring normal within 10 degrees of the bone bisector |
| 9 | **Dihedral histogram** | area-weighted share of edges with dihedral 8 to 25 degrees, per region | at most 35% (warn at 25%); declared plane breaks 25 to 60 degrees; declared planes under 8 degrees |
| 10 | **Quad planarity** | angle between the two triangles of each quad on a declared plane | at most 5 degrees; elsewhere at most 20 degrees with the ridge diagonal chosen |
| 11 | **Density targets** | triangle share / area share per region against the table in 2.3 (replaces the single 0.5 to 2 band) | gate on head, hands/paws, torso; warn on the rest |
| 12 | **Size continuity** | ratio of mean edge length across every ring between adjacent regions | at most 1.6 |
| 13 | **Silhouette vertices** | for each view, distance from each outline corner (over 30 degrees) and each per-bone extreme of the reference to the nearest cage vertex on the cage outline | at most 1.5% of body height |
| 14 | **Edge-on-form** | share of cross edges whose direction is within 15 degrees of square to the bone, per region outside joint bands | at most 60% on trunk and head (a pure ring stack scores near 100%) |
| 15 | **Range of motion** | folded area per pose and per joint band; area change of joint-band faces | at most 1.0% per pose, 0.5% per band, 60% area change |
| 16 | **Triangle count** | stage-1 cage | 1200 to 2200 |

Tighten existing limits: `edge_ratio` 4.0 to 3.0, `aspect5_pct` 5.0 to 1.0, `aspect3_pct` 20 to 10 and made a
gate, `flow` 0.3 to 0.75 (with inset roots every limb rail runs into the root loop, so anything lower is a layout
fault). `PROFILE_LIMITS` keeps taper and RMS and gains the 8-direction form of measure 6.

Measures 1 to 5 make the topology a pass/fail fact. Measures 6, 7, 9, 13 and 14 are the ones that separate
"AAA-acceptable" from "basic passes": they are the numeric form of "edges sit on the design" and "limbs are not
pipes".

---

## 5. Order of work

Smallest set first; each step is useful alone.

1. **Eight-direction sections** (`kit/carve.py`). Add `section_radii(guide, ring, dirs=8)` (ray from the station
   centre to the guide surface in each named direction) and let `ring_points` take per-point radii; change
   `PART['sides']` for limbs from 6 to 8 with the named order of 2.0 rule 4. Add measures 6 and 7 to
   `part_profiles` and `PROFILE_LIMITS` (`kit/bmkit.py`). This alone removes most of the "tube" read on arms and
   legs and is independent of the template.
2. **Inset roots and the root-collar gate** (`kit/bmkit.py`). Add a `branch(bm, patch, rings, name)` helper:
   inset, extrude, name the root loop and the rings. Add measures 4 and 5 to `topology()` and `TOPO_LIMITS`. Fixes
   the bear's kites and flank folds and the wolf's flank poles.
3. **Quadruped template** (new `kit/template.py`: `quadruped(k, J, plan, guide)` returning the bmesh and a name
   table; signature stored beside it). Trunk 14 with the c0 to c6 columns and eleven rows, scapula and haunch
   patches, neck 12, head box, muzzle 8, ears, tail. Add measures 1 to 3 (`topology()`), and the eye/mouth loops as
   gates. Rebuild wolf and bear on it. Owner sign-off of the template in wire and range of motion is the stop here.
4. **Hinge fan** (`kit/carve.py: part_budget`). Joint rings become centre + two tilted rings with the 2.4
   spacings; add measure 8 and tighten measure 15 in `cage_gates` / `rom_poses`.
5. **Biped template** (`kit/template.py: biped`). Torso 16, head 14, arms and legs 8 from inset patches, crotch
   strip, three-finger hand with thumb, toe-block foot, 6-sided ears and nose. Rebuild the goblin.
6. **Plane design layer** (`kit/template.py` name tables, `kit/bmkit.py: planarize`). Declared planes and plane
   breaks per template, the per-creature offset table, diagonal rule; measures 9, 10, 13, 14.
7. **Density and budget** (`TOPO_LIMITS`, `tri_budget`, `BRIEF.md` "Topology rules" and the stage-1 triangle gate).
   Region targets of 2.3, measures 11, 12, 16; named loop-cut ranges in the templates.
8. **Docs** (`BRIEF.md`, `WORKFLOW.md`, `ART_DIRECTOR.md`). Replace the ring-budget text with the template, the
   loop map and the new gates; the art-director packet gains the named-loop overlay and the dihedral histogram.

Steps 1 to 3 give the largest jump on the two quadrupeds; step 5 does the same for the biped. Steps 6 and 7 are
what turn a correct cage into one that looks designed.

## Limits of this review

The polycube counts and patch addresses in section 2 are a design, not a built and tested mesh. The inset-then-
extrude pole positions follow from the operation, but whether the lower shoulder and haunch poles clear the armpit
and groin crease on a given creature depends on the fit and has to be shown by measure 4 and the range-of-motion
poses on the first template build. The dihedral bands (8 and 25 degrees) and the density ranges are working values
from production habit and should be adjusted against the first cage the owner accepts.
