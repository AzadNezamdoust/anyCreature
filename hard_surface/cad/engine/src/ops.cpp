// Modelling ops - behaviour-matched to cadkit.tools (geom.py, solids.py, edit.py, pattern.py, importer.py).
#include "model.hpp"

#include <BOPAlgo_Builder.hxx>
#include <BRepAlgoAPI_Defeaturing.hxx>
#include <BRepAlgoAPI_Splitter.hxx>
#include <BRepBuilderAPI_MakeSolid.hxx>
#include <BRepFilletAPI_MakeFillet2d.hxx>
#include <BRepOffsetAPI_MakeOffset.hxx>
#include <BRepOffsetAPI_MakePipeShell.hxx>
#include <BRepOffsetAPI_MakeThickSolid.hxx>
#include <BRepOffsetAPI_ThruSections.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepPrimAPI_MakeRevol.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
#include <GC_MakeArcOfCircle.hxx>
#include <GeomAPI_Interpolate.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_TrimmedCurve.hxx>
#include <IFSelect_ReturnStatus.hxx>
#include <Interface_Static.hxx>
#include <LocOpe_DPrism.hxx>
#include <STEPControl_Reader.hxx>
#include <STEPControl_Writer.hxx>
#include <ShapeFix_Face.hxx>
#include <ShapeFix_Solid.hxx>
#include <TopLoc_Location.hxx>
#include <gp_Circ.hxx>
#include <BRepLib.hxx>
#include <BRepAdaptor_CompCurve.hxx>

#define OP(name, out, spec, doc) static json op_##name(Model& m, json& p); static OpReg reg_##name(#name, out, spec, doc, op_##name); static json op_##name(Model& m, json& p)

static std::string S(const json& p, const char* k, const char* d = "") { return p.contains(k) && !p[k].is_null() ? p[k].get<std::string>() : d; }
static double D(const json& p, const char* k, double d = 0) { return p.contains(k) && !p[k].is_null() ? p[k].get<double>() : d; }
static bool B(const json& p, const char* k, bool d = false) { return p.contains(k) && !p[k].is_null() ? p[k].get<bool>() : d; }
static json J(const json& p, const char* k) { return p.contains(k) ? p[k] : json(); }

// plane-local -> global
static gp_Trsf plane_trsf(const gp_Ax3& a) { gp_Trsf t; t.SetTransformation(a); return t.Inverted(); }
static gp_Pnt local(const gp_Ax3& a, const json& v) {
    double x = v.size() > 0 ? v[0].get<double>() : 0, y = v.size() > 1 ? v[1].get<double>() : 0, z = v.size() > 2 ? v[2].get<double>() : 0;
    gp_XYZ o = a.Location().XYZ() + a.XDirection().XYZ() * x + a.YDirection().XYZ() * y + a.Direction().XYZ() * z;
    return gp_Pnt(o);
}
static TopoDS_Shape place(Model& m, const TopoDS_Shape& s, const json& at, const json& pl) {
    gp_Trsf T = plane_trsf(m.plane(pl));
    gp_Trsf A;
    if (!at.is_null()) { gp_Vec v = geo::vec(at); A.SetTranslation(v); }
    return s.Moved(TopLoc_Location(T * A));
}
static TopoDS_Shape moved(const TopoDS_Shape& s, const gp_Vec& v) { gp_Trsf t; t.SetTranslation(v); return s.Moved(TopLoc_Location(t)); }
static TopoDS_Shape xform(const TopoDS_Shape& s, const gp_Trsf& t) { return BRepBuilderAPI_Transform(s, t, true).Shape(); }

static TopoDS_Wire make_wire(const std::vector<TopoDS_Edge>& es) {
    BRepBuilderAPI_MakeWire w;
    for (auto& e : es) w.Add(e);
    if (!w.IsDone()) throw ToolError("edges do not form a connected wire");
    return w.Wire();
}
static TopoDS_Wire polygon(const std::vector<gp_Pnt>& P, bool close) {
    BRepBuilderAPI_MakePolygon mp;
    for (auto& p : P) mp.Add(p);
    if (close) mp.Close();
    return mp.Wire();
}

static TopoDS_Wire as_wire(Model& m, const json& ref) {
    Sel s = m.resolve(ref);
    if (s.whole) {
        if (s.shape.ShapeType() == TopAbs_WIRE) return TopoDS::Wire(s.shape);
        if (s.shape.ShapeType() == TopAbs_EDGE) return make_wire({TopoDS::Edge(s.shape)});
        auto ws = geo::subshapes(s.shape, TopAbs_WIRE);
        if (ws.size() == 1) return TopoDS::Wire(ws[0]);
        throw ToolError(ref.dump() + " is not a curve");
    }
    std::vector<TopoDS_Edge> es;
    for (auto& x : s.items) if (x.ShapeType() == TopAbs_EDGE) es.push_back(TopoDS::Edge(x));
    if (s.items.size() == 1 && s.items[0].ShapeType() == TopAbs_WIRE) return TopoDS::Wire(s.items[0]);
    return make_wire(es);
}

static TopoDS_Face face_from_wire(const TopoDS_Wire& w, const std::vector<TopoDS_Wire>& inner = {}) {
    BRepBuilderAPI_MakeFace mf(w, true);
    if (!mf.IsDone()) throw ToolError("curve is not planar / closed - cannot make a face", "close it or make regions first");
    for (auto& i : inner) mf.Add(TopoDS::Wire(i.Reversed()));
    TopoDS_Face f = mf.Face();
    ShapeFix_Face sf(f);
    sf.FixOrientation();
    sf.Perform();
    TopoDS_Face r = TopoDS::Face(sf.Result());
    if (geo::area(r) < 0) {  // wire ran clockwise vs the plane: flip the face (positive region)
        BRepBuilderAPI_MakeFace mf2(TopoDS::Wire(w.Reversed()), true);  // no ShapeFix: it made a 'hole in infinite plane'
        for (auto& i : inner) mf2.Add(TopoDS::Wire(i));
        if (mf2.IsDone() && geo::area(mf2.Face()) > 0) return mf2.Face();
        return TopoDS::Face(r.Reversed());
    }
    return r;
}

