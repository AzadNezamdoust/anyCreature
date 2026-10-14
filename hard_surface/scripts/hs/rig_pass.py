"""
rig_pass.py -- the FUNCTION (rig) stage of the Blender hard-surface workflow. Contract: scripts/hs/rig.md.

  cd D:\\Git\\anyCreature\\hard_surface
  "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" -b --factory-startup --python-exit-code 1 ^
      --python scripts/hs/rig_pass.py -- --subject <s> [--rig <json>] [--build <py>] [--out-dir <dir>]
      [--no-render] [--no-judge]

Loads out/blender-hs/<s>/build.py (the look stage's build() -> (root, parts)) and out/blender-hs/<s>/rig.json, regroups
the parts under joint nodes (empties with their origins AT the pivots; no armature, no geometry change), and tests:
  a. pivot sanity     wheel / rotor run-out about the spin axis, turret pivot on its ring centre, trunnion on the bore
  b. clearance sweeps every joint through (and past) its limits, BVH overlap of the moving group against the rest
  c. ground / static  wheel + track + skid bottoms on the ground plane, mass, COM, support polygon, tip-over angles
  d. physics          rig_sim.py: drop + settle, 0.15 m bump at speed, accelerate / brake pitch, lateral load
  e. evidence         rig_sheet.png (posed contact sheet + the test table), rig_stats.json (PASS / FAIL per test)
  f. export           <s>_rigged.glb (node hierarchy, named joints, baked clips) + <s>_rig.json (rig.json + derived
                      mass / COM / inertia / colliders / measured clear ranges); tris and the look-stage judge numbers
                      must reproduce (regrouping only).
Exit code 1 = it could not run (bad rig.json, build raised). Test failures do NOT fail the process: read rig_stats.json.

run_pass.py is reused as a library without editing it: its source is executed minus the trailing `main()` call.
"""
import json
import math
import os
import shutil
import struct
import sys
import time
import types

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rig_sim  # noqa: E402
import glb_motion  # noqa: E402


def _load_run_pass():
    path = os.path.join(HERE, "run_pass.py")
    with open(path, encoding="utf-8") as f:
        src = f.read().rstrip()
    if not src.endswith("\nmain()"):
        raise SystemExit("rig_pass.py: run_pass.py no longer ends with a bare main() call; update _load_run_pass")
    mod = types.ModuleType("hs_run_pass")
    mod.__file__ = path
    exec(compile(src[:-len("main()")], path, "exec"), mod.__dict__)
    return mod


rp = _load_run_pass()
from hs import A  # noqa: E402  (after run_pass put scripts/hs on sys.path too)

SUBJECT, SDIR, ODIR, ROOTDIR = rp.SUBJECT, rp.SDIR, rp.ODIR, rp.ROOTDIR
RIG_PATH = os.path.abspath(os.path.join(ROOTDIR, rp._arg("--rig"))) if rp._arg("--rig") else os.path.join(SDIR, "rig.json")
NO_RENDER = "--no-render" in rp.argv
NO_JUDGE = "--no-judge" in rp.argv
if not os.path.exists(RIG_PATH):
    raise SystemExit(f"rig_pass.py: {RIG_PATH} missing (the rig contract: scripts/hs/rig.md)")
RIG = rp._json(RIG_PATH)
TOL = {"collide_m": 0.002, "pivot_m": 0.001, "ground_m": 0.005, "ring_m": 0.005, "bore_m": 0.03,
       **(RIG.get("tolerances") or {})}
PHYS = RIG.get("physics") or {}
GROUND_Y = float(PHYS.get("ground_y", 0.0))

ROTARY = {"turret_yaw", "weapon_pitch", "wheel_spin", "wheel_steer", "rotor_spin", "door", "hatch",
          "suspension_arm"}          # suspension_arm: a swing / trailing arm (rotary suspension, limits in deg)
PRISMATIC = {"suspension"}
STATIC = {"track_scroll", "fixed"}
CONTINUOUS = {"wheel_spin", "rotor_spin"}
CLIPS = {"turret_yaw": "TurretYaw", "weapon_pitch": "WeaponPitch", "wheel_spin": "WheelsRoll", "wheel_steer": "Steer",
         "suspension": "Suspension", "rotor_spin": "RotorSpin", "suspension_arm": "Suspension"}

# WF v10 — handheld weapons (rig.md "Handheld weapons"): physics.mode "handheld" = no ground / stability / drive sim
# (mass + COM still estimated), the weapon joint types below, and rig.json `sockets`. Additive: a vehicle rig uses none.
HANDHELD = PHYS.get("mode") == "handheld"
W_ROTARY = {"trigger", "barrel_spin", "cylinder", "hinge", "selector"}
W_PRISMATIC = {"slide", "magazine"}
ROTARY |= W_ROTARY
PRISMATIC |= W_PRISMATIC
CONTINUOUS |= {"barrel_spin", "cylinder"}
CLIPS.update({"trigger": "Fire", "slide": "Fire", "magazine": "Reload", "barrel_spin": "SpinUp", "cylinder": "CylinderIndex",
              "hinge": "Open", "selector": "Selector"})
SOCKETS = RIG.get("sockets") or []
# 2026-10-10 — `scale` joint (rig.md "Scale joints"): parts that compress / extend (a spring, a bellows, an inflating
# bladder) scale along one principal axis about the pivot plane; value = the far end's displacement along the axis (m),
# scale = 1 + value / length. `follow` drives it from a prismatic joint so the far end tracks that joint's slide.
SCALE = {"scale"}
CLIPS["scale"] = "Scale"
TOL.setdefault("socket_m", 0.02)        # a socket lies within this of the surface it names
TOL.setdefault("bore_socket_m", 0.003)  # the muzzle socket's distance off the bore line

# effective densities (kg per m3 of the part's closed mesh volume): hollow shells, not solid steel
DENSITY = {"armour_light": 1150.0, "armour_heavy": 1900.0, "turret_light": 1500.0, "turret_heavy": 2600.0,
           "soft_skin": 300.0, "cargo": 150.0, "wheel": 600.0, "track": 1500.0, "gun": 4000.0, "airframe": 110.0,
           "rotor": 300.0, "detail": 1500.0, "none": 0.0,
           # handheld weapons (effective, of the closed mesh volume): a bored steel barrel / bolt, a hollow alloy
           # receiver, hollow polymer furniture, a loaded magazine, optics
           "weapon_steel": 5000.0, "weapon_alloy": 1300.0, "polymer": 450.0, "magazine_loaded": 1400.0, "optic": 900.0,
           # bulk material densities (2026-10-10, rig.md "Mass: the honest rule"): used with mass.shell, the fraction of
           # the drawn closed volume that is material in the real object (1 = genuinely solid)
           "steel": 7850.0, "aluminium": 2700.0, "polymer_solid": 1300.0, "rubber": 1150.0, "brass": 8500.0,
           "glass": 2500.0}

TESTS = {}


def record(name, ok, **info):
    TESTS[name] = {"pass": bool(ok), **info}
    print("TEST", "PASS" if ok else "FAIL", name, json.dumps(info, default=float))


def author(v):
    """Blender vector -> author (x, y, z)."""
    return (v[0], v[2], -v[1])


# ------------------------------------------------------------------------------------------------ parts
class Part:
    def __init__(self, ob, source):
        self.ob, self.name, self.source, self.role = ob, ob.name, source, ob.get("part", ob.name)
        me = ob.data
        me.calc_loop_triangles()
        mw = ob.matrix_world
        self.V = np.array([author(mw @ v.co) for v in me.vertices], dtype=np.float64).reshape(-1, 3)
        self.T = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int64).reshape(-1, 3)
        self.joint = -1
        a, b, c = self.V[self.T[:, 0]], self.V[self.T[:, 1]], self.V[self.T[:, 2]]
        self.volume = abs(float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0)
        tv = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
        s = tv.sum()
        self.centroid = ((a + b + c) / 4.0 * tv[:, None]).sum(axis=0) / s if abs(s) > 1e-12 else self.V.mean(axis=0)
        self.lo, self.hi = self.V.min(axis=0), self.V.max(axis=0)


def islands_of(bm):
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            u = stack.pop()
            comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        out.append(comp)
    return out


def split_part(ob, box, new_name):
    """Move the mesh islands of `ob` whose bbox centre (author frame) lies inside `box` into a new object."""
    lo, hi = box
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    mw = ob.matrix_world
    pick = set()
    for comp in islands_of(bm):
        pts = np.array([author(mw @ v.co) for v in comp])
        c = (pts.min(axis=0) + pts.max(axis=0)) / 2
        if all(lo[k] - 1e-9 <= c[k] <= hi[k] + 1e-9 for k in range(3)):
            pick.update(v.index for v in comp)
    if not pick:
        bm.free()
        raise SystemExit(f"rig_pass.py: selector {new_name}: no island of '{ob.name}' has its bbox centre in {box}")
    me2 = ob.data.copy()
    me2.name = new_name
    bm2 = bmesh.new()
    bm2.from_mesh(me2)
    bmesh.ops.delete(bm2, geom=[v for v in bm2.verts if v.index not in pick], context="VERTS")
    bm2.to_mesh(me2)
    bm2.free()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in pick], context="VERTS")
    bm.to_mesh(ob.data)
    left = len(bm.verts)
    bm.free()
    nob = bpy.data.objects.new(new_name, me2)
    nob["part"] = ob.get("part", ob.name)
    bpy.context.scene.collection.objects.link(nob)
    nob.parent = ob.parent
    nob.matrix_world = ob.matrix_world.copy()
    return nob, left


# ------------------------------------------------------------------------------------------------ joints
def unit(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise SystemExit("rig_pass.py: zero-length axis in rig.json")
    return v / n


def rot3(axis, ang):
    x, y, z = axis
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


class Rig:
    def __init__(self, objs):
        self.objs = {o.name: o for o in objs}
        self.source = {o.name: o.name for o in objs}
        js = RIG.get("joints") or []
        ids = [j["id"] for j in js]
        if len(set(ids)) != len(ids):
            raise SystemExit("rig_pass.py: duplicate joint ids in rig.json")
        order, done = [], set()
        while len(order) < len(js):
            n = len(order)
            for j in js:
                if j["id"] not in done and (j.get("parent") is None or j["parent"] in done):
                    order.append(j)
                    done.add(j["id"])
            if len(order) == n:
                raise SystemExit("rig_pass.py: joint parent cycle / unknown parent in rig.json")
        self.joints = order
        self.jid = {j["id"]: i for i, j in enumerate(order)}
        for j in order:
            if j["type"] not in ROTARY | PRISMATIC | STATIC | SCALE:
                raise SystemExit(f"rig_pass.py: joint {j['id']}: unknown type {j['type']}")
            j["_axis"] = unit(j.get("axis", [0, 1, 0]))
            j["_pivot"] = np.array(j.get("pivot", [0, 0, 0]), dtype=np.float64)
            j["_parent"] = self.jid[j["parent"]] if j.get("parent") is not None else -1
            j["_names"] = []
            if j["id"] in self.objs:
                raise SystemExit(f"rig_pass.py: joint id '{j['id']}' is also a part name; node names must be unique")
        # selectors first (they take islands out of their source object), then plain names
        for j in order:
            for ref in j.get("parts", []):
                if isinstance(ref, dict):
                    src = ref["part"]
                    if src not in self.objs:
                        raise SystemExit(f"rig_pass.py: joint {j['id']}: no part '{src}' (have {sorted(self.objs)})")
                    name = ref.get("name") or f"{j['id']}_{src}"
                    nob, left = split_part(self.objs[src], ref["box"], name)
                    self.objs[nob.name] = nob
                    self.source[nob.name] = src
                    j["_names"].append(nob.name)
                    if left == 0:
                        ob = self.objs.pop(src)
                        me = ob.data
                        bpy.data.objects.remove(ob)
                        bpy.data.meshes.remove(me)
        claimed = {}
        for j in order:
            for ref in j.get("parts", []):
                if isinstance(ref, str):
                    if ref not in self.objs:
                        raise SystemExit(f"rig_pass.py: joint {j['id']}: no part '{ref}' (have {sorted(self.objs)})")
                    if ref in claimed:
                        raise SystemExit(f"rig_pass.py: part '{ref}' is claimed by {claimed[ref]} and {j['id']}")
                    claimed[ref] = j["id"]
                    j["_names"].append(ref)
        bpy.context.view_layer.update()
        self.parts = [Part(o, self.source[n]) for n, o in self.objs.items()]
        self.pid = {p.name: i for i, p in enumerate(self.parts)}
        for j in order:
            for n in j["_names"]:
                self.parts[self.pid[n]].joint = self.jid[j["id"]]
        self.sub = []
        for i in range(len(order)):
            s = {i}
            grew = True
            while grew:
                grew = False
                for k, j in enumerate(order):
                    if j["_parent"] in s and k not in s:
                        s.add(k)
                        grew = True
            self.sub.append(s)
        # contacts: {a, b[, seat {centre, r}]} -> {(pa, pb): None | bool mask over a's triangles}
        self.contacts = {}
        for c in RIG.get("contacts") or []:
            for k in ("a", "b"):
                if c[k] not in self.pid:
                    raise SystemExit(f"rig_pass.py: contact names unknown part '{c[k]}' (have {sorted(self.pid)})")
            pa, pb = self.pid[c["a"]], self.pid[c["b"]]
            mask = None
            if c.get("seat"):
                P = self.parts[pa]
                d = np.linalg.norm(P.V - np.array(c["seat"]["centre"], dtype=np.float64), axis=1) <= c["seat"]["r"]
                mask = d[P.T].all(axis=1)
            self.contacts[(pa, pb)] = mask
        self._cache = {}
        self._setup_scale()

    def _setup_scale(self):
        """scale joints: length, follow master, no children, a principal axis (glTF node scale is per local axis)."""
        self.followers = {}
        for ji, j in enumerate(self.joints):
            if j["type"] not in SCALE:
                continue
            a = j["_axis"]
            if float(np.abs(a).max()) < 1 - 1e-9:
                raise SystemExit(f"rig_pass.py: scale joint {j['id']}: axis must be a principal axis (+-x / y / z), got {a.tolist()}")
            if any(k["_parent"] == ji for k in self.joints):
                raise SystemExit(f"rig_pass.py: scale joint {j['id']} has child joints (they would inherit its scale)")
            own = [p.V for p in self.parts if p.joint == ji]
            if not own:
                raise SystemExit(f"rig_pass.py: scale joint {j['id']}: no parts")
            h = (np.vstack(own) - j["_pivot"]) @ a
            j["_base"], j["_extent"] = float(h.min()), float(h.max())
            # "length": null (a spec skeleton's placeholder) = the measured extent, like an absent key (2026-10-11)
            j["_L"] = float(j["_extent"] if j.get("length") is None else j["length"])
            if j["_L"] <= 1e-4:
                raise SystemExit(f"rig_pass.py: scale joint {j['id']}: length {j['_L']} <= 0 (pivot above its parts?)")
            fol = j.get("follow")
            if fol is not None:
                fol = {"joint": fol} if isinstance(fol, str) else fol
                mid = fol.get("joint")
                if mid not in self.jid:
                    raise SystemExit(f"rig_pass.py: scale joint {j['id']}: follow names unknown joint '{mid}'")
                m = self.joints[self.jid[mid]]
                if m["type"] not in PRISMATIC or m["_parent"] != j["_parent"] or not m.get("limits"):
                    raise SystemExit(f"rig_pass.py: scale joint {j['id']}: follow needs a limited prismatic joint with the same "
                                     f"parent ({mid} is {m['type']}, parent {m.get('parent')})")
                # far-end displacement along this axis per unit of the master's value
                j["_follow"] = (mid, float(fol.get("ratio", 1.0)) * float(m["_axis"] @ a))
                self.followers.setdefault(mid, []).append(j)
                vals = [j["_follow"][1] * float(v) for v in m["limits"]]
            elif j.get("limits"):
                vals = [float(v) for v in j["limits"]]
            else:
                raise SystemExit(f"rig_pass.py: scale joint {j['id']}: needs limits (m of far-end travel) or follow")
            j["_vals"] = (min(vals), max(vals))
            if 1 + j["_vals"][0] / j["_L"] <= 0.05:
                raise SystemExit(f"rig_pass.py: scale joint {j['id']}: scale {1 + j['_vals'][0] / j['_L']:.3f} at the limit (<= 0.05)")
        # a sweep whose moving group drives a follower that is NOT in the group: the "other" geometry moves too
        self._moves_other = []
        for ji in range(len(self.joints)):
            ids = {self.joints[k]["id"] for k in self.sub[ji]}
            self._moves_other.append(any(f["_follow"][0] in ids and self.jid[f["id"]] not in self.sub[ji]
                                         for fs in self.followers.values() for f in fs))

    def resolve(self, pose):
        """Pose + the values of the scale joints that follow a master (their own entry, if any, is overridden)."""
        pose = dict(pose or {})
        for j in self.joints:
            if j.get("_follow"):
                pose[j["id"]] = j["_follow"][1] * float(pose.get(j["_follow"][0], 0.0))
        return pose

    def scale_of(self, j, val):
        return 1.0 + float(val) / j["_L"]

    # -- pose
    def local(self, j, val, tilt=None):
        M = np.eye(4)
        p = j["_pivot"]
        if j["type"] in ROTARY:
            R = rot3(j["_axis"], math.radians(val))
            if tilt is not None:
                R = rot3(unit(tilt[0]), math.radians(tilt[1])) @ R
            M[:3, :3] = R
            M[:3, 3] = p - R @ p
        elif j["type"] in PRISMATIC:
            M[:3, 3] = j["_axis"] * val
        elif j["type"] in SCALE:
            S = np.eye(3) + (self.scale_of(j, val) - 1.0) * np.outer(j["_axis"], j["_axis"])
            M[:3, :3] = S
            M[:3, 3] = p - S @ p
        return M

    def mats(self, pose=None, tilt=None):
        pose, tilt = self.resolve(pose), tilt or {}
        out = []
        for j in self.joints:
            L = self.local(j, pose.get(j["id"], 0.0), tilt.get(j["id"]))
            out.append(L if j["_parent"] < 0 else out[j["_parent"]] @ L)
        return out

    def world(self, pi, mats):
        P = self.parts[pi]
        if P.joint < 0:
            return P.V
        M = mats[P.joint]
        return P.V @ M[:3, :3].T + M[:3, 3]

    def gather(self, pids, mats):
        Vs, Ts, own, loc, off = [], [], [], [], 0
        for pi in pids:
            W = self.world(pi, mats)
            T = self.parts[pi].T
            Vs.append(W)
            Ts.append(T + off)
            own.append(np.full(len(T), pi))
            loc.append(np.arange(len(T)))
            off += len(W)
        V, T = np.vstack(Vs), np.vstack(Ts)
        return {"V": V, "T": T, "own": np.concatenate(own), "loc": np.concatenate(loc),
                "bvh": BVHTree.FromPolygons(V.tolist(), T.tolist(), epsilon=0.0)}

    def collide(self, ji, pose, tilt=None, key=None):
        """Deepest interpenetration (m) of joint ji's moving group against everything else in `pose`.
        -> (depth, 'moving part > other part')."""
        mats = self.mats(pose, tilt)
        mov = [i for i, p in enumerate(self.parts) if p.joint in self.sub[ji]]
        if not mov:
            return 0.0, ""
        if self._moves_other[ji]:
            key = None      # a follower outside the moving group moves with it: never reuse the static geometry
        ck = (ji, key)
        if key is None or ck not in self._cache:
            oth = [i for i, p in enumerate(self.parts) if p.joint not in self.sub[ji]]
            other = self.gather(oth, mats)
            if key is not None:
                self._cache = {ck: other}
        else:
            other = self._cache[ck]
        m = self.gather(mov, mats)
        pairs = m["bvh"].overlap(other["bvh"])
        if not pairs:
            return 0.0, ""
        ia = np.fromiter((p[0] for p in pairs), dtype=np.int64, count=len(pairs))
        ib = np.fromiter((p[1] for p in pairs), dtype=np.int64, count=len(pairs))
        oa, ob = m["own"][ia], other["own"][ib]
        keep = np.ones(len(ia), dtype=bool)
        for (pa, pb), mask in self.contacts.items():
            sel = (oa == pa) & (ob == pb)
            if sel.any():
                keep &= ~(sel if mask is None else sel & mask[np.minimum(m["loc"][ia], len(mask) - 1)])   # clip: loc of OTHER parts may exceed a's mask
            sel = (oa == pb) & (ob == pa)
            if sel.any():
                keep &= ~(sel if mask is None else sel & mask[np.minimum(other["loc"][ib], len(mask) - 1)])
        if not keep.any():
            return 0.0, ""
        ia, ib, oa, ob = ia[keep], ib[keep], oa[keep], ob[keep]
        TA, TB = m["V"][m["T"][ia]], other["V"][other["T"][ib]]

        def nrm(Tr):
            n = np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0])
            return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
        nA, nB = nrm(TA), nrm(TB)
        dA = np.clip(-np.einsum("kvj,kj->kv", TA - TB[:, 0:1], nB).min(axis=1), 0, None)
        dB = np.clip(-np.einsum("kvj,kj->kv", TB - TA[:, 0:1], nA).min(axis=1), 0, None)
        d = np.minimum(dA, dB)
        k = int(d.argmax())
        return float(d[k]), f"{self.parts[oa[k]].name} > {self.parts[ob[k]].name}"

    def joint_verts(self, ji, own_only=True):
        ps = [p for p in self.parts if (p.joint == ji if own_only else p.joint in self.sub[ji])]
        return np.vstack([p.V for p in ps]) if ps else np.zeros((0, 3))


