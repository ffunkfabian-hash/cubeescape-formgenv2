"""Abgleich Baseline (BAnn) gegen BALLONs exportiertes GLB: Silhouetten-IoU in drei Orthos, Maße, Dreiecke.

  python tools/ballon_compare.py [--glb-dir ~/Library/Caches/CubeEscapeBallon/out] [--out <json>] [--sheet <png>]
  python tools/ballon_compare.py --base v21     # v2.1-Piloten (BASIC-NN-v2.1.glb) gegen die v2-Auswertung der Grundform (xprof)
  python tools/ballon_compare.py --asset BA01 [--glb <BALLON-GLB>] [--out <json>]     # 0.3: Kit-Asset gegen BALLON

--asset (0.5 „Forge“) vergleicht out/assets/<ID>.glb (BALLONs Kit über formgen.asset) mit einer BALLON-GLB: Netze und Dreiecke je
Netz, Materialien samt PBR-Werten, Leerknoten (Baugruppen, Anker), Dreieckspositionen in Weltkoordinaten (µm, Windung erhalten)
Knotenbaum (Eltern und Weltlage jedes Knotens, auch Anker) und Bytegleichheit; Vertexzahlen nur als Information (Normalen-Splits hängen an BALLONs Kit-Stand der Referenz).

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


def load_glb(path, per_node=False):
    """Return world-space triangles (n,3,3) in Blender frame (X links, Y hinten, Z oben) and node names.
    per_node: instead {(Knotenname, Materialname): Dreiecke} je Netzknoten und Primitiv-Material."""
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

    tris, names, groups = [], [], {}

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
                material = gltf["materials"][prim["material"]].get("name") if "material" in prim else None
                groups.setdefault((names[-1], material), []).append(tris[-1])
        for c in node.get("children", []):
            walk(c, m)

    for root in gltf["scenes"][gltf.get("scene", 0)]["nodes"]:
        walk(root, np.eye(4))
    blender = lambda t: np.stack([t[..., 0], -t[..., 2], t[..., 1]], axis=-1)   # noqa: E731  glTF (x, y oben, z) → Blender (x, −z, y)
    if per_node:
        return {k: blender(np.concatenate(v)) for k, v in groups.items()}
    return blender(np.concatenate(tris)), names


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


def triangle_set(tris):
    """Weltdreiecke als sortierte Liste ganzzahliger µm-Tupel; jedes Dreieck zyklisch auf die kleinste Ecke gedreht (Windung bleibt)."""
    t = np.round(np.asarray(tris) * 1e6).astype(np.int64)
    out = []
    for tri in t:
        k = min(range(3), key=lambda i: tuple(tri[i]))
        out.append(tuple(map(tuple, np.roll(tri, -k, axis=0))))
    return sorted(out)


def node_tree(path):
    """Alle Knoten: Name → (Elternname, Weltmatrix auf µm bzw. 1e-6 gerundet) – Hierarchie und Lage von Baugruppen und Ankern."""
    data = Path(path).read_bytes()
    n = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + n])
    found = {}

    def walk(i, parent, m):
        node = gltf["nodes"][i]
        world = m @ _matrix(node)
        name = node.get("name", str(i))
        found[name] = (parent, tuple(int(round(float(x) * 1e6)) for x in world.reshape(-1)))
        for c in node.get("children", []):
            walk(c, name, world)

    for root in gltf["scenes"][gltf.get("scene", 0)]["nodes"]:
        walk(root, None, np.eye(4))
    return found


def compare_asset(asset_glb, ballon_glb):
    """Kit-Asset gegen BALLON-GLB: dreiecks- und materialgleich heißt gleiche Netze mit gleichen Dreiecken je Netz und Material,
    gleiche Materialien (Name, PBR) und gleiche Dreiecke im Raum."""
    from formgen import asset
    a, b = asset.glb_info(asset_glb), asset.glb_info(ballon_glb)
    tris = lambda info: {k: [(x["triangles"], x["material"]) for x in v] for k, v in info["meshes"].items()}   # noqa: E731
    ta, tb = tris(a), tris(b)
    ma, mb = a["materials"], b["materials"]
    ga, gb = load_glb(asset_glb, per_node=True), load_glb(ballon_glb, per_node=True)     # je Netzknoten und Material
    sa = {k: triangle_set(v) for k, v in ga.items()}
    sb = {k: triangle_set(v) for k, v in gb.items()}
    na, nb = node_tree(asset_glb), node_tree(ballon_glb)
    verts = {k: (sum(x["vertices"] for x in a["meshes"][k]), sum(x["vertices"] for x in b["meshes"][k]))
             for k in a["meshes"] if k in b["meshes"]}
    result = {
        "triangles": {"asset": a["triangles"], "ballon": b["triangles"]},
        "meshes_equal": ta == tb, "meshes_differing": sorted(k for k in set(ta) | set(tb) if ta.get(k) != tb.get(k)),
        "materials_equal": ma == mb, "materials_differing": sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k)),
        "empties_equal": a["empties"] == b["empties"],
        "nodes_equal": na == nb, "nodes_differing": sorted(k for k in set(na) | set(nb) if na.get(k) != nb.get(k))[:20],
        "positions_equal": sa == sb,
        "positions_differing": sorted("/".join(map(str, k)) for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))[:20],
        "bytes_equal": Path(asset_glb).read_bytes() == Path(ballon_glb).read_bytes(),
        "vertices": {"asset": sum(v[0] for v in verts.values()), "ballon": sum(v[1] for v in verts.values()),
                     "meshes_differing": sum(v[0] != v[1] for v in verts.values())},
    }
    result["equal"] = all(result[k] for k in ("meshes_equal", "materials_equal", "empties_equal", "nodes_equal", "positions_equal"))
    return result


def reference_id(sid):
    """BALLON-ID der Grundform eines Blatts (0.6: Pilot BASIC-NN-v2.1, ohne Piloten BASIC-NN)."""
    from formgen import variants
    entry = variants.sheets()[sid]
    version = ballon.pilot_version(ballon.resolve_base(ballon.snapshot(), entry["num"], entry["variant"].get("base", "standard")))
    return f"BASIC-{entry['num']}" + (f"-v{version}" if version else "")


def main_asset(a):
    report = {}
    for sid in a.asset.split(","):
        wid = reference_id(sid)
        glb = a.glb or a.glb_dir / f"{wid}/{wid}.glb"
        report[sid] = {"ballon_glb": str(glb), **compare_asset(a.out_dir / f"assets/{sid}.glb", glb)}
        r = report[sid]
        print(sid, "gleich" if r["equal"] else "UNGLEICH", r["triangles"], "Bytes gleich" if r["bytes_equal"] else
              f"Vertices {r['vertices']['asset']}/{r['vertices']['ballon']}")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    return 0 if all(r["equal"] for r in report.values()) else 1


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--glb-dir", type=Path, default=Path.home() / "Library/Caches/CubeEscapeBallon/out")
    p.add_argument("--out-dir", type=Path, default=ROOT / "out"); p.add_argument("--out", type=Path); p.add_argument("--sheet", type=Path)
    p.add_argument("--asset", help="Blatt-IDs (kommagetrennt): out/assets/<ID>.glb gegen BALLON-GLB (Standard: Grundform der Linie im --glb-dir)")
    p.add_argument("--glb", type=Path, help="BALLON-GLB für --asset statt des Standardpfads")
    p.add_argument("--base", choices=("standard", "v21"), default="standard")
    p.add_argument("--allow-stale", action="store_true", help="auch vergleichen, wenn BALLONs Spec neben dem GLB abweicht (Status nennt die Felder)")
    a = p.parse_args(argv)
    if a.asset:
        return main_asset(a)
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
    raise SystemExit(main())
