# bear: blockout review

Verdict: **FIX**

```json
{"creature": "bear", "verdict": "FIX", "issues": [
 {"kind": "head",  "title": "Head is a narrow hanging wedge, not the broad skull of the concept"},
 {"kind": "mass",  "title": "Torso is one extruded tube: no shoulder mass, no waist, no haunch"},
 {"kind": "limbs", "title": "Hind leg is a straight post: no thigh, knee or hock"},
 {"kind": "limbs", "title": "Paws are thin flat planks, hind paws stick out behind the rump"},
 {"kind": "limbs", "title": "Wrist and hock collapse in fold and crouch"}
]}
```

Three questions. Is it the creature of the sheet: from the side yes (IoU 0.972, hump and
back line kept), from hero and front no, the head and the front end are a different, meeker
animal. Do the proportions match: the table passes, all six within 6 %. Designed cage or
scan: a side outline extruded sideways. The side view is solved; the width (front and top,
IoU 0.928 and 0.819, top barely over its floor) is not designed yet.

Kept and good: hump peak and its position, back line down to the rump, body length / height,
leg length, belly line, clean quad rings.

## Fixes (in order of weight)

1. **Head is a narrow hanging wedge, not the broad skull of the concept** (head)
   - Where: az000 and hero. In front the head is about 45 % of the shoulder width and sinks
     below the chest line; on the sheet front it is about 60 % and sits in front of the
     chest as its own block. From the side there is no forehead-to-muzzle step, the top
     line runs straight from the hump to the nose.
   - Direction: widen the cranium and cheeks by about 25 % of head width (to about 60 % of
     shoulder width), keep the muzzle at its present width so the skull-to-muzzle step
     appears. Raise the brow about 4 % of body height and drop a stop of about 3 % in front
     of it. Move the ears forward by about 6 % of body length onto the skull corners (they
     now sit on the neck behind the head) and make them wide blocks, about 20 % of head
     width each, so they break the front silhouette as on the sheet.

2. **Torso is one extruded tube: no shoulder mass, no waist, no haunch** (mass)
   - Where: top and az000 difference images, back34. Top: the model is too narrow at the
     shoulder (blue) and too wide through the middle (red), the sides are near parallel.
     Front: the upper flank is too wide (red both sides), a house shape instead of the
     sheet's sloped shoulders running into a narrow hump.
   - Direction: push the shoulder ring out about 6 % of body width per side at elbow
     height, pull the waist ring in about 8 % per side, keep the haunch at its present
     width. Pull the top of the shoulder in about 8 % of body width per side at 80 % body
     height so the hump narrows upward. The shoulder and the haunch should each read as a
     mass sitting on the barrel, with a plane break where they meet it.

3. **Hind leg is a straight post: no thigh, knee or hock** (limbs)
   - Where: az090 and back34. The hind leg drops as one even column from the rump to the
     ground; the sheet has a heavy thigh, the knee forward under the belly and the hock
     back.
   - Direction: widen the thigh at the top by about 15 % of leg length (front edge forward
     into the flank), move the knee forward about 5 % of body length, the hock back about
     4 %, and narrow the shank about 10 % below the hock. The fore leg needs the same in
     small: elbow back about 3 % of body length, forearm a little thicker than the upper
     arm line now suggests (limb thickness is 5 to 6 % under the sheet on both pairs).

4. **Paws are thin flat planks, hind paws stick out behind the rump** (limbs, stance)
   - Where: az090 and top difference (large red at the rear, blue at the front paws). The
     paws are slabs about 5 % of body height thick and longer than the leg is wide; the
     sheet paws are short tall wedges.
   - Direction: double the paw height to about 10 % of body height at the ankle, sloping
     to the toe; shorten them about 20 %; widen them about 10 % past the leg. Bring the
     hind paws forward about 5 % of body length so nothing passes the rump in top view,
     and turn the fore paws out to the sheet's footprint.

5. **Wrist and hock collapse in fold and crouch** (limbs, deformation)
   - Where: 5_rom fold az090 and crouch az090, wire. The wrist (2 loops, at the limit)
     pinches flat and the hind foot folds into the shank; 46 triangles flip, 4.48 % of the
     area. Elbow, knee, neck and the swing pose bend cleanly.
   - Direction: add a third loop at the wrist and space the three hock loops about 4 % of
     leg length apart, centred on the joint, with the paw starting one loop below the
     joint instead of on it. Target under 2 % flipped area.