static TopoDS_Face one_face(Model& m, const json& ref) {
    Sel s = m.resolve(ref);
    std::vector<TopoDS_Shape> fs;
    if (s.whole) { if (s.shape.ShapeType() == TopAbs_FACE) return TopoDS::Face(s.shape); fs = geo::subshapes(s.shape, TopAbs_FACE); }
    else fs = s.items;
    if (fs.size() == 1 && fs[0].ShapeType() == TopAbs_FACE) return TopoDS::Face(fs[0]);
    throw ToolError("ref " + ref.dump() + " gave " + std::to_string(fs.size()) + " faces, need 1");
}

static TopoDS_Face profile(Model& m, const json& ref) {
    Sel s = m.resolve(ref);
    if (s.whole && (s.shape.ShapeType() == TopAbs_WIRE || s.shape.ShapeType() == TopAbs_EDGE)) {
        TopoDS_Wire w = as_wire(m, ref);
        if (!BRep_Tool::IsClosed(w)) throw ToolError("profile " + ref.dump() + " is an open curve", "close it, or make regions from it first");
        return face_from_wire(w);
    }
    return one_face(m, ref);
}

static gp_Vec face_normal(const TopoDS_Face& f) { gp_Vec n; if (!geo::face_normal(f, n)) throw ToolError("face has no normal"); return n; }

// ------------------------------------------------------------------ solid combine (extrude/revolve mode)
static TopoDS_Shape boolean_k(const std::string& kind, const TopoDS_Shape& a, const std::vector<TopoDS_Shape>& tools, json* info = nullptr) {
    json i = json::object();
    std::vector<TopoDS_Shape> in{a};
    in.insert(in.end(), tools.begin(), tools.end());
    TopoDS_Shape r = run_kernel("boolean", in, {{"kind", kind}}, i);
    if (info) *info = i;
    return r;
}

static std::string apply_mode(Model& m, const std::string& name, const TopoDS_Shape& s, const std::string& mode, const json& target) {
    if (mode == "new" || target.is_null()) {
        if (mode != "new") throw ToolError("mode '" + mode + "' needs target", "pass target=<body name>");
        m.put(name, "solid", s);
        return name;
    }
    std::string k = mode == "union" ? "fuse" : mode == "cut" ? "cut" : mode == "intersect" ? "common" : "";
    if (k.empty()) throw ToolError("bad mode '" + mode + "'", "new|union|cut|intersect");
    std::string t = target.get<std::string>();
    Obj& o = m.get(t, {"solid"});
    json meta = o.meta;
    m.put(t, "solid", boolean_k(k, o.shape, {s}), meta);
    return t;
}

// ================================================================== primitives
OP(box, true, "spec 1 Primitives: Box (width/length/height, base plane)", "Box size [x,y,z] at [x,y,z] on plane. align center|min|base.") {
    double x = p["size"][0], y = p["size"][1], z = p["size"][2];
    std::string al = S(p, "align", "center");
    gp_Pnt c0 = al == "min" ? gp_Pnt(0, 0, 0) : al == "base" ? gp_Pnt(-x / 2, -y / 2, 0) : gp_Pnt(-x / 2, -y / 2, -z / 2);
    if (al != "min" && al != "base" && al != "center") throw ToolError("bad align " + al, "center|min|base");
    m.put(p["name"], "solid", place(m, BRepPrimAPI_MakeBox(c0, x, y, z).Shape(), J(p, "at"), J(p, "plane")));
    return {{"name", p["name"]}};
}
OP(cylinder, true, "spec 1 Primitives: Cylinder (radius, height)", "Cylinder centred at `at`, axis = plane normal.") {
    double r = p["radius"], h = p["height"];
    TopoDS_Shape s = BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0, 0, -h / 2), gp_Dir(0, 0, 1)), r, h).Shape();
    m.put(p["name"], "solid", place(m, s, J(p, "at"), J(p, "plane")));
    return {{"name", p["name"]}};
}
OP(cone, true, "spec 1 Primitives: Cone (radius1/radius2, height)", "Cone r1 bottom, r2 top, centred.") {
    double h = p["height"];
    TopoDS_Shape s = BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0, 0, -h / 2), gp_Dir(0, 0, 1)), p["radius1"].get<double>(), p["radius2"].get<double>(), h).Shape();
    m.put(p["name"], "solid", place(m, s, J(p, "at"), J(p, "plane")));
    return {{"name", p["name"]}};
}
OP(sphere, true, "spec 1 Primitives: Sphere (center, radius)", "Sphere at `at`.") {
    TopoDS_Shape s = BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 0), p["radius"].get<double>()).Shape();
    m.put(p["name"], "solid", J(p, "at").is_null() ? s : moved(s, geo::vec(p["at"])));
    return {{"name", p["name"]}};
}
OP(torus, true, "spec 1 Primitives (torus)", "Torus major/minor centred.") {
    TopoDS_Shape s = BRepPrimAPI_MakeTorus(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), p["major"].get<double>(), p["minor"].get<double>()).Shape();
    m.put(p["name"], "solid", place(m, s, J(p, "at"), J(p, "plane")));
    return {{"name", p["name"]}};
}
OP(prism, true, "spec 1 Primitives / 3 Region extrude: prism from a region", "Solid from a region along its normal.") {
    TopoDS_Face f = one_face(m, p["region"]);
    gp_Vec n = face_normal(f) * D(p, "height");
    m.put(p["name"], "solid", BRepPrimAPI_MakePrism(f, n).Shape());
    return {{"name", p["name"]}};
}

