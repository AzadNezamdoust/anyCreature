# Crab (opus) — round notes

Stage 0: blueprint.json drawn (carapace 0.95 x 0.64 m, rim z 0.31, top 0.445, eye tops 0.49; claws held forward
and raised, palm 0.2 tall; 4 legs per side fanning forward -> back, knees just outside the rim, tips on z = 0).

Topology plan: concentric 16-vertex half rings (top plateau, shoulder, toothed rim, rim underside, three body rings,
sternum), front seam -> left flank -> back seam. Body sectors are laid out for the limbs: claw = sector 4-5 on both
body bands (hexagonal arm), legs = sectors 6-7, 8-9, 10-11, 12-13 of the lower band (diamond sections, dark/pale
border along the front/back edge), spacer sectors between them.

## Stage 1

**r01** — first build: 932 tris, gates PASS, blueprint IoU side/front/top .78/.83/.69.
- Critique: worst = the legs are needles: thin straight spindles that fan out like pins (az000, az090); no knee,
  no merus mass. From the front the crab reads as a table on pins.
- Diagnosis: leg diamond sections hu 0.030-0.040 / hf 0.024-0.030, knee z 0.29-0.32 (below the rim) so the
  merus -> lower leg line is almost straight.
- Fix: thicker diamonds (merus 0.05 tall) and a real arch: merus runs out under the rim to a mid ring just
  outside it, then rises steeply to a knee at z 0.34-0.38 above the rim; lower leg drops to the tip.
- Result (r02): knees now peak just outside the rim, legs thicker; better but still light. 932 tris, IoU .79/.80/.71.

**r02 -> r03**
- Critique: worst = the claws, the signature, read as antlers from the top (a long thin arm, a palm no wider than
  the arm, stubby fingers) and as two small boxes from the front (az000).
- Diagnosis: claw sections: elbow/wrist 0.09 m from the body each, palm hexas hu 0.085-0.100 / hs 0.056-0.068,
  fingers 0.07 long.
- Fix: shorter arm (elbow and wrist pulled in), a swollen palm (hu 0.12, hs 0.085 at the middle ring), fingers
  0.10-0.11 long and thicker.
- Result (r03): palm swells but at full-body scale the claws are still small (palm 18 % of the carapace width)
  and from the front they are two boxes seen end-on, level with the body. 932 tris, IoU .77/.80/.72.

**r03 -> r04**
- Critique: worst = the front view (az000) reads "hamburger on pins": the claws are hidden end-on inside the body
  outline. The iconic crab front has two big raised mitts to either side, their pincers seen side-on.
- Diagnosis: claw path points straight forward at body height (palm z 0.29-0.31, direction -Y), palm hs 0.085.
- Fix: palm 1.2x bigger (hu 0.14 / hs 0.10), raised (palm z 0.33-0.35, top above the carapace), and turned ~45 deg
  inward so the pincers point at each other in front of the face (the resting chela pose); elbow further out.
- Result (r04): top view now says crab (two big mitts pinching in front); front view has two raised claws flanking
  the shell. 932 tris, IoU .75/.75/.69 (the blueprint claws were drawn thinner/straighter; the model is the truth now).

**r04 -> r05**
- Critique: worst = the shell reads as a hamburger from the front and side (az000, az090, az180): a flat lid-topped
  dome, a thin level rim and a body band of equal height stacked as three horizontal layers.
- Diagnosis: every carapace ring is level (rim z 0.31 all round, top plateau 0.445 at 0.40 scale), so the rim line
  is straight and the plateau is a big flat ellipse.
- Fix: carapace profile: rim high at the front (0.325) sweeping down to the flanks (0.29) and back (0.30), the
  shoulder ring higher (0.425, front 0.41), a smaller, higher plateau (0.42 scale, 0.46); leg coxae 5 mm lower.
- Result (r05): rim line now sweeps down to the flanks, plateau smaller; a subtle gain. 932 tris.

**r05 -> r06**
- Critique: worst = still the stacked "hamburger" from az180/az000: under the rim a pale body band of almost the
  carapace's width shows as a second layer (the back overhang is only 0.04 m).
- Diagnosis: body rings bt/bm/bb are near-vertical copies of B (0.96 scale at the bottom), B's back vertices at
  y 0.25-0.265 against a carapace back at 0.305.
