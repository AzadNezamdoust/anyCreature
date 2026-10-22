"""ModernGL offscreen renderer (no Blender): clay, zebra, ortho views, silhouettes, face-border lines.

    from cadkit.fast.render import Scene
    sc = Scene("out/.../mesh.npz")               # mm, per-part v/t/f/n from cadkit.fast.build
    img = sc.view("iso", mode="clay", res=640)   # PIL.Image
    m = sc.silhouette("+x", "+z", px_per_mm, origin_px=(u0, v0), size=(W, H))   # bool mask on a ref's pixel grid
    sc.sheet(path)                               # 3x3 contact sheet

Views are given as (u, v) world axes of the image right / up direction: "+x","-y",...  View dir = u x v.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

AX = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}
ORTHO = {  # name: (u, v)   camera looks along -(u x v)
    "front": ("+x", "+z"),   # from -Y
    "back": ("-x", "+z"),    # from +Y
    "left": ("-y", "+z"),    # from -X
    "right": ("+y", "+z"),   # from +X
    "top": ("+x", "+y"),     # from +Z
    "bottom": ("+x", "-y"),  # from -Z
}

VS = """
#version 330
uniform mat4 M; uniform mat3 R;
in vec3 p; in vec3 n; in float fid;
out vec3 vn; out vec3 vp; flat out float vf;
void main(){ gl_Position = M * vec4(p,1.0); vn = R * n; vp = p; vf = fid; }
"""
FS = """
#version 330
uniform int mode; uniform vec3 col; uniform float stripes; uniform vec3 vdir;
in vec3 vn; in vec3 vp; flat in float vf;
out vec4 o;
void main(){
  vec3 N = normalize(vn); if (!gl_FrontFacing) N = -N;
  if (mode == 2) { o = vec4(1.0); return; }
  if (mode == 3) { float f = vf + 1.0; o = vec4(mod(f,256.0)/255.0, mod(floor(f/256.0),256.0)/255.0,
                    floor(f/65536.0)/255.0, 1.0); return; }
  if (mode == 1) {  // zebra: stripes of the reflected view ray vs world-up (camera-space normals)
    vec3 r = reflect(vec3(0,0,-1), N);
    float s = smoothstep(-0.08, 0.08, sin(stripes * asin(clamp(r.y, -1.0, 1.0))));
    o = vec4(vec3(0.08 + 0.86 * s), 1.0); return; }
  vec3 L1 = normalize(vec3(-0.4, 0.7, 0.6)); vec3 L2 = normalize(vec3(0.6, -0.2, 0.5));
  float d = 0.18 + 0.62 * max(dot(N, L1), 0.0) + 0.25 * max(dot(N, L2), 0.0);
  float rim = pow(1.0 - abs(N.z), 3.0) * 0.18;
  vec3 base = mix(vec3(0.78), col, 0.35);
  o = vec4(base * d + rim, 1.0);
}
"""


def _basis(u, v):
    u = np.array(AX[u] if isinstance(u, str) else u, float)
    v = np.array(AX[v] if isinstance(v, str) else v, float)
    u /= np.linalg.norm(u)
    v -= u * (u @ v)
    v /= np.linalg.norm(v)
    return np.stack([u, v, np.cross(u, v)])   # rows: right, up, towards camera


ISO = {"iso": _basis((1, 0.8, 0), (-0.3, 0.35, 1)),        # from -X/-Y/+Z (front-left-top)
       "iso_back": _basis((-1, -0.8, 0), (0.3, -0.35, 1))}   # from +X/+Y/+Z


class Scene:
    def __init__(self, npz, ctx=None):
        import moderngl
        z = np.load(npz)
        self.names = [str(s) for s in z["names"]]
        self.cols = z["colours"]
        self.ctx = ctx or moderngl.create_standalone_context()
        self.prog = self.ctx.program(vertex_shader=VS, fragment_shader=FS)
        self.vaos, allv = [], []
        fid_off = 0
        for i in range(len(self.names)):
            v, t, f = z[f"v_{i}"].astype("f4"), z[f"t_{i}"].astype("i4"), z[f"f_{i}"].astype("f4")
            n = z[f"n_{i}"].astype("f4") if f"n_{i}" in z else np.tile([0, 0, 1], (len(v), 1)).astype("f4")
            fv = np.zeros(len(v), "f4")
            for k in range(3):                   # per-vertex face id (vertices are per B-rep face)
                fv[t[:, k]] = f + fid_off
            fid_off += int(f.max()) + 1 if len(f) else 0
            vb = self.ctx.buffer(np.hstack([v, n, fv[:, None]]).astype("f4").tobytes())
            ib = self.ctx.buffer(t.tobytes())
            self.vaos.append(self.ctx.vertex_array(self.prog, [(vb, "3f 3f 1f", "p", "n", "fid")], ib))
            allv.append(v)
        V = np.vstack(allv)
        self.lo, self.hi = V.min(0), V.max(0)
        self.ctr = (self.lo + self.hi) / 2
        self.rad = float(np.linalg.norm(self.hi - self.lo) / 2)
        self.corners = np.array([[x, y, zz] for x in (self.lo[0], self.hi[0]) for y in (self.lo[1], self.hi[1])
                                 for zz in (self.lo[2], self.hi[2])])

    # --------------------------------------------------------------- core
    def _draw(self, B, l, r, b, t, W, H, mode, ss=1, stripes=28.0):
        ctx = self.ctx
        Ws, Hs = W * ss, H * ss
        fbo = ctx.simple_framebuffer((Ws, Hs), components=4)
        fbo.use()
        bg = (1, 1, 1, 1) if mode != 2 and mode != 3 else (0, 0, 0, 1)
        fbo.clear(*bg)
        ctx.enable(ctx.DEPTH_TEST)
        ctx.disable(ctx.CULL_FACE)
        d = B @ (self.corners - self.ctr).T
        zn, zf = d[2].min() - 1, d[2].max() + 1
        P = np.array([[2 / (r - l), 0, 0, -(r + l) / (r - l)], [0, 2 / (t - b), 0, -(t + b) / (t - b)],
                      [0, 0, 0, 0], [0, 0, 0, 1]], float)
        P[2] = [0, 0, -2 / (zf - zn), (zf + zn) / (zf - zn)]   # camera looks along -cam_z; nearer = larger z
        Vm = np.eye(4)
        Vm[:3, :3] = B
        Vm[:3, 3] = -B @ self.ctr
        M = P @ Vm
        self.prog["M"].write(M.T.astype("f4").tobytes())
        if "R" in self.prog:
            self.prog["R"].write(B.T.astype("f4").tobytes())
        if "mode" in self.prog:
            self.prog["mode"].value = mode
        if "stripes" in self.prog:
            self.prog["stripes"].value = stripes
        for vao, c in zip(self.vaos, self.cols):
            if "col" in self.prog:
                self.prog["col"].value = tuple(float(x) for x in c)
            vao.render()
        a = np.frombuffer(fbo.read(components=4), np.uint8).reshape(Hs, Ws, 4)[::-1]
        fbo.release()
        if ss > 1:
            a = np.asarray(Image.fromarray(a).resize((W, H), Image.LANCZOS))
        return a

    def _fit(self, B, res, margin=0.06):
        d = B @ (self.corners - self.ctr).T
        l, r, b, t = d[0].min(), d[0].max(), d[1].min(), d[1].max()
        s = max(r - l, t - b) * (1 + 2 * margin) / 2
        cx, cy = (l + r) / 2, (b + t) / 2
        return cx - s, cx + s, cy - s, cy + s, res, res

    def basis(self, view):
        return ISO[view] if view in ISO else _basis(*ORTHO[view]) if view in ORTHO else _basis(*view)

    def view(self, view, mode="clay", res=512, lines=True, ss=2):
        B = self.basis(view)
        l, r, b, t, W, H = self._fit(B, res)
        mi = {"clay": 0, "zebra": 1}[mode]
        img = self._draw(B, l, r, b, t, W, H, mi, ss=ss)[..., :3].copy()
        if lines:   # B-rep face borders from a face-id pass (cheap feature lines)
            ids = self._draw(B, l, r, b, t, W, H, 3, ss=1)[..., :3].astype(np.int32)
            ids = ids[..., 0] + 256 * ids[..., 1] + 65536 * ids[..., 2]
            e = np.zeros(ids.shape, bool)
            e[1:] |= ids[1:] != ids[:-1]
            e[:, 1:] |= ids[:, 1:] != ids[:, :-1]
            img[e] = (img[e] * 0.35).astype(np.uint8)
        return Image.fromarray(img)

    def silhouette(self, u, v, px_per_mm, origin_px, size):
        """Mask on a reference image's pixel grid: world point w maps to px = origin + (w.u, -w.v) * px_per_mm."""
        B = _basis(u, v)
        W, H = size
        ox, oy = origin_px
        c = B @ self.ctr                                       # projection relative to ctr (as in _draw)
        l = (0 - ox) / px_per_mm - c[0]
        r = (W - ox) / px_per_mm - c[0]
        t = (oy - 0) / px_per_mm - c[1]
        b = (oy - H) / px_per_mm - c[1]
        a = self._draw(B, l, r, b, t, W, H, 2, ss=1)
        return a[..., 0] > 127

    def silhouette_bbox(self, u, v, px_per_mm):
        """Tight-cropped mask (bbox registration), returns (mask, (w_mm, h_mm))."""
        B = _basis(u, v)
        d = B @ (self.corners - self.ctr).T
        l, r, b, t = d[0].min(), d[0].max(), d[1].min(), d[1].max()
        W, H = int(round((r - l) * px_per_mm)) + 1, int(round((t - b) * px_per_mm)) + 1
        a = self._draw(B, l, r, b, t, W, H, 2, ss=1)
        return a[..., 0] > 127, (r - l, t - b)

    def sheet(self, path=None, res=420, extra=()):
        tiles = [("front", "clay"), ("left", "clay"), ("top", "clay"), ("back", "clay"), ("iso", "clay"),
                 ("iso_back", "clay"), ("iso", "zebra"), ("top", "zebra"), ("left", "zebra")]
        ims = [(f"{v} {m}", self.view(v, m, res)) for v, m in tiles] + list(extra)
        return compose(ims, path, res)


def compose(ims, path=None, res=420, cols=3):
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * res, rows * (res + 18)), "white")
    d = ImageDraw.Draw(sh)
    for i, (lab, im) in enumerate(ims):
        im = im.convert("RGB")
        im.thumbnail((res, res))
        x, y = (i % cols) * res, (i // cols) * (res + 18)
        sh.paste(im, (x + (res - im.width) // 2, y + 18))
        d.text((x + 4, y + 2), lab, fill=(20, 20, 20))
    if path:
        sh.save(path, quality=90)
    return sh


if __name__ == "__main__":
    import sys
    import time
    t = time.time()
    Scene(sys.argv[1]).sheet(sys.argv[2])
    print(f"sheet {time.time() - t:.2f}s")
