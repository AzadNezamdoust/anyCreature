# Goblin (opus) — round notes

Stage 0: blueprint.json drawn (blueprint.png): head 0.38 of 1.10 m (1:2.9), hunched, big ears, big feet/hands.
Build plan: one vertical stack of 7-point half rings (crotch -> crown); arms (6-sided), legs (6-sided),
ears (6-sided leaf), nose (seam sweep) are swept from sockets left open in the stack; hands go
6 -> 8 at the knuckles (two triangles in the flat of the palm) so 3 fingers + thumb sweep out as quads;
feet sweep the front three faces of the ankle block forward into a 3-toe forefoot.

## Stage 1
- r01 — first build, 1134 tris, all gates PASS, blueprint IoU side .86 / front .86 / top .76.
  Critique: the face reads as a visor — a horizontal slot runs across the whole face at the eye row
  (az000, hero), so the head looks like a helmet, not a goblin face.
  Diagnosis: ring ET is recessed at every column (col 0 nose bridge and col 3 temple too), so the
  groove wraps the head. Fix: recess ET only at cols 1-2 (the eye), keep col 0 flush with the nose
  bridge/brow and col 3 flush with the temple.
- r02 — 1134 tris. Result of r01 fix: marginal; the slot persists (hero): the brow ring BR is one
  horizontal level all round the head, so its underside is a straight dark band wrapping to the temple.
  Critique: the brow reads as a helmet visor rim, not a goblin brow. Diagnosis: BR z .978-.99 flat
  across cols 0-3, overhanging ET at col 2 as much as at col 1. Fix: make the brow a V — inner brow
  (cols 0-1) low and forward (z .965), outer brow (col 2) high (z 1.0) and only slightly forward, so
  it frowns over the eye and dies out at the temple.
- r03 — 1134 tris. Result: better — the brow now frowns in a V and dies out at the temple (close-up
  renders, scratchpad look.py). Critique: the nose is a thin twig poking straight out (az045, hero),
  not a large hooked goblin nose. Diagnosis: the root face (NB->EB col 0-1) is 0.045 x 0.05 m and the
  two sweep sections keep that thin section and run horizontally. Fix: grow the root (NB lower, EB
  higher: 0.08 m tall), make the first section a fat bulb (0.055 half-width, 0.075 tall) and the tip
  section hook down to z .81 over the upper lip.
- r04 — 1134 tris. Result: better — the nose is now a fat bulb hooking down over the lip (az045/hero).
  Critique: the head is a box — in az000 its outline is a rounded square (skull, cheek, mouth and
  jaw all ~0.15-0.185 half-width), so it reads as a crate with a face, not a goblin's pear-shaped
  head. Diagnosis: cols 2-4 of rings J0, L0, M, U sit nearly as wide as the brow rings.
  Fix: taper the lower head — jaw 0.12, mouth 0.15, cheekbone 0.185, cranium 0.19 — and narrow the
  chin (J0 col 1) so the front outline is an inverted pear ending in a pointed chin.
- r05 — 1134 tris. Result: better — the front outline is now a pear: wide cranium and cheekbones,
  narrow jaw, pointed chin (az000). Critique: in profile (az090) the body is an upright post — flat
  belly (5 cm bulge), shoulders straight over the hips — so it reads as a small man, not a hunched
  pot-bellied goblin. Diagnosis: rings B1/B2 front at -0.19/-0.20 vs hip/chest -0.145/-0.15, and
  CH/S/N1 centred over the pelvis. Fix: bulge and sag the belly (B1/B2 front -0.225), tuck hip and
  chest fronts, and hunch: CH -0.02, S -0.04, N1 -0.03 forward with the upper back humped, arm
  joints moved forward with the shoulder.
- r06 — 1134 tris. Result: better — the belly now bulges and sags and the chest is tucked (az090,
  hero). Critique: blueprint overlay (side) shows the back and seat sitting 3-5 cm inside the drawn
  line: a flat back and no seat, so the profile is still a post. Diagnosis: back seam/corner points
  (cols 5-6) of H, B1, B2, CH, S at y .10-.14 with no hump. Fix: seat out to .155, a rounded hump at
  CH/S (.125/.09, raised), so the back is one convex curve over a hunched spine.
