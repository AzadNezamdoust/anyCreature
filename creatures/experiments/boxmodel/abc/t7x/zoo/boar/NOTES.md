# boar (t7 hand box model) — NOTES

Technique of the base wolf: one spine loft of 6-vertex half rings (tail tip -> snout disc), legs extruded as 2-face regions from the lower flank, ears as 1-face extrusions. Blueprint traced from reference/sheet.png with kit/refs.py (height 0.95 m, length 1.50 m).

## Stage 1
- r1: first fit. Gates PASS, 628 tris, IoU side/front/top 0.874/0.877/0.845. Critique: az000/front overlay — barrel narrower than the ref's. Diagnosis: body W 0.20-0.24, profile widest high. Fix: W up to 0.25, lower-flank vertex (0.98, -0.45).
- r2: better, front IoU 0.893. Critique: hero — ears are thin spikes. Diagnosis: ear mid section barely clears its base face. Fix: EAR mid (0.155, -0.35, 0.89) rx/ry 0.05.
- r3: better, ears read as upright triangles (IoU 0.875/0.883/0.846). Critique: az090 — legs are stilts. Fix: chunkier leg sections.
- r4: FAIL, 4 self-intersecting pairs at the hind-leg root front. Diagnosis: stifle ring ry 0.13 reaches ahead of its base span. Fix: stifle (0.13, 0.46, 0.24) ry 0.11.
- r5: PASS, IoU 0.882/0.888/0.846. r6 LOCK: 316 verts, 628 tris, edge sha256 916c85a8a92c0984.

## Stage 2
- r1: elbow, stifle and neck rings, eye socket inset, brow/jowl moves, flat snout planes. FAIL: slivers 24 (3.4%), on the thin tail and the leg-root walls (glb probe).
- r2: Fix: tail rings 1.5x wider; lower-flank vertex of each leg-root ring out 2.5 cm (shoulder/ham bulge seen in the ref top view). PASS, 712 tris, slivers 1.1%, min IoU vs s1 0.971.

## Stage 3
- r1: 8 colours along existing loops (grey-brown flank, dark crest/back/ears/tail tuft, pale jowl and snout, light-brown legs/belly, black hooves, pink disc), small dark lens eyes with pupil, ivory tusks, 6 crest clumps per side, jowl tuft, two toes per hoof. PASS, 1,256 tris. Critique: crest reads as tall spikes. Fix (r2): lower, laid-back bristles. PASS.

## Stage 4
- r1: 16-bone rig + .R mirrors, idle/move (trot)/attack (head-down charge, tusk toss). All gates PASS; clip warning only (0.28% of surface). Critique: EEVEE/colour reads near black vs the ref's warm mid brown. Fix (r2): palette one step lighter. All gates PASS (slivers 1.0%, fold-overs 0, drift 0, lock OK, glbcheck OK).

18-view orbit: every view reads, no collapse. Fusion (rest pose): tail to hind legs 17 cm, fore L/R 10 cm, hind L/R 11 cm — nothing fused.
Weaknesses: tusks small; the mean of the ref's staggered leg pairs; tail tuft is a widened blade, not a separate tuft.

## Fix pass 1 (review_fable + review_opus)
Fix list (shape first): legs thin/long; crest = floating blade cards; tusks thin (read as whiskers), cheek plates flare; orbit sheet grey.
- Base change, stage 1 re-locked (old lock kept in before/): trunk drops 3 cm, leg section heights x0.9 (leg length -10 %), leg section radii x1.2 (+20 %). r7 FAIL: 4 self-intersecting pairs at the fore-leg root (elbow ring ry 0.12 past its span). r8: elbow/stifle root rings keep their depth, rx still +20 %. PASS, 628 tris, edge sha256 eac57c982a22284d. Blueprint IoU 0.849/0.873/0.846 (side lower: shorter legs, as asked).
- Stage 2: the cheek push-out dropped (cheek flare).
- Stage 3: crest = one continuous saw-tooth strip on the midline, 6 laid-back teeth, base sunk 2 cm into the spine, welded at x = 0 by the mirror. Tusks = triangular prisms rooted low in the jaw, ~2x thicker, curving out then up. Pale jowl tuft removed (read as a face plate); cheek stays cream paint.
- s4 r3 FAIL: total tris 1124 < 1200 (fewer pieces). r4: crest teeth get 4 stations each (valley, front slope, tip, back shoulder). All gates PASS, 1,268 tris; lock assert PASS; glbcheck OK.
- orbit18_sheet now from checks.py (EEVEE colour, all 18 views). Separation PASS: tail-hind 17 cm, fore L/R 7 cm, hind L/R 8 cm.
Not fixed: tail tuft still a widened blade; snout reads long vs the ref at az0.

