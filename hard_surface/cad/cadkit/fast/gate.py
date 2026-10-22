"""Composite quality gate (COURSE_CORRECTION.md): every check must pass before a blind Opus judge is asked.

    python -m cadkit.fast.gate <round_dir> <gate_spec.json> [--prev <prev_round_dir>]
-> <round_dir>/gate.json  (+ overlay_<view>.png, judge_packet.png + judge_prompt.txt when auto gates pass)

gate_spec.json (paths relative to the spec file's directory or to hard_surface/cad):
{
 "views": [ {"name": "side", "u": "+x", "v": "+z", "mask": "refs/L3/side_mask.png", "min_iou": 0.90,
             "register": "anchor", "px_per_mm": 7.21, "origin_px": [1521, 259]},           # ref grid known
            {"name": "top", "u": "+y", "v": "-x", "mask": "...", "register": "bbox", "px_per_mm": 4} ],  # scale to width
 "features": [...],            # see build.check_features (evaluated in the build worker -> features.json)
 "main_surfaces": ["housing"], "min_g1_frac": 0.95, "min_g2_frac": 0.0,
 "max_manifold": 0, "allow_fillet_shrink": false,
 "judge": {"ref_images": ["refs/L3/DCD777C2_1.png"], "views": ["left"], "min_score": 7}
}
Checks: iou[view] >= min_iou; every feature pass; no fillet/chamfer reduced/split/failed (shrink = fail);
boolean manifold fallbacks <= max_manifold and all bodies valid; continuity g1/g2 fractions on main surfaces.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

CAD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHRINK = ("reduced", "split", "split_partial", "cap_failed", "failed", "cap_round")


def _p(spec_dir, p):
    for b in (spec_dir, CAD):
        q = os.path.join(b, p)
        if os.path.exists(q):
            return q
    return p


def _overlay(model, ref):
    rgb = np.full(model.shape + (3,), 255, np.uint8)
    rgb[ref & ~model] = (220, 60, 60)     # red  = ref only (missing material)
    rgb[model & ~ref] = (60, 110, 230)    # blue = model only (extra material)
    rgb[model & ref] = (150, 150, 150)
    return Image.fromarray(rgb)


def iou_views(scene, views, spec_dir, rd):
    out, ims = {}, []
    for v in views:
        ref = np.asarray(Image.open(_p(spec_dir, v["mask"])).convert("L")) > 127
        if v.get("register", "anchor") == "anchor":
            mod = scene.silhouette(v["u"], v["v"], v["px_per_mm"], v["origin_px"], (ref.shape[1], ref.shape[0]))
        else:   # bbox: scale ref to the model's projected width, bottom-aligned (ref masks are bbox-cropped)
            m, _ = scene.silhouette_bbox(v["u"], v["v"], v.get("px_per_mm", 4.0))
            r = Image.fromarray(ref.astype(np.uint8) * 255)
            s = m.shape[1] / r.size[0]
            r = np.asarray(r.resize((m.shape[1], max(1, int(round(r.size[1] * s)))), Image.NEAREST)) > 127
            H = max(r.shape[0], m.shape[0])
            a = np.zeros((H, m.shape[1]), bool)
            b = a.copy()
            a[H - m.shape[0]:] = m
            b[H - r.shape[0]:] = r
            mod, ref = a, b
        I, U = (mod & ref).sum(), (mod | ref).sum()
        iou = float(I / max(U, 1))
        ov = _overlay(mod, ref)
        ov.save(os.path.join(rd, f"overlay_{v['name']}.png"))
        ims.append((f"IoU {v['name']} {iou:.3f}", ov))
        out[v["name"]] = {"iou": round(iou, 4), "min": v.get("min_iou", 0.9), "pass": iou >= v.get("min_iou", 0.9),
                          "missing_frac": round(float((ref & ~mod).sum() / max(ref.sum(), 1)), 4),
                          "extra_frac": round(float((mod & ~ref).sum() / max(ref.sum(), 1)), 4)}
    return out, ims


def run(rd, spec_path, prev=None, scene=None):
    from cadkit.fast.render import Scene
    spec = json.load(open(spec_path))
    sd = os.path.dirname(os.path.abspath(spec_path))
    st = json.load(open(os.path.join(rd, "state.json")))
    g = {"round_dir": rd, "ok_build": bool(st.get("ok")), "checks": {}, "fail": []}
    if not st.get("ok"):
        g["fail"].append("build: " + str(st.get("error"))[:300])
        g["pass_auto"] = False
        json.dump(g, open(os.path.join(rd, "gate.json"), "w"), indent=1)
        return g, []
    scene = scene or Scene(os.path.join(rd, "mesh.npz"))
    ims = []
    # 1 IoU per ortho view
    if spec.get("views"):
        g["checks"]["iou"], ims = iou_views(scene, spec["views"], sd, rd)
        g["fail"] += [f"iou {k} {v['iou']} < {v['min']}" for k, v in g["checks"]["iou"].items() if not v["pass"]]
    # 2 named features
    fp = os.path.join(rd, "features.json")
    if os.path.exists(fp):
        fe = json.load(open(fp))
        g["checks"]["features"] = {"n": len(fe), "pass": sum(f["pass"] for f in fe), "items": fe}
        g["fail"] += [f"feature {f['name']}: " + (f.get("error") or json.dumps(f.get("err"))) for f in fe
                      if not f["pass"]]
    # 3 fillets at requested radius
    ops = st.get("ops", [])
    fl = [o for o in ops if o.get("op") in ("fillet", "chamfer")]
    bad = [o for o in fl if o.get("status") in SHRINK]
    g["checks"]["fillets"] = {"n": len(fl), "shrunk_or_failed": len(bad),
                              "items": [{"label": o.get("label"), "status": o.get("status"), "asked": o.get("radius"),
                                         "applied": o.get("applied")} for o in bad][:12]}
    if bad and not spec.get("allow_fillet_shrink"):
        g["fail"] += [f"fillet '{o.get('label')}' {o.get('status')} asked {o.get('radius')} got {o.get('applied')}"
                      for o in bad]
    # 4 B-rep validity + no mesh fallbacks
    man = [o for o in ops if o.get("op") == "boolean" and o.get("status") == "manifold"]
    invalid = [k for k, b in st.get("bodies", {}).items() if not b.get("valid")]
    g["checks"]["brep"] = {"manifold_fallbacks": len(man), "invalid_bodies": invalid,
                           "boolean_failed": sum(1 for o in ops if o.get("op") == "boolean" and o.get("status") == "failed")}
    if len(man) > spec.get("max_manifold", 0):
        g["fail"] += [f"manifold fallback '{o.get('label')}'" for o in man]
    if invalid:
        g["fail"].append(f"invalid B-rep: {invalid}")
    # 5 continuity (zebra metric) on main surfaces
    cp = os.path.join(rd, "continuity.json")
    if os.path.exists(cp):
        co = json.load(open(cp))
        g["checks"]["continuity"] = co
        for k, c in co.items():
            if c["g1_frac"] < spec.get("min_g1_frac", 0.95):
                g["fail"].append(f"G1 {k}: {c['g1_ok']}/{c['smooth_edges']} smooth edges tangent (max "
                                 f"{c['max_g1_deg']} deg)")
            if c["g2_frac"] < spec.get("min_g2_frac", 0.0):
                g["fail"].append(f"G2 {k}: {c['g2_ok']}/{c['smooth_edges']} curvature-continuous")
    g["pass_auto"] = not g["fail"]
    # 6 blind judge only when the automatic gates pass
    j = spec.get("judge")
    if j:
        if g["pass_auto"]:
            refs = [Image.open(_p(sd, r)).convert("RGB") for r in j["ref_images"]]
            ours = [scene.view(v, "clay", 640) for v in j.get("views", ["iso"])]
            from cadkit.fast.render import compose
            compose([(f"A{i}", im) for i, im in enumerate(refs)] + [(f"B{i}", im) for i, im in enumerate(ours)],
                    os.path.join(rd, "judge_packet.png"), 640, cols=max(len(refs), len(ours)))
            open(os.path.join(rd, "judge_prompt.txt"), "w").write(
                "Blind side-by-side. Row A = photos of a real product, row B = a CAD model of it (clay). Score B 0-10 "
                "for how faithfully it replicates A (proportions, silhouette, every visible feature, surface "
                "quality). List the 5 biggest differences, most important first. Reply JSON {score, diffs}.")
            g["judge"] = {"status": "pending", "packet": os.path.join(rd, "judge_packet.png"),
                          "min_score": j.get("min_score", 7),
                          "how": "spawn ONE blind Opus lane on judge_packet.png + judge_prompt.txt (no titles, no "
                                 "round info); record with: python -m cadkit.fast.gate --record-judge <rd> <score>"}
        else:
            g["judge"] = {"status": "skipped", "why": "automatic gates failed"}
    if prev and os.path.exists(os.path.join(prev, "gate.json")):
        g["diff"] = diff(json.load(open(os.path.join(prev, "gate.json"))), g,
                         json.load(open(os.path.join(prev, "state.json"))), st)
    json.dump(g, open(os.path.join(rd, "gate.json"), "w"), indent=1, default=str)
    return g, ims


def diff(pg, g, ps, st):
    d = {}
    for k, v in g["checks"].get("iou", {}).items():
        if k in pg["checks"].get("iou", {}):
            d[f"iou_{k}"] = round(v["iou"] - pg["checks"]["iou"][k]["iou"], 4)
    pf = {f["name"]: f["pass"] for f in pg["checks"].get("features", {}).get("items", [])}
    cf = {f["name"]: f["pass"] for f in g["checks"].get("features", {}).get("items", [])}
    d["features_fixed"] = [k for k in cf if cf[k] and not pf.get(k, False)]
    d["features_broken"] = [k for k in cf if not cf[k] and pf.get(k, False)]
    d["fails_new"] = [f for f in g["fail"] if f not in pg["fail"]]
    d["fails_gone"] = [f for f in pg["fail"] if f not in g["fail"]]
    bd = {}
    for k, b in st.get("bodies", {}).items():
        o = ps.get("bodies", {}).get(k)
        if o is None:
            bd[k] = "new"
        elif abs(b["volume"] - o["volume"]) > 1e-9 * max(1, abs(o["volume"])) or b["faces"] != o["faces"]:
            bd[k] = {"dvol_pct": round(100 * (b["volume"] - o["volume"]) / max(abs(o["volume"]), 1e-12), 3),
                     "dfaces": b["faces"] - o["faces"]}
    bd.update({k: "removed" for k in ps.get("bodies", {}) if k not in st.get("bodies", {})})
    d["bodies_changed"] = bd
    return d


def record_judge(rd, score):
    p = os.path.join(rd, "gate.json")
    g = json.load(open(p))
    g.setdefault("judge", {})
    g["judge"].update(status="scored", score=float(score), pass_=float(score) >= g["judge"].get("min_score", 7))
    g["pass"] = g["pass_auto"] and g["judge"]["pass_"]
    json.dump(g, open(p, "w"), indent=1)
    return g


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "--record-judge":
        print(json.dumps(record_judge(a[1], a[2]), indent=1))
    else:
        prev = a[a.index("--prev") + 1] if "--prev" in a else None
        print(json.dumps(run(a[0], a[1], prev)[0], indent=1, default=str))
