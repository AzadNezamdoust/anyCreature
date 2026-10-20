"""Validate declared running attachments and sync against actual GLB animation accessors."""
import bisect
import json
import math
import struct


def read_binary(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:4] != b"glTF":
        raise ValueError("expected GLB")
    offset, document, binary = 12, None, None
    while offset < len(raw):
        length, kind = struct.unpack_from("<I4s", raw, offset)
        chunk = raw[offset + 8:offset + 8 + length]
        if kind == b"JSON":
            document = json.loads(chunk)
        elif kind == b"BIN\0":
            binary = chunk
        offset += 8 + length
    if document is None or binary is None:
        raise ValueError("missing JSON/BIN chunk")
    return document, binary


def validate(document, binary, joints, clip_names, tolerance_deg=0.01):
    by_id = {j["id"]: j for j in joints}
    errors, checked, samples = [], 0, 0
    spinning = {"wheel_spin", "rotor_spin", "barrel_spin", "cylinder"}
    connected = {j["id"]: set() for j in joints}
    for j in joints:
        if j.get("sync") and j["sync"]["joint"] in connected:
            connected[j["id"]].add(j["sync"]["joint"])
            connected[j["sync"]["joint"]].add(j["id"])
    order = {j["id"]: i for i, j in enumerate(joints)}

    def leader(name):
        found, queue = set(), [name]
        while queue:
            current = queue.pop()
            if current not in found:
                found.add(current)
                queue.extend(connected[current] - found)
        return min(found, key=order.get)

    def accessor(index):
        item = document["accessors"][index]
        view = document["bufferViews"][item["bufferView"]]
        if item["componentType"] != 5126 or item.get("sparse") or view.get("buffer", 0) != 0:
            raise ValueError("unsupported animation accessor")
        size = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[item["type"]]
        start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
        stride = view.get("byteStride", size * 4)
        return [struct.unpack_from("<" + "f" * size, binary, start + i * stride) for i in range(item["count"])]

    def difference(a, b):
        return abs((a - b + 180) % 360 - 180)

    for joint in joints:
        continuous = joint["type"] in spinning or (joint["type"] == "turret_yaw" and (joint.get("limits") is None or joint.get("continuous")))
        if not continuous and not joint.get("run_pose") and not joint.get("sync"):
            continue
        clip_name = joint.get("clip") or clip_names.get(joint["type"])
        clip = next((a for a in document.get("animations", []) if a.get("name") == clip_name), None)
        if clip is None:
            errors.append(f"{joint['id']}: missing {clip_name}")
            continue
        required = {joint["id"], *(joint.get("run_pose") or {})}
        if joint.get("sync"):
            required.add(joint["sync"]["joint"])
        curves = {}
        for channel in clip["channels"]:
            node = document["nodes"][channel["target"]["node"]]
            name, path = node.get("name"), channel["target"]["path"]
            if name not in required:
                continue
            sampler = clip["samplers"][channel["sampler"]]
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                raise ValueError("running motion requires sampled LINEAR channels")
            times, values = [t[0] for t in accessor(sampler["input"])], accessor(sampler["output"])
            if (len(times) != len(values) or len(times) < 2 or
                    not all(math.isfinite(t) for t in times) or
                    any(b <= a for a, b in zip(times, times[1:])) or
                    not all(math.isfinite(v) for row in values for v in row)):
                raise ValueError(f"{clip_name}/{name}: invalid animation samples")
            if path in ("translation", "scale"):
                parked = node.get(path, [0, 0, 0] if path == "translation" else [1, 1, 1])
                if (not all(math.isfinite(v) for v in parked) or
                        any(len(row) != 3 or max(abs(v - parked[i]) for i, v in enumerate(row)) > 1e-6 for row in values)):
                    errors.append(f"{clip_name}/{name}: running {path} leaves parked transform")
                continue
            if path != "rotation":
                errors.append(f"{clip_name}/{name}: unsupported running channel {path}")
                continue
            quaternions = values
            axis = by_id[name].get("_axis", by_id[name]["axis"])
            length = math.sqrt(sum(a * a for a in axis))
            axis = [a / length for a in axis]
            angles = []
            for q in quaternions:
                length_q = math.sqrt(sum(v * v for v in q))
                if len(q) != 4 or not math.isfinite(length_q) or abs(length_q - 1) > 1e-4:
                    raise ValueError(f"{clip_name}/{name}: nonunit rotation quaternion")
                q = [v / length_q for v in q]
                sine = sum(q[i] * axis[i] for i in range(3))
                if max(abs(q[i] - sine * axis[i]) for i in range(3)) > 1e-5:
                    errors.append(f"{clip_name}/{name}: rotation leaves declared axis")
                angle = math.degrees(2 * math.atan2(sine, q[3]))
                if angles:
                    angle = angles[-1] + (angle - angles[-1] + 180) % 360 - 180
                angles.append(angle)
            curves[name] = (times, angles)
        missing = required - curves.keys()
        if missing:
            errors.append(f"{clip_name}: missing rotation channels {sorted(missing)}")
            continue
        if continuous and leader(joint["id"]) == joint["id"]:
            expected_turn = 360.0 / max(2, int(joint.get("chambers", 6))) if joint["type"] == "cylinder" else 360.0
            key_times, key_angles = curves[joint["id"]]
            winding = key_angles[-1] - key_angles[0]
            checked += 1
            if abs(winding - expected_turn) > tolerance_deg:
                errors.append(f"{clip_name}/{joint['id']}: winding {winding:.6f} differs from expected {expected_turn:.6f} deg")
            duration = key_times[-1] - key_times[0]
            if duration <= 0:
                errors.append(f"{clip_name}/{joint['id']}: nonpositive duration")
            else:
                for time, angle in zip(key_times, key_angles):
                    checked += 1
                    expected = key_angles[0] + expected_turn * (time - key_times[0]) / duration
                    if abs(angle - expected) > tolerance_deg:
                        errors.append(f"{clip_name}/{joint['id']}: continuous progression differs at {time:.6f}s")
        times = sorted({t for name in required for t in curves[name][0]})
        times = sorted(set(times + [(a + b) / 2 for a, b in zip(times, times[1:])]))

        def at(name, time):
            ts, vs = curves[name]
            if len(ts) < 2 or any(b <= a for a, b in zip(ts, ts[1:])):
                raise ValueError("invalid animation time domain")
            if time < ts[0] - 1e-7 or time > ts[-1] + 1e-7:
                errors.append(f"{clip_name}/{name}: running channel does not span clip")
            i = max(0, min(len(ts) - 2, bisect.bisect_right(ts, time) - 1))
            fraction = max(0, min(1, (time - ts[i]) / (ts[i + 1] - ts[i])))
            # Axis alignment is checked above: interpolating unwrapped angles is quaternion SLERP.
            return vs[i] + fraction * (vs[i + 1] - vs[i])

        for time in times:
            samples += 1
            for name, value in (joint.get("run_pose") or {}).items():
                checked += 1
                if difference(at(name, time), float(value)) > tolerance_deg:
                    errors.append(f"{clip_name}/{name}: running pose differs at {time:.6f}s")
            sync = joint.get("sync")
            if sync:
                checked += 1
                expected = at(joint["id"], time) * float(sync.get("ratio", 1)) + float(sync.get("phase_deg", 0))
                if difference(at(sync["joint"], time), expected) > tolerance_deg:
                    errors.append(f"{clip_name}/{joint['id']}: sync differs at {time:.6f}s")
    return {"pass": not errors, "constraints_checked": checked, "sampled_times": samples,
            "angular_tolerance_deg": tolerance_deg, "error_count": len(errors), "first_errors": errors[:10]}


def channel_values(document, binary, node_name, path):
    """{animation name: [sampled output values]} of `path` ("scale" / "translation" / "rotation") on the named node
    (rig_pass.py export test of scale joints)."""
    nodes = document.get("nodes", [])
    idx = next((i for i, n in enumerate(nodes) if n.get("name") == node_name), None)
    out = {}
    if idx is None:
        return out

    def accessor(index):
        item = document["accessors"][index]
        view = document["bufferViews"][item["bufferView"]]
        size = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[item["type"]]
        if item["componentType"] != 5126 or item.get("sparse"):
            raise ValueError("unsupported animation accessor")
        start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
        stride = view.get("byteStride", size * 4)
        return [struct.unpack_from("<" + "f" * size, binary, start + i * stride) for i in range(item["count"])]

    for anim in document.get("animations", []):
        for ch in anim.get("channels", []):
            t = ch.get("target", {})
            if t.get("node") == idx and t.get("path") == path:
                out[anim.get("name", "")] = accessor(anim["samplers"][ch["sampler"]]["output"])
    return out
