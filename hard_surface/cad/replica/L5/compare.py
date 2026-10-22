"""Silhouette IoU + overlays + dimension table: model_hq.glb vs registered photo traces (refdata.py)."""
import json
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter

import refdata as R

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "refs", "L5")
MMPX = 4.0   # raster resolution mm/px
BOX = (-2500, 2500, -1300, 1300, -50, 1450)   # x, y, z ranges


def load(glb):
    sc = trimesh.load(glb, force="scene")
    parts = {}
    for node in sc.graph.nodes_geometry:
        T, gname = sc.graph[node]
        m = sc.geometry[gname].copy()
        m.apply_transform(T)
        parts.setdefault(node.rsplit("_", 1)[0], []).append(m)
    parts = {k: trimesh.util.concatenate(v) for k, v in parts.items()}
    allv = np.vstack([m.vertices for m in parts.values()])
    s = 1000.0 if np.ptp(allv[:, 0]) < 50 else 1.0          # metres -> mm
    # glTF is Y-up: convert back to model Z-up (x, y, z) = (x, -z, y)
    for k, m in parts.items():
        v = m.vertices * s
        m.vertices = np.c_[v[:, 0], -v[:, 2], v[:, 1]]
    return parts


def raster(mesh_list, ax_u, ax_v, ur, vr):
    w, h = int((ur[1] - ur[0]) / MMPX), int((vr[1] - vr[0]) / MMPX)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for m in mesh_list:
        V = m.vertices
        P = np.c_[(V[:, ax_u] - ur[0]) / MMPX, (vr[1] - V[:, ax_v]) / MMPX]
        for t in m.faces:
            d.polygon([tuple(P[i]) for i in t], fill=255)
    return np.array(im) > 0


def poly_mask(polys, circles, ur, vr):
    w, h = int((ur[1] - ur[0]) / MMPX), int((vr[1] - vr[0]) / MMPX)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    f = lambda u, v: ((u - ur[0]) / MMPX, (vr[1] - v) / MMPX)  # noqa: E731
    for p in polys:
        d.polygon([f(u, v) for u, v in p], fill=255)
    for (u, v, r) in circles:
        a, b = f(u - r, v + r), f(u + r, v - r)
        d.ellipse([a, b], fill=255)
    return np.array(im) > 0


def iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))


def overlay(photo, mask, ur, vr, mm2px, ref_px_polys, out_png, crop=None):
    im = Image.open(os.path.join(REFS, photo)).convert("RGB")
    edge = Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.FIND_EDGES)
    E = np.argwhere(np.array(edge) > 0)
    d = ImageDraw.Draw(im)
    for p in ref_px_polys:
        d.line(p + [p[0]], fill=(40, 220, 60), width=3)
    for (r_, c_) in E[:: 1]:
        u, v = ur[0] + c_ * MMPX, vr[1] - r_ * MMPX
        px, py = mm2px(u, v)
        d.point((float(px), float(py)), fill=(255, 30, 30))
    im2 = im.filter(ImageFilter.MaxFilter(1))
    if crop:
        im2 = im2.crop(crop)
    im2.save(out_png)
    return out_png


