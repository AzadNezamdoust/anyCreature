# owl (opus) — round notes

Build: one trunk of 6-vert half-rings [T, BK, SD, FC, FF, B] bent through a right angle —
tail tip (vertical slices) -> rump and belly (diagonal) -> chest, neck, head (horizontal) —
each ring a slice between a dorsal point T and a ventral point B of the side profile. The crown
closes on an inner ring (quads away from the seam). Out of the trunk: ear tufts from the crown's
outer-front quad; 4-sided feathered legs from the belly-underside quad, a foot box, 4 toes from
its walls (2 forward, 2 back); folded wings from a 2-face patch on the upper flank under the head
(6-vert sections wrapping flank and back, tips over the tail).

## Stage 0
- blueprint.json: 0.6 m standing incl. tufts, head 0.345-0.56 (1:2.8 of height), head as wide as
  the body, wings forming the egg outline, short tail past the wing tips. blueprint.png reads as a
  horned owl from the front.

## Stage 1
- r01 — Critique: 16 self-intersecting face pairs (gate FAIL); OWL_DBG face dump shows the wing's
  lower band cutting the rump. Diagnosis: the wing went from its z 0.165 section straight to a tip
  section at x 0.06, y 0.16 — through the rump. Fix: an extra section wrapping round the rump.
  Result (r02 first try): the wing folded over itself (two near-coplanar sections); sections
  re-planned as a sweep that rotates from horizontal (down the flank) to vertical (tip over the
  tail). 0 hits, 564 tris.
- r02 — Critique: wings read as arms / boxes beside the body from az000, square shoulder with a
  dark slot. Diagnosis: shoulder section top flat at z 0.345 out to x 0.172; wing inner surface
  1.5-2.4 cm off a body that was widest (W 0.14) exactly under the wing. Fix: shoulder top sloped
  down (0.330-0.338), wing inner hugs the breast, body rings b0-b2 narrowed (0.115/0.125/0.13) so
  the wing forms the egg outline. Result (r03): tighter from the front, 0 hits; better. 564 tris.
- r03 — Critique: az180/az135 the wings are thin handles with daylight through them; the back is
  bare. Diagnosis: wing sections were slabs in x (outer/inner) whose back edge stopped at x 0.11.
  Fix: sect() now wraps each section round the body — front edge on the flank, a back-side corner,
  back edge 4 cm off the spine — thickness taken toward the body axis. Result (r04, after raising the
  tip sections 2-3 cm off the rump): two broad wing panels cover the back; better. 564 tris.
- r04 — Critique: the ear tufts are cat ears (az000, hero): wide triangles on the head corners.
  Diagnosis: 2 tuft sections scaled uniformly 0.72 -> 0.18 from a 7.5 cm crown quad. Fix: a
  narrow neck section, an outward bend, tip further out. Result (r05): now bull horns, curved;
  worse identity (devil/horns), 580 tris.
- r05 — Critique: tufts read as horns from the front and as wide triangles from the side.
  Diagnosis: the root quad is long in y and short in x, and the sections scale uniformly, so the
  tuft is a cone that is wider in side view than in front view. Fix: anisotropic sections
  (y scale 0.45/0.32/0.1, x/z 0.85/0.6/0.16) — a flat blade, wide from the front, thin from the
  side. Result (r06): feather blades; better, but the flat crown between them still says cat.
  580 tris.
- r06 — Critique: az000 the head top is flat with a tuft on each corner: a cat head. Diagnosis: k3
  and the inner crown ring k4 flat at z 0.55-0.565. Fix: TWEAK the front-seam and front-face verts
  of k3/k4 down 1.4-3 cm (the brow V between the tufts running down to the beak). Result (r07):
  the classic horned-owl V head from the front; much better. 580 tris.
- r07 — Critique: legs are thin pillars on flat plank feet (az000, az090). Diagnosis: trousers
  section 0.072 x 0.06, toes 0.026 tall and wide-flat, foot box as wide as the leg. Fix: fatter
  trouser section (0.084 x 0.072), compact foot box, thicker taller toes. Result (r08): chunkier
  feathered legs; modestly better. 580 tris.
