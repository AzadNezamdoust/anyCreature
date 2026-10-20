"""
matfix_probe.py -- byte-level signature of a finished build (Blender 5.1, background): proves an hs.py change is
geometry-neutral on out/blender-hs/<s>/build.py without rendering or scoring.

  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 ^
      --python scripts/hs/fuzz/matfix_probe.py -- --subject <s> --out <json> [--hs-dir <dir with hs.py>]

--hs-dir: import hs from there (default scripts/hs; pass a copy of the pre-guard hs.py for the original baseline).
Guards follow the build (off for every finished build) unless HS_GUARDS=1 is set in the environment.

Per part: tris, vertex count, sha1 of the float32 vertex coordinates, sha1 of the polygon vertex lists, sha1 of the
per-face material NAMES (the slot a face renders with, independent of slot indices), the slot list (None = empty), and
`canon`: an ORDER-INVARIANT sha1 of the part = the sorted list of faces, each face = its exact float32 corner
coordinates in loop order (rotated to start at the smallest corner, so winding counts but the loop start does not)
+ its material name. Blender builds are not order-deterministic run to run (the same hs.py twice gives a different
face / vertex order on ~1 part in 30, identical coordinates); `canon` is what "same geometry" means here.
compare: python scripts/hs/fuzz/matfix_probe.py --compare a.json b.json   (plain Python)
"""
import hashlib
import importlib.util
import json
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def _arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # hard_surface


def compare(a, b):
    A, B = json.load(open(a, encoding="utf-8")), json.load(open(b, encoding="utf-8"))
    geo = mat = slots = order = 0
    notes = []
    for name in sorted(set(A["parts"]) | set(B["parts"])):
        pa, pb = A["parts"].get(name), B["parts"].get(name)
        if pa is None or pb is None:
            geo += 1
            notes.append(f"{name}: missing in {'a' if pa is None else 'b'}")
            continue
        if pa.get("canon") == pb.get("canon") and pa["canon"] is not None:
            if any(pa[k] != pb[k] for k in ("co", "polys", "facemat")):
                order += 1
            if pa["slots"] != pb["slots"]:
                slots += 1
                notes.append(f"{name}: slots {pa['slots']} -> {pb['slots']}")
                mat += 1
            continue
        if any(pa[k] != pb[k] for k in ("tris", "verts", "co", "polys", "canon")):
            geo += 1
            how = []
            for k in ("tris", "verts", "polys", "co_um"):
                if k in pa and pa[k] != pb[k]:
                    how.append(k if k not in ("tris", "verts") else f"{k} {pa[k]}->{pb[k]}")
            if "bbox" in pa:
                how.append(f"bbox max|d| {max(abs(x - y) for x, y in zip(pa['bbox'], pb['bbox'])):.2e}")
            notes.append(f"{name}: geometry differs ({', '.join(how) or 'float bits only'})")
        if pa["facemat"] != pb["facemat"]:
            mat += 1
            notes.append(f"{name}: per-face materials differ")
        if pa["slots"] != pb["slots"]:
            slots += 1
            ra = [s for s in pa["slots"] if s is not None]
            rb = [s for s in pb["slots"] if s is not None]
            only_empty = ra == rb
            notes.append(f"{name}: slots {pa['slots']} -> {pb['slots']}" + ("" if only_empty else "  NON-EMPTY SLOTS CHANGED"))
            if not only_empty:
                mat += 1
    verdict = "PASS" if geo == 0 and mat == 0 else "FAIL"
    print(f"{A['subject']}: {verdict} parts {len(A['parts'])} geometry_diff {geo} facemat_diff {mat} slot_lists_changed {slots} "
          f"order_only {order} "
          f"empty_slots {A['empty_slots']} -> {B['empty_slots']}")
    for n in notes:
        print("   ", n)
    return verdict == "PASS"


if "--compare" in argv:
    i = argv.index("--compare")
    ok = compare(argv[i + 1], argv[i + 2])
    sys.exit(0 if ok else 1)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

SUBJECT = _arg("--subject")
HSDIR = os.path.abspath(_arg("--hs-dir", os.path.join(ROOT, "scripts", "hs")))
sys.path.insert(0, HSDIR)
sys.dont_write_bytecode = True
import hs  # noqa: E402

BUILD = os.path.join(ROOT, "out", "blender-hs", SUBJECT, "build.py")
sys.path.insert(1, os.path.dirname(BUILD))
spec = importlib.util.spec_from_file_location(f"build_{SUBJECT}", BUILD)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
root, parts = mod.build()
bpy.context.view_layer.update()


def sha(arr):
    return hashlib.sha1(np.ascontiguousarray(arr).tobytes()).hexdigest()[:16]


out = {"subject": SUBJECT, "hs": os.path.join(HSDIR, "hs.py"), "guards": getattr(hs, "GUARDS", None), "parts": {}, "empty_slots": 0, "guard_warn": list(getattr(hs, "GUARD_WARN", []))}
for ob in parts:
    if ob.type != "MESH":
        continue
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    nl = len(me.loops)
    lv = np.empty(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_start", ls)
    mi = np.empty(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    slots = [m.name if m is not None else None for m in me.materials]
    names = [(slots[i] if 0 <= i < len(slots) else f"<oob {i}>") or "<empty>" for i in mi.tolist()]
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    cb = co.reshape(-1, 3)
    vkey = [cb[i].tobytes() for i in range(n)]
    faces = []
    for fi in range(len(ls)):
        a = int(ls[fi])
        b = int(ls[fi + 1]) if fi + 1 < len(ls) else nl
        loop = [vkey[i] for i in lv[a:b].tolist()]
        k = loop.index(min(loop))
        faces.append(b"".join(loop[k:] + loop[:k]) + b"|" + names[fi].encode())
    canon = hashlib.sha1(b"".join(sorted(hashlib.sha1(f).digest() for f in faces))).hexdigest()[:16]
    out["parts"][ob.name] = {"tris": tris, "verts": n, "co": sha(co), "co_um": sha(np.round(co.astype(np.float64), 6)),
                             "bbox": [float(co.reshape(-1, 3)[:, i].min()) if n else 0.0 for i in range(3)] +
                                     [float(co.reshape(-1, 3)[:, i].max()) if n else 0.0 for i in range(3)], "polys": sha(np.concatenate([ls, lv])),
                             "facemat": hashlib.sha1("\n".join(names).encode()).hexdigest()[:16], "slots": slots,
                             "faces_on_empty": names.count("<empty>"), "canon": canon}
    out["empty_slots"] += slots.count(None)
os.makedirs(os.path.dirname(os.path.abspath(_arg("--out"))), exist_ok=True)
with open(_arg("--out"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("PROBE", SUBJECT, "parts", len(out["parts"]), "empty_slots", out["empty_slots"], "->", _arg("--out"))
