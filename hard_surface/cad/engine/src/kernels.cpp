// Risky kernel ops (fillet/chamfer, boolean, shell, offset_face). Pure: shapes in -> shape out, so they can run
// in-process or in the isolated worker child (isolate.cpp) with identical results.
#include "model.hpp"

#include <BRepAlgoAPI_Common.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepClass3d_SolidClassifier.hxx>
#include <BRepFilletAPI_MakeChamfer.hxx>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <BRepOffsetAPI_MakeOffsetShape.hxx>
#include <BRepOffsetAPI_MakeThickSolid.hxx>
#include <BRepOffset_MakeOffset.hxx>
#include <thread>

std::map<std::string, KernelFn>& kernel_registry() { static std::map<std::string, KernelFn> r; return r; }
KernelReg::KernelReg(const char* n, KernelFn f) { kernel_registry()[n] = std::move(f); }

static bool ok_solid(const TopoDS_Shape& s) {
    if (s.IsNull()) return false;
    try { return geo::valid(s) && geo::volume(s) > 1e-12; } catch (...) { return false; }
}

static std::vector<TopoDS_Shape> by_index(const TopoDS_Shape& s, TopAbs_ShapeEnum t, const json& idx) {
    auto all = geo::subshapes(s, t);
    std::vector<TopoDS_Shape> out;
    for (auto& i : idx) {
        int k = i.get<int>();
        if (k < 0 || k >= (int)all.size()) throw ToolError("sub-shape index out of range");
        out.push_back(all[k]);
    }
    return out;
}

// ------------------------------------------------------------------ fillet / chamfer: full radius or FAIL
// (no silent shrink: on failure bisect the max feasible radius and report it + the edges that fail alone)
static TopoDS_Shape try_round(const TopoDS_Shape& s, const std::vector<TopoDS_Shape>& es, double r, bool chamfer) {
    try {
        TopoDS_Shape res;
        if (chamfer) {
            BRepFilletAPI_MakeChamfer mk(s);
            for (auto& e : es) mk.Add(r, TopoDS::Edge(e));
            mk.Build();
            if (!mk.IsDone()) return {};
            res = mk.Shape();
        } else {
            BRepFilletAPI_MakeFillet mk(s, ChFi3d_Rational);
            for (auto& e : es) mk.Add(r, TopoDS::Edge(e));
            mk.Build();
            if (!mk.IsDone()) return {};
            res = mk.Shape();
        }
        res = geo::cast_solid(res);
        return ok_solid(res) ? res : TopoDS_Shape();
    } catch (...) { return {}; }
}

static KernelReg k_round("round", [](const std::vector<TopoDS_Shape>& in, const json& p, json& info) -> TopoDS_Shape {
    const TopoDS_Shape& s = in.at(0);
    auto es = by_index(s, TopAbs_EDGE, p.at("edges"));
    double r = p.at("radius");
    bool ch = p.value("chamfer", false);
    TopoDS_Shape res = try_round(s, es, r, ch);
    if (!res.IsNull()) { info["applied"] = r; return res; }
    double lo = 0, hi = 1;
    for (int i = 0; i < 7; ++i) {
        double mid = 0.5 * (lo + hi);
        if (!try_round(s, es, r * mid, ch).IsNull()) lo = mid; else hi = mid;
    }
    json bad = json::array();
    if (es.size() > 1 && es.size() <= 24)
        for (auto& e : es)
            if (try_round(s, {e}, r, ch).IsNull() && bad.size() < 6) bad.push_back(desc(e));
    std::string what = ch ? "chamfer" : "fillet";
    std::ostringstream m;
    m << what << " r=" << r << " impossible on " << es.size() << " edge(s); max feasible radius ~" << geo::rnd(r * lo, 6)
      << " (no silent shrink: lower r, or split the edge set)";
    json d = {{"max_feasible", geo::rnd(r * lo, 6)}, {"requested", r}};
    if (!bad.empty()) d["bad_edges"] = bad;
    throw ToolError(m.str(), "radius too big for a neighbouring short edge/face: lower it or split the edge set (error data has max).", d);
});