- r08 — Critique: the face is one flat plate (hero, az000) — no facial disc, the owl's key read.
  Diagnosis: FF (dish centre) and FC (rim) of k0-k2 lie in one plane with the seam. Fix: TWEAK
  FF back 1.4-2.6 cm (a dish per eye), FC rim forward 1.2-1.4 cm and out, the seam left standing
  as the beak ridge. Result (r09): two dishes and a centre ridge read in hero/az000; better. 580.
- r09 — Critique: az000 the body is a tall rectangle (vertical wing sides from shoulder to foot),
  not the owl's egg. Diagnosis: wing outer x 0.165-0.17 at z 0.26-0.34 and 0.16 at z 0.16.
  Fix: shoulder narrower (0.146-0.156, the inner verts in with it — a first try folded the
  section), the z 0.165 section wider (0.176). Result (r10): egg outline widest low; better. 580.
- LOCKED stage 1 (r11, with orbit): 292 verts, 580 tris, edge sha256 a4a9df937bf49fac. Orbit holds.
  Remaining for stage 2: no rim crease on the disc, a notch/shelf under the head, flat breast.

## Stage 2
- s2 r01 — Critique: the facial disc has no rim (hero): dish and rim one soft surface. Diagnosis:
  nothing between FF (dish) and FC (rim) columns. Fix: partial_loop through the k1/k2 FF-FC edges
  (t 0.28 from the rim), terminators in the cheek (k0-k1) and brow (k2-k3), the new verts pulled
  1.2 cm forward as the rim lip. Result: a raised lip round each dish in hero; better. 588 tris,
  IoU min 0.99.
- s2 r02 — Critique: the head needs a swivel ring (idle head turn) and the under-disc ruff.
  Fix: full loopcut in the n0-k0 band, front half flared forward/down. Result: a dark shelf under
  the head in az000/hero — the head reads as a helmet on a separate body; worse. 608 tris.
- s2 r03 — Fix: loop moved out only slightly. Result: shelf still there (the band from k0 in to the
  narrower neck faces down). Same. 608 tris.
- s2 r04 — Diagnosis: the neck loop and n0 are 1-2 cm inside k0 all round. Fix: the neck loop takes
  85% of k0's section, n0 swells 0.6-1 cm toward it. Result: the head grows out of the body with no
  notch (az000, hero); better. 608 tris, IoU min 0.99.
- s2 r05 (final, with orbit) — Critique: the breast is a flat vertical plate in az090. Fix: belly
  seam/FF verts of b0-b2 forward 0.4-1.4 cm (a swelling breast), b1/b2 FF+FC flattened into one
  breast plane per side. Result: a swelling breast facet in az090; better. 608 tris, IoU min 0.979,
  lock assertion PASS, orbit holds.

## Stage 3
Palette (8, the brief's): body #8a6a48, dark #5a4230 (wings, tufts, back, tail), disc #c9ad84,
rim #3e2e22 (disc rim lip, brow V, brow pieces), belly #d8c4a0 (breast, legs, throat, glint),
eye #f09a20, pupil #111111, horn #3a3530 (beak, talons). Pieces: eyes (8-sided iris prism on the
dish, pupil, 4-sided glint), hooked beak (unmirrored), brow wedges, 8 talons.
- s3 r01 — Result: reads as a horned owl at once (hero, az000 colour). Critique: a full-width dark
  strip under the face (az000 colour) reads as a collar. Diagnosis: the chin band (neck loop -> k0,
  z < 0.368) was painted 'rim'. Fix: paint it 'belly' — the horned owl's pale throat bib. 898 tris.
- s3 r02 — Result: pale throat bib; but disc, throat and breast merge into one pale column
  (az000 colour). Fix: the chin band's outer faces (x > 0.075) painted 'rim' — the disc ring's
  lower corners converging on the pale bib. Result (r03): the disc is bounded; better. 898 tris.
