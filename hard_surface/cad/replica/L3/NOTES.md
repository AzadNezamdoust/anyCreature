# L3 replica - DeWalt DCD777 + DCB201  (final = r6)
Files: model.py (named constants, coords = side-photo px * S), round.py (render round), iou.py (side IoU vs ref mask).
Out: out/replica/L3/dcd777.step, dcd777_hq.glb (+ r1..r6 dirs). Images here: hero/clay/zebra/side_clay.jpg,
overlay_side.jpg (blue=ref only, yellow=model only, grey=both), compare.jpg (ref | model left ortho).

## Rounds
| r | change | side IoU |
|---|---|---|
| 1 | first build: revolved chuck/clutch/gearcase, lofted housing, polyline side slabs | n/a (no IoU tool yet); rim fillets mostly reduced/partial |
| 2-3 | periodic-spline profiles | build failed: BSplCLib::Interpolate (dup end pt), then OCCT heap-corruption crash on rim fillet |
| 4 | polyline + 2D vertex fillets + rim fillet | 0.965 |
| 5 | housing loft re-stationed | 0.915 (loft twisted at RectangleRounded seams) |
| 6 | housing = side-profile slab like the other shells | **0.971** |
Front / top / back IoU: NOT MEASURED - no orthographic front/top/back reference exists in the refs found.

## Dimension errors (side, vs ref photo at 0.1387 mm/px)
| dim | ref | model | err |
|---|---|---|---|
| head length (spec 7.52 in) | 191.0 | 189.5 | -1.5 mm (chuck nose fillet) |
| overall height with DCB201 | 227.1 | 227.1 | 0 |
| widths (housing 58, grip 40, foot 74, pack 76) | unknown | EST | unverified |

## Fillet / boolean log (r6)
- housing rim 14 -> 9.6, trigger housing 8 -> 4, grip 9 -> 6.2, foot 6 -> 2.0 (reduced), battery rim split_partial (some edges sharp).
- 0 failed booleans.
## Kit gaps (implemented locally, cadkit untouched)
- OCCT fillet of the rim of a periodic-spline extrusion crashes the process (0xc0000374). Local workaround: polyline
  profile + 2D vertex fillets (`side_solid`). Loft through RectangleRounded sections with varying aspect twists (seam).
- No silhouette-IoU / ref-overlay tool in kit -> replica/L3/iou.py.

## Remaining defects (honest)
- Shells are constant-width slabs with rounded rims: no crowning/draft of the real clamshell, flat sides read boxy (zebra).
- Widths are estimates (no front/top ref). Battery is a plain slab: missing DCB201 two-tone stepped top, label recess, grip ribs.
- Missing: yellow/black overmold split on grip, clutch numerals, LED, belt-hook slot, chuck jaws, rear vent grille detail,
  DeWALT logo/labels; side IoU hides these because they are inside the silhouette.
- Chuck tip rounded too much (-1.5 mm length); trigger slightly undersized at bottom.
