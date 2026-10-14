"""Classic low-poly methods: decimate | instant | quadriflow.

  E:/gen3d/venv_lp/Scripts/python run_classic.py <method> [--in-root E:/gen3d/r8]
        [--out-root E:/gen3d/lowpoly] [--animals wolf,horse] [--budgets 1500,5000]

Output: <out-root>/<method>/<animal>_<budget>.obj (normalized y-up, ground y=0,
height 1) + results line appended to <out-root>/<method>/log.jsonl.
Budget = polygon count (quads count as 1 face)."""
import argparse, json, os, subprocess, sys, time, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp_common as C

HERE = os.path.dirname(os.path.abspath(__file__))
IM_EXE = os.path.join(HERE, 'bin', 'instant-meshes', 'Instant Meshes.exe')
QF_EXE = os.path.join(HERE, 'bin', 'quadriflow', 'quadriflow.exe')


SOLID = 0   # set by --solid N: watertight SDF+marching-cubes rebuild at N^3


def solidify(V, F, res):
    """Thin open sheets (wings, ear flaps, fins, toes) wreck field-aligned
    remeshers; rebuild a closed manifold shell at res^3 via mesh2sdf (fix=True
    = winding/flood-fill sign, gives a thin solid around open sheets)."""
    import mesh2sdf
    from skimage import measure
    c = (V.max(0) + V.min(0)) / 2; s = (V.max(0) - V.min(0)).max() / 2 / 0.9
    Vn = (V - c) / s
    sdf = mesh2sdf.compute(Vn.astype(np.float32), F.astype(np.int64), res,
                           fix=True, level=1.5 / res)
    v, f, _, _ = measure.marching_cubes(sdf, 0)
    v = v / (res - 1) * 2 - 1
    return v * s + c, f[:, ::-1].copy()


def prep_input(src, tmpdir, target_tris=200000):
    """Normalize, optional watertight rebuild, cleanup, light pre-decimate."""
    import pymeshlab as ml
    m = C.load_tri(src)
    V, F = C.normalize(m.vertices), np.asarray(m.faces)
    if SOLID:
        V, F = solidify(V, F, SOLID)
    ms = ml.MeshSet()
    ms.add_mesh(ml.Mesh(V, F))
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_remove_unreferenced_vertices()
    ms.meshing_remove_connected_component_by_diameter(
        mincomponentdiag=ml.PercentageValue(5))
    if ms.current_mesh().face_number() > target_tris:
        ms.meshing_decimation_quadric_edge_collapse(
            targetfacenum=target_tris, preservenormal=True)
    p = os.path.join(tmpdir, 'in.obj')
    ms.save_current_mesh(p, save_vertex_normal=False)
    return p, ms


def decimate(src, budget, out, tmp):
    import pymeshlab as ml
    p, ms = prep_input(src, tmp)
    ms.meshing_decimation_quadric_edge_collapse(
        targetfacenum=budget, preservenormal=True, preserveboundary=True,
        optimalplacement=True, planarquadric=True, qualitythr=0.3)
    m = ms.current_mesh()
    C.write_obj_polys(out, m.vertex_matrix(), m.face_matrix().tolist())


def instant(src, budget, out, tmp):
    p, _ = prep_input(src, tmp)
    # pure-quad output (no -D); -f is target face count of the final mesh
    # Pure-quad mode subdivides the dominant mesh (~4x faces), so -f is not
    # the final count: start at budget/4 and correct proportionally twice.
    # Occasionally hangs (frog@1500): 60 s timeout, retry nudged and non-det.
    f = budget / 4
    det = ['-d']
    for _ in range(5):
        cmd = [IM_EXE, p, '-o', out, '-f', str(int(f)), '-r', '4', '-p', '4',
               '-b', '-S', '2'] + det
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            f *= 1.03; det = []
            continue
        got = len(C.read_obj_polys(out)[1])
        if abs(got - budget) < 0.08 * budget:
            break
        f *= budget / got


def quadriflow(src, budget, out, tmp):
    # PyPI pyquadriflow (ctypes wrapper bundling a QuadriFlow DLL; the official
    # repo ships no Windows binary). -sharp off: noisy gen meshes -> spiky flow.
    from pyQuadriFlow.pyQuadriFlow import pyquadriflow
    _, ms = prep_input(src, tmp, target_tris=60000)
    m = ms.current_mesh()
    Vl, Fl = m.vertex_matrix().tolist(), m.face_matrix().tolist()
    # undershoots on thin shapes -> proportional correction; on internal
    # failure retry with another seed.
    f, best, err = budget, None, None
    for seed in range(6):
        try:
            r = pyquadriflow(int(f), seed, Vl, Fl, False, False, False, True, False)
        except Exception as e:
            err = e; continue
        got = len(r['faces'])
        if best is None or abs(got - budget) < abs(len(best['faces']) - budget):
            best = r
        if abs(got - budget) < 0.08 * budget:
            break
        f *= budget / got
    if best is None:
        raise err
    C.write_obj_polys(out, np.array(best['vertices']), best['faces'])


METHODS = dict(decimate=decimate, instant=instant, quadriflow=quadriflow)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('method', choices=list(METHODS))
    ap.add_argument('--in-root', default='E:/gen3d/r8')
    ap.add_argument('--out-root', default='E:/gen3d/lowpoly')
    ap.add_argument('--animals', default=','.join(C.ANIMALS))
    ap.add_argument('--budgets', default='1500,5000')
    ap.add_argument('--solid', type=int, default=0,
                    help='watertight SDF rebuild resolution before remeshing (e.g. 256); 0=off')
    ap.add_argument('--tag', default=None, help='output subdir (default = method)')
    a = ap.parse_args()
    global SOLID
    SOLID = a.solid
    od = os.path.join(a.out_root, a.tag or a.method)
    os.makedirs(od, exist_ok=True)
    for an in a.animals.split(','):
        src = os.path.join(a.in_root, an, 'final.obj')
        for b in map(int, a.budgets.split(',')):
            out = os.path.join(od, f'{an}_{b}.obj')
            t0 = time.time()
            rec = dict(animal=an, budget=b, method=a.method)
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    METHODS[a.method](src, b, out, tmp)
                V, P = C.read_obj_polys(out)
                V = C.normalize(V)            # re-ground after remesh
                C.write_obj_polys(out, V, P)
                rec.update(C.stats(P), ok=True)
            except Exception as e:
                rec.update(ok=False, err=repr(e)[:300])
            rec['sec'] = round(time.time() - t0, 1)
            print(json.dumps(rec), flush=True)
            with open(os.path.join(od, 'log.jsonl'), 'a') as f:
                f.write(json.dumps(rec) + '\n')


if __name__ == '__main__':
    main()
