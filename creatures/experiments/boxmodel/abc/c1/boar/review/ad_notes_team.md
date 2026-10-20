# boar (abc/c1): art-director notes, team round

Reviewer: Fable 5.1 (art director). Packet: review/1_beauty.jpg, 2_closeups.jpg, 3_tech.jpg, 4_posed.jpg, 5_reference.jpg, techqa.json. Reference: reference/sheet.png.

## Score: 6.5 / 10   Verdict: FIX

Reads as a boar in one glance from every view; the carved mass (withers hump, deep chest, tucked belly, round hams) is the best base of the batch and the tech sheet is clean (hit 0, float 0, drift 0, flips 0, 4 slivers). What holds it under 7 is the head furniture: the ears are antelope horns, the crest is a row of identical sawteeth, and the face has no eye at thumbnail size. None of this needs the base.

## Keep (must not regress)
- Stage-1 mass: hump-to-rump taper, deep chest, tucked belly, round hams (1_beauty az090, back34).
- Snout: flat pink-grey disc with two nostrils, thick cream tusks framing it from the lower jaw (1_beauty az000, 2_closeups head).
- Tech: 0 hit / float / drift / z-fight, 0 posed flips; mantle and hoof colour borders on logged loops (3_tech, 4_posed).

## Must-fix (ordered by visual damage)

### 1. Ears read as thin dark horns, not boar ears
- Stage: 3
- Where: 1_beauty az000 and az090; 2_closeups head wire. The ear plates are narrow isosceles spikes, nearly black, tilted up and back. The reference (5_reference front, side) has broad leaf ears, base about 45 % of the head's height at the eye, tilted ~30 deg forward and ~35 deg outward, body-brown outside with the dark colour only on the inner cup.
- Fix: rebuild `piece_ears` as a cupped leaf: base width ~0.11 m (about 25 % of body width 0.46), length ~0.14 m, 3-4 mm thick; pivot at the current seat on the skull top (x 0.092), lean forward 30 deg and outward 35 deg; outside brown #7d5843, inner cup dark #46322a; keep rigid to the head bone (stage 4 r05 fix). Sink the base 4 mm as before.
- Check: 1_beauty az000 next to 5_reference front: ear outline is a leaf as wide at the base as the eye-to-eye distance is at the eye; az090 shows the ear tip ahead of its base, not behind it. 3_tech: float 0.

### 2. Crest is a comb of identical, evenly spaced sawteeth
- Stage: 3
- Where: 1_beauty az090 and hero; 2_closeups crest. Seven near-identical triangles on a fixed pitch, with a visible gap between the ear and the first clump (the nape is bare); reference crest starts right behind the ears, is tallest at the withers, dense (clumps overlap), and tapers to nothing at mid-back.
- Fix: rebuild `piece_crest` with 8-9 clumps of varied width (±30 %) and height (tallest at the withers ~0.09 m, about 10 % of the shoulder height 0.9; nape clumps ~0.05 m; last two ~0.03 m), pitch varied so neighbours overlap at the base by ~1/3; start the strip 2 cm behind the ear seat; lean every clump back 15-20 deg; keep one connected strip (no floats).
- Check: 1_beauty az090 side-by-side with 5_reference side: no two adjacent clumps the same height, no bare nape; 3_tech float 0, hit 0.

### 3. The face has no eye or brow at thumbnail size
- Stage: 3 (lens and paint) with a small Stage 2 brow move
- Where: 1_beauty az000 and hero; 2_closeups head colour. The eye is a 2-3 px dot; the reference reads a dark almond eye under a dark brow with a dark cheek patch on each jowl (5_reference front).
- Fix: eye lens 1.8x its current size (~0.03 m long, 15 % of the head's height), tilted so the outer corner is 10 deg lower than the inner (the boar's mean look); paint a dark #46322a patch on the brow-to-cheek facets above and in front of the socket (the three facets bounded by the socket inset and the eye-cut loop) and the jowl facet beside the tusk root. Stage 2: push the brow rim vert a further 6 mm out so the lens sits in a shadow.
- Check: 1_beauty az000 at 25 % zoom: both eyes and the dark brow visible as the reference shows them; 2_closeups head colour.

### 4. Hind legs are straight columns, no hock
- Stage: 2
- Where: 1_beauty az090; 2_closeups hind limb. The hind leg drops vertically from the ham; the reference side view (5_reference) has the hock ~40 % up the leg set back ~5 % of body length, the cannon angled forward to the hoof.
- Fix: on the hind leg verts between z 0.12 and z 0.35, move the hock ring (z ~0.30) back 6 cm (~4 % of length 1.4) and the ring just below the ham (z ~0.42) back 3 cm, keep the hoof ring where it is (feet planted, hoof loop at z 0.045 untouched); `flatten` the front of the cannon so it is one plane. Also narrow the front legs 10 % in x below the elbow. Stay within IoU 0.9 (legs are < 8 % of the side silhouette).
- Check: 1_beauty az090 beside 5_reference side: a visible hock angle; 4_posed move frames: hooves do not slide; stage-2 IoU printout > 0.9 all views.

### 5. Mantle border is one straight diagonal; body brown too light and red
- Stage: 3 (repaint) using the existing stage-2 mantle loop; one extra partial loop at Stage 2 if the straight edge cannot be bent
- Where: 1_beauty hero and az090 vs 5_reference side. The mantle's lower edge runs as one straight line from the ear to the mid-back; the reference's edge dips down over the shoulder blade (to ~55 % of shoulder height) behind the foreleg and rises to the back behind it, then runs to the hip in a soft point.
- Fix: slide the mantle lower-edge loop so the shoulder segment drops ~10 cm (11 % of shoulder height) above the foreleg and comes back up behind it; repaint the facets inside it dark. Body brown toward the brief's #6f5040 (the current #7d5843 reads orange next to the reference); keep the mantle #46322a.
- Check: 5_reference side pair: the dark shape matches the reference's shoulder saddle; 3_tech slivers still ≤ 2 %.

No Stage-1 unlock needed. The base's silhouette matches the reference in every view (5_reference); the rear-view width is 6-8 % narrower in the hams than the sheet but is not worth a relock.

## Should-fix (short)
- Hooves: a cloven notch (a 4 mm inset on the front face of each hoof, Stage 2) so close-ups don't read as boots.
- Tail: the stub is short and dark; thin the tail base and lengthen the tuft 30 % (Stage 3), hang it, do not stick it out.
- Slivers: 4 yellow slivers on the neck-shoulder bisect (3_tech az090, az000 cheek); one vertex merge each.
- Snout disc: tilt the disc 10 deg more toward vertical so it faces the camera at az000 like the reference.
- Attack: f016 is a head turn; add 10 cm of head lift between f008 and f016 so the tusk toss reads in silhouette (Stage 4 keys).
