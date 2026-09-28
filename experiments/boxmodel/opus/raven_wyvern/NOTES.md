# raven_wyvern (opus) — round notes

Build: one trunk of 5-vert half-rings (tail tip -> beak tip), each ring a slice between a
dorsal and a ventral point of the side profile. Legs (6-sided) extruded from a 2-face patch on
the lower flank at the hips; toes (4-sided) extruded from the foot-box walls; folded wings
(6-sided: bone strip over membrane) extruded from a 2-face patch at the shoulder.

Kit note: `extrude()` on a 2-face region deletes the old faces FACES_ONLY, so the region's interior
edge survives as a loose wire (20 non-manifold edges in r01's first run). The program deletes
loose edges after the extrusions. Reported, kit untouched.

## Stage 0
- blueprint.json drawn from the design numbers (head 1:3.4 of height, hip ~0.56, tail tip
  0.98, folded wing wrist above the shoulder). blueprint.png reads as a crested raven biped.

## Stage 1
- r01 — Critique: wings are thin planks standing off the body with daylight between (az000,
  az180, top): boards, not folded wings. Diagnosis: sail sections at x 0.30, thickness 0.045,
  vertical. Fix: sail() takes LE x and TE x; LE tucked in to 0.215-0.23, TE following the
  flank, thickness 0.055-0.06. Result (r02): wings hug the body, read as a folded cape from
  az180; better. 636 tris.
- r02 — Critique: legs are straight pillars (az090, az000): no drumstick, the reversed knee is
  invisible, creature reads leggy. Diagnosis: thigh top section hf 0.125 tapers linearly to
  knee 0.07 -> shank 0.055, knee only 0.07 behind the thigh. Fix: thigh top bigger (0.14 x
  0.108) and lower (z 0.38), knee thinner (0.058) and further back (y 0.22), belly ventral
  points lowered 4-6 cm. Result (r03): drumstick + backward knee read in az090 wire; better.
  636 tris.
- r03 — Critique: torso reads slim/penguin from az000 and top; head nearly as wide as the body.
  Diagnosis: body rings W 0.18-0.21, lower-side vert at 0.55 W (a knife keel). Fix: body W to
  0.20-0.245, lower-side 0.64 W; wings moved out 0.035 with it. Result (r04): plumper from the
  front, head:torso width 0.7; better. 636 tris.
- r04 — Critique: tail is a long thin spike (top, az090): a rod. Diagnosis: t0..t2 W 0.045-0.12,
  tip at y 0.98. Fix: tail shorter (tip 0.88), root W 0.16 and deeper (0.8x the rear radius), tip
  ring kept 0.075 wide for the fan. Result (r05): a thick tapering wedge that continues the back;
  better. 636 tris.
- r05 — Critique: head is one long cone, skull flows into the bill with no stop: vulture/toucan
  (hero, az090). Diagnosis: k2 -> b0 -> b1 taper evenly (W 0.15 -> 0.10 -> 0.065). Fix: k2 a tall
  near-vertical face plane (W 0.16), b0 narrower (0.085) set only 3 cm in front (a step), bill
  shorter and deeper with the hook. Result (r06): the bill is a distinct block growing out of the
  face; better. 636 tris.
- r06 — Critique: the wing arm/wrist stands as a tall post beside the head (az000, hero), dark pit
  between neck and wing. Diagnosis: wrist at z 1.19 on an arm going straight up. Fix: wrist lowered
  to 1.10 and brought forward to the neck base, sail LE lowered to meet it. Result (r07): hunched
  shoulder knob, no post; better, a small thumb spike remains at the wrist. 636 tris.
- r07 — Critique: head too small: 21% of the side silhouette (target 25-29%). Diagnosis: head
  rings k0..b3 sized for a 1:3.9 head. Fix: HEAD_SCALE 1.15 about the skull top (jaw drops, neck
  shortens). Result (r08): head 25.9% of the side view (own mask measure; the harness orbit is
  empty for an unpainted base); reads as a big-headed character; better. 636 tris.
- r08 — Critique: from the top the wings are two thin strips beside the body with a gap, and a pit
  opens between neck and wing (top, az180, hero). Diagnosis: sail sections vertical (LE x ~ TE x).
  Fix: LE x pulled in 0.03-0.05 so the sail leans over the back like a draped cape. Result (r09):
  wings visible from the top as wedges over the flanks, az180 reads as folded wings; better. 636 tris.
- r09 — Critique: from az000 the face is a flat octagonal plate with the bill sunk in its centre —
  a mask. Diagnosis: b0 top 7 cm below k2 top, so the step runs all round the bill. Fix: b0 top
  raised to continue the forehead (culmen line), the step kept only at the sides (b0 W 0.09 vs
  face 0.16). Result (r10): a big raven bill growing out of the forehead, face plate gone; better
  (bill is on the large side: watch it). 636 tris.
- r10 — Critique: the back of the neck is a vertical post under a flat skull back (az090): the
  head sits on a stalk. Diagnosis: n0/n1/k0 dorsal points all at y -0.30. Fix: dorsal neck points
  set back to -0.26/-0.265/-0.28 and the neck rings widened 5 mm, so the nape runs concave from
  occiput to shoulders. Result (r11): smoother nape, thicker neck base; modestly better. 636 tris.
- r11 — Critique: the wrist is a thin vertical fin (hero, hero wire), not a knuckle. Diagnosis:
  wrist section only +-0.03 in x and +-0.05 along its up axis. Fix: +-0.045-0.05 in x, +-0.04 up.
  Result (r12): a small blocky wrist knuckle at the neck base; better. 636 tris.
- r12 — Critique: the bill is outsize: toucan/hornbill in az090 and hero. Diagnosis: b1..b3 reach
  y -0.92 (pre-scale), bill ~0.62 of the head length. Fix: b1-b3 pulled back 3-4 cm. Result
  (r13): raven proportion, head 26.1% of the side view; better. 636 tris.
- r13 — Lock round (r14, no geometry change): reads as a big-headed raven biped with folded
  wings from every view. Remaining for stage 2: one big flat wing plane in az090, straight belly
  diagonal, boxy skull, no eye socket/brow.
- LOCKED stage 1: 320 verts, 636 tris, edge sha256 01338bad3cee56f4...

## Stage 2
- s2 r01 — Fix (face first, the brief's rule 6): `inset` eye socket in the upper-side face between
  the skull ring k1 and the face ring k2, inner ring pushed 2.2 cm in; the brow (k1/k2 upper-side
  verts) moved out 2-3 cm and down over it. Result: a recessed socket under an overhanging brow in
  az090 wire; better. 652 tris, IoU min 0.992.
- s2 r02 — Critique: the ventral line is one straight diagonal jaw -> belly (az090, hero): no breast,
  no tuck. Diagnosis: ventral/lower-side verts of n0 c1 c0 h1 h0 lie on a line. Fix: vertex moves —
  n0/c1/c0 bottom + lower-side forward/down 1-4 cm, h1/h0/t2 bottom up 2-3.5 cm. Result: a swelling
  breast and a tucked belly; modest, better. 652 tris, IoU min 0.969.
- s2 r03 — Critique: the knee is a single ring between long segments: it will fold flat in the
  walk, and the feathered thigh has no end. Fix: `loopcut` a full loop each side of the knee ring
  (t 0.80 on the thigh, 0.22 on the shank); thigh-side ring scaled 1.18 (a feather cuff ending
  the drumstick), shank-side ring 0.88. Result: a cuff reads at the knee in az045; 2 supporting
  loops per knee for stage 4. 700 tris, IoU min 0.965.
- s2 r04 — Critique: the bill is a smooth cone with no mouth line: the face has no expression line
  (az045, az090). Fix: vertex moves — the bill's side verts (b0-b3 index 2) pressed in 0.4-2.2 cm,
  the k2 side vert pulled back/down as the mouth corner. Result: a gape crease along the bill,
  upper mandible overhanging; subtle but reads; better. 700 tris, IoU min 0.965.
- s2 r05 — Critique: the folded wing's leading edge is flush with the membrane: one flat leaf in
  az090/az135, no bone. Fix: vertex moves — the bone-bottom outer vert (P4) of sail sections
  S2-S4 out 1.8-2.6 cm and down 1 cm. Result: a faint overhang line under the bone strip; small
  in clay, the paint (bone #33353e over membrane #6e5a98) will carry it. 700 tris, IoU 0.965.
- s2 r06 — Critique: under the eye the head side is a lumpy run of facets, no deliberate plane
  (hero). Fix: `flatten` the k0-k2 side / lower-side verts into one cheek-jaw plane. Result: one
  clean jaw facet from occiput to mouth corner; better. Stage 2 final: 700 tris, IoU min 0.965,
  3 logged ops (eye inset, 2 knee loops), lock assertion PASS.

## Stage 3
Palette (8): plumage #5e6272, dark #4c505e (head, neck, tail, wing bone), ink #1c1d24 (brow,
claws, pupil, socket), beak #c89233 (bill AND leg scales — merged to stay within 8), eye #ffb21e,
membrane #6e5a98, crest #b02cf0 (crest AND tail fan — merged), pale #a2a3ae (hackles, eye glint).
- s2 r07 (orchestrator-directed amendment after review "reads parrot/vulture"): vertex moves only —
  bill culmen lengthened and straightened (b1-b3 forward 3-8 cm, tops up 2-6 cm), mandibles
  thinner, small hook at the tip. Result: a raven bill, not a parrot's; IoU min 0.937. 700 tris.
- s3 r01 — paint (8 colours) + pieces: eye (iris/pupil/glint), brow, horns x3/side, hackle ruff x5/side,
  dorsal spikes (midline, unmirrored), wing thumb claw + 3 finger ribs/side, claws x4/foot, tail fan
  x3/side. Gates PASS, 1480 tris total. Critique: the horns fan upward like a cockatoo tuft (az090,
  hero) — the parrot read. Diagnosis: tips rise 15-19 cm over 25-40 cm, thin (w 0.026-0.034), a
  third near-vertical blade. Fix (r02): 3 thick horns swept back nearly level past the occiput.
- s3 r02 — Result: horns swept back nearly level past the occiput, a cheek horn behind the eye;
  reads as horns in az090; better. 1480 tris. Next critique: the wing reads as a bird wing with
  pins — finger ribs thin (w 0.013) and short past a straight trailing edge (az090 colour).
- s3 r03 — Fix: finger ribs bold (w 0.02) running 9-13 cm past the trailing edge, plus a membrane
  flap per finger from the trailing edge down to the rib tip. Result: a scalloped bat/dragon
  trailing edge in az090; better. 1528 tris.
- s3 r04 — Fix: dorsal spikes 4.5-9 cm (were 3-5.5, hidden between the wing bones), tail fan blades
  wider/longer, plumage lifted one value step #5e6272 -> #6b7082 (the orchestrator's mid-value
  note: the workbench rendered the body near-black). Result: violet ridge reads above the folded
  wings (az135), fan reads. Stage 3 final: 1528 tris, 8 colours, gates PASS.

## Stage 4
Rig from J: hips, chest, neck, head, crest (carries the horns), tail0, tail1, fan (carries the fan),
thigh/shin/foot.L, arm/hand/tip.L (+ .R mirrors) = 20 bones. skin() then a weight cleanup: wing
bones only on wing verts, shin/foot only on leg verts, crest/fan off the body (bone heat bleeds the
folded wing into the flank, 2-4 cm apart). Pieces: eye/brow -> head, horns -> crest, fan -> fan,
hackles/spines/wingbones/claws -> body weights.
- s4 r01 — gates PASS (glbcheck OK). Critique: the attack runs backwards — at f16 (lunge) the neck
  throws the head straight up, beak to the sky; at f8 (windup) it dips. Diagnosis: bone-local +X
  bends chest/neck/head back on this rig. Walk strides correctly (az090 f13), idle fine.
  Fix (r02): invert the chest/neck/head X signs in the attack.
- s4 r02 — Result: windup rears back (f8), lunge drives the bill forward-down with the wings
  half-raised (f16); neck keeps its volume in the posed wire; gates PASS, glbcheck OK.
- s4 r03 — final run with the harness orbit, no change.

## Totals
- Triangles: stage 1 636 | stage 2 700 | stage 3 1528 (body 700 + pieces 828) | stage 4 1528.
- Rounds: stage 1 14 (13 fixes + lock round) | stage 2 7 (6 + orchestrator-directed bill amendment)
  | stage 3 4 | stage 4 3. Lock edge sha256 01338bad3cee56f460fb0e48e5165f42af47af2c5ec4bf3ca6b45d2c707f6b2f.
- side_by_side.jpg: faceted and designed next to the engine's tube-loft version; the identity is
  still bird-first (see weaknesses in the final report).

## Orchestrator pass 2 (review of side_by_side: slate plumage read pigeon/parrot, washed out)
- s3 r05 — Fix: dark-not-black palette — plumage #454a59, new 'dark' #363a47 on head+neck (front
  of the n0 ring), the back saddle (top face row, normal z > 0.5) and the tail (behind t2), ink
  #2a2c34 (wing bone, brow, claws, pupil), membrane #7a62a8; 'pale' dropped to stay at 8: the
  hackles take the plumage colour and the eye glint the eye gold. Horns re-swept along the skull
  line (tips 1.24-1.455, reaching y -0.02..-0.06). Gates PASS, 1528 tris, 8 colours.
- s4 r04 — rerun + orbit + compare, no change. Result: reads as a dark raven with facets holding
  under the key light, violet membrane separate from the body; horns lie back in az090 (from the
  high hero camera they still rise somewhat). Gates PASS, glbcheck OK.
