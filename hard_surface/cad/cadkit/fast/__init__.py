"""cadkit.fast - iteration-speed layer on top of the kit (no core edits).

cache.py   content-addressed op cache (B-rep results on disk, keyed by op + input geometry + params)
build.py   worker: exec model with the cache on, write state.json + fine mesh.npz + continuity/feature data
render.py  ModernGL offscreen clay / zebra / ortho / silhouette sheet (< 2 s)
gate.py    composite quality gate (IoU per ortho view, feature checklist, fillet shrink, fallbacks, G1/G2)
round.py   one-call round: build -> render -> gate -> diff vs last round
"""
