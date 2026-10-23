# bear (t9 RECREATE, 2026-10-23) — NOTES

Rebuild from scratch of zoo/bear, program generated from the t9 fox program (same loft/grow/grow_ear code) with the
bear's own sections read off blueprint.json (copied with reference/ from zoo/bear, sheet refs/gpt/v3/bear/sheet_1.png,
height 1.2). Identity cue: shoulder hump, dish face + tan muzzle box, massive columnar legs, small round ears.
Sheet: hump 1.20 at y -0.2, back 1.06, belly 0.34, half-width 0.38 (front z 0.4-0.7), legs x 0.065-0.33.

## S1
- r1: 2,280 tris, IoU side/front/top 0.889/0.903/0.828 (reads as a bear). FAIL self-intersection 24 pairs at the
  hind window's inner edge (x 0.05-0.12, z 0.34). Diagnosis: leg sections' inner wall (x 0.04) inboard of the window
  rim (j12 x 0.076): the transition ring folds under the belly. Fix: leg centre 0.22/0.218, rx 0.14 at the root.
- r2 LOCK b150ef02: 2,280 tris, IoU 0.889/0.900/0.828, self-intersection 0.

## S2/S3 (inside the S4 rounds): eye socket inset (ray y -0.725 z 0.985), flat muzzle planes H4-H7, nose cap slant;
paint + smooth_borders (stairs 11 -> 6, 3-to-1 7 -> 0); lens eye 42 mm, 4 chunky pale claws per paw, nose knob,
stub tail knob.

## S4
- r1: kit gates PASS (glbcheck OK), junction probe PASS (ears, upperarms, thighs), clips PASS after --fix-clips;
  detail FAIL 5 groups < 6. Critique: az000/hero colour — the whole muzzle front is black and the lower half of the
  body dark (sheet: tan muzzle with a black nose tip, legs a shade darker). Fix: nose paint tip only, dark belly
  fh < -0.80; + brow mounds (6th detail group).
- r2: ALL gates PASS — kit (glbcheck OK, posed clip warn 1 tri), junction PASS (ears knife 0/strip 1.0 r; upperarm
  0/0.29 r; thigh 0/0.78 r), eyes 0.72/0.81/0.46 (41 mm = 0.078 head), membranes PASS, detail PASS 6 groups, clips
  PASS after --fix-clips, pack PASS (LOD IoU 0.997/0.989/0.973), ROM audit 3 fails; 3,036 tris.
- A/B vs zoo/bear (fresh Opus seat per order, sheet referee): AB -> zoo, BA -> zoo: zoo WINS both orders -> KEEP.
  Reasons: no shoulder hump (a capsule barrel), soft many-segment look, dark leg-top band reads as stuck-on legs.
- Fix round (backup before_fix1/): s4 r3 = stage-2 hump +5.5 cm over the fore window, saddle -3 cm behind; leg dark
  from the elbow/stifle loop (z 0.30) down.
- fix1 judge: vs r2 AB -> fix1, BA -> r2: flip = TIE -> r2 kept; vs zoo AB -> fix1, BA -> zoo: flip = TIE -> zoo.
  fix1 reverted (program + stage4 restored from before_fix1/; fix1 kept in var_fix1/). Seats: fix1 has the deeper
  hump, but its dark leg colour now stops in a hard "boot" band and leaves dark crescents on chest/rump.
- FINAL (r2): verdict KEEP zoo/bear. --review, --compare, junction re-probe PASS on the restored r2 GLB.
  Note: at 08:22 the r2 --review/--compare chain overlapped the fix1 build (two Blender processes for ~5 min);
  review/compare were re-run on the restored r2 GLB at 08:30.
  Residuals (owner packet): no strong hump / soft many-segment barrel vs the zoo's crisp planes; leg-top colour band;
  boxy rear and a weak tail nub; ears small.