- Fix: the body becomes a keel that hides in the rim's shadow: bb scaled 0.85 and the sternum 0.45 toward the
  centre, B's front/back vertices pulled in (front -0.235, back 0.235).
- Result (r06): the body now tapers under the rim (a keel toward the sternum); the layered read from az180 is
  weaker but the level camera still sees the leg-root band. 932 tris. Accepted; carapace volume revisited later.

**r06 -> r07**
- Critique: worst = the pincer does not read (az045, hero): the fingers are 0.07 m stubs, a notch in the end of a
  faceted lemon; the signature needs two clear fingers, as long as the palm, with daylight between them.
- Diagnosis: one finger section + tip each (dac/pol) placed 0.05-0.08 m from palm2.
- Fix: each finger gets a base and a mid section (quad) and a tip 0.17 m from the palm front; dactyl arches up then
  hooks down, pollex runs level then hooks up; a 0.05 m gape at mid-length.
- Result (r07): two fingers with daylight between them read in top, az045 and hero. 964 tris.

**r07 -> r08**
- Critique: worst = the walking legs: from the side (az090) a comb of long needles, from the front thin sticks;
  the dactyl alone is a 0.14 m spike and the knee barely rises above the rim, so the leg is one straight taper.
- Diagnosis: ankle rings at z 0.12-0.13 (so the pointed tip segment is long), knees at z 0.29-0.38, diamonds
  0.026-0.050 tall.
- Fix: knees up to z 0.37-0.42 (a real arch above the rim), ankles down to 0.08 (short pointed dactyl), diamonds
  ~15 % thicker (merus 0.055 tall).
- Result (r08): the legs arch from the front and the dactyl is a short point, but the lower legs drop almost
  vertically (66 deg): in az090 they are a row of posts, a table, not a sprawl. 964 tris.

**r08 -> r09**
- Critique: worst = stilt lower legs (az090, az135): a crab stands in a low sprawl with its feet well outside
  the knees.
- Diagnosis: knee x 0.575-0.615 / z 0.40-0.42, ankle only 0.13-0.15 further out.
- Fix: knees in and down (x 0.56-0.595, z 0.35-0.385), ankles and tips out by 0.02-0.03: the lower leg leans ~58 deg.
- Result (r09): legs sprawl more from the front and top; from the side a crab's legs are foreshortened toward the
  camera anyway, the comb read there is anatomical. 964 tris.

**r09 -> r10**
- Critique: worst = the carapace, the biggest mass, reads as a pie dish (hero, az045): a big flat elliptical lid
  (the 16-gon plateau) on a thin band of radial strips; no crown, no shield.
- Diagnosis: the top ring capped by one planar n-gon at 0.42 scale / z 0.46; the shoulder ring at 0.74 scale.
- Fix: replace the lid with a crown: the top ring at 0.50 scale / z 0.455 fans to one peak on the seam
  (0, 0.01, 0.49), so the top is a low faceted pyramid whose ridges radiate from the crown (stage 2 flattens
  them into a few bold planes); shoulder ring a little wider (0.78) and higher (0.43).
- Result (r10): the lid is gone; the shell is a low faceted crown rising to one peak, top view reads as a shield.
  966 tris, IoU .76/.72/.71. The base reads as a crab from top, front, side and 3/4 -> lock.

**r11 (lock round, orbit)** — no geometry change.
- Result (r11): LOCKED — 485 verts, 510 faces, 966 tris, edge sha256 8ecd6e614c1117de. Orbit holds from every
  azimuth (the harness only advises that no head chain exists: a crab has none).

## Stage 2

**s2 r01**
- Critique: worst = the carapace shoulder is a smooth run of 15 thin radial facets per side (hero wire): the tube
  look on the biggest mass; no deliberate planes.
- Diagnosis: top + shoulder ring vertices follow the smooth outline S, so each sector is its own facet.
- Fix: flatten the top/shoulder vertices in four groups per side (frontal slope, anterolateral, branchial
  flank, back) so the shell reads as a few bold planes.
- Result (r01): shoulder planes read in the close-ups; the rim band keeps its teeth. 966 tris, min IoU 0.997.

**s2 r02**
- Critique: worst = each leg below the knee is one long straight spike (close az090, back34): the knee and
  the ankle do not read, so the legs look like needles, not jointed crab legs.