// ------------------------------------------------------------------ booleans: plain -> fuzzy, sanity + no-op probe
static TopoDS_Shape occ_bool(const std::string& kind, const TopoDS_Shape& a, const std::vector<TopoDS_Shape>& tools, double fuzzy) {
    std::unique_ptr<BRepAlgoAPI_BooleanOperation> op;
    if (kind == "cut") op = std::make_unique<BRepAlgoAPI_Cut>();
    else if (kind == "fuse") op = std::make_unique<BRepAlgoAPI_Fuse>();
    else op = std::make_unique<BRepAlgoAPI_Common>();
    ShapeList la, lb;
    la.Append(a);
    for (auto& t : tools) lb.Append(t);
    op->SetArguments(la);
    op->SetTools(lb);
    if (fuzzy > 0) op->SetFuzzyValue(fuzzy);
    op->SetRunParallel(true);
    op->Build();
    if (!op->IsDone()) return {};
    return geo::clean(op->Shape());
}

static double overlap_estimate(const TopoDS_Shape& a, const TopoDS_Shape& b, int n = 6) {
    Bnd_Box A = geo::bbox(a), B = geo::bbox(b);
    double lo[3], hi[3], a0[3], a1[3], b0[3], b1[3];
    A.Get(a0[0], a0[1], a0[2], a1[0], a1[1], a1[2]);
    B.Get(b0[0], b0[1], b0[2], b1[0], b1[1], b1[2]);
    for (int i = 0; i < 3; ++i) { lo[i] = std::max(a0[i], b0[i]); hi[i] = std::min(a1[i], b1[i]); if (hi[i] <= lo[i]) return 0; }
    BRepClass3d_SolidClassifier ca(a), cb(b);
    int hit = 0;
    for (int i = 0; i < n; ++i) for (int j = 0; j < n; ++j) for (int k = 0; k < n; ++k) {
        gp_Pnt p(lo[0] + (hi[0] - lo[0]) * (i + 0.5) / n, lo[1] + (hi[1] - lo[1]) * (j + 0.5) / n, lo[2] + (hi[2] - lo[2]) * (k + 0.5) / n);
        ca.Perform(p, 1e-7);
        if (ca.State() != TopAbs_IN) continue;
        cb.Perform(p, 1e-7);
        hit += cb.State() == TopAbs_IN;
    }
    return (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2]) * hit / (double)(n * n * n);
}

static KernelReg k_bool("boolean", [](const std::vector<TopoDS_Shape>& in, const json& p, json& info) -> TopoDS_Shape {
    std::string kind = p.at("kind");
    const TopoDS_Shape& a = in.at(0);
    std::vector<TopoDS_Shape> tools(in.begin() + 1, in.end());
    BRep_Builder bb; TopoDS_Compound tc; bb.MakeCompound(tc);
    for (auto& t : tools) bb.Add(tc, t);
    double va = geo::volume(a), vb = geo::volume(tc);
    auto sane = [&](const TopoDS_Shape& r) {
        if (!ok_solid(r)) return false;
        double v = geo::volume(r), tol = 1e-3 * std::max(va, vb) + 1e-9;
        if (kind == "cut") {
            if (!(v <= va + tol && v >= va - vb - tol)) return false;
            double est = overlap_estimate(a, tc);
            if (est > 0.02 * va && (va - v) < 0.4 * est) { info["noop_rejected"] = geo::rnd(est / va, 4); return false; }
            return true;
        }
        if (kind == "fuse") return v >= std::max(va, vb) - tol && v <= va + vb + tol;
        return v <= std::min(va, vb) + tol;
    };
    TopoDS_Shape r;
    try { r = occ_bool(kind, a, tools, 0); } catch (...) { r.Nullify(); }
    if (sane(r)) { info["status"] = "ok"; return r; }
    double d = std::max(geo::diag(a), 1e-9);
    for (double fz : {1e-6, 1e-5, 1e-4}) {
        try { r = occ_bool(kind, a, tools, fz * d); } catch (...) { r.Nullify(); }
        if (sane(r)) { info["status"] = "fuzzy"; info["fuzzy"] = fz * d; return r; }
    }
    std::string extra = info.contains("noop_rejected") ? " (OCCT returned a silent no-op: the tool overlaps but nothing was removed)" : "";
    throw ToolError("boolean " + kind + " failed (plain, fuzzy 1e-6..1e-4; no mesh fallback)" + extra,
                    "move the tool off coplanar/tangent faces by ~1e-4, simplify the tool, or fillet after the boolean.");
});

// ------------------------------------------------------------------ shell
static bool shell_ok(const TopoDS_Shape& r, double area, double t, double vin) {
    if (!ok_solid(r)) return false;
    double v = geo::volume(r);
    return v < vin && v > 0.25 * area * t && v < 1.75 * area * t;
}

