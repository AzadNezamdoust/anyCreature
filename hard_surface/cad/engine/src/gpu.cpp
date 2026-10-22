// GPU layer: tessellate -> GPU buffers; offscreen multi-view sheets (clay / zebra / curvature / deviation),
// silhouette IoU vs registered reference images (compute shader, atomic counters), deviation heatmap (compute shader
// point->triangle distance). OpenGL 4.5 via a hidden WGL window (no visible window; runs on GTX 10xx / RTX 2070M).
#include <windows.h>
#include <GL/gl.h>
#include "gpu.hpp"

#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepLib_ToolTriangulatedShape.hxx>
#include <Poly_Triangulation.hxx>

#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_ONLY_JPEG
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

// ------------------------------------------------------------------ minimal GL 4.5 loader
typedef char GLchar;
typedef ptrdiff_t GLsizeiptr;
typedef ptrdiff_t GLintptr;
#define GL_ARRAY_BUFFER 0x8892
#define GL_ELEMENT_ARRAY_BUFFER 0x8893
#define GL_STATIC_DRAW 0x88E4
#define GL_DYNAMIC_DRAW 0x88E8
#define GL_DYNAMIC_READ 0x88E9
#define GL_FRAGMENT_SHADER 0x8B30
#define GL_VERTEX_SHADER 0x8B31
#define GL_COMPUTE_SHADER 0x91B9
#define GL_COMPILE_STATUS 0x8B81
#define GL_LINK_STATUS 0x8B82
#define GL_FRAMEBUFFER 0x8D40
#define GL_READ_FRAMEBUFFER 0x8CA8
#define GL_DRAW_FRAMEBUFFER 0x8CA9
#define GL_RENDERBUFFER 0x8D41
#define GL_COLOR_ATTACHMENT0 0x8CE0
#define GL_DEPTH_ATTACHMENT 0x8D00
#define GL_DEPTH_COMPONENT24 0x81A6
#define GL_FRAMEBUFFER_COMPLETE 0x8CD5
#define GL_SHADER_STORAGE_BUFFER 0x90D2
#define GL_ALL_BARRIER_BITS 0xFFFFFFFF
#define GL_RGBA8 0x8058
#define GL_R8 0x8229
#define GL_RED 0x1903
#define GL_READ_ONLY 0x88B8
#define GL_MULTISAMPLE 0x809D

#define GLFUNCS(X) \
    X(GLuint, glCreateShader, (GLenum)) X(void, glShaderSource, (GLuint, GLsizei, const GLchar* const*, const GLint*)) \
    X(void, glCompileShader, (GLuint)) X(void, glGetShaderiv, (GLuint, GLenum, GLint*)) \
    X(void, glGetShaderInfoLog, (GLuint, GLsizei, GLsizei*, GLchar*)) X(GLuint, glCreateProgram, ()) \
    X(void, glAttachShader, (GLuint, GLuint)) X(void, glLinkProgram, (GLuint)) X(void, glGetProgramiv, (GLuint, GLenum, GLint*)) \
    X(void, glGetProgramInfoLog, (GLuint, GLsizei, GLsizei*, GLchar*)) X(void, glUseProgram, (GLuint)) \
    X(GLint, glGetUniformLocation, (GLuint, const GLchar*)) X(void, glUniformMatrix4fv, (GLint, GLsizei, GLboolean, const GLfloat*)) \
    X(void, glUniformMatrix3fv, (GLint, GLsizei, GLboolean, const GLfloat*)) X(void, glUniform1i, (GLint, GLint)) \
    X(void, glUniform1f, (GLint, GLfloat)) X(void, glUniform2f, (GLint, GLfloat, GLfloat)) X(void, glUniform3f, (GLint, GLfloat, GLfloat, GLfloat)) \
    X(void, glUniform1ui, (GLint, GLuint)) \
    X(void, glGenVertexArrays, (GLsizei, GLuint*)) X(void, glBindVertexArray, (GLuint)) X(void, glDeleteVertexArrays, (GLsizei, const GLuint*)) \
    X(void, glGenBuffers, (GLsizei, GLuint*)) X(void, glBindBuffer, (GLenum, GLuint)) X(void, glDeleteBuffers, (GLsizei, const GLuint*)) \
    X(void, glBufferData, (GLenum, GLsizeiptr, const void*, GLenum)) X(void, glBufferSubData, (GLenum, GLintptr, GLsizeiptr, const void*)) \
    X(void, glGetBufferSubData, (GLenum, GLintptr, GLsizeiptr, void*)) \
    X(void, glVertexAttribPointer, (GLuint, GLint, GLenum, GLboolean, GLsizei, const void*)) X(void, glEnableVertexAttribArray, (GLuint)) \
    X(void, glGenFramebuffers, (GLsizei, GLuint*)) X(void, glBindFramebuffer, (GLenum, GLuint)) X(void, glDeleteFramebuffers, (GLsizei, const GLuint*)) \
    X(void, glFramebufferTexture2D, (GLenum, GLenum, GLenum, GLuint, GLint)) X(void, glGenRenderbuffers, (GLsizei, GLuint*)) \
    X(void, glBindRenderbuffer, (GLenum, GLuint)) X(void, glDeleteRenderbuffers, (GLsizei, const GLuint*)) \
    X(void, glRenderbufferStorageMultisample, (GLenum, GLsizei, GLenum, GLsizei, GLsizei)) \
    X(void, glFramebufferRenderbuffer, (GLenum, GLenum, GLenum, GLuint)) X(GLenum, glCheckFramebufferStatus, (GLenum)) \
    X(void, glBlitFramebuffer, (GLint, GLint, GLint, GLint, GLint, GLint, GLint, GLint, GLbitfield, GLenum)) \
    X(void, glBindBufferBase, (GLenum, GLuint, GLuint)) X(void, glDispatchCompute, (GLuint, GLuint, GLuint)) \
    X(void, glMemoryBarrier, (GLbitfield)) X(void, glBindImageTexture, (GLuint, GLuint, GLint, GLboolean, GLint, GLenum, GLenum)) \
    X(void, glTexStorage2D, (GLenum, GLsizei, GLenum, GLsizei, GLsizei)) X(void, glActiveTexture, (GLenum))

