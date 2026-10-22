"""Round runner v2 shim:  venv_cad python scripts/round.py replica/L3 --spec fast_specs/L3_gate_spec.json
(see cadkit/fast/round.py)."""
import os
import runpy
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
os.environ["PYTHONPATH"] = CAD + os.pathsep + os.environ.get("PYTHONPATH", "")
runpy.run_module("cadkit.fast.round", run_name="__main__")
