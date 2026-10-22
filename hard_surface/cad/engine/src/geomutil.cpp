#include "common.hpp"

#include <BinTools.hxx>
#include <ShapeUpgrade_UnifySameDomain.hxx>
#include <GeomAbs_SurfaceType.hxx>
#include <GeomAbs_CurveType.hxx>

namespace geo {

gp_Vec vec(const json& v) {
    if (v.is_string()) {
        std::string s = v.get<std::string>();
        double sg = 1;
        while (!s.empty() && (s[0] == '+' || s[0] == '-')) { if (s[0] == '-') sg = -sg; s.erase(0, 1); }
        char c = s.empty() ? 'z' : (char)tolower(s[0]);
        if (c == 'x') return gp_Vec(sg, 0, 0);
        if (c == 'y') return gp_Vec(0, sg, 0);
        if (c == 'z') return gp_Vec(0, 0, sg);
        throw ToolError("bad axis '" + v.get<std::string>() + "'", "use x|y|z with optional sign or [x,y,z]");
    }
    if (!v.is_array() || v.size() < 2) throw ToolError("bad vector " + v.dump(), "use [x,y,z]");
    return gp_Vec(v[0].get<double>(), v[1].get<double>(), v.size() > 2 ? v[2].get<double>() : 0.0);
}

gp_Pnt pnt(const json& v) { gp_Vec x = vec(v); return gp_Pnt(x.X(), x.Y(), x.Z()); }

std::vector<TopoDS_Shape> subshapes(const TopoDS_Shape& s, TopAbs_ShapeEnum t) {
    ShapeMap m;
    TopExp::MapShapes(s, t, m);
    std::vector<TopoDS_Shape> out;
    out.reserve(m.Extent());
    for (int i = 1; i <= m.Extent(); ++i)
        if (t != TopAbs_EDGE || !BRep_Tool::Degenerated(TopoDS::Edge(m(i)))) out.push_back(m(i));  // build123d skips degenerate edges
    return out;
}

TopAbs_ShapeEnum kind_enum(const std::string& k) {
    if (k == "faces") return TopAbs_FACE;
    if (k == "edges") return TopAbs_EDGE;
    if (k == "vertices") return TopAbs_VERTEX;
    if (k == "solids") return TopAbs_SOLID;
    if (k == "wires") return TopAbs_WIRE;
    throw ToolError("bad sub-shape kind " + k);
}

static double edge_param_at(const BRepAdaptor_Curve& c, double t) {
    double len = GCPnts_AbscissaPoint::Length(c);
    GCPnts_AbscissaPoint ap(c, len * t, c.FirstParameter());
    return ap.Parameter();
}

gp_Pnt edge_point(const TopoDS_Edge& e, double t) {
    BRepAdaptor_Curve c(e);
    return c.Value(edge_param_at(c, t));
}

gp_Vec edge_tangent(const TopoDS_Edge& e, double t) {
    BRepAdaptor_Curve c(e);
    gp_Pnt p;
    gp_Vec d;
    c.D1(edge_param_at(c, t), p, d);
    if (d.Magnitude() > 1e-15) d.Normalize();
    return d;
}

gp_Pnt center(const TopoDS_Shape& s) {
    GProp_GProps g;
    switch (s.ShapeType()) {
        case TopAbs_VERTEX: return BRep_Tool::Pnt(TopoDS::Vertex(s));
        case TopAbs_EDGE: return edge_point(TopoDS::Edge(s), 0.5);
        case TopAbs_WIRE: BRepGProp::LinearProperties(s, g); return g.CentreOfMass();
        case TopAbs_FACE: {
            BRepAdaptor_Surface a(TopoDS::Face(s));
            if (a.GetType() == GeomAbs_Plane) { BRepGProp::SurfaceProperties(s, g); return g.CentreOfMass(); }
            double u0, u1, v0, v1;
            BRepTools::UVBounds(TopoDS::Face(s), u0, u1, v0, v1);
            gp_Pnt p; gp_Vec n;
            BRepGProp_Face(TopoDS::Face(s)).Normal(0.5 * (u0 + u1), 0.5 * (v0 + v1), p, n);
            return p;
        }
        case TopAbs_SHELL: BRepGProp::SurfaceProperties(s, g); return g.CentreOfMass();
        default: BRepGProp::VolumeProperties(s, g); return g.CentreOfMass();
    }
}

double volume(const TopoDS_Shape& s) { GProp_GProps g; BRepGProp::VolumeProperties(s, g); return g.Mass(); }
double area(const TopoDS_Shape& s) { GProp_GProps g; BRepGProp::SurfaceProperties(s, g); return g.Mass(); }
double length(const TopoDS_Shape& s) {
    if (s.ShapeType() == TopAbs_EDGE) { BRepAdaptor_Curve c(TopoDS::Edge(s)); return GCPnts_AbscissaPoint::Length(c); }
    GProp_GProps g; BRepGProp::LinearProperties(s, g); return g.Mass();
}

std::string geom_type(const TopoDS_Shape& s) {
    if (s.ShapeType() == TopAbs_FACE) {
        switch (BRepAdaptor_Surface(TopoDS::Face(s)).GetType()) {
            case GeomAbs_Plane: return "plane"; case GeomAbs_Cylinder: return "cylinder";
            case GeomAbs_Cone: return "cone"; case GeomAbs_Sphere: return "sphere"; case GeomAbs_Torus: return "torus";
            case GeomAbs_BezierSurface: return "bezier"; case GeomAbs_BSplineSurface: return "bspline";
            case GeomAbs_SurfaceOfRevolution: return "revolution"; case GeomAbs_SurfaceOfExtrusion: return "extrusion";
            case GeomAbs_OffsetSurface: return "offset"; default: return "other";
        }
    }
    if (s.ShapeType() == TopAbs_EDGE) {
        if (BRep_Tool::Degenerated(TopoDS::Edge(s))) return "degenerate";
        switch (BRepAdaptor_Curve(TopoDS::Edge(s)).GetType()) {
            case GeomAbs_Line: return "line"; case GeomAbs_Circle: return "circle"; case GeomAbs_Ellipse: return "ellipse";
            case GeomAbs_Hyperbola: return "hyperbola"; case GeomAbs_Parabola: return "parabola";
            case GeomAbs_BezierCurve: return "bezier"; case GeomAbs_BSplineCurve: return "bspline";
            case GeomAbs_OffsetCurve: return "offset"; default: return "other";
        }
    }
    return "";
}

bool face_normal(const TopoDS_Face& f, gp_Vec& n) {
    double u0, u1, v0, v1;
    BRepTools::UVBounds(f, u0, u1, v0, v1);
    gp_Pnt p;
    BRepGProp_Face(f).Normal(0.5 * (u0 + u1), 0.5 * (v0 + v1), p, n);
    if (n.Magnitude() < 1e-15) return false;
    n.Normalize();
    return true;
}

Bnd_Box bbox(const TopoDS_Shape& s) {
    Bnd_Box b;
    if (!s.IsNull()) BRepBndLib::AddOptimal(s, b, false, false);
    return b;
}
double diag(const TopoDS_Shape& s) {
    Bnd_Box b = bbox(s);
    if (b.IsVoid()) return 0;
    return b.CornerMin().Distance(b.CornerMax());
}
bool valid(const TopoDS_Shape& s) { return !s.IsNull() && BRepCheck_Analyzer(s).IsValid(); }
int count(const TopoDS_Shape& s, TopAbs_ShapeEnum t) { return (int)subshapes(s, t).size(); }

TopoDS_Shape clean(const TopoDS_Shape& s) {
    try {
        ShapeUpgrade_UnifySameDomain u(s, true, true, true);
        u.AllowInternalEdges(false);
        u.Build();
        return u.Shape();
    } catch (...) { return s; }
}

TopoDS_Shape cast_solid(const TopoDS_Shape& s) {
    auto sols = subshapes(s, TopAbs_SOLID);
    if (sols.size() == 1) return sols[0];
    if (sols.empty()) return s;
    BRep_Builder b; TopoDS_Compound c; b.MakeCompound(c);
    for (auto& x : sols) b.Add(c, x);
    return c;
}

double rnd(double v, int n) { double k = std::pow(10.0, n); double r = std::round(v * k) / k; return r == 0 ? 0.0 : r; }
json rnd(const gp_Pnt& p, int n) { return json::array({rnd(p.X(), n), rnd(p.Y(), n), rnd(p.Z(), n)}); }

gp_Ax3 plane_named(const std::string& nm, bool& ok) {
    ok = true;
    auto P = [](gp_Dir x, gp_Dir z) { return gp_Ax3(gp_Pnt(0, 0, 0), z, x); };
    if (nm == "XY" || nm == "top") return P(gp_Dir(1, 0, 0), gp_Dir(0, 0, 1));
    if (nm == "YZ" || nm == "right") return P(gp_Dir(0, 1, 0), gp_Dir(1, 0, 0));
    if (nm == "ZX") return P(gp_Dir(0, 0, 1), gp_Dir(0, 1, 0));
    if (nm == "XZ" || nm == "front") return P(gp_Dir(1, 0, 0), gp_Dir(0, -1, 0));
    if (nm == "YX") return P(gp_Dir(0, 1, 0), gp_Dir(0, 0, -1));
    if (nm == "ZY") return P(gp_Dir(0, 0, 1), gp_Dir(-1, 0, 0));
    ok = false;
    return gp_Ax3();
}

std::string brep_to_string(const TopoDS_Shape& s) {
    std::ostringstream os(std::ios::binary);
    BinTools::Write(s, os);
    return os.str();
}
TopoDS_Shape brep_from_string(const std::string& str) {
    std::istringstream is(str, std::ios::binary);
    TopoDS_Shape s;
    BinTools::Read(s, is);
    return s;
}

}  // namespace geo
