"""STEP/IGES import as a journal op, editable by native ops, round-trip export, deviation vs reference."""
import os

import pytest
from build123d import Box, Cylinder, Pos, export_step, Unit


@pytest.fixture
def step_file(tmp_path):
    # mm part as another app would export it: 40x30x20 block with a 10 mm hole, plus a separate pin
    blk = Box(40, 30, 20) - Cylinder(5, 30)
    blk.label = "block"
    pin = Pos(60, 0, 0) * Cylinder(4, 20)
    pin.label = "pin"
    from build123d import Compound
    p = str(tmp_path / "ext.step")
    export_step(Compound(children=[blk, pin]), p, unit=Unit.MM)
    return p


def test_import_edit_roundtrip(m, step_file, tmp_path):
    info = m.run("import_step", name="imp", path=step_file)
    assert info["solids"] == 2 and set(info["objects"]) == {"imp_1", "imp_2"}
    blk = min(info["objects"], key=lambda n: -m.get(n).shape.volume)
    v0 = m.get(blk).shape.volume
    assert v0 == pytest.approx((0.04 * 0.03 * 0.02) - 3.14159265 * 0.005 ** 2 * 0.02, rel=1e-4)  # mm -> m
    assert f"{blk}/f0" in m.tags
    # native ops on imported geometry via semantic refs
    m.run("fillet", body=blk, edges={"parallel": "z"}, radius=0.002)
    m.run("push_pull", body=blk, faces={"normal": "+x"}, distance=0.005)
    m.run("box", name="cutter", size=[0.01, 0.01, 0.05])
    m.run("boolean", name="boolean1", kind="cut", target=blk, tools=["cutter"])
    m.run("split", body=blk, plane={"origin": [0, 0, 0], "normal": [0, 0, 1]}, keep="above")
    s = m.get(blk).shape
    assert s.is_valid and s.volume < v0
    # journal replay re-imports and re-applies (semantic refs re-resolved)
    m.run("tag", tag="top", ref={"obj": blk, "faces": {"normal": "+z"}})
    out = str(tmp_path / "rt.step")
    m.run("export_step", path=out, objects=[blk])
    from cadkit.tools import Model
    m2 = Model()
    i2 = m2.run("import_step", name="rt", path=out)
    assert m2.get(i2["name"]).shape.volume == pytest.approx(s.volume, rel=1e-6)


def test_units_and_iges(m, tmp_path):
    p = str(tmp_path / "b.step")
    export_step(Box(10, 10, 10), p, unit=Unit.MM)
    m.run("import_step", name="a", path=p, units="mm")
    assert m.get("a").shape.volume == pytest.approx(1000, rel=1e-6)
    from OCP.IGESControl import IGESControl_Writer
    w = IGESControl_Writer("MM", 1)
    w.AddShape(Box(10, 10, 10).wrapped)
    w.ComputeModel()
    pi = str(tmp_path / "b.igs")
    assert w.Write(pi)
    m.run("import_step", name="g", path=pi)
    sh = m.get("g").shape if "g" in m.objects else None
    assert sh is not None or any(k.startswith("g_sheet") for k in m.objects)


def test_native_formats_refused(m, tmp_path):
    from cadkit.tools import ToolError
    p = tmp_path / "x.plasticity"
    p.write_bytes(b"\0")
    with pytest.raises(ToolError, match="intentionally not parsed"):
        m.run("import_step", name="x", path=str(p))


def test_deviation_to_ref_heatmap(m, tmp_path):
    p = str(tmp_path / "ref.step")
    export_step(Box(40, 30, 20), p, unit=Unit.MM)
    m.run("import_step", name="ref", path=p)
    m.run("box", name="ours", size=[0.04, 0.03, 0.02])
    m.run("offset_face", body="ours", faces={"normal": "+z"}, distance=0.001)
    hm = str(tmp_path / "hm.png")
    r = m.run("deviation_to_ref", model="ours", ref="ref", samples=4000, heatmap=hm, tol=1e-4)
    assert r["hausdorff"] == pytest.approx(0.001, abs=1e-4) and os.path.exists(hm)
    top = max(r["per_face"], key=lambda f: f["centre"][2])  # moved face: whole face off by 1 mm
    assert top["mean"] == pytest.approx(0.001, abs=1e-4) and top["centre"][2] > 0.0104
    assert min(f["mean"] for f in r["per_face"]) < 0.0006
    assert r["over_tol"]


@pytest.mark.skipif(not os.environ.get("CADKIT_SAMPLE_STEP"), reason="set CADKIT_SAMPLE_STEP to a public sample")
def test_public_sample(m):
    info = m.run("import_step", name="s", path=os.environ["CADKIT_SAMPLE_STEP"])
    assert info["faces"] > 0
