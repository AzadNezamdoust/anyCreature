"""Crash/hang isolation for OCCT ops inside model scripts (fillet/chamfer attempts on spline bodies).

OCCT's fillet builder can SEGFAULT / corrupt the heap (0xc0000374, ladder L3 drill, L4 Xbox) or spin for >10 min
(L2 mouse caps) on BSpline/periodic-extrusion bodies. Those attempts run in ONE persistent child process
(`python -m cadkit.isolate --serve`): shape is passed as a .brep file, edges by their index in TopExp.MapShapes
(order survives BRep write/read). Child crash or per-attempt timeout -> only THAT child is killed (by its own
Popen handle, never by name/pid scan, so other lanes' processes are untouched) and restarted lazily.

Env: CADKIT_ISOLATE=0 disables (in-process), =1 forces for every body (default: auto = bodies with free-form faces).
     CADKIT_OP_TIMEOUT (s, default 90) per attempt;  CADKIT_OP_BUDGET (s, default 600) per safe_fillet call.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess

_NOWIN_KW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}  # no stray console windows (Windows)
import sys
import tempfile
import threading
import time

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS = {"attempts": 0, "crashes": 0, "timeouts": 0, "restarts": 0}


class IsolationFailure(RuntimeError):
    """Attempt crashed or timed out in the child (parent is fine)."""


def mode():
    return os.environ.get("CADKIT_ISOLATE", "auto")


def needs_isolation(shape) -> bool:
    m = mode()
    if m == "0":
        return False
    if m == "1":
        return True
    try:
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere, GeomAbs_Torus
        simple = {GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Sphere, GeomAbs_Torus}
        return any(BRepAdaptor_Surface(f.wrapped).GetType() not in simple for f in shape.faces())
    except Exception:
        return True


def edge_indices(shape, edges):
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_EDGE
    mp = _imap()
    TopExp.MapShapes_s(shape.wrapped, TopAbs_EDGE, mp)
    out = []
    for e in edges:
        i = mp.FindIndex(e.wrapped)
        if i <= 0:
            raise IsolationFailure("edge not in shape (stale edge from an older body?)")
        out.append(i)
    return out


def _imap():
    try:
        from OCP.TopTools import TopTools_IndexedMapOfShape as M
    except ImportError:  # OCP 8.x
        from OCP.collections import IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher as M
    return M()


class OpWorker:
    def __init__(self):
        self.proc, self.q, self.n = None, None, 0
        self.tmp = tempfile.mkdtemp(prefix="cadkit_iso_")
        self._brep_of = []  # [(TopoDS_Shape, brep path)] (shape cached in the child by path)
        self.lock = threading.Lock()

    def _start(self):
        env = dict(os.environ, PYTHONPATH=CAD + os.pathsep + os.environ.get("PYTHONPATH", ""))
        self.proc = subprocess.Popen(**_NOWIN_KW, args=[sys.executable, "-u", "-m", "cadkit.isolate", "--serve"], cwd=CAD, env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, encoding="utf-8", bufsize=1)
        self.q = queue.Queue()
        p, q = self.proc, self.q

        def pump():
            for line in p.stdout:
                q.put(line)
            q.put(None)
        threading.Thread(target=pump, daemon=True).start()

    def kill(self):
        if self.proc is not None:
            try:
                self.proc.kill()  # this child only
                self.proc.wait(5)
            except Exception:
                pass
        self.proc = None
        STATS["restarts"] += 1

    def _path(self, shape):
        # keyed by the TopoDS object, which is kept alive with the entry (a bare id() gets reused by a later
        # body -> stale brep, wrong edge indices). Only the last few bodies are kept.
        for w, p in self._brep_of:
            if w.IsSame(shape.wrapped) and w.Location().IsEqual(shape.wrapped.Location()) and os.path.exists(p):
                return p
        from OCP.BRepTools import BRepTools
        self.n_in = getattr(self, "n_in", 0) + 1
        p = os.path.join(self.tmp, f"in_{self.n_in}.brep")
        BRepTools.Write_s(shape.wrapped, p)
        self._brep_of = (self._brep_of + [(shape.wrapped, p)])[-4:]
        return p

    def run(self, kind, shape, edges, value, timeout):
        """kind fillet|chamfer. Returns build123d shape or None (op not done / invalid). Raises IsolationFailure."""
        from OCP.BRepTools import BRepTools
        from OCP.BRep import BRep_Builder
        from OCP.TopoDS import TopoDS_Shape
        from build123d import Shape
        with self.lock:
            STATS["attempts"] += 1
            idx = edge_indices(shape, edges)
            src = self._path(shape)
            self.n += 1
            dst = os.path.join(self.tmp, f"out_{self.n}.brep")
            if self.proc is None or self.proc.poll() is not None:
                self._start()
            try:
                self.proc.stdin.write(json.dumps({"id": self.n, "kind": kind, "src": src, "edges": idx,
                                                  "value": value, "dst": dst}) + "\n")
                self.proc.stdin.flush()
            except OSError:
                self.kill()
                STATS["crashes"] += 1
                raise IsolationFailure("isolation child pipe broken")
            t_end = time.time() + timeout
            while True:
                try:
                    line = self.q.get(timeout=max(0.05, t_end - time.time()))
                except queue.Empty:
                    self.kill()
                    STATS["timeouts"] += 1
                    raise IsolationFailure(f"{kind} attempt timed out after {timeout:.0f}s (child killed)")
                if line is None:
                    code = self.proc.poll()
                    self.kill()
                    STATS["crashes"] += 1
                    raise IsolationFailure(f"{kind} attempt crashed the OCCT child (exit {code})")
                try:
                    rep = json.loads(line)
                except ValueError:
                    continue
                if rep.get("id") == self.n:
                    break
        if not rep.get("ok"):
            return None
        sh = TopoDS_Shape()
        BRepTools.Read_s(sh, dst, BRep_Builder())
        os.remove(dst)
        return Shape.cast(sh)


_W = None


def worker():
    global _W
    if _W is None:
        _W = OpWorker()
    return _W


def timeout_s():
    return float(os.environ.get("CADKIT_OP_TIMEOUT", "90"))


def budget_s():
    return float(os.environ.get("CADKIT_OP_BUDGET", "600"))


# ------------------------------------------------------------------ child
def _child_op(kind, shape, edges, value):
    from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer
    if kind == "debug_crash":
        import faulthandler
        faulthandler._sigsegv()
    if kind == "debug_hang":
        time.sleep(3600)
    mk = BRepFilletAPI_MakeFillet(shape) if kind == "fillet" else BRepFilletAPI_MakeChamfer(shape)
    for e in edges:
        mk.Add(value, e)
    mk.Build()
    if not mk.IsDone():
        return None
    return mk.Shape()


def serve():
    real = os.dup(1)
    os.dup2(2, 1)
    out = os.fdopen(real, "w", encoding="utf-8", buffering=1)
    from OCP.BRepTools import BRepTools
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Shape
    from build123d.topology.shape_core import downcast
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.BRepCheck import BRepCheck_Analyzer
    cache = {}
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        ok = False
        try:
            if msg["src"] not in cache:
                sh = TopoDS_Shape()
                BRepTools.Read_s(sh, msg["src"], BRep_Builder())
                mp = _imap()
                TopExp.MapShapes_s(sh, TopAbs_EDGE, mp)
                cache = {msg["src"]: (sh, mp)}  # keep one body (memory); paths are never reused
            sh, mp = cache[msg["src"]]
            es = [downcast(mp.FindKey(i)) for i in msg["edges"]]
            res = _child_op(msg["kind"], sh, es, float(msg["value"]))
            if res is not None and BRepCheck_Analyzer(res).IsValid():
                BRepTools.Write_s(res, msg["dst"])
                ok = True
        except Exception:
            ok = False
        out.write(json.dumps({"id": msg["id"], "ok": ok}) + "\n")
        out.flush()


if __name__ == "__main__" and "--serve" in sys.argv:
    serve()
