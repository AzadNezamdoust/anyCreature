"""
regress.py -- re-run finished builds through run_pass.py (pass 99, outputs under out/fuzz/) and compare with their
stored out/blender-hs/<s>/stats.json: tris, topology (totals + per object) and per-view iou / agree.

  python scripts/hs/fuzz/regress.py --subjects apc_8x8,pistol [--guards] [--workers 6]

Guards off (default): the build runs exactly as finished -> must match stats.json. --guards: HS_GUARDS=1 forces
hs.begin(..., guards=True) without editing build.py (out/fuzz/regress_guards/<s>) -> report what changes.
"""
import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"


def run(s, guards):
    od = os.path.join("out", "fuzz", "regress_guards" if guards else "regress", s)
    os.makedirs(os.path.join(ROOT, od), exist_ok=True)
    if os.path.exists(os.path.join(ROOT, od, "pass99_stats.json")):
        return od
    env = dict(os.environ)
    env.pop("HS_GUARDS", None)
    if guards:
        env["HS_GUARDS"] = "1"
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", os.path.join("scripts", "hs", "run_pass.py"),
           "--", "--subject", s, "--pass", "99", "--out-dir", od]
    with open(os.path.join(ROOT, od, "run_pass.log"), "w", encoding="utf-8", errors="replace") as lf:
        subprocess.run(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, env=env)
    return od


def compare(s, od):
    ref = json.load(open(os.path.join(ROOT, "out", "blender-hs", s, "stats.json"), encoding="utf-8"))
    p = os.path.join(ROOT, od, "pass99_stats.json")
    if not os.path.exists(p):
        return False, [f"{s}: no pass99_stats.json (see {od}/run_pass.log)"]
    new = json.load(open(p, encoding="utf-8"))
    diffs = []
    if ref["tris"] != new["tris"]:
        diffs.append(f"tris {ref['tris']} -> {new['tris']}")
    rt, nt = ref["topology"]["totals"], new["topology"]["totals"]
    for k in rt:
        if rt[k] != nt.get(k):
            diffs.append(f"topo {k} {rt[k]} -> {nt.get(k)}")
    ro, no = ref["topology"]["objects"], new["topology"]["objects"]
    for n in sorted(set(ro) | set(no)):
        if ro.get(n) != no.get(n):
            a, b = ro.get(n) or {}, no.get(n) or {}
            ch = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
            diffs.append(f"object {n}: " + ", ".join(f"{k} {x}->{y}" for k, (x, y) in sorted(ch.items())))
    for v in ref["scores"]:
        for k in ("iou", "agree"):
            a, b = ref["scores"][v][k], new["scores"].get(v, {}).get(k)
            if a != b:
                diffs.append(f"{v} {k} {a} -> {b}")
    return not diffs, diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--guards", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    subs = args.subjects.split(",")
    with ThreadPoolExecutor(max_workers=min(args.workers, 6)) as ex:
        ods = list(ex.map(lambda s: run(s, args.guards), subs))
    lines = []
    for s, od in zip(subs, ods):
        same, diffs = compare(s, od)
        lines.append(f"{s}: {'IDENTICAL' if same else 'DIFFERS'} ({od})")
        lines += ["    " + d for d in diffs]
    tag = "guards" if args.guards else "off"
    open(os.path.join(ROOT, "out", "fuzz", f"regress_{tag}.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