// ================================================================== curves
static std::vector<gp_Pnt> pts(Model& m, const json& P, const json& pl) {
    gp_Ax3 a = m.plane(pl);
    std::vector<gp_Pnt> out;
    for (auto& v : P) out.push_back(local(a, v));
    return out;
}
OP(line, true, "spec 1 Curves: Polyline/line", "Polyline through points (2D on plane or 3D). closed -> back to first point.") {
    auto P = pts(m, p["points"], J(p, "plane"));
    if (B(p, "closed")) P.push_back(P[0]);
    std::vector<TopoDS_Edge> es;
    for (size_t i = 0; i + 1 < P.size(); ++i) es.push_back(BRepBuilderAPI_MakeEdge(P[i], P[i + 1]).Edge());
    m.put(p["name"], "curve", make_wire(es));
    return {{"name", p["name"]}, {"edges", es.size()}};
}
OP(arc, true, "spec 1 Curves: Arc (3-pt)", "Arc through start, mid, end.") {
    auto P = pts(m, json::array({p["start"], p["mid"], p["end"]}), J(p, "plane"));
    m.put(p["name"], "curve", make_wire({BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(P[0], P[1], P[2]).Value()).Edge()}));
    return {{"name", p["name"]}};
}
OP(spline, true, "spec 1 Curves: Curve (NURBS/cubic, CurveFactory)", "Interpolating B-spline through points; optional end tangents.") {
    auto P = pts(m, p["points"], J(p, "plane"));
    occ::handle<NCollection_HArray1<gp_Pnt>> arr = new NCollection_HArray1<gp_Pnt>(1, (int)P.size());
    for (size_t i = 0; i < P.size(); ++i) arr->SetValue((int)i + 1, P[i]);
    GeomAPI_Interpolate ip(arr, B(p, "closed"), 1e-6);
    json tg = J(p, "tangents");
    if (tg.is_array() && tg.size() == 2) ip.Load(geo::vec(tg[0]), geo::vec(tg[1]), true);
    ip.Perform();
    if (!ip.IsDone()) throw ToolError("spline interpolation failed", "points must be distinct");
    m.put(p["name"], "curve", make_wire({BRepBuilderAPI_MakeEdge(ip.Curve()).Edge()}));
    return {{"name", p["name"]}};
}
OP(circle, true, "spec 1 Curves: Circle (center)", "Circle on plane at center.") {
    gp_Ax3 a = m.plane(J(p, "plane"));
    gp_Pnt c = local(a, J(p, "center").is_null() ? json::array({0, 0}) : p["center"]);
    gp_Circ ci(gp_Ax2(c, a.Direction(), a.XDirection()), p["radius"].get<double>());
    m.put(p["name"], "curve", make_wire({BRepBuilderAPI_MakeEdge(ci).Edge()}));
    return {{"name", p["name"]}};
}
static TopoDS_Wire fillet2d(const TopoDS_Wire& w, double r, const std::vector<TopoDS_Shape>& verts) {
    TopoDS_Face f = face_from_wire(w);
    BRepFilletAPI_MakeFillet2d mk(f);
    for (auto& v : verts) {
        // vertex of the face (same geometry)
        for (auto& fv : geo::subshapes(f, TopAbs_VERTEX))
            if (BRep_Tool::Pnt(TopoDS::Vertex(fv)).Distance(BRep_Tool::Pnt(TopoDS::Vertex(v))) < 1e-9) { mk.AddFillet(TopoDS::Vertex(fv), r); break; }
    }
    mk.Build();
    if (!mk.IsDone()) throw ToolError("2d fillet failed");
    return BRepTools::OuterWire(TopoDS::Face(mk.Shape()));
}
OP(rectangle, true, "spec 1 Primitives: Rectangle (corner/center)", "Rectangle width x height at center on plane; corner_radius rounds corners.") {
    json c = J(p, "center");
    double cx = c.is_array() ? c[0].get<double>() : 0, cy = c.is_array() ? c[1].get<double>() : 0, w = D(p, "width") / 2, h = D(p, "height") / 2;
    auto P = pts(m, json::array({{cx - w, cy - h}, {cx + w, cy - h}, {cx + w, cy + h}, {cx - w, cy + h}}), J(p, "plane"));
    TopoDS_Wire wire = polygon(P, true);
    if (D(p, "corner_radius") > 0) wire = fillet2d(wire, D(p, "corner_radius"), geo::subshapes(wire, TopAbs_VERTEX));
    m.put(p["name"], "curve", wire);
    return {{"name", p["name"]}};
}
OP(polygon, true, "spec 1 Primitives: Polygon (sides)", "Regular polygon: sides, radius (circumradius), rotation deg.") {
    json c = J(p, "center");
    double cx = c.is_array() ? c[0].get<double>() : 0, cy = c.is_array() ? c[1].get<double>() : 0, r = p["radius"], a0 = D(p, "rotation") * M_PI / 180;
    int n = p["sides"];
    json P = json::array();
    for (int i = 0; i < n; ++i) P.push_back({cx + r * std::cos(a0 + 2 * M_PI * i / n), cy + r * std::sin(a0 + 2 * M_PI * i / n)});
    m.put(p["name"], "curve", polygon(pts(m, P, J(p, "plane")), true));
    return {{"name", p["name"]}};
}
OP(offset_curve, true, "spec 1 Curves edit: Offset planar curve (distance, side)", "Offset planar wire (+ out / - in). kind arc|intersection.") {
    TopoDS_Wire w = as_wire(m, p["curve"]);
    BRepOffsetAPI_MakeOffset mk;
    mk.Init(S(p, "kind", "arc") == "arc" ? GeomAbs_Arc : GeomAbs_Intersection);
    mk.AddWire(w);
    mk.Perform(D(p, "distance"));
    if (!mk.IsDone()) throw ToolError("offset_curve failed", "distance smaller than the tightest curve radius");
    auto ws = geo::subshapes(mk.Shape(), TopAbs_WIRE);
    if (ws.empty()) throw ToolError("offset_curve produced nothing");
    m.put(p["name"], "curve", ws[0]);
    return {{"name", p["name"]}};
}
OP(fillet_curve, true, "spec 1 Curves edit: Fillet a curve vertex (radius)", "Round planar wire corners (all, or vertices nearest `near`).") {
    TopoDS_Wire w = as_wire(m, p["curve"]);
    auto vs = geo::subshapes(w, TopAbs_VERTEX);
    if (p.contains("near") && !p["near"].is_null()) {
        std::vector<TopoDS_Shape> sel;
        for (auto& q : p["near"]) {
            gp_Pnt t = geo::pnt(q);
            auto best = std::min_element(vs.begin(), vs.end(), [&](auto& a, auto& b) { return BRep_Tool::Pnt(TopoDS::Vertex(a)).Distance(t) < BRep_Tool::Pnt(TopoDS::Vertex(b)).Distance(t); });
            sel.push_back(*best);
        }
        vs = sel;
    }
    try { m.put(p["name"], "curve", fillet2d(w, D(p, "radius"), vs)); }
    catch (ToolError&) {
        double sh = 1e300;
        for (auto& e : geo::subshapes(w, TopAbs_EDGE)) sh = std::min(sh, geo::length(e));
        throw ToolError("fillet_curve r=" + std::to_string(D(p, "radius")) + " failed", "shortest segment " + std::to_string(sh) + ": keep r < " + std::to_string(sh / 2));
    }
    return {{"name", p["name"]}};
}
OP(regions, false, "spec 1 Curves: Regions (closed planar curves split into fillable faces)", "Closed planar curves -> faces <prefix>1..N sorted by area desc.") {
    std::string prefix = S(p, "prefix", "region");
    json out = json::array();
    std::vector<TopoDS_Face> faces;
    for (auto& c : p["curves"]) {
        TopoDS_Wire w = as_wire(m, c);
        if (!BRep_Tool::IsClosed(w)) throw ToolError("curve " + c.dump() + " is open", "close it (line closed=true) or join curves first");
        faces.push_back(face_from_wire(w));
    }
    if (faces.size() == 1) {
        m.put(prefix + "1", "region", faces[0]);
        return {{"regions", json::array({{{"name", prefix + "1"}, {"area", geo::rnd(geo::area(faces[0]), 8)}}})}};
    }
    BOPAlgo_Builder b;
    for (auto& f : faces) b.AddArgument(f);
    b.Perform();
    if (b.HasErrors()) throw ToolError("region split failed", "curves must be coplanar");
    auto frags = geo::subshapes(b.Shape(), TopAbs_FACE);
    std::vector<std::pair<double, TopoDS_Shape>> fa;
    for (auto& f : frags) { double a = geo::area(f); fa.push_back({std::abs(a), a < 0 ? f.Reversed() : f}); }
    std::stable_sort(fa.begin(), fa.end(), [](auto& a, auto& b) { return a.first > b.first; });
    int i = 1;
    for (auto& [a, f] : fa) {
        std::string nm = prefix + std::to_string(i++);
        m.put(nm, "region", f);
        out.push_back({{"name", nm}, {"area", geo::rnd(a, 8)}, {"center", geo::rnd(geo::center(f), 5)}});
    }
    return {{"regions", out}};
}
OP(cplane, false, "spec 1 Construction planes", "Named cplane from face | points | origin+normal(+x_dir); offset along normal.") {
    std::string cn = p["cname"];
    gp_Ax3 a;
    if (p.contains("face") && !p["face"].is_null()) {
        TopoDS_Face f = one_face(m, p["face"]);
        a = gp_Ax3(geo::center(f), gp_Dir(face_normal(f)));
    } else if (p.contains("points") && !p["points"].is_null()) {
        gp_Pnt A = geo::pnt(p["points"][0]), Bp = geo::pnt(p["points"][1]), C = geo::pnt(p["points"][2]);
        gp_Vec x(A, Bp), z = x.Crossed(gp_Vec(A, C));
        a = gp_Ax3(A, gp_Dir(z), gp_Dir(x));
    } else {
        gp_Pnt o = p.contains("origin") && !p["origin"].is_null() ? geo::pnt(p["origin"]) : gp_Pnt(0, 0, 0);
        gp_Dir n(geo::vec(p.contains("normal") && !p["normal"].is_null() ? p["normal"] : json("z")));
        a = p.contains("x_dir") && !p["x_dir"].is_null() ? gp_Ax3(o, n, gp_Dir(geo::vec(p["x_dir"]))) : gp_Ax3(o, n);
    }
    double off = D(p, "offset");
    if (off != 0) a.SetLocation(a.Location().Translated(gp_Vec(a.Direction()) * off));
    m.cur.cplanes[cn] = a;
    return {{"cplane", cn}, {"origin", geo::rnd(a.Location(), 5)}, {"normal", geo::rnd(gp_Pnt(a.Direction().XYZ()), 5)}};
}