#define DECL(ret, name, args) typedef ret(APIENTRY* PFN_##name) args; static PFN_##name name;
GLFUNCS(DECL)
#undef DECL

static HWND g_wnd;
static HDC g_dc;
static HGLRC g_rc;
static std::string g_renderer;
static GLuint g_prog = 0, g_iou = 0, g_dev = 0;

static GLuint compile(GLenum t, const char* src) {
    GLuint s = glCreateShader(t);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    GLint ok;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char log[4096]; glGetShaderInfoLog(s, 4096, nullptr, log); throw ToolError(std::string("shader: ") + log); }
    return s;
}
static GLuint link(std::initializer_list<GLuint> sh) {
    GLuint p = glCreateProgram();
    for (auto s : sh) glAttachShader(p, s);
    glLinkProgram(p);
    GLint ok;
    glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) { char log[4096]; glGetProgramInfoLog(p, 4096, nullptr, log); throw ToolError(std::string("link: ") + log); }
    return p;
}

static const char* VS = R"(#version 450
layout(location=0) in vec3 p; layout(location=1) in vec3 n; layout(location=2) in float s;
uniform mat4 M; uniform mat3 R;
out vec3 vn; out vec3 vw; out float vs;
void main(){ gl_Position = M * vec4(p, 1.0); vn = R * n; vw = p; vs = s; })";
static const char* FS = R"(#version 450
uniform int mode; uniform vec3 col; uniform float stripes; uniform vec2 srange; uniform float kscale;
in vec3 vn; in vec3 vw; in float vs; out vec4 o;
vec3 ramp(float t){ t = clamp(t, 0.0, 1.0); return clamp(vec3(1.5 - abs(4.0*t - 3.0), 1.5 - abs(4.0*t - 2.0), 1.5 - abs(4.0*t - 1.0)), 0.0, 1.0); }
void main(){
  vec3 N = normalize(vn); if (!gl_FrontFacing) N = -N;
  if (mode == 3) { o = vec4(1.0); return; }
  if (mode == 1) { vec3 r = reflect(vec3(0,0,-1), N);
    float s = smoothstep(-0.08, 0.08, sin(stripes * asin(clamp(r.y, -1.0, 1.0)))); o = vec4(vec3(0.08 + 0.86*s), 1.0); return; }
  float d = 0.18 + 0.62*max(dot(N, normalize(vec3(-0.4,0.7,0.6))), 0.0) + 0.25*max(dot(N, normalize(vec3(0.6,-0.2,0.5))), 0.0);
  if (mode == 2) { float k = length(fwidth(vn)) / max(length(fwidth(vw)), 1e-12); o = vec4(ramp(k * kscale) * (0.45 + 0.55*d), 1.0); return; }
  if (mode == 4) { float t = (vs - srange.x) / max(srange.y - srange.x, 1e-12); o = vec4(ramp(t) * (0.5 + 0.5*d), 1.0); return; }
  float rim = pow(1.0 - abs(N.z), 3.0) * 0.18;
  o = vec4(mix(vec3(0.78), col, 0.35) * d + rim, 1.0);
})";
// silhouette IoU: model mask (rendered) vs ref mask (texture, rows top-down) -> 4 atomic counters
static const char* CS_IOU = R"(#version 450
layout(local_size_x = 16, local_size_y = 16) in;
layout(binding = 0, rgba8) uniform readonly image2D model;
layout(binding = 1, r8) uniform readonly image2D refm;
layout(std430, binding = 2) buffer C { uint inter; uint uni; uint nm; uint nr; };
uniform ivec2 size;
void main(){
  ivec2 q = ivec2(gl_GlobalInvocationID.xy); if (q.x >= size.x || q.y >= size.y) return;
  bool a = imageLoad(model, q).r > 0.5;
  bool b = imageLoad(refm, ivec2(q.x, size.y - 1 - q.y)).r > 0.5;
  if (a && b) atomicAdd(inter, 1u); if (a || b) atomicAdd(uni, 1u); if (a) atomicAdd(nm, 1u); if (b) atomicAdd(nr, 1u);
})";
// deviation: per point of A, exact distance to the nearest triangle of B (brute force; fine up to ~1e9 pairs)
static const char* CS_DEV = R"(#version 450
layout(local_size_x = 128) in;
layout(std430, binding = 0) readonly buffer P { vec4 pts[]; };
layout(std430, binding = 1) readonly buffer T { vec4 tri[]; };
layout(std430, binding = 2) writeonly buffer D { float dist[]; };
uniform uint np; uniform uint nt;
float d2tri(vec3 p, vec3 a, vec3 b, vec3 c){
  vec3 ab = b-a, ac = c-a, ap = p-a; float d1 = dot(ab,ap), d2 = dot(ac,ap);
  if (d1 <= 0.0 && d2 <= 0.0) return dot(ap,ap);
  vec3 bp = p-b; float d3 = dot(ab,bp), d4 = dot(ac,bp);
  if (d3 >= 0.0 && d4 <= d3) return dot(bp,bp);
  float vc = d1*d4 - d3*d2;
  if (vc <= 0.0 && d1 >= 0.0 && d3 <= 0.0) { float v = d1/(d1-d3); vec3 q = a + v*ab - p; return dot(q,q); }
  vec3 cp = p-c; float d5 = dot(ab,cp), d6 = dot(ac,cp);
  if (d6 >= 0.0 && d5 <= d6) return dot(cp,cp);
  float vb = d5*d2 - d1*d6;
  if (vb <= 0.0 && d2 >= 0.0 && d6 <= 0.0) { float w = d2/(d2-d6); vec3 q = a + w*ac - p; return dot(q,q); }
  float va = d3*d6 - d5*d4;
  if (va <= 0.0 && (d4-d3) >= 0.0 && (d5-d6) >= 0.0) { float w = (d4-d3)/((d4-d3)+(d5-d6)); vec3 q = b + w*(c-b) - p; return dot(q,q); }
  float den = 1.0/(va+vb+vc); float v = vb*den, w = vc*den; vec3 q = a + ab*v + ac*w - p; return dot(q,q);
}
void main(){
  uint i = gl_GlobalInvocationID.x; if (i >= np) return;
  vec3 p = pts[i].xyz; float best = 3.4e38;
  for (uint t = 0u; t < nt; ++t) best = min(best, d2tri(p, tri[3u*t].xyz, tri[3u*t+1u].xyz, tri[3u*t+2u].xyz));
  dist[i] = sqrt(best);
})";

