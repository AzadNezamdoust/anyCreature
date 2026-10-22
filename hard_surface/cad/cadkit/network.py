"""Class-A-lite surfacing: Gordon network surface, edge continuity report (G0/G1/G2), zebra smoothness.

gordon_surface(u_curves, v_curves): the transfinite Gordon surface G = Lu + Lv - T through a curve network
(Lu = skin of the u-curves interpolated across v, Lv = skin of the v-curves across u, T = tensor interpolant of the
intersection points). GeomFill rejects real curve networks (different degrees/knots/directions), so the network
is NORMALISED here instead: curves oriented + sorted, every curve reparametrised (monotone PCHIP) so that its
intersections sit at common parameters, G evaluated on a dense grid, then fitted by ONE C2 B-spline
(GeomAPI_PointsToBSplineSurface, deg 3-5). A single C2 patch -> no internal seams, smooth zebra by construction.
Accuracy is reported (max distance of every network curve to the surface).
"""
from __future__ import annotations

import math

import numpy as np
from build123d import Edge, Face, Shape, Wire

from .ops import CadOpError


# ------------------------------------------------------------------ curve helpers (raw-parameter based)
class _C:
    def __init__(self, e):
        from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_CompCurve
        self.e = e
        if isinstance(e, Wire) and len(e.edges()) > 1:
            self.ad = BRepAdaptor_CompCurve(e.wrapped)
        else:
            e1 = e if isinstance(e, Edge) else e.edges()[0]
            self.ad = BRepAdaptor_Curve(e1.wrapped)
        self.u0, self.u1 = self.ad.FirstParameter(), self.ad.LastParameter()
        self.flip = False

    def __call__(self, t):  # t in 0..1 (array)
        t = np.atleast_1d(np.asarray(t, float))
        if self.flip:
            t = 1 - t
        out = np.empty((len(t), 3))
        for i, s in enumerate(t):
            p = self.ad.Value(self.u0 + (self.u1 - self.u0) * float(s))
            out[i] = (p.X(), p.Y(), p.Z())
        return out

    def param_of(self, p, n=400):
        ts = np.linspace(0, 1, n)
        P = self(ts)
        i = int(np.argmin(((P - p) ** 2).sum(1)))
        lo, hi = ts[max(i - 1, 0)], ts[min(i + 1, n - 1)]
        for _ in range(40):  # golden-ish refine
            a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
            if ((self(a)[0] - p) ** 2).sum() < ((self(b)[0] - p) ** 2).sum():
                hi = b
            else:
                lo = a
        t = (lo + hi) / 2
        return t, float(np.sqrt(((self(t)[0] - p) ** 2).sum()))


def _closest(ca, cb, n=300):
    A, B = ca(np.linspace(0, 1, n)), cb(np.linspace(0, 1, n))
    d = ((A[:, None, :] - B[None, :, :]) ** 2).sum(2)
    i, j = np.unravel_index(int(np.argmin(d)), d.shape)
    p = (A[i] + B[j]) / 2
    for _ in range(3):
        ta, _ = ca.param_of(p)
        tb, _ = cb.param_of(p)
        pa, pb = ca(ta)[0], cb(tb)[0]
        p = (pa + pb) / 2
    return ta, tb, float(np.linalg.norm(pa - pb)), p


def _remap(nodes_common, nodes_own):
    """Monotone map common param -> own param through (u_j, s_ij), pinned at 0 and 1."""
    from scipy.interpolate import PchipInterpolator
    x, y = np.asarray(nodes_common, float).copy(), np.asarray(nodes_own, float).copy()
    # curves usually START/END on the first/last crossing: snap those nodes to 0/1 instead of adding a near-duplicate
    # pin (a pin 1e-6 away made the spline map overshoot -> folded boundary row, zebra flip)
    if x[0] < 2e-2 and y[0] < 2e-2:
        x[0] = y[0] = 0.0
    else:
        x, y = np.concatenate([[0.0], x]), np.concatenate([[0.0], y])
    if x[-1] > 1 - 2e-2 and y[-1] > 1 - 2e-2:
        x[-1] = y[-1] = 1.0
    else:
        x, y = np.concatenate([x, [1.0]]), np.concatenate([y, [1.0]])
    y = np.maximum.accumulate(y)
    # C2 reparametrisation (a C1 PCHIP map makes the whole surface only C1 -> visible zebra wobble);
    # fall back to PCHIP only if the cubic would fold (non-monotone)
    from scipy.interpolate import CubicSpline
    if len(x) >= 3:
        cs = CubicSpline(x, y, bc_type="natural")
        if np.all(np.diff(cs(np.linspace(0, 1, 2001))) > 0):
            return cs
    return PchipInterpolator(x, y)


