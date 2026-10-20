# Commercially clean texturing helpers: moderngl (MIT) rasterizer, xatlas (MIT) UVs, numpy bake. No nvdiffrast.
import os, numpy as np, trimesh, moderngl, cv2
from PIL import Image

ROOT = r'E:\gen3d\texc'
ORIG = dict(wolf=r'E:\gen3d\r8\wolf\ref_rgba.png', crocodile=r'E:\gen3d\r8\crocodile\ref_rgba.png',
            eagle=r'E:\gen3d\r8\eagle\ref_rgba.png', frog=r'E:\gen3d\r8\frog\ref_rgba.png')
for _a, _k in dict(horse=5, elephant=9, giraffe=3, shark=3, tortoise=3, kangaroo=4).items():
    ORIG[_a] = rf'E:\gen3d\r9\{_a}\ref_c{_k}.png'
_ctx = None
def ctx():
    global _ctx
    if _ctx is None: _ctx = moderngl.create_standalone_context(require=430)
    return _ctx

def load_uv_mesh(a):
    """r9pick mesh + xatlas UVs, cached. Returns (V[N,3], F[M,3], UV[N,2]) with seams split."""
    p = os.path.join(ROOT, '_uv', a + '.npz'); os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        d = np.load(p); return d['v'], d['f'], d['uv']
    import xatlas
    m = trimesh.load(rf'E:\gen3d\r9pick\{a}.obj', process=False, force='mesh')
    at = xatlas.Atlas(); at.add_mesh(m.vertices.astype(np.float32), m.faces.astype(np.uint32))
    po = xatlas.PackOptions(); po.resolution = 2048; po.padding = 4; po.bilinear = True
    at.generate(pack_options=po)
    vm, f, uv = at[0]
    v = m.vertices[vm].astype(np.float32)
    np.savez(p, v=v, f=f.astype(np.int32), uv=uv.astype(np.float32)); return v, f.astype(np.int32), uv.astype(np.float32)

def vnormals(v, f):
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    n = np.zeros_like(v); [np.add.at(n, f[:, i], fn) for i in range(3)]
    # average across seam-split duplicates (same position) for smooth normals
    key = np.unique(np.round(v, 6), axis=0, return_inverse=True)[1].ravel()
    acc = np.zeros((key.max() + 1, 3)); np.add.at(acc, key, n); n = acc[key]
    return (n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)).astype(np.float32)

_VS = '''#version 430
in vec3 p; in vec3 a; uniform mat4 M; uniform int uvmode; out vec3 va; out vec3 vp;
void main(){ va=a; vp=p; if(uvmode==1){ gl_Position=vec4(a.xy*2.0-1.0,0.0,1.0);} else { gl_Position=M*vec4(p,1.0);} }'''
_FS = '''#version 430
in vec3 va; in vec3 vp; out vec4 o; uniform int outpos;
void main(){ o = outpos==1 ? vec4(vp,1.0) : vec4(va,1.0); }'''
_prog = None
def raster(v, f, attr, M=None, res=768, uvmode=False, outpos=False):
    """Rasterize mesh; returns float32 [res,res,4] (alpha=coverage) and depth [res,res]. Row 0 = NDC y=-1."""
    c = ctx(); global _prog
    if _prog is None: _prog = c.program(vertex_shader=_VS, fragment_shader=_FS)
    vb = c.buffer(np.ascontiguousarray(v, np.float32)); ab = c.buffer(np.ascontiguousarray(attr, np.float32))
    ib = c.buffer(np.ascontiguousarray(f, np.int32))
    vao = c.vertex_array(_prog, [(vb, '3f', 'p'), (ab, '3f', 'a')], ib)
    fbo = c.framebuffer([c.texture((res, res), 4, dtype='f4')], c.depth_texture((res, res)))
    fbo.use(); fbo.clear(0, 0, 0, 0, depth=1.0)
    c.enable(moderngl.DEPTH_TEST) if not uvmode else c.disable(moderngl.DEPTH_TEST)
    c.disable(moderngl.CULL_FACE)
    _prog['M'].write(np.ascontiguousarray((np.eye(4) if M is None else M).T, np.float32))
    _prog['uvmode'].value = int(uvmode); _prog['outpos'].value = int(outpos)
    vao.render(moderngl.TRIANGLES)
    img = np.frombuffer(fbo.color_attachments[0].read(), np.float32).reshape(res, res, 4).copy()
    dep = np.frombuffer(fbo.depth_attachment.read(), np.float32).reshape(res, res).copy()
    for o in (vao, vb, ab, ib, fbo): o.release()
    return img, dep