- s3 r03 — Orchestrator review: reads as an owl instantly; the wings/back render near-black and
  hide their facets. Fix: dark lifted to #5e4632 (tufts, back, tail), a new wing colour #6e5238;
  to stay within 8 colours the beak and talons take the rim's #3e2e22 (it was #3a3530, same value).
- s3 r04 (final, with orbit): wings #6e5238 now show their facets in hero; 898 tris total
  (body 608 + eyes, beak, brows, talons), 8 colours, lock assertion PASS, orbit holds.

## Stage 4
Rig from J: hips, chest, neck, head, tail, thigh/shin/foot .L/.R, arm/hand/tip .L/.R. Bone heat,
then weights cleaned (wing bones only on wing verts, shin/foot only on leg verts, body verts off
both). Eyes/beak/brows rigid to head; talons borrow the body's weights.
- s4 r01 — all gates PASS, glbcheck OK. Idle head swivel (neck 22-24 + head 48-52 deg) deforms
  cleanly at the neck loop (idle_f012 wire). Critique: attack f016 pitches the whole body 28 deg
  forward — the owl looks like it is falling on its face and the head leaves the frame, while the
  talons barely come forward. Fix: hips/chest pitch 8/5, the lunge carried by hips translation
  (forward 6 cm, up 4.5 cm), thighs -70 so the talons lead.
- s4 r02 — Result: a level lunge with the talons leading; better. Critique: the flared wings are
  flat plates seen edge-on from the front (hero f008: the right wing is a stick). Diagnosis: arm
  bone-local Z spreads the folded wing sideways but leaves its surface horizontal (checked with a
  bone-tail probe in Blender: the rig is symmetric, signs right). Fix: +40..60 deg twist on the
  arm (local Y) — the wing mantles up with its face forward (probe: tip rises from z 0.32 to 0.48).
- s4 r03 (final, with orbit) — Result: the wings mantle up and out with their faces forward (hero
  f008/f016), a level lunge with the talons leading; idle swivel and hop deform cleanly at the neck
  loop and knees. All stage-4 gates PASS, glbcheck OK, orbit holds.

## Triangles per stage
stage 1: 580 (locked, edge sha256 a4a9df937bf49fac) · stage 2: 608 · stage 3: 898 total
(body 608 + pieces) · stage 4: 898. Rounds: s1 11 (incl. lock), s2 5, s3 4, s4 3.

## Repair pass (AD notes round 1; rounds from 60)
Debug loop: an env-guarded `_flip_dbg` (OWL_FLIPDBG) run on a scratch copy prints posed fold-overs
per clip with their rest positions, and the sliver/float faces (not counted as rounds).
- r60 (note 1, wing-root fold-over) — Diagnosis: 23 attack flips at the root band (x 0.125-0.135,
  z 0.29-0.34): the arm twist 60 + spread 72 swung the 2.5 cm root band's shoulder verts through
  the root ring; the idle head tilt dragged the n0 root top. Fix: stage 2 logged loop half-way
  root->shoulder; stage 4 root ring on chest only, the new loop 50/50 arm/chest, the shoulder
  section 80/20; shoulder pivot moved to the top of the root (0.12, 0.01, 0.345); the attack's
  wing flare now opens from the wrist (arm 18-25 spread / 0-10 twist, hand 45-60, tip 15-25); idle
  swivel carried by the head (neck 4, head 64-70) and a milder tilt. Result: flips 31 -> 2 (0.22%)
  PASS; wings still flare wide in attack f016. Slivers 18 -> 24 (2.6%, FAIL) and the 2 floating
  glints remain for notes 2-3. 910 tris.
