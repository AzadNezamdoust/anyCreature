"""
guards_report.py -- paired guards-off vs guards-on fuzz runs (same seeds), per guard (plain Python).

  python scripts/hs/fuzz/run_fuzz.py --seed 0 --n 1000 --workers 6 --run g_off --no-freestyle
  python scripts/hs/fuzz/run_fuzz.py --seed 0 --n 1000 --workers 6 --run g_on --guards --no-freestyle
  python scripts/hs/fuzz/guards_report.py out/fuzz/g_off out/fuzz/g_on [--out out/fuzz/guards_report.md]

Subsets (a case can be in several): the guard fired / applies in the guards-on run. "defect" = report.py's true
defect (any fail code except mat_empty_slot and run_pass's 1e-8 m2 zero-area rule); "mat" = mat_empty_slot /
mat_oob_faces. fixed = defect off -> clean on; broken = clean off -> defect on.
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import defect_codes, load  # noqa: E402


def subsets(r):
    rec = r.get("recipe") or {}
    base = rec.get("base") or {}
    ops = rec.get("ops") or []
    warn = r.get("guard_warn") or []
    out = []
    if any("bevel_mod" in w and "clamped" in w for w in warn):
        out.append("bevel clamp fired (width > 0.45 x thinnest)")
    if any("bevel_mod" in w and "safe range" in w for w in warn):
        out.append("bevel outside safe range (warn only)")
    if any(w.startswith("box chamfer") for w in warn):
        out.append("box chamfer clamp fired (> 0.45 x thinnest)")
    if base.get("k") == "tyre":
        hw = base["hw"]
        out.append("tyre hw < 0.045" if hw < 0.045 else ("tyre 0.045 <= hw < 0.2 (scaled)" if hw < 0.2 else "tyre hw >= 0.2 (unchanged)"))
    if any(o["op"] == "mirror_x" and o.get("via") == "apply" for o in ops):
        out.append("mirror_x (apply)")
    if any(o["op"] == "cut" for o in ops):
        out.append("has a boolean")
    if not out:
        out.append("other (finish weld only)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("off")
    ap.add_argument("on")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    A = {r["case"]: r for r in load(args.off)}
    B = {r["case"]: r for r in load(args.on)}
    ids = sorted(set(A) & set(B))
    rows = collections.OrderedDict()
    order = ["all cases", "bevel clamp fired (width > 0.45 x thinnest)", "bevel outside safe range (warn only)",
             "box chamfer clamp fired (> 0.45 x thinnest)", "tyre hw < 0.045", "tyre 0.045 <= hw < 0.2 (scaled)",
             "tyre hw >= 0.2 (unchanged)", "mirror_x (apply)", "has a boolean", "other (finish weld only)"]
    for k in order:
        rows[k] = collections.Counter()
    broken_codes = collections.Counter()
    fixed_codes = collections.Counter()
    for c in ids:
        a, b = A[c], B[c]
        da, db = bool(defect_codes(a)), bool(defect_codes(b))
        ma = any(x.startswith("mat_") for x in a.get("fail", []))
        mb = any(x.startswith("mat_") for x in b.get("fail", []))
        for k in ["all cases"] + subsets(b):
            row = rows[k]
            row["n"] += 1
            row["d_off"] += da
            row["d_on"] += db
            row["fixed"] += da and not db
            row["broken"] += db and not da
            row["m_off"] += ma
            row["m_on"] += mb
        if db and not da:
            broken_codes.update(set(defect_codes(b)))
        if da and not db:
            fixed_codes.update(set(defect_codes(a)))
    pc = lambda k, n: f"{k} ({100.0 * k / n:.1f} %)" if n else "-"
    lines = [f"paired cases: {len(ids)} (off: {args.off}, on: {args.on})", "",
             "| subset | n | defect off | defect on | fixed | broken | material fail off | on |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k, r in rows.items():
        if r["n"]:
            lines.append(f"| {k} | {r['n']} | {pc(r['d_off'], r['n'])} | {pc(r['d_on'], r['n'])} | {r['fixed']} | {r['broken']} | "
                         f"{pc(r['m_off'], r['n'])} | {pc(r['m_on'], r['n'])} |")
    lines += ["", "fixed cases, codes they had: " + ", ".join(f"{k} {v}" for k, v in fixed_codes.most_common()),
              "broken cases, codes they got: " + ", ".join(f"{k} {v}" for k, v in broken_codes.most_common())]
    txt = "\n".join(lines)
    print(txt)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
