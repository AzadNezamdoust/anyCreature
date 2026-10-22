// cadengine - shared types. OpenCASCADE 8.0.x (LGPL-2.1 + exception, dynamically linked).
#pragma once
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include "json.hpp"

#include <BRepAdaptor_Curve.hxx>
#include <BRepAdaptor_Surface.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepBuilderAPI_GTransform.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepGProp.hxx>
#include <BRepGProp_Face.hxx>
#include <BRepTools.hxx>
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <Bnd_Box.hxx>
#include <GCPnts_AbscissaPoint.hxx>
#include <GProp_GProps.hxx>
#include <Standard_Failure.hxx>
#include <Standard_Version.hxx>
#include <TopAbs.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Wire.hxx>
#include <NCollection_IndexedMap.hxx>
#include <NCollection_List.hxx>
#include <TopTools_ShapeMapHasher.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Ax3.hxx>
#include <gp_Pln.hxx>
#include <gp_Pnt.hxx>
#include <gp_Trsf.hxx>
#include <gp_Vec.hxx>

using json = nlohmann::ordered_json;
using ShapeMap = NCollection_IndexedMap<TopoDS_Shape, TopTools_ShapeMapHasher>;
using ShapeList = NCollection_List<TopoDS_Shape>;

// Error with an LLM-actionable hint (same shape as cadkit.tools.ToolError.as_dict()).
struct ToolError : std::runtime_error {
    std::string hint;
    json data;
    ToolError(const std::string& m, const std::string& h = "", json d = json::object())
        : std::runtime_error(m), hint(h), data(std::move(d)) {}
    json as_json() const {
        json j = {{"ok", false}, {"error", what()}, {"hint", hint}};
        if (!data.empty()) j["data"] = data;
        return j;
    }
};

struct Obj {
    std::string kind;  // solid | curve | region | sheet
    TopoDS_Shape shape;
    json meta = json::object();
};

struct Snap {
    std::map<std::string, Obj> objects;
    json tags = json::object();
    std::map<std::string, gp_Ax3> cplanes;
};

inline double now_ms() {
    using namespace std::chrono;
    return duration<double, std::milli>(steady_clock::now().time_since_epoch()).count();
}

// ---------------------------------------------------------------- geometry helpers (geomutil.cpp)
namespace geo {
gp_Vec vec(const json& v);                 // "x" "-z" or [x,y,z]
gp_Pnt pnt(const json& v);
std::vector<TopoDS_Shape> subshapes(const TopoDS_Shape& s, TopAbs_ShapeEnum t);  // TopExp::MapShapes order
TopAbs_ShapeEnum kind_enum(const std::string& kind);
gp_Pnt center(const TopoDS_Shape& s);      // build123d semantics (edge: arc-length mid, face: planar mass / uv mid)
double volume(const TopoDS_Shape& s);
double area(const TopoDS_Shape& s);
double length(const TopoDS_Shape& s);
std::string geom_type(const TopoDS_Shape& s);
bool face_normal(const TopoDS_Face& f, gp_Vec& n);  // at center, honours orientation
gp_Pnt edge_point(const TopoDS_Edge& e, double t);  // t in 0..1 arc length
gp_Vec edge_tangent(const TopoDS_Edge& e, double t);
Bnd_Box bbox(const TopoDS_Shape& s);
double diag(const TopoDS_Shape& s);
bool valid(const TopoDS_Shape& s);
int count(const TopoDS_Shape& s, TopAbs_ShapeEnum t);
TopoDS_Shape clean(const TopoDS_Shape& s);   // ShapeUpgrade_UnifySameDomain (build123d clean())
TopoDS_Shape cast_solid(const TopoDS_Shape& s);  // 1 solid -> solid, n -> compound of solids
json rnd(const gp_Pnt& p, int n = 5);
double rnd(double v, int n);
gp_Ax3 plane_named(const std::string& name, bool& ok);
std::string brep_to_string(const TopoDS_Shape& s);
TopoDS_Shape brep_from_string(const std::string& s);
}  // namespace geo