- Diagnosis: the knee -> ankle band is a single straight taper (two rings, no middle).
- Fix: one loop per leg in the knee -> ankle band (logged), swollen 1.3x (the propodus), knee and ankle
  rings pinched (0.88 / 0.85): segments with joints.
- Result (r02): legs now segment: thin knee, a swollen propodus, a pinched ankle, a short dark-to-be point.
  1030 tris, min IoU 0.975.

**s2 r03**
- Critique: worst = the claw palm is a faceted lemon with a flat hexagonal back plate (az045 far claw reads as a
  cube, hero near claw a blob); the fingers are shorter than a third of the palm.
- Diagnosis: palm0 (the heel) as big as the palm front, so the palm is a prism; finger tips 0.10 m from palm2.
- Fix: taper the heel (palm0 0.78x, wrist 0.9x), bulge the palm middle ring 10 %, fingers 0.04 m longer with
  the tips hooking toward each other.
- Result (r03): the palm tapers from a heavy middle into the wrist (a glove), fingers longer and hooked; the far
  claw still reads as a block when its fingers point at the camera (foreshortening). 1030 tris, min IoU 0.95.

**s2 r04**
- Critique: worst = the front of the shell has nowhere for the eyes: stalks stuck on a smooth slope would read as
  pins glued on (BRIEF §2.6: eyes in the topology).
- Diagnosis: the frontal shoulder face over the orbit notch (mid/rim sector 1-2) is one flat quad.
- Fix: inset it (logged) and sink the inner quad 18 mm: an orbit socket the stage-3 stalk grows from.
- Result (r04): orbit sockets sit in the frontal slope behind the claws; the eye stalks (stage 3) will rise out of
  them above the claw line. 1046 tris, min IoU 0.95; gates PASS. Stage 2 final (re-run of r04 with the orbit).

## Stage 3

**s3 r01** — paint from stage-1 part labels (every base vertex is tagged ring/leg/claw/finger as it is built;
stage-2 loops by op number): carapace #c8502e with the tooth faces of the rim band in the darker ridge
#8e3420; everything under the rim edge #efc9a0 (the border is the rim ring); leg diamonds dark on top / pale
underneath (the border is the front/back edge line); dactyl points and finger ends #2a1c18. Pieces: eye stalks
from the orbit sockets, black bead eyes with a small shine, five barnacles (asymmetric) on the back of the shell.
- Result (s3 r01): 1306 tris, 6 colours, gates PASS. Reads as a crab from every close view.
- Orchestrator review of s3 r01: the carapace top is a radial fan of thin triangles meeting at one pole
  (procedural), and the claws read as boxy blocks. Both are stage-2 vertex work: back to stage 2 (rounds 5-6).

**s2 r05** (after the s3 r01 review)
- Critique: worst = the crown fan: fifteen thin triangles per side meeting at one pole (top, hero) reads
  procedural, not hand-cut.
- Diagnosis: the crown vertex and the level top ring at 0.50 scale; the r01 flatten groups only touched the
  shoulder band, the fan stayed a cone.
- Fix: a raised central plate (crown + top-ring vertices 0-3 and 12-15 levelled at z 0.485, the front edge
  reaching 2 cm further over the eyes), a single frontal and back slope hinged on the plate edges, and three
  facet panels per side (top+shoulder vertices of sectors 3-6, 6-9, 9-12) projected onto planes through the
  crown (weighted plane fit, pinned hinge vertices). Replaces the r01 four-group flatten.
- Result (r05): the top reads as a raised central plate with three cut panels per side (top view, hero); the
  fan edges still exist in the wire (the locked topology) but no longer shade as a radial fan. 1046 tris,
  min IoU 0.929.

**s2 r06**
- Critique: worst = the claws are boxy blocks (hero far claw, az000): hexagonal prisms with flat tops, a heel
  plate as big as the palm, a straight upper finger.
- Diagnosis: palm rings are flat-topped hexas (top/bottom corners at +-0.8 hs), heel 0.78x; the dactyl rings
  sit on the straight line palm -> tip.
- Fix (claw shaping only): heel 0.62x; each palm ring pinches its top and bottom pairs (0.66-0.74) and pushes
  its side corners out (1.04-1.14) -> a swollen round mitt; the dactyl arches up (mid ring +4 cm) and hooks down
  at the tip; the pollex tapers (0.88 / 0.66) and turns up; daylight stays open between them.
