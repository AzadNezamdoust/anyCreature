# Bear (opus) — round notes

## Stage 0: blueprint
Side/front/top outlines from the design numbers: nose-to-rump 1.73 (nose -0.87, rump 0.85, stub tail to 0.905),
shoulder hump 1.01 over the forelegs, rump 0.94, head carried low (skull top 0.84, below the hump line), dished
profile (steep stop at y -0.66, flat short muzzle), small round ears, thick pillar legs, plantigrade paws (hind
foot 0.29 long heel-to-toe). Reads bear: hump, low head, round rump, flat long hind feet.

## Stage 1
- **r01** Built from the blueprint numbers: 16 half rings (6 verts) nose -> tail root + 2 tail rings; legs are 4
  hex levels + a sloping paw top + a flat sole, extruded from the B0-B1 / B4-B5 lower-flank faces; ears from the
  H2-H3 upper-side face. 692 tris. Critique: gate FAIL, 12 face-pair hits. Diagnosis: the shoulder and ham levels
  (inner z .40/.46, inner x ~.115) run their inner walls through the belly faces, and the ham front ridge (y .472)
  pokes ahead of its root ring into the B3-B4 flank. Visual (worst, az090): no hump — the back is a straight line.
- **r02** Fix (gate hygiene): shoulder inner z .40 -> .36, half-depth .112 -> .100; ham centre .600 -> .605,
  half-depth .128 -> .105, inner z .46 -> .40. Result: all gates PASS, 692 tris. Shape unchanged.
- **r03** Critique: az090 — the bear's signature, the shoulder hump, does not read: the top line runs 0.89 (neck)
  -> 1.01 -> 0.955 -> 0.93 -> 0.94, a gentle straight back like a dog's. Diagnosis: top seam / back-edge of
  NK, B0, B2-B5. Fix: keep the hump at ~1.02 and drop the neighbours: neck .86, saddle behind the hump .915,
  loin .895, hip .915, rump .87 (rump lower than the hump, a dip behind it).
  Result: the hump now reads in az090/hero as a peak over the shoulders with a dip behind; 692 tris.
- **r04** Critique: az090/az045 — the legs are dog/hyena legs: thin (forearm 0.18 deep, wrist 0.16) and tapering
  under a massive body; a bear stands on pillars. Diagnosis: FORE/HIND half-widths and half-depths below the
  shoulder/ham. Fix: every lower leg level ~15% thicker (elbow .096x.122, forearm .088x.110, wrist .080x.094;
  knee .094x.124, shin .084x.100, ankle .076x.086), paws broader (hw .092/.090) and a little longer.
  Result: legs read as pillars in az045/az135, better; 692 tris. Still a long-bodied look, but the head is worse.
- **r05** Critique: hero/az045/az090 — the head is a pig/anteater cone: the top line slopes straight from the
  ears to the nose (no stop, no dome), the muzzle tapers to a point. A bear has a domed skull, a steep forehead
  and a short, blunt, flat-topped muzzle. Diagnosis: N0-H3 top seam/back-edge heights (.648 -> .845 in an even
  slope). Fix: muzzle a flat-topped box (.662 -> .700 over 0.16), a steep stop (.700 -> .800 in 0.06), a domed
  skull (.855), muzzle root 0.124 half-wide against 0.205 cheeks; nose at -0.865.
  Result: hero/az045 now show a stop and a blunt muzzle: the head reads bear, not pig; 692 tris.
- **r06** Critique: az000/top/hero — the body is narrow (half-width .28 on a 1.02 hump, legs close together):
  from the front it is a dog, not a massive bear. Diagnosis: the x of every body ring and the leg cx. Fix: body
  rings widened (neck x1.08, chest 1.15, hump 1.18, barrel 1.20, loin/hip 1.18, rump 1.15, rump back 1.10) and
  both legs moved out 0.04.
  Result: hero/az000 now massive and broad; 692 tris. (Blueprint front/top updated to this deliberate width.)
- **r07** Critique: hero/az090 — the torso is a crate: the flank is one vertical wall (lower flank x = widest x)
  over a straight belly line from chest to groin. Diagnosis: v3/v4 x equal to v2 on B0-B4 and flat keel z.
  Fix: a rounder, keeled barrel — lower flank x 0.92-0.96 and belly side 0.88-0.94 of their old x, the belly
  sags between the legs (B1 -0.02, B2 -0.035, B3 -0.02).
  Result: hero shows a rounder barrel with a keel; subtle but the crate wall is gone; 692 tris.
