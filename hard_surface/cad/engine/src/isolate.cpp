// Crash/hang isolation for risky kernels: ONE persistent child (`cadengine --worker`, CREATE_NO_WINDOW), shapes
// passed as BinTools files in a private temp dir, JSON lines over pipes. A crash/timeout kills only that child
// (by handle, never by name); it restarts lazily on the next call. CADENGINE_ISOLATE=0 runs kernels in-process.
#include "model.hpp"

#include <windows.h>
#include <condition_variable>
#include <fstream>
#include <iostream>
#include <mutex>
#include <thread>

static json g_iso = {{"calls", 0}, {"crashes", 0}, {"timeouts", 0}, {"restarts", 0}, {"io_ms", 0.0}};

static bool isolation_on() {
    char buf[16];
    DWORD n = GetEnvironmentVariableA("CADENGINE_ISOLATE", buf, sizeof buf);
    return !(n > 0 && buf[0] == '0');
}
static double op_timeout_s() {
    char buf[32];
    DWORD n = GetEnvironmentVariableA("CADENGINE_OP_TIMEOUT", buf, sizeof buf);
    return n > 0 ? atof(buf) : 120.0;
}

static std::string tmpdir() {
    static std::string d;
    if (d.empty()) {
        char b[MAX_PATH];
        GetTempPathA(MAX_PATH, b);
        d = std::string(b) + "cadengine_" + std::to_string(GetCurrentProcessId());
        CreateDirectoryA(d.c_str(), nullptr);
    }
    return d;
}

static void write_file(const std::string& p, const std::string& s) { std::ofstream f(p, std::ios::binary); f.write(s.data(), s.size()); }
static std::string read_file(const std::string& p) { std::ifstream f(p, std::ios::binary); return std::string(std::istreambuf_iterator<char>(f), {}); }

struct Child {
    PROCESS_INFORMATION pi{};
    HANDLE in_w = nullptr, out_r = nullptr;
    std::string buf;
    bool alive() const { return pi.hProcess && WaitForSingleObject(pi.hProcess, 0) == WAIT_TIMEOUT; }
    void kill() {
        if (pi.hProcess) { TerminateProcess(pi.hProcess, 1); WaitForSingleObject(pi.hProcess, 5000); CloseHandle(pi.hProcess); CloseHandle(pi.hThread); }
        if (in_w) CloseHandle(in_w);
        if (out_r) CloseHandle(out_r);
        pi = {}; in_w = out_r = nullptr; buf.clear();
    }
    void start() {
        SECURITY_ATTRIBUTES sa{sizeof sa, nullptr, TRUE};
        HANDLE in_r, out_w;
        CreatePipe(&in_r, &in_w, &sa, 0);
        CreatePipe(&out_r, &out_w, &sa, 0);
        SetHandleInformation(in_w, HANDLE_FLAG_INHERIT, 0);
        SetHandleInformation(out_r, HANDLE_FLAG_INHERIT, 0);
        STARTUPINFOA si{sizeof si};
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = in_r;
        si.hStdOutput = out_w;
        si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
        char exe[MAX_PATH];
        GetModuleFileNameA(nullptr, exe, MAX_PATH);
        std::string cmd = std::string("\"") + exe + "\" --worker";
        if (!CreateProcessA(nullptr, cmd.data(), nullptr, nullptr, TRUE, CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi))
            throw ToolError("could not start isolation worker");
        CloseHandle(in_r);
        CloseHandle(out_w);
        g_iso["restarts"] = g_iso["restarts"].get<int>() + 1;
    }
    // read one line with timeout; returns false on timeout/EOF
    bool read_line(std::string& line, double timeout_s, bool& timed_out) {
        timed_out = false;
        double t_end = now_ms() + timeout_s * 1000;
        for (;;) {
            size_t nl = buf.find('\n');
            if (nl != std::string::npos) { line = buf.substr(0, nl); buf.erase(0, nl + 1); return true; }
            DWORD avail = 0;
            if (!PeekNamedPipe(out_r, nullptr, 0, nullptr, &avail, nullptr)) return false;  // EOF / child died
            if (avail) {
                std::string chunk(avail, '\0');
                DWORD got = 0;
                if (!ReadFile(out_r, chunk.data(), avail, &got, nullptr)) return false;
                buf.append(chunk.data(), got);
                continue;
            }
            if (!alive()) return false;
            if (now_ms() > t_end) { timed_out = true; return false; }
            Sleep(0);
            if (now_ms() + 1 < t_end) WaitForSingleObject(pi.hProcess, 1);
        }
    }
};

