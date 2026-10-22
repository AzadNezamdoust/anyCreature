#pragma once
#include "common.hpp"

struct Model;
using OpFn = std::function<json(Model&, json&)>;
struct OpDef { OpFn fn; bool out; std::string spec; std::string doc; bool risky = false; };
std::map<std::string, OpDef>& op_registry();
struct OpReg { OpReg(const char* n, bool out, const char* spec, const char* doc, OpFn f, bool risky = false); };

// ---- kernel functions: pure shapes-in / shape-out, run in-process or in the isolated worker child
using KernelFn = std::function<TopoDS_Shape(const std::vector<TopoDS_Shape>&, const json&, json& info)>;
std::map<std::string, KernelFn>& kernel_registry();
struct KernelReg { KernelReg(const char* n, KernelFn f); };
// Runs kernel `name`; isolated child process with timeout when isolation is on (CADENGINE_ISOLATE != 0).
TopoDS_Shape run_kernel(const std::string& name, const std::vector<TopoDS_Shape>& in, const json& params, json& info);
int worker_main();                     // --worker entry
json isolation_stats();

struct Sel {                           // resolved ref: whole object shape or a list of sub-shapes
    bool whole = false;
    TopoDS_Shape shape;
    std::vector<TopoDS_Shape> items;
};

struct Node { int id; int parent; std::string op; json params; };

struct Model {
    std::vector<Node> nodes;
    int head = -1;
    Snap cur;
    // per-op result cache: chain key (hash of parent key + op + params) -> state after that op
    std::unordered_map<uint64_t, std::shared_ptr<Snap>> cache;
    std::vector<uint64_t> cache_order;
    size_t cache_cap = 2048;
    json stats = {{"ops_executed", 0}, {"cache_hits", 0}};
    json last_summary;                 // summary at head (diff base)

    json run(const std::string& op, json params);
    void checkout(int nid);
    void undo();
    void redo();
    json set_param(int nid, const std::string& key, const json& value);
    json to_json() const;
    void from_json(const json& j);
    json state() const;
    json summary() const;

    Obj& get(const std::string& name, std::initializer_list<const char*> kinds = {});
    void put(const std::string& name, const std::string& kind, const TopoDS_Shape& s, json meta = json::object());
    std::string autoname(const std::string& op) const;

    // refs
    Sel resolve(const json& ref, const std::string& want = "");
    std::vector<TopoDS_Shape> sub(const json& ref, const std::string& want);  // always a list
    gp_Ax3 plane(const json& p);

  private:
    std::vector<int> path(int nid) const;
    uint64_t key_of(int nid) const;
    void exec(const std::string& op, json& params, json* info);
    void cache_put(uint64_t k);
};

json diff_summary(const json& before, const json& after);
std::vector<TopoDS_Shape> tangent_chain(const TopoDS_Shape& shape, std::vector<TopoDS_Shape> seeds, double tol_deg = 2.0);
json describe_items(const std::vector<TopoDS_Shape>& items, size_t n = 12);
json desc(const TopoDS_Shape& s);