def run(glb, out):
    parts = load(glb)
    body = [m for k, m in parts.items() if not k.startswith(("tyre", "rim", "disc", "caliper"))]
    car = list(parts.values())
    res = {}
    # ---------------- SIDE (view from +Y = car's right side, as photographed; image u = -X so front is right)
    ur, vr = (-2500, 2500), (-50, 1450)
    neg = [trimesh.Trimesh(np.c_[-m.vertices[:, 0], m.vertices[:, 1], m.vertices[:, 2]], m.faces) for m in car]
    ms = raster(neg, 0, 2, ur, vr)
    side = [(-x, z) for x, z in R.side_poly_mm(R.SIDE_OUTLINE_PX)]
    circ = []
    for (cx, cy, r) in R.SIDE_WHEELS_PX:
        x, z = R.side_px2mm(cx, cy)
        circ.append((-x, z, r * R.S_ZS))
    rs = poly_mask([side], circ, ur, vr)
    res["iou_side"] = iou(ms, rs)

    def s_mm2px(u, v):
        px, py = R.side_mm2px(-u, v)
        return float(px), float(py)
    overlay("Porsche_992_Carrera_S.jpg.jpg", ms, ur, vr, s_mm2px, [R.SIDE_OUTLINE_PX], os.path.join(out, "ov_side.png"),
            crop=(0, 380, 1920, 1040))
    # ---------------- FRONT (view from -X: image u = +Y? camera looking +X: car's left (-Y) appears on image right)
    ur2, vr2 = (-1300, 1300), (-50, 1450)
    mf = raster([trimesh.Trimesh(np.c_[-m.vertices[:, 1], m.vertices[:, 0], m.vertices[:, 2]], m.faces) for m in car],
                0, 2, ur2, vr2)
    half = [R.front_px2mm(*p) for p in R.FRONT_HALF_PX]
    fpoly = half + [(-u, v) for u, v in reversed(half)]
    mir = [R.front_px2mm(*p) for p in R.FRONT_MIRROR_PX]
    rf = poly_mask([fpoly, mir, [(-u, v) for u, v in mir]], [], ur2, vr2)
    res["iou_front"] = iou(mf, rf)
    fpx = [p for p in R.FRONT_HALF_PX] + [(2 * R.F_CX - x, y) for x, y in reversed(R.FRONT_HALF_PX)]
    overlay("Porsche_992_911_Carrera_S_White_9.jpg.jpg", mf, ur2, vr2,
            lambda u, v: (R.F_CX + u / R.F_SY, R.F_GROUND - v / R.F_SZ), [fpx], os.path.join(out, "ov_front.png"),
            crop=(150, 200, 1800, 1300))
    # ---------------- REAR (view from +X: car's right (+Y) appears on image right)
    mr = raster([trimesh.Trimesh(np.c_[m.vertices[:, 1], m.vertices[:, 0], m.vertices[:, 2]], m.faces) for m in car],
                0, 2, ur2, vr2)
    half = [R.rear_px2mm(*p) for p in R.REAR_HALF_PX]
    rpoly = half + [(-u, v) for u, v in reversed(half)]
    mir = [R.rear_px2mm(*p) for p in R.REAR_MIRROR_PX]
    rr = poly_mask([rpoly, mir, [(-u, v) for u, v in mir]], [], ur2, vr2)
    res["iou_rear"] = iou(mr, rr)
    rpx = [p for p in R.REAR_HALF_PX] + [(2 * R.R_CX - x, y) for x, y in reversed(R.REAR_HALF_PX)]
    overlay("Porsche_992_911_Carrera_S_White_16.jpg.jpg", mr, ur2, vr2,
            lambda u, v: (R.R_CX + u / R.R_SY, R.R_GROUND - v / R.R_SZ), [rpx], os.path.join(out, "ov_rear.png"),
            crop=(380, 330, 1720, 1150))
    # ---------------- dimensions
    bv = np.vstack([m.vertices for k, m in parts.items() if k == "body"])
    av = np.vstack([m.vertices for m in car])
    tyres = {k: m.vertices for k, m in parts.items() if k.startswith("tyre")}
    cen = sorted([(float(v[:, 0].mean()), float((v[:, 1].min() + v[:, 1].max()) / 2), float(v[:, 2].max())) for v in tyres.values()])
    xf = np.mean([c[0] for c in cen[:2]])
    xr = np.mean([c[0] for c in cen[2:]])
    dims = {
        "L": (float(np.ptp(bv[:, 0])), R.L), "W_body": (float(np.ptp(bv[:, 1])), R.W),
        "H": (float(av[:, 2].max() - av[:, 2].min()), R.H), "WB": (float(xr - xf), R.WB),
        "track_F": (abs(cen[0][1] - cen[1][1]), R.TRACK_F), "track_R": (abs(cen[2][1] - cen[3][1]), R.TRACK_R),
        "ovh_F": (float(xf - bv[:, 0].min()), R.OVH_F), "ovh_R": (float(bv[:, 0].max() - xr), R.OVH_R),
        "tyre_D_F": (cen[0][2], 2 * R.R_TF), "tyre_D_R": (cen[2][2], 2 * R.R_TR),
    }
    res["dims"] = {k: {"model": round(a, 1), "ref": round(b, 1), "err": round(a - b, 1)} for k, (a, b) in dims.items()}
    # side top-profile error (centreline roofline, rear->front): max |dz| at traced x
    Zs = []
    cols = np.where(ms.any(0))[0]
    for (px, py) in R.SIDE_TOP_PX:
        x, z = R.side_px2mm(px, py)
        c = int((-x - ur[0]) / MMPX)
        col = ms[:, c] if 0 <= c < ms.shape[1] else None
        if col is not None and col.any():
            zm = vr[1] - np.argmax(col) * MMPX
            Zs.append((round(x), round(zm - z)))
    res["top_profile_dz"] = Zs
    res["top_profile_max_abs"] = max(abs(d) for _, d in Zs) if Zs else None
    # combined debug sheet: model mask vs ref mask (green ref only, red model only, white both)
    for name, a, b in [("side", ms, rs), ("front", mf, rf), ("rear", mr, rr)]:
        rgb = np.zeros(a.shape + (3,), "uint8")
        rgb[a & b] = (230, 230, 230)
        rgb[a & ~b] = (230, 40, 40)
        rgb[~a & b] = (40, 200, 60)
        Image.fromarray(rgb).save(os.path.join(out, f"mask_{name}.png"))
    json.dump(res, open(os.path.join(out, "compare.json"), "w"), indent=1)
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}


if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=1))
