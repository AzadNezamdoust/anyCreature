"""Crash isolation for the direct-modelling MCP tools.

Every call that can touch OCCT runs in ONE persistent kernel worker subprocess (`python -m cadkit.tools.sandbox`).
The parent (MCP server) never imports build123d for ops. JSON lines over the worker's stdin/stdout:
    -> {"id": n, "method": "run", "args": {...}, "sess_dir": "..."}      <- {"id": n, "result": "<json string>"}
The on-disk session journal (out/tools_sessions/<s>.json, written by the worker AFTER a successful op) is the
source of truth: if the worker segfaults / aborts / hangs, the parent restarts it and the next call rebuilds the
session by replaying the journal. The failed call returns {"ok": false, "crashed": true, "error", "hint"}.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time

CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class KernelPool:
    """One persistent worker, restart-on-crash. Thread-safe (calls serialised)."""

    def __init__(self, timeout=300.0, env=None, log_path=None):
        self.timeout, self.extra_env = timeout, dict(env or {})
        self.log_path = log_path or os.path.join(CAD, "out", "kernel_worker.log")
        self.proc, self.q, self.n, self.restarts = None, None, 0, 0
        self.lock = threading.Lock()

    def _start(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        env = dict(os.environ, PYTHONPATH=CAD + os.pathsep + os.environ.get("PYTHONPATH", ""), **self.extra_env)
        env.pop("CADKIT_INPROC", None)
        self._log = open(self.log_path, "a", buffering=1)
        self.proc = subprocess.Popen([sys.executable, "-u", "-m", "cadkit.tools.sandbox", "--serve"], cwd=CAD,
                                     env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._log,
                                     text=True, encoding="utf-8", bufsize=1)
        self.q = queue.Queue()
        p, q = self.proc, self.q

        def pump():
            for line in p.stdout:
                q.put(line)
            q.put(None)  # EOF = worker died
        threading.Thread(target=pump, daemon=True).start()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def kill(self):
        if self.proc is not None:
            try:
                self.proc.kill()
                self.proc.wait(5)
            except Exception:
                pass
        self.proc = None

    def request(self, method, args, sess_dir, timeout=None):
        with self.lock:
            if not self.alive():
                self._start()
            self.n += 1
            msg = json.dumps({"id": self.n, "method": method, "args": args, "sess_dir": sess_dir}, default=str)
            try:
                self.proc.stdin.write(msg + "\n")
                self.proc.stdin.flush()
            except OSError:
                return self._crash(method, args, "worker pipe broken")
            t_end = time.time() + (timeout or self.timeout)
            while True:
                try:
                    line = self.q.get(timeout=max(0.05, t_end - time.time()))
                except queue.Empty:
                    self.kill()
                    self.restarts += 1
                    return json.dumps({"ok": False, "crashed": True, "error": f"{method}: kernel worker timed out "
                                       f"after {timeout or self.timeout:.0f}s (killed, restarted)",
                                       "hint": "journal unchanged; simplify the op (fewer edges / smaller radius) "
                                               "or split it; state rebuilds by replay on the next call"})
                if line is None:
                    return self._crash(method, args, "")
                try:
                    rep = json.loads(line)
                except ValueError:
                    continue  # stray stdout noise
                if rep.get("id") == self.n:
                    return rep["result"]

    def _crash(self, method, args, why):
        code = self.proc.poll() if self.proc else None
        self.kill()
        self.restarts += 1
        op = args.get("op") or method
        return json.dumps({"ok": False, "crashed": True,
                           "error": f"{op}: OCCT kernel worker crashed (exit {code}{', ' + why if why else ''}); "
                                    f"server survived, worker restarted",
                           "hint": "journal unchanged (last good state is rebuilt by replay). The op hit a kernel "
                                   "bug: change its inputs (other radius / edge subset / profile), e.g. fillet loft "
                                   "end caps with radius below the cap size, or use the fallback ops "
                                   "(cap_round, shell strategy=..., blend_surface)."})


def serve():
    """Worker loop. Real stdout is kept private; fd 1 -> stderr so OCCT/printf noise can't corrupt the protocol."""
    real = os.dup(1)
    os.dup2(2, 1)
    out = os.fdopen(real, "w", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr
    sys.path.insert(0, CAD)
    if os.environ.get("CADKIT_DEBUG_OPS") == "1":
        _register_debug_ops()
    import mcp_tools
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("sess_dir"):
            mcp_tools.SESS_DIR = msg["sess_dir"]
        res = mcp_tools.inproc(msg["method"], msg.get("args") or {})
        out.write(json.dumps({"id": msg["id"], "result": res}) + "\n")
        out.flush()


def _register_debug_ops():
    from cadkit.tools.core import op

    @op("debug_crash", "test only: hard native crash (null pointer read) to prove crash isolation", out=False)
    def debug_crash(m, how="segv"):
        if how == "abort":
            os.abort()
        import faulthandler
        faulthandler._sigsegv()  # real native SIGSEGV / access violation (ctypes would turn it into OSError)

    @op("debug_hang", "test only: never returns", out=False)
    def debug_hang(m, s=3600):
        time.sleep(s)


if __name__ == "__main__" and "--serve" in sys.argv:
    serve()
