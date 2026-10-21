import pytest


def test_delete_face_heals_boss(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("cylinder", name="c", radius=0.1, height=0.4, at=[0, 0, 0.6])
    m.run("boolean", kind="union", target="b", tools=["c"])
    m.run("delete_face", body="b", faces={"within": [[-0.2, -0.2, 0.5001], [0.2, 0.2, 1]]})
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1, rel=1e-6)


def test_remove_fillets_and_refillet(m):
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    m.run("remove_fillets", body="b", max_radius=0.15)
    assert m.state()["objects"]["b"]["volume"] == pytest.approx(1, rel=1e-6)
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    v1 = m.state()["objects"]["b"]["volume"]
    m.run("refillet", body="b", radius=0.2, max_radius=0.15)
    assert m.state()["objects"]["b"]["volume"] < v1 and m.state()["objects"]["b"]["faces"] == 10


def test_edit_then_refillet(m):
    """spec 2.5: push/pull a filleted body, then re-apply the blends."""
    m.run("box", name="b", size=[1, 1, 1])
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    m.run("remove_fillets", body="b", max_radius=0.15)
    m.run("offset_face", body="b", faces={"normal": "+x"}, distance=0.3)
    m.run("fillet", body="b", edges={"parallel": "z"}, radius=0.1)
    st = m.state()["objects"]["b"]
    assert st["valid"] and st["faces"] == 10 and st["bbox"][1][0] == pytest.approx(0.8)