def _interp_across(nodes, vals, at):
    """vals[k] (k over nodes) arrays of shape (..., 3) -> value at params `at` (cubic, not-a-knot / quadratic)."""
    from scipy.interpolate import CubicSpline, interp1d
    nodes = np.asarray(nodes, float)
    if len(nodes) >= 4:
        f = CubicSpline(nodes, np.asarray(vals), axis=0, bc_type="not-a-knot", extrapolate=True)
    else:
        f = interp1d(nodes, np.asarray(vals), axis=0, kind="quadratic" if len(nodes) == 3 else "linear",
                     fill_value="extrapolate")
    return f(at)


# ------------------------------------------------------------------ Gordon
def gordon_surface(u_curves, v_curves, nu=60, nv=60, tol=None, degree=(3, 3), net_tol=None):
    """u_curves (>=2, e.g. sections) and v_curves (>=2, e.g. feature lines) that cross each other.
    Returns (Face, report{max_dev, per_curve, grid, degree}). Raises CadOpError if a pair does not meet."""
    U, V = [_C(c) for c in u_curves], [_C(c) for c in v_curves]
    if len(U) < 2 or len(V) < 2:
        raise CadOpError("gordon_surface needs >= 2 u-curves and >= 2 v-curves")
    allp = np.vstack([c(np.linspace(0, 1, 20)) for c in U + V])
    diag = float(np.linalg.norm(allp.max(0) - allp.min(0)))
    net_tol = net_tol or 2e-3 * diag
    tol = tol or 2e-5 * diag
    # intersections + orientation normalisation
    n, m = len(U), len(V)
    S, Tt, X = np.zeros((n, m)), np.zeros((n, m)), np.zeros((n, m, 3))
    for i in range(n):
        for j in range(m):
            S[i, j], Tt[i, j], d, X[i, j] = _closest(U[i], V[j])
            if d > net_tol:
                raise CadOpError(f"network curves u{i} and v{j} do not meet (gap {d:.4g} > {net_tol:.4g}); "
                                 f"every u-curve must cross every v-curve")
    # sort v-curves along u-curves and u-curves along v-curves (by mean param), orient so params increase
    oj = np.argsort(S.mean(0))
    V, S, Tt, X = [V[k] for k in oj], S[:, oj], Tt[:, oj], X[:, oj]
    for i in range(n):
        if S[i, 0] > S[i, -1]:
            U[i].flip = not U[i].flip
            S[i] = 1 - S[i]
    oi = np.argsort(Tt.mean(1))
    U, S, Tt, X = [U[k] for k in oi], S[oi], Tt[oi], X[oi]
    for j in range(m):
        if Tt[0, j] > Tt[-1, j]:
            V[j].flip = not V[j].flip
            Tt[:, j] = 1 - Tt[:, j]
    if np.any(np.diff(S, axis=1) <= 0) or np.any(np.diff(Tt, axis=0) <= 0):
        raise CadOpError("network is not a grid: intersection order differs between curves (crossing / folded "
                         "network). Check that feature lines do not cross each other.")
    uc, vc = S.mean(0), Tt.mean(1)  # common parameters of the v-curves (along u) and the u-curves (along v)
    gu, gv = np.linspace(0, 1, nu), np.linspace(0, 1, nv)
    Pu = np.stack([U[i](_remap(uc, S[i])(gu)) for i in range(n)])          # n x nu x 3
    Pv = np.stack([V[j](_remap(vc, Tt[:, j])(gv)) for j in range(m)])     # m x nv x 3
    Lu = _interp_across(vc, Pu, gv).transpose(1, 0, 2)                     # nu x nv x 3
    Lv = _interp_across(uc, Pv, gu)                                        # nu x nv x 3
    Tx = _interp_across(uc, _interp_across(vc, X, gv).transpose(1, 0, 2), gu)  # (nu, nv, 3)
    G = Lu + Lv - Tx
    face = fit_grid(G, tol, degree)
    rep = {"grid": [nu, nv], "u_curves": n, "v_curves": m, "diag": round(diag, 6)}
    devs = []
    for k, c in enumerate(U + V):
        P = c(np.linspace(0, 1, 40))
        devs.append(round(max(_dist_to_face(face, p) for p in P), 7))
    rep["per_curve_max_dev"] = devs
    rep["max_dev"] = max(devs)
    return face, rep


