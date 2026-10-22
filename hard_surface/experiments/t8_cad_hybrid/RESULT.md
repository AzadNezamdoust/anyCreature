# t8_cad_hybrid: A/B result (2026-10-22)

The asset is assault_rifle, the only finished v10 weapon (pass 13, rig 21/21).
- Baseline A: `D:\Git\checkout\tools\LLMModeling\out\blender-hs\assault_rifle\build.py`. It was copied to `A/` and was not changed.
- Candidate B: `B/cad_parts.py`, run with build123d 0.13 in `venv/`. It uses the same locked part tree and the same dimensional plan (same metres and pixels), stored as exact B-rep solids. Booleans are exact, and the edges are broken with CAD chamfers. Each part is written to its own STL. Then `B/build.py` takes over in Blender: weld, material predicates, Freestyle marks, sharp edges above 30°, Weighted Normal and box-projected UVs.
- Both were scored by the same harness, `run_pass.py` (checkout), with `--build/--out-dir`. They used the same refs, camera and budget (8000 tris).

| metric | A baseline | B CAD hybrid |
|---|---|---|
| tris | 6048 | 6242 |
| topology (non-manifold / boundary / zero-area / duplicate / coincident) | 0 | 0 (pass 3) |
| agree side / front / rear / top | .925 / .718 / .734 / .855 | .925 / .718 / .734 / .855 |
| concept (not a gate) | .794 | .796 |
| v10 gate | PASS | PASS |
| judge J1 (A top, B bottom) | | picked bottom = B |
| judge J2 (B top, A bottom) | picked bottom = A | |
| judge net | flip = no preference, so the tie goes to the baseline | |
| checklist (10 yes/no) | 9/10 (pad not lighter) | 9/10 (same miss) |
| shading crops | clean, faint faceting on the butt | identical, clean |
| own read | the renders are practically indistinguishable; B's knob grooves and brake ports are as crisp | |
| cost | 13 passes + polish (historical) | about 1.5 h wall: about 12 min pip install, 3 Blender passes, about 10 CAD iterations |

What went wrong in B along the way:
- OCC chamfers on a whole set after a boolean hung for more than 5 min. Fixed by breaking each primitive's edges before the booleans, falling back to one edge at a time.
- Ruled B-spline lofts and true cylinders tessellated to 64k, then 19k tris. Fixed with planar-face sewn shells and game-res n-gon primitives, which got it to 7.4k.
- The sliver weld in Blender was needed to reach zero-area 0.
- One part (upper) needed ShapeFix to come out valid.

Verdict: **REJECT**. B gives the same outline, tris, topology and look. There is no judged gain, and the CAD layer adds a venv, OCC failure modes and more time. It only pays off for a part with real CAD-only features (threads, fillet blends, exact chamfered intersections), and this plan has none.

Files: `ab_compare.jpg` (top = A, bottom = B), `judge_order1.jpg`, `judge_order2.jpg`, `renders/`, `A/pass1_*`, `B/pass3_*`, `B/plan.json`.
