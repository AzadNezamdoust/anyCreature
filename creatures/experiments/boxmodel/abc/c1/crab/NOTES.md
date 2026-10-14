# crab, setting c1 (carve + detail)

Reference 2x2 sheet copied from abc/k3/crab with blueprint.json (unchanged). Pattern: wolf (mask edits) + k3 crab (limbs, rig).

## Stage 1
- r01: carve_base defaults. Critique: the eight splayed legs carve into tall walls (az090, az000) and 2 self-intersections; a visual hull of radial legs is ambiguous in every view. Fix: hand edit of the carve input (masks.py): every view's mask clipped to KEEP polygons (side: carapace+belly, claw; front: |x| <= 0.47; top: carapace ellipse, claw without legs or eye ball); target 500-800.
- r02: PASS, 644 tris; carapace + two claws with a finger gap (top, az090). Critique: legs gone (expected); the underbody is a box out to the rim (front-view claws cover it). Fix: (1 change, the planned leg build) walking legs extruded by hand: 4 per side from two joined carve triangles on the underbody, paths read off top.png/side.png (hip, knee a/b, second bend, dark-tip ring, tip); underbody squeezed below the rim to the front view's belly bowl.
- r03: FAIL self-intersection 4, 980 tris. Critique: legs are flat blades (az090, hero): k3's limb rescales the root quad's own projection, and a diagonal quad collapses. Fix: each ring placed on a designed w x h box by angle order.
- r04: PASS, 980 tris, IoU .561/.681/.757 (the blueprint traces legs at other places than the plan read). Critique: legs read boxy but thin next to the reference's chunky legs (hero). Fix: leg sections +15%.
- r05: FAIL self-intersection 4 (debug: the hind leg's knee fold, femur vs tibia at 95 deg). r06 Fix: hind knee b further out (0.278, 0.405), second bend lower/out. r06: PASS, 980 tris. Critique: carapace is a flat slab with a vertical front wall (az000, az090); reference is a low dome over an overhanging rim. Fix: clamp carapace verts under a dome z = 0.385 - 0.08 r^2.
- r07: PASS, 980 tris, IoU unchanged: the hull top already sits under that dome except the front edge. Critique (az000): under the rim the front is a vertical grooved wall down to the belly; reference has the toothed rim lip over a face set back. Fix: verts between the claw arms below the rim pulled back to a receding front (y -0.26 under the lip to -0.16 at the belly).
- r08: FAIL self-intersection 188: the recess pulled the claws' inner palm faces (x 0.15-0.22) through the body. r09: restricted to x < 0.14: still 12 hits (the hull fuses body and claw there). Reverted: the front wall stays, stage 3 paints it cream under rim teeth. r10 Fix: stronger dome (rim 0.28: z = 0.385 - 0.105 r^2) so the carapace reads as a shield, not a slab.
- r10: dome moved 0 verts: debug showed the carapace peak at 0.323, not 0.385. Diagnosis: carve_base puts its lowest point on z = 0, and the clipped hull has no feet (its lowest point is the claw at 0.055): the whole base sat 5.5 cm low. Fix: lift the carve by the clipped side mask's lowest z (0.055). Result: IoU .796/.801/.770 (from .56/.69/.77), dome now trims 13 verts; FAIL 46 hits: the leg roots now fell on faces under the lifted belly.
- r11: Fix (one cause, two code lines): root faces only from the carve's own faces, picked facing the leg's reach (n.r > 0.55), hips moved out to z 0.175, and each ring keeps the face's cyclic order (an edge-on root quad had mapped to a bow-tie: duplicate-centre hits). Result: PASS, 980 tris, IoU .796/.801/.778. Reads as a crab in az090/hero/top: domed disc, two chunky claws with a finger gap held in front, eight two-bend legs. Remaining (stage 2): front wall under the rim, no rim crease, eye sockets, palm planes. Lock (r12).

## Stage 1 lock
- r12: LOCKED, 980 tris, edge sha256 f850c2e710b24a0b, IoU .796/.801/.778; orbit holds (advise: no head chain, a crab has none). Rounds: 12 (no re-lock).

## Stage 2
- r01: colour borders as planar loops (bisect logged as 'loop'): belly (z = rim 0.235), rim band (z 0.272, dark red), claw finger tips (y -0.53); eye-socket inset on the front rim; seam crown +1 cm. FAIL 4 hits (inset on a sliver triangle at the rim) and slivers 3.4%.
- r02: verts within 12 mm snap onto each cut plane first. Still FAIL: debug shows 13 of the half's slivers are in the LOCKED base (knee a->b segments fold into needles; 4 on the carved shell), the inset adds the hits.
- r03: Fix: knee-b rings slide 2 cm toward the second bend (vertex moves), inset dropped (stalks root on the rim as pieces). PASS, 1156 tris, min IoU .985, slivers 8 per half.
- r04 Critique: az000 front wall under the rim is a fan of needle facets (stripes). Fix: flatten the wall verts into one plane.
- r04 result: FAIL 8 hits: the wall's fan overlaps itself once flat (the triangles are not a disc in the plane). Reverted; the wall is painted cream under the rim teeth in stage 3. Stage 2 final = r03 geometry (1156 tris).

## Stage 3
- r01: palette from colour_from_sheet's clusters per brief role (bear's rule): shell #de593d (sheet), ridge/belly/tip/eye/barnacle brief; paint on the stage-2 loops. Pieces: eye stalks (6-sided) + 10-sided ball eyes rooted on the front rim, rim teeth, 5 cratered barnacles on the rear slope. PASS, 1632 tris, 6 colours. Critique (hero/az090 colour): walking legs have no dark tips (rule tested max z <= 0.07 but the tip ring is tilted, z 0.055-0.085) and the claw's dark zone covers the inner palm (az000 black blocks: centre test, plane at -0.53). Fix: leg tip = faces touching the tip vertex; finger tip = faces wholly past the claw-tip loop, the loop moved to y -0.555 (stage-2 cut, last ~third of the fingers).
- r02: PASS, 1584 tris. Leg tips and finger tips now dark (hero). Critique (hero, az000): only 2 rim teeth per side, invisible: the inward rays from r 0.45 hit the claw arm or the set-back front wall. Fix: each tooth sits on the outermost rim-band vertex within +-7 deg of its direction.
- r03: PASS, 1620 tris, 6 colours; 5 teeth per side (69/93 deg have no rim vertex inside r 0.37). Top view reads as a toothed front rim. Stage 3 closed (eyes, teeth, barnacles; leg/finger tips dark).

