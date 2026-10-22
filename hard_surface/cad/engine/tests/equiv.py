"""Equivalence: run every journal in cases.py through the Python kit (cadkit.tools.Model, the REFERENCE) and the
C++ engine; compare per object: kind, volume/area/length (rel 1e-5), bbox (abs 1e-4 * scene size), face/edge counts,
validity, plus op errors. Writes engine/tests/equiv_report.json. Run with E:\\gen3d\\venv_cad\\Scripts\\python.exe.

    python engine/tests/equiv.py [case ...]
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, CAD)
sys.path.insert(0, HERE)

from cases import CASES  # noqa: E402


def run_py(journal):
    from cadkit.tools import Model, ToolError
    m, errs, t0 = Model(), [], time.perf_counter()
    for i, (op, p) in enumerate(journal):
        try:
            m.run(op, **p)
        except ToolError as e:
            errs.append((i, op, str(e)[:200]))
    return m.state()["objects"], errs, time.perf_counter() - t0


def run_cpp(eng, journal, sess):
    from cadkit.engine_client import EngineError
    eng.new(sess)
    errs, t0 = [], time.perf_counter()
    for i, (op, p) in enumerate(journal):
        try:
            eng.run(op, session=sess, **p)
        except EngineError as e:
            errs.append((i, op, str(e)[:200]))
    return eng.state(sess)["objects"], errs, time.perf_counter() - t0


def close(a, b, rel=1e-5, abs_=1e-9):
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


def compare(po, co):
    rows, scale = [], 1e-12
    for o in po.values():
        if "bbox" in o:
            scale = max(scale, max(abs(v) for c in o["bbox"] for v in c))
    for k in sorted(set(po) | set(co)):
        if k not in po or k not in co:
            rows.append({"obj": k, "ok": False, "why": "missing in " + ("cpp" if k not in co else "py")})
            continue
        a, b = po[k], co[k]
        bad = []
        if a["kind"] != b["kind"]:
            bad.append(f"kind {a['kind']} vs {b['kind']}")
        for f in ("volume", "area", "length"):
            if f in a and f in b and not close(a[f], b[f], abs_=1e-9 * scale ** 3):
                bad.append(f"{f} {a[f]} vs {b[f]}")
        for f in ("faces", "edges", "valid"):
            if f in a and f in b and a[f] != b[f]:
                bad.append(f"{f} {a[f]} vs {b[f]}")
        if "bbox" in a and "bbox" in b:
            d = max(abs(x - y) for ca, cb in zip(a["bbox"], b["bbox"]) for x, y in zip(ca, cb))
            if d > 1e-4 * scale:
                bad.append(f"bbox max diff {d:.3g}")
        rows.append({"obj": k, "ok": not bad, "why": "; ".join(bad),
                     **{f: [a.get(f), b.get(f)] for f in ("volume", "area", "faces", "edges") if f in a}})
    return rows


def main(names):
    from cadkit.engine_client import Engine
    eng = Engine()
    report, n_ok, n_all = {}, 0, 0
    for name in names or CASES:
        J = CASES[name]
        po, pe, pt = run_py(J)
        co, ce, ct = run_cpp(eng, J, name)
        rows = compare(po, co)
        ok = sum(r["ok"] for r in rows)
        n_ok += ok
        n_all += len(rows)
        same_err = [e[:2] for e in pe] == [e[:2] for e in ce]
        report[name] = {"objects_match": f"{ok}/{len(rows)}", "py_s": round(pt, 3), "cpp_s": round(ct, 3),
                        "py_errors": pe, "cpp_errors": ce, "errors_match": same_err,
                        "mismatches": [r for r in rows if not r["ok"]], "rows": rows}
        print(f"{name:22s} {ok}/{len(rows)} objects match  py {pt:7.2f}s  cpp {ct:6.3f}s  "
              f"errors py={len(pe)} cpp={len(ce)}{'' if same_err else ' (DIFFER)'}")
        for r in rows:
            if not r["ok"]:
                print(f"    {r['obj']}: {r['why']}")
        for e in pe + ce:
            print("    err", e)
    eng.close()
    report["_total"] = f"{n_ok}/{n_all}"
    json.dump(report, open(os.path.join(HERE, "equiv_report.json"), "w"), indent=1)
    print("TOTAL", n_ok, "/", n_all)


if __name__ == "__main__":
    main(sys.argv[1:])
