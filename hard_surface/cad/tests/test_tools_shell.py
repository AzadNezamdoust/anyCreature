import pytest


def test_shell_open_top(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("shell", body="b", thickness=0.1, open_faces={"obj": "b", "faces": {"normal": "+z"}})
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1 - 0.8 * 0.8 * 0.9, rel=1e-4)


def test_thicken(m):
    m.run("rectangle", name="r", width=1, height=1)
    m.run("regions", curves=["r"])
    m.run("thicken", name="t", face="region1", thickness=0.1)
    assert m.state()["objects"]["t"]["volume"] == pytest.approx(0.1, rel=1e-6)


@pytest.mark.parametrize("d", [0.2, -0.2])
def test_offset_face(m, d):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("offset_face", body="b", faces={"normal": "+x"}, distance=d)
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1 + d, rel=1e-6)