static void gl_init() {
    if (g_rc) return;
    WNDCLASSA wc{};
    wc.lpfnWndProc = DefWindowProcA;
    wc.hInstance = GetModuleHandleA(nullptr);
    wc.lpszClassName = "cadengine_gl";
    RegisterClassA(&wc);
    g_wnd = CreateWindowA("cadengine_gl", "cadengine", WS_OVERLAPPEDWINDOW, 0, 0, 16, 16, nullptr, nullptr, wc.hInstance, nullptr);  // never shown
    g_dc = GetDC(g_wnd);
    PIXELFORMATDESCRIPTOR pfd{sizeof pfd, 1, PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER, PFD_TYPE_RGBA, 32};
    pfd.cDepthBits = 24;
    SetPixelFormat(g_dc, ChoosePixelFormat(g_dc, &pfd), &pfd);
    g_rc = wglCreateContext(g_dc);
    if (!g_rc || !wglMakeCurrent(g_dc, g_rc)) throw ToolError("OpenGL context creation failed");
#define LOAD(ret, name, args) name = (PFN_##name)wglGetProcAddress(#name); if (!name) throw ToolError("GL 4.5 function missing: " #name);
    GLFUNCS(LOAD)
#undef LOAD
    g_renderer = std::string((const char*)glGetString(GL_RENDERER)) + " / GL " + (const char*)glGetString(GL_VERSION);
    g_prog = link({compile(GL_VERTEX_SHADER, VS), compile(GL_FRAGMENT_SHADER, FS)});
    g_iou = link({compile(GL_COMPUTE_SHADER, CS_IOU)});
    g_dev = link({compile(GL_COMPUTE_SHADER, CS_DEV)});
}

// ------------------------------------------------------------------ meshes
struct GMesh {
    TopoDS_Shape src;
    std::vector<float> v;       // x y z nx ny nz s
    std::vector<uint32_t> idx;
    GLuint vao = 0, vbo = 0, ibo = 0;
    bool scalar_dirty = false;
    Bnd_Box box;
    double tess_ms = 0;
    ~GMesh() { if (vbo) { glDeleteBuffers(1, &vbo); glDeleteBuffers(1, &ibo); glDeleteVertexArrays(1, &vao); } }
};
static std::vector<std::shared_ptr<GMesh>> g_meshes;  // cache by shape identity (IsEqual)