- Result (r06): the palms are swollen rounded mitts tapering to a thin wrist, the dactyl arches and hooks down
  onto a tapered pollex with daylight between (back34, az000, az045). 1046 tris, min IoU 0.92. Stage 2 final
  (r06 re-run with the orbit).

**s3 r02** — no stage-3 change; re-render of the paint and pieces on the new stage-2 shell and claws.
- Result (s3 r02): 1306 tris (body 1046 + pieces 260), 6 colours; rounded mitts with dark hooked fingers,
  the cut shell plate, eye stalks with black beads, barnacles. Stage 3 final.

## Stage 4

**s4 r01** — rig from J: body; per leg merus (coxa->knee), carpus (knee->ankle), dactyl (ankle->tip); claw arm,
fore, claw (wrist -> pollex tip), finger (dactyl hinge -> hooked tip); eye stalk bone; .L mirrored to .R.
Automatic weights; eye stalk/bead/shine to the nearest eye bone, barnacles rigid to body. Clips: idle 48
(fingers open/close, body bob, stalk twitch), move 24 (two alternating leg sets lift, body sways along X and
rolls: a sideways scuttle), attack 32 (claws rise and open, snap forward and shut, body rocks).
- Critique of r01 posed renders (+ printed bone tails, CRAB_POSE=1): worst = the attack "raise" swung both
  claws down and inward across the face; leg lifts in move went sideways. Diagnosis: the kit's default bone
  rolls leave local X at arbitrary angles on these out-and-up limb bones (arm +30 X moved the claw tip down).
- Fix (s4 r02): align every bone's roll so local Z points up (forward for near-vertical bones): +X now lifts
  a bone's tip on both sides (checked per bone). Retuned: move lifts merus 13 / carpus 6, body roll 2.5 deg and
  sway 3.5 cm along X; attack raises arm 30 / fore 12, fingers open 32, then thrusts and shuts.
- Result (r02): gates PASS, glbcheck OK. Attack raises both claws over the face and snaps them forward and down;
  move lifts alternating leg sets while the body sways side to side; idle opens the fingers 0.1 m at the tip.
  Skin holds at the knees and claw joints (wire); the arm roots stretch the front underside on the raise.

**s4 r03** — final run with the orbit; no change.
- Result (r03): all stage-4 gates PASS, glbcheck OK (anims attack/idle/move), orbit holds. `--compare` written
  (no engine creature: two columns, stage-1 base | final).

## Triangles per stage
stage 1: 966 · stage 2: 1046 · stage 3/4 total: 1306 (body 1046 + pieces 260) · 6 colours.
Rounds: stage 1 = 11 (lock r11, edge sha256 8ecd6e614c1117de…), stage 2 = 6, stage 3 = 2, stage 4 = 3.
Kit note: default bone rolls from armature() leave local X arbitrary on out-and-up limb bones; the crab aligns
rolls itself (set_rolls) before skinning.

## Repair pass (AD notes round 1, `review/ad_notes.md`)

**STAGE-1 UNLOCK (note 1, allowed by the note).** Why: note 1 asks for legs ~20 % shorter with the knee raised
well above the rim; the stage-2 min IoU was already 0.92, so moving the leg joints in stage 2 would break the
IoU > 0.9 gate and leave J (the rig skeleton) out of step with the mesh. Only the walking-leg joints (J l1-l4,
via `leg_plane`) and the leg section sizes changed; body, claw and crown code untouched. Old lock moved to the
scratchpad; re-locked in r61. Topology is identical, so the edge hash is unchanged (8ecd6e614c1117de); pos hash new.

