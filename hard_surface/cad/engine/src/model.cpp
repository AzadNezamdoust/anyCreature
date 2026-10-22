// Model: journal tree, per-op result cache, state/diff, semantic refs (same JSON grammar as cadkit.tools.core).
#include "model.hpp"

std::map<std::string, OpDef>& op_registry() { static std::map<std::string, OpDef> r; return r; }
OpReg::OpReg(const char* n, bool out, const char* spec, const char* doc, OpFn f, bool risky) {
    op_registry()[n] = OpDef{std::move(f), out, spec, doc, risky};
}

static uint64_t fnv(const std::string& s, uint64_t h = 1469598103934665603ULL) {
    for (unsigned char c : s) { h ^= c; h *= 1099511628211ULL; }
    return h;
}

static std::string kernel_hint(const std::string& op) {
    if (op == "fillet" || op == "chamfer") return "radius too big for a neighbouring short edge/face: lower it or split the edge set (error data has max).";
    if (op == "boolean") return "nudge tools ~1e-4 off coplanar/tangent faces or simplify the tool.";
    if (op == "shell" || op == "offset_face" || op == "thicken") return "thickness bigger than the smallest local radius of curvature/fillet: shell before filleting or thin it.";
    if (op == "loft" || op == "sweep" || op == "pipe") return "profiles must be closed, same edge count helps loft; sweep path should be G1 with radius > profile size.";
    return "check the refs resolve to what you expect (use the select tool) and the params' units.";
}

// ------------------------------------------------------------------ objects
Obj& Model::get(const std::string& name, std::initializer_list<const char*> kinds) {
    auto it = cur.objects.find(name);
    if (it == cur.objects.end()) {
        json names = json::array();
        for (auto& [k, v] : cur.objects) names.push_back(k);
        throw ToolError("no object '" + name + "'", "objects: " + names.dump());
    }
    if (kinds.size()) {
        bool ok = false;
        for (auto k : kinds) ok |= it->second.kind == k;
        if (!ok) throw ToolError("'" + name + "' is a " + it->second.kind + ", need " + (*kinds.begin()));
    }
    return it->second;
}

void Model::put(const std::string& name, const std::string& kind, const TopoDS_Shape& s, json meta) {
    cur.objects[name] = Obj{kind, s, meta.is_null() ? json::object() : meta};
}

std::string Model::autoname(const std::string& op) const {
    for (int i = 1;; ++i) {
        std::string n = op + std::to_string(i);
        if (!cur.objects.count(n)) return n;
    }
}

// ------------------------------------------------------------------ journal
std::vector<int> Model::path(int nid) const {
    std::vector<int> out;
    while (nid >= 0) { out.push_back(nid); nid = nodes[nid].parent; }
    std::reverse(out.begin(), out.end());
    return out;
}

uint64_t Model::key_of(int nid) const {
    uint64_t h = 1469598103934665603ULL;
    for (int n : path(nid)) h = fnv(nodes[n].op + "\x1f" + nodes[n].params.dump(), h ^ 0x9e3779b97f4a7c15ULL);
    return h;
}

void Model::cache_put(uint64_t k) {
    if (!cache.count(k)) cache_order.push_back(k);
    cache[k] = std::make_shared<Snap>(cur);
    while (cache_order.size() > cache_cap) { cache.erase(cache_order.front()); cache_order.erase(cache_order.begin()); }
}

void Model::exec(const std::string& op, json& params, json* info) {
    auto& reg = op_registry();
    auto it = reg.find(op);
    if (it == reg.end()) {
        json names = json::array();
        for (auto& [k, v] : reg) names.push_back(k);
        throw ToolError("unknown op '" + op + "'", "known ops: " + names.dump());
    }
    Snap before = cur;
    try {
        json r = it->second.fn(*this, params);
        stats["ops_executed"] = stats["ops_executed"].get<int>() + 1;
        if (info) *info = r.is_null() ? json::object() : r;
    } catch (ToolError&) {
        cur = before;
        throw;
    } catch (json::exception& e) {
        cur = before;
        throw ToolError(op + ": bad params: " + e.what(), "see describe_ops['" + op + "']");
    } catch (Standard_Failure& e) {
        cur = before;
        throw ToolError(op + " failed: " + std::string("Standard_Failure: ") + (e.GetMessageString() ? e.GetMessageString() : ""), kernel_hint(op));
    } catch (std::exception& e) {
        cur = before;
        throw ToolError(op + " failed: " + e.what(), kernel_hint(op));
    }
}

