"""Round runner v2: edit -> incremental build -> fast render -> gate -> diff vs last round, one call.

    venv_cad python -m cadkit.fast.round <dir with model.py [+ gate_spec.json]> [--name L3] [--round N]
            [--timeout 600] [--op-timeout 240] [--no-cache] [--step] [--spec gate_spec.json] [--cold]
-> out/fast/<name>/r<N>/  state.json mesh.npz gate.json sheet.jpg overlay_*.png [judge_packet.png]
   out/fast/<name>/rounds.jsonl (one line per round: timings, cache hits, gate fails, diff)
Build runs in a warm per-name daemon (serve.py; --cold = fresh child per round, pays the ~40 s import): an op over --op-timeout makes the child exit itself (watchdog);
a total overrun kills only that child. Completed ops stay in the cache -> the next round resumes there.
Blender is NOT used; for the final hero render use cadkit.runner / render_hq.py once.
"""
from __future__ import annotations

import json
import os
import subprocess

_NOWIN_KW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}  # no stray console windows (Windows)
import sys
import time

import numpy as np
from PIL import Image

CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _arg(a, k, d=None):
    return a[a.index(k) + 1] if k in a else d


class _DaemonLost(RuntimeError):
    pass


def _src_sig():
    from cadkit.fast.serve import src_sig
    return src_sig()


def _spawn_daemon(base, pf):
    log = open(os.path.join(base, "serve.log"), "ab")
    flags = 0x08000000 | 0x00000200 if os.name == "nt" else 0   # CREATE_NO_WINDOW | NEW_PROCESS_GROUP (detached-from-console but no window)
    subprocess.Popen(args=[sys.executable, "-m", "cadkit.fast.serve", pf], cwd=CAD, stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, env=dict(os.environ, PYTHONPATH=CAD), creationflags=flags)


def _daemon_build(base, argv, timeout, start_wait=240):
    """Send one build to this name's warm daemon (start it if absent). Timeout -> kill THAT daemon (pid we
    recorded) only."""
    import socket
    pf = os.path.join(base, ".serve.json")
    t0 = time.time()
    started = False
    while True:
        info = None
        if os.path.exists(pf):
            try:
                info = json.load(open(pf))
            except Exception:
                info = None
        if info and info.get("src") != _src_sig():      # kit / fast code changed -> replace OUR daemon
            try:
                os.kill(info["pid"], 9)
            except OSError:
                pass
            try:
                os.remove(pf)
            except OSError:
                pass
            info = None
        if info:
            try:
                s = socket.create_connection(("127.0.0.1", info["port"]), timeout=5)
                break
            except OSError:
                try:
                    os.remove(pf)            # stale (daemon died)
                except OSError:
                    pass
                info = None
        if not started:
            _spawn_daemon(base, pf)
            started = True
        if time.time() - t0 > start_wait:
            raise _DaemonLost("daemon did not start")
        time.sleep(0.25)
    s.settimeout(timeout)
    f = s.makefile("rwb")
    f.write((json.dumps({"argv": argv}) + "\n").encode())
    f.flush()
    try:
        line = f.readline()
    except (socket.timeout, TimeoutError):
        try:
            os.kill(info["pid"], 9)
        except OSError:
            pass
        raise _DaemonLost(f"build_timeout > {timeout}s (daemon pid {info['pid']} killed)")
    finally:
        s.close()
    if not line:
        raise _DaemonLost("daemon exited during build (op timeout or OCCT crash) - restarted next round")
    rep = json.loads(line)
    rep["_daemon"] = {"cold_start": started, "wait_s": round(time.time() - t0, 2)}
    return rep


