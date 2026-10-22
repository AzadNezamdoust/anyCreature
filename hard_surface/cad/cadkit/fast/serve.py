"""Warm build daemon: pays the build123d import (~40 s on a loaded box, ~3-5 s idle) once, then runs builds.

    python -m cadkit.fast.serve <port_file>       (round.py starts it on demand, one per out/fast/<name>)
Protocol: one TCP connection per build on 127.0.0.1, request = one JSON line {"argv": [...build args]},
reply = one JSON line {"ok", "total_s"}. Results are in the files build() writes.
Isolation: a per-op timeout (build watchdog) or an OCCT crash kills only THIS daemon; round.py notices the
dropped connection, reports it, and the next round starts a fresh daemon (cached ops survive on disk).
Exits after IDLE_S idle or MAX_BUILDS builds (bounds OCCT memory growth / heap damage).
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time

IDLE_S = float(os.environ.get("CADKIT_FAST_IDLE", "1800"))
MAX_BUILDS = int(os.environ.get("CADKIT_FAST_MAX_BUILDS", "25"))


def src_sig():
    """mtime signature of the kit + fast sources: a daemon running older code is replaced by round.py."""
    here = os.path.dirname(os.path.abspath(__file__))
    kit = os.path.dirname(here)
    fs = [os.path.join(d, f) for d in (here, kit, os.path.join(kit, "tools")) if os.path.isdir(d)
          for f in os.listdir(d) if f.endswith(".py")]
    return str(round(max(os.path.getmtime(f) for f in fs), 3))


def _purge_model_modules(model_dir):
    md = os.path.normcase(os.path.abspath(model_dir))
    for k, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if f and os.path.normcase(os.path.dirname(os.path.abspath(f))) == md:
            del sys.modules[k]


def main(port_file):
    import build123d  # noqa: F401  (the slow import, once)
    import cadkit  # noqa: F401
    from cadkit.fast import build
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    srv.settimeout(IDLE_S)
    tmp = port_file + ".tmp"
    json.dump({"port": srv.getsockname()[1], "pid": os.getpid(), "t": time.time(), "src": src_sig()}, open(tmp, "w"))
    os.replace(tmp, port_file)
    n = 0
    try:
        while n < MAX_BUILDS:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                break
            with conn:
                f = conn.makefile("rwb")
                req = json.loads(f.readline())
                if req.get("ping"):
                    f.write(b'{"pong": true}\n')
                    f.flush()
                    continue
                _purge_model_modules(os.path.dirname(os.path.abspath(req["argv"][0])))
                try:
                    st = build.build(req["argv"])
                    rep = {"ok": st.get("ok"), "total_s": st.get("total_s")}
                except Exception as e:   # build() catches model errors itself; this is a harness bug
                    rep = {"ok": False, "error": f"serve: {type(e).__name__}: {e}"}
                f.write((json.dumps(rep) + "\n").encode())
                f.flush()
                n += 1
    finally:
        try:
            os.remove(port_file)
        except OSError:
            pass
    os._exit(0)


if __name__ == "__main__":
    main(sys.argv[1])
