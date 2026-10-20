# Class rules — weapon (WF v10, `pipeline: "direct"`)

Handheld first-person-shooter weapons. No JS-kernel module and no validator chain: the model is a Blender build
(`out/blender-hs/<s>/build.py` on `scripts/hs/hs.py`), brief `out/blender-hs/BUILD-DIRECT.md`, method `scripts/hs/method.md`.

## Frame
- Metres. **Muzzle +z, the weapon's left flank +x, y up.** `y = 0` is the weapon's LOWEST point (magazine floor plate,
  grip heel or bipod foot — whichever the side view shows lowest), x is centred on the bore plane, z is centred on the
  overall length (muzzle tip at `+L/2`, butt at `-L/2`).
- Bore plane in the registration (2026-10-10): the span rule centres front / rear / top on the whole silhouette, so a
  part protruding from one flank (facts.json `asymmetric[].protrudes`) moves the bore off x = 0. `scripts/v7/boreplane.mjs
  --subject <s> --write` measures the front / rear mirror-symmetry axis and writes it as views.json per-view `shift`
  (+ `_boreplane` evidence); then build on x = 0. Without it the registered bore sits at the bbox-centred offset.
- Views (`subjects/<s>/turnaround/views.json`): side = the left flank, muzzle to the image left; front = muzzle on (the
  weapon's left on the image right); rear = butt on; top = plan, muzzle to the image left, left flank at the bottom.
- The scale anchor is the stated overall length L (not the width): `views.json anchor {dim: "L"}`. `families.table` holds
  ONE family (`body` = every flat colour of the concept) so the L / W spans are the whole foreground.
- Concept camera: the style's fixed isometric (30 deg elevation, 45 deg azimuth from front-left), `subjects/<s>/camera.json`
  written by `gold.mjs new`; scale / offset fitted to the concept's foreground box (`hull.mjs --write-frame`,
  `scripts/v7/conceptreg.mjs`).

## Parts (roles are free text for the judge; these names are what rig.json and reviews expect)
`receiver`, `barrel`, `handguard`, `stock`, `grip`, `magazine`, `trigger`, `trigger_guard`, `bolt`,
`charging_handle`, `slide`, `pump`, `cylinder`, `barrel_cluster`, `drum`, `belt_box`, `feed_cover`, `sight`, `optic`,
`rail`, `muzzle_device`, `bipod`, `selector`, `tube`, `rocket`.

## Riggable rules (function stage, `scripts/hs/rig.md` "Handheld weapons")
- Every moving group is its own object: trigger, magazine, bolt / charging handle / slide / pump, cylinder, barrel
  cluster, each bipod leg, a folding stock, a feed cover, the selector lever.
- Closed geometry under moving parts: the magazine well is a real pocket the magazine slides out of, the ejection port
  shows a bolt (not a hole into nothing), the breech face behind a cylinder / barrel cluster is closed.
- Pivots on axes: the barrel, a barrel cluster and a cylinder are bodies of revolution about their axis; the bore is a
  straight line along z; the sights sit on one line above the receiver.
- Clearance: the trigger swings inside the guard, the bolt handle travels its slot without touching the receiver
  walls, the magazine clears the well over its whole travel.
- Hollow muzzle (`hs.bore`), a real trigger-guard opening, no decals or text.