def _arm_wheel(rig, sj):
    """suspension_arm: the wheel_spin joint it carries (first descendant), else None."""
    ji = rig.jid[sj["id"]]
    return next((k for i, k in enumerate(rig.joints) if i in rig.sub[ji] and k["type"] == "wheel_spin"), None)


def susp_metres(rig, sj, val):
    """Joint value -> the wheel's VERTICAL travel (m, + = compression). Vertical prismatic: identity; a raked
    prismatic axis (bike fork): val * axis.y; a suspension_arm (deg): the rise of its wheel centre."""
    if sj["type"] == "suspension_arm":
        w = _arm_wheel(rig, sj)
        r = (w["_pivot"] if w is not None else sj["_pivot"]) - sj["_pivot"]
        return float((rot3(sj["_axis"], math.radians(val)) @ r - r)[1])
    return float(val) * float(abs(sj["_axis"][1])) if abs(sj["_axis"][1]) < 0.9999 else float(val)


def susp_value(rig, sj, m):
    """Inverse of susp_metres (bisection for an arm, within +-60 deg)."""
    if sj["type"] != "suspension_arm":
        return float(m) / float(abs(sj["_axis"][1])) if 1e-6 < abs(sj["_axis"][1]) < 0.9999 else float(m)
    lo, hi = -60.0, 60.0
    up = susp_metres(rig, sj, hi) > susp_metres(rig, sj, lo)
    for _ in range(40):
        mid = (lo + hi) / 2
        if (susp_metres(rig, sj, mid) < m) == up:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def perp_basis(axis):
    a = np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0])
    u = unit(np.cross(axis, a))
    return u, np.cross(axis, u)