**s1 r60** (note 1) — legs laid out per plane: fan -25 / -5 / +14 / +33 deg, reach ~13 % shorter, knees z 0.37-0.455,
merus diamond 2:1 (hu .055 / hf .032). Result: knees arch above the shell from az180/back; from az000 the merus
still hides behind the claw. 966 tris.
**s1 r61 (lock)** (note 1) — knees pushed 3 cm further out so the knee clears the claw in az000; knee angles
44-68 deg (varied). LOCKED, 966 tris, gates PASS, orbit holds.
**s2 r62** (notes 1, 2, 3) — legs: logged merus loop per leg, shaped into a paddle (1.65x tall, 1.15x deep, arched
+12 mm), plus the old propodus loop; crown: two logged rings round the pole (plate edge at 0.52, band at 0.74),
the plate one plane per side (a soft seam ridge), five panels per side hinged on the plate edge, soft crease on
the band; teeth: rim verts 3/5/7/9 out 20-26 mm, notches in. Result: teeth read in top/hero, plate + ring read,
paddle knees arch. 1230 tris, min IoU 0.93, slivers 14. Pole valence stays 16/half: it is locked topology (see end).
**s2 r63** (notes 5, 6) — palm outer face cut into two planes; dactyl root seated 20 % into the palm; gape opened
(dactyl +9 deg, pollex -6 deg); orbit floor reshaped to a compact quad so the socket walls are broad bevels.
Result: wider gape in hero; the yellow slivers at the stalk roots are gone (14 -> 6, 0.5 %). min IoU 0.92.
**s3 r64** (notes 6, 7) — stalks with a flared root (r .034, 1.5x), leaning 18 deg out; rounded 6x3 eye bulbs
(r .025, 1.3x the stalk top) with shine; barnacles: one cluster of four at the left rear panel, 1.5-2x bigger,
sunk 30 % (ray-cast onto the shell) + one stray right. Result: gates PASS (hit/float/zfight 0), 1538 tris.
**s4 r65** (note 4) — move clip rebuilt as an alternating tetrapod gait (L1 R2 L3 R4 / L2 R1 L4 R3), tips lift
0.11 m (~14 % of the leg) and reach 1.5 cm out, body sways 3 cm sideways and bobs 1 cm; planted legs solved per
key by a planar two-bone IK (`leg_ik`) from J. Result (CRAB_POSE bone tails): planted tips drifted 3 cm with
y error. Diagnosis: `set_rolls` used a forward reference for bones with |d.z| > 0.9; the new steeper carpus bones
(~0.96) crossed it, so their X was not the leg-plane normal. Fix: threshold 0.985.
**s4 r66** (note 4) — roll fix + a merus yaw about world vertical for the off-plane part of the sway (splayed
l1/l4). Result: planted tips fixed to the millimetre at f1/f7/f19, swing tips exactly +0.11 m; all stage-4 gates
PASS, fold-overs 0.00 %, 1538 tris. Steps read in move_f007 (near L1/L3 up, L2/L4 planted).
**s4 r67 (final, orbit)** (note 1 follow-up) — propodus swell graded per leg (l1 1.45 -> l4 1.22) so the four
legs are not identical spikes. Result: every gate PASS (IoU min 0.92, lock assert PASS, hit/float/zfight 0,
slivers 0.4 %, fold-overs 0.00 %), glbcheck OK, orbit holds. `--review` and `--compare` rebuilt.

Repair status: note 1 fixed (stage-1 unlock logged above); 2 partly: plate + ring + 5 panels/side read as planes,
but the crown pole keeps 16 edges per half because the fan is locked stage-1 topology (stage 2 cannot remove
original edges and the unlock was granted for the legs only), so the "<= 8 edges" check still fails in wire;
3 fixed (4 teeth/side, clear in top view, subtle in beauty views); 4 fixed (IK-planted tetrapod gait);
5 fixed; 6 fixed (chamfer done as a reshaped orbit floor: broad bevel walls, not an extra loop, which would have
re-created slivers in the narrow face); 7 fixed.
Repair triangles: stage 1: 966 · stage 2: 1230 · stage 3/4 total: 1538 (body 1230 + pieces 308) · 6 colours.
Rounds 60-67 (8). Lock edge hash unchanged 8ecd6e614c1117de (positions re-locked).

## Repair pass 2 (AD notes round 2, `review/ad_notes_r2.md`, K=2)

**s4 r90 (baseline)** — no change; every stage-4 gate PASS on the current kit (drift 0, fold-overs 0.00 % tris /
0.00 % area), so there is no item 0.
**s2 r91 / s4 r92** (note 1, crown)
- Critique: the crown reads as a pie lid: spokes and ring bands shade in colour (close-ups, back34), and the side
  wall under the shoulder ring is a skirt of long thin pleat triangles.