static std::shared_ptr<GMesh> mesh_of(const TopoDS_Shape& s, double rel_defl = 1e-3) {
    for (auto& m : g_meshes) if (m->src.IsEqual(s)) return m;
    double t0 = now_ms();
    auto m = std::make_shared<GMesh>();
    m->src = s;
    double dg = std::max(geo::diag(s), 1e-9);
    BRepMesh_IncrementalMesh mesher(s, dg * rel_defl, false, 0.3, true);
    for (auto& fs : geo::subshapes(s, TopAbs_FACE)) {
        TopoDS_Face f = TopoDS::Face(fs);
        TopLoc_Location loc;
        const occ::handle<Poly_Triangulation>& T = BRep_Tool::Triangulation(f, loc);
        if (T.IsNull()) continue;
        if (!T->HasNormals()) BRepLib_ToolTriangulatedShape::ComputeNormals(f, T);
        gp_Trsf tr = loc.Transformation();
        bool rev = f.Orientation() == TopAbs_REVERSED;
        uint32_t base = (uint32_t)(m->v.size() / 7);
        for (int i = 1; i <= T->NbNodes(); ++i) {
            gp_Pnt p = T->Node(i).Transformed(tr);
            gp_Dir n = T->Normal(i).Transformed(tr);
            if (rev) n.Reverse();
            m->v.insert(m->v.end(), {(float)p.X(), (float)p.Y(), (float)p.Z(), (float)n.X(), (float)n.Y(), (float)n.Z(), 0.f});
            m->box.Add(p);
        }
        for (int i = 1; i <= T->NbTriangles(); ++i) {
            int a, b, c;
            T->Triangle(i).Get(a, b, c);
            if (rev) std::swap(b, c);
            m->idx.insert(m->idx.end(), {base + a - 1, base + b - 1, base + c - 1});
        }
    }
    m->tess_ms = now_ms() - t0;
    glGenVertexArrays(1, &m->vao);
    glBindVertexArray(m->vao);
    glGenBuffers(1, &m->vbo);
    glBindBuffer(GL_ARRAY_BUFFER, m->vbo);
    glBufferData(GL_ARRAY_BUFFER, m->v.size() * 4, m->v.data(), GL_DYNAMIC_DRAW);
    glGenBuffers(1, &m->ibo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m->ibo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, m->idx.size() * 4, m->idx.data(), GL_STATIC_DRAW);
    for (int a = 0; a < 3; ++a) glEnableVertexAttribArray(a);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 28, (void*)0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 28, (void*)12);
    glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 28, (void*)24);
    glBindVertexArray(0);
    g_meshes.push_back(m);
    if (g_meshes.size() > 256) g_meshes.erase(g_meshes.begin());
    return m;
}

struct Item { std::string name; std::shared_ptr<GMesh> mesh; float col[3]; };

static std::vector<Item> scene_items(Model& M, const json& names, json& stat) {
    static const float pal[][3] = {{0.75f, 0.45f, 0.35f}, {0.35f, 0.55f, 0.8f}, {0.5f, 0.75f, 0.4f}, {0.85f, 0.75f, 0.35f}, {0.65f, 0.45f, 0.8f}, {0.4f, 0.75f, 0.75f}};
    std::vector<Item> out;
    double tess = 0;
    int i = 0, tris = 0;
    for (auto& [k, o] : M.cur.objects) {
        bool want = names.is_array() && !names.empty() ? std::find(names.begin(), names.end(), k) != names.end() : (o.kind == "solid" || o.kind == "sheet");
        if (!want) continue;
        bool cached = false;
        for (auto& m : g_meshes) if (m->src.IsEqual(o.shape)) cached = true;
        auto m = mesh_of(o.shape);
        if (!cached) tess += m->tess_ms;
        Item it{k, m};
        float c[3] = {pal[i % 6][0], pal[i % 6][1], pal[i % 6][2]};
        if (o.meta.contains("color") && o.meta["color"].is_string()) {
            unsigned rgb = 0;
            sscanf(o.meta["color"].get<std::string>().c_str() + 1, "%x", &rgb);
            c[0] = ((rgb >> 16) & 255) / 255.f; c[1] = ((rgb >> 8) & 255) / 255.f; c[2] = (rgb & 255) / 255.f;
        }
        std::copy(c, c + 3, it.col);
        tris += (int)m->idx.size() / 3;
        out.push_back(it);
        ++i;
    }
    stat["tess_ms"] = geo::rnd(tess, 2);
    stat["tris"] = tris;
    return out;
}

// ------------------------------------------------------------------ cameras
struct View { const char* name; gp_Vec u, v; };
static View view_of(const std::string& n) {
    if (n == "front") return {"front", gp_Vec(1, 0, 0), gp_Vec(0, 0, 1)};
    if (n == "back") return {"back", gp_Vec(-1, 0, 0), gp_Vec(0, 0, 1)};
    if (n == "left") return {"left", gp_Vec(0, -1, 0), gp_Vec(0, 0, 1)};
    if (n == "right") return {"right", gp_Vec(0, 1, 0), gp_Vec(0, 0, 1)};
    if (n == "top") return {"top", gp_Vec(1, 0, 0), gp_Vec(0, 1, 0)};
    if (n == "bottom") return {"bottom", gp_Vec(1, 0, 0), gp_Vec(0, -1, 0)};
    if (n == "iso" || n == "iso2") {
        gp_Vec d = n == "iso" ? gp_Vec(1, 1, -1) : gp_Vec(-1, 1, -1);  // view direction
        d.Normalize();
        gp_Vec u = d.Crossed(gp_Vec(0, 0, 1)).Normalized();
        return {n == "iso" ? "iso" : "iso2", u, u.Crossed(d).Normalized()};
    }
    throw ToolError("unknown view " + n, "front|back|left|right|top|bottom|iso|iso2");
}