def fit_grid(G, tol, degree=(3, 5)):
    from OCP.GeomAPI import GeomAPI_PointsToBSplineSurface
    from OCP.GeomAbs import GeomAbs_C2
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.collections import Array2_gp_Pnt
    from OCP.gp import gp_Pnt
    nu, nv = G.shape[:2]
    arr = Array2_gp_Pnt(1, nu, 1, nv)
    for i in range(nu):
        for j in range(nv):
            arr.SetValue(i + 1, j + 1, gp_Pnt(*map(float, G[i, j])))
    fit = GeomAPI_PointsToBSplineSurface(arr, degree[0], degree[1], GeomAbs_C2, float(tol))
    if not fit.IsDone():
        raise CadOpError("B-spline fit of the network grid failed; raise tol or reduce grid")
    mk = BRepBuilderAPI_MakeFace(fit.Surface(), 1e-6)
    return Face(mk.Face())


def _dist_to_face(face, p):
    from OCP.BRep import BRep_Tool
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf
    from OCP.gp import gp_Pnt
    pr = GeomAPI_ProjectPointOnSurf(gp_Pnt(*map(float, p)), BRep_Tool.Surface_s(face.wrapped))
    return pr.LowerDistance() if pr.NbPoints() else math.inf


# ------------------------------------------------------------------ continuity
def _surf_props(face, p):
    """normal (face-orientation aware), principal curvatures + directions at the projection of p."""
    from OCP.BRep import BRep_Tool
    from OCP.ShapeAnalysis import ShapeAnalysis_Surface
    from OCP.GeomLProp import GeomLProp_SLProps
    from OCP.TopAbs import TopAbs_REVERSED
    from OCP.gp import gp_Pnt, gp_Dir
    s = BRep_Tool.Surface_s(face.wrapped)
    uv = ShapeAnalysis_Surface(s).ValueOfUV(gp_Pnt(*map(float, p)), 1e-7)
    pr = GeomLProp_SLProps(s, uv.X(), uv.Y(), 2, 1e-9)
    q = pr.Value()
    if not pr.IsNormalDefined():
        return None
    nd = pr.Normal()
    nrm = np.array([nd.X(), nd.Y(), nd.Z()])
    sgn = -1.0 if face.wrapped.Orientation() == TopAbs_REVERSED else 1.0
    nrm *= sgn
    k1 = k2 = 0.0
    d1 = d2 = np.zeros(3)
    if pr.IsCurvatureDefined():
        k1, k2 = pr.MaxCurvature() * sgn, pr.MinCurvature() * sgn
        a, b = gp_Dir(), gp_Dir()
        pr.CurvatureDirections(a, b)
        d1, d2 = np.array([a.X(), a.Y(), a.Z()]), np.array([b.X(), b.Y(), b.Z()])
    return np.array([q.X(), q.Y(), q.Z()]), nrm, (k1, d1), (k2, d2)


def _kn(props, direction):
    _, _, (k1, d1), (k2, d2) = props
    if not d1.any():
        return 0.0
    c = float(np.dot(direction, d1))
    s = float(np.dot(direction, d2))
    return k1 * c * c + k2 * s * s


def edge_continuity(shape, edges=None, samples=9, g1_deg=0.1, g2_rel=0.05, gap_tol=None):
    """For every edge shared by two faces of `shape` (or the given edges): G0 gap, G1 normal angle (deg), G2
    cross-curvature jump. Returns list of {edge, centre, length, gap, angle_deg, dk_rel, dk_abs, cls} with
    cls in G2|G1|G0|open, plus a summary count."""
    from OCP.TopExp import TopExp
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    try:
        from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
    except ImportError:  # OCP 8.x
        from OCP.collections import \
            IndexedDataMap_TopoDS_Shape_List_TopoDS_Shape_TopTools_ShapeMapHasher as \
            TopTools_IndexedDataMapOfShapeListOfShape
    from build123d.topology.shape_core import downcast
    mp = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, mp)
    bb = shape.bounding_box()
    gap_tol = gap_tol or 1e-5 * bb.diagonal
    want = None if edges is None else list(edges)
    out = []
    for i in range(1, mp.Extent() + 1):
        e = Edge(downcast(mp.FindKey(i)))
        if want is not None and not any(e.is_same(w) for w in want):
            continue
        fl = mp.FindFromIndex(i)
        faces = []
        for f in fl:
            ff = Face(downcast(f))
            if not any(ff.is_same(x) for x in faces):
                faces.append(ff)
        if e.length < 1e-12:
            continue
        row = {"edge": i, "centre": [round(v, 6) for v in tuple(e.center())], "length": round(e.length, 6)}
        if len(faces) < 2:
            row.update(cls="open")
            out.append(row)
            continue
        fa, fb = faces[0], faces[1]
        gaps, angs, dks, dka = [], [], [], []
        for t in np.linspace(0.05, 0.95, samples):
            p = np.array(tuple(e.position_at(t)))
            tg = np.array(tuple(e.tangent_at(t)))
            pa, pb = _surf_props(fa, p), _surf_props(fb, p)
            if pa is None or pb is None:
                continue
            gaps.append(float(np.linalg.norm(pa[0] - pb[0])))
            na, nb = pa[1], pb[1]
            angs.append(math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(na, nb)))))))
            cross = np.cross(tg, na)
            cross /= max(np.linalg.norm(cross), 1e-12)
            ka, kb = _kn(pa, cross), _kn(pb, cross)
            dka.append(abs(ka - kb))
            dks.append(abs(ka - kb) / max(abs(ka), abs(kb), 1e-12) if max(abs(ka), abs(kb)) > 1e-9 else 0.0)
        if not gaps:
            continue
        g, a, dr, da = max(gaps), max(angs), max(dks), max(dka)
        cls = "G2" if a < g1_deg and dr < g2_rel else "G1" if a < g1_deg * 5 else "G0" if g < max(gap_tol, 1e-7) \
            else "open"
        row.update(gap=round(g, 9), angle_deg=round(a, 4), dk_rel=round(dr, 4), dk_abs=round(da, 6), cls=cls)
        out.append(row)
    summ = {c: sum(r["cls"] == c for r in out) for c in ("G2", "G1", "G0", "open")}
    return {"edges": out, "summary": summ}


