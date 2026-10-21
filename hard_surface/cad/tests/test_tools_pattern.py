import pytest


def test_mirror_union_and_copy(m):
    m.run("box", name="b", size=[1, 1, 1], at=[1, 0, 0])
    m.run("mirror", body="b", plane="YZ")
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(2, rel=1e-6)
    m.run("box", name="c", size=[1, 1, 1], at=[0, 3, 0])
    m.run("mirror", name="c_m", body="c", plane="XZ", union=False)
    assert m.state()["objects"]["c_m"]["bbox"][1][1] == pytest.approx(-2.5)


def test_linear_radial_arrays(m):
    m.run("box", name="b", size=[0.1, 0.1, 0.1])
    m.run("linear_array", name="la", body="b", count=4, step=[0.2, 0, 0], count2=2, step2=[0, 0.2, 0])
    assert m.state()["objects"]["la"]["volume"] == pytest.approx(8e-3, rel=1e-6)
    m.run("cylinder", name="bolt", radius=0.05, height=0.1, at=[1, 0, 0])
    m.run("radial_array", name="ra", body="bolt", count=6)
    bb = m.state()["objects"]["ra"]["bbox"]
    assert bb[0][0] == pytest.approx(-1.05, abs=1e-3)


def test_union_array(m):
    m.run("box", name="b", size=[0.1, 0.1, 0.1])
    m.run("linear_array", name="la", body="b", count=3, step=[0.05, 0, 0], union=True)
    assert m.state()["objects"]["la"]["volume"] == pytest.approx(0.2 * 0.01, rel=1e-6)


def test_instances_follow_source(m):
    m.run("box", name="src", size=[1, 1, 1])
    m.run("instance", name="i1", source="src", move=[3, 0, 0])
    m.run("fillet", body="src", edges={"parallel": "z"}, radius=0.2)
    assert m.state()["objects"]["i1"]["volume"] == pytest.approx(m.state()["objects"]["src"]["volume"])
    m.run("realize", name="i1")
    m.run("scale", obj="src", factor=2)
    assert m.state()["objects"]["i1"]["volume"] < m.state()["objects"]["src"]["volume"]


def test_transforms(m):
    m.run("box", name="b", size=[2, 1, 1])
    m.run("move", obj="b", by=[1, 0, 0])
    m.run("rotate", obj="b", axis_dir="z", angle=90)
    bb = m.state()["objects"]["b"]["bbox"]
    assert bb[1][1] - bb[0][1] == pytest.approx(2)
    m.run("duplicate", name="d", source="b")
    m.run("delete", obj="b")
    assert list(m.objects) == ["d"]