# ------------------------------------------------------------------------------------------------ a. pivot sanity
def test_pivots(rig):
    for ji, j in enumerate(rig.joints):
        t, ax, pv = j["type"], j["_axis"], j["_pivot"]
        name = f"pivot:{j['id']}"
        if t in CONTINUOUS:
            V = rig.joint_verts(ji, own_only=False)
            if not len(V):
                record(name, False, why="no parts")
                continue
            if j.get("run_pose"):     # optional {joint id: value}: judge the spinning group in its RUNNING pose (a
                rm = rig.mats(j["run_pose"])     # parked rotor's drooped blade raised by its flap joint), not at rest
                V = np.vstack([rig.world(pi, rm) for pi, p in enumerate(rig.parts) if p.joint in rig.sub[ji]])
            u, v = perp_basis(ax)
            d = V - pv
            pu, pw, pa = d @ u, d @ v, d @ ax
            r = np.hypot(pu, pw)
            R = float(r.max())
            rim = r > 0.9 * R
            # least-squares circle through the rim vertices (exact for any n-fold symmetric wheel / rotor)
            Am = np.column_stack([2 * pu[rim], 2 * pw[rim], np.ones(rim.sum())])
            sol = np.linalg.lstsq(Am, pu[rim] ** 2 + pw[rim] ** 2, rcond=None)[0]
            radial = float(math.hypot(sol[0], sol[1]))
            # axial run-out: slope of the rim vertices' axial coordinate across the wheel plane, at the rim
            Bm = np.column_stack([pu[rim], pw[rim], np.ones(rim.sum())])
            sl = np.linalg.lstsq(Bm, pa[rim], rcond=None)[0]
            axial = float(math.hypot(sl[0], sl[1]) * R)
            bb = float(math.hypot((pu.min() + pu.max()) / 2, (pw.min() + pw.max()) / 2))
            # bbox over a full turn (faceting ripple of an n-gon is expected; reported, not judged)
            ext = []
            for k in range(72):
                a = math.radians(5 * k)
                ext.append((pu * math.cos(a) - pw * math.sin(a)).max())
            # an odd n-fold wheel (23 knobs) has its static bbox centre off by half the facet ripple: judge the
            # bbox centre's first harmonic over the turn (= a real eccentricity) when that is smaller
            cen = [((pu * math.cos(math.radians(5 * k)) - pw * math.sin(math.radians(5 * k))).min() + ext[k]) / 2
                   for k in range(72)]
            bb_turn = 2 * float(math.hypot(sum(c * math.cos(math.radians(5 * k)) for k, c in enumerate(cen)),
                                           sum(c * math.sin(math.radians(5 * k)) for k, c in enumerate(cen)))) / 72
            extra, ok_w = {}, True
            if t in W_ROTARY:     # barrel_spin / cylinder: the axis is the bore direction; a cylinder indexes n chambers
                extra["axis_vs_bore_deg"] = round(math.degrees(math.acos(min(1.0, abs(float(ax[2]))))), 2)
                ok_w = extra["axis_vs_bore_deg"] <= 2.0 or bool(j.get("free_axis"))
                n = int(j.get("chambers", 0))
                if t == "cylinder":
                    ok_w = ok_w and n >= 2
                if n >= 2:     # n-fold symmetry: the vertex set turned by 360 / n lands on itself
                    Rn = rot3(ax, 2 * math.pi / n)
                    Q = d @ Rn.T
                    P_ = d[:: max(1, len(d) // 3000)]
                    worst_i = 0.0
                    for a0 in range(0, len(P_), 256):
                        dd = np.linalg.norm(P_[a0:a0 + 256, None, :] - Q[None, :, :], axis=2).min(axis=1)
                        worst_i = max(worst_i, float(dd.max()))
                    extra.update(chambers=n, index_deg=round(360.0 / n, 3), index_symmetry_err_mm=round(worst_i * 1000, 3))
                    ok_w = ok_w and worst_i <= TOL["pivot_m"]
            record(name, radial <= TOL["pivot_m"] and axial <= TOL["pivot_m"] and min(bb, bb_turn) <= TOL["pivot_m"] and ok_w,
                   type=t, radius_m=round(R, 4), radial_runout_mm=round(radial * 1000, 3),
                   axial_runout_mm=round(axial * 1000, 3), bbox_centre_off_mm=round(bb * 1000, 3),
                   bbox_centre_turn_mm=round(bb_turn * 1000, 3),
                   facet_ripple_mm=round((max(ext) - min(ext)) * 1000, 2), tol_mm=TOL["pivot_m"] * 1000, **extra)
        elif t == "turret_yaw":
            V = rig.joint_verts(ji)
            if not len(V):
                record(name, False, why="no parts")
                continue
            u, v = perp_basis(ax)
            d = V - pv
            h = d @ ax
            ring = h <= h.min() + 0.03
            cu = (d[ring] @ u).min() / 2 + (d[ring] @ u).max() / 2
            cv = (d[ring] @ v).min() / 2 + (d[ring] @ v).max() / 2
            off = float(math.hypot(cu, cv))
            allv = rig.joint_verts(ji, own_only=False) - pv
            record(name, off <= TOL["ring_m"], type=t, ring_centre_off_mm=round(off * 1000, 2),
                   tol_mm=TOL["ring_m"] * 1000, ring_radius_m=round(float(np.hypot(d[ring] @ u, d[ring] @ v).max()), 4),
                   swept_radius_m=round(float(np.hypot(allv @ u, allv @ v).max()), 4))
        elif t == "weapon_pitch":
            V = rig.joint_verts(ji, own_only=False)
            if j.get("bore_parts"):   # optional: fit the bore line to these parts only (a shield / ammo box on the
                bp = [p.V for p in rig.parts if p.name in j["bore_parts"]]   # pitching group skews the group's PCA)
                V = np.vstack(bp) if bp else V
            if not len(V):
                record(name, False, why="no parts")
                continue
            c = V.mean(axis=0)
            w, vec = np.linalg.eigh(np.cov((V - c).T))
            bore = vec[:, int(w.argmax())]
            off = float(np.linalg.norm(np.cross(pv - c, bore)))
            skew = abs(90 - math.degrees(math.acos(min(1.0, abs(float(bore @ ax))))))
            record(name, off <= TOL["bore_m"] and skew <= 2.0, type=t, trunnion_off_bore_mm=round(off * 1000, 2),
                   tol_mm=TOL["bore_m"] * 1000, bore_vs_axis_skew_deg=round(skew, 2))
        elif t == "wheel_steer":
            kids = [k for k in rig.joints if k["_parent"] == ji and k["type"] == "wheel_spin"]
            if not kids:     # bike fork: steer -> telescopic suspension -> wheel
                kids = [k for i, k in enumerate(rig.joints) if i in rig.sub[ji] and k["type"] == "wheel_spin"]
            scrub = float(np.linalg.norm(np.cross(kids[0]["_pivot"] - pv, ax))) if kids else 0.0
            V = rig.joint_verts(ji, own_only=False)
            hw = float(np.ptp((V - pv) @ kids[0]["_axis"]) / 2) if kids and len(V) else 0.0
            record(name, bool(kids) and scrub <= max(hw, 1e-6), type=t, scrub_radius_m=round(scrub, 4),
                   half_width_m=round(hw, 4), kingpin_tilt_deg=round(math.degrees(math.acos(min(1, abs(ax[1])))), 2))
        elif t == "suspension_arm":
            w = _arm_wheel(rig, j)
            arm = float(np.linalg.norm(np.cross(w["_pivot"] - pv, ax))) if w is not None else 0.0
            record(name, w is not None and arm > 0.05 and abs(ax[1]) <= math.sin(math.radians(5)), type=t,
                   arm_m=round(arm, 4), axis_from_horizontal_deg=round(math.degrees(math.asin(min(1, abs(ax[1])))), 2),
                   wheel_travel_m_per_deg=round(susp_metres(rig, j, 1.0), 5))
        elif t in SCALE:
            # the anchored end lies on the pivot plane (pin_m, default 5 mm), the scale stays >= min_scale (0.2) over the
            # travel, and a follower's far end tracks its master (a `length` other than the parts' extent: error =
            # |1 - s| x |extent - length| <= pivot_m)
            L, (v0, v1) = j["_L"], j["_vals"]
            pin = float(j.get("pin_m", 0.005))
            s_lo, s_hi = rig.scale_of(j, v0), rig.scale_of(j, v1)
            track = max(abs(s_lo - 1), abs(s_hi - 1)) * abs(j["_extent"] - L)
            ok = abs(j["_base"]) <= pin and s_lo >= float(j.get("min_scale", 0.2)) and track <= TOL["pivot_m"]
            info = {"type": t, "axis": [round(float(v), 4) for v in ax], "length_m": round(L, 5),
                    "parts_extent_m": round(j["_extent"], 5), "base_off_pivot_mm": round(j["_base"] * 1000, 2),
                    "tol_mm": pin * 1000, "far_end_travel_m": [round(v0, 5), round(v1, 5)],
                    "scale_range": [round(s_lo, 4), round(s_hi, 4)], "track_err_mm": round(track * 1000, 3)}
            if j.get("_follow"):
                info["follow"] = {"joint": j["_follow"][0], "m_per_m": round(j["_follow"][1], 4)}
            record(name, ok, **info)
        elif t == "suspension":
            record(name, abs(ax[1]) >= math.cos(math.radians(40)), type=t,
                   axis_from_vertical_deg=round(math.degrees(math.acos(min(1, abs(ax[1])))), 2))
        elif t in ("trigger", "selector", "hinge"):
            # the pivot pin lies in (or within pin_m of) the bbox of the parts it carries; a trigger / selector turns
            # about the cross axis (x) unless "free_axis"; reports the tip's arc over the limits
            V = rig.joint_verts(ji, own_only=False)
            if not len(V):
                record(name, False, why="no parts")
                continue
            pin = float(j.get("pin_m", 0.02 if t == "hinge" else 0.01))
            gap = float(np.linalg.norm(np.maximum(0, np.maximum(V.min(axis=0) - pv, pv - V.max(axis=0)))))
            cross = abs(float(ax[0])) >= math.cos(math.radians(5))
            d = V - pv
            rad = float(np.linalg.norm(d - np.outer(d @ ax, ax), axis=1).max())
            lim = j.get("limits") or [0, 0]
            ok = gap <= pin and (cross or t == "hinge" or j.get("free_axis")) and bool(j.get("limits"))
            if t == "trigger":      # a small arc: the tip moves 2..25 mm
                arc = rad * math.radians(abs(lim[1] - lim[0]))
                ok = ok and 0.002 <= arc <= 0.025
            record(name, ok, type=t, pivot_off_parts_mm=round(gap * 1000, 2), tol_mm=pin * 1000, axis_is_cross=cross,
                   tip_radius_m=round(rad, 4), tip_arc_mm=round(rad * math.radians(abs(lim[1] - lim[0])) * 1000, 2))
        elif t in W_PRISMATIC:
            # slide (bolt, charging handle, pistol slide, pump): travels along the bore (z) within 2 deg unless
            # "free_axis"; magazine: its axis lies in the bore plane (no x component) and points out of the well
            V = rig.joint_verts(ji, own_only=False)
            if not len(V) or not j.get("limits"):
                record(name, False, why="no parts" if not len(V) else "limits missing")
                continue
            lim = j["limits"]
            travel = abs(lim[1] - lim[0])
            if t == "slide":
                skew = math.degrees(math.acos(min(1.0, abs(float(ax[2])))))
                ok = (skew <= 2.0 or bool(j.get("free_axis"))) and travel >= 0.005
                record(name, ok, type=t, axis_vs_bore_deg=round(skew, 2), travel_m=round(travel, 4))
            else:
                size = float(np.ptp(V @ ax))
                ok = abs(float(ax[0])) <= 0.05 and travel >= 0.5 * size
                record(name, ok, type=t, axis_x=round(float(ax[0]), 4), travel_m=round(travel, 4),
                       magazine_length_along_axis_m=round(size, 4), need_travel_m=round(0.5 * size, 4))


# ------------------------------------------------------------------------------------------------ b. sweeps
def _scan(fn, lo_probe, hi_probe, step):
    """Walk out from 0 in both directions until the first collision. -> report dict."""
    d0, w0 = fn(0.0)
    if d0 > TOL["collide_m"]:
        return {"clear": [0.0, 0.0], "rest_collision": w0, "rest_depth_mm": round(d0 * 1000, 2)}
    out = {"clear": [0.0, 0.0], "probe": [lo_probe, hi_probe]}
    for sign, end, key in ((1, hi_probe, "hi"), (-1, lo_probe, "lo")):
        v, last = 0.0, 0.0
        while True:
            v = round(v + sign * step, 6)
            if (sign > 0 and v > end + 1e-9) or (sign < 0 and v < end - 1e-9):
                break
            d, w = fn(v)
            if d > TOL["collide_m"]:
                out[f"first_hit_{key}"] = {"at": v, "parts": w, "depth_mm": round(d * 1000, 2)}
                break
            last = v
        out["clear"][0 if sign < 0 else 1] = last
    return out


def _ancestor(rig, ji, typ):
    k = rig.joints[ji]["_parent"]
    while k >= 0:
        if rig.joints[k]["type"] == typ:
            return rig.joints[k]
        k = rig.joints[k]["_parent"]
    return None


def test_sweeps(rig):
    measured = {}
    for ji, j in enumerate(rig.joints):
        t, jid = j["type"], j["id"]
        if t in STATIC:
            continue
        name = f"sweep:{jid}"
        lim = j.get("limits")
        t0 = time.time()
        if t in SCALE:
            # a follower is swept by driving its master over the master's limits (+ one step), checking the scaled group
            # against everything else (the master's group posed too); a free scale joint over its own limits
            fol = j.get("_follow")
            if fol:
                m = rig.joints[rig.jid[fol[0]]]
                lo, hi = float(m["limits"][0]), float(m["limits"][1])
                step = float(j.get("step", m.get("step", 0.002 if m["type"] in W_PRISMATIC else 0.005)))
                drive = m["id"]
            else:
                lo, hi = float(lim[0]), float(lim[1])
                step = float(j.get("step", 0.002))
                drive = jid
            pad = list(j.get("probe") or [lo - step, hi + step])
            k = fol[1] if fol else 1.0     # keep the probe's scale > 0.05
            for i_ in (0, 1):
                while abs(k) > 1e-12 and rig.scale_of(j, k * pad[i_]) <= 0.05:
                    pad[i_] += step if i_ == 0 else -step
            r = _scan(lambda v: rig.collide(ji, {drive: v}), pad[0], pad[1], step)
            ok = r["clear"][0] <= lo + 1e-9 and r["clear"][1] >= hi - 1e-9 and "rest_collision" not in r
            info = {"type": t, "driven_by": drive, "limits": [lo, hi], "clear": [round(r["clear"][0], 4), round(r["clear"][1], 4)],
                    "unit": "m", "probe": [round(v, 4) for v in pad], "step": step,
                    "scale_at_limits": [round(rig.scale_of(j, k * lo), 4), round(rig.scale_of(j, k * hi), 4)],
                    "sec": round(time.time() - t0, 1)}
            info.update({x: r[x] for x in ("first_hit_lo", "first_hit_hi", "rest_collision", "rest_depth_mm") if x in r})
            record(name, ok, **info)
            measured[jid] = {"clear": info["clear"], "unit": "m", "driven_by": drive}
            continue
        if t in CONTINUOUS or (t == "turret_yaw" and (lim is None or j.get("continuous"))):
            step = float(j.get("step", 15 if t == "wheel_spin" else 5))
            tilts = [None]
            if j.get("flap_deg"):
                u, v = perp_basis(j["_axis"])
                f = float(j["flap_deg"])
                tilts += [(u, f), (u, -f), (v, f), (v, -f)]
            hits, worst = [], (0.0, "")
            # optional: "run_pose" {joint id: value} = the pose the joint spins in; "sync" {"joint", "ratio",
            # "phase_deg"} = a geared partner (tandem / intermeshing rotors) that turns with it: partner value =
            # ratio * value + phase_deg; every flap tilt is then swept twice: this disc alone, and both discs with
            # the same world tilt (tandem discs lean into each other; at asin(gap / hub distance) they are coplanar)
            base, sy = dict(j.get("run_pose") or {}), j.get("sync")
            if sy:
                tilts = tilts + [(t_[0], t_[1], True) for t_ in tilts[1:]]
            for ti, tl in enumerate(tilts):
                for k in range(int(round(360 / step))):
                    if base or sy:
                        pose, tilt = {**base, jid: k * step}, ({jid: tl} if tl else None)
                        if sy:
                            pose[sy["joint"]] = float(sy.get("ratio", 1.0)) * k * step + float(sy.get("phase_deg", 0.0))
                            tilt = {jid: tl[:2], **({sy["joint"]: tl[:2]} if len(tl) > 2 else {})} if tl else None
                        d, w = rig.collide(ji, pose, tilt, key=None if sy else "rest")
                    else:
                        d, w = rig.collide(ji, {jid: k * step}, {jid: tl} if tl else None, key="rest")
                    if d > TOL["collide_m"]:
                        hits.append({"at": k * step, "tilt": ti, "parts": w, "depth_mm": round(d * 1000, 2)})
                    if d > worst[0]:
                        worst = (d, w)
            record(name, not hits, type=t, range="0..360", step_deg=step, tilts=len(tilts), colliding_steps=len(hits),
                   first_hit=hits[0] if hits else None, worst_depth_mm=round(worst[0] * 1000, 2), worst=worst[1],
                   **({"sync": sy} if sy else {}), **({"run_pose": base} if base else {}))
            measured[jid] = {"clear": None if hits else "0..360"}
            continue
        if lim is None:
            record(name, False, type=t, why="limits missing")
            continue
        lo, hi = float(lim[0]), float(lim[1])
        prismatic = t in PRISMATIC
        step = float(j.get("step", 0.005 if prismatic else 1.0))
        pad = j.get("probe") or ([lo - 0.05, hi + 0.10] if prismatic else [lo - 10, hi + 10])
        if t in W_ROTARY | W_PRISMATIC:     # a weapon part works inside its limits: probe one step past them
            step = float(j.get("step", 0.002 if prismatic else 1.0))
            pad = j.get("probe") or [lo - step, hi + step]
        cases = [("", {})]
        yaw = _ancestor(rig, ji, "turret_yaw")
        sus = _ancestor(rig, ji, "suspension")
        if sus is None and t == "wheel_steer":     # bike fork: the suspension is a descendant of the steer joint
            sus = next((k for i, k in enumerate(rig.joints) if i in rig.sub[ji] and k["type"] == "suspension"), None)
        if t == "weapon_pitch" and yaw is not None:
            n = int(j.get("yaw_samples", 12))
            if yaw.get("limits") and not yaw.get("continuous"):
                a, b = yaw["limits"]
                cases = [(f"yaw {a + (b - a) * k / (n - 1):.0f}", {yaw["id"]: a + (b - a) * k / (n - 1)}) for k in range(n)]
            else:
                cases = [(f"yaw {360 * k / n:.0f}", {yaw["id"]: 360.0 * k / n}) for k in range(n)]
        elif t == "wheel_steer" and sus is not None and sus.get("limits"):
            cases = [(f"susp {v:+.3f}", {sus["id"]: v}) for v in (sus["limits"][0], 0.0, sus["limits"][1])]
        per, clear = {}, [pad[0], pad[1]]
        first = None
        for ci, (label, base) in enumerate(cases):
            r = _scan(lambda v: rig.collide(ji, {**base, jid: v}, key=("case", ci)), pad[0], pad[1], step)
            per[label or "rest"] = r
            clear = [max(clear[0], r["clear"][0]), min(clear[1], r["clear"][1])]
            for k in ("rest_collision", "first_hit_lo", "first_hit_hi"):
                if k in r and (lo - 1e-9 > r["clear"][0] or hi + 1e-9 < r["clear"][1] or k == "rest_collision") and first is None:
                    first = {"case": label or "rest", k: r[k]}
        ok = clear[0] <= lo + 1e-9 and clear[1] >= hi - 1e-9 and not any("rest_collision" in r for r in per.values())
        unit_ = "m" if prismatic else "deg"
        info = {"type": t, "limits": [lo, hi], "clear": [round(clear[0], 4), round(clear[1], 4)], "unit": unit_,
                "probe": pad, "step": step, "sec": round(time.time() - t0, 1)}
        if len(cases) > 1:
            info["per_case_clear"] = {k: r["clear"] for k, r in per.items()}
        hit = {}
        for label, r in per.items():
            for k in ("first_hit_lo", "first_hit_hi", "rest_collision"):
                if k in r and (k not in hit or (k == "first_hit_lo" and r[k]["at"] > hit[k]["at"])
                               or (k == "first_hit_hi" and r[k]["at"] < hit[k]["at"])):
                    hit[k] = {**r[k], "case": label} if isinstance(r[k], dict) else r[k]
        info.update(hit)
        if t == "magazine":
            # out of the well at full travel: with the declared seat contacts switched OFF the magazine no longer
            # touches anything (a magazine still inside its well at the limit has not detached)
            far = lo if abs(lo) > abs(hi) else hi
            keep, rig.contacts = rig.contacts, {}
            dd, ww = rig.collide(ji, {jid: far})
            rig.contacts = keep
            info["detached_at_limit"] = bool(dd <= TOL["collide_m"])
            if dd > TOL["collide_m"]:
                info["still_in_well"] = {"at": far, "parts": ww, "depth_mm": round(dd * 1000, 2)}
            ok = ok and info["detached_at_limit"]
        record(name, ok, **info)
        measured[jid] = {"clear": info["clear"], "unit": unit_}
    return measured


# ------------------------------------------------------------------------------------------------ b2. sockets (WF v10)
def _parts_named(rig, names):
    """Parts by object name, source object name or role."""
    return [p for p in rig.parts if p.name in names or p.source in names or p.role in names]


def bore_line(rig):
    """The bore: rig.json `bore` {"parts": [...]} (default: parts named / with role "barrel") -> (point, unit dir
    toward the muzzle, muzzle z). A barrel is a body of revolution about z: the line through its bbox centre."""
    cfg = RIG.get("bore") or {}
    ps = _parts_named(rig, cfg.get("parts") or ["barrel"])
    if not ps:
        return None
    V = np.vstack([p.V for p in ps])
    if cfg.get("point") and cfg.get("dir"):
        return np.array(cfg["point"], dtype=np.float64), unit(cfg["dir"]), float(V[:, 2].max())
    c = (V.min(axis=0) + V.max(axis=0)) / 2
    return np.array([c[0], c[1], 0.0]), np.array([0.0, 0.0, 1.0]), float(V[:, 2].max())


def test_sockets(rig):
    """rig.json `sockets`: [{id, pos, axis, parent?, parts?}] — named attachment points, each tested as stated
    (rig.md "Sockets"): muzzle on the bore line at the muzzle face; sight_rear -> sight_front a line parallel to the
    bore that nothing but the sights' own parts blocks; every other socket within socket_m of the surface it names."""
    if not SOCKETS:
        return
    ids = [s_["id"] for s_ in SOCKETS]
    if len(set(ids)) != len(ids):
        raise SystemExit("rig_pass.py: duplicate socket ids in rig.json")
    bore = bore_line(rig)
    by = {s_["id"]: s_ for s_ in SOCKETS}
    for s_ in SOCKETS:
        sid, pos = s_["id"], np.array(s_["pos"], dtype=np.float64)
        ax = unit(s_.get("axis", [0, 0, 1]))
        name = f"socket:{sid}"
        if s_.get("parent") is not None and s_["parent"] not in rig.jid:
            record(name, False, why=f"unknown parent joint {s_['parent']}")
            continue
        if sid == "muzzle":
            if bore is None:
                record(name, False, why="no bore (rig.json bore.parts, or a part named / with role 'barrel')")
                continue
            bp, bd, mz = bore
            off = float(np.linalg.norm(np.cross(pos - bp, bd)))
            skew = math.degrees(math.acos(min(1.0, abs(float(ax @ bd)))))
            ahead = float(pos[2] - mz)
            front = max(float(p.hi[2]) for p in rig.parts)
            muzzle_parts = _parts_named(rig, s_.get("parts") or []) if s_.get("parts") else rig.parts
            unknown = [key for key in (s_.get("parts") or []) if not _parts_named(rig, [key])]
            if not muzzle_parts or unknown:
                record(name, False, why="muzzle parts match no geometry" if not muzzle_parts else f"unknown muzzle parts {unknown}")
                continue
            mouth = max(float(p.hi[2]) for p in muzzle_parts)
            record(name, off <= TOL["bore_socket_m"] and skew <= 2.0 and float(ax @ bd) > 0 and pos[2] >= mouth - 0.005 and pos[2] <= mouth + 0.03,
                   off_bore_mm=round(off * 1000, 2), tol_mm=TOL["bore_socket_m"] * 1000, axis_vs_bore_deg=round(skew, 2),
                   ahead_of_barrel_mm=round(ahead * 1000, 2), ahead_of_everything_mm=round(float(pos[2] - front) * 1000, 2),
                   front_reference="specified muzzle parts" if s_.get("parts") else "all parts",
                   muzzle_parts=sorted({p.name for p in muzzle_parts}) if s_.get("parts") else "all parts",
                   ahead_of_muzzle_parts_mm=round(float(pos[2] - mouth) * 1000, 2))
            continue
        ps = _parts_named(rig, s_.get("parts") or []) or rig.parts
        V = np.vstack([p.V for p in ps])
        T = np.vstack([p.T + o for p, o in zip(ps, np.cumsum([0] + [len(p.V) for p in ps[:-1]]))])
        near = BVHTree.FromPolygons(V.tolist(), T.tolist(), epsilon=0.0).find_nearest(Vector(pos))
        dist = float(near[3]) if near and near[3] is not None else 9.0
        # a hand / opening socket (grip_*, magazine_well) sits at the CENTRE of the handle / mouth: half its width away
        stol = float(s_.get("tol_m", 0.035 if sid.startswith("grip") or sid == "magazine_well" else TOL["socket_m"]))
        info = {"surface_dist_mm": round(dist * 1000, 2), "tol_mm": stol * 1000,
                "of": sorted({p.name for p in ps}) if s_.get("parts") else "any part"}
        ok = dist <= stol
        if sid == "magazine_well":
            mj = next((j for j in rig.joints if j["type"] == "magazine"), None)
            if mj is not None:
                info["axis_vs_magazine_deg"] = round(math.degrees(math.acos(min(1.0, abs(float(ax @ mj["_axis"]))))), 2)
                ok = ok and info["axis_vs_magazine_deg"] <= 5.0
        record(name, ok, **info)
    if "sight_rear" in by and "sight_front" in by:
        a, b = np.array(by["sight_rear"]["pos"], dtype=np.float64), np.array(by["sight_front"]["pos"], dtype=np.float64)
        d = b - a
        ln = float(np.linalg.norm(d))
        own = set((by["sight_rear"].get("parts") or []) + (by["sight_front"].get("parts") or []))
        ps = [p for p in rig.parts if not (p.name in own or p.source in own or p.role in own)]
        V = np.vstack([p.V for p in ps])
        T = np.vstack([p.T + o for p, o in zip(ps, np.cumsum([0] + [len(p.V) for p in ps[:-1]]))])
        owner = np.concatenate([np.full(len(p.T), i) for i, p in enumerate(ps)])
        hit = BVHTree.FromPolygons(V.tolist(), T.tolist(), epsilon=0.0).ray_cast(Vector(a), Vector(d / max(ln, 1e-9)), ln)
        blocked = ps[int(owner[hit[2]])].name if hit and hit[0] is not None else None
        info = {"length_m": round(ln, 4), "blocked_by": blocked, "x_off_mm": round(max(abs(a[0]), abs(b[0])) * 1000, 2)}
        ok = blocked is None and ln > 0.02
        if bore is not None:
            bp, bd, _ = bore
            info["vs_bore_deg"] = round(math.degrees(math.acos(min(1.0, abs(float(d @ bd)) / max(ln, 1e-9)))), 2)
            info["height_over_bore_mm"] = round(float(((a + b) / 2 - bp)[1]) * 1000, 1)
            ok = ok and info["vs_bore_deg"] <= 3.0 and info["height_over_bore_mm"] > 0
        record("socket:sight_line", ok, **info)


def _expect_value(j, at):
    """expect.at -> the joint value: "hi" / "max" / "lo" / "min" (its limits) or a number (deg / m)."""
    if isinstance(at, (int, float)):
        return float(at)
    lim = j.get("limits") or (list(j["_vals"]) if j["type"] in SCALE and j.get("_vals") else None)
    if not lim:
        raise SystemExit(f"rig_pass.py: joint {j['id']}: expect.at '{at}' needs limits")
    k = {"hi": 1, "max": 1, "lo": 0, "min": 0}.get(str(at))
    if k is None:
        raise SystemExit(f"rig_pass.py: joint {j['id']}: expect.at must be hi / lo / max / min or a number, got {at!r}")
    return float(max(lim) if k else min(lim))


def _expect_point(rig, mats, ref, jid):
    """expect.point -> (posed author point, the parts it belongs to, label). Forms: "socket:<id>" or {"socket": id}
    (the socket's rest pos carried by its parent joint); "<part>" or {"part": p} (bbox centre of the posed part);
    {"part": p, "vertex": i} (that vertex of the part's mesh); {"part": p, "extreme": [dx, dy, dz]} (the part's REST
    vertex furthest along the direction, e.g. a wing tip, then posed)."""
    if isinstance(ref, str):
        ref = {"socket": ref[len("socket:"):]} if ref.startswith("socket:") else {"part": ref}
    if "socket" in ref:
        s_ = next((s for s in SOCKETS if s["id"] == ref["socket"]), None)
        if s_ is None:
            raise SystemExit(f"rig_pass.py: joint {jid}: expect.point names unknown socket '{ref['socket']}'")
        pos = np.array(s_["pos"], dtype=np.float64)
        par = s_.get("parent")
        if par is not None:
            M = mats[rig.jid[par]]
            pos = M[:3, :3] @ pos + M[:3, 3]
        return pos, [], f"socket {ref['socket']}"
    ps = _parts_named(rig, [ref["part"]])
    if not ps:
        raise SystemExit(f"rig_pass.py: joint {jid}: expect.point names no part '{ref['part']}' (have {sorted(rig.pid)})")
    idx = [rig.pid[p.name] for p in ps]
    rest = np.vstack([p.V for p in ps])
    W = np.vstack([rig.world(i, mats) for i in idx])
    if "vertex" in ref:
        k = int(ref["vertex"])
        if not 0 <= k < len(W):
            raise SystemExit(f"rig_pass.py: joint {jid}: expect.point vertex {k} outside 0..{len(W) - 1}")
        return W[k], ps, f"{ref['part']} vertex {k}"
    if "extreme" in ref:
        k = int(np.argmax(rest @ unit(ref["extreme"])))
        return W[k], ps, f"{ref['part']} rest-extreme {list(ref['extreme'])} (vertex {k})"
    return (W.min(axis=0) + W.max(axis=0)) / 2, ps, f"{ref['part']} bbox centre"


def test_pose_expect(rig):
    """rig.json joint `expect` (2026-10-11, rig.md "Pose expectations"): the END POSE a limited joint must reach, stated
    by the function spec BEFORE the hinge is solved (glide-wing lesson: a drum-axis hinge swept clear yet put the wings
    at hip height). At expect.at (default "hi") with every other joint at rest (or expect.pose {id: value}), the named
    point must lie within tol_m of `near`; optional `normal`: the posed part's thinnest principal axis (PCA of its
    vertices = a panel's normal, sign-free) within tol_deg of it. One test `pose:<joint>` per expect (a list ->
    `pose:<joint>.<k>` or its own `id`)."""
    for j in rig.joints:
        exp = j.get("expect")
        if not exp:
            continue
        exps = exp if isinstance(exp, list) else [exp]
        for k, e in enumerate(exps):
            jid = j["id"]
            name = "pose:" + (e.get("id") or (jid if len(exps) == 1 else f"{jid}.{k + 1}"))
            for need in ("point", "near"):
                if need not in e:
                    raise SystemExit(f"rig_pass.py: joint {j['id']}: expect needs '{need}' (rig.md 'Pose expectations')")
            val = _expect_value(j, e.get("at", "hi"))
            pose = {**{kk: float(vv) for kk, vv in (e.get("pose") or {}).items()}, j["id"]: val}
            for kk in pose:
                if kk not in rig.jid:
                    raise SystemExit(f"rig_pass.py: joint {j['id']}: expect.pose names unknown joint '{kk}'")
            mats = rig.mats(pose)
            pt, ps, label = _expect_point(rig, mats, e["point"], j["id"])
            near = np.array(e["near"], dtype=np.float64)
            tol = float(e.get("tol_m", 0.05))
            dist = float(np.linalg.norm(pt - near))
            ok = dist <= tol
            info = {"type": "expect", "joint": j["id"], "at": val, "point": label, "pos": [round(float(v), 4) for v in pt],
                    "near": [float(v) for v in near], "dist_m": round(dist, 4), "tol_m": tol}
            if e.get("normal") is not None:
                nps = _parts_named(rig, [e["normal_of"]]) if e.get("normal_of") else ps
                if not nps:
                    raise SystemExit(f"rig_pass.py: joint {j['id']}: expect.normal needs normal_of (a part) "
                                     f"when the point is a socket, or names no part '{e.get('normal_of')}'")
                W = np.vstack([rig.world(rig.pid[p.name], mats) for p in nps])
                w, vec = np.linalg.eigh(np.cov((W - W.mean(axis=0)).T))
                n = vec[:, 0]
                want = unit(e["normal"])
                ang = math.degrees(math.acos(min(1.0, abs(float(n @ want)))))
                tdeg = float(e.get("tol_deg", 15.0))
                n = n if float(n @ want) >= 0 else -n
                info.update(normal=[round(float(v), 4) for v in n], normal_want=[float(v) for v in want],
                            normal_of=sorted({p.name for p in nps}), normal_off_deg=round(ang, 2), tol_deg=tdeg,
                            normal_flatness=round(float(w[0] / max(w[1], 1e-18)), 4))
                ok = ok and ang <= tdeg
            if e.get("_why"):
                info["why"] = e["_why"]
            record(name, ok, **info)


def socket_empties(rig, emp, root):
    """Sockets as empties `socket_<id>` under their parent joint (or the root), at their rest position; the axis
    rides as an extra (identity rotation, like the joint nodes)."""
    out = {}
    for s_ in SOCKETS:
        if s_.get("parent") is not None and s_["parent"] not in emp:
            continue
        e = bpy.data.objects.new(f"socket_{s_['id']}", None)
        e.empty_display_size = 0.02
        bpy.context.scene.collection.objects.link(e)
        par = s_.get("parent")
        e.parent = emp[par] if par is not None else root
        pp = rig.joints[rig.jid[par]]["_pivot"] if par is not None else np.zeros(3)
        e.location = A(*(np.array(s_["pos"], dtype=np.float64) - pp))
        e["socket"] = s_["id"]
        e["socket_axis"] = [float(v) for v in unit(s_.get("axis", [0, 0, 1]))]
        out[s_["id"]] = e
    bpy.context.view_layer.update()
    return out


# ------------------------------------------------------------------------------------------------ c. ground / mass
def density_of(part, table):
    for key in (part.name, part.source, part.role):
        if key in table:
            d = table[key]
            return float(DENSITY[d]) if isinstance(d, str) else float(d)
    d = table.get("default", "weapon_alloy" if HANDHELD else "detail")
    return float(DENSITY[d]) if isinstance(d, str) else float(d)


def shell_of(part, shell):
    """mass.shell (optional, additive): the fraction of a part's drawn closed volume that is material in reality.
    A number in (0, 1], {"wall_m": t} (a closed shell of wall t over the part's own mesh: min(1, area x t / volume),
    any shape), or {"bore_d_m": d} (a tube along the bbox's longest axis, outer diameter = mean of the other two
    extents). Matched by name / source / role."""
    for key in (part.name, part.source, part.role):
        if key in shell:
            v = shell[key]
            s = part.hi - part.lo
            if isinstance(v, dict) and "wall_m" in v:
                a, b, c = part.V[part.T[:, 0]], part.V[part.T[:, 1]], part.V[part.T[:, 2]]
                area = float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()) / 2.0
                return float(min(1.0, area * float(v["wall_m"]) / max(part.volume, 1e-12)))
            if isinstance(v, dict) and "bore_d_m" in v:
                od = float(np.sort(s)[:2].mean())
                return float(max(0.0, 1.0 - (float(v["bore_d_m"]) / max(od, 1e-9)) ** 2))
            f = float(v)
            if not 0.0 < f <= 1.0:
                raise SystemExit(f"rig_pass.py: mass.shell['{key}'] = {v}: a fill fraction must be in (0, 1]")
            return f
    return 1.0


def mass_props(rig):
    mcfg = PHYS.get("mass") or {}
    table = mcfg.get("density") or {}
    for v in table.values():
        if isinstance(v, str) and v not in DENSITY:
            raise SystemExit(f"rig_pass.py: unknown density class '{v}' (have {sorted(DENSITY)})")
    shell = {k: v for k, v in (mcfg.get("shell") or {}).items() if not k.startswith("_")}
    fills = [shell_of(p, shell) for p in rig.parts]
    ms = np.array([p.volume * density_of(p, table) * f for p, f in zip(rig.parts, fills)])
    M = float(ms.sum())
    cs = np.array([p.centroid for p in rig.parts])
    com = (cs * ms[:, None]).sum(axis=0) / max(M, 1e-9)
    if mcfg.get("mass_kg"):
        ms *= float(mcfg["mass_kg"]) / max(M, 1e-9)
        M = float(mcfg["mass_kg"])
    I = np.zeros(3)
    for p, m in zip(rig.parts, ms):
        s = p.hi - p.lo
        d = p.centroid - com
        I += m * np.array([(s[1] ** 2 + s[2] ** 2) / 12 + d[1] ** 2 + d[2] ** 2,
                           (s[0] ** 2 + s[2] ** 2) / 12 + d[0] ** 2 + d[2] ** 2,
                           (s[0] ** 2 + s[1] ** 2) / 12 + d[0] ** 2 + d[1] ** 2])
    by = {}
    for p, m in zip(rig.parts, ms):
        by[p.source] = by.get(p.source, 0.0) + float(m)
    rng = mcfg.get("range_kg")
    # honest range (rig.md "Mass: the honest rule"): a stated real-world reference {item, kg, source} sets the range; a
    # builder range_kg that differs is ignored, and a mass outside the reference is an owner item, never widened
    ref = mcfg.get("reference")
    hon, excl, Mx = {}, set(), 0.0
    if ref:
        if not (isinstance(ref, dict) and len(ref.get("kg") or []) == 2 and ref.get("item") and ref.get("source")):
            raise SystemExit("rig_pass.py: mass.reference needs {item, kg: [lo, hi], source}")
        if rng and [float(x) for x in rng] != [float(x) for x in ref["kg"]]:
            hon["range_kg_ignored"] = rng
        rng = [float(x) for x in ref["kg"]]
        hon.update(range_source="reference", reference=ref)
        excl = set(ref.get("exclude_parts") or [])      # parts the reference item does not include (e.g. ammo)
        if excl:
            Mx = float(sum(m for p, m in zip(rig.parts, ms) if {p.name, p.source, p.role} & excl))
            hon.update(reference_scope_kg=round(M - Mx, 3), excluded_kg=round(Mx, 3))
    elif rng and HANDHELD:
        hon["range_source"] = "builder (unreferenced)"
    Mref = M - Mx
    if shell:
        hon["shell_fill"] = {p.name: round(f, 3) for p, f in zip(rig.parts, fills) if f != 1.0}
        if mcfg.get("shell", {}).get("_why"):
            hon["shell_why"] = mcfg["shell"]["_why"]
    if ref and not rng[0] <= Mref <= rng[1]:
        hon["owner_item"] = (f"estimated mass {Mref:.4g} kg{' (reference scope)' if excl else ''} is outside the reference "
                             f"{rng[0]:g}-{rng[1]:g} kg "
                             f"({ref['item']}); owner: accept, set a game mass_kg, or change the model")
    # physics.mass.mass_game_kg (optional, 2026-10-11): the mass the GAME uses (a chunky prop is 2-4x a real one).
    # Reported next to the honest estimate, never tested and never used for COM / inertia; the test above stays the
    # honest one (estimate vs the reference). Which number gates a set is an open owner question (rig.md "Mass").
    if mcfg.get("mass_game_kg") is not None:
        g = float(mcfg["mass_game_kg"])
        hon.update(mass_game_kg=g, game_over_estimate=round(g / max(Mref, 1e-9), 3))
        if ref:
            hon["game_in_reference"] = rng[0] <= g <= rng[1]
    com_auth = PHYS.get("com")
    dev = float(np.linalg.norm(np.array(com_auth) - com)) if com_auth else 0.0
    if HANDHELD:     # a few kg: 3 decimals, litres, the COM along the weapon (z from the grip socket when there is one)
        grip = next((np.array(s_["pos"], dtype=np.float64) for s_ in SOCKETS if s_["id"] == "grip_r"), None)
        record("mass", (not rng or rng[0] <= Mref <= rng[1]) and dev <= 0.05, mass_kg=round(M, 3), range_kg=rng,
               com=[round(float(v), 4) for v in com], authored_com=com_auth, authored_com_dev_m=round(dev, 4),
               inertia_kgm2=[round(float(v), 5) for v in I],
               volume_l=round(float(sum(p.volume for p in rig.parts)) * 1000, 3),
               com_ahead_of_grip_m=None if grip is None else round(float(com[2] - grip[2]), 4),
               by_part_kg={k: round(v, 3) for k, v in sorted(by.items(), key=lambda kv: -kv[1])}, **hon)
        return M, (np.array(com_auth, dtype=np.float64) if com_auth else com), I
    record("mass", (not rng or rng[0] <= Mref <= rng[1]) and dev <= 0.15, mass_kg=round(M, 1), range_kg=rng,
           com=[round(float(v), 4) for v in com], authored_com=com_auth, authored_com_dev_m=round(dev, 4),
           inertia_kgm2=[round(float(v), 1) for v in I], volume_m3=round(float(sum(p.volume for p in rig.parts)), 3),
           by_part_kg={k: round(v, 1) for k, v in sorted(by.items(), key=lambda kv: -kv[1])}, **hon)
    return M, (np.array(com_auth, dtype=np.float64) if com_auth else com), I


def test_ground(rig):
    tol = TOL["ground_m"]
    rows, ok = {}, True
    for w in PHYS.get("wheels") or []:
        ji = rig.jid.get(w.get("joint_spin"))
        if ji is None:
            rows[w["id"]] = {"why": "joint_spin missing"}
            ok = False
            continue
        j = rig.joints[ji]
        V = rig.joint_verts(ji, own_only=False)
        bottom = float(V[:, 1].min()) - GROUND_Y
        u, v = perp_basis(j["_axis"])
        d = V - j["_pivot"]
        R = float(np.hypot(d @ u, d @ v).max())
        coff = float(np.linalg.norm(np.array(w["centre"]) - j["_pivot"]))
        roll = float(w["centre"][1]) - GROUND_Y
        good = abs(bottom) <= tol and coff <= TOL["pivot_m"] and abs(w["radius"] - roll) <= tol
        ok &= good
        rows[w["id"]] = {"bottom_mm": round(bottom * 1000, 2), "mesh_radius_m": round(R, 4), "radius_m": w["radius"],
                         "centre_height_m": round(roll, 4), "centre_vs_pivot_mm": round(coff * 1000, 3),
                         "width_m": round(float(np.ptp(d @ j["_axis"])), 4), "pass": bool(good)}
    for tr in PHYS.get("tracks") or []:
        ps = [rig.parts[rig.pid[n]] for n in tr.get("parts", []) if n in rig.pid]
        bottom = min(float(p.lo[1]) for p in ps) - GROUND_Y if ps else 9.0
        cy = max(abs(c["centre"][1] - c.get("radius", 0.0) - GROUND_Y) for c in tr["contacts"])
        good = abs(bottom) <= tol and cy <= tol
        ok &= good
        rows[tr["id"]] = {"bottom_mm": round(bottom * 1000, 2), "contact_err_mm": round(cy * 1000, 2), "pass": bool(good)}
    for sk in PHYS.get("skids") or []:
        ps = [rig.parts[rig.pid[n]] for n in sk.get("parts", []) if n in rig.pid]
        bottom = min(float(p.lo[1]) for p in ps) - GROUND_Y if ps else 9.0
        good = abs(bottom) <= tol
        ok &= good
        rows[sk["id"]] = {"bottom_mm": round(bottom * 1000, 2), "pass": bool(good)}
    lowest = min(rig.parts, key=lambda p: p.lo[1])
    under = float(lowest.lo[1]) - GROUND_Y
    record("ground", ok and under >= -tol and bool(rows), tol_mm=tol * 1000, lowest_part=lowest.name,
           lowest_mm=round(under * 1000, 2), contacts=rows)


def colliders(rig):
    out, chassis = [], None
    for c in PHYS.get("colliders") or []:
        names = [n for n in rig.pid if n in c.get("parts", []) or rig.parts[rig.pid[n]].source in c.get("parts", [])]
        if not names:
            raise SystemExit(f"rig_pass.py: collider {c['id']}: no parts match {c.get('parts')}")
        V = np.vstack([rig.parts[rig.pid[n]].V for n in names])
        lo, hi = V.min(axis=0), V.max(axis=0)
        r = {"id": c["id"], "type": c.get("type", "box"), "joint": c.get("joint"), "parts": c.get("parts"),
             "centre": [round(float(v), 4) for v in (lo + hi) / 2], "size": [round(float(v), 4) for v in hi - lo]}
        if c.get("centre") and c.get("size"):
            r["centre"], r["size"] = c["centre"], c["size"]
        bm = bmesh.new()
        vs = [bm.verts.new(A(*p)) for p in np.unique(np.round(V, 4), axis=0)]
        res = bmesh.ops.convex_hull(bm, input=vs)
        hv = {v for g in res["geom"] if isinstance(g, bmesh.types.BMFace) for v in g.verts}
        hull = np.array([author(v.co) for v in hv])
        bm.free()
        if r["type"] == "convex":
            r["verts"] = [[round(float(a), 4) for a in p] for p in hull]
        if c.get("chassis") or (chassis is None and c.get("joint") is None):
            if r["type"] == "box":
                cx, cy, cz = r["centre"]
                sx, sy, sz = r["size"]
                pts = [[cx + a * sx / 2, cy - sy / 2, cz + b * sz / 2] for a in (-1, 0, 1) for b in (-1, -0.5, 0, 0.5, 1)]
            else:
                low = hull[hull[:, 1] <= lo[1] + 0.5 * (hi[1] - lo[1])]
                pts = low[np.argsort(low[:, 1])][:40].tolist()
            chassis = {"id": c["id"], "points": pts, "bottom_m": round(float(lo[1]) - GROUND_Y, 4)}
        out.append(r)
    return out, chassis


def sim_input(rig, M, com, I, measured, chassis):
    sus = PHYS.get("suspension") or {}
    con = []
    for w in PHYS.get("wheels") or []:
        sj = rig.joints[rig.jid[w["joint_suspension"]]] if w.get("joint_suspension") in rig.jid else None
        lim = sj["limits"] if sj is not None and sj.get("limits") else [-sus.get("travel_droop", 0.1), sus.get("travel_bump", 0.1)]
        clear = (measured.get(sj["id"], {}).get("clear") or [None, lim[1]])[1] if sj is not None else lim[1]
        if sj is not None:     # raked prismatic axis / suspension_arm (deg) -> vertical wheel travel (m)
            lim = [susp_metres(rig, sj, lim[0]), susp_metres(rig, sj, lim[1])]
            clear = susp_metres(rig, sj, clear)
        con.append({"id": w["id"], "pos": [float(v) for v in w["centre"]], "radius": float(w["centre"][1]) - GROUND_Y,
                    "width": w.get("width", 0.0), "bump": float(lim[1]), "droop": float(-lim[0]),
                    "clear_bump": float(clear), "driven": bool(w.get("driven", True)), "braked": True,
                    "joint_suspension": w.get("joint_suspension")})
    for tr in PHYS.get("tracks") or []:
        for k, c in enumerate(tr["contacts"]):
            con.append({"id": f"{tr['id']}_{k + 1}", "pos": [float(v) for v in c["centre"]],
                        "radius": float(c.get("radius", 0.0)), "width": tr.get("width", 0.0),
                        "bump": float(c.get("bump", sus.get("travel_bump", 0.1))),
                        "droop": float(c.get("droop", sus.get("travel_droop", 0.1))),
                        "clear_bump": float(c.get("clear_bump", c.get("bump", sus.get("travel_bump", 0.1)))),
                        "driven": True, "braked": True})
    for sk in PHYS.get("skids") or []:
        for k, c in enumerate(sk["contacts"]):
            con.append({"id": f"{sk['id']}_{k + 1}", "pos": [float(v) for v in c], "radius": 0.0, "width": 0.0,
                        "bump": float(sk.get("flex", 0.05)), "droop": float(sk.get("flex", 0.05)),
                        "clear_bump": float(sk.get("flex", 0.05)) * 2, "driven": False, "braked": True})
    inp = {"mass": M, "com": [float(v) for v in com], "inertia": [float(v) for v in I], "contacts": con,
            "chassis_points": [list(map(float, q)) for q in chassis["points"]] if chassis else [],
            "frequency_hz": sus.get("frequency_hz", 1.6), "damping_ratio": sus.get("damping_ratio", 0.6),
            "bump_stop_ratio": sus.get("bump_stop_ratio", 30.0), "mu": PHYS.get("mu", 0.9),
            "drive": bool(PHYS.get("drive", bool(PHYS.get("wheels") or PHYS.get("tracks")))),
            "lock_roll": bool(PHYS.get("lock_roll", False)), "sim": PHYS.get("sim") or {},
            "limits": PHYS.get("limits") or {}}
    if GROUND_Y:     # the sim's ground is y = 0: hand it heights above physics.ground_y
        inp["com"][1] -= GROUND_Y
        for q in [c["pos"] for c in con] + inp["chassis_points"]:
            q[1] -= GROUND_Y
    return inp


def test_static(inp):
    lim = {"tip_side_min_deg": 30.0, "tip_pitch_min_deg": 30.0, **(PHYS.get("limits") or {})}
    if len(inp["contacts"]) < 2:
        record("stability", False, why="fewer than 2 ground contacts in physics")
        return
    st = rig_sim.stability(inp)
    side = min(st["tip_left_deg"], st["tip_right_deg"])
    pitch = min(st["tip_front_deg"], st["tip_rear_deg"])
    ok = st["com_inside"] and pitch >= lim["tip_pitch_min_deg"] and (inp["lock_roll"] or side >= lim["tip_side_min_deg"])
    record("stability", ok, **st, min_side_deg=lim["tip_side_min_deg"], min_pitch_deg=lim["tip_pitch_min_deg"],
           side_skipped=inp["lock_roll"])


# ------------------------------------------------------------------------------------------------ hierarchy + export
def build_hierarchy(rig, root):
    # Parts may use real local origins. Freeze every world matrix before reparenting any part.
    bpy.context.view_layer.update()
    original_world = {name: ob.matrix_world.copy() for name, ob in rig.objs.items()}
    moving_names = {name for joint in rig.joints for name in joint["_names"]}
    # Unclaimed geometry is static even when the builder parented it to a moving mesh.
    for name, ob in rig.objs.items():
        if name not in moving_names:
            if ob.data.users > 1:
                ob.data = ob.data.copy()
            # Bake the full matrix: a reparented TRS cannot retain inherited shear.
            ob.data.transform(root.matrix_world.inverted() @ original_world[name])
            ob.parent = root
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = Matrix.Identity(4)
    emp = {}
    for j in rig.joints:
        e = bpy.data.objects.new(j["id"], None)
        e.empty_display_size = 0.2
        bpy.context.scene.collection.objects.link(e)
        par = emp[rig.joints[j["_parent"]]["id"]] if j["_parent"] >= 0 else root
        e.parent = par
        pp = rig.joints[j["_parent"]]["_pivot"] if j["_parent"] >= 0 else np.zeros(3)
        e.location = A(*(j["_pivot"] - pp))
        e.rotation_mode = "QUATERNION"
        e["joint_type"] = j["type"]
        e["joint_axis"] = [float(v) for v in j["_axis"]]
        if j.get("limits"):
            e["joint_limits"] = [float(v) for v in j["limits"]]
        for k in ("speed_param", "continuous"):
            if k in j:
                e[f"joint_{k}"] = j[k]
        j["_rest"] = e.location.copy()
        emp[j["id"]] = e
        shift = Matrix.Translation(-A(*j["_pivot"]))
        for n in j["_names"]:
            ob = rig.objs[n]
            if ob.data.users > 1:
                ob.data = ob.data.copy()
            ob.data.transform(shift @ original_world[n])
            ob.parent = e
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    return emp


def scale_vec(rig, j, v):
    """Blender empty scale for a scale joint: the axis' Blender component scaled (author -> Blender = hs.A)."""
    b = A(*j["_axis"])
    sc = [1.0, 1.0, 1.0]
    sc[int(np.argmax(np.abs(np.array(b[:]))))] = rig.scale_of(j, v)
    return sc


def set_pose(rig, emp, pose=None):
    pose = rig.resolve(pose)
    for j in rig.joints:
        e, v = emp[j["id"]], pose.get(j["id"], 0.0)
        # the glTF exporter (NLA sampling) can leave a child joint's location rotated by its parent's last sampled
        # pose (main_battle_tank: gun_pitch came back 120 deg round the turret axis) -> always restore the rest offset
        e.location = j["_rest"]
        if j["type"] in SCALE:
            e.scale = scale_vec(rig, j, v)
        elif j["type"] in ROTARY:
            e.rotation_quaternion = Quaternion(A(*j["_axis"]), math.radians(v))
        elif j["type"] in PRISMATIC:
            e.location = j["_rest"] + A(*j["_axis"]) * v


def pose_check(rig, emp):
    """The numpy pose (tests) and the Blender hierarchy (renders, glb) must agree."""
    pose = {}
    for j in rig.joints:
        if j["type"] in ROTARY:
            pose[j["id"]] = 23.0 if not j.get("limits") else j["limits"][1] * 0.7
        elif j["type"] in PRISMATIC:
            pose[j["id"]] = j["limits"][1] * 0.7 if j.get("limits") else 0.03
        elif j["type"] in SCALE and not j.get("_follow"):     # a follower is resolved from its master's pose value
            pose[j["id"]] = 0.7 * (j["_vals"][0] if abs(j["_vals"][0]) > abs(j["_vals"][1]) else j["_vals"][1])
    set_pose(rig, emp, pose)
    bpy.context.view_layer.update()
    mats = rig.mats(pose)
    worst = 0.0
    for pi, p in enumerate(rig.parts):
        W = rig.world(pi, mats)
        mw = p.ob.matrix_world
        B = np.array([author(mw @ v.co) for v in p.ob.data.vertices])
        if len(B) == len(W):
            worst = max(worst, float(np.abs(B - W).max()))
        else:
            worst = 9.0
    set_pose(rig, emp)
    bpy.context.view_layer.update()
    rest = max(float(np.abs(np.array([author(p.ob.matrix_world @ v.co) for v in p.ob.data.vertices]) - p.V).max())
               for p in rig.parts)
    record("regroup", worst < 1e-4 and rest < 1e-5, posed_max_err_mm=round(worst * 1000, 4),
           rest_max_err_mm=round(rest * 1000, 5), joints=len(rig.joints), parts=len(rig.parts))


def clip_keys(j):
    """[(frame, value)] one key per frame, starting and ending at rest."""
    t = j["type"]
    lim = j.get("limits")
    if t in SCALE and j.get("_follow"):
        return []      # keyed in its master's clip (clip_curves)
    if t in CONTINUOUS or (t == "turret_yaw" and (lim is None or j.get("continuous"))):
        n = {"wheel_spin": 48, "rotor_spin": 24}.get(t, 96)
        if t == "cylinder":      # one index step: 360 / chambers over 12 frames (the next chamber lands where this one was)
            return [(f, 360.0 / max(2, int(j.get("chambers", 6))) * f / 12) for f in range(13)]
        if t == "barrel_spin":
            n = 24
        return [(f, 360.0 * f / n) for f in range(n + 1)]
    if not lim or t in STATIC:
        return []
    if t in ("trigger", "slide", "magazine", "selector", "hinge"):
        # weapon clips: rest -> the far limit -> rest. Fire = trigger (pull, frames 0-4-8) + slide / bolt cycle
        # (back by frame 10, home by 16); Reload = magazine out (12) and in (24); Open / Selector = out and back
        far = lim[0] if abs(lim[0]) > abs(lim[1]) else lim[1]
        a, b, c, end = {"trigger": (0, 4, 8, 16), "slide": (4, 10, 16, 16), "magazine": (0, 12, 24, 24)}.get(t, (0, 12, 24, 24))
        out = []
        for f in range(end + 1):
            v = 0.0 if f <= a or f >= c else far * ((f - a) / (b - a) if f <= b else (c - f) / (c - b))
            out.append((f, v))
        return out
    lo, hi = lim
    seg = 16
    way = [0.0, hi, 0.0, lo, 0.0]
    out = []
    for s in range(4):
        for f in range(seg):
            out.append((s * seg + f, way[s] + (way[s + 1] - way[s]) * f / seg))
    out.append((4 * seg, 0.0))
    return out


def continuous_joint(j):
    return j["type"] in CONTINUOUS or (j["type"] == "turret_yaw" and (j.get("limits") is None or j.get("continuous")))


def continuous_pose(rig, jid, value):
    """Resolve one running pose; the caller chooses the leader's phase.

    Reciprocal sync constraints are checked modulo a turn. Equal scalar values about opposite
    axes remain opposite spins. A running attachment gets its own constant animation channel.
    """
    links = {j["id"]: [] for j in rig.joints}
    for j in rig.joints:
        sync = j.get("sync")
        if not sync:
            continue
        target = sync["joint"]
        if target not in rig.jid or not continuous_joint(j) or not continuous_joint(rig.joints[rig.jid[target]]):
            raise SystemExit(f"rig_pass.py: {j['id']}: sync requires known continuous joints ({target})")
        ratio, phase = float(sync.get("ratio", 1)), float(sync.get("phase_deg", 0))
        if not math.isfinite(ratio) or not math.isfinite(phase) or abs(ratio) < 1e-9:
            raise SystemExit(f"rig_pass.py: {j['id']}: invalid sync ratio/phase")
        links[j["id"]].append((target, ratio, phase))
        links[target].append((j["id"], 1 / ratio, -phase / ratio))
    coefficients, queue = {}, [(jid, 1.0, 0.0)]
    while queue:
        name, slope, offset = queue.pop(0)
        if name not in rig.jid or not math.isfinite(slope) or not math.isfinite(offset):
            raise SystemExit(f"rig_pass.py: invalid running joint/constraint {name}")
        j = rig.joints[rig.jid[name]]
        if name in coefficients:
            old_slope, old_offset = coefficients[name]
            error = offset - old_offset
            if continuous_joint(j):
                error = (error + 180) % 360 - 180
            # Validate the affine constraint over the whole motion, not only a sampled angle.
            if abs(slope - old_slope) > 1e-9 or abs(error) > 1e-6:
                raise SystemExit(f"rig_pass.py: inconsistent running pose constraints for {name}")
            continue
        if abs(slope) < 1e-9 and j.get("limits"):
            lo, hi = j["limits"]
            if offset < lo - 1e-6 or offset > hi + 1e-6:
                raise SystemExit(f"rig_pass.py: {name}: running pose {offset} outside limits {lo}..{hi}")
        coefficients[name] = (slope, offset)
        queue.extend((other, ratio * slope, ratio * offset + phase) for other, ratio, phase in links[name])
        queue.extend((other, 0.0, float(angle)) for other, angle in (j.get("run_pose") or {}).items())
    return {name: slope * float(value) + offset for name, (slope, offset) in coefficients.items()}


def clip_curves(rig):
    """One curve per (clip, joint); synchronized components resolve once per clip."""
    clips = {}
    for j in rig.joints:
        clip = j.get("clip") or CLIPS.get(j["type"]) or (f"Open_{j['id']}" if j["type"] in ("door", "hatch") else None)
        keys = clip_keys(j)
        if not clip or not keys:
            continue
        curves = clips.setdefault(clip, {})
        if j["id"] in curves:
            continue
        proposed = {}
        for f, v in keys:
            pose = continuous_pose(rig, j["id"], v) if continuous_joint(j) else {j["id"]: v}
            for mid in list(pose):      # scale joints following a joint of this clip ride in the same clip
                for fj in rig.followers.get(mid, []):
                    pose[fj["id"]] = fj["_follow"][1] * pose[mid]
            for name, value in pose.items():
                proposed.setdefault(name, []).append((f, value))
        for name, curve in proposed.items():
            if continuous_joint(rig.joints[rig.jid[name]]) and any(abs(b[1] - a[1]) >= 180 - 1e-6 for a, b in zip(curve, curve[1:])):
                raise SystemExit(f"rig_pass.py: {clip}/{name}: angular step >=180 degrees cannot be represented by sampled quaternion interpolation")
            if name in curves and curves[name] != curve:
                raise SystemExit(f"rig_pass.py: conflicting {clip} curves for {name}")
            curves[name] = curve
    return clips


def make_clips(rig, emp):
    names = set()
    entries = [(clip, name, keys) for clip, curves in clip_curves(rig).items() for name, keys in curves.items()]
    for clip, name, keys in entries:
        j = rig.joints[rig.jid[name]]
        e = emp[name]
        e.animation_data_create()
        prev = None
        for f, v in keys:
            if j["type"] in ROTARY:
                q = Quaternion(A(*j["_axis"]), math.radians(v))
                if prev is not None and q.dot(prev) < 0:
                    q.negate()
                prev = q.copy()
                e.rotation_quaternion = q
                e.keyframe_insert("rotation_quaternion", frame=f)
            elif j["type"] in SCALE:
                e.scale = scale_vec(rig, j, v)
                e.keyframe_insert("scale", frame=f)
            else:
                e.location = j["_rest"] + A(*j["_axis"]) * v
                e.keyframe_insert("location", frame=f)
        act = e.animation_data.action
        act.name = f"{clip}.{name}"
        slot = getattr(e.animation_data, "action_slot", None)
        tr = e.animation_data.nla_tracks.new()
        tr.name = clip
        strip = tr.strips.new(clip, 0, act)
        try:
            if slot is not None and getattr(strip, "action_slot", None) is None:
                strip.action_slot = slot
        except (AttributeError, TypeError) as ex:
            print("WARN nla slot:", ex)
        e.animation_data.action = None
        names.add(clip)
    # Default glTF transforms must be the parked rest pose, not active RotorSpin frame zero.
    # The NLA_TRACKS exporter temporarily enables NLA for each sampled clip itself.
    for e in emp.values():
        if e.animation_data:
            e.animation_data.use_nla = False
    bpy.context.scene.frame_set(0)
    set_pose(rig, emp)
    bpy.context.view_layer.update()
    return sorted(names)


def export_glb(path):
    props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    kw = {"filepath": path, "export_format": "GLB", "use_selection": False, "export_apply": True, "export_yup": True,
          "export_animations": True, "export_animation_mode": "NLA_TRACKS", "export_force_sampling": True,
          "export_extras": True, "export_frame_range": False, "export_optimize_animation_size": False,
          "export_anim_single_armature": False, "export_optimize_animation_keep_anim_object": True}
    bpy.ops.export_scene.gltf(**{k: v for k, v in kw.items() if k in props or k == "filepath"})


def read_glb(path):
    with open(path, "rb") as f:
        magic, _, _ = struct.unpack("<4sII", f.read(12))
        n, kind = struct.unpack("<I4s", f.read(8))
        if magic != b"glTF" or kind != b"JSON":
            raise SystemExit(f"rig_pass.py: {path} is not a glb")
        return json.loads(f.read(n).decode("utf-8"))


def test_export(rig, glb, tris_expected, clips):
    G = read_glb(glb)
    nodes = G.get("nodes", [])
    acc = G.get("accessors", [])
    tris = 0
    for m in G.get("meshes", []):
        for p in m["primitives"]:
            tris += (acc[p["indices"]]["count"] if "indices" in p else acc[p["attributes"]["POSITION"]]["count"]) // 3
    parent = {}
    for i, nd in enumerate(nodes):
        for c in nd.get("children", []):
            parent[c] = i
    byname = {nd.get("name"): i for i, nd in enumerate(nodes)}

    def world_t(i):
        t = np.zeros(3)
        while i is not None:
            nd = nodes[i]
            if "rotation" in nd and max(abs(a) for a in nd["rotation"][:3]) > 1e-6:
                return None
            t = t + np.array(nd.get("translation", [0, 0, 0]))
            i = parent.get(i)
        return t
    err, missing, bad_parent = 0.0, [], []
    for j in rig.joints:
        i = byname.get(j["id"])
        if i is None:
            missing.append(j["id"])
            continue
        w = world_t(i)
        err = max(err, 9.0 if w is None else float(np.abs(w - j["_pivot"]).max()))
        want = rig.joints[j["_parent"]]["id"] if j["_parent"] >= 0 else SUBJECT
        if (nodes[parent[i]].get("name") if i in parent else None) != want:
            bad_parent.append(j["id"])
    anims = sorted(a.get("name", "") for a in G.get("animations", []))
    sock, sock_ok = {}, True
    if SOCKETS:
        s_missing, s_err = [], 0.0
        for s_ in SOCKETS:
            i = byname.get(f"socket_{s_['id']}")
            if i is None:
                s_missing.append(s_["id"])
                continue
            w = world_t(i)
            s_err = max(s_err, 9.0 if w is None else float(np.abs(w - np.array(s_["pos"], dtype=np.float64)).max()))
        sock = {"sockets": len(SOCKETS), "socket_nodes_missing": s_missing, "socket_max_err_mm": round(s_err * 1000, 4)}
        sock_ok = not s_missing and s_err < 1e-4
    scl, scl_ok = {}, True
    sj = [j for j in rig.joints if j["type"] in SCALE]
    if sj:     # every scale joint: a glTF `scale` channel in the clip that carries it, sampled values = the rig's
        doc, binary = glb_motion.read_binary(glb)
        want = {name: (clip, curve) for clip, curves in clip_curves(rig).items() for name, curve in curves.items()}
        for j in sj:
            clip, curve = want.get(j["id"], (None, []))
            ax = int(np.argmax(np.abs(j["_axis"])))
            got = glb_motion.channel_values(doc, binary, j["id"], "scale").get(clip, [])
            s_want = [rig.scale_of(j, v) for _, v in curve]
            row = {"clip": clip, "samples": len(got)}
            good = False
            if got and s_want:
                g = [v[ax] for v in got]
                off = [max(abs(v[i] - 1.0) for i in range(3) if i != ax) for v in got]
                row.update(min=round(min(g), 5), max=round(max(g), 5), want_min=round(min(s_want), 5),
                           want_max=round(max(s_want), 5), off_axis_max=round(max(off), 6))
                good = abs(min(g) - min(s_want)) < 1e-4 and abs(max(g) - max(s_want)) < 1e-4 and max(off) < 1e-5
            scl[j["id"]] = row
            scl_ok &= good
        rest_s = [nodes[byname[j["id"]]].get("scale", [1, 1, 1]) for j in sj if j["id"] in byname]
        scl_ok &= all(abs(v - 1) < 1e-6 for s_ in rest_s for v in s_)
    record("export", tris == tris_expected and not missing and not bad_parent and err < 1e-4 and set(clips) <= set(anims) and sock_ok and scl_ok,
           **({"scale_tracks": scl} if sj else {}),
           glb=os.path.basename(glb), tris=tris, tris_look_stage=tris_expected, nodes=len(nodes),
           joint_nodes_missing=missing, joint_parent_wrong=bad_parent, pivot_max_err_mm=round(err * 1000, 4),
           clips=anims, clips_expected=clips, bytes=os.path.getsize(glb), **sock)


def test_look(rig):
    """The regrouped model at rest must score exactly as the look stage did (and still pass its gate vs gold)."""
    st_path = os.path.join(SDIR, "stats.json")
    look = rp._json(st_path) if os.path.exists(st_path) else None
    objs = [p.ob for p in rig.parts]
    topo = rp.topology_report(objs)
    clean = all(v == 0 for v in topo["totals"].values())
    info = {"tris": topo["tris"], "budget": rp.tri_budget(), "topology": topo["totals"]}
    ok = clean and topo["tris"] <= info["budget"]
    if look:
        info["tris_look_stage"] = look["tris"]
        ok &= look["tris"] == topo["tris"]
        snap = os.path.join(SDIR, f"pass{look.get('pass')}_build.py")
        if os.path.exists(snap):
            with open(snap, "rb") as a, open(rp.BUILD, "rb") as b:
                info["build_is_look_stage_final"] = a.read() == b.read()
            ok &= info["build_is_look_stage_final"]
    else:
        info["why"] = "no look-stage stats.json (run run_pass.py --final first)"
        ok = False
    if not NO_JUDGE:
        mesh = os.path.join(ODIR, "_rig_mesh.json")
        rp.dump_mesh(objs, mesh)
        # a look stage scored before the robust sigma fit (2026-10-10; its judge has no sigmaFit) is re-scored with
        # the judge's golden section alone, so a finished subject's rig keeps reproducing its stats.json exactly
        fit = "golden" if look and not (look.get("judge") or {}).get("sigmaFit") else None
        J = rp.judge_scores(mesh, os.path.join(ODIR, "_rig_judge.json"), sigma_fit=fit)
        info["sigma_fit"] = fit or "robust"
        os.remove(mesh)
        os.remove(os.path.join(ODIR, "_rig_judge.json"))
        info["sigma"] = J["sigma"]
        info["agree"] = {v: J["views"][v]["agree"] for v in J["views"]}
        info["iou"] = {v: J["views"][v]["iou"] for v in J["views"]}
        info["gold_agree"] = rp.CURRENT_AGREE
        info["delta_vs_gold"] = {v: round(info["agree"][v] - rp.CURRENT_AGREE[v], 4) for v in info["agree"] if v in rp.CURRENT_AGREE}
        # scripts/hs/method.md (owner 2026-10-04): no ortho view more than .04 below gold; the concept is not gated
        gate = all(d >= -0.04 for v, d in info["delta_vs_gold"].items() if v != "concept")
        hero = (look or {}).get("hero") or {}
        if getattr(rp, "DIRECT", False) and os.path.exists(rp.PARTS_JSON) and hero.get("verdict"):
            # hero-led rule (2026-10-11, research/PLAN-ITEMS30.md): a direct subject with subjects/<s>/parts.json is
            # built against the HERO; its polish may drop an ortho view below an earlier pass on purpose (hero-led
            # views, POLISH.md). The rig then reproduces the FINAL pass (identity below) and that pass's HERO
            # verdict must be PASS; the best-earlier ortho rule is reported, not gated.
            gate = hero["verdict"] == "PASS"
            info["reference"] = "direct hero-led: the final look pass (stats.json) + its HERO verdict"
            info["hero_verdict"] = hero["verdict"]
            info["hero_fails"] = hero.get("fails")
            info["below_best_earlier_info"] = {v: d for v, d in info["delta_vs_gold"].items()
                                               if v != "concept" and d < -rp.DIRECT_GATE}
            info["sigma_in_band_0.98_1.03"] = 0.98 <= float(J["sigma"]) <= 1.03
        elif getattr(rp, "DIRECT", False):   # WF v10: no gold model — orthos within DIRECT_GATE of the best earlier pass
            gate = all(d >= -rp.DIRECT_GATE for v, d in info["delta_vs_gold"].items() if v != "concept")
            info["reference"] = "direct: the look stage's best earlier pass per view (not gold)"
        info["gate_vs_gold"] = gate
        ok &= gate
        if look:
            d = max(max(abs(look["scores"][v]["agree"] - info["agree"][v]), abs(look["scores"][v]["iou"] - info["iou"][v]))
                    for v in info["agree"] if v in look["scores"])
            info["max_diff_vs_look_stage"] = round(d, 5)
            ok &= d <= 1e-4
    record("look", ok, **info)
    return topo["tris"]


# ------------------------------------------------------------------------------------------------ e. renders
def fit_params(right, up, lo, hi, w, h, margin=0.06):
    r, u = np.array(right, dtype=float), np.array(up, dtype=float)
    cs = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    pr, pu = cs @ r, cs @ u
    s = min(w * (1 - 2 * margin) / (pr.max() - pr.min()), h * (1 - 2 * margin) / (pu.max() - pu.min()))
    ox = w / 2 - s * (pr.max() + pr.min()) / 2
    oy = h / 2 + s * (pu.max() + pu.min()) / 2
    return r, u, ox, oy, s


def fit_cam(right, up, lo, hi, w, h, margin=0.06):
    r, u, ox, oy, s = fit_params(right, up, lo, hi, w, h, margin)
    return rp.camera_for(tuple(r), tuple(u), ox, oy, s, w, h)


VIEW_TAG = {"side": "SIDE", "front": "FRONT", "top": "TOP", "q": "QUARTER", "muzzle": "MUZZLE", "front_q": "MUZZLE QUARTER"}
BORE_PARALLEL_COS = math.cos(math.radians(25.0))     # a rotary joint whose axis is within 25 deg of the bore direction


def best_view(rig, pose, jids, lo, hi, w, h):
    """Handheld hinge / slide limit tiles: the view (side / front / top ortho or the quarter) where the moving group's
    mean displacement between rest and `pose` is largest in projected pixels (same fit as the tile cameras)."""
    rest, posed = rig.mats(), rig.mats(pose)
    moving = [pi for pi, P in enumerate(rig.parts) if any(P.joint in rig.sub[rig.jid[i]] for i in jids)]
    if not moving:
        return "q"
    d = np.vstack([rig.world(pi, posed) - rig.world(pi, rest) for pi in moving])
    best, best_px = "q", -1.0
    for kind in ("q", "side", "front", "top"):
        r, u, _, _, s = fit_params(*view_basis(kind), lo, hi, w, h)
        px = s * float(np.linalg.norm(np.stack([d @ r, d @ u], axis=1), axis=1).mean())
        if px > best_px + 1e-9:
            best, best_px = kind, px
    return best


def bore_parallel(rig, j):
    """Handheld: a rotary joint (cylinder, or a hinge / selector / barrel_spin) turning about an axis parallel to the
    bore (it_mason_gun head index): its motion is seen end-on, from the muzzle, never from the side."""
    if j["type"] == "cylinder":
        return True
    if j["type"] not in W_ROTARY or j["type"] == "trigger":
        return False
    bl = bore_line(rig)
    d = bl[1] if bl is not None else np.array([0.0, 0.0, 1.0])
    return abs(float(np.dot(j["_axis"], d))) >= BORE_PARALLEL_COS


def visible_share(rig, mats, moving, back, n_max=1500):
    """Share of the moving group's vertices not hidden from an orthographic camera looking along -back by the parts
    that do not move with it (BVH ray from each vertex toward the camera)."""
    static = [pi for pi in range(len(rig.parts)) if pi not in set(moving)]
    if not static:
        return 1.0
    g = rig.gather(static, mats)
    V = np.vstack([rig.world(pi, mats) for pi in moving])
    if len(V) > n_max:
        V = V[np.linspace(0, len(V) - 1, n_max).astype(int)]
    b = Vector(tuple(back))
    seen = 0
    for v in V:
        hit = g["bvh"].ray_cast(Vector(tuple(v)) + b * 1e-4, b)
        seen += hit[0] is None
    return seen / len(V)


def best_view_bore(rig, pose, jids, lo, hi, w, h):
    """Handheld rotary joints about the bore axis (cylinder index, nozzle-head index): best_view's projected
    displacement, times the share of the moving group visible (mean of rest and posed), over the views that can see
    the muzzle end too ("muzzle" ortho from +z, "front_q") — "front" looks from the rear, where the body hides a
    muzzle-end part. Ties keep the order muzzle, front_q, q, side, top, front."""
    rest, posed = rig.mats(), rig.mats(pose)
    moving = [pi for pi, P in enumerate(rig.parts) if any(P.joint in rig.sub[rig.jid[i]] for i in jids)]
    if not moving:
        return "q", {}
    d = np.vstack([rig.world(pi, posed) - rig.world(pi, rest) for pi in moving])
    best, best_v, why = "q", -1.0, {}
    for kind in ("muzzle", "front_q", "q", "side", "top", "front"):
        r, u, _, _, s = fit_params(*view_basis(kind), lo, hi, w, h)
        px = s * float(np.linalg.norm(np.stack([d @ r, d @ u], axis=1), axis=1).mean())
        back = np.cross(np.array(r), np.array(u))
        vis = 0.5 * (visible_share(rig, rest, moving, back) + visible_share(rig, posed, moving, back))
        why[kind] = {"px": round(px, 2), "visible": round(vis, 3), "score": round(px * vis, 2)}
        if px * vis > best_v + 1e-9:
            best, best_v = kind, px * vis
    return best, why


def view_basis(kind):
    if kind == "muzzle":      # handheld: ortho from the muzzle end (+z), left flank +x on the image right
        return (1, 0, 0), (0, 1, 0)
    if kind == "side":
        return (0, 0, -1), (0, 1, 0)
    if kind == "top":
        return (0, 0, -1), (-1, 0, 0)
    if kind == "front":
        return (-1, 0, 0), (0, 1, 0)
    if kind == "front_q":     # handheld: muzzle-end three-quarter (muzzle +z, left flank +x), so a spinning barrel
        b = unit((0.45, 0.35, 0.82))     # cluster / its muzzle face is in view ("front" looks from -z = the rear)
        r = unit(np.cross((0, 1, 0), b))
        return tuple(r), tuple(np.cross(b, r))
    b = unit((0.62, 0.50, 0.60))
    r = unit(np.cross((0, 1, 0), b))
    return tuple(r), tuple(np.cross(b, r))


C4 = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))     # author -> Blender


