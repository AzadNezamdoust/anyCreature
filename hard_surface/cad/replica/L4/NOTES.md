# L4 replica - Xbox Wireless Controller (model 1914)

Build: `venv_cad python replica/L4/round.py L4 <n>`; IoU: `python replica/L4/iou.py <n>`. Final = r8.
Outputs: out/replica/L4/model.step, out/replica/L4/model_hq.glb (+ r<n>/ per round).
Images here: hero.jpg, clay.jpg, zebra.jpg, overlay_top.jpg, overlay_back.jpg (grey = match, red = ref only, blue = model only), compare.jpg (photo | model top ortho).

Method: body = plan extrusion (traced, symmetrised spline) n lofted underside skin n lofted domed top skin,
then one perimeter round (r5). Buttons/sticks/d-pad are separate parts in cut openings, seated on the analytic top
skin height. Part breaks: top/bottom shell split groove (z=31, planar - approximation), battery-door line,
USB-C, pair button, 3.5 mm jack.

## Rounds
| r | change | IoU top | IoU back | size X/Y/Z mm |
|---|---|---|---|---|
| 1 | plan n side-profile extrusion + rounds | 0.963 | 0.666 | 100.1/153/44.0 |
| 2 | lofted domed top, all features | 0.917 | 0.661 | 111.0/153/61.0 |
| 3 | body +5.5 mm, stick cap 12.5 mm proud, triggers inside depth | 0.944 | 0.740 | 103.4/153/58.7 |
| 4 | rolled underside loft, lever triggers, gimbal domes, spline seam moved (USB-C/jack booleans failed on the seam) | 0.941 | 0.663 | 103.3/152.6/55.4 |
| 5 | grip-only underside roll, LIFT 16 | crash (timeout; Manifold-faceted body) | | |
| 6 | single all-edge perimeter round, LIFT 12 unclamped | 0.944 | 0.733 | 103.3/153/58.7 |
| 7 | centre underside rise 8 mm | OCCT segfault, reverted | | |
| 8 | = r6 (final) | 0.944 | 0.733 | 103.3/153/58.7 |

## Dimension errors (final vs spec 153 x 102 x 61)
| dim | spec | model | err |
|---|---|---|---|
| width | 153 | 153.0 | 0 |
| depth | 102 | 103.3 | +1.3 (trigger levers) |
| height incl. sticks | 61 | 58.7 | -2.3 |

## Fillet / boolean failures
- r1-r3 bottom round r12 reduced to ~9.4; r4 top round split_partial + bottom skipped (edge classification by Z failed on the periodic rim edge) -> r6 rounds all rim edges at r5 (so the large r11 shoulder roll is NOT there).
- trigger r2.5 fillet failed on the periodic-spline seam edge -> triggers are lofts of shrunk sections instead.
- USB-C and 3.5 mm jack cuts failed when they sat on the plan spline seam -> seam rotated to the grip outer point.
- clamped underside loft -> common fell to Manifold (faceted, LINE edges) -> unclamped.
- centre-underside rise (real underside between grips ~10 mm above grip bottoms) -> segfault, not modelled.
- bumper skin cut needed fuzzy boolean.

## Remaining defects (honest)
- Refs are photos, not blueprints: plan trace is hand-digitised from an oblique photo, rescaled anisotropically to 153x102;
  rear mask includes the top face seen from above (~10 mm), which caps the back IoU (~0.73) regardless of the model.
- No side-view IoU: only a low-angle perspective side photo was available.
- Bumpers are slab cut-outs of a 3.5 % scaled skin with flat ends - not the real wrap-around bumper form.
- Underside between the grips is too low (model ~3 mm vs ~10 mm in the rear photo); grips read too flat.
- Shoulder roll only r5 vs ~11 mm real; top face is an analytic dome, not measured.
- Shell split line is a horizontal plane, real one curves; no grip texture panels (P3 shows separate textured grip backs).
- D-pad is a disc + cross, not the faceted hybrid dish; stick caps lack knurl; buttons lack legends; logo flat.
- Hero render orthographic top is rotated 180 deg vs the photo (compare.jpg rotated to match).

## Kit gaps
- No reliable way to select rim edges of a periodic-spline extrusion common; Z-split selection breaks.
- Perimeter fillet on loft-intersection bodies segfaults for some underside shapes (r7) - no crash isolation in worker path.
- No blueprint/silhouette IoU tool in cadkit: implemented locally (iou.py, ref_masks.py).
