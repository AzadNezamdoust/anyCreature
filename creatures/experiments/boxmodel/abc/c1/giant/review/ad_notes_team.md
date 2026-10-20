# giant (abc/c1): art-director notes, team round

Reviewer: Fable 5.1 (art director). Packet: review/1_beauty.jpg, 2_closeups.jpg, 3_tech.jpg, 4_posed.jpg,
5_reference.jpg, techqa.json (all gates PASS, 2730 tris, 8 colours).

## Score: 6.5 / 10. Verdict: FIX.

It reads as a mountain troll in one glance from every view: the hump-to-small-head silhouette (az090 vs
reference side) is the best match in the batch, the arm gap is clean, the face carries brow / sunken amber
eyes / tusks at thumbnail size. What keeps it off 7+ is all in the dressing and the mid-body: the belt is a
hoop floating in front of the belly, the moss is one dull olive cap with pebbles on it instead of clumps and
rocks, the loincloth is paper-thin, the belly is flat, the toes are nubs. None of it needs the base.

## Keep (must not regress)

- Hump / shoulder mass and the sunken head under it (1_beauty az090, back34; 5_reference side pair).
- The arm gap and the arms hanging forward of the flank (az000, back34).
- Face: angry V brow, deep sockets with amber eyes, tusks from the underbite, nose bulb (az000, head crop).
- All tech gates at PASS: hit 0, float 0, z-fight 0, slivers 14 (1.2%), flips 6 / 0.36% area, drift 0.

## Must-fix (ordered by visual damage)

### 1. Belt is a thin hoop standing off the belly
- Where: 1_beauty hero and az000, waist. A 3-10 cm gap shows between the band and the hide across the whole
  front; the band is as thin as a wire and the stone toggles are invisible. The reference belt is a wide
  leather band that hugs the hips, dips at the front, with a visible knot/toggle under the navel.
- Stage: 3.
- Fix: rebuild the belt as a band 0.22-0.28 m tall (6% of height) and 0.06-0.08 m thick, sampled against
  the stage-2 body so it sits 1-2 cm proud of the surface (not 3-10), with the front edge dipping ~0.1 m
  below the back edge. One toggle piece 0.15 m wide front-centre under the belly, proud of the band. Keep the
  hips-bone binding for the toggles so drift stays 0.
- Check: 1_beauty hero and az000: no light gap under the band; az090: the band reads as a strap on the hip,
  not a ring. techqa hit = 0, float = 0.

### 2. Moss is one flat olive cap; rocks are pebbles
- Where: 1_beauty back34 and az090, 5_reference rear and top pairs. The model's mantle is a single uniform
  #69733f sheet from shoulder to shoulder; the reference moss is a brighter yellow-green in clumps with hide
  showing down the centre of the back and large flat grey rocks (0.4-0.6 m) half-bedded in it.
- Stage: 3.
- Fix: (a) paint the moss region with the brief's #6f8f3a (keep the dark hide and stone as is); (b) rocks:
  scale the 4 bedded rocks to 0.45-0.6 m across (12-15% of body length), sink them 40% into the mantle, and
  move two onto the shoulder caps where the reference has them; (c) moss clumps: 4-6 clumps 0.3-0.4 m, proud
  of the mantle by 0.08-0.12 m, so the mantle top has lumps instead of a smooth dome.
- Check: 1_beauty back34 and the top pair in 5_reference: rocks read as rocks at thumbnail size, moss reads
  as the reference's green; 2_closeups moss crop shows clump relief. Colour count stays <= 8.

### 3. Loincloth flaps are paper-thin rods in profile
- Where: 1_beauty az090 (both flaps read as sticks hanging 0.2-0.3 m off the body), hero (front flap a flat
  plate). 2_closeups front limb wire: the flap is a single-layer fan.
- Stage: 3.
- Fix: give both flaps a thickness of 0.06-0.08 m (closed box, not a plate), hang the front flap against the
  belly/thigh curve with a 2-4 cm clearance (not 0.2 m), and widen the front flap top to the full belt width
  between the thighs (reference: ~0.7 m, 18% of body width). Ragged hem keeps 4-5 points.
- Check: az090: the flaps read as cloth with an edge, lying on the body; techqa hit 0, drift 0, and the
  posed frames in 4_posed show the flaps still clear of the legs in move_f009/f017.

### 4. Belly and pec shelf are flat
- Where: 1_beauty az090 and the side pair in 5_reference: the model's torso front is a straight line from
  chest to knee; the reference bulges 0.25 m forward at belly height. az000: no pot belly reads below the
  pecs.
- Stage: 2 (the r02 move was 0.07 m; the IoU is 0.993, so there is room).
- Fix: belly verts z 1.3-2.0, |x| < 0.6: forward (-Y) by a further 0.12-0.15 m (5-6% of body length), falloff
  to zero at z 1.1 and z 2.15; under-pec row z 2.2 back 0.03 more so the shelf overhang reads. Re-fit belt
  item 1 after this.
- Check: az090 silhouette shows a belly bulge in front of the thigh line; IoU side/front > 0.9 (logged).

### 5. Toes are nubs
- Where: 1_beauty az000 and hero, 2_closeups hind limb: three small blocks under a flat wedge foot. Reference:
  three big rounded toes with stone nails, ~1/3 of the foot's length.
- Stage: 3.
- Fix: scale each toe to 0.22-0.26 m long (30% of foot length) and 0.18 m tall, nails 0.08 m, toes abutting
  with no gap, tops rounded (chamfer the front top edge). Keep the sole dark.
- Check: az000: the toes read at thumbnail size as the reference's; techqa float 0, hit 0.

## STAGE-1 UNLOCK

None needed. Every item above is a stage-2 or stage-3 change; the base silhouette matches the reference
in all four views and should stay locked.

## Should-fix (short)

- Ears: the pointed ears stick out sideways and read as cat ears in hero and az000; the reference has none
  visible. Remove them or lay them back along the skull at half size (stage 3).
- Face: the dark paint under the socket runs down to the nostril as a diagonal slash in the head crop; limit
  the dark region to the socket and the mouth crease (stage 3 paint).
- Fists: fingers read as four equal blocks; make the knuckle row one step bigger than the finger bodies
  (stage 3).
- Attack clip: the slam passes the forearms through the belt / flank (clip warning 8.4% area, pink in
  3_tech hero); raise the arm arc 10-15 deg so the forearm clears the hip (stage 4).
- Moss cap top in the top view is a smooth dome; item 2's clumps cover this.
