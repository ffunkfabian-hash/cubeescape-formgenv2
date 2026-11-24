"""EXTENDED-Modelle (0.15 „Spearhead“): eigenständige Waffen der BASIC-Familie, gebaut im BALLON-Kit-Vokabular.

Ein EXTENDED-Modell ist kein Generatorlauf über einer BASIC-Grundform, sondern ein eigenes Modul unter `formgen/models/extended/` mit
denselben Datenfeldern wie ein BALLON-Pilot (META, PARTS, ASSEMBLIES, ANCHORS, POINTS, ACTIONS). Es importiert nur Familienbausteine aus
`basic.common` (genormte Schnittstellen: Griff BGM-1, Visier, Schrauben) des gepinnten Snapshots; die Geometrie ist eigene Arbeit.

  load("e01")          → Datensatz (tief kopiert), Snapshot danach wieder aus sys.path/sys.modules
  source("e01")        → Quellhash: eigene Datei + BALLON-Closure der importierten `basic`-Module
  side_mask(parts)     → Seitensilhouette (f, u) als Bool-Raster, 1 mm je Pixel, Ursprung Socket_Hand
  side_iou(a, b)       → IoU zweier Teillisten in der Seitenansicht (gemeinsamer Ursprung, kein Fit)

Die Silhouette ist eine Näherung für Vielfaltsprüfungen: Extrusionen und Zylinder als Flächen, Durchbrüche nur, wenn der Schneidkörper
das Teil quer ganz durchdringt (Daumenloch, Fenster), Schrift ignoriert. Rendern: `tools/extended_render.py` (BALLONs unverändertes
`tools/blender_build.main`).
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

from . import ballon
from .cache import canonical

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "formgen/models/extended"
MODELS = {"e01": "e01_spearhead"}          # Kurzname → Modul; IDs ewig (META.id)
MODELS.update({"e02": "e02_cadence", "e03": "e03_meridian"})   # 0.17 „Outrider“: Impuls- und Spähergewehr
MODELS.update(e04="e04_sledge", e05="e05_duplex")   # 0.18 „Holster“: Handkanone, Seitenwaffe
# Blatt-ID je Kurzname (Nutzerentscheid 23.11.2026): E<Linie><NN>, Linie A = Grundform, NN = EXTENDED-Nummer; ewig wie BA01/RA01.
# Vergeben ist nur die ID; ein Blattweg (formgen.pipeline) und die Website-Aufnahme folgen in einer eigenen Version.
SHEETS = {"e01": "EA01"}
SHEETS.update({"e02": "EA02", "e03": "EA03"})                  # 0.17 „Outrider“
SHEETS.update(e04="EA04", e05="EA05")      # 0.18 „Holster“
MODELS.update(e10="e10_bellmouth", e11="e11_collimator")   # 0.19 „Crucible“: Fusion und lineare Fusion
SHEETS.update(e10="EA10", e11="EA11")                     # 0.19 „Crucible“
SHEET_PATTERN = r"E[A-HJ-NP-Z]\d{2}"      # Linienbuchstabe nach der Variantenregel (ohne I/O)
MODELS["e16"], SHEETS["e16"] = "e16_sweepguard", "EA16"   # 0.20 Riftguard: Schwert (Nahkampf)
MODELS["e17"], SHEETS["e17"] = "e17_gorget", "EA17"       # 0.20 Riftguard: Glefe (Nahkampf)


def sheet_id(key: str) -> str:
    return SHEETS[key]
FIELDS = ("META", "PARTS", "ASSEMBLIES", "ANCHORS", "POINTS", "ACTIONS", "EJECT", "EGO_GRIPS", "EXPLODE", "HERO")
MM_PX = 1.0


def module_name(key: str) -> str:
    return f"formgen.models.extended.{MODELS[key]}"


def _purge(extra=()):
    for name in [n for n in sys.modules if n == "basic" or n.startswith("basic.") or n in extra]:
        del sys.modules[name]


def load(key: str = "e01", snap: Path | None = None) -> dict:
    """Datensatz eines EXTENDED-Modells (tief kopiert). Der Snapshot steht nur während des Imports auf sys.path."""
    snap = Path(snap or ballon.snapshot())
    name = module_name(key)
    _purge((name,))
    sys.path.insert(0, str(snap))
    try:
        module = importlib.import_module(name)
        data = {k: copy.deepcopy(getattr(module, k)) for k in FIELDS if hasattr(module, k)}
    finally:
        sys.path.remove(str(snap))
        _purge((name,))
    return data


def load_basic(num: str = "01", snap: Path | None = None) -> dict:
    """BASIC-Pilot zum Vergleich (neueste Pilotfassung)."""
    snap = Path(snap or ballon.snapshot())
    return ballon.load(snap, num, ballon.resolve_base(snap, num, "pilot"))


def source(key: str = "e01", snap: Path | None = None) -> dict:
    """Quellhash: Modelldatei + statisch importierte `basic`-Module des Snapshots (Inhalt, keine Pfade)."""
    snap = Path(snap or ballon.snapshot())
    path = FOLDER / f"{MODELS[key]}.py"
    files = {f"formgen/models/extended/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()}
    todo = [path]
    seen = set()
    while todo:
        p = todo.pop()
        for node in ast.walk(ast.parse(p.read_bytes())):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]   # `from basic import reticles`
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            for n in names:
                if n.split(".")[0] != "basic" or n in seen:
                    continue
                seen.add(n)
                parts = n.split(".")
                cands = [snap.joinpath(*parts).with_suffix(".py")]
                cands += [snap.joinpath(*parts[:i], "__init__.py") for i in range(1, len(parts) + 1)]   # Paket-Init läuft mit
                for cand in cands:
                    rel = cand.relative_to(snap).as_posix() if cand.is_file() else None
                    if rel and rel not in files:
                        files[rel] = hashlib.sha256(cand.read_bytes()).hexdigest()
                        todo.append(cand)
    files = dict(sorted(files.items()))
    return {"files": files, "source_sha256": hashlib.sha256(canonical(files)).hexdigest()}


# ------------------------------------------------------------------ Seitensilhouette

def _side_polys(p) -> list[list[tuple[float, float]]]:
    """Seitenprojektion einer Form als Polygone (f, u)."""
    k = p.get("shape", "box")
    if k == "multi":
        return [q for i in p["items"] for q in _side_polys(i)]
    if k == "prof":
        return [list(map(tuple, p["pts"]))]
    if k == "box":
        return [[(p["f0"], p["u0"]), (p["f1"], p["u0"]), (p["f1"], p["u1"]), (p["f0"], p["u1"])]]
    if k == "cyl":
        a0, a1, r, r1 = p["a0"], p["a1"], p["r"], p.get("r1", p["r"])
        if p["axis"] == "f":
            u = p["c"][0]
            return [[(a0, u - r), (a1, u - r1), (a1, u + r1), (a0, u + r)]]
        if p["axis"] == "x":
            f, u = p["c"]
            n = max(8, p.get("segs", 24))
            return [[(f + r * np.cos(2 * np.pi * i / n), u + r * np.sin(2 * np.pi * i / n)) for i in range(n)]]
        f = p["c"][0]
        rr = max(r, r1)
        return [[(f - rr, a0), (f + rr, a0), (f + rr, a1), (f - rr, a1)]]
    if k == "plan":
        fs = [q[0] for q in p["pts"]]
        return [[(min(fs), p["u0"]), (max(fs), p["u0"]), (max(fs), p["u1"]), (min(fs), p["u1"])]]
    if k == "xprof":
        us = [q[1] + p["cu"] for q in p["pts"]]
        return [[(p["f0"], min(us)), (p["f1"], min(us)), (p["f1"], max(us)), (p["f0"], max(us))]]
    if k in ("xbox", "frame"):
        h = p.get("hh", p.get("oh"))
        return [[(p["f0"], p["cu"] - h / 2), (p["f1"], p["cu"] - h / 2), (p["f1"], p["cu"] + h / 2), (p["f0"], p["cu"] + h / 2)]]
    if k == "tube":
        pts = p["path"]
        r = p["r"]
        out = []
        for (f0, u0, _), (f1, u1, _) in zip(pts, pts[1:]):
            d = np.array([f1 - f0, u1 - u0], float)
            n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) or 1) * r
            out.append([(f0 + n[0], u0 + n[1]), (f1 + n[0], u1 + n[1]), (f1 - n[0], u1 - n[1]), (f0 - n[0], u0 - n[1])])
        return out
    return []   # text


def _width(p):
    k = p.get("shape")
    if k in ("prof", "box"):
        return p.get("x", 0.0), p["w"]
    return None


def _through(p, c) -> bool:
    """Schneidkörper durchdringt das Teil quer vollständig (nur prof/box gegen prof/box)."""
    a, b = _width(p), _width(c) if c.get("shape", "box") in ("prof", "box") else None
    if not a or not b:
        return False
    return abs(b[0] - a[0]) + a[1] / 2 <= b[1] / 2 + 1e-6


def side_mask(parts, lo=(-420.0, -200.0), size=(1200, 520)) -> np.ndarray:
    """Bool-Raster der Seitensilhouette; Pixel (i, j) = (u, f) ab lo, 1 mm je Pixel. Durchbrüche wirken nur im eigenen Teil."""
    total = np.zeros(size[::-1], bool)

    def px(pts):
        return [((f - lo[0]) / MM_PX, size[1] - 1 - (u - lo[1]) / MM_PX) for f, u in pts]
    for p in parts:
        im = Image.new("1", size, 0)
        d = ImageDraw.Draw(im)
        for poly in _side_polys(p):
            if len(poly) >= 3:
                d.polygon(px(poly), fill=1)
        for c in p.get("cuts") or ():
            if _through(p, c):
                for poly in _side_polys(c):
                    d.polygon(px(poly), fill=0)
        total |= np.asarray(im, bool)
    if total[0].any() or total[-1].any() or total[:, 0].any() or total[:, -1].any():
        raise ValueError(f"Seitensilhouette am Rasterrand beschnitten (Rahmen ab {lo}, {size} mm)")
    return total


def side_iou(a, b, **frame) -> float:
    """frame: lo/size wie side_mask (0.19: Langwaffen über f 780, z. B. EXTENDED-11, brauchen einen längeren Rahmen)."""
    ma, mb = side_mask(a, **frame), side_mask(b, **frame)
    return round(float((ma & mb).sum() / (ma | mb).sum()), 4)


# ------------------------------------------------------------------ Hüllquader und Zusammenhang (keine schwebenden Teile)

def bounds(p):
    """Achsparalleler Hüllquader einer Form ((f0, u0, x0), (f1, u1, x1)) in mm; None für Schrift."""
    k = p.get("shape", "box")
    if k == "multi":
        bs = [b for b in (bounds(i) for i in p["items"]) if b]
        return (tuple(min(b[0][i] for b in bs) for i in range(3)), tuple(max(b[1][i] for b in bs) for i in range(3)))
    x = p.get("x", p.get("cx", 0.0))
    if k == "prof":
        fs, us = [q[0] for q in p["pts"]], [q[1] for q in p["pts"]]
        return (min(fs), min(us), x - p["w"] / 2), (max(fs), max(us), x + p["w"] / 2)
    if k == "box":
        return (p["f0"], p["u0"], x - p["w"] / 2), (p["f1"], p["u1"], x + p["w"] / 2)
    if k == "cyl":
        r = max(p["r"], p.get("r1", p["r"]))
        a0, a1 = sorted((p["a0"], p["a1"]))
        c0, c1 = p["c"]
        if p["axis"] == "f":
            return (a0, c0 - r, c1 - r), (a1, c0 + r, c1 + r)
        if p["axis"] == "x":
            return (c0 - r, c1 - r, a0), (c0 + r, c1 + r, a1)
        return (c0 - r, a0, c1 - r), (c0 + r, a1, c1 + r)
    if k == "plan":
        fs, xs = [q[0] for q in p["pts"]], [q[1] for q in p["pts"]]
        return (min(fs), p["u0"], min(xs)), (max(fs), p["u1"], max(xs))
    if k == "xprof":
        xs, us = [q[0] + x for q in p["pts"]], [q[1] + p["cu"] for q in p["pts"]]
        return (p["f0"], min(us), min(xs)), (p["f1"], max(us), max(xs))
    if k in ("xbox", "frame"):
        w, h = p.get("ww", p.get("ow")), p.get("hh", p.get("oh"))
        return (p["f0"], p["cu"] - h / 2, x - w / 2), (p["f1"], p["cu"] + h / 2, x + w / 2)
    if k == "tube":
        pts, r = p["path"], p["r"]
        return (tuple(min(q[i] for q in pts) - r for i in range(3)), tuple(max(q[i] for q in pts) + r for i in range(3)))
    return None


def components(parts, tol=0.5) -> list[list[str]]:
    """Gruppen sich berührender Teile (Hüllquader überlappen bis auf tol mm); ein Modell ohne schwebende Teile hat genau eine."""
    boxes = {p["id"]: bounds(p) for p in parts if bounds(p)}
    ids = list(boxes)
    parent = {i: i for i in ids}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            (lo1, hi1), (lo2, hi2) = boxes[a], boxes[b]
            if all(lo1[k] <= hi2[k] + tol and lo2[k] <= hi1[k] + tol for k in range(3)):
                parent[find(a)] = find(b)
    groups = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)
MODELS["e06"], SHEETS["e06"] = "e06_wishbone", "EA06"     # 0.22 Torrent: Maschinenpistole (Dauerfeuer)
MODELS["e15"], SHEETS["e15"] = "e15_flywheel", "EA15"     # 0.22 Torrent: Maschinengewehr (Dauerfeuer)