- r61 (note 2, needle tips) — Diagnosis: slivers were the thickness bands running 17 cm from the
  rump section (WING[3]) to a 3 cm tip, and the plank tail's thin t0 end. Fix (stage 2 moves): the
  wing tip section reshaped into one blunt slanted end (5-9 cm wide, 2 cm thick, WING_TIP), the rump
  section's outer front verts 1 cm out (thicker lower edge), the tail tip ring slid 35% toward t1
  (~25% shorter, blunter); the wing-root loop's lower verts nudged to keep that strip from needling.
  Result: slivers 24 -> 8 (0.9%) PASS; flips 2 PASS; IoU min 0.927; the tail reads as a short
  blunt fan in az090/back34. Remaining sliver: 1 per tuft tip, 2 per wing root, 1 per wing tip. 930.
- r62 (note 3, eyes float) — Diagnosis: the iris stood 10 mm proud of the dish, the pupil 14 mm, the
  glint 18 mm with a 1 mm gap to the pupil (float 2). Fix (stage 3): iris front 4 mm proud with its
  back 12 mm into the dish, pupil 2 mm proud of the iris and rooted in it, glint sunk half into the
  pupil. Result: float 0, z-fight 0, every stage-4 gate PASS; the dish rim now overlaps the iris
  edge (seated) in close-up 3 and az000; in az090 only the brow blades still jut past the face. 930.
- r63 (note 4, cube head) — Deviation: a logged chamfer on the head's vertical edges would run a
  full loop through the wing root and the trunk (the BK/SD columns continue down the body), so the
  rounding is done with stage-2 vertex moves: the k0-k3 back-corner (BK) verts in 12% onto an
  ellipse through the back seam and the widest side, the top-back edge (k3/k4 T and BK) dropped
  1-1.2 cm and forward, the back seam 4 mm out on k1/k2, the disc centre (FF of k0-k2) 8 mm further
  back. Result: back34 reads a rounded dome with a bevelled corner instead of a crate; IoU min
  0.927; all gates PASS (flips 3). The deeper dish now clips the iris's outer edge. 930.
- r64 (note 5, tufts and brows) — Fix: stage 2 logged partial loop down each tuft blade (terminators
  in the flat of the blade), its two tip verts pulled 45% down = a notch that splits the tip into
  two feather points; the tip section thickened to 1.1 cm; the blade tilted 10 deg out (5 at its
  first section). Stage 3: the brow wedges rebuilt from surface hits, centre line 2-3 mm off the
  face (about 60% buried), 25% shorter, less forward bend. Result: tufts read as feather clumps
  from az000/hero; the brows sit on the face as ridges, no horn in az090; slivers 8 -> 6 (0.6%);
  all gates PASS (flips 3). Eyes read smaller since r63 (dish covers the iris edge). 938 tris.
- r65 (note 6, feet) — Fix (stage 2 moves): each toe's knuckle section narrowed to 0.75x and its
  tip to 0.6x (a taper), the tip height 0.8x. Deviation: the toes stay rooted on the foot-box walls
  (a shorter palm edge needs a new extrusion, not allowed in stage 2). Result: digits instead of a
  mitt in hero_low/az000; talons still seated (hit 0, float 0); IoU min 0.921; all gates PASS. 938.
- r66 (note 7, throat strap and beak hook; eye regression) — Fix (stage 3): the chin band paints
  'rim' only past x 0.105, so the dark rim continues down the cheek into a small corner and the
  pale bib runs between; the beak's mid bulges 2 cm forward and its tip curls back (a hook); the
  eyes were turned toward the dish normal. Result: throat reads as a bib, hook visible in hero; but
  the tilted irises showed only a sliver of orange and the glints floated (float 2, FAIL): reverted.
- r67 (note 3 follow-up) — Fix: eyes back to the forward look; the iris 7 mm proud (back 12 mm in)
  so the deeper dish no longer buries its outer edge. Result: full orange rings in az000/close-up,
  nothing past the face profile in az090 except the tucked brow nub; float 0, z-fight 0, all gates
  PASS. 938 tris.