- **r08** Critique: az000/az090/hero — the forelegs are two straight square posts (parallel from the front,
  vertical from the side); a bear's forelegs bow (elbows out, paws toed in) and the forearm leans forward to the
  wrist. Diagnosis: FORE cx .245/.240/.232/.222 and cy -0.20/-0.18/-0.204/-0.22. Fix: elbow out to .262 and back
  to -0.165, forearm .245, wrist .220 and forward to -0.232, forepaw toed in 0.022 (new pawpts param).
  Result: az000 shows the bow (elbows out, paws in), az090 a forward-leaning forearm; 692 tris.
- **r09** Critique: az000/hero — the ears are 4 cm tabs that vanish against the hump from the front; round ears
  set wide on the skull are a bear's front-view cue. Diagnosis: ear() quads (base .036, mid .046, tip .026) and
  ear_tip .915. Fix: a bigger round ear — mid width .060 at 7.5 cm up, tip .034 wide at z .945, leaning out more
  (u x .42) so it sits wide.
  Result: the ears read round and wide from az000/hero — the front view now says bear; 692 tris.
- **r10** Critique: az090 — the head is too small for a stylised asset: 0.42 long on a 1.73 body (1:4.1; STYLE
  wants 1:2.5-3 for a quadruped), 0.37 tall against a 0.62-deep chest; it reads as a realistic bear, not an
  appealing game bear. Diagnosis: head rings N0-H3. Fix: scale the head rings about the back of the skull
  (y -0.45, z 0.66) by 1.15 in x/z and 1.10 in y (the muzzle stays short); the ears ride with it.
  Result: az090/hero — a big appealing head, a nape step below the skull; 692 tris.
- **r11** Critique: az000/hero — the muzzle ends in a flat vertical disc framed by concentric rings: a pig's
  snout. A bear's nose pad leads and the chin recedes under it. Diagnosis: N0 is a planar ring at one y. Fix:
  per-vertex y offsets (new optional third number): N0 tilts (lower verts back up to 4 cm), N1's chin back 2 cm.
  Result: az090 — the muzzle now leads with the nose and the chin tucks under; subtle from the front; 692 tris.