## Fix pass 2 (review2_fable + review2_opus, concept sheet as referee)
Fix list (shape first): tusks barely visible; head small, hips narrow; legs thin; snout long and pale. Skipped: Opus "raise the mane 1.5x" (sheet shows a smooth dark ridge, no spikes); Fable "drop the pink disc" (sheet has a pink snout disc; kept).
- Base change, stage 1 re-locked (old lock in before2/): N0/H0/H1 W x1.15; R0/R1 W 0.14/0.22 -> 0.17/0.24; snout H3/H4 3-4 cm back (~15 % shorter); upper legs rx x1.25, forearm/gaskin ry x1.15. r10 LOCK PASS, 628 tris, edge sha256 ae72fd85ee504c6c. Blueprint IoU 0.850/0.843/0.824.
- Stage 3: tusks ~2x long, curling up past the snout top, root one ring back; snout painted body grey-brown (cream only on cheek/jowl), pink disc kept.
- s4 r5: all gates PASS, lock assert PASS, glbcheck OK, slivers 2.0 %. Separation PASS: tail-hind 17 cm, fore L/R 5.4 cm, hind L/R 8.6 cm. checks.py now also writes side_by_side.jpg (sheet views | model).
Not fixed: tail tuft still a widened blade; crest teeth kept (sheet ridge is smooth).

## Poly pass 3 (owner: denser main mesh, ~2x tris, same t7 technique)
Before renders and the pass-2 script/lock kept in before3/.
- Base change, stage 1 re-locked: half rings 6 -> 12 vertices (superellipse profiles per region: barrel, skull, muzzle, tail); spine loft 18 -> 27 stations, refitted to the traced sheet (tops/bellies off the side outline; widths off the plan view: shoulder bulge W 0.272, waist 0.21-0.22, ham 0.255, rump rounded off 0.19/0.13). Legs: 2x2-face roots -> octagon legs, 8 stations each (new upper arm/ham, lower forearm/gaskin taper, coronet).
- s1 r11 FAIL: 18 self-intersecting pairs, upper-leg ring under the belly. r12: upper ring narrower and outward. r13: rump/waist/shoulder widths from the plan view. r14 LOCK PASS: 866 verts, 1,728 tris, edge sha256 451cdc593937ee6f. Blueprint IoU 0.850/0.843/0.859 (was 0.850/0.843/0.824).
- Stage 2: elbow, stifle, neck rings and eye socket re-targeted to the new rings; snout planes on 4 stations; shoulder/ham bulge on the window flank verts. s4 r6 FAIL: slivers 3.8 % (12-vertex tail rings over long spans). r7: one ring in the tuft and stalk spans, tuft 1.3x wider. All gates PASS, slivers 1.6 %, lock assert PASS, glbcheck OK; clip warning only.
- Tris 1,280 -> 2,508: body 712 -> 1,940, details unchanged (568); the whole increase is in the body loft. Separation PASS: tail-hind 15.7 cm, fore L/R 4.4 cm, hind L/R 8.6 cm.

## Poly MIX pass (review_poly2x: MIX, restore torso/back loft, keep head and eye)
2x-pass script, lock, hero and sheets kept in pass3/.
- Base change, stage 1 re-locked: torso stations R0-C1 back to the pass-2 values (W1/M1 dropped; Rb/Cb = straight midpoints for the 3-ring leg windows). BODY = pass-2 6-vertex barrel resampled to 12 on straight segments, none on the back plane, so the dorsal ridge and flat flank planes return. Head, eye, muzzle, tail and legs unchanged from the 2x pass.
- s1 r15 lock FAIL (expected), r16 LOCK PASS: 822 verts, 1,640 tris, edge sha256 55b7502f1413b847; IoU 0.850/0.843/0.859.
- s4 r8: all gates PASS, lock assert PASS, slivers 1.7 %; clip warning only. Total 2,420 tris (was 2,508). Separation PASS: tail-hind 15.7 cm, fore L/R 4.4 cm, hind L/R 8.6 cm.
- before_after4.jpg: before3 | 2x pass | now.

## Fix pass 5 (owner: "boar eyes still bad"; eyes and socket only)
Before renders in before5/.
Diagnosis: (1) after the 12-vertex head pass the socket was a 0.3 inset pushed 1.2 cm in and squashed: a narrow dark slot; (2) the lens (1.4 cm) sat on a point nearest the old pass-2 eye centre, at the slot's rear corner, half buried; (3) dark-brown iris on a dark grey-brown face, no contrast; (4) socket floor painted cream with the cheek, so it read as a pale liner; (5) the lens faced the body normal under the brow, lost in the hero/front views.
Fixes: stage 2 socket = 0.12 inset, 4 mm deep, no squash (same logged op, base lock untouched); stage 3 lens 1.7 cm, centred on the socket floor, facing the eye face normal turned a little to the front, apex proud of the skin; amber iris #a8702e with a black pupil fan; socket painted plain fur. Rest of the boar unchanged.
s4 r13: all gates PASS, lock assert PASS, slivers 1.7 %, clip warning only; 2,420 tris. Separation PASS (tail-hind 15.7 cm, fore L/R 4.4 cm, hind L/R 8.6 cm). before_after5.jpg: hero and head close-up, before5 | after.
Not fixed: in the az0 view the eye is still small, near the head edge above the tusk tips.