static KernelReg k_shell("shell", [](const std::vector<TopoDS_Shape>& in, const json& p, json& info) -> TopoDS_Shape {
    const TopoDS_Shape& s = in.at(0);
    double t = std::abs(p.at("thickness").get<double>());
    bool outward = p.value("outward", false);
    double off = outward ? t : -t;
    auto faces = by_index(s, TopAbs_FACE, p.value("faces", json::array()));
    std::string force = p.value("strategy", "");
    double A = geo::area(s), V = geo::volume(s);
    json tried = json::array();
    auto attempt = [&](const std::string& name) -> TopoDS_Shape {
        try {
            if (name == "arc" || name == "intersection") {
                ShapeList closing;
                for (auto& f : faces) closing.Append(f);
                if (faces.empty()) {
                    BRepOffsetAPI_MakeOffsetShape mk;
                    mk.PerformByJoin(s, off, 1e-4, BRepOffset_Skin, name == "intersection", false, name == "arc" ? GeomAbs_Arc : GeomAbs_Intersection);
                    if (!mk.IsDone()) return {};
                    TopoDS_Shape o = geo::cast_solid(mk.Shape());
                    // closed hollow: offset skin -> solid with a void
                    return outward ? occ_bool("cut", o, {s}, 0) : occ_bool("cut", s, {o}, 0);
                }
                BRepOffsetAPI_MakeThickSolid mk;
                mk.MakeThickSolidByJoin(s, closing, off, 1e-4, BRepOffset_Skin, name == "intersection", false, name == "arc" ? GeomAbs_Arc : GeomAbs_Intersection);
                mk.Build();
                if (!mk.IsDone()) return {};
                return geo::cast_solid(mk.Shape());
            }
            if (name == "simple" && faces.empty()) {
                BRepOffsetAPI_MakeOffsetShape mk;
                mk.PerformBySimple(s, off);
                if (!mk.IsDone()) return {};
                TopoDS_Shape o = geo::cast_solid(mk.Shape());
                return outward ? occ_bool("cut", o, {s}, 0) : occ_bool("cut", s, {o}, 0);
            }
        } catch (...) {}
        return {};
    };
    std::vector<std::string> order = force.empty() ? std::vector<std::string>{"arc", "intersection", "simple"} : std::vector<std::string>{force};
    for (auto& n : order) {
        TopoDS_Shape r = attempt(n);
        tried.push_back(n);
        double vref = outward ? 1e300 : V;
        if (shell_ok(r, A, t, vref)) { info["method"] = n; info["tried"] = tried; return r; }
    }
    throw ToolError("shell t=" + std::to_string(t) + " failed (tried " + tried.dump() + ")",
                    "thickness bigger than the smallest local radius of curvature/fillet: shell before filleting or thin it.");
});

// ------------------------------------------------------------------ offset_face (per-face BRepOffset)
static KernelReg k_offface("offset_face", [](const std::vector<TopoDS_Shape>& in, const json& p, json& info) -> TopoDS_Shape {
    const TopoDS_Shape& s = in.at(0);
    double d = p.at("distance");
    auto faces = by_index(s, TopAbs_FACE, p.at("faces"));
    BRepOffset_MakeOffset mk;
    mk.Initialize(s, 0.0, 1e-6, BRepOffset_Skin, true, false, GeomAbs_Intersection, false, false);
    for (auto& f : faces) mk.SetOffsetOnFace(TopoDS::Face(f), d);
    mk.MakeOffsetShape();
    if (mk.IsDone()) {
        TopoDS_Shape r = geo::cast_solid(mk.Shape());
        if (ok_solid(r)) {
            double dv = geo::volume(r) - geo::volume(s);
            if ((d > 0) == (dv > 0) && std::abs(dv) > 1e-15) { info["method"] = "per_face"; return r; }
        }
    }
    throw ToolError("offset_face d=" + std::to_string(d) + " failed", "smaller distance, or offset before filleting the neighbours");
});

// ------------------------------------------------------------------ test-only: prove crash/hang isolation
static KernelReg k_crash("debug_crash", [](const std::vector<TopoDS_Shape>&, const json& p, json&) -> TopoDS_Shape {
    if (p.value("how", std::string("segv")) == "hang") for (;;) std::this_thread::sleep_for(std::chrono::seconds(1));
    volatile int* null = nullptr;
    *null = 42;  // access violation in the CHILD only
    return {};
});
