# raven_wyvern (w4) build notes

Reference sheet present: blueprint.json traced from it is the stage-1 target (not redrawn).
Design: one lofted spine (tail tip -> bill tip, 16 half-rings of 5 verts = 8-gon sections),
legs and wing-arms extruded from flank faces, the leading finger spar extruded from the wrist's back face.

## Stage 1
- r01: 460 tris, gates PASS, IoU side .682 / front .690 / top .488 (top low: no membrane yet).
  Critique: az000/hero: head and neck read as a thin tube with a cone bill; ref head+neck are a big mass.
  Diagnosis: ST rows N1..H3 half-widths .10-.13 and bill .075/.04. Fix (r02): widen neck to .12, skull to .15, bill base .085, bill .05.
  Result r02: IoU .689/.713/.483, 460 tris; head mass better from the front, still a tube neck.
- r02 critique: az000/az090: legs are sticks; the ref has big feathered thighs down to a hock at z .2 and a short scaly shank.
  Diagnosis: leg chain rows 1-2 (w .07/.06). Fix (r03): thigh rows w .085/.07, d .11/.085, running down to the hock at z .205.
  Result r03: IoU .687/.710/.499, 460 tris; thigh mostly hidden inside the body line from the side, legs still read thin.
- r03 critique: az090 wire: the head is a cone from occiput to bill tip, no skull box, no stop between skull and bill.
  Diagnosis: only H1 (w .15) then H2 (top 1.215) - a linear taper. Fix (r04): split the skull into H1 (y -.68) + H1b (y -.78, full height) so the top drops ~.1 to the bill base H2: a stop.
  Result r04: IoU .684/.709/.497, 476 tris; a skull box and a stop now show in az045/hero.
- r04 critique: az000/az090: the thigh is hidden behind a belly that hangs to z .35; the ref shows a big drumstick thigh under a tucked belly.
  Diagnosis: Bm/B1 bottom B .17/.22; thigh rows w .085/.07. Fix (r05): tuck Bm/B1 (B .13/.19, centres +.01) and thigh rows w .095/.075, d .12/.09.
  (r05 first try: 4 self-intersections, thigh inner face into the tucked belly; thigh moved out to x .215, w .085 -> PASS)
  Result r05: IoU .686/.707/.507, 476 tris; thigh now shows below the belly from az000/az090.
- r05 critique: az000: the skull is a peaked tent (upper-side vertex at 0.6 of the height), the ref skull is a broad flat-topped box.
  Diagnosis: half_ring p1 height factor 0.6 on H0/H1/H1b/N2. Fix (r06): per-station factor HU = .75-.85 on the neck top and skull.
  Result r06: IoU .686/.711/.506, 476 tris; skull reads as a flat-topped box with a stop from az000/hero.
- r07: lock round, no geometry change (r06 reads as a biped wyvern from every view: two legs, wing-arms to the ground, long tail, raven skull + bill).
  Remaining for stage 2: brow over the eye, keel crease, thigh/hock planes; stage 3: membrane, hackles, horns, fin, talons.
- Lock (r07): 240 verts, 476 tris, edge sha256 9d3d301c14b57009. Min stage-1 blueprint IoU at lock: top .506 (side .686, front .711).
  Kit-use bug found after the lock: the finger's root side face was picked by stale BMesh normals (random per run); fixed with normal_update(), reproduces the lock hash.

## Stage 2
- r01: gates PASS except slivers 40 (7.6%). Moves: brow overhang, stop, hooked bill, keel, squarer rump, flat rib plane; loops at the neck (x2); eye inset.
  Critique: TECH QA: yellow needles along both wing-finger spars, the tail tip and the bill tip.
  Diagnosis: finger segments .47 m long on .04-.05 m faces, tip rings .005-.012 wide (< 6 deg angles).
  Fix (r02): scale finger rings 1.35/1.9/3.2, blunt tail and bill tips, two loops along the finger spar.
  (r02: bill-tip scale pivot off the seam broke the lock, fixed with a pivot on x=0; the hook moved 3 of 5 tip verts and folded the ring (4 hits), now the whole ring drops)
- r03: all stage-2 gates PASS, 572 tris, min IoU vs stage 1 .904. Slivers fixed by a shoulder-ring move and a tail-tip loop (needle finder behind RW_DEBUG).
  Stage-2 orbit round skipped for budget; the stage-4 final runs the orbit.

## Stage 3
- r01: pieces: membrane sail, 2 extra spars, thumb claw, 4 talons, horn, eye diamond, 7 hackles, 7 graded dorsal spines, 2-lobe tail fin; 7 colours.
  r01 result: 1218 tris, FAIL: hit 4 (membrane, spar3), float 2 (hind toe), z-fight 4 (toes), slivers 104 (8.5%: thin slab walls, long 4-sided spars).
- r02 fix: membrane rebuilt as a closed lens (shared rim, bulging centre: no thin side walls), spars rooted in the wrist with 3-sided 4-segment sections, toes spaced and the hind toe sunk into the foot.
  r02 result: 1214 tris, only slivers left 28 (2.3%): toes r .017 and spar2 needles.
- r03 fix: toe radii .021, spar radii +.004.
  r03 result: all stage-3 gates PASS, 1214 tris total, 7 colours. Reads as a raven-headed wyvern from hero/az090; plumage renders near-black under the key light, membrane reads mostly from hero/top.

## Stage 4
- r01: 17-bone rig from the build joints (roll auto), automatic weights, every piece bound with body= weights; idle 48f, move 32f, attack 40f.
  r01 result: all stage-4 gates PASS (hit 0, float 0, z-fight 0, slivers 10 = 0.8%, posed flips 0.08% tris / 0.10% area, drift 0, lock PASS, glbcheck OK). 1214 tris.
  Posed wires: the neck lunge (attack f20) and the idle head tilt bend without collapse; the walk is subtle; the plumage reads near-black.
