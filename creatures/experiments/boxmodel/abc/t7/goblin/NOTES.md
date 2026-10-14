# goblin (t7) - NOTES

No reference folder: stage 0 blueprint drawn by hand (blueprint.json).

## Stage 1
- r01: 676 tris, gates PASS, bp IoU side .84 / front .90 / top .78. Critique: the stance is upright - side view (az090) shows a straight spine and near-straight legs; a goblin must crouch and hunch. Diagnosis: torso ring centres (yc) all near 0, head rings on the neck line, knee only 0.10 ahead of the hip. Fix: crouch + hunch: R3-R6 lean forward (yc -0.02..-0.08, back hump db 0.15), head rings -0.05 y, knee to y -0.12, ankle back, arm and ear paths follow; pot belly df 0.20.
  Result r02: better - knees forward, head ahead of the chest; 676 tris. Side bp IoU fell to .73 (the drawing is upright; the model is the better design).
- r02 critique: front view (az000) - the torso is a tall straight-sided box: no pot belly, square shoulders; reads as a lanky child. Diagnosis: R1-R5 half-widths 0.155-0.175 nearly equal. Fix: pear torso - R2 belly a .195/df .22, R1 a .17, chest R4 a .14, shoulders R5 a .15, hump db .165.
  Result r03: better - pear torso, belly reads in az000/az045; 676 tris.
- r03 critique: front view (az000/az180) - legs are parallel vertical stilts, thin next to the belly; no crouch reads from the front. Diagnosis: leg path x constant 0.12-0.14, thigh a .05. Fix: bow the legs - knee out to x .165, shin .155, ankle .135; thigh a .058 / b .074, knee a .045.
  Result r04: better - bowed crouch reads from the front; 676 tris.
- r04 critique: side view (az090) - the back is a straight vertical line (butt behind the shoulders), the head stacks on top: no hunch. Diagnosis: R4/R5 back depth db .15/.165 < butt; neck R6 yc -.08. Fix: hump - R3-R5 db .15/.20/.20, R5 yc -.07, neck yc -.10, head rings HY -.07 (ears follow).
  Result r05: better - hump behind the shoulders, head hangs forward in az090; 676 tris.
- r05 critique: az000/hero - the hands are thin blades (x half .012-.016), no hand mass at the end of the long arms; the brief's clawed hands do not read. Diagnosis: palm/finger sections a .016/.012. Fix: chunky hands - palm a .026 b .046, fingers a .02 b .042 lower to z .155, thumb scale .7 pushed forward.
  Result r06: better - hands have a palm and thumb mass; 676 tris.
- r06 critique: az000 - the face is a ball with a nose; the jaw is narrower than the cheeks and its underside reads as a dark moustache band; no brow shelf. Diagnosis: R7 jaw front at y -.21 behind R8, R8 corners x .125, R11 brow flush with R10. Fix: jutting wide jaw (R7 front -.235, x .07/.125), wide grin ring R8 (x .075/.145, corners up), brow R11 pushed forward at P1 (-.255) and down at the outer corner; eye station R10 P2 recessed.
  Result r07: better - jutting jaw and grin wedge read in az000/hero, brow shelf over the eye station; 676 tris.
- r07 critique: az000 - the arms leave the chest horizontally, so each shoulder is a square epaulette box; a hunched goblin's shoulders slope. Diagnosis: first arm section at z .685 (level with the root face centre) and x .20. Fix: shoulder section down/in to (0.19, z .668), upper arm x .235.
  Result r08: better - sloped shoulders, no epaulette; 676 tris. Reads as a goblin from every view: big domed head, long horizontal pointed ears, hooked nose, hump, pot belly, bowed crouch, hands at the knees.
- r09: lock (no geometry change).

LOCKED stage 1 at r09: 676 tris, edge sha256 8e69ed5b2fc6c848. Min blueprint IoU 0.669 (top; the blueprint was drawn upright, the model hunched - the model is the better design).