# ------------------------------------------------------------------ zebra
def zebra(face, n=160, stripes=16, light=(0.35, -0.45, 0.82), png=None):
    """Isophote zebra over the face's parameter grid: phase = n.L (light dir). Stripes = floor(phase*stripes).
    Returns {kink, wiggle, png}: kink = worst |2nd difference| of the phase relative to the 99th percentile
    (a crease / G1 break -> isolated spike >> 1; smooth G2 surface ~ 1-3); wiggle = mean number of inflections
    of the phase per grid line (waviness; a fair surface has few). Optional PNG (parameter space)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepTools import BRepTools
    from OCP.GeomLProp import GeomLProp_SLProps
    s = BRep_Tool.Surface_s(face.wrapped)
    u0, u1, v0, v1 = BRepTools.UVBounds_s(face.wrapped)
    L = np.array(light, float)
    L /= np.linalg.norm(L)
    ph = np.zeros((n, n))
    for i, u in enumerate(np.linspace(u0, u1, n)):
        for j, v in enumerate(np.linspace(v0, v1, n)):
            pr = GeomLProp_SLProps(s, u, v, 1, 1e-9)
            if pr.IsNormalDefined():
                nd = pr.Normal()
                ph[i, j] = nd.X() * L[0] + nd.Y() * L[1] + nd.Z() * L[2]
            else:
                ph[i, j] = ph[i, j - 1] if j else 0.0
    sec = np.concatenate([np.abs(np.diff(ph, 2, axis=0)).ravel(), np.abs(np.diff(ph, 2, axis=1)).ravel()])
    kink = float(sec.max() / max(np.percentile(sec, 99), 1e-12))
    c0 = np.sign(np.round(np.diff(ph, 2, axis=0), 9))
    c1 = np.sign(np.round(np.diff(ph, 2, axis=1), 9))
    wig = float(((np.abs(np.diff(c0, axis=0)) > 1).sum(0).mean() + (np.abs(np.diff(c1, axis=1)) > 1).sum(1).mean()) / 2)
    out = {"kink": round(kink, 3), "wiggle": round(wig, 3)}
    if png:
        from PIL import Image
        img = ((np.floor((ph + 1) * stripes) % 2) * 255).astype(np.uint8)
        Image.fromarray(img.T[::-1]).resize((480, 480), Image.NEAREST).save(png)
        out["png"] = png
    return out


def sew(faces, tol=1e-6):
    """Sew sheets into a shell (and a solid if closed)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
    sw = BRepBuilderAPI_Sewing(tol)
    for f in faces:
        sw.Add(f.wrapped)
    sw.Perform()
    sh = Shape.cast(sw.SewedShape())
    shells = sh.shells() if hasattr(sh, "shells") else []
    if len(shells) == 1:
        from OCP.BRepCheck import BRepCheck_Shell
        from OCP.BRepCheck import BRepCheck_Status
        if BRepCheck_Shell(shells[0].wrapped).Closed() == BRepCheck_Status.BRepCheck_NoError:
            from build123d import Solid
            return Solid(shells[0].wrapped)
    return sh