// ================================================================== shape from profile
static TopoDS_Shape extrude_face(const TopoDS_Face& f, double amount, const gp_Vec& dir, double taper) {
    if (std::abs(taper) < 1e-12) return BRepPrimAPI_MakePrism(f, dir.Normalized() * amount).Shape();
    gp_Vec n = face_normal(f);
    if (dir.Normalized().IsEqual(n, 1e-9, 1e-9) && amount > 0) {
        LocOpe_DPrism dp(f, amount / std::cos(taper * M_PI / 180), taper * M_PI / 180);
        return dp.Shape();
    }
    throw ToolError("draft extrude only along +normal in the C++ engine (Phase 1)", "extrude along the profile normal, or use the Python kit");
}
OP(extrude, true, "spec 1 Shape-from-profile: Extrude (distance1/2, draft, thickness, mode)", "Push/pull a region/face/closed curve along normal (or direction); distance2 the other way; mode new|union|cut|intersect.") {
    TopoDS_Face f = profile(m, p["profile"]);
    double th = D(p, "thickness");
    if (th > 0) {
        BRepOffsetAPI_MakeOffset mk;
        mk.Init(GeomAbs_Arc);
        mk.AddWire(BRepTools::OuterWire(f));
        mk.Perform(-th);
        auto ws = geo::subshapes(mk.Shape(), TopAbs_WIRE);
        if (!mk.IsDone() || ws.empty()) throw ToolError("thin-wall inset failed", "thickness < half the narrowest profile width");
        f = face_from_wire(BRepTools::OuterWire(f), {TopoDS::Wire(ws[0])});
    }
    gp_Vec n = p.contains("direction") && !p["direction"].is_null() ? geo::vec(p["direction"]).Normalized() : face_normal(f);
    double d1 = D(p, "distance"), d2 = D(p, "distance2"), dr = D(p, "draft");
    double dr2 = p.contains("draft2") && !p["draft2"].is_null() ? p["draft2"].get<double>() : dr;
    std::vector<TopoDS_Shape> parts;
    if (std::abs(d1) > 1e-12) parts.push_back(extrude_face(f, d1, n, dr));
    if (std::abs(d2) > 1e-12) parts.push_back(extrude_face(f, d2, -n, dr2));
    if (parts.empty()) throw ToolError("extrude distance is 0");
    TopoDS_Shape s = parts.size() == 1 ? parts[0] : boolean_k("fuse", parts[0], {parts[1]});
    std::string out = apply_mode(m, p["name"], s, S(p, "mode", "new"), J(p, "target"));
    return {{"name", out}, {"volume", geo::rnd(geo::volume(m.get(out).shape), 9)}};
}
OP(revolve, true, "spec 1 Shape-from-profile: Revolve (axis, angle)", "Revolve profile about axis_origin/axis_dir by angle deg.") {
    TopoDS_Face f = profile(m, p["profile"]);
    gp_Ax1 ax(p.contains("axis_origin") ? geo::pnt(p["axis_origin"]) : gp_Pnt(0, 0, 0), gp_Dir(geo::vec(p.contains("axis_dir") ? p["axis_dir"] : json("z"))));
    double ang = D(p, "angle", 360);
    TopoDS_Shape s = BRepPrimAPI_MakeRevol(f, ax, ang * M_PI / 180).Shape();
    return {{"name", apply_mode(m, p["name"], s, S(p, "mode", "new"), J(p, "target"))}};
}
static TopoDS_Shape pipe_shell(const TopoDS_Wire& path, const TopoDS_Wire& w, bool frenet, int tr) {
    BRepOffsetAPI_MakePipeShell ps(path);
    ps.SetMode(frenet);
    ps.SetTransitionMode((BRepBuilderAPI_TransitionMode)tr);
    ps.Add(w, false, false);
    ps.Build();
    if (!ps.IsDone()) throw ToolError("sweep failed", "sweep path should be G1 with radius > profile size");
    ps.MakeSolid();
    return ps.Shape();
}
static TopoDS_Shape sweep_face(const TopoDS_Face& f, const TopoDS_Wire& path, bool frenet, int tr) {
    TopoDS_Wire ow = BRepTools::OuterWire(f);
    TopoDS_Shape s = pipe_shell(path, ow, frenet, tr);
    std::vector<TopoDS_Shape> holes;
    for (auto& w : geo::subshapes(f, TopAbs_WIRE)) if (!w.IsSame(ow)) holes.push_back(pipe_shell(path, TopoDS::Wire(w), frenet, tr));
    if (!holes.empty()) s = boolean_k("cut", s, holes);
    return geo::cast_solid(s);
}
OP(sweep, true, "spec 1 Shape-from-profile: Sweep (profile, path, mode)", "Sweep a profile (at the path start) along a path curve.") {
    TopoDS_Face f = profile(m, p["profile"]);
    TopoDS_Wire path = as_wire(m, p["path"]);
    std::string t = S(p, "transition", "right");
    int tr = t == "right" ? BRepBuilderAPI_RightCorner : t == "round" ? BRepBuilderAPI_RoundCorner : BRepBuilderAPI_Transformed;
    return {{"name", apply_mode(m, p["name"], sweep_face(f, path, B(p, "frenet"), tr), S(p, "mode", "new"), J(p, "target"))}};
}
OP(loft, true, "spec 1 Shape-from-profile: Loft (ordered curves/regions, ruled)", "Loft ordered profiles (outer wires).") {
    if (p["profiles"].size() < 2) throw ToolError("loft needs >= 2 profiles");
    BRepOffsetAPI_ThruSections ts(true, B(p, "ruled"));
    for (auto& r : p["profiles"]) ts.AddWire(BRepTools::OuterWire(profile(m, r)));
    if (p.contains("guide") && !p["guide"].is_null()) throw ToolError("loft guide not ported to the C++ engine yet", "use the Python kit (CADKIT_BACKEND=py)");
    ts.Build();
    if (!ts.IsDone()) throw ToolError("loft failed", "use profiles with equal edge counts and no twist");
    TopoDS_Shape s = geo::cast_solid(ts.Shape());
    if (!geo::valid(s)) throw ToolError("loft produced an invalid solid", "use profiles with equal edge counts and no twist");
    return {{"name", apply_mode(m, p["name"], s, S(p, "mode", "new"), J(p, "target"))}};
}
OP(pipe, true, "spec 1 Shape-from-profile: Pipe (path, radius, inner radius)", "Round tube along a path; inner_radius>0 hollow.") {
    TopoDS_Wire path = as_wire(m, p["path"]);
    double r = p["radius"], ri = D(p, "inner_radius");
    if (ri >= r) throw ToolError("inner_radius must be < radius");
    BRepAdaptor_CompCurve cc(path);
    gp_Pnt p0;
    gp_Vec t0;
    cc.D1(cc.FirstParameter(), p0, t0);
    gp_Ax2 ax(p0, gp_Dir(t0));
    TopoDS_Wire ow = make_wire({BRepBuilderAPI_MakeEdge(gp_Circ(ax, r)).Edge()});
    std::vector<TopoDS_Wire> inner;
    if (ri > 0) inner.push_back(make_wire({BRepBuilderAPI_MakeEdge(gp_Circ(ax, ri)).Edge()}));
    TopoDS_Face f = face_from_wire(ow, inner);
    return {{"name", apply_mode(m, p["name"], sweep_face(f, path, false, BRepBuilderAPI_RoundCorner), S(p, "mode", "new"), J(p, "target"))}};
}

