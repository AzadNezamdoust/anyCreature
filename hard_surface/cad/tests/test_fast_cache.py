"""cadkit.fast op cache correctness: cached result == fresh build.

Each model is built three times in separate processes (as round.py does): fresh (--no-cache), cold cache
(all misses, fills it), warm cache (hits). Per part the three must agree on volume, area, face/edge/solid count,
bbox, validity and the cache's geometric fingerprint; warm must actually hit; an edit must miss only from the
edited op on.  CADKIT_FAST_TEST_REPLICA=1 also runs replica/L3 (slow: ~1-2 min).
"""
import json
import os
import subprocess
import sys
import textwrap

import pytest

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)

PROBE = textwrap.dedent('''
    import sys, json, runpy, hashlib
    sys.path.insert(0, sys.argv[3])
    from cadkit.fast import cache
    if sys.argv[2] != "-":
        cache.install(sys.argv[2])
    ns = runpy.run_path(sys.argv[1], run_name="__cadmodel__")
    from cadkit.worker import collect_parts
    out = {"calls": [c[:2] for c in cache.STATS["calls"]], "parts": {}}
    for k, (s, _) in collect_parts(ns).items():
        bb = s.bounding_box()
        out["parts"][k] = {"volume": s.volume, "area": s.area, "faces": len(s.faces()), "edges": len(s.edges()),
                           "solids": len(s.solids()), "valid": bool(s.is_valid),
                           "bbox": [*tuple(bb.min), *tuple(bb.max)],
                           "fp": hashlib.sha1(cache._fingerprint(s)).hexdigest()}
    from cadkit.ops import LOG
    out["log"] = [(o.get("op"), o.get("status")) for o in LOG]
    print("@@" + json.dumps(out))
    sys.stdout.flush()
    import os; os._exit(0)
''')

MODEL = textwrap.dedent('''
    from cadkit import *
    UNITS = "mm"
    R = {r}
    f = make_face(Polyline((0, 0), (40, 0), (40, 20), (10, 30), close=True))
    f = fillet(f.vertices(), 3)
    s = extrude(Plane.XZ * f, amount=10, both=True)
    s = safe_fillet(s, [e for e in s.edges() if abs(abs(e.center().Y) - 10) < 1e-3], 2.0, label="rim")
    try:
        s = safe_fillet(s, s.edges(), 50.0, label="too big")      # raises -> cached exception, re-raised on hit
    except Exception:
        pass
    s = cut(s, [Pos(x, 0, 10) * Box(4, 30, 4) for x in (12, 20, 28)], "slots")
    b = revolve(Plane.XZ * make_face(Polyline((0, 0), (R, 0), (R, 6), (0, 9), close=True)), Axis.Z)
    b = Pos(20, 0, 30) * b
    s = fuse(s, b, "knob")
    PARTS = {{"body": (s, "#888888"), "knob": (b, "#333333")}}
''')


def _run(model, cache_dir, tmp):
    p = subprocess.run([sys.executable, "-c", PROBE, model, cache_dir or "-", CAD], capture_output=True, text=True,
                       timeout=900, cwd=CAD, env=dict(os.environ, PYTHONPATH=CAD, CADKIT_ISOLATE="0"))
    line = [ln for ln in p.stdout.splitlines() if ln.startswith("@@")]
    assert line, p.stderr[-3000:]
    return json.loads(line[-1][2:])


def _same(a, b):
    assert a["parts"].keys() == b["parts"].keys()
    for k in a["parts"]:
        x, y = a["parts"][k], b["parts"][k]
        for q in ("faces", "edges", "solids", "valid", "fp"):
            assert x[q] == y[q], (k, q, x[q], y[q])
        for q in ("volume", "area"):
            assert abs(x[q] - y[q]) <= 1e-9 * max(1.0, abs(x[q])), (k, q, x[q], y[q])
        assert max(abs(u - v) for u, v in zip(x["bbox"], y["bbox"])) < 1e-7, k
    assert a["log"] == b["log"]


def test_cached_equals_fresh(tmp_path):
    m = tmp_path / "m.py"
    m.write_text(MODEL.format(r=8.0))
    c = str(tmp_path / "cache")
    fresh = _run(str(m), None, tmp_path)
    cold = _run(str(m), c, tmp_path)
    warm = _run(str(m), c, tmp_path)
    _same(fresh, cold)
    _same(fresh, warm)
    assert all(s == "miss" for _, s in cold["calls"])
    assert all(s == "hit" for _, s in warm["calls"]), warm["calls"]


def test_edit_replays_only_downstream(tmp_path):
    c = str(tmp_path / "cache")
    m = tmp_path / "m.py"
    m.write_text(MODEL.format(r=8.0))
    _run(str(m), c, tmp_path)
    m.write_text(MODEL.format(r=7.0))      # edit the revolve (late op)
    edited = _run(str(m), c, tmp_path)
    st = [s for _, s in edited["calls"]]
    first_miss = st.index("miss")
    names = [n for n, _ in edited["calls"]]
    assert names[first_miss] == "revolve"
    assert all(s == "hit" for s in st[:first_miss])
    m2 = tmp_path / "fresh.py"
    m2.write_text(MODEL.format(r=7.0))
    _same(_run(str(m2), None, tmp_path), edited)


@pytest.mark.skipif(os.environ.get("CADKIT_FAST_TEST_REPLICA") != "1", reason="slow; set CADKIT_FAST_TEST_REPLICA=1")
def test_replica_l3_cached_equals_fresh(tmp_path):
    m = os.path.join(CAD, "replica", "L3", "model.py")
    c = str(tmp_path / "cache")
    fresh = _run(m, None, tmp_path)
    _run(m, c, tmp_path)
    warm = _run(m, c, tmp_path)
    _same(fresh, warm)
    assert sum(s == "hit" for _, s in warm["calls"]) == len(warm["calls"])
