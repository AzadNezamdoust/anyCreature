# stag (abc/c1): art-director notes, team review

Reviewer: Fable 5.1 (art director). Packet: review/1_beauty.jpg, 2_closeups.jpg, 3_tech.jpg, 4_posed.jpg, 5_reference.jpg, techqa.json. Reference: reference/sheet.png.

**Score: 6.5 / 10.  Verdict: FIX.**

Reads as a stag at one glance from every view; the side (az090) against the reference side is close in body plan, proportion and colour regions. The tech sheet is clean (no hit, float, z-fight, flip or drift; slivers 0.9%; the 14-tri pink clip under the ears is invisible in every beauty and posed frame, so the heatmap and my eye agree). What holds it under 7 is the front view and the close-ups: cream paint climbing the forelegs, slit eyes, mane locks standing off as cards, and rake-like antlers.

## Keep (must not regress)

1. The carved body plan seen in az090 and back34: deep chest, high withers, rounded rump, upright maned neck, slim legs with a knee and a hock, small hooves. Silhouette IoU against stage 1 stays > 0.9.
2. Colour borders on edge-path cuts: rump patch, belly band, jaw cream, bib V, hoof line. No saw-tooth borders anywhere on the body.
3. Tech cleanliness and deformation: all gates PASS; the neck pitches down in the attack and graze frames without collapse (4_posed.jpg, attack_f016, idle_f024).

## Must-fix (ordered by visual damage)

### 1. Cream belly band paints the forelegs
- **Stage:** 3 (repaint; a stage-2 partial loop under the elbow if the paint rule needs an edge to stop on).
- **Where:** az000 and hero in 1_beauty.jpg; "front limb colour" in 2_closeups.jpg. The cream belly region runs up the inside and front of both forelegs to the elbow, as a cluster of cream triangles with a jagged border. From the front the stag looks like it wears pale knee socks on the wrong end of the leg. The reference front has brown forelegs and a single cream chest patch between them, below the mane.
- **Fix:** restrict the cream belly to faces below the elbow line (z of the elbow) AND inside the body's inner width (|x| < ~60% of chest half-width); forelegs body-brown from the shoulder to the knee. Add the reference's cream chest patch: a diamond between the forelegs below the mane's point, ~15% of body width wide, ~12% of body height tall.
- **Check:** 1_beauty.jpg az000: no cream on either foreleg; one cream patch on the chest. 2_closeups.jpg front limb colour: brown from the shoulder to the knee.

### 2. Eyes are slits
- **Stage:** 3 (eye lens piece).
- **Where:** "head colour" in 2_closeups.jpg, hero and az000 in 1_beauty.jpg. The eye is a 1-pixel black dash at thumbnail size; the reference eye is a round dark almond that carries the face.
- **Fix:** eye lens 2.0-2.5x larger (about 0.03 m across, ~20% of head length), almond-to-round, domed 3-4 mm proud of the socket, sitting in the socket inset so it does not float. Keep the socket inset.
- **Check:** 1_beauty.jpg az000 at thumbnail: two visible dark eyes. 2_closeups.jpg head colour: an almond eye the size of the nostril block. techqa float = 0.

### 3. Mane locks stand off as flat cards; the mane ends in a skirt
- **Stage:** 3 (mane pieces + mane paint border).
- **Where:** hero in 1_beauty.jpg: a rectangular dark plate at the base of the neck over the shoulder; az000: vertical dark bars either side of the neck like a vest; back34: a shard hanging under the throat. 3_tech.jpg hero shows the same plate edge-on. The mane's bottom edge is a horizontal line at the shoulder with jagged flaps below it, where the reference tapers the mane to a point on the chest.
- **Fix:** every lock lies on the skin with its root offset <= 8 mm and its outer face within ~15 mm of the body; cut the lock count to 3-4 per side; drop the shoulder plate. Reshape the painted mane's lower edge from a horizontal line into a V whose point sits ~55% of the way from the throat to the elbow (front plane), so the chest patch of item 1 sits under it.
- **Check:** 1_beauty.jpg hero: no plate at the shoulder; az000: the mane is a dark V with a jagged fringe, not a vest. 3_tech.jpg: no blue floating marks.

### 4. Antlers read as a rake: thin beams, long near-horizontal tines, dark stick base
- **Stage:** 3 (antler piece).
- **Where:** az000 and hero in 1_beauty.jpg; "antlers (largest piece)" in 2_closeups.jpg; 5_reference.jpg front pair. The model's tines point sideways and down like rake teeth, the spread in az000 is ~2.2x the head width (reference ~1.6x), and the lower half of each beam is painted dark brown, so the antlers read as sticks with spikes rather than one chunky crown.
- **Fix:** tine pitch raised ~25 deg toward vertical (tips up, brow tines still forward); tine length -20%; beam radius +25% at the base (keep the taper); crown tips kept. Spread in the front view no more than 1.6x head width. Dark burr only on the bottom 10% of the beam; the rest antler tan.
- **Check:** 1_beauty.jpg az000: tines point up-and-out, spread <= 1.6 head widths; hero: tan antlers with a small dark burr. techqa slivers <= 2%.

### 5. Ears stick out sideways like wings
- **Stage:** 3 (ear piece).
- **Where:** hero, back34 and az000 in 1_beauty.jpg: the ears are horizontal leaves pointing straight out from the skull; the reference ears angle up at ~45 deg and sit close to the antler base.
- **Fix:** rotate each ear up 30-35 deg about its root (tip higher than the root), yaw it 10 deg forward; length -15%. Root stays sunk in the skull.
- **Check:** 1_beauty.jpg az000: ear tips above the ear roots, inside the antler spread; techqa float = 0, pink clip not worse than 14 tris.

No Stage-1 unlock is needed: the base carries the body plan, and every item above is a piece or a paint rule.

## Should-fix (short)

- Lower legs: the near-black starts at the knee/hock and reads heavy (az090). Move the border down ~8-10% of leg height so the dark cannon is the lower 30% of the leg, and paint the cannon the mane colour with the hoof black (the reference uses two values there).
- Tail: lengthen ~20% and give it the reference's slight hang; back34 shows a short wedge stuck to the rump patch.
- Rump: the back34 view shows a flat vertical plane above the rump patch; a stage-2 vertex move rounding the croup (top-rear edge pulled 2-3% of body length forward) would help.
- Walk cycle (4_posed.jpg move_f007): the hind leg lifts higher than the fore leg; even them and give the head a small nod.