// column-major mat4 for ortho camera fitted to box, aspect w/h
static void camera(const View& V, const Bnd_Box& box, double aspect, float M[16], float R[9]) {
    gp_Vec u = V.u.Normalized(), v = V.v.Normalized(), w = u.Crossed(v);
    double lo[3] = {1e300, 1e300, 1e300}, hi[3] = {-1e300, -1e300, -1e300};
    double x0, y0, z0, x1, y1, z1;
    box.Get(x0, y0, z0, x1, y1, z1);
    for (int c = 0; c < 8; ++c) {
        gp_Vec p(c & 1 ? x1 : x0, c & 2 ? y1 : y0, c & 4 ? z1 : z0);
        double q[3] = {p.Dot(u), p.Dot(v), p.Dot(w)};
        for (int k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], q[k]); hi[k] = std::max(hi[k], q[k]); }
    }
    double cu = (lo[0] + hi[0]) / 2, cv = (lo[1] + hi[1]) / 2, hu = (hi[0] - lo[0]) / 2, hv = (hi[1] - lo[1]) / 2;
    double s = std::max(hu / aspect, hv) * 1.08 + 1e-12;
    double sx = 1 / (s * aspect), sy = 1 / s, zr = std::max(hi[2] - lo[2], 1e-9), zc = (lo[2] + hi[2]) / 2;
    double sz = -1.9 / zr;  // larger w (toward camera) -> smaller depth
    gp_Vec row[3] = {u * sx, v * sy, w * sz};
    double off[3] = {-cu * sx, -cv * sy, -zc * sz};
    for (int r = 0; r < 3; ++r) { M[0 * 4 + r] = (float)row[r].X(); M[1 * 4 + r] = (float)row[r].Y(); M[2 * 4 + r] = (float)row[r].Z(); M[3 * 4 + r] = (float)off[r]; }
    M[3] = M[7] = M[11] = 0; M[15] = 1;
    gp_Vec rr[3] = {u, v, w};
    for (int r = 0; r < 3; ++r) { R[0 * 3 + r] = (float)rr[r].X(); R[1 * 3 + r] = (float)rr[r].Y(); R[2 * 3 + r] = (float)rr[r].Z(); }
}

// ------------------------------------------------------------------ render targets
struct Target {
    int w = 0, h = 0, samples = 0;
    GLuint fbo_ms = 0, rb_c = 0, rb_d = 0, fbo = 0, tex = 0;
    void make(int W, int H, int S) {
        if (W == w && H == h && S == samples) return;
        if (fbo) { glDeleteFramebuffers(1, &fbo); glDeleteTextures(1, &tex); }
        if (fbo_ms) { glDeleteFramebuffers(1, &fbo_ms); glDeleteRenderbuffers(1, &rb_c); glDeleteRenderbuffers(1, &rb_d); }
        w = W; h = H; samples = S;
        glGenTextures(1, &tex);
        glBindTexture(GL_TEXTURE_2D, tex);
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, W, H);
        glGenFramebuffers(1, &fbo);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);
        glGenRenderbuffers(1, &rb_d);
        glBindRenderbuffer(GL_RENDERBUFFER, rb_d);
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 0, GL_DEPTH_COMPONENT24, W, H);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rb_d);
        if (S > 1) {
            glGenFramebuffers(1, &fbo_ms);
            glBindFramebuffer(GL_FRAMEBUFFER, fbo_ms);
            GLuint rbs[2];
            glGenRenderbuffers(2, rbs);
            rb_c = rbs[0]; GLuint rd = rbs[1];
            glBindRenderbuffer(GL_RENDERBUFFER, rb_c);
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, S, GL_RGBA8, W, H);
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rb_c);
            glBindRenderbuffer(GL_RENDERBUFFER, rd);
            glRenderbufferStorageMultisample(GL_RENDERBUFFER, S, GL_DEPTH_COMPONENT24, W, H);
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rd);
            rb_d = rd;
        }
        if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) throw ToolError("FBO incomplete");
    }
    void bind_draw() { glBindFramebuffer(GL_FRAMEBUFFER, samples > 1 ? fbo_ms : fbo); glViewport(0, 0, w, h); }
    void resolve() {
        if (samples <= 1) return;
        glBindFramebuffer(GL_READ_FRAMEBUFFER, fbo_ms);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo);
        glBlitFramebuffer(0, 0, w, h, 0, 0, w, h, GL_COLOR_BUFFER_BIT, GL_NEAREST);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    }
};
static Target g_tile, g_mask;

static int mode_of(const std::string& m) {
    if (m == "clay") return 0; if (m == "zebra") return 1; if (m == "curvature") return 2; if (m == "mask") return 3; if (m == "deviation") return 4;
    throw ToolError("unknown mode " + m, "clay|zebra|curvature|deviation|mask");
}

static void draw(const std::vector<Item>& items, const float M[16], const float R[9], int mode, double diag, float s0 = 0, float s1 = 1) {
    glUseProgram(g_prog);
    glUniformMatrix4fv(glGetUniformLocation(g_prog, "M"), 1, GL_FALSE, M);
    glUniformMatrix3fv(glGetUniformLocation(g_prog, "R"), 1, GL_FALSE, R);
    glUniform1i(glGetUniformLocation(g_prog, "mode"), mode);
    glUniform1f(glGetUniformLocation(g_prog, "stripes"), 14.0f);
    glUniform2f(glGetUniformLocation(g_prog, "srange"), s0, s1);
    glUniform1f(glGetUniformLocation(g_prog, "kscale"), (float)(diag / 40.0));
    for (auto& it : items) {
        glUniform3f(glGetUniformLocation(g_prog, "col"), it.col[0], it.col[1], it.col[2]);
        glBindVertexArray(it.mesh->vao);
        glDrawElements(GL_TRIANGLES, (GLsizei)it.mesh->idx.size(), GL_UNSIGNED_INT, nullptr);
    }
    glBindVertexArray(0);
}