json Model::run(const std::string& op, json params) {
    if (params.is_null()) params = json::object();
    auto it = op_registry().find(op);
    if (it != op_registry().end() && it->second.out && (!params.contains("name") || params["name"].is_null() || params["name"] == ""))
        params["name"] = autoname(op);
    json before = last_summary.is_null() ? json::object() : last_summary;
    json info;
    // per-op cache: same parent state + same op/params -> reuse
    int nid = (int)nodes.size();
    nodes.push_back({nid, head, op, params});
    uint64_t k = key_of(nid);
    auto c = cache.find(k);
    if (c != cache.end()) {
        cur = *c->second;
        info = json::object();
        stats["cache_hits"] = stats["cache_hits"].get<int>() + 1;
    } else {
        try { exec(op, params, &info); } catch (...) { nodes.pop_back(); throw; }
        cache_put(k);
    }
    head = nid;
    json after = summary();
    last_summary = after;
    info["node"] = nid;
    json d = diff_summary(before, after);
    if (!d.empty()) info["diff"] = d;
    return info;
}

void Model::checkout(int nid) {
    std::vector<int> p = nid >= 0 ? path(nid) : std::vector<int>{};
    // nearest cached state along the path
    int start = 0;
    cur = Snap();
    std::vector<uint64_t> keys(p.size());
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < p.size(); ++i) {
        h = fnv(nodes[p[i]].op + "\x1f" + nodes[p[i]].params.dump(), h ^ 0x9e3779b97f4a7c15ULL);
        keys[i] = h;
    }
    for (int i = (int)p.size() - 1; i >= 0; --i) {
        auto c = cache.find(keys[i]);
        if (c != cache.end()) { cur = *c->second; start = i + 1; stats["cache_hits"] = stats["cache_hits"].get<int>() + 1; break; }
    }
    for (size_t i = start; i < p.size(); ++i) {
        exec(nodes[p[i]].op, nodes[p[i]].params, nullptr);
        cache_put(keys[i]);
    }
    head = nid;
    last_summary = summary();
}

void Model::undo() {
    if (head < 0) throw ToolError("nothing to undo");
    checkout(nodes[head].parent);
}

void Model::redo() {
    int kid = -1;
    for (auto& n : nodes) if (n.parent == head) kid = n.id;
    if (kid < 0) throw ToolError("nothing to redo");
    checkout(kid);
}

json Model::set_param(int nid, const std::string& key, const json& value) {
    if (nid < 0 || nid >= (int)nodes.size()) throw ToolError("no node " + std::to_string(nid));
    json before = last_summary;
    json& P = nodes[nid].params;
    bool had = P.contains(key);
    json old = had ? P[key] : json();
    P[key] = value;
    double t0 = now_ms();
    int ex0 = stats["ops_executed"].get<int>();
    try {
        checkout(head);
    } catch (ToolError& e) {
        if (had) P[key] = old; else P.erase(key);
        checkout(head);
        throw ToolError("set_param node " + std::to_string(nid) + " " + key + "=" + value.dump() + " broke replay: " + e.what(), e.hint, e.data);
    }
    json r = {{"node", nid}, {"replayed_ops", stats["ops_executed"].get<int>() - ex0}, {"ms", geo::rnd(now_ms() - t0, 2)}};
    json d = diff_summary(before, last_summary);
    if (!d.empty()) r["diff"] = d;
    return r;
}

json Model::to_json() const {
    json ns = json::array();
    for (auto& n : nodes) ns.push_back({{"id", n.id}, {"parent", n.parent < 0 ? json() : json(n.parent)}, {"op", n.op}, {"params", n.params}});
    return {{"version", 1}, {"nodes", ns}, {"head", head < 0 ? json() : json(head)}};
}

void Model::from_json(const json& j) {
    nodes.clear();
    for (auto& n : j.at("nodes")) nodes.push_back({n.at("id").get<int>(), n["parent"].is_null() ? -1 : n["parent"].get<int>(), n.at("op").get<std::string>(), n.value("params", json::object())});
    checkout(j.contains("head") && !j["head"].is_null() ? j["head"].get<int>() : -1);
}