- **r12** Critique: az090/top — the torso is a long sausage (chest to rump 1.15 on 0.6 depth, the flank bands
  run on and on); a stylised bear is compact. Diagnosis: y spacing of B2-B7, the tail and the hind leg. Fix:
  compress everything behind the hump toward it (y' = -0.10 + 0.9 (y + 0.10)): rump end 0.845 -> 0.750,
  nose-to-rump 1.66; ham half-depth .105 -> .095 so its front ridge stays behind its root ring. J updated to the
  leg tables (shoulder/elbow/wrist/paw, hip/knee/ankle/paw).
  Result: az090/hero — compact and chunky, the hump now sits over a short barrel; 692 tris. Blueprint updated to
  the round-6/10/12 design decisions (width, head scale, compression) so the overlay stays an honest reference.
- **r13 (lock)** No geometry change. Reads bear from every view: shoulder hump over the forelegs with a dip
  behind, big low head with a stop and a blunt muzzle, round ears set wide, bowed pillar forelegs with toed-in
  paws, long flat hind feet, round rump and a stub tail. Remaining for stage 2: no face (brow, eye socket,
  nostrils, mouth line), flank bands, paws are plain slabs.
  Locked: 348 verts, 692 tris, edge sha256 7f3f48eaeafbb8c3. Blueprint IoU side/front/top .895/.928/.957; harness
  orbit holds (advise: no head chain in a grey mesh, expected).

## Stage 2
- **r01** Critique: hero — no face: skull to nose is blank. Fix: eye socket = inset (.40) in the N3-H1 stop-side
  face, an almond sunk 14 mm; the brow vertex H1.v1 pushed forward 22 mm / out 14 mm to overhang it, cheekbone
  H1.v2 forward. Result: hero shows a small socket under a brow; IoU min .997; 708 tris.
- **r02** Critique: hero/az000 — the muzzle end is blank and there is no mouth. Fix: nostril = inset (.50) in the
  half nose disc, a flat oval sunk 10 mm, high on the pad; mouth line = partial loop (t .40) through the lower
  muzzle strip (v3-v4) from the disc rim to the cheek quad under the eye, fan terminators at both ends (skull,
  nothing bends), creased 10 mm in and lifting to the corner. Result: az045/hero read a lipped jaw; the disc reads
  "snout" until it is painted as a nose pad; 748 tris, IoU min .997.
- **r03** Critique: hero — the ears are flat cards. Fix: inset (.30) in the ear's forward face, pushed 12 mm
  back. Result: az045 shows a cupped ear; 764 tris, IoU .997.
- **r04** Critique: az045/hero — the muzzle, shoulder, barrel and rump are gently curving loft strips. Fix:
  flatten five planes (muzzle bridge, muzzle side, shoulder blade B0-B1 upper side, barrel lower flank B1-B3,
  rump top-side B4-B5). Result: the muzzle side and barrel read as single facets in az045; 764 tris, IoU min .988.
- **r05 (final s2)** Critique: az045/hero — soft landmarks: no cheek ruff, a timid hump crest, no elbow point or
  heel. Fix: vertex moves only — cheek ruff out/down 22/16 mm, hump crest up 12-14 mm, elbow point back 20 mm,
  knee forward 16 mm, heel back, throat ruff lower. Result: broader jowls and a stronger hump crest in az000/hero;
  IoU min .984; 764 tris. Stage 2 done: 4 logged topo ops (eye socket, nostril, mouth partial loop, ear cup), lock
  assertion PASS. Harness orbit holds.

## Stage 3
- **r01** Paint (6 body regions on stage-1/2 loops: fur, dark stockings below the elbow/knee loops and a dark
  saddle, muzzle ahead of the N3 loop, nose pad on the disc + strip, eye socket, inner ear cup) + pieces: eye
  bipyramids with a glint, 4 toe lumps + 4 hooked claws per paw, shoulder ruff blades. 1436 tris, 7 colours.
  Reads "bear" in colour at a glance. Critique: hero — the ruff blades are small dark triangles flat on the
  shoulder: they read as holes/scabs torn in the fur (the §1 failure), not fur.
- **r02** Fix: ruff redesigned as 6 bold clumps in the FUR colour that break the outline: three at the jowl
  edge behind the jaw, three down the side of the hump, bigger (9-15 cm) and standing off the surface.
  Result: 1436 tris. Worse at the jaw: the jowl clumps hang like fangs/spikes off the cheek in az090/az045; the
  hump clumps roughen the hump outline acceptably.
- **r03** Fix: drop the three jowl clumps; keep the three hump clumps.
- **r04** Critique (orchestrator + own): az090/hero colour — legs and back read near-black and swallow the facets;
  the muzzle is too close to the fur to carry the face from the front. Fix (palette only): legs #4e3726 -> #5a3f2c,
  a separate back saddle #5e4230 (fur stays #6b4a32), muzzle #a58362 -> #b08e6c.
  Gates PASS, glbcheck OK, 1400 tris. Posed wire: the neck and shoulders bend without collapse (attack f22, move
  f17). Colour under the beauty light: legs/back now show their facets. Critique: attack f22 — the bear does not
  rear: it pitches FORWARD onto its forepaws with the rump up. Diagnosis: on the forward-pointing spine bones
  (hips, chest) positive bone-X lifts the front (the opposite of my derivation); limbs keep +X = back.
- **r02** Fix: attack spine signs flipped — hips +32 with thighs -26 to keep the hind legs planted, chest +8,
  neck -14 / head -16 so the reared head stays level; crouch and recovery keys flipped to match.
  Result: WORSE — az090 shows the rump thrown up and the head driven down: r01's signs were right (+X on the
  forward-pointing hips bone pitches the front DOWN); r01's hero-angle frame had misled me.
- **r03 (final)** Fix: r01 attack keys restored. Result: attack f22 az090 — reared on the hind legs, both forepaws
  up and forward, head level, hind feet planted; gates PASS, glbcheck OK (idle/move/attack), orbit run.

## Triangles per stage
stage 1: 692 (locked, edge sha256 7f3f48eaeafbb8c3) · stage 2: 764 · stage 3: 1400 total (body 764 + pieces) ·
stage 4: 1400. Rounds: s1 13 (r13 = lock), s2 5, s3 4, s4 3. Colours: 8 (fur, legs, back, muzzle, nose/claws,
inner ear, eye, glint).
Harness orbit at stage 4 (advise only): az000 head_merged (head 45% of the front view, 7% of its outline clears
the body — the low-carried head sits in front of the hump), az180 head_hidden — both expected for a bear.