static Bnd_Box scene_box(const std::vector<Item>& items) { Bnd_Box b; for (auto& it : items) b.Add(it.mesh->box); return b; }

// ------------------------------------------------------------------ sheet
static json render_impl(const std::vector<Item>& items, const json& p, json stat, float s0 = 0, float s1 = 1) {
    double t0 = now_ms();
    std::string path = p.at("path");
    int res = p.value("res", 300);
    json views = p.value("views", json::array({"iso", "left", "right", "front", "back", "top"}));
    json modes = p.contains("modes") ? p["modes"] : json::array({p.value("mode", std::string("clay"))});
    int cols = p.value("cols", 3);
    int nt = (int)(views.size() * modes.size());
    int rows = (nt + cols - 1) / cols;
    int W = cols * res, H = rows * res;
    if (items.empty()) throw ToolError("nothing to render (no solids)");
    Bnd_Box box = scene_box(items);
    double dg = box.CornerMin().Distance(box.CornerMax());
    std::vector<unsigned char> sheet((size_t)W * H * 4, p.value("mode", std::string()) == "mask" ? 0 : 255), tile((size_t)res * res * 4);
    g_tile.make(res, res, 4);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_MULTISAMPLE);
    int k = 0;
    double gpu = 0;
    for (auto& md : modes) {
        int mode = mode_of(md);
        for (auto& vn : views) {
            double g0 = now_ms();
            float M[16], R[9];
            camera(view_of(vn), box, 1.0, M, R);
            g_tile.bind_draw();
            if (mode == 3) glClearColor(0, 0, 0, 1); else glClearColor(0.93f, 0.93f, 0.94f, 1);
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
            draw(items, M, R, mode, dg, s0, s1);
            g_tile.resolve();
            glReadPixels(0, 0, res, res, GL_RGBA, GL_UNSIGNED_BYTE, tile.data());
            gpu += now_ms() - g0;
            int cx = (k % cols) * res, cy = (k / cols) * res;
            for (int y = 0; y < res; ++y) memcpy(&sheet[((size_t)(cy + y) * W + cx) * 4], &tile[(size_t)(res - 1 - y) * res * 4], (size_t)res * 4);
            ++k;
        }
    }
    double e0 = now_ms();
    stbi_write_png_compression_level = 1;
    const char* ext = strrchr(path.c_str(), '.');
    bool ok = ext && (_stricmp(ext, ".jpg") == 0 || _stricmp(ext, ".jpeg") == 0) ? stbi_write_jpg(path.c_str(), W, H, 4, sheet.data(), 90)
                                                                              : stbi_write_png(path.c_str(), W, H, 4, sheet.data(), W * 4);
    if (!ok) throw ToolError("could not write " + path);
    stat["path"] = path;
    stat["size"] = json::array({W, H});
    stat["gpu_ms"] = geo::rnd(gpu, 2);
    stat["encode_ms"] = geo::rnd(now_ms() - e0, 2);
    stat["render_ms"] = geo::rnd(now_ms() - t0, 2);
    stat["renderer"] = g_renderer;
    return stat;
}

json gpu_render(Model& M, const json& p) {
    gl_init();
    json stat;
    double t0 = now_ms();
    auto items = scene_items(M, p.value("objects", json()), stat);
    json r = render_impl(items, p, stat);
    r["total_ms"] = geo::rnd(now_ms() - t0, 2);
    return r;
}

// ------------------------------------------------------------------ registered reference silhouettes + IoU
struct RefImg { std::string view; int w, h; GLuint tex; int bb[4]; int npx; double mpp = 0; double ox = 0, oy = 0; bool abs = false; };
static std::map<std::string, RefImg> g_refs;

json gpu_register_ref(const json& p) {
    gl_init();
    std::string name = p.at("name"), path = p.at("image");
    int w, h, n;
    unsigned char* img = stbi_load(path.c_str(), &w, &h, &n, 4);
    if (!img) throw ToolError("cannot load reference image " + path);
    int thr = p.value("threshold", 128);
    std::vector<unsigned char> mask((size_t)w * h);
    int amin = 255;
    for (size_t i = 0; i < (size_t)w * h; ++i) amin = std::min(amin, (int)img[i * 4 + 3]);
    bool use_alpha = n == 4 && amin < 250;
    auto lum = [&](int x, int y) { const unsigned char* q = img + ((size_t)y * w + x) * 4; return (q[0] + q[1] + q[2]) / 3.0; };
    double corners = 0;
    int cn = 0;
    for (int y = 0; y < 4; ++y) for (int x = 0; x < 4; ++x) { corners += lum(x, y) + lum(w - 1 - x, h - 1 - y) + lum(w - 1 - x, y) + lum(x, h - 1 - y); cn += 4; }
    bool dark_on_light = corners / cn >= thr;
    RefImg r{p.value("view", std::string("front")), w, h, 0, {w, h, 0, 0}, 0};
    for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) {
        bool in = use_alpha ? img[((size_t)y * w + x) * 4 + 3] > 127 : (dark_on_light ? lum(x, y) < thr : lum(x, y) >= thr);
        mask[(size_t)y * w + x] = in ? 255 : 0;
        if (in) { r.npx++; r.bb[0] = std::min(r.bb[0], x); r.bb[1] = std::min(r.bb[1], y); r.bb[2] = std::max(r.bb[2], x + 1); r.bb[3] = std::max(r.bb[3], y + 1); }
    }
    stbi_image_free(img);
    if (!r.npx) throw ToolError("reference image has no silhouette", "check threshold / background");
    if (p.contains("m_per_px") && !p["m_per_px"].is_null()) {
        r.abs = true; r.mpp = p["m_per_px"];
        r.ox = p.contains("origin_px") ? p["origin_px"][0].get<double>() : w / 2.0;
        r.oy = p.contains("origin_px") ? p["origin_px"][1].get<double>() : h / 2.0;
    }
    if (g_refs.count(name)) glDeleteTextures(1, &g_refs[name].tex);
    glGenTextures(1, &r.tex);
    glBindTexture(GL_TEXTURE_2D, r.tex);
    glTexStorage2D(GL_TEXTURE_2D, 1, GL_R8, w, h);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RED, GL_UNSIGNED_BYTE, mask.data());
    g_refs[name] = r;
    return {{"name", name}, {"size", json::array({w, h})}, {"ref_px", r.npx}, {"bbox_px", json::array({r.bb[0], r.bb[1], r.bb[2], r.bb[3]})}, {"mode", r.abs ? "absolute" : "normalised"}};
}