// ------------------------------------------------------------------ state / summary / diff
static json obj_summary(const Obj& o, bool full) {
    json d = {{"kind", o.kind}};
    try {
        Bnd_Box b = geo::bbox(o.shape);
        if (!b.IsVoid()) d["bbox"] = json::array({geo::rnd(b.CornerMin(), 5), geo::rnd(b.CornerMax(), 5)});
        if (o.kind == "solid") {
            d["volume"] = geo::rnd(geo::volume(o.shape), 9);
            d["faces"] = geo::count(o.shape, TopAbs_FACE);
            d["edges"] = geo::count(o.shape, TopAbs_EDGE);
            if (full) d["valid"] = geo::valid(o.shape);
        } else if (o.kind == "region" || o.kind == "sheet") {
            d["area"] = geo::rnd(geo::area(o.shape), 9);
            d["faces"] = geo::count(o.shape, TopAbs_FACE);
        } else if (o.kind == "curve") {
            d["length"] = geo::rnd(geo::length(o.shape), 6);
            if (full) d["closed"] = o.shape.ShapeType() == TopAbs_WIRE ? (bool)BRep_Tool::IsClosed(o.shape) : false;
        }
    } catch (Standard_Failure& e) {
        d["error"] = std::string(e.GetMessageString() ? e.GetMessageString() : "kernel error").substr(0, 120);
    }
    if (full)
        for (auto& [k, v] : o.meta.items())
            if (!k.empty() && k[0] != '_' && (v.is_string() || v.is_number() || v.is_boolean() || v.is_array())) d[k] = v;
    return d;
}

// per-shape summary cache: unchanged objects (same TShape + location + orientation) are not re-measured
struct ShapeEq { bool operator()(const TopoDS_Shape& a, const TopoDS_Shape& b) const { return a.IsEqual(b); } };
static std::unordered_map<TopoDS_Shape, json, std::hash<TopoDS_Shape>, ShapeEq> g_sum;

json Model::summary() const {
    json out = json::object();
    for (auto& [k, o] : cur.objects) {
        auto it = g_sum.find(o.shape);
        if (it != g_sum.end() && it->second["kind"] == o.kind) { out[k] = it->second; continue; }
        if (g_sum.size() > 20000) g_sum.clear();
        out[k] = g_sum[o.shape] = obj_summary(o, false);
    }
    return out;
}

json Model::state() const {
    json objs = json::object();
    for (auto& [k, o] : cur.objects) objs[k] = obj_summary(o, true);
    json cps = json::array();
    for (auto& [k, v] : cur.cplanes) cps.push_back(k);
    return {{"head", head < 0 ? json() : json(head)}, {"nodes", nodes.size()}, {"objects", objs}, {"tags", cur.tags}, {"cplanes", cps}};
}

json diff_summary(const json& before, const json& after) {
    json res = json::object(), added = json::object(), removed = json::array(), changed = json::object();
    for (auto& [k, v] : after.items()) if (!before.contains(k)) added[k] = v;
    for (auto& [k, v] : before.items()) if (!after.contains(k)) removed.push_back(k);
    for (auto& [k, v] : after.items()) {
        if (!before.contains(k) || before[k] == v) continue;
        json ch = json::object();
        for (auto& [f, b] : v.items()) {
            json a = before[k].contains(f) ? before[k][f] : json();
            if (a == b) continue;
            if (b.is_number() && a.is_number()) ch[f] = {{"from", a}, {"to", b}, {"delta", geo::rnd(b.get<double>() - a.get<double>(), 9)}};
            else ch[f] = json::array({a, b});
        }
        changed[k] = ch;
    }
    if (!added.empty()) res["added"] = added;
    if (!removed.empty()) res["removed"] = removed;
    if (!changed.empty()) res["changed"] = changed;
    return res;
}

// ------------------------------------------------------------------ refs / selection
gp_Ax3 Model::plane(const json& p) {
    if (p.is_null()) { bool ok; return geo::plane_named("XY", ok); }
    if (p.is_string()) {
        bool ok;
        std::string s = p.get<std::string>();
        gp_Ax3 a = geo::plane_named(s, ok);
        if (ok) return a;
        auto it = cur.cplanes.find(s);
        if (it != cur.cplanes.end()) return it->second;
        throw ToolError("no cplane '" + s + "'", "XY/XZ/YZ or a cplane name");
    }
    gp_Pnt o = p.contains("origin") ? geo::pnt(p["origin"]) : gp_Pnt(0, 0, 0);
    gp_Vec n = geo::vec(p.value("normal", json("z")));
    if (p.contains("x_dir") && !p["x_dir"].is_null()) return gp_Ax3(o, gp_Dir(n), gp_Dir(geo::vec(p["x_dir"])));
    return gp_Ax3(o, gp_Dir(n));
}