## AD repair pass (notes: review/ad_notes.md, round 1 reconciled)
- **r60 (note 1, blocker)** Stage 3: `piece_ruff` removed (paper plates read as shards / a second pair of ears).
  Stage 2: the hump is in the base — top seam/back-edge of B0 +6.0/5.5 cm, B1 +7.0/6.5 cm, B2 +2 cm, NK +1 cm,
  peaking over the forelegs. Result: az090 hump is the highest point, no plate breaks the outline; IoU min .937;
  1364 tris; gates PASS.
- **r61 (note 4)** Stage 2: the three ear quads re-placed (new EAR_NEW table): 38% lower (tip .086 up the ear axis
  vs .173), depth 0.060 at 0.124 wide (48%), base slid out 12 mm / down 8 mm; a logged inset on the tip cap raised
  2 cm into a dome = a round top. Result: az000/hero round half-disc ears; IoU min .92; 1380 tris. Ear cup rim
  quads became slivers (10).
- **r62 (note 3)** Stage 2: the nostril inset ring is re-placed as the nose PAD — the upper front of the disc with
  a straight bottom edge at z .600, 8 mm proud. Stage 3: black = the pad + the top strip behind it (z > .625, not
  the sides); a thin dark lip line (legs colour) on the faces under the mouth partial loop. Result: az000 nose has
  a straight bottom edge, no spade/fangs; a thin pale midline split remains (the seam rim quad, x 0-.008).
- **r63 (note 4 tech)** Ear cup inner ring narrowed (w .75, u .55) and pad side verts moved in: slivers 12 -> 2.
- **r64 (note 5)** Stage 3: eye rebuilt as an 8-sided bead (rim .017x.022, a half-size front ring, apex), 1.5x,
  30% of its depth below the socket floor, the glint ONE small apex facet. Result: solid dark beads with a pin
  glint in az000/hero; hit/float/zfight 0; 1420 tris.
- **r65 (note 6)** Stage 2: wrist level scaled .85 in x/y, elbow level back 3 cm, FO/FC/FI of elbow, forearm and
  wrist flattened into one front plane. Result: az090 the forearm leans to a narrower wrist over a broad paw;
  IoU min .914; slivers 6 (0.4%).