// ================================================================== booleans / fillet / shell (isolated kernels)
static std::vector<int> indices_in(const TopoDS_Shape& s, TopAbs_ShapeEnum t, const std::vector<TopoDS_Shape>& items) {
    ShapeMap mp;
    TopExp::MapShapes(s, t, mp);
    std::vector<int> out;
    for (auto& x : items) {
        int i = mp.FindIndex(x);
        if (i <= 0) throw ToolError("selected sub-shape is not part of the body");
        out.push_back(i - 1);
    }
    return out;
}

OP(boolean, true, "spec 1 Booleans: Union/Difference/Intersect; plain -> fuzzy, no-op probe, no mesh fallback", "kind union|cut|intersect; target replaced; tools removed unless keep_tools.") {
    std::string kind = p["kind"];
    std::string k = kind == "union" || kind == "fuse" ? "fuse" : kind == "cut" ? "cut" : kind == "intersect" || kind == "common" ? "common" : "";
    if (k.empty()) throw ToolError("bad kind '" + kind + "'", "union|cut|intersect");
    std::vector<std::string> tools;
    if (p["tools"].is_string()) tools.push_back(p["tools"]); else for (auto& t : p["tools"]) tools.push_back(t);
    std::string target = p["target"];
    Obj& a = m.get(target, {"solid"});
    std::vector<TopoDS_Shape> ts;
    for (auto& t : tools) ts.push_back(m.get(t, {"solid"}).shape);
    json info;
    TopoDS_Shape r = boolean_k(k, a.shape, ts, &info);
    std::string nm = p["name"];
    std::string out = nm.rfind("boolean", 0) == 0 ? target : nm;
    json meta = a.meta;
    m.put(out, "solid", r, meta);
    if (!B(p, "keep_tools")) for (auto& t : tools) if (t != out) m.cur.objects.erase(t);
    json res = {{"name", out}, {"volume", geo::rnd(geo::volume(r), 9)}, {"faces", geo::count(r, TopAbs_FACE)}};
    if (info.value("status", "ok") != "ok") res["status"] = info["status"];
    return res;
}