static bool same_in(const std::vector<TopoDS_Shape>& v, const TopoDS_Shape& s) {
    for (auto& x : v) if (x.IsSame(s)) return true;
    return false;
}

static std::vector<TopoDS_Shape> dedupe(const std::vector<TopoDS_Shape>& in) {
    std::vector<TopoDS_Shape> out;
    for (auto& s : in) if (!same_in(out, s)) out.push_back(s);
    return out;
}

// map sub-shapes (maybe from an older revision) onto `shape` by IsSame, then by centre match (<1e-5)
static std::vector<TopoDS_Shape> map_into(const TopoDS_Shape& shape, TopAbs_ShapeEnum t, const std::vector<TopoDS_Shape>& base) {
    auto cur = geo::subshapes(shape, t);
    std::vector<gp_Pnt> cc;
    std::vector<TopoDS_Shape> out;
    for (auto& b : base) {
        const TopoDS_Shape* hit = nullptr;
        for (auto& c : cur) if (c.IsSame(b)) { hit = &c; break; }
        if (!hit) {
            if (cc.empty()) for (auto& c : cur) cc.push_back(geo::center(c));
            gp_Pnt bc = geo::center(b);
            double best = 1e300; size_t bi = 0;
            for (size_t i = 0; i < cur.size(); ++i) { double d = cc[i].Distance(bc); if (d < best) { best = d; bi = i; } }
            if (best < 1e-5) hit = &cur[bi];
        }
        if (hit && !same_in(out, *hit)) out.push_back(*hit);
    }
    return out;
}

static bool tangent_join(const TopoDS_Edge& a, const TopoDS_Edge& b, double ctol) {
    for (double ta : {0.0, 1.0}) {
        gp_Pnt pa = geo::edge_point(a, ta);
        for (double tb : {0.0, 1.0})
            if (pa.Distance(geo::edge_point(b, tb)) < 1e-6) {
                if (std::abs(geo::edge_tangent(a, ta).Dot(geo::edge_tangent(b, tb))) >= ctol) return true;
            }
    }
    return false;
}

std::vector<TopoDS_Shape> tangent_chain(const TopoDS_Shape& shape, std::vector<TopoDS_Shape> seeds, double tol_deg) {
    auto edges = geo::subshapes(shape, TopAbs_EDGE);
    auto chain = dedupe(seeds);
    double ctol = std::cos(tol_deg * M_PI / 180.0);
    bool grew = true;
    while (grew) {
        grew = false;
        for (auto& e : edges) {
            if (same_in(chain, e) || BRep_Tool::Degenerated(TopoDS::Edge(e))) continue;
            for (size_t i = 0; i < chain.size(); ++i)
                if (tangent_join(TopoDS::Edge(chain[i]), TopoDS::Edge(e), ctol)) { chain.push_back(e); grew = true; break; }
        }
    }
    return chain;
}

json desc(const TopoDS_Shape& s) {
    static const char* names[] = {"Compound", "CompSolid", "Solid", "Shell", "Face", "Wire", "Edge", "Vertex", "Shape"};
    json d = {{"type", names[s.ShapeType()]}, {"center", geo::rnd(geo::center(s), 5)}};
    std::string g = geo::geom_type(s);
    if (!g.empty()) d["geom"] = g;
    if (s.ShapeType() == TopAbs_FACE) {
        d["area"] = geo::rnd(geo::area(s), 8);
        gp_Vec n;
        if (g == "plane" && geo::face_normal(TopoDS::Face(s), n)) d["normal"] = json::array({geo::rnd(n.X(), 4), geo::rnd(n.Y(), 4), geo::rnd(n.Z(), 4)});
    } else if (s.ShapeType() == TopAbs_EDGE) {
        d["length"] = geo::rnd(geo::length(s), 6);
    }
    return d;
}

