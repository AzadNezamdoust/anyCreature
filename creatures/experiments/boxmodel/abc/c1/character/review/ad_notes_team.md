# character (abc/c1): art director notes, team round

**Score: 6/10. Verdict: FIX.**

Reads as the brief's toon figure at a glance: the big faceted sphere head on a thin neck, the slim straight torso,
long thin limbs, and the proportions sit close to the reference in `5_reference.jpg` (side and front). The tech
sheet is clean (hit/float/z-fight 0, 3 tiny flips under the limit, no drift). What stops it being shippable is at
the extremities and on the face: the hands are paddles with a hook, the eye pieces are goggles glued onto the
sphere, and the nose is missing in every view except a dot in the side view.

## Keep (must not regress)

- Head/body proportion and the neck: head ~1/4 of the height, thin round neck, matches `5_reference.jpg` side and front.
- Clean posed deformation: knees and elbows bend on the stage-2 loops in `4_posed.jpg` (move_f017, attack_f013), no collapse at hips or shoulders.
- The flat 4-colour palette and the eye/brow/mouth placement from the front (`1_beauty.jpg` az000): expression reads at thumbnail size.

## Must-fix (ordered by visual damage)

### 1. Hands: a flat paddle with a hook, not a mitten with a thumb. STAGE-1 UNLOCK
- Stage: 1 (hand-built mitten rings, r03/r04). Stages 2-4 cannot add a knuckle row or a thumb with volume; vertex moves on the present 6-gon ring stack only make a fatter paddle.
- What I see: `1_beauty.jpg` az000: both hands are thin slabs the width of the wrist, ending in a notch; the "thumb" is a small hook pointing back toward the body. `2_closeups.jpg` front limb: the hand is a bent flipper with a bite out of it. `1_beauty.jpg` hero: the hanging hand is a kinked flap. The reference has a mitten that is clearly wider than the wrist, with a knuckle row, finger blocks curling down, and a thumb standing off the palm (`5_reference.jpg` reference front and top).
- Fix: rebuild the mitten: palm width ~1.6x the wrist (about 0.07 m, ~4.5% of height), hand length ~0.10 m from the wrist to the fingertips (~6% of height), palm thickness ~0.025 m; a knuckle ring at ~45% of the hand length, the finger block beyond it curling down ~30 deg; the thumb a two-segment block from the palm's front-inner edge, ~55% of the hand length, pointing forward (-Y) and slightly out, not back toward the body. Keep the fingers as one mitten block (the brief allows it), but the knuckle ring must be there so the curl has a hinge. Relock stage 1, rerun 2-4; stage-2 IoU will not move (hands are <1% of the silhouette).
- Check: `1_beauty.jpg` az000 (hand wider than the wrist, thumb visible as a separate lump on the forward edge) and `2_closeups.jpg` front limb (knuckle row and curl visible in the wire); `4_posed.jpg` attack_f007 (the fist reads as a hand, not a blob).

### 2. Eye pieces: goggles stuck on the sphere; the black outline shows from behind
- Stage: 3.
- What I see: `1_beauty.jpg` az090: the eye stands off the head as a thick black ring with a white disc, about half an eye-diameter proud of the skull; `1_beauty.jpg` back34: a black crescent of the outline torus pokes out past the head silhouette; `3_tech.jpg` hero: same ring. The reference side view has the eye dome barely proud, with a thin outline, and nothing visible from the rear.
- Fix: sink the sclera dome and the outline ring into the head by ~35% of the eye radius (the sclera's back ring was raised in s3 r04 to clear the pupil; move the whole eye stack in instead, and keep the pupil's back cap inside the sclera by shortening it, not by lifting the sclera); outline torus minor radius down ~40%, so the ring reads as a line (brief: "a thin black outline"), and tilt the ring to the sphere's local normal at the eye centre so it does not lift at the outer edge. Pupils: ok.
- Check: `1_beauty.jpg` az090 (eye proud by < 1/5 of its diameter, outline a thin line) and back34 (no black crescent outside the head outline); `3_tech.jpg` hit stays 0.

### 3. Nose: missing
- Stage: 3.
- What I see: `1_beauty.jpg` hero and az000: no nose at all; az090: a 2-3 mm spike at the lower edge of the eye. `5_reference.jpg` reference side and top: a clear pointed cone, ~0.35 of the head radius long, between and below the eyes, and visible as a point in the top view.
- Fix: scale the nose cone 2.5x: length ~0.06 m (0.3 of the head radius 0.198) forward (-Y), base diameter ~0.035 m; seat it on the sphere at the midline, ~0.3 head-radius below the eye centres, with the base pushed 5 mm into the skin so it grows out of the head.
- Check: `1_beauty.jpg` hero (nose visible as a point between the eyes), az090 (cone protrudes clearly), `5_reference.jpg` model top (a point at the front of the head like the reference top).

### 4. Shoulder wedge and sternum crease
- Stage: 2.
- What I see: `1_beauty.jpg` hero and az000: the arm root is a sharp inverted triangle at the armpit with a hard ridge running from the shoulder point down the chest, and a vertical crease down the sternum; `2_closeups.jpg` front limb colour: the deltoid is a flat-faced wedge, lit as two planes meeting at a knife edge. The reference shoulder is a rounded cap flowing into the arm (`5_reference.jpg` reference front).
- Fix: at the shoulder, move the deltoid ring vertices out ~8 mm (about 5% of the shoulder width) and down 5 mm so the cap is convex; slide the crease edge off the sternum line and `flatten` the chest front plane across the two facets that meet at the ridge; soften the armpit by pulling the inner armpit vertex 6 mm up into the torso. IoU stays well above 0.9.
- Check: `1_beauty.jpg` hero (no knife-edge ridge from the shoulder down the chest, deltoid reads as a rounded cap) and `2_closeups.jpg` front limb colour.

### 5. Idle arm: double kink at elbow and wrist
- Stage: 4.
- What I see: `1_beauty.jpg` hero (idle frame 1): the hanging near arm bends sharply forward at the elbow and then the hand flips back at the wrist, so the arm reads as a hook; the far arm is straight. The reference has no idle pose, but a game idle wants a relaxed slight elbow bend and the hand following the forearm.
- Fix: in the idle clip keys, reduce the elbow flex from the present ~35 deg to ~12 deg on both arms, wrist flex to 0 (hand in line with the forearm, palm toward the thigh); keep the breathing and the blink.
- Check: `1_beauty.jpg` hero and az090 (hands hang by the thighs, one gentle bend per arm, both arms matching); `4_posed.jpg` idle_f012/idle_f024 the same.

## Should-fix (short)

- Toes (stage 3): the four blocks are tiny stubs crammed at the inner side of the foot (`2_closeups.jpg` toes); make them ~1.8x longer and spread them across the full foot width, big toe largest.
- Feet (stage 2): in `1_beauty.jpg` az000 the feet splay ~25 deg outward and look like flippers; rotate the foot vertices toward -Y by ~15 deg per foot and narrow the toe end 10%. Reference feet point almost forward.
- Brows (stage 3): in the hero view the near brow slopes down toward the nose and reads angry; the reference brow is a gentle arch. Flatten the inner end ~3 mm.
- Elbow crease (stage 2): `2_closeups.jpg` front limb wire shows the elbow loop as the only straight line in a sea of random carve triangles; a second loop 20 mm on each side would make the bend cleaner in `4_posed.jpg` attack_f007.
- Tech: the 3 flips (0.14%) at the upper arm and thigh in `3_tech.jpg` are under the limit; leave them unless weights are touched for item 5.
