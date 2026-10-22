"""Crash isolation: a deliberately crashing op kills only the kernel worker; the caller gets a clear error,
the worker restarts and rebuilds the session from the on-disk journal."""
import json

import pytest


@pytest.fixture
def pool(tmp_path):
    from cadkit.tools.sandbox import KernelPool
    p = KernelPool(timeout=60, env={"CADKIT_DEBUG_OPS": "1"}, log_path=str(tmp_path / "w.log"))
    yield p
    p.kill()


@pytest.mark.parametrize("how", ["segv", "abort"])
def test_crashing_op_is_survived(pool, tmp_path, how):
    sd = str(tmp_path)
    r = lambda meth, **a: json.loads(pool.request(meth, a, sd))  # noqa: E731
    assert r("new", session="s")["ok"]
    assert r("run", session="s", op="box", params={"name": "b", "size": [1, 1, 1]})["ok"]
    pid0 = r("ping")["pid"]
    bad = r("run", session="s", op="debug_crash", params={"how": how})
    assert not bad["ok"] and bad["crashed"] and "crashed" in bad["error"] and bad["hint"]
    # worker restarted, state rebuilt by journal replay, crash op not journaled
    st = r("state", session="s")
    assert st["ok"] and st["objects"]["b"]["volume"] == pytest.approx(1) and st["nodes"] == 1
    assert r("ping")["pid"] != pid0 and pool.restarts == 1
    assert r("run", session="s", op="fillet", params={"body": "b", "edges": {"parallel": "z"}, "radius": 0.1})["ok"]


def test_hang_times_out(pool, tmp_path):
    sd = str(tmp_path)
    assert json.loads(pool.request("new", {"session": "h"}, sd))["ok"]
    bad = json.loads(pool.request("run", {"session": "h", "op": "debug_hang", "params": {}}, sd, timeout=5))
    assert bad["crashed"] and "timed out" in bad["error"]
    assert json.loads(pool.request("state", {"session": "h"}, sd))["ok"]