json describe_items(const std::vector<TopoDS_Shape>& items, size_t n) {
    json arr = json::array();
    for (size_t i = 0; i < items.size() && i < n; ++i) arr.push_back(desc(items[i]));
    return {{"count", items.size()}, {"items", arr}};
}

static std::vector<TopoDS_Shape> select(Model& m, const TopoDS_Shape& shape, const std::string& kind, const json& flt);

Sel Model::resolve(const json& ref, const std::string& want) {
    Sel r;
    if (ref.is_string()) {
        std::string s = ref.get<std::string>();
        if (cur.tags.contains(s) && !cur.objects.count(s)) return resolve(cur.tags[s], want);
        Obj& o = get(s);
        if (!want.empty()) { r.items = geo::subshapes(o.shape, geo::kind_enum(want)); return r; }
        r.whole = true; r.shape = o.shape; return r;
    }
    if (!ref.is_object() || !ref.contains("obj")) {
        if (ref.is_object() && ref.contains("tag") && ref.size() == 1) {
            std::string t = ref["tag"].get<std::string>();
            if (!cur.tags.contains(t)) throw ToolError("no tag '" + t + "'");
            return resolve(cur.tags[t], want);
        }
        throw ToolError("bad ref " + ref.dump(), "use \"name\" or {\"obj\": name, \"faces\"|\"edges\"|\"vertices\": {filter}}");
    }
    TopoDS_Shape shape = get(ref["obj"].get<std::string>()).shape;
    std::string kind;
    for (const char* k : {"faces", "edges", "vertices", "solids", "wires"}) if (ref.contains(k)) { kind = k; break; }
    if (kind.empty()) {
        if (!want.empty()) { r.items = geo::subshapes(shape, geo::kind_enum(want)); return r; }
        r.whole = true; r.shape = shape; return r;
    }
    json flt = ref[kind].is_null() ? json::object() : ref[kind];
    auto items = select(*this, shape, kind, flt);
    if (!want.empty() && want != kind) {
        std::vector<TopoDS_Shape> x;
        for (auto& it : items) for (auto& s : geo::subshapes(it, geo::kind_enum(want))) x.push_back(s);
        items = dedupe(x);
    }
    r.items = items;
    return r;
}

std::vector<TopoDS_Shape> Model::sub(const json& ref, const std::string& want) {
    Sel s = resolve(ref, want);
    if (s.whole) return geo::subshapes(s.shape, geo::kind_enum(want));
    return s.items;
}

static double sort_key(const TopoDS_Shape& s, const std::string& kind) {
    if (kind == "faces") return geo::area(s);
    if (kind == "edges") return geo::length(s);
    return geo::volume(s);
}

