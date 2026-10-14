"""
run_fuzz.py -- run scripts/hs/fuzz/fuzz_helpers.py in K parallel Blender processes over a seed range.

  cd D:\\Git\\anyCreature\\hard_surface
  python scripts/hs/fuzz/run_fuzz.py --seed 0 --n 4000 [--workers 8] [--chunk 100] [--run main] [--no-freestyle]
  python scripts/hs/fuzz/report.py out/fuzz/main

The range is cut into chunks of --chunk cases; each chunk is one Blender process writing out/fuzz/<run>/chunk_<start>.jsonl.
A chunk that crashes (Blender segfault in a boolean) or hangs (no new output for --idle seconds) is killed, the case that
was running (fuzz_helpers writes its id to <jsonl>.cur) is recorded as {"fail": ["crash"|"hang"]} and the chunk resumes
after it. Re-running the same command resumes: finished chunks (<chunk>.done) are skipped.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # hard_surface
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
SCRIPT = os.path.join(HERE, "fuzz_helpers.py")

lock = threading.Lock()
state = {"done_cases": 0, "crashes": 0, "chunks_done": 0, "chunks_total": 0}


def count_cases(path):
    ids = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    ids.add(json.loads(ln)["case"])
                except (ValueError, KeyError):
                    pass
    return ids


def kill_tree(p):
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
    except OSError:
        p.kill()


def run_chunk(args, runroot, start, n):
    path = os.path.join(runroot, f"chunk_{start:07d}.jsonl")
    done = path + ".done"
    if os.path.exists(done):
        with lock:
            state["chunks_done"] += 1
            state["done_cases"] += n
        return
    log = os.path.join(runroot, "logs", f"chunk_{start:07d}.log")
    end = start + n
    restarts = 0
    while True:
        have = count_cases(path)
        nxt = start
        while nxt in have and nxt < end:
            nxt += 1
        if nxt >= end:
            break
        cmd = [BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", "--python", SCRIPT, "--",
               "--seed", str(nxt), "--n", str(end - nxt), "--out", path]
        if args.no_freestyle:
            cmd.append("--no-freestyle")
        if args.policy != "wide":
            cmd += ["--policy", args.policy]
        if args.safe_json:
            cmd += ["--safe-json", os.path.abspath(args.safe_json)]
        if args.fix:
            cmd += ["--fix", args.fix]
        if args.guards:
            cmd.append("--guards")
        with open(log, "a", encoding="utf-8", errors="replace") as lf:
            env = dict(os.environ)
            env.pop("HS_GUARDS", None)   # guards only via --guards
            p = subprocess.Popen(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, env=env)
            last = (-1, time.time())
            hang = False
            while p.poll() is None:
                time.sleep(2)
                sz = os.path.getsize(path) if os.path.exists(path) else 0
                if sz != last[0]:
                    last = (sz, time.time())
                elif time.time() - last[1] > args.idle:
                    hang = True
                    kill_tree(p)
                    p.wait()
                    break
            rc = p.returncode
        have2 = count_cases(path)
        if all(c in have2 for c in range(nxt, end)):
            break
        # a case did not finish: crash / hang / python error
        cur = None
        try:
            cur = int(open(path + ".cur").read().strip())
        except (OSError, ValueError):
            pass
        restarts += 1
        if cur is None or cur in have2 or restarts > 60:
            with lock:
                print(f"[chunk {start}] giving up (rc={rc}, cur={cur}, restarts={restarts})", flush=True)
            break
        rec = {"case": cur, "crash": True, "hang": hang, "rc": rc, "fail": ["hang" if hang else "crash"], "soft": []}
        with open(path, "a", encoding="utf-8") as fo:
            fo.write(json.dumps(rec) + "\n")
        with lock:
            state["crashes"] += 1
            print(f"[chunk {start}] case {cur} {'HANG' if hang else 'CRASH'} rc={rc}", flush=True)
    open(done, "w").write("ok")
    with lock:
        state["chunks_done"] += 1
        state["done_cases"] += n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--run", default="main")
    ap.add_argument("--idle", type=int, default=240, help="kill a chunk with no new output for this many seconds")
    ap.add_argument("--no-freestyle", action="store_true")
    ap.add_argument("--policy", default="wide", help="wide (default) | safe: constrained sampling, thresholds from --safe-json")
    ap.add_argument("--safe-json", default=None)
    ap.add_argument("--fix", default="", help="comma list of execution fixes under test: cutmats, weld, popnone")
    ap.add_argument("--guards", action="store_true", help="hs.begin(..., guards=True): the hs.py guards")
    args = ap.parse_args()
    runroot = os.path.join(ROOT, "out", "fuzz", args.run)
    os.makedirs(os.path.join(runroot, "logs"), exist_ok=True)
    chunks = [(s, min(args.chunk, args.seed + args.n - s)) for s in range(args.seed, args.seed + args.n, args.chunk)]
    state["chunks_total"] = len(chunks)
    meta = {"seed": args.seed, "n": args.n, "chunk": args.chunk, "workers": args.workers, "freestyle": not args.no_freestyle, "policy": args.policy, "safe_json": args.safe_json, "fix": args.fix,
            "guards": args.guards, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(runroot, "meta.json"), "w") as f:
        json.dump(meta, f)
    t0 = time.time()
    stop = threading.Event()

    def ticker():
        while not stop.wait(30):
            with lock:
                d = state["done_cases"]
            el = time.time() - t0
            prog = {"done_chunks": state["chunks_done"], "chunks": state["chunks_total"], "approx_cases": d, "of": args.n,
                    "crashes": state["crashes"], "elapsed_s": round(el), "finished": False}
            with open(os.path.join(runroot, "progress.json"), "w") as f:
                json.dump(prog, f)
            print(f"[{time.strftime('%H:%M:%S')}] chunks {state['chunks_done']}/{state['chunks_total']} cases~{d}/{args.n} crashes {state['crashes']} elapsed {el:.0f}s", flush=True)

    th = threading.Thread(target=ticker, daemon=True)
    th.start()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(lambda c: run_chunk(args, runroot, c[0], c[1]), chunks))
    stop.set()
    el = time.time() - t0
    with open(os.path.join(runroot, "progress.json"), "w") as f:
        json.dump({"done_chunks": state["chunks_done"], "chunks": state["chunks_total"], "approx_cases": args.n, "of": args.n,
                   "crashes": state["crashes"], "elapsed_s": round(el), "finished": True}, f)
    print(f"RUN DONE {args.n} cases in {el:.0f}s, crashes/hangs {state['crashes']} -> {runroot}", flush=True)


if __name__ == "__main__":
    main()