static std::vector<TopoDS_Shape> edges_of(Model& m, const std::string& body, const json& ref) {
    json r = ref.is_object() && !ref.contains("obj") ? json{{"obj", body}, {"edges", ref}} : ref;
    auto es = m.sub(r, "edges");
    if (es.empty()) throw ToolError("edge ref " + ref.dump() + " matched nothing", "use the select tool to inspect");
    return es;
}
static std::vector<TopoDS_Shape> faces_of(Model& m, const std::string& body, const json& ref) {
    json r = ref.is_object() && !ref.contains("obj") ? json{{"obj", body}, {"faces", ref}} : ref;
    return m.sub(r, "faces");
}

static json round_op(Model& m, json& p, bool chamfer) {
    std::string body = p["body"];
    Obj& o = m.get(body, {"solid"});
    auto es = edges_of(m, body, p["edges"]);
    double r = chamfer ? D(p, "distance") : D(p, "radius");
    if (chamfer && (p.contains("distance2") && !p["distance2"].is_null() || p.contains("angle") && !p["angle"].is_null()))
        throw ToolError("asymmetric chamfer not ported to the C++ engine yet", "use distance only, or the Python kit");
    if (!chamfer && S(p, "shape", "round") != "round") throw ToolError("fillet shape '" + S(p, "shape") + "' not ported yet", "shape=round");
    json info;
    TopoDS_Shape res = run_kernel("round", {o.shape}, {{"edges", indices_in(o.shape, TopAbs_EDGE, es)}, {"radius", r}, {"chamfer", chamfer}}, info);
    json meta = o.meta;
    m.put(body, "solid", res, meta);
    return {{"name", body}, {"edges", es.size()}, {"faces", geo::count(res, TopAbs_FACE)}};
}
OP(fillet, false, "spec 1 Fillet: constant radius; impossible radius -> error with max_feasible (no silent shrink)", "Fillet edges (ref) of body at radius.") { return round_op(m, p, false); }
OP(chamfer, false, "spec 1 Fillet/chamfer: chamfer by distance", "Chamfer edges (ref) by distance.") { return round_op(m, p, true); }