def ortho_cams(elev, azim, dist=1.8, half=0.55):
    """Same convention as MV-Adapter get_orthogonal_camera (z-up std frame). Returns list of (mvp, campos)."""
    out = []
    for e, a in zip(elev, azim):
        e, a = np.radians(e), np.radians(a)
        cp = dist * np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
        look = -cp / np.linalg.norm(cp); up = np.array([0, 0, 1.0])
        r = np.cross(look, up); r /= np.linalg.norm(r); u = np.cross(r, look); u /= np.linalg.norm(u)
        c2w = np.eye(4); c2w[:3, 0], c2w[:3, 1], c2w[:3, 2], c2w[:3, 3] = r, u, -look, cp
        n, fa = 0.1, 100.0; P = np.zeros((4, 4))
        P[0, 0] = 1 / half; P[1, 1] = -1 / half; P[2, 2] = -2 / (fa - n); P[2, 3] = -(fa + n) / (fa - n); P[3, 3] = 1
        out.append((P @ np.linalg.inv(c2w), cp))
    return out

def to_std(v, n=None):
    """mesh (y-up, head toward -x) -> centred, |max|=0.5, std frame (z-up). front('-x') faces the azimuth -90 camera."""
    c = (v.max(0) + v.min(0)) / 2; vs = v - c; vs = vs / np.abs(vs).max() * 0.5
    T = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], np.float32)   # std=(-x, z, y)
    return (vs @ T.T).astype(np.float32), (None if n is None else (n @ T.T).astype(np.float32))

def bake(vs, ns, f, uv, views, cams, tex=1024, power=4.0, masks=None):
    """Project view images onto UVs. views: list of float [H,W,3] 0..1. Returns tex [tex,tex,3], filled mask."""
    pos_uv, _ = _raster_uv_attr(vs, f, uv, vs, tex)
    nrm_uv, _ = _raster_uv_attr(vs, f, uv, ns, tex)
    cov = pos_uv[..., 3] > 0; P = pos_uv[cov][:, :3]; N = nrm_uv[cov][:, :3]
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    acc = np.zeros((len(P), 3)); wsum = np.zeros(len(P)); best = np.zeros(len(P))
    for i, (img, (M, cp)) in enumerate(zip(views, cams)):
        H = img.shape[0]
        _, dep = raster(vs, f, ns, M=M, res=H)
        clip = np.c_[P, np.ones(len(P))] @ M.T; ndc = clip[:, :3] / clip[:, 3:]
        px = ((ndc[:, 0] + 1) / 2 * H - 0.5); py = ((ndc[:, 1] + 1) / 2 * H - 0.5)
        ix = np.clip(np.round(px).astype(int), 0, H - 1); iy = np.clip(np.round(py).astype(int), 0, H - 1)
        z = ndc[:, 2] * 0.5 + 0.5
        vis = z <= dep[iy, ix] + 2e-3
        d = cp / np.linalg.norm(cp); cos = (N @ d).clip(0, 1)
        if masks is not None: vis &= masks[i][iy, ix] > 0.5
        w = np.where(vis, cos ** power, 0) * (cos > 0.15)
        col = bilerp(img.astype(np.float32), px, py)
        acc += col * w[:, None]; wsum += w
    out = np.zeros((tex, tex, 3), np.float32); have = np.zeros((tex, tex), bool)
    ok = wsum > 1e-4; tmp = np.zeros((len(P), 3)); tmp[ok] = acc[ok] / wsum[ok, None]
    out[cov] = tmp; hv = np.zeros(len(P), bool); hv[ok] = True; have[cov] = hv
    return out, have, cov

def bilerp(img, x, y):
    H, W = img.shape[:2]; x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)

