import os

import pytest

from cadkit.tools import export_file, write_run

BLENDER = r"E:\gen3d\blender\blender-5.2.2-windows-x64\blender.exe"


@pytest.mark.parametrize("ext", ["step", "glb", "gltf", "obj", "stl"])
def test_export(m, tmp_path, ext):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    p = export_file(m, str(tmp_path / f"x.{ext}"))
    assert os.path.getsize(p) > 200


def test_write_run(m, tmp_path):
    m.run("box", name="b", size=[1, 1, 1])
    st = write_run(m, str(tmp_path / "run"), tris=500, hq=False)
    assert st["tris"] <= 500 and os.path.exists(tmp_path / "run" / "mesh.npz")


@pytest.mark.skipif(not os.path.exists(BLENDER), reason="no blender")
def test_game_mesh_blender(m, tmp_path):
    from cadkit.tools import game_mesh
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    rep = game_mesh(m, str(tmp_path / "gm"), tris=800)
    assert os.path.exists(tmp_path / "gm" / "model.glb") and rep["tris"] > 0
