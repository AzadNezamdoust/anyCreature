# bear (abc/c1): art director notes, team round

Packet read: 1_beauty, 2_closeups, 3_tech, 4_posed, 5_reference, techqa.json, reference/sheet.png.

**Score: 6.5 / 10**
**Verdict: FIX** (no blocker, four majors; identity holds)

It reads as a bear in one glance from every view: hump high, head low, heavy body, pale muzzle, dot eyes,
nose pad, dark socks, five claws. Tech QA is clean (hit 0, float 0, z-fight 0, slivers 0.7%, flips 0, drift 0).
What keeps it off 7+ is the surface and the limbs: the body is a crumpled decimated hull rather than planes,
the hind legs are slabs with no hock, the front legs are not separated from the chest, and the attack clip
does not read as an attack.

## Keep (must not regress)
- Side silhouette (az090 / 5_reference side): hump is the highest point, back slopes to the rump, head carried low.
- Face kit at thumbnail: pale muzzle plane with a clean border, V bib under the chin, dot eyes, nose pad (az000, hero).
- Five graded claws rooted in each paw, no float/hit (2_closeups claws, 3_tech).
- Tail stub and round rump (back34).
- All stage-4 gates PASS.

## Must-fix (ordered by visual damage)

### 1. Body surface is a noisy hull, not planes
- Stage: 2
- Where: 1_beauty back34 and az090 (whole back, flank, rump), 2_closeups hind limb wire.
- Fix: `flatten` the big masses into a few large facets: back (one top plane from hump to rump), each flank
  (2-3 planes: rib cage, belly, hip), rump (2 planes), thigh (1-2 planes), hump cap. Remove the random small
  facets that catch light at different angles. Target: no light-catching facet smaller than ~5% of body length on
  back/flank; IoU stays > 0.9 (these are surface moves of ~1-2% of width).
- Check: 1_beauty back34 and az090: the flank and back read as 6-8 big flat planes like the reference sheet side view,
  no "crumpled paper" speckle. 2_closeups hind-limb wire shows planes, not a triangle soup.

### 2. Hind legs are pillars: no hock, no heel, no foot
- Stage: 2
- Where: 1_beauty az090 (hind leg is a straight vertical slab from belly to floor), 2_closeups hind limb colour/wire,
  5_reference side (reference hind leg has a clear hock angle and a flat plantigrade foot).
- Fix: at ~35-40% of hump height on the rear edge of the hind leg, pull the hock vertices back by ~4-5% of body
  length; below it, move the shin's front edge forward ~2-3% of length so the lower leg angles down-forward to a
  flat foot; flatten the foot top into a plane ~8% of length long. Keep the dark-sock loop on the new leg.
- Check: 1_beauty az090: a visible hock angle on the hind leg, the foot a flat block, as in the reference side view.
  IoU > 0.9 in every view.

### 3. Hind-leg dark paint is a jagged vertical patch, and the dark is too grey
- Stage: 3
- Where: 1_beauty az090 and back34: the dark region on the hind leg runs up the rear/inner side as an irregular
  stripe toward the belly instead of being a sock cut at the z 0.30 loop; 2_closeups hind limb colour (dark inner
  panel, light outer). The dark is #403832 (cool grey); the brief wants warm #4a3222.
- Fix: repaint the hind-leg dark region by the same vertex-side test as the front legs so the border is the planar
  loop at z 0.30 only (same height on all four legs). Warm dark fur toward #4a3222 (keep 6 colours).
- Check: 1_beauty az090 + back34: one straight horizontal dark border at the same height on all four legs; no dark
  tongue climbing the thigh. Palette on the sheet reads brown, not grey.

### 4. Front legs are not separated from the chest
- Stage: 2
- Where: 1_beauty hero and az000 (the near front leg is one block with the chest, a dark seam instead of a shoulder),
  2_closeups front limb (dark cleft panel between the legs, yellow slivers in the armpits on 3_tech hero/az000).
- Fix: raise the chest-floor vertices between the front legs by ~3% of hump height and pull the armpit vertices
  inward ~3% of body width so each leg reads as a cylinder leaving the body; flatten the shoulder-blade plane
  outward ~1-2% of width so a shoulder mass sits above the leg. Clean the armpit slivers with the same moves.
- Check: 1_beauty hero: a shadow gap between leg and chest, shoulder mass above the leg. 3_tech hero/az000: no
  yellow at the armpits. IoU > 0.9.

### 5. Attack clip does not read as an attack
- Stage: 4
- Where: 4_posed attack_f010 / attack_f020 look like idle frames (small head dip, feet planted, no paw off the ground).
- Fix: key a lunge: body forward ~10% of length and down ~5% of height at f010, head up; one front paw raised to
  chest height (~45% of hump height) and swept across ~20% of width at f020, with the opposite shoulder dropping.
  Keep the hind feet planted. Re-check drift/fold-over gates on every keyed frame.
- Check: 4_posed attack frames: raised paw and forward lean are obvious in wire at thumbnail size; gates PASS.

(No Stage-1 item. The carved base carries the identity; everything above is reachable in stages 2-4.)

## Should-fix (short)
- Ears: ~30% larger radius, moved up and back to the top corners of the skull; in az090 they are tiny fins (Stage 3).
- Brow: a small shelf above each eye (socket-top verts out ~1% of length) so the eye sits under a brow, not on the
  mask border; eyes ~15% larger (Stage 2 / 3).
- A mouth notch: a single short dark edge under the nose pad on the muzzle underside (Stage 2 flatten + Stage 3 paint).
- Paws: widen the front paws ~15% and lengthen claws ~20%; they are narrow boots with needle claws (Stage 2 / 3).
- Front view width: the reference's shoulders are squarer and the stance wider; splay the front feet ~3% of width (Stage 2).
