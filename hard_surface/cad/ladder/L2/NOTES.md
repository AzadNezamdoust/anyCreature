# L2 mouse - final r9 (9 rounds incl. r8 face-sort flake; 1 over the 8-round budget)
- Build 178 s (the 3D offsets are slow), 72 lines, 11 ops. Variable fillet on the base rim reduced. 0 fuzzy, 0 manifold.
- Body: loft through 12 superellipse stations, flat base, variable fillet 1 to 2.5 mm, 1.8 mm shell (body minus offset cavity), wheel slot pocket with filleted rim, split lines and thumb-button outlines that follow the skin, ribbed wheel, base plate.
- Broke: plan x side x section intersection then offset -> no; filleting a loft end cap SEGFAULTED OCCT (r2); the slot-rim fillet on an offset shell failed at any r; offset fails once features exist. Fixes: do all offsets on the clean loft first, fillet on the solid, then subtract the cavity.
- vs real CAD: smooth G2 zebra on the main body. Ends are near-point stations, not designed caps. Mid split line faint. Form is blobby, not a styled product.