// python query._VIEWS: (horizontal axis, vertical axis, flip of horizontal)
static void iou_axes(const std::string& v, int& ix, int& iy, double& flip) {
    if (v == "front") { ix = 0; iy = 2; flip = 1; } else if (v == "back") { ix = 0; iy = 2; flip = -1; }
    else if (v == "side" || v == "right") { ix = 1; iy = 2; flip = 1; } else if (v == "left") { ix = 1; iy = 2; flip = -1; }
    else if (v == "top") { ix = 0; iy = 1; flip = 1; } else if (v == "bottom") { ix = 0; iy = 1; flip = -1; }
    else throw ToolError("bad iou view " + v);
}

json gpu_iou(Model& M, const json& p) {
    gl_init();
    double t0 = now_ms();
    json stat;
    auto items = scene_items(M, p.value("objects", json()), stat);
    if (items.empty()) throw ToolError("no solids to compare");
    json names = p.value("refs", json());
    json out = json::object();
    GLuint ssbo;
    glGenBuffers(1, &ssbo);
    glDisable(GL_DEPTH_TEST);
    for (auto& [rn, R] : g_refs) {
        if (names.is_array() && !names.empty() && std::find(names.begin(), names.end(), rn) == names.end()) continue;
        int ix, iy; double flip;
        iou_axes(R.view, ix, iy, flip);
        // model 2D bbox in view axes (from mesh vertices)
        double lo[2] = {1e300, 1e300}, hi[2] = {-1e300, -1e300};
        for (auto& it : items) for (size_t i = 0; i < it.mesh->v.size(); i += 7) {
            double a = flip * it.mesh->v[i + ix], b = it.mesh->v[i + iy];
            lo[0] = std::min(lo[0], a); hi[0] = std::max(hi[0], a); lo[1] = std::min(lo[1], b); hi[1] = std::max(hi[1], b);
        }
        // pixel = A*P + B (x), y_px = C*P + D ; ndc_x = 2 px/W - 1, ndc_y = 1 - 2 py/H
        double ax, bx, cy, dy, mpp;
        if (R.abs) { ax = 1 / R.mpp; bx = R.ox; cy = -1 / R.mpp; dy = R.oy; mpp = R.mpp; }
        else {
            double sc = (R.bb[3] - R.bb[1]) / std::max(hi[1] - lo[1], 1e-12);
            ax = sc; bx = R.bb[0] - lo[0] * sc + ((R.bb[2] - R.bb[0]) - (hi[0] - lo[0]) * sc) / 2;
            cy = -sc; dy = R.bb[3] + lo[1] * sc; mpp = 1 / sc;
        }
        float Mx[16] = {0}, Rm[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
        double kx = 2.0 / R.w, ky = -2.0 / R.h;
        Mx[ix * 4 + 0] = (float)(kx * ax * flip);
        Mx[12] = (float)(kx * bx - 1);
        Mx[iy * 4 + 1] = (float)(ky * cy);
        Mx[13] = (float)(ky * dy + 1);
        Mx[15] = 1;
        g_mask.make(R.w, R.h, 1);
        g_mask.bind_draw();
        glClearColor(0, 0, 0, 1);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        draw(items, Mx, Rm, 3, 1);
        uint32_t zero[4] = {0, 0, 0, 0};
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo);
        glBufferData(GL_SHADER_STORAGE_BUFFER, 16, zero, GL_DYNAMIC_READ);
        glUseProgram(g_iou);
        glBindImageTexture(0, g_mask.tex, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA8);
        glBindImageTexture(1, R.tex, 0, GL_FALSE, 0, GL_READ_ONLY, GL_R8);
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, ssbo);
        GLint loc = glGetUniformLocation(g_iou, "size");
        typedef void(APIENTRY * PFN2i)(GLint, GLint, GLint);
        static PFN2i u2i = (PFN2i)wglGetProcAddress("glUniform2i");
        u2i(loc, R.w, R.h);
        glDispatchCompute((R.w + 15) / 16, (R.h + 15) / 16, 1);
        glMemoryBarrier(GL_ALL_BARRIER_BITS);
        uint32_t c[4];
        glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, 16, c);
        out[rn] = {{"iou", geo::rnd(c[0] / (double)std::max(c[1], 1u), 4)}, {"view", R.view}, {"mode", R.abs ? "absolute" : "normalised (height-fit, centred)"},
                   {"m_per_px", geo::rnd(mpp, 8)}, {"model_px", c[2]}, {"ref_px", c[3]},
                   {"model_only_frac", geo::rnd((c[2] - c[0]) / (double)std::max(c[1], 1u), 4)}, {"ref_only_frac", geo::rnd((c[3] - c[0]) / (double)std::max(c[1], 1u), 4)}};
    }
    glDeleteBuffers(1, &ssbo);
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    return {{"refs", out}, {"tess_ms", stat["tess_ms"]}, {"total_ms", geo::rnd(now_ms() - t0, 2)}};
}