def run_round(src_dir, name=None, rnd=None, timeout=600, op_timeout=240, cache=True, step=False, model="model.py",
              spec=None, warm=True):
    src_dir = os.path.abspath(src_dir)
    name = name or os.path.basename(src_dir)
    base = os.path.join(CAD, "out", "fast", name)
    os.makedirs(base, exist_ok=True)
    prevs = sorted((int(d[1:]) for d in os.listdir(base) if d[:1] == "r" and d[1:].isdigit()))
    rnd = rnd if rnd is not None else (prevs[-1] + 1 if prevs else 1)
    prev = os.path.join(base, f"r{prevs[-1]}") if prevs and prevs[-1] != rnd else None
    rd = os.path.join(base, f"r{rnd}")
    os.makedirs(rd, exist_ok=True)
    spec = os.path.abspath(spec) if spec else os.path.join(src_dir, "gate_spec.json")
    T = {}
    t0 = time.time()
    cmd = [sys.executable, "-m", "cadkit.fast.build", os.path.join(src_dir, model), rd, "--op-timeout", str(op_timeout),
           "--cache", os.path.join(base, ".cache")]
    if not cache:
        cmd.append("--no-cache")
    if step:
        cmd.append("--step")
    if os.path.exists(spec):
        cmd += ["--features", spec]
    sp = os.path.join(rd, "state.json")
    if os.path.exists(sp):
        os.remove(sp)
    se = ""
    if warm:
        try:
            rep = _daemon_build(base, cmd[3:], timeout)
            T["daemon"] = rep.get("_daemon")
        except _DaemonLost as e:
            se = str(e)
    else:
        p = subprocess.Popen(**_NOWIN_KW, args=cmd, cwd=CAD, env=dict(os.environ, PYTHONPATH=CAD), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
        try:
            so, se = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()            # only our own child
            so, se = p.communicate()
            if not os.path.exists(sp):
                json.dump({"ok": False, "error": f"build_timeout > {timeout}s"}, open(sp, "w"))
    if not os.path.exists(sp):
        json.dump({"ok": False, "error": "crash", "stderr": (se or "")[-2000:]}, open(sp, "w"))
    T["build_s"] = round(time.time() - t0, 2)
    st = json.load(open(sp))
    rec = {"round": rnd, "ok": st.get("ok"), "build_s": T["build_s"], "exec_s": st.get("timing", {}).get("exec_s"),
           "cache": {k: st.get("cache", {}).get(k) for k in ("hits", "misses", "hit_s", "miss_s", "hash_s")}}
    from cadkit.fast import gate as G
    if st.get("ok"):
        from cadkit.fast.render import Scene, compose
        t1 = time.time()
        sc = Scene(os.path.join(rd, "mesh.npz"))
        tiles = [("front", "clay"), ("left", "clay"), ("top", "clay"), ("back", "clay"), ("iso", "clay"),
                 ("iso_back", "clay"), ("iso", "zebra"), ("top", "zebra"), ("left", "zebra")]
        ims = [(f"{v} {m}", sc.view(v, m, 480)) for v, m in tiles]
        ims[4][1].save(os.path.join(rd, "iso.png"))
        T["render_s"] = round(time.time() - t1, 2)
        t2 = time.time()
        g, ov = G.run(rd, spec, prev, scene=sc) if os.path.exists(spec) else ({"pass_auto": None, "fail": []}, [])
        T["gate_s"] = round(time.time() - t2, 2)
        extra = list(ov)
        if prev and os.path.exists(os.path.join(prev, "iso.png")):
            a = np.asarray(ims[4][1].convert("L"), float)
            b = np.asarray(Image.open(os.path.join(prev, "iso.png")).convert("L"), float)
            if a.shape == b.shape:
                d = np.clip(np.abs(a - b) * 3, 0, 255).astype(np.uint8)
                extra.append((f"diff iso vs r{os.path.basename(prev)[1:]}", Image.fromarray(255 - d)))
        compose(ims + extra, os.path.join(rd, "sheet.jpg"), 480)
        rec.update(gate_pass_auto=g.get("pass_auto"), fails=g.get("fail")[:12],
                   iou={k: v["iou"] for k, v in g.get("checks", {}).get("iou", {}).items()},
                   features=(lambda f: f and f"{f['pass']}/{f['n']}")(g.get("checks", {}).get("features")),
                   judge=g.get("judge", {}).get("status"), diff=g.get("diff"), faces=st.get("faces"),
                   tris=st.get("tris"), sheet=os.path.join(rd, "sheet.jpg"))
    else:
        rec.update(error=st.get("error"), op=st.get("op"), line=st.get("line"),
                   tb=(st.get("traceback") or st.get("stderr") or "")[-800:])
    T["total_s"] = round(time.time() - t0, 2)
    rec["t"] = T
    with open(os.path.join(base, "rounds.jsonl"), "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    return rec


if __name__ == "__main__":
    a = sys.argv[1:]
    r = run_round(a[0], _arg(a, "--name"), int(_arg(a, "--round")) if "--round" in a else None,
                  float(_arg(a, "--timeout", 600)), float(_arg(a, "--op-timeout", 240)), "--no-cache" not in a,
                  "--step" in a, _arg(a, "--model", "model.py"), _arg(a, "--spec"),
                  "--cold" not in a)
    print(json.dumps(r, indent=1, default=str))