def _raster_uv_attr(vs, f, uv, attr, tex):
    c = ctx(); global _prog
    vsrc = '''#version 430
in vec2 t; in vec3 a; out vec3 va; void main(){ va=a; gl_Position=vec4(t*2.0-1.0,0.0,1.0);}'''
    fsrc = '''#version 430
in vec3 va; out vec4 o; void main(){ o=vec4(va,1.0);}'''
    pr = c.program(vertex_shader=vsrc, fragment_shader=fsrc)
    tb = c.buffer(np.ascontiguousarray(uv, np.float32)); ab = c.buffer(np.ascontiguousarray(attr, np.float32)); ib = c.buffer(np.ascontiguousarray(f, np.int32))
    vao = c.vertex_array(pr, [(tb, '2f', 't'), (ab, '3f', 'a')], ib)
    fbo = c.framebuffer([c.texture((tex, tex), 4, dtype='f4')]); fbo.use(); fbo.clear(0, 0, 0, 0); c.disable(moderngl.DEPTH_TEST)
    vao.render(moderngl.TRIANGLES)
    img = np.frombuffer(fbo.color_attachments[0].read(), np.float32).reshape(tex, tex, 4).copy()
    for o in (vao, tb, ab, ib, fbo, pr): o.release()
    return img, None

def fill_uv(tex, have, cov, pad=16):
    """Fill un-seen texels (inside charts) by OpenCV inpaint, then dilate outside charts for mip safety."""
    t8 = (tex.clip(0, 1) * 255).astype(np.uint8)
    hole = (cov & ~have).astype(np.uint8)
    if hole.any():
        small = cv2.resize(t8, (512, 512), interpolation=cv2.INTER_AREA)
        inp = cv2.inpaint(small, ((cv2.resize((~have).astype(np.uint8), (512, 512), interpolation=cv2.INTER_NEAREST)) * 255), 5, cv2.INPAINT_TELEA)
        up = cv2.resize(inp, t8.shape[:2][::-1], interpolation=cv2.INTER_LINEAR)
        t8[hole > 0] = up[hole > 0]
    img = t8.astype(np.float32); cur = cov.copy(); k = np.ones((3, 3), np.float32)
    for _ in range(pad):
        s = cv2.filter2D(img * cur[..., None], -1, k, borderType=cv2.BORDER_CONSTANT)
        cn = cv2.filter2D(cur.astype(np.float32), -1, k, borderType=cv2.BORDER_CONSTANT)
        new = (~cur) & (cn > 0); img[new] = s[new] / cn[new][:, None]; cur |= new
    return img.clip(0, 255).astype(np.uint8)

def export(d, v, f, uv, tex8):
    """tex8 is in raster layout (row0 = v=0). glTF/PIL want row0 = v=1 -> flip."""
    os.makedirs(d, exist_ok=True)
    im = Image.fromarray(tex8[::-1].copy()); im.save(os.path.join(d, 'albedo.png'))
    mat = trimesh.visual.material.PBRMaterial(baseColorTexture=im, metallicFactor=0.0, roughnessFactor=0.9)
    m = trimesh.Trimesh(v, f, process=False, visual=trimesh.visual.TextureVisuals(uv=uv, material=mat))
    m.export(os.path.join(d, 'textured.glb'))

def preview(d, v, f, uv, tex8, R=768):
    """Same layout as glb_preview21.py: centre/normalise, rotate about Y at 0/90/180/270, white bg, 4 tiles."""
    vc = v - v.mean(0); vc = vc / np.abs(vc).max(); tiles = []
    for az in [0, 90, 180, 270]:
        a = np.radians(-az); rot = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
        p = vc @ rot.T * 0.9; M = np.eye(4); M[2, 2] = -0.5  # nearer = larger z in glb_preview21 -> flip for GL less-depth
        img, _ = raster(p.astype(np.float32), f, np.c_[uv, np.zeros(len(uv))], M=M, res=R)
        msk = img[..., 3] > 0; t = img[..., :2]; H = tex8.shape[0]
        px = (t[..., 0] * (H - 1)).astype(np.float32); py = (t[..., 1] * (H - 1)).astype(np.float32)
        col = cv2.remap(tex8, px, py, cv2.INTER_LINEAR)
        out = np.full((R, R, 3), 255, np.uint8); out[msk] = col[msk]; tiles.append(out[::-1])
    Image.fromarray(np.concatenate(tiles, 1)).save(os.path.join(d, 'preview.png'))