// ------------------------------------------------------------------ deviation heatmap
json gpu_deviation(Model& M, const json& p) {
    gl_init();
    double t0 = now_ms();
    json sa, sb;
    auto A = scene_items(M, json::array({p.at("a")}), sa);
    auto Bi = scene_items(M, json::array({p.at("b")}), sb);
    if (A.empty() || Bi.empty()) throw ToolError("deviation needs two existing objects a, b");
    auto& ma = *A[0].mesh;
    auto& mb = *Bi[0].mesh;
    uint32_t np = (uint32_t)(ma.v.size() / 7), nt = (uint32_t)(mb.idx.size() / 3);
    std::vector<float> P(np * 4), T(nt * 12);
    for (uint32_t i = 0; i < np; ++i) { P[i * 4] = ma.v[i * 7]; P[i * 4 + 1] = ma.v[i * 7 + 1]; P[i * 4 + 2] = ma.v[i * 7 + 2]; P[i * 4 + 3] = 1; }
    for (uint32_t t = 0; t < nt; ++t) for (int k = 0; k < 3; ++k) { uint32_t vi = mb.idx[t * 3 + k]; for (int c = 0; c < 3; ++c) T[t * 12 + k * 4 + c] = mb.v[vi * 7 + c]; T[t * 12 + k * 4 + 3] = 1; }
    GLuint buf[3];
    glGenBuffers(3, buf);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf[0]); glBufferData(GL_SHADER_STORAGE_BUFFER, P.size() * 4, P.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf[1]); glBufferData(GL_SHADER_STORAGE_BUFFER, T.size() * 4, T.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf[2]); glBufferData(GL_SHADER_STORAGE_BUFFER, np * 4, nullptr, GL_DYNAMIC_READ);
    double g0 = now_ms();
    glUseProgram(g_dev);
    for (int i = 0; i < 3; ++i) glBindBufferBase(GL_SHADER_STORAGE_BUFFER, i, buf[i]);
    glUniform1ui(glGetUniformLocation(g_dev, "np"), np);
    glUniform1ui(glGetUniformLocation(g_dev, "nt"), nt);
    glDispatchCompute((np + 127) / 128, 1, 1);
    glMemoryBarrier(GL_ALL_BARRIER_BITS);
    std::vector<float> d(np);
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, np * 4, d.data());
    double gms = now_ms() - g0;
    glDeleteBuffers(3, buf);
    std::vector<float> s = d;
    std::sort(s.begin(), s.end());
    double mean = 0, rms = 0;
    for (float x : d) { mean += x; rms += x * x; }
    mean /= std::max<size_t>(np, 1); rms = std::sqrt(rms / std::max<size_t>(np, 1));
    size_t wi = std::max_element(d.begin(), d.end()) - d.begin();
    json res = {{"a_to_b", {{"max", geo::rnd(s.back(), 6)}, {"mean", geo::rnd(mean, 6)}, {"rms", geo::rnd(rms, 6)}, {"p95", geo::rnd(s[(size_t)(0.95 * (np - 1))], 6)},
                            {"worst_point", json::array({geo::rnd(P[wi * 4], 5), geo::rnd(P[wi * 4 + 1], 5), geo::rnd(P[wi * 4 + 2], 5)})}}},
                {"points", np}, {"ref_tris", nt}, {"gpu_ms", geo::rnd(gms, 2)}};
    if (p.contains("heatmap") && !p["heatmap"].is_null()) {
        for (uint32_t i = 0; i < np; ++i) ma.v[i * 7 + 6] = d[i];
        glBindBuffer(GL_ARRAY_BUFFER, ma.vbo);
        glBufferData(GL_ARRAY_BUFFER, ma.v.size() * 4, ma.v.data(), GL_DYNAMIC_DRAW);
        float hi = p.contains("tol") && !p["tol"].is_null() ? p["tol"].get<float>() : std::max(s.back(), 1e-9f);
        json rp = {{"path", p["heatmap"]}, {"mode", "deviation"}, {"res", p.value("res", 300)}, {"views", p.value("views", json::array({"iso", "front", "top"}))}};
        res["heatmap"] = render_impl(A, rp, json::object(), 0, hi);
        res["heatmap"]["range"] = json::array({0, hi});
    }
    res["total_ms"] = geo::rnd(now_ms() - t0, 2);
    return res;
}

json gpu_info() { gl_init(); return {{"renderer", g_renderer}, {"meshes_cached", g_meshes.size()}, {"refs", g_refs.size()}}; }