## Stage 4
- r01: k3's rig and clips (body; 4 legs x coxa/femur/tibia/tarsus on the LEGS paths; claw arm/wrist/palm/pollex/dactyl read off the carved claw; k3 rolls so +Z swings every tip down), every piece bound with the body's weights. Swing trimmed vs k3 (dactyl -20/-22, coxa lift -12, claw arm -14). Result: all gates PASS, glbcheck OK; clip warn 2 tris (0.05% of area); posed frames: claws rise/open and snap, legs alternate, no collapse at leg roots.
- r02: final with orbit, then --review and --compare.
- r02 result: all gates PASS; glbcheck OK (attack/idle/move); slivers 20 (1.2%); hit/float/z-fight/flip/drift 0; clip warn 2 tris (rim teeth, 0.05% of area); orbit holds. --review and --compare done.

## Totals
- triangles: stage 1 980 (lock f850c2e710b24a0b), stage 2 1156, stage 3/4 1620; 6 colours.
- rounds: s1 12 (no re-lock), s2 4, s3 3, s4 2.
- vs abc/k3/crab (1_beauty): domed carapace with a dark rim band over an overhanging cream belly bowl; claws are big rounded carved palms with a real finger gap and dark tips (k3: box palm); proportions follow the sheet (IoU .80/.80/.78 vs k3 .66/.69/.62). Weaker: az000 front under the rim is a flat cream wall with needle facets; barnacles and rim teeth small; legs are plain 4-sided boxes with a soft second bend; the claws' dark zone shows as blocks on the inner palm from the front.
- restored to the solo carve + detail version (orchestrator, 2026-10-05): both blind reviewers preferred it over the team pass. The team version is commit 923ec33.