- r07 — 1134 tris. Result: better — one convex back curve with a seat and hump (az090, az135);
  side IoU .849 -> .867. Hand and foot close-ups (look.py) read: 3 fingers + thumb with V gaps,
  3 splayed blunt toes. Critique: the legs are two straight vertical posts (az000, az090) — the knee
  sits only 3 cm ahead of the hip-ankle line, so there is no crouch and no bow. Diagnosis: J['knee']
  (0.12, -0.075, 0.19). Fix: knee forward and out to (0.135, -0.105, 0.195): a bent, bowed goblin
  stance with the ankle still under the hip.
- r08 — 1134 tris. Result: better — knees bent and bowed (az000, az135); a crouch now reads.
  Critique: in profile (az090) the head is a box — vertical flat back from nape to crown, so the
  cranium looks small and the head sits on the neck like a crate. Diagnosis: back points (cols 5-6)
  of L0..FH all at y .075-.105. Fix: tuck the nape (L0/M back .06-.07) and bulge the cranium back
  (EB/ET/BR back .12-.13), so the profile is a goblin's egg-shaped skull over a thin neck.
- r09 — 1134 tris. Result: better — egg-shaped skull bulging back over a tucked nape (az090, az135).
  Critique: the extremities are not chunky — from az000 the hands are thin paddles no wider than
  the wrist and the forearm barely out-sizes the stick upper arm (STYLE: chunky extremities; brief:
  BIG hands). Diagnosis: build_arm sections: forearm 0.058/0.050, palm 0.052/0.024, knuckles
  0.056/0.022, fingers 0.0155/0.0175 x 0.066 long. Fix: scale the hand ~1.25x (palm 0.064/0.030,
  knuckles 0.068/0.028, fingers 0.019/0.021 and 20% longer, thumb likewise) and the forearm bulge
  to 0.064/0.056.
- r10 — 1134 tris. Result: better — the hands are now big mitts with thick fingers and the forearm
  swells (az045, az135, hero). Critique: the signature ears vanish in profile (az090: a small
  triangle behind the brow) and read as thin spikes from the top — they point straight sideways.
  Diagnosis: J['eartip'] (0.43, 0.03, 1.03) is almost pure +x from the root (0.19, -0.075, 0.95).
  Fix: sweep the tip back and up to (0.40, 0.11, 1.05) so the ear shows as a long back-swept blade
  from the side and top while keeping its width in front.
- r11 — 1134 tris. Result: better — the ears read as long back-swept blades in profile and from
  the top, still wide from the front. Critique: the torso is a lofted egg (hero, az045): six rings
  at an even 0.065-0.075 m pitch give equal thin bands and a smooth gradient — the tube look the
  brief warns about. Diagnosis: ring z levels C .335, H .41, B1 .475, B2 .55, CH .615, S .67.
  Fix: uneven rhythm — B1 down to .455 (belly underside), B2 up to .565 (belly top) so the belly
  front is one big sagging plane with a clear underside plane below and the chest shelf above.
- r12 — 1134 tris. Result: better — the belly is now one big sagging front plane over a clear
  underside plane with a chest shelf above (az000, hero); torso bands no longer equal.
  Decision: the base reads as a goblin from every view (pear head, hooked nose, swept ears, hunch,
  pot belly, bowed knees, big hands/feet). Remaining face work (eye sockets, brow, mouth corners,
  cheek planes) is stage-2 territory. Lock at r13.
- r13 — LOCK. 569 verts, 574 faces, 1134 tris, edge sha256 fa2eaf4f89fdfc6b (stage1_lock.json).
  Harness orbit on the grey s1.glb renders every view empty (metrics.json only, no sheet) — the
  grey GLB has no materials; noted, not a kit edit.