## Stage 2
- r01 plan: joint loops (hip, knee x2, ankle, shoulder, elbow x2, neck), waist loop for the belt border, mouth loop pushed in for the grin line, eye socket inset under the brow.
  Result s2 r01: all gates PASS, min IoU vs s1 0.997, slivers 0.9%, 1136 tris. Grin line reads from the front; socket dents under the brow. Stage 2 done in one round.

## Stage 3
- r01 plan: paint 6 colours (skin, belly bordered by the waist loop and R4, cloth wrap below the waist loop, dark grin line); pieces - socket eyes with a pupil loop, 4 fangs, 12 claws (2 finger + 1 thumb per hand, 3 per foot), belt band projected onto the body + seam buckle, tattered front/back loincloth flaps under the belt.
- r01: FAIL 1 floating shell, 1540 tris. Critique: the back loincloth flap floats ~5 cm behind the rump (blue in az090/back34 TECH QA); the front flap is a 9 mm shard edge-on. Diagnosis: back flap top was placed from the body at z .47 (the rump), not inside the belt band at the waist, and hung vertical. Fix: both flaps start inside the belt band (belt outer - 12 mm) and sag outward over the rump (+55/+62 mm), thickness 13 mm.
- r02: the edit script failed (no code change); r02 re-ran r01 with the orbit - same float. Fix re-applied for r03.
- r03: float fixed; FAIL 1 hit on piece_belt, 1540 tris. Diagnosis: both loincloth flaps were one object, so the belt saw two separate contact patches (front and back) from it on one side = "passes through twice". Fix: each flap is its own object (loin_front, loin_back).
- r04: all stage-3 gates PASS; 1540 tris total (body 1136); 6 colours. Reads as a goblin in colour (green skin, pale belly, belt + buckle, tattered cloth, yellow eyes, fangs, claws). Weakness: eyes are small for the head.

## Stage 4
- r01 plan: 17-bone rig from J (hips-spine-chest-neck-head, ears, clavicle/upperarm/forearm/hand, thigh/shin/foot), roll auto, auto weights, every piece bound with body= weights; idle 48f, move 32f, attack 28f.
- r01: FAIL posed fold-overs 1.69% tris / 0.75% area (belt 12, loin_front 10, body 4); glbcheck OK; hit/float/zfight/drift 0. Diagnosis: heat weights gave the thigh bones the pelvis flanks up to z .52, the belt copies them, so its top follows the hips while its bottom follows the swinging thigh and the band folds; the front flap's lower verts copied inner-thigh weights. Fix: strip thigh weights from body verts above z .445 inside |x| < .19 (fallback hips), loincloth flaps bound rigidly to hips.
- r02: fold-overs 1.23% tris / 0.44% area (belt 15, body 4), drift 1 (loin_front). Diagnosis: the heatmap puts the belt folds on its flank beside the elbow - body= copies the nearest surface, which there is the arm, so the band follows the arm swing; the front flap brushes the inner thigh at rest (seated) and the thigh swings away from it. Fix: belt bound rigidly to hips (the waist skin is hips-only since r02); front flap narrower (x .056) and sagging 2-3 cm clear of the thighs.
- r03: fold-overs now 0.26% tris / 0.09% area (body only) PASS; loin_front hit 1 + drift 1. Diagnosis: the front flap's top row (z ZB+.012) sat inside the belly bulge (body y -.163 vs flap -.156), so it was seated in the belly skin and drifted; the r03 sag pushed its middle through the buckle shell (second contact). Fix: front flap top row at ZB-.005 where the body recedes (1.6 cm clear, inside the belt band), thickness 10 mm, sag -6/-20 mm (3 mm clear of the buckle).
- r04 (final, with orbit + glbcheck): ALL gates PASS - hit 0, float 0, z-fight 0, slivers 0.9%, fold-overs 0.26% tris / 0.09% area, drift 0, lock PASS, glbcheck OK (attack/idle/move). Posed renders: neck and knees bend without collapse; the attack swipe reads.

## Triangles per stage
s1 676 (locked, edge sha 8e69ed5b2fc6c848) | s2 1136 | s3/s4 total 1540 (body 1136 + pieces).
Rounds: s1 9 (8 + lock), s2 1, s3 4, s4 4.