## Fix pass 6 (owner crops: leg-join speck, dark crease, ear join)
Before renders in before6/. Crops located on the hero view (1: near fore-leg root; 2: flank over the near hind-leg root; 3: far ear root). Probe: body closed (0 open edges, no duplicate shells); the faults are knife folds (adjacent faces at normal dot -0.86 to -0.97).
- Cause (1, 2): the first ring of each leg overhung its 2x2 root window: 4 cm past the window front/back, the inner side 8 cm in under the belly, the outer side 3 cm inside the flank. The rear/front and inner root walls folded back up against the belly (the white glint and pinhole at 1), and the flank overhung the leg as a dark ledge (2).
- Cause (3): the ear's root ring overhung its 1-face root 3.5 cm behind and 2 cm inward, so its rear and inner walls folded down onto the skull.
- Fix (stage 2 vertex moves, base lock untouched): leg root rings re-placed inside the window footprint (fore ry 0.085, hind 0.076), outer side 1.5 cm out flush with the flank, inner side lower; window inner edge (j9 of its three rings) 2 cm in and 2.5 cm down so the inner wall drops steeply. Ear root ring centred on its face (rx 0.037, ry 0.033, 3 cm lower). Worst fold: legs -0.97 -> -0.49, ear rear -0.97 -> -0.53, ear inner -0.89 -> -0.76.
- s4 r14 FAIL slivers 49 (2.0 %): fore rear root vertex coplanar with C0 j8-j9. r16: fore mid pair 1.5 cm out. r17-r19: outer flush, window edge down. r19: all gates PASS, lock assert PASS, slivers 1.9 %, clip warning only; 2,420 tris. Separation PASS (tail-hind 15.7 cm, fore L/R 4.4 cm, hind L/R 8.6 cm). crop_fix.jpg: owner crop | before | after.
Not fixed: a small sightline gap between the hind legs now shows under the belly in crop 2's view; the ear reads slightly slimmer.

## Fix pass 9 (owner: keep the 2x density, fix its faults inside it)
Before renders, script and lock in before9/. Starts from the 2x pass (pass3/), keeping fix passes 5 (eye) and 6 (leg/ear root junctions).
- Base change, stage 1 re-locked: torso back to the 2x stations (W1/M1 return, 12 torso rings). BODY = a hand-placed 12-vertex barrel instead of the round superellipse: one flat back plane (mane plane) to a hard dorsal ridge, a shoulder bevel, a near-flat flank plane, the leg-root bevel, a flat belly. Torso widths smoothed into one monotone run per mass (rump 0.14 -> ham 0.252, waist plateau 0.234-0.238, shoulder 0.262); tops and bellies re-read as one monotone-cubic curve through the side-outline anchors (the old tops stepped 2 / 4 / 2 cm ring to ring: the rib bands).
- s1 r17 lock FAIL (expected), r18/r19 LOCK PASS: 866 verts, 1,728 tris, edge sha256 52d9e4771e22dfa8; IoU 0.853/0.854/0.839.
- s4 r20, r21: all gates PASS, slivers 1.9 %, clip warning only; glbcheck OK. Total 2,508 tris (was 2,420). Separation PASS (tail-hind 15.7 cm, fore L/R 4.4 cm, hind L/R 8.6 cm). Eye unchanged (fix-pass-5 lens). Leg/ear roots: fix-pass-6 moves kept; no holes or specks in the hero.
- fix9.jpg: hero before9 | after, torso and eye close-ups.
Not fixed: faint shade steps remain on the mid flank next to the stage-2 shoulder/ham bulge.

## Weakfix 2026-10-23 (night, backup before_weakfix/)
- s4 r22. Critique: rear view — the hind legs stand 3-8 cm apart all the way down: a narrow slit under the tail (sheet: the hams meet, the lower legs part with clear space). Fix (stage 2 vertex moves, lock kept): hind-leg vertices below the stifle ring move out 2.4 cm (ramped from the stifle to full at the gaskin), the hind toes and the hock/hpaw/htoe joints with them.
- Result: kit gates PASS (clip warn 3 tris), detail PASS, clips PASS after --fix-clips; junction: thighs PASS (knife 0, strip 0.51 r); FAIL ears (knife 3.05 r), upperarm strip 1.04 r, tail0 strip 1.85 r (untouched geometry). A/B (2 fresh Opus seats): variant wins both orders: ADOPT. Both judges: tiny pale specks beside the tail base in the rear view, in both builds (pre-existing).