- Diagnosis: the r62 shaping fits five panels per side hinged on the inner ring, then lifts the band ring 6 mm (a
  ring crease); the plate is tilted; the shoulder ring sits at 0.78 of the outline, so the wall to the rim is 13 cm tall.
- Fix: `crown_planes`: a level central plate (pole fan + inner ring, one polygon with straight edges) and four sector
  planes per half (front plateau and back across the seam, a front side and a back side), each through its own
  plate edge; the ridge lines run corner -> shoulder point on spokes 3 / 7 / 13 and the outer ridge heights are
  solved so adjacent planes meet exactly on the ridge spoke (every band/top/shoulder vertex lies on its sector
  plane: no ring or spoke shades). The shoulder ring slides out to 0.85 (front 0.80) onto the planes: the wall is
  about half as tall, its triangles wider.
- Result: top and close-ups show 7 big planes (plate, front, 2 front sides, 2 back sides, back); no band shading.
  1230 base tris, min IoU 0.916, slivers 0.4 %, every stage-4 gate PASS.
**s2 r93** (note 2, legs, stage 2)
- Critique: az090 / hero: the lower legs are straight vertical stakes under a tall stance (spider read).
- Diagnosis: knee -> ankle is one near-vertical taper (J l1-l4 ankle only 8-11 cm out from the knee), the dactyl
  continues the same line.
- Fix tried: knee 2.5-4 cm lower, ankle 4-5.5 cm out and 4-5 cm up (a second bend), tip 5-6.5 cm out, graded
  front -> back (LEG_D; LEG2 = the moved skeleton, used by paint and rig). Result: IoU 0.76 on every view: the
  legs are thinner than the move, so each lower segment loses nearly all of its overlap. At 30 % of the move the
  min IoU is still 0.87. The IoU > 0.9 floor (owner-ratified) blocks the stage-2 leg reshape: kept only a dactyl
  bend (tips 2-2.8 cm further out, graded per leg, so the point angles out-and-down past the propodus line):
  min IoU 0.907.
**s4 r94** (note 2, stage-4 fallback from the notes)
- Fix: the body 4.5 cm (~10 %) lower in every clip; all eight tips IK-planted at every key of idle, move and attack
  (idle/attack re-keyed on unified frames, which also removes the old idle frame-24 finger snap to rest); leg_ik now
  maps targets through the body's keyed pitch, so the attack rock no longer lifts front tips 3.7 cm / sinks rear
  tips 3.4 cm below the floor.
- Result: posed frames crouch with knees bent up above the shell; tips fixed to the mm in attack f9 and move
  f1/7/19; every gate PASS (fold-overs 0.00 %, drift 0). The rest-pose beauty renders cannot show the stance.
**s3 r95** (note 3, barnacles)
- Critique: back34: pale hexagonal prisms that read as nuts, spread over the back panel.
- Diagnosis: `barnacle` = 6-sided prism with a lip, painted the pale 'shine' #d8d0c0, placed on the back plate.
- Fix: 7-sided irregular low cones (base sunk 40 % of r, low shoulder, lip, a dark pit painted 'tip'), a muted
  'barnacle' #9a8474; four in mixed sizes (1-1.8x) clustered on the left rear edge + one small stray right rear;
  axes tilted up from the steep back wall.
- Result: one cluster on the rear edge in back34, dark pits, top centre clean; 7 colours, 1638 tris, gates PASS.
**s4 r96** (should-fix F3)
- Critique: the review frames move f006/f007/f012/f013 caught one A-lift peak and a neutral pair, so the alternation
  could not be seen. Fix: two steps per 24 frames (keys every frame), phased so set A peaks at f6.5 and set B at
  f12.5; lift 0.11 m and 3 cm sway kept. Result: f006 near L1/L3 up, f012 near legs planted and far set up.
**s4 r97 (final, orbit)** — no change. Every gate PASS: lock assertion PASS, min IoU 0.907, hit/float/zfight 0,
slivers 0.4 %, fold-overs 0.00 % tris / 0.00 % area, drift 0; glbcheck OK; orbit holds. `--review`, `--compare` rebuilt.

