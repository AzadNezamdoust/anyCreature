"""model_server.py - persistent local GPU stage server for run_inbox.py (--server). Run with the venv python.

    E:/gen3d/venv/Scripts/python.exe model_server.py [--port 8765] [--lowvram]
    python run_inbox.py wolf --seeds 0,1,2 --lowvram --server        # GPU stages go to the server

Same stage scripts as subprocess mode (run_inbox templates them identically, plus `_cached(...)` wrappers around
the model constructors). The server runs each script with runpy in-process, so torch/CUDA init, imports and model
weights (Hunyuan3D-2.1 shape, 2mv, Paint 2.1, HunyuanDiT T2I) are paid once per server lifetime, not per stage.
--lowvram: shape/2mv keep the accelerate CPU-offload chain (weights live in host RAM, swapped to GPU per module),
paint keeps its staged UNet/VAE/DINO offload; after every job the server offloads any chained hooks and empties the
CUDA cache, so stages swap on an 8 GB card while weights stay resident in host RAM.
Start the server with the same env the client would use (VRAM_CAP / TURING / PYTORCH_CUDA_ALLOC_CONF are read at
CUDA init): --lowvram sets PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True.

HTTP (127.0.0.1 only): POST /run {script, argv, cwd, env, log} -> {rc, dt}; GET /stats; POST /drop (free cache).
Jobs run serially. Monkeypatches a script registers via _cleanup(fn) are undone after the job.
"""
import argparse, builtins, contextlib, gc, io, json, os, runpy, sys, time, traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

builtins._MODEL_CACHE = {}
builtins._JOB_CLEANUP = []
STATS = dict(jobs=0, started=time.time(), hits=0, misses=0)


def post_job():
    import torch
    for f in builtins._JOB_CLEANUP[::-1]:
        try: f()
        except Exception: traceback.print_exc()
    builtins._JOB_CLEANUP.clear()
    for o in builtins._MODEL_CACHE.values():
        h = getattr(o, '_last_hook', None)
        if h is not None:
            try: h.offload()
            except Exception: pass
    gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()


def run_job(j):
    import torch
    old_env = dict(os.environ); old_argv = sys.argv[:]; old_cwd = os.getcwd(); old_path = sys.path[:]
    os.environ.update(j.get('env') or {})
    rc = 0; t = time.time()
    with open(j['log'], 'w', encoding='utf-8', errors='replace', buffering=1) as lf:
        with contextlib.redirect_stdout(lf), contextlib.redirect_stderr(lf):
            try:
                os.chdir(j.get('cwd') or old_cwd)
                sys.argv = [j['script']] + list(j.get('argv') or [])
                if torch.cuda.is_available(): torch.cuda.reset_peak_memory_stats()
                h0, m0 = STATS['hits'], STATS['misses']
                g = runpy.run_path(j['script'], run_name='__main__')
                if '_peak' in g: g['_peak']('exit')
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
                print('SystemExit', e.code, flush=True)
            except BaseException:
                traceback.print_exc(); rc = 1
            finally:
                try: post_job()
                except Exception: traceback.print_exc()
                print(f'SERVER job {time.time() - t:.1f}s cache {list(builtins._MODEL_CACHE)}', flush=True)
    os.chdir(old_cwd); sys.argv = old_argv; sys.path[:] = old_path
    os.environ.clear(); os.environ.update(old_env)
    STATS['jobs'] += 1
    return dict(rc=rc, dt=round(time.time() - t, 1))


class H(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == '/stats':
            self._send(dict(STATS, cache=list(builtins._MODEL_CACHE), uptime=round(time.time() - STATS['started'])))
        else: self._send({'ok': True})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); j = json.loads(self.rfile.read(n) or b'{}')
        if self.path == '/run': self._send(run_job(j))
        elif self.path == '/drop':
            builtins._MODEL_CACHE.clear(); post_job(); self._send({'dropped': True})
        else: self._send({'err': 'unknown'}, 404)

    def log_message(self, *a): pass


def _cached(key, fn):   # also injected by run_inbox CAP_PREFIX; this copy counts hits for /stats
    c = builtins._MODEL_CACHE
    if key in c: STATS['hits'] += 1; print('CACHE hit', key, flush=True); return c[key]
    STATS['misses'] += 1; t = time.time(); c[key] = fn(); print(f'CACHE miss {key} built in {time.time() - t:.1f}s', flush=True)
    return c[key]


builtins._cached_impl = _cached

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8765); ap.add_argument('--lowvram', action='store_true')
    a = ap.parse_args()
    if a.lowvram: os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    import torch  # CUDA init once
    print(f'model_server on 127.0.0.1:{a.port} cuda={torch.cuda.is_available()}', flush=True)
    HTTPServer(('127.0.0.1', a.port), H).serve_forever()