- **r66-67 (note 7)** Palette: 'eye' merged into the nose black; a lighter chest/throat bib #83603f on the
  front-facing NK-B1 faces; stockings darkened 15% (#5a3f2c -> #4e3627). 8 colours. Result: az090 reads bib /
  body / dark legs as three values; hero still reads warm brown, not black.
- **r68 (note 2)** Stage 4: `blend_throat` — 4 Laplacian passes over the spine weights (hips/chest/neck/head)
  in the neck region (y -.56..-.20, z > .40), each vertex keeping its spine share; attack rear neck/head bend
  14/16 -> 4/11 (-15 deg). Result: flips 10 -> 7 (0.49%, PASS but purple still at the throat).
  Diagnosis (per-frame measure, env-guarded debug, since removed): all flips at attack f18/f26 on the NK-B0
  v3-v4 face (±.21, -.33, .52) and the keel, not the neck bone.
- **r69 (note 2)** Stage 4: `blend_all` smooths all deform weights on the chest front (y -.44..-.16, z .34-.76);
  the rear-up arm raise eased (L -70 -> -58, R -55/-60 -> -50/-52, forearms +2..8 to keep the paw up). Stage 2:
  the r05 throat-ruff drop on NK v4 (+12 mm out, -16 mm down) removed — it made the NK-B0 face nearly edge-on
  and it was the face that folded. Result: posed fold-overs 0 (0.00%), no purple anywhere; attack f22 az090
  still reared with the hind feet planted and a forward swipe; 1420 tris; gates PASS; glbcheck OK.
- **r70 (final, with orbit)** No change. All gates PASS (s1 lock match, s2 IoU min .914, s3 8 colours / 1420
  tris, s4 hit 0 / float 0 / zfight 0 / slivers 6 (0.4%) / posed flips 0), glbcheck OK; orbit advise only
  (az000 head_merged, az180 head_hidden: the low bear head, as before). `--review` and `--compare` rebuilt.
  Triangles: s1 692 (lock unchanged) · s2 ~780 base · s3/s4 1420 total. Repair rounds: 11 (r60-r70).
  Left: a thin pale midline split through the nose pad (the seam rim quad of the nostril inset, x 0-.008;
  narrowing it makes needle slivers); ears read small from az090; the lip line is subtle.

## AD repair pass 2 (notes: review/ad_notes_r2.md, round 2 reconciled, K=2)
- **r90 (baseline, current kit)** No change. All gates PASS except drift: 2 shells (the eye beads L/R); hit/float/
  zfight 0, slivers 6 (0.4%), flips 0 (0.00% tris / 0.00% area), lock PASS, IoU min .914, 1420 tris.
- **r91 (must-fix 1 + item 0)** Critique: 4_posed attack f011/f022 — the eye beads stay behind as the head drops
  and lifts (drift 2). Diagnosis: stage 4 binds `piece_eye` rigidly to 'head' while the socket skin carries
  blended neck/head weights. Fix: `bind(eye, rig, body=body)` — the beads borrow the face skin's weights.
  Result: drift 0; attack f011/f022 hero colour show both eyes in their sockets; all gates PASS; 1420 tris.
- **r92 (O2)** Critique: hero/az090 — the lighter chest is a yellow-olive stripe down the shoulder front. Diagnosis:
  the chest rule took side faces (n.y < -.30, |x| < .30) and #83603f leans yellow. Fix (paint only): chest = front-
  facing faces between the forelegs (n.y < -.45, |x| < .20), colour = fur hue at +12% value (#785338). Result: the
  shoulder stripe is gone in hero/az090; the chest under the chin reads a shade lighter in az000; gates PASS.
- **r93 (O3, tried)** Paint the ear cup, its four rim walls and the lower forward ear face light. Result: WORSE —
  the whole ear front turned tan, no dark rim: a flat disc, not a cup. Reverted in r94.
- **r94 (O3)** Diagnosis: the cup inset sits in the short upper forward face (mid -> tip quad, ~4 cm tall), so it
  can only be a bar. Fix (stage 2 vertex move + stage 3 paint): the mid quad's front edge slides 2.6 cm down the ear
  axis (EAR_MIDF_DROP), making the upper forward face tall; the cup's inner ring keeps 80% of that height (was 55%);
  paint the cup only. Result: close-up/az000 — a taller light hollow inside a dark rim; slivers 6, IoU .914.
- **r95 (F2)** Critique: 2_closeups — four identical claws per paw, the outer one splayed. Fix (stage 3): each claw
  runs along the paw axis (heel -> toe centre, the toe-in included) fanned <= 4 deg; sizes .75/1.0/.95/.8 inner ->
  outer, rooted in the toe tip. Result: close-up 1 — claws point forward in a graded row; gates PASS.
- **r96 (F3)** Critique: az000 — the foreleg is still a post. Fix (stage 2): wrist level x 0.85 again (now ~.72 of
  its stage-1 width), forearm level x 0.90, before the front-plane flatten. Result: az000 the leg steps in below the
  forearm; IoU min .909 (az000); gates PASS.
- **r97 (O4)** Critique: az090 — the forearm rakes ~20 deg forward, paws ahead of the hump. Fix (stage 2): wrist and
  both paw loops back 8 cm, forearm level 5 cm (toes/claws built at FPAW2, forearm/forepaw bones follow). Result:
  FAIL IoU az000 .899 (az090 .907).
- **r98 (O4, partly)** Same fix at 6 cm (wrist/paw) and 4 cm (forearm). Result: az090 forearm near vertical (~9 deg),
  paw under the front half of the hump; IoU min .901 (az000; owner floor .9 — the full 8 cm does not fit);
  slivers 2 (0.1%), flips 0, drift 0; posed wire attack f022 / move f017 clean; 1420 tris.
- **r99 (final, with orbit)** No change. All gates PASS: lock match, IoU min .901 (az000), 8 colours, hit/float/zfight
  0, slivers 2 (0.1%), flips 0 (0.00% tris / 0.00% area), drift 0; glbcheck OK; orbit advise only (az000
  head_merged, az180 head_hidden, as before). `--review` and `--compare` rebuilt. 1420 tris. Rounds r90-r99 (10).
  Left: O4 only partly done (6 of 8 cm; the forearm is ~9 deg off vertical), because the IoU floor binds at az000;
  the inner-ear hollow is a rounded quad, not an oval; the pale midline split through the nose pad is still there.
