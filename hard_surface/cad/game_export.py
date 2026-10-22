"""CAD model -> game-ready asset.  python game_export.py ladder/L1/model.py [--name L1] [--res 2048] [--lod0 8000]
  [--lods 1,0.5,0.25] [--sharp 30] [--no-quad] [--stages tess,build,bake,final]
Outputs out/game/<name>/ (glb per LOD, fbx, maps, game.blend, report.json, preview_sheet.jpg) + game_previews/<name>_game.jpg."""
import argparse
import json
import os
import sys

CAD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CAD)
from cadkit.game.pipeline import run  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model"); ap.add_argument("--name"); ap.add_argument("--res", type=int, default=2048)
    ap.add_argument("--lod0", type=int); ap.add_argument("--lods", default="1,0.5,0.25")
    ap.add_argument("--sharp", type=float, default=30.0); ap.add_argument("--no-quad", action="store_true")
    ap.add_argument("--stages", default="tess,build,bake,final")
    a = ap.parse_args()
    name = a.name or os.path.basename(os.path.dirname(os.path.abspath(a.model)))
    rep = run(a.model, os.path.join(CAD, "out", "game", name), name, a.res, tuple(float(x) for x in a.lods.split(",")),
              a.lod0, a.sharp, not a.no_quad, previews_dir=os.path.join(CAD, "game_previews"), stages=a.stages.split(","))
    b = rep.get("build", {})
    print(json.dumps({"name": name, "hi_tris": b.get("hi", {}).get("tris"),
                      "lods": {k: v["tris"] for k, v in b.get("lods", {}).items()},
                      "bake_s": rep.get("bake", {}).get("total_s"), "vram_mb": rep.get("vram_mb"),
                      "sheet": rep.get("preview_small")}))


if __name__ == "__main__":
    main()
