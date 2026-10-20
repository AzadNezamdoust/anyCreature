# griffin (r20)
Design: white eagle head with a hooked yellow beak and swept feather tufts on a tan lion body; raised brown wings with dark flight-feather tips, a thin lion tail with a dark tuft, yellow talon forefeet.
Identity cue in the base: beak + tufts (stage 1); wings are stage-3 pieces.
Base: copied from opus/wolf/wolf.py; PARAMS block (BEAK, HEAD_SCALE, EAR_TIP*, WING, TUFT ...).
- s1 r00 baseline wolf copy; r01 beak rings + thin tail: tufts too tall; r02 tufts lower/back; r03 stronger beak hook -> LOCK (728 tris).
- s2 r01 inherited wolf stage 2 (loops, eye socket): IoU min 0.971.
- s3 r01 palette/wing/tuft/collar: sliver 2.3% FAIL (wing edges); r02 WING_T 0.022->0.050: PASS, 1820 tris.
- s4 r01 drift+flip on wing; r02 rigid side binding: drift; r03 root on body weights: drift (anchors = first 12 verts = rows 0-1); r04 extra shoulder row so anchors ride the skin: PASS; r05 flap sign flipped (wings spread on attack), final + orbit: all gates PASS, glbcheck OK, 1844 tris.
Weakness: wing is one slab per side (no separate feathers); wolf-proportioned legs.
