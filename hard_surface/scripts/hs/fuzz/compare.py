"""
compare.py -- compare two fuzz runs (plain Python).

  python scripts/hs/fuzz/compare.py out/fuzz/main out/fuzz/fix_all [--label-a wide] [--label-b fixes]

Rates per failure code in both runs; when the same case ids exist in both (execution-fix variants share the recipes'
rng stream) also the paired counts: cases fixed (fail in A, clean in B) and cases broken (clean in A, fail in B).
"""
import argparse
import collections
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report import defect_codes, core, load  # noqa: E402


def rate(cases, pred):
    n = len(cases)
    k = sum(1 for r in cases if pred(r))
    return k, n, 100.0 * k / max(1, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--common", action="store_true", help="restrict both runs to the case ids they share")
    x = ap.parse_args()
    A = [r for r in load(x.a) if not r.get("crash")]
    B = [r for r in load(x.b) if not r.get("crash")]
    if x.common:
        ids = {r["case"] for r in A} & {r["case"] for r in B}
        A = [r for r in A if r["case"] in ids]
        B = [r for r in B if r["case"] in ids]
    print(f"{x.label_a}: {len(A)} cases ({x.a})   {x.label_b}: {len(B)} cases ({x.b})\n")
    codes = sorted({c for r in A + B for c in r["fail"]})
    print(f"| metric | {x.label_a} | {x.label_b} |\n|---|---:|---:|")
    for name, pred in (("any failure", lambda r: bool(r["fail"])), ("core (run_pass verbatim)", lambda r: bool(core(r))),
                       ("true defect", lambda r: bool(defect_codes(r)))):
        ka, na, pa = rate(A, pred)
        kb, nb, pb = rate(B, pred)
        print(f"| {name} | {ka}/{na} = {pa:.1f}% | {kb}/{nb} = {pb:.1f}% |")
    for c in codes:
        ka, na, pa = rate(A, lambda r, c=c: c in r["fail"])
        kb, nb, pb = rate(B, lambda r, c=c: c in r["fail"])
        print(f"| {c} | {ka} = {pa:.1f}% | {kb} = {pb:.1f}% |")
    ia = {r["case"]: r for r in A}
    ib = {r["case"]: r for r in B}
    both = sorted(set(ia) & set(ib))
    if both:
        print(f"\npaired on {len(both)} common case ids")
        for name, pred in (("true defect", lambda r: bool(defect_codes(r))), ("core", lambda r: bool(core(r))),
                           ("mat_empty_slot", lambda r: "mat_empty_slot" in r["fail"]),
                           ("freestyle_twice", lambda r: "freestyle_twice" in r["fail"])):
            fixed = sum(1 for k in both if pred(ia[k]) and not pred(ib[k]))
            broke = sum(1 for k in both if not pred(ia[k]) and pred(ib[k]))
            both_bad = sum(1 for k in both if pred(ia[k]) and pred(ib[k]))
            print(f"  {name}: fixed {fixed}, broken {broke}, still failing {both_bad}")


if __name__ == "__main__":
    main()