## Stage 2
- r01 — 1150 tris, gates PASS, min IoU .992. Fix (from the lock critique: no eye sockets, the eye
  band was a 3 cm recessed strip): opened the eye face to 0.065 m tall by moving EB/ET/BR cols 1-2,
  then an inset (topo #1) pushed 1.4 cm in. Result: better — two clear sockets under the brow (az000).
  Critique: the sockets are square windows (az000, close-up) — mechanical, no expression.
  Diagnosis: the inset's 4 inner verts are a scaled copy of the rectangular face. Fix: shape them
  — inner-top corner pressed down under the frowning brow, outer corners lifted — a slanted
  almond, deeper at the top.
- r02 — 1150 tris, PASS, min IoU .992. Result: better — slanted almond sockets, the inner corner
  pressed under the frowning brow: an angry squint (close-up az000/hero).
  Critique (rig readiness, the brief's first stage-4 check): the neck has ONE ring (N1) between the
  shoulder ring S and the jaw ring J0, so a head turn/nod will fold it. Diagnosis: band S->N1 is the
  whole neck (5-6 cm) with no loop. Fix: a full loop (topo loopcut) through band S->N1 at t=0.5,
  pulled in 6% toward the neck axis so the neck keeps a waist; S, loop, N1, J0 = 3 loops at the joint.
- r03 — 1174 tris, PASS, min IoU .992. Result: neck now S / new loop / N1 / J0 (wire az090); no
  visible change in clay, as intended. Orchestrator review of r03: reads as a goblin at once;
  priorities ears (flat spikes), mouth (plain slot), eyes/fangs/clothes as pieces, mid palette.
  Critique: the ears are flat knife blades (top view, az135: 2-4 cm thick, a flat front face) — no
  cup, no weight. Diagnosis: ear rings use t = 0.022/0.018/0.012 and the front (idx 4-5-0) is
  nearly flat. Fix (r04): thicken the back of each ear ring, inset the two front faces of the middle
  segment and push the inset back into a cupped inner ear, and droop the ear 9 degrees about its root.
- r04 — 1206 tris, PASS, min IoU .954. Result: better — ears thicker (top view), cupped slot on the
  inner face (az045), drooped 9 degrees (az000). Critique: the mouth is a straight horizontal slot
  across the face (az000, hero) — no grin, the overbite barely shows. Diagnosis: rings L0/M/U are
  level across cols 0-3. Fix: vertex moves only — mouth line M curved up and back to grinning
  corners at cols 2-3 (+0.015-0.02 m), upper lip U lifted with it, lower lip L0 pulled back 0.7-1 cm
  so the upper jaw overbites.
- r05 — 1206 tris, PASS, min IoU .954. Result: better — the mouth curves up into grinning corners
  and the upper lip overbites (close-up az000/az045). Critique: the inner-ear cup is a thin slit
  (close-up hero) — reads as a cut, not a bowl. Diagnosis: inset amount 0.26 leaves the inner faces
  small; pushed only 0.9 cm. Fix (final stage-2 round, with orbit): inset 0.16 and push 1.2 cm.
- r06 — 1206 tris, PASS, min IoU .954 (orbit run). Result: better — the inner ear is now a readable
  groove (az045). Stage 2 done: 3 logged topo ops (eye inset, neck loop, ear-cup inset); all other
  work vertex moves (eye opening, almond shape, grin, overbite, ear thickness + droop).

## Stage 3
- r01 — 1542 tris, 8 colours, gates PASS. Paint: skin / skin_dark (brow, sockets, inner ear, claws)
  / belly (paler, on the belly-plane loops) / leather mouth band on the M-ring faces; pieces: gold
  lens eyes + pupil + glint, 4 upper fangs, 14 claws (from recorded digit tips), belt + buckle,
  front/back loincloth fitted by ray casts. Result: reads as a goblin in colour at once.
  Critique: the loincloth flaps are flat vertical planks (az090 colour: two thin lines; az000: a
  narrow board). Diagnosis: flap rows stacked straight down at a constant 1-2 cm off the body.
  Fix: flare the hem out 4.5 cm and bow the mid row, widen the flaps to 0.125/0.13 half-width.
- r02 — 1542 tris, PASS. Result: better — the flaps flare and bow away from the legs (az090 colour,
  hero). Critique: the head is one flat green apart from the brow (hero, top) — no value plan on
  the biggest mass (STYLE §6). Diagnosis: region rule paints only brow/socket/ear. Fix (final
  stage-3 round, with orbit): darker crown — the FH->TOP band and the cap (upward faces above
  z 1.035) in skin_dark, leaving a lighter forehead band between crown and brow.
- r03 — 1542 tris, 8 colours, PASS (orbit run; harness "orbit holds, head reads"). Result: marginal —
  the crown is darker but under the studio top light it only reads as a slightly deeper green
  (hero); brow-forehead-crown banding is subtle. Stage 3 closed at the round budget.
  Triangles: body 1206 + pieces 336 = 1542.

## Stage 4
- r01 — gates PASS (clips, weights, lock, glbcheck OK). Posed wire: neck (3 loops) and knees bend
  cleanly; move f013 shows a real knee lift. Critique: the attack wind-up is invisible (attack_f008
  hero: only claw tips poke over the crown) — the right arm swings BACK behind the big head.
  Diagnosis: bone-local X on these down-pointing arm bones is negative = backward (the shins confirm:
  -X bends the knee back), so upperarm.R -150 raised it behind; forearm -15 in move hyper-extends
  the elbow for the same reason. Fix: flip the arm signs — upperarm.R +150 wind-up in front/over the
  head then +40 swipe, forearm flex positive in attack and move.
- r02 — PASS. Result: worse — the arm now winds up behind the back (attack_f008 az090). Probed the
  axes in Blender (scratch axes.py): on these down-pointing bones +X swings the tail BACK and up,
  on the spine/hips +X leans forward, +X on the ear lifts it. So r01's arm signs were right (the
  hand was simply hidden behind the big head in hero), and the real bug is the knees: shin -X in
  move/attack hyper-extends them forward. Fix (r03): restore r01 arm values; shins positive
  (flex) in move and attack; lunge thigh.L -X (forward).
- r03 — PASS (orbit: "orbit holds, the head reads"; glbcheck OK). Result: better — knees now flex
  the right way in move (f007/f013 az090) and the lunge; neck/knee wire clean. Critique: the attack
  wind-up still hides the raised claw behind the huge head from the left side (attack_f008 az090).
  Diagnosis: pure X swing keeps the arm in the sagittal plane, straight behind the skull. Fix
  (final round): abduct upperarm.R +40 Z at the wind-up (probed: +Z on the .R upper arm swings it
  outward and up) so the claw is raised beside the head.
- r04 — all gates PASS (orbit holds, glbcheck OK). Result: mixed — the wind-up claw now shows
  beside the head in hero (attack_f008), but the X+Z Euler mix leaves the hand at jaw height, not
  overhead; stage-4 round budget spent, left as a known weakness.

## Totals
- Triangles: stage 1 1134 (locked), stage 2 1206, stage 3/4 1542 (body 1206 + pieces 336).
- Rounds: stage 1 13 (lock at r13), stage 2 6, stage 3 3, stage 4 4. Lock edge sha256 fa2eaf4f89fdfc6b...
- side_by_side.jpg written (no engine goblin: two columns).

## Repair pass (art-director notes, review/ad_notes.md)
- r60 (s3) — note 1: belt/buckle/loincloth rebuilt as closed solids in a cylindrical (angle, z, r)
  frame fitted by rays. Result: open 0 but hit 4 — the belt cut the belly. Cause: pieces were fitted
  to Blender's default quad split, but the kit folds every non-planar quad OUT before QA/export.
- r61 (s3) — note 1 (cont.): fit to a convex-triangulated copy (techqa.triangulate_convex on a
  duplicate), envelope of +-8 deg / +-7 mm around each ray, 4 mm gap; belt 1.7 cm deep x 4.4 cm,
  buckle a box 2 mm proud; flaps split into loincloth_front / loincloth_back (one belt contact each),
  0.7 cm thick tucked inside the belt, 1.4 cm at the hem, cleared 4 mm off legs/seat. Result: open 0,
  hit 0, float 0, zfight 0, gates PASS. 1946 tris.
- r62 (s4) — note 2: loincloth rigid to hips -> flaps 0 flips, but the body-weighted 1.7 cm belt
  folded (47 flips); belt + buckle rigid to hips too. First shoulder ramp made the body worse (7 -> 15).
- r63 (s4) — note 2 (cont.): a debug pass (GOB_DBG, per-clip techqa.measure) located the flips: attack
  only, the RIGHT flank under the armpit (bone heat gave the torso side upper-arm weight) + one knee
  face in move. Moved 20 deg of the wind-up to a clavicle shrug (upperarm.R -135, clavicle.R +22).
- r64 (s4) — note 2 (cont.): torso_off_arm() strips arm weights from the flank below the socket
  (chest/spine only); ramp_joint() smooth ramps at the shoulder (upperarm 0->1 over -5..+6 cm, rest
  clavicle 60/chest 40, arm-side verts only) and the knee (shin over +-3.5 cm). Result: flip 54 -> 7
  (0.36%), all stage-4 gates PASS. Kit note: the stage-4 tech tiles render a posed state (belt/head
  tilted) — the heatmap is painted on rest flags, so only the look is off.
- r65 (s3, stage-2 change) — note 3 (stage 2): hands_and_feet(): back finger splays 12 deg from the
  middle one (index kept: splaying it forward ran it into the thumb, 8 self-hits), whole hand scaled
  about the wrist 1.3x long / 1.25x wide / same thickness (uniform 1.3 dropped the bottom-view IoU to
  .89), toes 1.06x longer along their axis + outer toes splayed 6 deg. digit() now records its ring
  positions (DIGITS) — no geometry change, lock hash holds; TIPS move with the digits so claws follow.
  IoU min .918. Side effect: the flap clearance rays hit the bigger hands and flared the front flap
  into a skirt.
- r66 (s3) — flap clearance rays start 0.25 m out (inside the hanging hands). Flap back to shape,
  gates PASS, 1946 tris.
- r67 (s3) — note 3 (stage 3): claws rebuilt as nail wedges: a 4-vert base rooted 1 cm inside the digit
  on its nail side -> mid ring -> tip hooked toward palm/sole. Gates PASS, 2058 tris. Result: the
  spikes are gone but the nails were buried nubs (hero crop).
- r68 (s3) — note 3 (cont.): nails longer (tip 1.45 x digit size, mid ring 0.6) — they now read as
  short dark hooked nails on separated digits (hero/az090 crops). Gates PASS, 2058 tris.
- r69 (s3, stage-2 change) — notes 4, 5, 7(face): nose tip ring dropped 3.4-4.6 cm and pulled back
  0.6-1.8 cm, top verts dropping more (bridge tapers, hooks over the lip); TOP ring raised 3-4.4 cm
  and drawn in 10% (a domed skull, the FH->TOP band a slanted rim plane); crown paint removed (lid
  now skin green); grin corners (M/U/L0 cols 2-3) up 0.8-1.2 cm; ear root ring back +2.2 cm, mid
  back vertex +1 cm more (round back plane). Gates PASS, IoU min .908. Result: hooked nose in profile,
  rounded skull, grin reads from the front; a small notch at the crown seam (col 0 low).
- r70 (s3, stage-2 change) — notes 6, 7(arm), 5 tweak: B1/B2 centre forward 1.4-2 cm, B2 border
  rising at the centre and dropping 1.2 cm at the side (curved top border on the B2 loop), CH front
  +0.6-0.8 cm; belly paint only below the B2 loop; forearm rings x1.15 about their centres, back of
  the elbow (2 verts x 2 rings) flattened into one plane; crown col 0 raised to 4.4 cm (notch gone).
  Gates PASS, IoU min .904, 2058 tris.
- r71 (s4, final, with orbit) — note 7(fangs): outer fangs 1.7x long, 1.5x wide, root 6 mm higher
  into the lifted lip. Every gate PASS: lock, IoU min .904, hit 0, float 0, zfight 0, slivers 8
  (0.4%), flips 7 (0.34%), open 0, glbcheck OK. Then --review and --compare.
  Repair totals: body 1206 tris (stage 2, unchanged), pieces 852, total 2058. Rounds 60-71 (12).
  Honest residue: in EEVEE the belly still reads as a paler flat front block (the border curve is
  small); nails are small; the attack wind-up still does not clear the head (arm raise cut to 135 deg
  for the shoulder).

## Repair pass 2 (review/ad_notes_r2.md, K=2)
- r90 (s4 baseline, current kit) — every gate PASS except drift: 2 shells (belt, one claw). Must-fix 0 = item 2.
- r91 (s3, debug print) — critique: the buckle is a white blade at the belt front (az090). Diagnosis: the belt's
  front face lies on the belly underside at ~58 deg from vertical (outer top y -.268 z .45 -> bottom y -.196 z .406),
  and the old buckle's depth was an offset along -Y, i.e. a sheared 5.7 mm plate on that slope.
- r92 (s4) — item 1 fix: buckle rebuilt in the belt face's own frame (t down the slope, n outward): 3.2 x 3.2 cm,
  1.6 cm deep, back sunk 5 mm (sides 8 mm), front edges bevelled 4 mm. Result: better — a small cream block under
  the belly, no blade in az090/hero; buckle slivers 2 -> 0 (total 8 -> 6). Drift still 2.
- r93 (s4) — item 2: belt + buckle bind(body=), claws bind(body=). Claw drift 0; belt 66 flips (3.5%) and still
  drifts. Diagnosis: nearest-surface transfer gives the belt's outer flank verts the hanging forearm's weights.
- r94 (s4) — waist_weights(): each belt/buckle vertex takes the weights of the skin straight in from it (horizontal
  ray to the waist axis), torso bones only. Belt flips 0, still drift 1: the waist skin at the flank/back is
  thigh-dominant (bone heat), so a torso-only belt slides over it in a stride.
- r95 (s4) — waist_weights() allows thigh.L/.R too (the ray keeps each section's weights equal inside/outside,
  so the band moves as a unit). Every gate PASS: drift 0, flips 7 (0.34% / 0.30% area). Items 1-2 done.
- r96 (s4, stage-2 + stage-3 change) — item 3 critique: az090 torso front is a near-straight wall and the belt
  pokes 2 cm past it. Diagnosis: the belt sits on the belly underside (B1 -> H), its 1.7 cm radial depth reaching
  the B1 front. Fix: B1 cols 0-1 forward 4.0/2.9 cm and up 1.8/1.6 cm (the gut's low front corner), belt front
  lowered 1.6 cm (zc .428 -> .412 at the front, back unchanged). Result: better — in az090 the belly overhangs the
  belt; IoU min .904 (az090 .917). Gates PASS, flips 8 (0.39%).
- r97 (s4, stage 3) — belly paint: every face under the B2 loop (piecewise-linear arch in x), not a z box. Result:
  marginal — B2 was barely arched, so the top border still read straight (az000).
- r98 (s4, stage 2) — B2 col 1 down 3.0 cm, col 2 down 6.8 cm (slid along the surface): the loop arches and the
  pale patch now has a peaked, curved top in az000/hero. IoU min .904. Gates PASS. Item 3 done.
- r99 (debug rounds, same number reused; GOB_DBG/GOB_DBGF per-frame flip counts) — item 4 critique: purple at the
  .R shoulder top-front (hero/az000). Diagnosis: not asymmetric weights (ramp_joint already mirrors both sides) but
  the attack wind-up: only the right arm rises 125 deg, and the short socket->deltoid band (S2-S3 -> d0-d1) collapses
  below 20% of its area in frames 7-17; the left arm never rises that far. Tried and rejected: wider/shifted
  shoulder ramps, clavicle 0/-30/45/55/75, less raise (-100..-40 with more abduction; >60 deg still folds), twist
  +-30, an extra logged shoulder loop (24 flips: both halves fold), elbow flex 95 (elbow folds).
  Fix kept: smooth_weights() (4 Laplacian passes, r 9 cm, both shoulders, after the ramp) + flatten of the S2-S3-d0-d1
  quad (splits on its short diagonal); clavicle.R shrug 22 -> 32 and upperarm.R -135 -> -125 (so the raised pose is
  near-unchanged). Result: attack flips 6 -> 1 face; total flips 7 -> 3 (0.14% / 0.10% area). Item 4 partly done.
  Should-fix O8: nose bridge 20% narrower (x .037 -> .030), tip ~12% wider. IoU min .906. 2070 tris. Gates PASS.
- r100 (s4, final, with orbit) — every gate PASS: lock, IoU min .906, hit 0, float 0, zfight 0, slivers 6 (0.3%),
  flips 3 (0.14% tris / 0.10% area), drift 0, glbcheck OK, orbit holds. Then --review and --compare.
  Pass-2 totals: body 1206 tris, pieces 864, total 2070. Rounds 90-100 (11). Residue: one collapsing triangle
  pair at the right shoulder in the attack wind-up (purple); the buckle faces down-forward with the belt, so it is
  small in az000; loincloth flaps (O5) untouched.