OP(shell, false, "spec 1 Shell/hollow: faces to remove, thickness, inward/outward", "Hollow body to wall thickness removing open_faces (ref). strategy arc|intersection|simple.") {
    std::string body = p["body"];
    Obj& o = m.get(body, {"solid"});
    std::vector<TopoDS_Shape> fs;
    if (p.contains("open_faces") && !p["open_faces"].is_null()) fs = m.sub(p["open_faces"], "faces");
    json info;
    json kp = {{"faces", indices_in(o.shape, TopAbs_FACE, fs)}, {"thickness", p["thickness"]}, {"outward", B(p, "outward")}};
    if (p.contains("strategy") && !p["strategy"].is_null()) kp["strategy"] = p["strategy"];
    TopoDS_Shape r = run_kernel("shell", {o.shape}, kp, info);
    json meta = o.meta;
    m.put(body, "solid", r, meta);
    return {{"name", body}, {"volume", geo::rnd(geo::volume(r), 9)}, {"method", info.value("method", "")}};
}
OP(offset_face, false, "spec 1 Offset face (push/pull, neighbours adapt)", "Push (+)/pull (-) faces along normals.") {
    std::string body = p["body"];
    Obj& o = m.get(body, {"solid"});
    auto fs = faces_of(m, body, p["faces"]);
    if (fs.empty()) throw ToolError("face ref matched nothing");
    json info;
    TopoDS_Shape r = run_kernel("offset_face", {o.shape}, {{"faces", indices_in(o.shape, TopAbs_FACE, fs)}, {"distance", p["distance"]}}, info);
    json meta = o.meta;
    m.put(body, "solid", r, meta);
    return {{"name", body}, {"method", info.value("method", "")}, {"volume", geo::rnd(geo::volume(r), 9)}};
}
OP(thicken, true, "spec 1 Thicken sheet -> solid", "Thicken a face by thickness (both sides if both).") {
    TopoDS_Face f = one_face(m, p["face"]);
    double t = p["thickness"];
    BRepOffset_MakeOffset mo;
    mo.Initialize(f, t, 1e-4, BRepOffset_Skin, false, false, GeomAbs_Intersection, true, false);
    if (B(p, "both")) { mo.Initialize(TopoDS::Face(moved(f, face_normal(f) * (-t))), 2 * t, 1e-4, BRepOffset_Skin, false, false, GeomAbs_Intersection, true, false); }
    mo.MakeOffsetShape();
    if (!mo.IsDone()) throw ToolError("thicken failed", "smaller thickness");
    m.put(p["name"], "solid", geo::cast_solid(mo.Shape()));
    return {{"name", p["name"]}};
}
static TopoDS_Shape defeature(const TopoDS_Shape& s, const std::vector<TopoDS_Shape>& fs) {
    BRepAlgoAPI_Defeaturing d;
    d.SetShape(s);
    for (auto& f : fs) d.AddFaceToRemove(f);
    d.SetRunParallel(true);
    d.Build();
    if (!d.IsDone()) throw ToolError("delete face / heal failed", "remove a smaller connected set (whole blend chain, whole boss)");
    TopoDS_Shape r = geo::cast_solid(d.Shape());
    if (!geo::valid(r)) throw ToolError("healed body invalid", "the neighbours cannot extend to close the gap; delete more faces");
    return r;
}
OP(delete_face, false, "spec 1 Direct edit: delete face (heal)", "Delete faces, neighbours extend to close.") {
    std::string body = p["body"];
    Obj& o = m.get(body, {"solid"});
    auto fs = faces_of(m, body, p["faces"]);
    TopoDS_Shape r = defeature(o.shape, fs);
    json meta = o.meta;
    m.put(body, "solid", r, meta);
    return {{"name", body}, {"removed", fs.size()}, {"faces", geo::count(r, TopAbs_FACE)}};
}
OP(split, false, "spec 1 Cut or split by plane", "Split body by plane ({origin,normal}/cplane); keep both -> <prefix>_1..N, above/below replaces body.") {
    std::string body = p["body"];
    Obj& o = m.get(body, {"solid"});
    if (p.contains("curve") && !p["curve"].is_null()) throw ToolError("split by curve not ported to the C++ engine yet", "split by plane, or use the Python kit");
    double dg = geo::diag(o.shape);
    gp_Ax3 pl = m.plane(p.contains("plane") && !p["plane"].is_null() ? p["plane"] : J(p, "cplane"));
    TopoDS_Face tool = BRepBuilderAPI_MakeFace(gp_Pln(pl), -1.5 * dg * 3 / 2, 1.5 * dg * 3 / 2, -1.5 * dg * 3 / 2, 1.5 * dg * 3 / 2).Face();
    BRepAlgoAPI_Splitter sp;
    ShapeList a, t;
    a.Append(o.shape);
    t.Append(tool);
    sp.SetArguments(a);
    sp.SetTools(t);
    sp.SetRunParallel(true);
    sp.Build();
    if (!sp.IsDone()) throw ToolError("split failed", "tool must cross the body; nudge off coplanar faces");
    gp_Vec n(pl.Direction());
    auto sols = geo::subshapes(sp.Shape(), TopAbs_SOLID);
    std::stable_sort(sols.begin(), sols.end(), [&](auto& x, auto& y) { return gp_Vec(geo::center(x).XYZ()).Dot(n) < gp_Vec(geo::center(y).XYZ()).Dot(n); });
    if (sols.size() < 2) throw ToolError("split produced 1 piece", "the plane/curve must cross the body");
    std::string keep = S(p, "keep", "both");
    json meta = o.meta;
    if (keep == "above" || keep == "below") { m.put(body, "solid", keep == "above" ? sols.back() : sols.front(), meta); return {{"name", body}}; }
    std::string prefix = S(p, "prefix", body.c_str());
    json names = json::array();
    m.cur.objects.erase(body);
    for (size_t i = 0; i < sols.size(); ++i) { std::string nm = prefix + "_" + std::to_string(i + 1); m.put(nm, "solid", sols[i]); names.push_back(nm); }
    return {{"pieces", names}};
}
OP(tag, false, "spec 3 / 5.9: stable references re-resolved from geometry", "Store a named ref spec.") {
    Sel s = m.resolve(p["ref"]);
    m.cur.tags[p["tag"].get<std::string>()] = p["ref"];
    json r = {{"tag", p["tag"]}};
    if (s.whole) r["count"] = 1; else { json d = describe_items(s.items); r.update(d); }
    return r;
}

