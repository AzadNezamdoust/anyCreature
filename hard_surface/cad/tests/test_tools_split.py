import pytest


def test_split_plane_both_and_keep(m):
    m.run("box", name="b", size=[1, 1, 1])
    info = m.run("split", body="b", plane={"origin": [0, 0, 0.25], "normal": "z"})
    assert info["pieces"] == ["b_1", "b_2"]
    assert m.state()["objects"]["b_2"]["volume"] == pytest.approx(0.25, rel=1e-6)
    m.run("box", name="c", size=[1, 1, 1])
    m.run("split", body="c", plane="XY", keep="above")
    assert m.state()["objects"]["c"]["volume"] == pytest.approx(0.5, rel=1e-6)


def test_split_by_curve(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("line", name="l", points=[[-1, -0.2], [1, 0.3]])
    info = m.run("split", body="b", curve="l", cplane="XY")
    assert len(info["pieces"]) == 2


def test_imprint_keeps_volume(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("rectangle", name="p", width=0.5, height=0.3, plane={"origin": [0, 0, 1]})
    info = m.run("imprint", body="b", curves=["p"], direction="-z")
    assert info["faces"] == info["faces_before"] + 1
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1, rel=1e-9)