Repair-2 status: note 1 done (7 planes: plate + front, 2 front sides, 2 back sides, back; wall ~half as tall; the pole
fan stays in wire, valence waived). Note 2 partly: the IoU > 0.9 floor blocks the stage-2 reshape (0.76 full,
0.87 at 30 %); only a dactyl out-bend fits (0.907); the stage-4 fallback lowers the body 4.5 cm with bent knees in
every clip, but the rest-pose beauty renders still show the tall stance. Note 3 done. F3 done.
Triangles: stage 1 966 · stage 2 1230 · total 1638 (pieces 408) · 7 colours. Rounds 90-97 (8).

## Repair pass 3 (AD notes round 3, `review/ad_notes_r3.md`, K=3)

**s4 r130 (baseline)** — no change; every stage-4 gate PASS on the current kit: no item 0.

**STAGE-1 UNLOCK (owner-authorised for the walking legs and the body height; note 1).** `stage1_lock.json` renamed to
`stage1_lock.pre_unlock.json`. Changed in stage1(): (a) the whole body (shell rings, crown, claw and eye joints) sits
`DZ = -0.075` lower, a pure translation (stage 2's PLATE_Z and the crown ridge heights follow it); (b) new walking-leg
joints in J (l1-l4). Nothing else in stage 1 changed. The canonical-order lock renumbers base ids, so `PART` is now built
in the kit's position order (bmkit.canonical_order).
**s1 r131-r132** (note 1) — critique: long straight lower legs, knees above the rim, body a third of its height up.
Fix: knee z .27-.31 (carapace top .415), carpus/propodus drops steeply out, dactyl angles back IN (tip s < ankle s),
below-knee length ~24 % shorter (l2 .45 -> .34 m), fans -45 / -12 / +20 / +55 deg (front 20 forward, rear 22 back).
r131: 8 hits, l1 merus through front rim tooth 7 -> r132: l1 mid section further out and lower. Result: gates PASS.
**s1 r133 (lock)** then **s2 r134-r135** — l2's paddle merus hit rim tooth 9 (stage-2 push 20 mm) -> tooth 9 push 4 mm.
Min IoU 0.91. **s4 r136-r137** — paint scrambled (PART in creation order vs canonical ids) -> fixed as above.
**s3 r138** (note 2) — barnacles: four cones on the left rear rim only (stray removed), sizes 1-1.8x, tint #966856
(r2 #9a8474 35 % toward the shadow red), base sunk 65 % of r (was 40 %), lower shoulder/lip. back34: no pale nut, top clean.
**s1 r139-r140 (re-lock)** (note 1) — critique (idle beauty az090): l2/l3's second bend lies in their own leg plane,
which faces the camera, so they still read as knee + stake. Fix: each tip swept sideways off the leg plane
(l1 -3, l2 -4.5, l3 +4.5, l4 +3.5 cm; front forward, rear back), so the ankle angle shows side-on. My r133 lock moved to
the scratchpad (the pre-unlock record stays); re-locked r140, edge sha256 798fdff6b698df67, 966 tris.
**s4 r141-r143** (note 3) — `leg_ik` now solves in the knee plane (the tip is off it); DROP 0 (body lowered at the
source). Move: 3 deg body roll down toward the side it sways onto, IK targets mapped through the rolled body; swing legs
lift from the coxa (merus +19-21 deg on top of the planted IK pose), so they keep both bends in the air. Measured
(CRAB_POSE): swing tips 0.10-0.12 m (15-17 % of the ~0.69 m leg) at f6 vs 0 at f12 and the reverse; planted tips move
<= 1.3 mm between consecutive frames. Far-side swing knees peak at z .39 (below the .415 carapace top).
**s4 r144 (final, orbit)** — no change. Every gate PASS; glbcheck OK; orbit holds. `--review`, `--compare` rebuilt.

Repair-3 status: note 1 done (stage-1 unlock: two bends per leg, knees under the carapace top, underside .053 m = 15 %
of the body height, pairs splayed; clips keep the IK stance). Note 2 done. Note 3 done. Should-fix crown pole: not done
(a stage-1 plate cap needs front-to-back strip quads at ~6 deg min angle, the sliver limit, and a rewrite of the stage-2
crown planes). Should-fix pleat merge: not done (min IoU 0.91 leaves no room).
Triangles: stage 1 966 · stage 2 1230 · total 1586 (pieces 356) · 7 colours. Rounds 130-144 (15).