// ================================================================== pattern / transforms
OP(mirror, true, "spec 1 Mirror across a plane (keep, auto-union)", "Mirror body across plane; keep+union fuses; keep+!union copy `name`; keep=false replaces.") {
    std::string body = p["body"];
    Obj o = m.get(body);
    gp_Ax3 pl = m.plane(p.contains("plane") ? p["plane"] : json("YZ"));
    gp_Trsf t;
    t.SetMirror(gp_Ax2(pl.Location(), pl.Direction(), pl.XDirection()));
    TopoDS_Shape mir = xform(o.shape, t);
    if (!B(p, "keep", true)) { m.put(body, o.kind, mir, o.meta); return {{"name", body}}; }
    if (B(p, "union", true) && o.kind == "solid") { m.put(body, "solid", boolean_k("fuse", o.shape, {mir}), o.meta); return {{"name", body}}; }
    m.put(p["name"], o.kind, mir, {{"mirror_of", body}});
    return {{"name", p["name"]}};
}
static TopoDS_Shape combine(const TopoDS_Shape& base, const std::vector<TopoDS_Shape>& pcs, bool uni) {
    if (uni) return boolean_k("fuse", base, pcs);
    BRep_Builder b; TopoDS_Compound c; b.MakeCompound(c);
    b.Add(c, base);
    for (auto& x : pcs) b.Add(c, x);
    return c;
}
OP(linear_array, true, "spec 1 Rectangular arrays (count, spacing)", "count copies spaced by step (+ count2/step2); union -> fused body, else compound.") {
    std::string body = p["body"];
    Obj o = m.get(body);
    int c1 = p["count"], c2 = p.value("count2", 1);
    gp_Vec st = geo::vec(p["step"]), st2 = p.contains("step2") && !p["step2"].is_null() ? geo::vec(p["step2"]) : gp_Vec(0, 0, 0);
    std::vector<TopoDS_Shape> pcs;
    for (int j = 0; j < c2; ++j) for (int i = 0; i < c1; ++i) if (i || j) pcs.push_back(moved(o.shape, st * i + st2 * j));
    bool uni = B(p, "union");
    std::string nm = p["name"];
    m.put(nm, uni ? o.kind : "solid", combine(o.shape, pcs, uni), {{"array_of", body}, {"count", c1 * c2}});
    if (nm != body) m.cur.objects.erase(body);
    return {{"name", nm}, {"count", c1 * c2}};
}
OP(radial_array, true, "spec 1 Radial arrays (count, angle)", "count copies about axis over angle; union fuses.") {
    std::string body = p["body"];
    Obj o = m.get(body);
    int n = p["count"];
    double ang = D(p, "angle", 360);
    gp_Ax1 ax(p.contains("axis_origin") ? geo::pnt(p["axis_origin"]) : gp_Pnt(0, 0, 0), gp_Dir(geo::vec(p.contains("axis_dir") ? p["axis_dir"] : json("z"))));
    bool full = std::abs(ang - 360) < 1e-9;
    double da = ang / (full ? n : std::max(n - 1, 1));
    std::vector<TopoDS_Shape> pcs;
    for (int i = 1; i < n; ++i) { gp_Trsf t; t.SetRotation(ax, da * i * M_PI / 180); pcs.push_back(xform(o.shape, t)); }
    std::string nm = p["name"];
    m.put(nm, "solid", combine(o.shape, pcs, B(p, "union")), {{"array_of", body}, {"count", n}});
    if (nm != body) m.cur.objects.erase(body);
    return {{"name", nm}, {"count", n}};
}
OP(duplicate, true, "spec 1 Duplicate", "Copy source as name.") {
    Obj o = m.get(p["source"]);
    m.put(p["name"], o.kind, o.shape, o.meta);
    return {{"name", p["name"]}};
}
OP(move, false, "spec 1 Transforms: Move", "Translate obj by [dx,dy,dz].") {
    Obj& o = m.get(p["obj"]);
    o.shape = moved(o.shape, geo::vec(p["by"]));
    return {{"name", p["obj"]}};
}
static gp_Pnt bbox_center(const TopoDS_Shape& s) { Bnd_Box b = geo::bbox(s); return gp_Pnt((b.CornerMin().XYZ() + b.CornerMax().XYZ()) * 0.5); }
OP(rotate, false, "spec 1 Transforms: Rotate (pivot = point / bbox centre)", "Rotate obj about axis_dir through pivot by angle deg.") {
    Obj& o = m.get(p["obj"]);
    gp_Pnt pv = p.contains("pivot") && !p["pivot"].is_null() ? geo::pnt(p["pivot"]) : bbox_center(o.shape);
    gp_Trsf t;
    t.SetRotation(gp_Ax1(pv, gp_Dir(geo::vec(p["axis_dir"]))), D(p, "angle") * M_PI / 180);
    o.shape = xform(o.shape, t);
    return {{"name", p["obj"]}};
}
OP(scale, false, "spec 1 Transforms: Scale (uniform, pivot)", "Uniform scale about pivot / bbox centre.") {
    Obj& o = m.get(p["obj"]);
    gp_Pnt pv = p.contains("pivot") && !p["pivot"].is_null() ? geo::pnt(p["pivot"]) : bbox_center(o.shape);
    gp_Trsf t;
    t.SetScale(pv, D(p, "factor"));
    o.shape = xform(o.shape, t);
    return {{"name", p["obj"]}};
}
OP(delete, false, "utility: delete object", "Delete object.") {
    m.get(p["obj"]);
    m.cur.objects.erase(p["obj"].get<std::string>());
    return {{"deleted", p["obj"]}};
}

// ================================================================== STEP exchange
OP(import_step, true, "exchange: STEP import -> editable solids, tags per solid", "Import STEP path; one solid -> name, several -> name_1..N. units auto|mm|m (scale to metres if m).") {
    STEPControl_Reader rd;
    std::string path = p["path"];
    if (rd.ReadFile(path.c_str()) != IFSelect_RetDone) throw ToolError("cannot read STEP " + path);
    rd.TransferRoots();
    TopoDS_Shape s = rd.OneShape();
    std::string units = S(p, "units", "auto");
    if (units == "m") { gp_Trsf t; t.SetScale(gp_Pnt(0, 0, 0), 0.001); s = xform(s, t); }
    auto sols = geo::subshapes(s, TopAbs_SOLID);
    std::string nm = p["name"];
    json names = json::array();
    if (sols.size() == 1) { m.put(nm, "solid", sols[0], {{"source", path}}); names.push_back(nm); }
    else for (size_t i = 0; i < sols.size(); ++i) { std::string n2 = nm + "_" + std::to_string(i + 1); m.put(n2, "solid", sols[i], {{"source", path}}); names.push_back(n2); }
    if (sols.empty()) { m.put(nm, "sheet", s, {{"source", path}}); names.push_back(nm); }
    return {{"name", nm}, {"objects", names}};
}
OP(export_step, false, "exchange: write objects to STEP (AP214)", "Write objects (default all solids) to path.") {
    STEPControl_Writer wr;
    Interface_Static::SetCVal("write.step.schema", "AP214");
    Interface_Static::SetCVal("write.step.unit", S(p, "units", "mm") == "m" ? "M" : "MM");
    json objs = J(p, "objects");
    int n = 0;
    for (auto& [k, o] : m.cur.objects) {
        bool want = objs.is_array() ? std::find(objs.begin(), objs.end(), k) != objs.end() : (o.kind == "solid" || o.kind == "sheet");
        if (!want) continue;
        wr.Transfer(o.shape, STEPControl_AsIs);
        ++n;
    }
    if (!n) throw ToolError("nothing to export");
    std::string path = p["path"];
    if (wr.Write(path.c_str()) != IFSelect_RetDone) throw ToolError("STEP write failed: " + path);
    return {{"path", path}, {"objects", n}};
}

// test-only op (needs CADENGINE_DEBUG_OPS=1): runs the debug_crash kernel through the isolation path
OP(debug_crash, false, "test only: native crash / hang inside the isolated kernel child", "how segv|hang") {
    if (!std::getenv("CADENGINE_DEBUG_OPS")) throw ToolError("debug ops disabled", "set CADENGINE_DEBUG_OPS=1");
    json info;
    run_kernel("debug_crash", {}, {{"how", S(p, "how", "segv")}}, info);
    return json::object();
}