- r68 (final, with orbit) — every stage-4 gate PASS (hit 0, float 0, z-fight 0, sliver 6 = 0.6%,
  flips 3 = 0.32%), glbcheck OK, orbit holds; --review and --compare rebuilt. Stage 1 still locked
  (edge sha256 a4a9df937bf49fac, never unlocked). Triangles: body 624 after stage 2, 938 total.
  Remaining: idle f012's 70 deg head swivel lets the rigid eye/brow pieces drift over the heat-
  weighted face; the head is still box-like from the side; the wings flare from the wrist, so the
  shoulder stays tucked in the attack.

## Repair pass 2 (AD notes round 2, `review/ad_notes_r2.md`; rounds from 90)
- r90 (baseline, current kit) — every gate PASS except drift: 7 shells (eyes 4, brows 2, beak 1) FAIL.
  Flips 3 = 0.32% of tris / 0.28% of area. 938 tris.
- r91 (note 1, face drift) — Diagnosis: eyes, brows and beak rode the head bone rigidly while the disc
  skin under them carries bone-heat blends. Fix (stage 4): bind the three with body= (the disc's own
  weights). Result: drift 0; the pieces stay flush in idle_f012 and attack_f016; all gates PASS.
- r92 (note 2, neck fold-over) — Diagnosis (OWL_FLIPDBG, now printing weights): the neck loop was 100%
  head and n0 100% chest, so the 70-deg head turn and the attack pitch folded the one band between
  (idle flip at the right shoulder root, attack flips at the nape). Fix (stage 4, `_blend_neck`): the
  neck loop 50% head / 50% neck, n0's free verts (T, FF, B) 20% neck / 80% chest; n0's wing-root verts
  keep riding the chest. Result: flips 3 -> 0 (0.00% tris and area), no purple in 3_tech.
- r93 (note 3, brow) — Fix (stage 3): the brow's centre line 3-4 mm inside the disc (was 2-3 mm proud),
  its outer end pulled in to x 0.092 (inside the disc edge) and ended in a 20%-wide cap (`spike` tipw).
  Result: no blade tip past the head in az000/close-up, the brow projects less than the beak in az090;
  but the long thin cap bands split into slivers (6 -> 14, 1.5%).
- r94 — Fix: cap 30% wide, the mid section moved out to 0.58 (a shorter cap band). Result: slivers back
  to 6 (0.6%), the blunt end still reads. 950 tris.
- r95 (note 4, tail brick) — Deviation: the note says stage 3, but the tail is base geometry, so it is
  re-shaped with stage-2 vertex moves. Fix: the tip ring (t0) thinned to 50% below the top ridge, t1 to
  85%; seam feather 1-1.2 cm longer, outer feathers dropped/forward: a blunt point with 3 top facets
  (centre + 2 outer). Result: az090 a thinner wedge, back34 end still a bit square. IoU min 0.925.
- r96 — Fix: tip 42% / t1 78%, the point sharpened (seam +1.4-1.6 cm, outer -0.6-0.8 cm). Result: az090
  and back34 read a tapered fan ending in a blunt point below the wing tips; slivers 7 (0.7%), IoU 0.926.
- r97 (should-fix O3, tufts) — Fix (stage 2): each tuft tilted 15 deg back (first section 7) and
  shortened 15%. Result: az090 the tuft leans back instead of a vertical horn; az000 tufts near
  unchanged; IoU min 0.922. The two tips cannot separate in profile while the body is mirrored.
- r98 (should-fix O2, throat band) — Fix (stage 3 paint): the chin band is a narrow pale bib point
  (x < 0.045), the disc colour between, the dark rim corners wider (x > 0.095). Result: az000 no
  full-width pale band; the dark corners round the disc bottom. The stage-2 cheek-vert slide not done.
- r99 (final, with orbit) — every stage-4 gate PASS: hit 0, float 0, z-fight 0, sliver 7 (0.7%), flips
  0 (0.00% tris / 0.00% area), drift 0; lock PASS (never unlocked); IoU min 0.922; glbcheck OK; orbit
  holds. --review and --compare rebuilt. 950 tris (body 624). Not done: F3 wing trailing spikes, O7 leg
  fan, O2's stage-2 cheek slide.
