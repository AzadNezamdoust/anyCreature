"""
matfix_all.py -- run matfix_probe.py on every finished build (out/blender-hs/*/stats.json) and compare with the
pre-guard hs.py:
  orig   = the pre-guard hs.py (--orig-hs <dir>)          <- baseline
  orig2  = the same again                                  <- run-to-run noise of the build itself
  off    = hs.py as shipped, guards off (as finished)      must equal orig (vertex coordinates, face materials, slots)
  guards = hs.py with HS_GUARDS=1                          informational: what the guards would change
  python scripts/hs/fuzz/matfix_all.py --orig-hs <dir> [--workers 6] [--subjects a,b]
Writes out/fuzz/matfix/<s>.<variant>.json and out/fuzz/matfix/summary.txt.
"""
import argparse
import glob
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
OUT = os.path.join(ROOT, "out", "fuzz", "matfix")


def run(args, s, variant):
    path = os.path.join(OUT, f"{s}.{variant}.json")
    if os.path.exists(path):
        return
    cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", os.path.join(HERE, "matfix_probe.py"),
           "--", "--subject", s, "--out", path]
    if variant in ("orig", "orig2"):
        cmd += ["--hs-dir", args.orig_hs]
    env = dict(os.environ)
    env.pop("HS_GUARDS", None)
    if variant == "guards":
        env["HS_GUARDS"] = "1"
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace", env=env)
    if r.returncode != 0 or not os.path.exists(path):
        print(f"{s} {variant}: FAILED rc={r.returncode}\n{r.stdout[-1500:]}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig-hs", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--subjects", default="")
    args = ap.parse_args()
    subs = args.subjects.split(",") if args.subjects else sorted(
        os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "out", "blender-hs", "*", "stats.json")))
    os.makedirs(OUT, exist_ok=True)
    jobs = [(s, v) for s in subs for v in ("orig", "orig2", "off", "guards")]
    with ThreadPoolExecutor(max_workers=min(args.workers, 6)) as ex:
        list(ex.map(lambda j: run(args, *j), jobs))
    lines = []
    ok = True
    for s in subs:
        for v in ("orig2", "off", "guards"):
            a, b = os.path.join(OUT, f"{s}.orig.json"), os.path.join(OUT, f"{s}.{v}.json")
            if not (os.path.exists(a) and os.path.exists(b)):
                lines.append(f"[{v}] {s}: MISSING")
                ok = False
                continue
            r = subprocess.run([sys.executable, os.path.join(HERE, "matfix_probe.py"), "--compare", a, b], capture_output=True, text=True)
            lines.append(f"[{v}] " + r.stdout.strip())
            if v == "off":
                ok &= r.returncode == 0 and "slot_lists_changed 0" in r.stdout
    lines.append("OVERALL (off vs orig) " + ("PASS" if ok else "FAIL"))
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
