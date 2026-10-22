// cadengine: persistent CAD engine process. JSON-RPC 2.0-style lines over stdio:
//   -> {"id": 1, "method": "run", "params": {"session": "s", "op": "box", "params": {...}}}
//   <- {"id": 1, "result": {...}}  |  {"id": 1, "error": {"message", "hint", "data"}}
// `cadengine --worker` = isolated kernel child (isolate.cpp). `cadengine --bench journal.json` = timing harness.
#include "gpu.hpp"

#include <fcntl.h>
#include <io.h>
#include <fstream>
#include <iostream>

static std::map<std::string, Model> g_sess;

static Model& sess(const json& p) { return g_sess[p.value("session", std::string("default"))]; }

static json describe_ops() {
    json o = json::object();
    for (auto& [k, v] : op_registry()) o[k] = {{"spec", v.spec}, {"doc", v.doc}};
    return o;
}

static json measure(Model& m, const json& p) {
    Sel a = m.resolve(p.at("a"));
    auto props = [](const std::vector<TopoDS_Shape>& xs) {
        json arr = json::array();
        for (auto& s : xs) arr.push_back(desc(s));
        return arr;
    };
    std::vector<TopoDS_Shape> xs = a.whole ? std::vector<TopoDS_Shape>{a.shape} : a.items;
    json r = {{"a", props(xs)}};
    if (p.contains("b") && !p["b"].is_null()) {
        Sel b = m.resolve(p["b"]);
        std::vector<TopoDS_Shape> ys = b.whole ? std::vector<TopoDS_Shape>{b.shape} : b.items;
        gp_Pnt ca = geo::center(xs.at(0)), cb = geo::center(ys.at(0));
        r["b"] = props(ys);
        r["center_distance"] = geo::rnd(ca.Distance(cb), 7);
    }
    return r;
}

static json handle(const std::string& method, const json& p) {
    if (method == "ping") return {{"pong", true}, {"ops", op_registry().size()}};
    if (method == "describe_ops") return describe_ops();
    if (method == "new") { std::string s = p.value("session", std::string("default")); g_sess[s] = Model(); return {{"session", s}}; }
    if (method == "close") { g_sess.erase(p.value("session", std::string("default"))); return {{"closed", true}}; }
    Model& m = sess(p);
    if (method == "run") {
        double t0 = now_ms();
        json info = m.run(p.at("op"), p.value("params", json::object()));
        info["ms"] = geo::rnd(now_ms() - t0, 2);
        return info;
    }
    if (method == "undo") { m.undo(); return m.state(); }
    if (method == "redo") { m.redo(); return m.state(); }
    if (method == "checkout") { m.checkout(p.at("node").is_null() ? -1 : p["node"].get<int>()); return m.state(); }
    if (method == "set_param") return m.set_param(p.at("node"), p.at("key"), p.at("value"));
    if (method == "state") return m.state();
    if (method == "journal") return m.to_json();
    if (method == "load") {
        double t0 = now_ms();
        int ex0 = m.stats["ops_executed"];
        m.from_json(p.at("journal"));
        return {{"head", m.head}, {"nodes", m.nodes.size()}, {"replayed_ops", m.stats["ops_executed"].get<int>() - ex0}, {"ms", geo::rnd(now_ms() - t0, 2)}};
    }
    if (method == "select") {
        Sel s = m.resolve(p.at("ref"));
        return s.whole ? describe_items({s.shape}) : describe_items(s.items, p.value("n", 12));
    }
    if (method == "measure") return measure(m, p);
    if (method == "brep") {  // exact geometry of one object (BinTools file) for cross-checks
        std::string path = p.at("path");
        std::ofstream f(path, std::ios::binary);
        std::string s = geo::brep_to_string(m.get(p.at("obj")).shape);
        f.write(s.data(), s.size());
        return {{"path", path}, {"bytes", s.size()}};
    }
    if (method == "render") return gpu_render(m, p);
    if (method == "register_ref") return gpu_register_ref(p);
    if (method == "iou") return gpu_iou(m, p);
    if (method == "deviation") return gpu_deviation(m, p);
    if (method == "gpu_info") return gpu_info();
    if (method == "stats") return {{"model", m.stats}, {"cache_entries", m.cache.size()}, {"isolation", isolation_stats()}};
    throw ToolError("unknown method '" + method + "'", "ping|new|run|undo|redo|checkout|set_param|state|journal|load|select|measure|render|register_ref|iou|deviation|stats|describe_ops");
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--worker") return worker_main();
    // protocol gets a private copy of stdout; fd 1 -> stderr so OCCT/printf noise (STEP writer...) can't corrupt it
    int real = _dup(1);
    _dup2(2, 1);
    FILE* out = _fdopen(real, "wb");
    auto send = [&](const json& j) { std::string s = j.dump() + "\n"; fwrite(s.data(), 1, s.size(), out); fflush(out); };
    std::string line;
    send(json({{"ready", true}, {"engine", "cadengine 0.1"}, {"occt", OCC_VERSION_COMPLETE}}));
    while (std::getline(std::cin, line)) {
        if (line.empty()) continue;
        json rep;
        json id;
        try {
            json msg = json::parse(line);
            id = msg.value("id", json());
            std::string method = msg.at("method");
            if (method == "shutdown") { send(json({{"id", id}, {"result", {{"bye", true}}}})); break; }
            rep = {{"id", id}, {"result", handle(method, msg.value("params", json::object()))}};
        } catch (ToolError& e) {
            json err = {{"message", e.what()}, {"hint", e.hint}};
            if (!e.data.empty()) err["data"] = e.data;
            rep = {{"id", id}, {"error", err}};
        } catch (Standard_Failure& e) {
            rep = {{"id", id}, {"error", {{"message", std::string("kernel: ") + (e.GetMessageString() ? e.GetMessageString() : "Standard_Failure")}}}};
        } catch (std::exception& e) {
            rep = {{"id", id}, {"error", {{"message", e.what()}}}};
        }
        send(rep);
    }
    _exit(0);  // skip OCCT static teardown (cadkit TICKET T7)
}