static std::vector<TopoDS_Shape> select(Model& m, const TopoDS_Shape& shape, const std::string& kind, const json& flt) {
    TopAbs_ShapeEnum T = geo::kind_enum(kind);
    std::vector<TopoDS_Shape> items;
    if (flt.contains("tag")) {
        std::string t = flt["tag"].get<std::string>();
        if (!m.cur.tags.contains(t)) throw ToolError("no tag '" + t + "'");
        Sel b = m.resolve(m.cur.tags[t]);
        auto base = b.whole ? geo::subshapes(b.shape, T) : b.items;
        items = map_into(shape, T, base);
    } else if (flt.contains("of_faces") && (kind == "edges" || kind == "vertices")) {
        auto faces = select(m, shape, "faces", flt["of_faces"]);
        std::string loop = flt.value("loop", "all");
        std::vector<TopoDS_Shape> x;
        for (auto& f : faces) {
            TopoDS_Wire ow = BRepTools::OuterWire(TopoDS::Face(f));
            for (auto& w : geo::subshapes(f, TopAbs_WIRE)) {
                bool outer = w.IsSame(ow);
                if (loop == "outer" && !outer) continue;
                if (loop == "inner" && outer) continue;
                for (auto& s : geo::subshapes(w, T)) x.push_back(s);
            }
        }
        items = map_into(shape, T, dedupe(x));
    } else {
        items = geo::subshapes(shape, T);
    }
    auto keep = [&](auto pred) { std::vector<TopoDS_Shape> o; for (auto& s : items) if (pred(s)) o.push_back(s); items.swap(o); };
    if (flt.contains("geom")) { std::string g = flt["geom"].get<std::string>(); keep([&](auto& s) { return geo::geom_type(s) == g; }); }
    if (flt.contains("normal")) {
        gp_Vec n = geo::vec(flt["normal"]).Normalized();
        double tol = flt.value("angle_tol", 5.0) * M_PI / 180.0;
        keep([&](auto& s) {
            if (s.ShapeType() != TopAbs_FACE || geo::geom_type(s) != "plane") return false;
            gp_Vec fn;
            return geo::face_normal(TopoDS::Face(s), fn) && fn.Angle(n) <= tol + 1e-12;
        });
    }
    if (flt.contains("parallel")) {
        gp_Vec a = geo::vec(flt["parallel"]).Normalized();
        keep([&](auto& s) {
            if (s.ShapeType() != TopAbs_EDGE || geo::geom_type(s) != "line") return false;
            gp_Vec d(geo::edge_point(TopoDS::Edge(s), 0), geo::edge_point(TopoDS::Edge(s), 1));
            if (d.Magnitude() < 1e-15) return false;
            return std::abs(std::abs(d.Normalized().Dot(a)) - 1) < 1e-4;
        });
    }
    if (flt.contains("longer")) { double L = flt["longer"]; keep([&](auto& s) { return geo::length(s) >= L; }); }
    if (flt.contains("shorter")) { double L = flt["shorter"]; keep([&](auto& s) { return geo::length(s) <= L; }); }
    if (flt.contains("within")) {
        gp_Pnt lo = geo::pnt(flt["within"][0]), hi = geo::pnt(flt["within"][1]);
        keep([&](auto& s) {
            gp_Pnt c = geo::center(s);
            return c.X() >= lo.X() - 1e-7 && c.X() <= hi.X() + 1e-7 && c.Y() >= lo.Y() - 1e-7 && c.Y() <= hi.Y() + 1e-7 &&
                   c.Z() >= lo.Z() - 1e-7 && c.Z() <= hi.Z() + 1e-7;
        });
    }
    if (flt.contains("near")) {
        gp_Pnt p = geo::pnt(flt["near"]);
        if (flt.contains("radius")) { double r = flt["radius"]; keep([&](auto& s) { return geo::center(s).Distance(p) <= r; }); }
        else if (!items.empty()) {
            std::vector<std::pair<double, size_t>> d;
            for (size_t i = 0; i < items.size(); ++i) d.push_back({geo::center(items[i]).Distance(p), i});
            std::stable_sort(d.begin(), d.end(), [](auto& a, auto& b) { return a.first < b.first; });
            items = {items[d[0].second]};
        }
    }
    if (flt.contains("pick") && !items.empty()) {
        std::string pk = flt["pick"];
        if (pk == "largest" || pk == "smallest") {
            std::vector<std::pair<double, size_t>> d;
            for (size_t i = 0; i < items.size(); ++i) d.push_back({sort_key(items[i], kind), i});
            std::stable_sort(d.begin(), d.end(), [](auto& a, auto& b) { return a.first < b.first; });
            items = {items[(pk == "largest" ? d.back() : d.front()).second]};
        } else {
            gp_Vec ax = geo::vec(flt.value("axis", json("z")));
            std::vector<double> v;
            for (auto& s : items) { gp_Pnt c = geo::center(s); v.push_back(gp_Vec(c.XYZ()).Dot(ax)); }
            double tgt = pk == "max" ? *std::max_element(v.begin(), v.end()) : *std::min_element(v.begin(), v.end());
            double tol = flt.value("tol", 1e-6);
            std::vector<TopoDS_Shape> o;
            for (size_t i = 0; i < items.size(); ++i) if (std::abs(v[i] - tgt) < tol) o.push_back(items[i]);
            items.swap(o);
        }
    }
    if (flt.value("tangent_chain", false) && kind == "edges") items = tangent_chain(shape, items);
    if (flt.contains("first")) { size_t n = flt["first"]; if (items.size() > n) items.resize(n); }
    if (flt.contains("expect") && (int)items.size() != flt["expect"].get<int>()) {
        json mt = json::array();
        for (size_t i = 0; i < items.size() && i < 6; ++i) mt.push_back(desc(items[i]));
        throw ToolError("ref matched " + std::to_string(items.size()) + " " + kind + ", expected " + flt["expect"].dump(), "loosen/tighten the filter", {{"matched", mt}});
    }
    return items;
}