def ground_object(bump=None):
    """A dark slab under y = 0 (author) with the sim's sin^2 bump across the full width."""
    mat = bpy.data.materials.get("rig_ground") or bpy.data.materials.new("rig_ground")
    nt = mat.node_tree
    if nt is None:
        mat.use_nodes = True
        nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.25, 0.23, 0.2, 1)
    nt.links.new(em.outputs[0], o.inputs["Surface"])
    prof = [(-12.0, 0.0)]
    if bump:
        for k in range(17):
            s = k / 16
            prof.append((bump["z"] + s * bump["len"], bump["h"] * math.sin(math.pi * s) ** 2))
    prof += [(12.0, 0.0), (12.0, -0.12), (-12.0, -0.12)]
    bm = bmesh.new()
    a = [bm.verts.new(A(-2.2, y, z)) for z, y in prof]
    b = [bm.verts.new(A(2.2, y, z)) for z, y in prof]
    n = len(prof)
    for i in range(n):
        k = (i + 1) % n
        bm.faces.new((a[i], a[k], b[k], b[i]))
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("rig_ground")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new("rig_ground", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def render_sheet(rig, emp, root, inp, frames, lines, path):
    rp.toon_materials()
    rp.setup_scene()
    W, H = 440, 300
    lo = np.min([p.lo for p in rig.parts], axis=0) - 0.15
    hi = np.max([p.hi for p in rig.parts], axis=0) + np.array([0.15, 0.55, 0.15])
    lo[1] = min(lo[1], -0.12)
    vehicle_hinges = [] if HANDHELD else [j for j in rig.joints
                                         if j["type"] in ("door", "hatch", "hinge") and j.get("limits")]
    # Keep a ramp or hatch at either limit inside the same camera as its rest pose.
    for j in vehicle_hinges:
        for value in j["limits"]:
            mats = rig.mats({j["id"]: value})
            for pi, part in enumerate(rig.parts):
                if part.joint not in rig.sub[rig.jid[j["id"]]]:
                    continue
                vertices = rig.world(pi, mats)
                lo = np.minimum(lo, vertices.min(axis=0) - 0.15)
                hi = np.maximum(hi, vertices.max(axis=0) + 0.15)
    if HANDHELD:     # frame the weapon itself (+ room for a magazine pulled out / a slide run back)
        lo = np.min([p.lo for p in rig.parts], axis=0)
        hi = np.max([p.hi for p in rig.parts], axis=0)
        m = 0.06 * float((hi - lo).max())
        lo, hi = lo - np.array([m, 3 * m, 2 * m]), hi + m
    cams, light = {}, {"q": (0.3, 1.0, 0.45), "side": (1.0, 0.8, -0.15), "top": (0.15, 1.0, 0.2), "front": (0.1, 0.8, 1.0)}
    if HANDHELD:
        light["front_q"] = (0.35, 0.9, 0.8)
        light["muzzle"] = (0.25, 0.85, 1.0)
    for kind in ("q", "side", "top", "front") + (("front_q",) if HANDHELD else ()):
        r, u = view_basis(kind)
        cams[kind] = fit_cam(r, u, lo, hi, W, H)
    if vehicle_hinges:
        back = unit((0.62, 0.50, -0.60))
        right = unit(np.cross((0, 1, 0), back))
        cams["rear_q"] = fit_cam(right, np.cross(back, right), lo, hi, W, H)
        light["rear_q"] = (0.3, 1.0, -0.45)
    by_type = {}
    for j in rig.joints:
        by_type.setdefault(j["type"], []).append(j)
    tiles = []

    def lim(j, k):
        return j["limits"][k] if j.get("limits") else 0.0
    yaw = by_type.get("turret_yaw", [])

    def yv(j, a):
        """a limited turret (helicopter chin gun) is posed inside its limits, never past them."""
        if j.get("limits") and not j.get("continuous"):
            return max(j["limits"][0], min(j["limits"][1], a - 360 if a > 180 else a))
        return a
    for a in (0, 45, 90, 135, 180):
        if yaw:
            tiles.append((f"TURRET YAW {yv(yaw[0], a):g}", {j["id"]: yv(j, a) for j in yaw}, "q", None))
    gp = by_type.get("weapon_pitch", [])
    if gp:
        tiles.append((f"WEAPON PITCH MIN {lim(gp[0], 0):.0f}", {j["id"]: lim(j, 0) for j in gp}, "side", None))
        tiles.append(("WEAPON PITCH 0", {}, "side", None))
        tiles.append((f"WEAPON PITCH MAX {lim(gp[0], 1):.0f}", {j["id"]: lim(j, 1) for j in gp}, "side", None))
        tiles.append((f"YAW 90 PITCH MAX", {**{j["id"]: yv(j, 90) for j in yaw}, **{j["id"]: lim(j, 1) for j in gp}}, "q", None))
        tiles.append((f"YAW 270 PITCH MIN", {**{j["id"]: yv(j, 270) for j in yaw}, **{j["id"]: lim(j, 0) for j in gp}}, "q", None))
    st = by_type.get("wheel_steer", [])
    if st:
        tiles.append(("STEER LEFT MAX", {j["id"]: lim(j, 1) for j in st}, "top", None))
        tiles.append(("STEER RIGHT MAX", {j["id"]: lim(j, 0) for j in st}, "top", None))
        tiles.append(("STEER LEFT MAX", {j["id"]: lim(j, 1) for j in st}, "q", None))
    su = by_type.get("suspension", []) + by_type.get("suspension_arm", [])
    if su:
        tiles.append((f"SUSPENSION BUMP {lim(su[0], 1) * 1000:.0f} MM", {j["id"]: lim(j, 1) for j in su}, "side", None))
        tiles.append((f"SUSPENSION DROOP {-lim(su[0], 0) * 1000:.0f} MM", {j["id"]: lim(j, 0) for j in su}, "side", None))
        if st:
            tiles.append(("BUMP + STEER", {**{j["id"]: lim(j, 1) for j in su}, **{j["id"]: lim(j, 1) for j in st}}, "front", None))
    sp = by_type.get("wheel_spin", [])
    if sp:
        tiles.append(("WHEELS ROLL 100 DEG", {j["id"]: 100 for j in sp}, "side", None))
    ro = by_type.get("rotor_spin", [])
    for a in (0, 30, 60, 90):
        if ro:
            pose = {}
            for j in ro:
                if j["id"] not in pose:
                    for name, value in continuous_pose(rig, j["id"], a).items():
                        if name in pose and abs(pose[name] - value) > 1e-6:
                            raise SystemExit(f"rig_pass.py: conflicting rotor sheet pose for {name}")
                        pose[name] = value
            tiles.append((f"ROTOR {a}", pose, "top" if a in (0, 60) else "q", None))
    for j in vehicle_hinges:
        for value in j["limits"]:
            tiles.append((f"{j['id'].upper()} {value:g}", {j["id"]: value}, "side", None))
            tiles.append((f"{j['id'].upper()} {value:g}", {j["id"]: value}, "rear_q", None))
    if HANDHELD:
        def far(j):
            L_ = j.get("limits") or [0.0, 0.0]
            return L_[0] if abs(L_[0]) > abs(L_[1]) else L_[1]
        tiles.append(("REST", {}, "q", None))
        tiles.append(("REST SIDE", {}, "side", None))
        fire = by_type.get("trigger", []) + by_type.get("slide", [])
        if fire:
            tiles.append(("TRIGGER+SLIDE LIMITS (DIAG)", {j["id"]: far(j) for j in fire}, ("auto", [j["id"] for j in fire]), None))
        mg = by_type.get("magazine", [])
        if mg:
            tiles.append((f"RELOAD: MAGAZINE OUT {abs(far(mg[0])) * 1000:.0f} MM", {j["id"]: far(j) for j in mg}, "side", None))
            tiles.append(("MAGAZINE HALF OUT", {j["id"]: far(j) / 2 for j in mg}, "q", None))
        for j in by_type.get("hinge", []):     # a hinge about the bore axis (head index): the muzzle-end aware choice
            tiles.append((f"OPEN {j['id']} {far(j):g}", {j["id"]: far(j)}, ("auto_bore" if bore_parallel(rig, j) else "auto", [j["id"]]), None))
        sp_ = by_type.get("barrel_spin", [])
        if sp_:
            tiles.append(("SPIN 30", {j["id"]: 30 for j in sp_}, "front_q", None))
        for j in by_type.get("cylinder", []):
            tiles.append((f"CYLINDER HALF INDEX {180 / max(2, int(j.get('chambers', 6))):g}", {j["id"]: 180 / max(2, int(j.get("chambers", 6)))}, ("auto_bore", [j["id"]]), None))
        if by_type.get("selector"):
            tiles.append(("SELECTOR AT LIMIT", {j["id"]: far(j) for j in by_type["selector"]}, "side", None))
    for mid, fs in rig.followers.items():     # scale joints: the master at its far limit, the followers posed with it
        m = rig.joints[rig.jid[mid]]
        L_ = m["limits"]
        far_ = L_[0] if abs(L_[0]) > abs(L_[1]) else L_[1]
        s_ = min(rig.scale_of(f, f["_follow"][1] * far_) for f in fs)
        for kind in ("side", "q"):
            tiles.append((f"{mid.upper()} {far_ * 1000:g} MM: SCALE {s_:.3f}", {mid: far_}, kind, None))
    for j in [j for j in rig.joints if j["type"] in SCALE and not j.get("_follow")]:
        v_ = j["_vals"][0] if abs(j["_vals"][0]) > abs(j["_vals"][1]) else j["_vals"][1]
        for kind in ("side", "q"):
            tiles.append((f"SCALE {j['id'].upper()} {rig.scale_of(j, v_):.3f}", {j["id"]: v_}, kind, None))
    sus_of = {c["id"]: c.get("joint_suspension") for c in inp["contacts"]}
    ids = [c["id"] for c in inp["contacts"]]
    for fr in frames:
        pose = {sus_of[i]: susp_value(rig, rig.joints[rig.jid[sus_of[i]]], fr["comp"][k])
                for k, i in enumerate(ids) if sus_of.get(i) in rig.jid}
        tiles.append((fr["label"], pose, "side", fr))
    if HANDHELD:
        # Fit every requested pose, including detached magazines and long projectile travel.
        posed_lo = np.min([p.lo for p in rig.parts], axis=0)
        posed_hi = np.max([p.hi for p in rig.parts], axis=0)
        for _, pose, _, _ in tiles:
            mats = rig.mats(pose)
            for pi in range(len(rig.parts)):
                vertices = rig.world(pi, mats)
                posed_lo = np.minimum(posed_lo, vertices.min(axis=0))
                posed_hi = np.maximum(posed_hi, vertices.max(axis=0))
        margin = 0.06 * float((posed_hi - posed_lo).max())
        lo, hi = posed_lo - margin, posed_hi + margin
        for kind in ("q", "side", "top", "front", "front_q", "muzzle"):
            r, u = view_basis(kind)
            cams[kind] = fit_cam(r, u, lo, hi, W, H)
        # hinge / slide limit tiles: render from the view that shows the moving part's displacement best, label it;
        # rotary joints about the bore axis (auto_bore): the same, weighted by how much of the moving group is visible
        view_choice = {}
        for k, (label, pose, kind, fr) in enumerate(tiles):
            if isinstance(kind, tuple):
                if kind[0] == "auto_bore":
                    kind, why = best_view_bore(rig, pose, kind[1], lo, hi, W, H)
                    view_choice[label] = {"view": kind, "candidates": why}
                else:
                    kind = best_view(rig, pose, kind[1], lo, hi, W, H)
                tiles[k] = (f"{label} [{VIEW_TAG[kind]}]", pose, kind, fr)
    with open(os.path.join(ODIR, "rig_pose_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"subject": SUBJECT, "sheet": os.path.basename(path),
                   "framing": {"bounds_min": lo.tolist(), "bounds_max": hi.tolist(),
                               "source": "requested pose union" if HANDHELD else "rest plus vehicle hinge limits"},
                   **({"bore_axis_views": view_choice} if HANDHELD and view_choice else {}),
                   "poses": [{"label": label, "joints": pose, "view": kind}
                             for label, pose, kind, _ in tiles]}, f, indent=1)
    imgs = []
    tmp = os.path.join(ODIR, "_rig_tile.png")
    com = np.array(inp["com"])
    for label, pose, kind, fr in tiles:
        set_pose(rig, emp, pose)
        g = None
        if fr is not None:
            R = np.array(fr["rot"])
            p = np.array(fr["pos"])
            zoff = p[2] - com[2]
            t = p - R @ (com + np.array([0.0, GROUND_Y, 0.0]))     # inp com is above ground_y; the mesh is not
            t[2] -= zoff
            M = Matrix.Identity(4)
            for a in range(3):
                for b in range(3):
                    M[a][b] = R[a][b]
                M[a][3] = t[a]
            root.matrix_world = C4 @ M @ C4.inverted()
            bump = fr.get("bump")
            g = ground_object({**bump, "z": bump["z"] - zoff} if bump else None)
        bpy.context.view_layer.update()
        rp.set_light(light[kind])
        rp.render_to(tmp, cams[kind], W, H)
        imgs.append((label, rp.render_to.last[..., :3].copy()))
        if g is not None:
            me = g.data
            bpy.data.objects.remove(g)
            bpy.data.meshes.remove(me)
            root.matrix_world = Matrix.Identity(4)
    set_pose(rig, emp)
    if os.path.exists(tmp):
        os.remove(tmp)
    cols = 5
    rows = (len(imgs) + cols - 1) // cols
    gap, lab = 10, 22
    text_h = 18 * len(lines) + 20
    sheet = np.ones((rows * (H + lab + gap) + gap + text_h, cols * (W + gap) + gap, 3), np.float32)
    for k, (label, im) in enumerate(imgs):
        y = gap + (k // cols) * (H + lab + gap)
        x = gap + (k % cols) * (W + gap)
        rp.draw_text(sheet, x, y + 3, label, 2)
        sheet[y + lab:y + lab + H, x:x + W] = im
    y = rows * (H + lab + gap) + gap
    for ln in lines:
        col = (0.6, 0.05, 0.05) if ln.startswith("FAIL") else (0.05, 0.35, 0.1) if ln.startswith("PASS") else (0.1, 0.1, 0.1)
        rp.draw_text(sheet, gap, y, ln, 2, col)
        y += 18
    rp.imgio.save(path, sheet)


# ------------------------------------------------------------------------------------------------ summary
def summary_lines(M, com):
    lines = [f"{SUBJECT} RIG - MASS {M:.0f} KG - COM {com[0]:.2f} {com[1]:.2f} {com[2]:.2f}"]
    if HANDHELD:
        lines = [f"{SUBJECT} RIG (HANDHELD) - MASS {M:.2f} KG - COM {com[0]:.3f} {com[1]:.3f} {com[2]:.3f} - SOCKETS {len(SOCKETS)}"]
    groups = {}
    for name, t in TESTS.items():
        if ":" in name and "type" in t:
            groups.setdefault((name.split(":")[0], t["type"]), []).append((name, t))
        else:
            groups[(name, "")] = [(name, t)]
    for (kind, typ), items in groups.items():
        ok = sum(1 for _, t in items if t["pass"])
        head = f"{'PASS' if ok == len(items) else 'FAIL'} {kind} {typ} {ok}/{len(items)}"
        t = items[0][1]
        extra = ""
        if kind == "sweep":
            cl = [x[1].get("clear") for x in items if isinstance(x[1].get("clear"), list)]
            if cl:
                limited = [(name, test) for name, test in items if isinstance(test.get("clear"), list)]
                signatures = {(tuple(test["limits"]), tuple(test["clear"]), test["unit"]) for _, test in limited}
                if len(limited) == len(items) and len(signatures) == 1:
                    t = limited[0][1]
                    extra = f" LIMITS {t['limits'][0]:g}..{t['limits'][1]:g} CLEAR {t['clear'][0]:g}..{t['clear'][1]:g} {t['unit']}"
                else:
                    # Distinct joints have distinct domains; their numeric intersection is not a joint clearance.
                    lines.append(head + " JOINTS")
                    for name, test in items:
                        label = name.split(":", 1)[1]
                        if isinstance(test.get("clear"), list):
                            lines.append(f"  {label} {'PASS' if test['pass'] else 'FAIL'} LIMITS {test['limits'][0]:g}..{test['limits'][1]:g} CLEAR {test['clear'][0]:g}..{test['clear'][1]:g} {test['unit']}")
                        else:
                            lines.append(f"  {label} {'PASS' if test['pass'] else 'FAIL'} 0..360 COLLIDING STEPS {test.get('colliding_steps', 0)}")
                    continue
            else:
                extra = f" 0..360 COLLIDING STEPS {sum(x[1].get('colliding_steps', 0) for x in items)}"
        elif kind == "pivot" and typ in CONTINUOUS:
            extra = f" RUNOUT RADIAL {max(x[1]['radial_runout_mm'] for x in items):.2f} AXIAL {max(x[1]['axial_runout_mm'] for x in items):.2f} MM"
        elif kind == "pivot" and typ == "turret_yaw":
            extra = f" RING CENTRE OFF {t['ring_centre_off_mm']:.1f} MM SWEPT R {t['swept_radius_m']:.2f}"
        elif kind == "pivot" and typ == "weapon_pitch":
            extra = f" TRUNNION OFF BORE {t['trunnion_off_bore_mm']:.1f} MM"
        elif kind == "stability" and "tip_left_deg" in t:
            extra = f" TIP SIDE {min(t['tip_left_deg'], t['tip_right_deg']):.1f} FRONT {t['tip_front_deg']:.1f} REAR {t['tip_rear_deg']:.1f} DEG"
        elif kind == "ground":
            bs = [c["bottom_mm"] for c in t.get("contacts", {}).values() if "bottom_mm" in c]
            extra = f" BOTTOMS {min(bs):.1f}..{max(bs):.1f} MM" if bs else ""
        elif kind == "sim:drop_settle":
            extra = f" SETTLE {t['settle_s']:.2f} S RIDE ERR {t['ride_height_err_m'] * 1000:.1f} MM MAX COMP {t['max_compression_m'] * 1000:.0f} MM CLEARANCE {t['min_chassis_clearance_m']:.2f}"
        elif kind == "sim:bump":
            extra = f" MAX COMP {t['worst_compression_m'] * 1000:.0f} / ARCH {t['arch_clear_m'] * 1000:.0f} MM PITCH {t['pitch_deg'][0]:.1f}..{t['pitch_deg'][1]:.1f} CLEARANCE {t['min_chassis_clearance_m']:.2f}"
        elif kind == "sim:accelerate":
            extra = f" SQUAT {t['steady_pitch_deg']:.2f} DEG"
        elif kind == "sim:brake":
            extra = f" DIVE {t['dive_pitch_deg']:.2f} DEG STOP {t['stop_dist_m']:.1f} M"
        elif kind == "sim:lateral":
            extra = f" ROLL {t['steady_roll_deg']:.2f} DEG"
        elif kind == "look" and "agree" in t:
            extra = " AGREE " + " ".join(f"{v[:1]} {a:.4f}" for v, a in t["agree"].items()) + f" TRIS {t['tris']}"
        elif kind == "export":
            extra = f" TRIS {t['tris']} CLIPS {len(t['clips'])}"
        elif kind == "pose":
            extra = " " + " ".join(f"{n.split(':', 1)[1]} {x['dist_m']:.3f}/{x['tol_m']:g} M"
                                   + (f" {x['normal_off_deg']:.0f}/{x['tol_deg']:g} DEG" if "normal_off_deg" in x else "")
                                   for n, x in items)
        lines.append(head + extra)
    return lines


# ------------------------------------------------------------------------------------------------ main
def main():
    t0 = time.time()
    mod = rp.load_build()
    root, parts = mod.build()
    objs = [o for o in parts if o.type == "MESH"]
    root.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    rig = Rig(objs)
    print(f"RIG {SUBJECT}: {len(rig.joints)} joints, {len(rig.parts)} parts ({time.time() - t0:.0f} s build)")
    test_pivots(rig)
    measured = test_sweeps(rig)
    test_sockets(rig)
    test_pose_expect(rig)
    if HANDHELD:     # WF v10: a handheld weapon has no ground contacts, no stability, no drive sim; mass + COM reported
        M, com, I = mass_props(rig)
        cols, chassis = (colliders(rig) if PHYS.get("colliders") else ([], None))
        inp = {"mode": "handheld", "mass": M, "com": [float(v) for v in com], "inertia": [float(v) for v in I], "contacts": []}
        frames, static = [], {}
    else:
        test_ground(rig)
        M, com, I = mass_props(rig)
        cols, chassis = colliders(rig)
        if chassis:
            record("colliders", chassis["bottom_m"] > 0.02, chassis=chassis["id"], chassis_bottom_m=chassis["bottom_m"],
                   count=len(cols), ids=[c["id"] for c in cols])
        else:
            record("colliders", False, why="physics.colliders has no chassis collider")
        inp = sim_input(rig, M, com, I, measured, chassis)
        test_static(inp)
        frames = []
    if HANDHELD:
        pass
    elif len(inp["contacts"]) >= 2:
        res = rig_sim.simulate(inp)
        frames = res["frames"]
        for k, v in res["tests"].items():
            record(f"sim:{k}", v.pop("pass"), **v)
        static = res["static"]
    else:
        static = {}
        record("sim:drop_settle", False, why="no ground contacts in physics")
    emp = build_hierarchy(rig, root)
    socket_empties(rig, emp, root)
    pose_check(rig, emp)
    tris = test_look(rig)
    clips = make_clips(rig, emp)
    glb = os.path.join(ODIR, f"{SUBJECT}_rigged.glb")
    export_glb(glb)
    test_export(rig, glb, tris, clips)
    if any(continuous_joint(j) or j.get("run_pose") or j.get("sync") for j in rig.joints):
        try:
            motion = glb_motion.validate(*glb_motion.read_binary(glb), rig.joints, CLIPS)
        except (ValueError, KeyError, struct.error) as error:
            motion = {"pass": False, "error": str(error)}
        record("export_motion", motion.pop("pass"), **motion)
    for e in emp.values():
        e.animation_data_clear()
    set_pose(rig, emp)
    resolved = {k: v for k, v in RIG.items()}
    resolved["joints"] = [{k: v for k, v in j.items() if not k.startswith("_")} | {"resolved_parts": j["_names"]}
                          | ({"resolved_length_m": round(j["_L"], 6),
                              "resolved_scale_range": [round(rig.scale_of(j, v), 5) for v in j["_vals"]],
                              "scale_rule": "node scale along the axis = 1 + value / resolved_length_m"
                                            + (f"; value = {j['_follow'][1]:g} x {j['_follow'][0]}" if j.get("_follow") else "")}
                             if j["type"] in SCALE else {})
                          for j in rig.joints]
    resolved["derived"] = {"mass_kg": round(M, 1),
                           **({"mass_game_kg": float((PHYS.get("mass") or {})["mass_game_kg"])}
                              if (PHYS.get("mass") or {}).get("mass_game_kg") is not None else {}),
                           "com": [round(float(v), 4) for v in com],
                           "inertia_kgm2": [round(float(v), 1) for v in I], "colliders": cols,
                           "clear_ranges": measured, "static_loads_N": static.get("loads_N"),
                           **({"sockets": [f"socket_{s_['id']}" for s_ in SOCKETS]} if SOCKETS else {}),
                           "spring_rate_note": "k_i = N_i / (g / (2 pi f)^2), damper = 2 zeta sqrt(k_i N_i / g)",
                           "clips": clips, "glb": os.path.basename(glb), "frame": "glTF: +Y up, +Z nose, +X left, metres"}
    with open(os.path.join(ODIR, f"{SUBJECT}_rig.json"), "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=1)
    lines = summary_lines(M, com)
    npass = sum(1 for t in TESTS.values() if t["pass"])
    stats = {"subject": SUBJECT, "rig": RIG_PATH.replace("\\", "/"),
             "pass": npass == len(TESTS), "passed": npass, "total": len(TESTS),
             "failed": [k for k, t in TESTS.items() if not t["pass"]], "summary": lines, "tests": TESTS,
             **({"owner_items": {k: t["owner_item"] for k, t in TESTS.items() if t.get("owner_item")}}
                if any(t.get("owner_item") for t in TESTS.values()) else {}),
             "sim_input": inp, "sim_frames": frames}
    with open(os.path.join(ODIR, "rig_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1, default=float)
    for ln in lines:
        print("SUMMARY", ln)
    if not NO_RENDER:
        render_sheet(rig, emp, root, inp, frames, lines, os.path.join(ODIR, "rig_sheet.png"))
    print(f"RIG {'PASS' if stats['pass'] else 'FAIL'} {npass}/{len(TESTS)} failed={stats['failed']} ({time.time() - t0:.0f} s)")
    print("DONE", os.path.join(ODIR, "rig_stats.json"))


main()