static Child g_child;
static int g_seq = 0;

TopoDS_Shape run_kernel(const std::string& name, const std::vector<TopoDS_Shape>& in, const json& params, json& info) {
    auto it = kernel_registry().find(name);
    if (it == kernel_registry().end()) throw ToolError("unknown kernel " + name);
    if (!isolation_on()) return it->second(in, params, info);
    g_iso["calls"] = g_iso["calls"].get<int>() + 1;
    double t0 = now_ms();
    if (!g_child.alive()) { g_child.kill(); g_child.start(); }
    std::string base = tmpdir() + "\\k" + std::to_string(++g_seq);
    json paths = json::array();
    for (size_t i = 0; i < in.size(); ++i) {
        std::string p = base + "_in" + std::to_string(i) + ".bin";
        write_file(p, geo::brep_to_string(in[i]));
        paths.push_back(p);
    }
    std::string outp = base + "_out.bin";
    std::string msg = json({{"k", name}, {"in", paths}, {"params", params}, {"out", outp}}).dump() + "\n";
    DWORD w;
    double t_io = now_ms() - t0;
    if (!WriteFile(g_child.in_w, msg.data(), (DWORD)msg.size(), &w, nullptr)) {
        g_child.kill();
        throw ToolError(name + ": isolation worker pipe broken (restarted)", "retry the op");
    }
    std::string line;
    bool to;
    bool got = g_child.read_line(line, op_timeout_s(), to);
    for (auto& p : paths) DeleteFileA(p.get<std::string>().c_str());
    if (!got) {
        DWORD code = 0;
        if (g_child.pi.hProcess) GetExitCodeProcess(g_child.pi.hProcess, &code);
        g_child.kill();
        g_iso[to ? "timeouts" : "crashes"] = g_iso[to ? "timeouts" : "crashes"].get<int>() + 1;
        std::ostringstream m;
        if (to) m << name << ": kernel worker timed out after " << op_timeout_s() << " s (killed only that child; engine state intact)";
        else m << name << ": OCCT kernel worker crashed (exit 0x" << std::hex << code << "); engine survived, worker restarts on next call";
        throw ToolError(m.str(), "journal unchanged. Change the op inputs (smaller radius / fewer edges / other profile).", {{"crashed", true}});
    }
    json rep = json::parse(line);
    if (!rep.value("ok", false)) {
        DeleteFileA(outp.c_str());
        throw ToolError(rep.value("error", "kernel failed"), rep.value("hint", ""), rep.value("data", json::object()));
    }
    double t1 = now_ms();
    TopoDS_Shape r = geo::brep_from_string(read_file(outp));
    DeleteFileA(outp.c_str());
    if (rep.contains("info")) for (auto& [k, v] : rep["info"].items()) info[k] = v;
    g_iso["io_ms"] = g_iso["io_ms"].get<double>() + t_io + (now_ms() - t1);
    return r;
}

json isolation_stats() { json j = g_iso; j["enabled"] = isolation_on(); return j; }

int worker_main() {
    std::string line;
    while (std::getline(std::cin, line)) {
        json rep;
        try {
            json msg = json::parse(line);
            std::vector<TopoDS_Shape> in;
            for (auto& p : msg["in"]) in.push_back(geo::brep_from_string(read_file(p.get<std::string>())));
            json info = json::object();
            TopoDS_Shape r = kernel_registry().at(msg["k"].get<std::string>())(in, msg["params"], info);
            write_file(msg["out"].get<std::string>(), geo::brep_to_string(r));
            rep = {{"ok", true}, {"info", info}};
        } catch (ToolError& e) {
            rep = e.as_json();
        } catch (Standard_Failure& e) {
            rep = {{"ok", false}, {"error", std::string("kernel: ") + (e.GetMessageString() ? e.GetMessageString() : "Standard_Failure")}};
        } catch (std::exception& e) {
            rep = {{"ok", false}, {"error", e.what()}};
        }
        std::cout << rep.dump() << "\n" << std::flush;
    }
    return 0;
}
