"""Thin client for the C++ CAD engine (hard_surface/cad/engine, `cadengine.exe`). No build123d / OCP import:
starts in milliseconds. One persistent engine process (CREATE_NO_WINDOW), JSON lines over stdio.

    from cadkit.engine_client import Engine
    e = Engine()                                     # starts engine\\bin\\cadengine.exe (or $CADENGINE_EXE)
    e.run("box", size=[0.6, 0.4, 0.4], name="crate")
    e.run("fillet", body="crate", edges={"parallel": "z"}, radius=0.03)
    e.set_param(0, "size", [0.7, 0.4, 0.4])          # replays only ops 0..end, cached ancestors reused
    e.render("out/sheet.png", modes=["clay", "zebra"])
    e.close()

Same op names / params / ref grammar / journal JSON as cadkit.tools.Model (journals are interchangeable).
Errors raise EngineError(message, hint, data) - same fields as cadkit.tools.ToolError.as_dict().
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import threading

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.environ.get("CADENGINE_EXE") or os.path.join(CAD, "engine", "bin", "cadengine.exe")
_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class EngineError(RuntimeError):
    def __init__(self, message, hint="", data=None, crashed=False):
        super().__init__(message)
        self.hint, self.data, self.crashed = hint, data or {}, crashed

    def as_dict(self):
        d = {"ok": False, "error": str(self), "hint": self.hint}
        if self.data:
            d["data"] = self.data
        if self.crashed:
            d["crashed"] = True
        return d


class Engine:
    """One engine process. Thread-safe (calls serialised). Restarts after an engine crash; the caller can reload
    the journal with load(journal) (the MCP wiring does this from the on-disk session journal)."""

    def __init__(self, exe=EXE, timeout=600.0, env=None):
        self.exe, self.timeout = exe, timeout
        self.env = dict(os.environ, **(env or {}))
        self.proc = None
        self.n = 0
        self.lock = threading.Lock()
        self._start()

    def _start(self):
        if not os.path.exists(self.exe):
            raise EngineError(f"cadengine not built: {self.exe}", "run hard_surface/cad/engine/build.bat")
        self.proc = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1,
                                     env=self.env, creationflags=_NOWIN)
        self.q = queue.Queue()
        p, q = self.proc, self.q

        def pump():
            for line in p.stdout:
                q.put(line)
            q.put(None)
        threading.Thread(target=pump, daemon=True).start()
        hello = self.q.get(timeout=60)
        if not hello:
            raise EngineError("cadengine failed to start (missing DLLs?)")
        self.info = json.loads(hello)

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def call(self, method, **params):
        with self.lock:
            if not self.alive():
                self._start()
            self.n += 1
            self.proc.stdin.write(json.dumps({"id": self.n, "method": method, "params": params}) + "\n")
            self.proc.stdin.flush()
            while True:
                try:
                    line = self.q.get(timeout=self.timeout)
                except queue.Empty:
                    self.proc.kill()
                    raise EngineError(f"{method}: engine timed out after {self.timeout:.0f}s (killed)", crashed=True)
                if line is None:
                    raise EngineError(f"{method}: engine process died (exit {self.proc.poll()})", crashed=True)
                try:
                    rep = json.loads(line)
                except ValueError:
                    continue  # stray output
                if rep.get("id") != self.n:
                    continue
                if "error" in rep:
                    e = rep["error"]
                    raise EngineError(e.get("message", "error"), e.get("hint", ""), e.get("data"),
                                      bool((e.get("data") or {}).get("crashed")))
                return rep["result"]

    # ---- modelling (same signatures as cadkit.tools.Model)
    def run(self, op, session="default", **params):
        return self.call("run", session=session, op=op, params=params)

    def undo(self, session="default"):
        return self.call("undo", session=session)

    def redo(self, session="default"):
        return self.call("redo", session=session)

    def checkout(self, node, session="default"):
        return self.call("checkout", session=session, node=node)

    def set_param(self, node, key, value, session="default"):
        return self.call("set_param", session=session, node=node, key=key, value=value)

    def state(self, session="default"):
        return self.call("state", session=session)

    def journal(self, session="default"):
        return self.call("journal", session=session)

    def load(self, journal, session="default"):
        return self.call("load", session=session, journal=journal)

    def new(self, session="default"):
        return self.call("new", session=session)

    def select(self, ref, session="default"):
        return self.call("select", session=session, ref=ref)

    def measure(self, a, b=None, session="default"):
        return self.call("measure", session=session, a=a, b=b)

    # ---- GPU
    def render(self, path, session="default", **kw):
        """kw: views=[...], modes=["clay","zebra","curvature"], res=300, objects=[...]"""
        return self.call("render", session=session, path=os.path.abspath(path), **kw)

    def register_ref(self, name, image, view="front", **kw):
        return self.call("register_ref", name=name, image=os.path.abspath(image), view=view, **kw)

    def iou(self, refs=None, session="default", objects=None):
        return self.call("iou", session=session, refs=refs, objects=objects)

    def deviation(self, a, b, heatmap=None, session="default", **kw):
        return self.call("deviation", session=session, a=a, b=b,
                         heatmap=os.path.abspath(heatmap) if heatmap else None, **kw)

    def stats(self, session="default"):
        return self.call("stats", session=session)

    def close(self):
        if self.alive():
            try:
                self.proc.stdin.write(json.dumps({"id": 0, "method": "shutdown"}) + "\n")
                self.proc.stdin.flush()
                self.proc.wait(5)
            except Exception:
                self.proc.kill()
        self.proc = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


_SHARED = None


def shared():
    global _SHARED
    if _SHARED is None:
        _SHARED = Engine()
    return _SHARED
