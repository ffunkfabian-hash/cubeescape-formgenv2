"""Abgleich Baseline (BAnn) gegen BALLONs exportiertes GLB: Silhouetten-IoU in drei Orthos, Maße, Dreiecke.

  python tools/ballon_compare.py [--glb-dir ~/Library/Caches/CubeEscapeBallon/out] [--out <json>] [--sheet <png>]
  python tools/ballon_compare.py --base v21     # v2.1-Piloten (BASIC-NN-v2.1.glb) gegen die v2-Auswertung der Grundform (xprof)

Nur gelesen: BALLONs GLB (Blender-Export, glTF Y oben) und out/geometry/BAnn.json (v2, Meter, Z oben, −Y vorn).
Gilt nur, wenn BALLONs Spec neben dem GLB bytegleich zum gepinnten Spec ist (sonst „veraltet“).
Masken: gefüllte Dreiecke, 0,5 mm je Pixel, gemeinsamer Ursprung (Socket_Hand = 0); kein Fit, keine Verschiebung.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import ballon, generator, geom, model  # noqa: E402

MM_PX = 0.5
VIEWS = {"side": (1, 2), "top": (1, 0), "front": (0, 2)}   # Achsen (Blender-Rahmen): Seite = Y/Z, oben = Y/X, vorn = X/Z
TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
SIZES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], float).reshape(4, 4).T
    t = np.eye(4); t[:3, 3] = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    r = np.eye(4); r[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    s = np.diag([*node.get("scale", [1, 1, 1]), 1])
    return t @ r @ s


def load_glb(path):
    """Return world-space triangles (n,3,3) in Blender frame (X links, Y hinten, Z oben) and node names."""
    data = Path(path).read_bytes()
    n = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + n]); binary = data[20 + n + 8:]

    def accessor(i):
        a = gltf["accessors"][i]; v = gltf["bufferViews"][a["bufferView"]]
        count, size = a["count"], SIZES[a["type"]]
        dtype = np.dtype(TYPES[a["componentType"]])
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0) or dtype.itemsize * size
        raw = np.frombuffer(binary, np.uint8, count=stride * (count - 1) + dtype.itemsize * size, offset=start)
        return np.lib.stride_tricks.as_strided(raw.view(np.uint8), (count, size * dtype.itemsize), (stride, 1)).copy().view(dtype).reshape(count, size)

    tris, names = [], []

    def walk(i, parent):
        node = gltf["nodes"][i]; m = parent @ _matrix(node)
        if "mesh" in node:
            names.append(node.get("name", str(i)))
            for prim in gltf["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                pos = accessor(prim["attributes"]["POSITION"]).astype(float)
                idx = accessor(prim["indices"]).reshape(-1) if "indices" in prim else np.arange(len(pos))
                world = (np.c_[pos, np.ones(len(pos))] @ m.T)[:, :3]
                tris.append(world[idx.reshape(-1, 3)])
        for c in node.get("children", []):
            walk(c, m)

    for root in gltf["scenes"][gltf.get("scene", 0)]["nodes"]:
        walk(root, np.eye(4))
    t = np.concatenate(tris)
    return np.stack([t[..., 0], -t[..., 2], t[..., 1]], axis=-1), names   # glTF (x, y oben, z) → Blender (x, −z, y)


def load_v2(path):
    doc = json.loads(Path(path).read_text())
    tris = [np.asarray(p["mesh"]["vertices"], float)[np.asarray(p["mesh"]["faces"])] for p in doc["parts"]]
    return np.concatenate(tris), doc


def mask(tris, axes, lo, shape):
    im = Image.new("1", shape[::-1], 0); d = ImageDraw.Draw(im)
    pts = (tris[..., list(axes)] * 1000 - lo) / MM_PX
    for t in pts:
        d.polygon([(float(x), float(shape[0] - 1 - y)) for x, y in t], fill=1)
    return np.asarray(im, bool)


def evaluated_base(snap, num, base):
    """Baseline-Geometrie der Grundform `base` frisch ausgewertet (mit Booleans und Fasen wie die Pipeline)."""
    author, _ = generator.build({"letter": "A", "name": "Baseline", "idea": "Bezug", "since": "0.2", "skin": "standard",
                                 "base": base, "params": {}}, num, snap)
    doc = geom.evaluate(model.normalize(author))
    return np.concatenate([np.asarray(p["mesh"]["vertices"], float)[np.asarray(p["mesh"]["faces"])] for p in doc["parts"]]), doc


def compare(glb, geometry):
    a, names = load_glb(glb); b, doc = load_v2(geometry) if isinstance(geometry, (str, Path)) else geometry
    result = {"triangles": {"ballon": int(len(a)), "v2": int(len(b))}, "views": {},
              "dims_mm": {}, "ballon_objects": len(names)}
    for k, i in (("length", 1), ("height", 2), ("width", 0)):
        result["dims_mm"][k] = {"ballon": round(float(np.ptp(a[..., i])) * 1000, 2), "v2": round(float(np.ptp(b[..., i])) * 1000, 2)}
    masks = {}
    for view, axes in VIEWS.items():
        both = np.concatenate([a.reshape(-1, 3), b.reshape(-1, 3)])[:, list(axes)] * 1000
        lo = both.min(0) - 4; shape = tuple(int(x) for x in ((both.max(0) + 4 - lo) / MM_PX)[::-1] + 1)
        ma, mb = mask(a, axes, lo, shape), mask(b, axes, lo, shape)
        result["views"][view] = {"iou": round(float((ma & mb).sum() / (ma | mb).sum()), 4),
                                 "only_ballon_px": int((ma & ~mb).sum()), "only_v2_px": int((mb & ~ma).sum())}
        masks[view] = (ma, mb)
    return result, masks


def overlay(ma, mb, height=150):
    img = np.full(ma.shape + (3,), 236, np.uint8)
    img[ma] = [220, 70, 80]; img[mb] = [60, 130, 230]; img[ma & mb] = [95, 80, 150]
    im = Image.fromarray(img)
    return im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--glb-dir", type=Path, default=Path.home() / "Library/Caches/CubeEscapeBallon/out")
    p.add_argument("--out-dir", type=Path, default=ROOT / "out"); p.add_argument("--out", type=Path); p.add_argument("--sheet", type=Path)
    p.add_argument("--base", choices=("standard", "v21"), default="standard")
    p.add_argument("--allow-stale", action="store_true", help="auch vergleichen, wenn BALLONs Spec neben dem GLB abweicht (Status nennt die Felder)")
    a = p.parse_args(argv)
    suffix = "-v2.1" if a.base == "v21" else ""
    snap = ballon.snapshot(); report = {"ballon_commit": ballon.config()["commit"], "mm_per_px": MM_PX, "types": {}}
    rows = []
    for num in ballon.TYPES:
        folder = a.glb_dir / f"BASIC-{num}{suffix}"
        glb, spec = folder / f"BASIC-{num}{suffix}.glb", folder / f"BASIC-{num}{suffix}.spec.json"
        entry = {}
        if a.base == "v21" and not ballon.has_base(snap, num, "v21"):
            continue
        if not glb.exists():
            entry["status"] = "GLB fehlt"
        elif hashlib.sha256(spec.read_bytes()).hexdigest() != ballon.source(snap, num, a.base)["spec_sha256"] and not a.allow_stale:
            entry["status"] = "veraltet (Spec neben GLB ≠ gepinnter Spec)"
        else:
            pinned, beside = ballon.load_spec(snap, num, a.base), json.loads(spec.read_text())
            stale = sorted(k for k in set(pinned) | set(beside) if pinned.get(k) != beside.get(k))
            source = a.out_dir / f"geometry/BA{num}.json" if a.base == "standard" else evaluated_base(snap, num, a.base)
            res, masks = compare(glb, source)
            entry = {"status": "verglichen" + (f" (GLB-Spec weicht ab: {', '.join(stale)})" if stale else ""), **res}
            rows.append((num, masks))
        report["types"][num] = entry
        v = entry.get("views", {})
        print(num, entry["status"], {k: x["iou"] for k, x in v.items()}, entry.get("triangles", ""))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    if a.sheet and rows:
        tiles = [[overlay(*m[v]) for v in VIEWS] for _, m in rows]
        w = max(sum(t.width for t in row) + 20 * len(row) for row in tiles) + 130
        sheet = Image.new("RGB", (w, 20 + 170 * len(tiles)), "#e9e6df"); d = ImageDraw.Draw(sheet)
        for i, ((num, _), row) in enumerate(zip(rows, tiles)):
            y = 10 + 170 * i; x = 130
            d.text((10, y + 60), f"BASIC-{num}", fill="#995021")
            for view, t in zip(VIEWS, row):
                sheet.paste(t, (x, y)); d.text((x, y + 152), f"{view} IoU {report['types'][num]['views'][view]['iou']:.4f}", fill="#22252a"); x += t.width + 20
        a.sheet.parent.mkdir(parents=True, exist_ok=True); sheet.save(a.sheet)


if __name__ == "__main__":
    main()
