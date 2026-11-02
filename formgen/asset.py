"""Waffen-Assets über BALLONs Blender-Baukasten (0.3 „Forge“, Machbarkeitsnachweis; noch keine Pipeline-Stufe).

  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.asset BA01 BB01 BC01
  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python -m formgen.asset BA01 --package <ordner>   # + FBX, AAA-Atlas

Weg: Variantenregister → `generator.generate` (nur aufgerufen, BALLON-Vokabular) → `kit_model` (zurück auf BALLONs Datensatz:
Metadaten der Teile, Baugruppen, Aktionen; v2-eigene Anpassungen zurückgenommen) → Blender headless mit BALLONs unverändertem
`tools/blender_build.py` aus dem gepinnten Schnappschuss (`formgen.ballon_kit`). Ergebnis je Blatt-ID unter festem Pfad
`out/assets/<ID>.glb` (Cacheeintrag, Inhalts-Hash in `out/assets/index.json` für einen späteren Viewer).

Schlüssel (nur Inhalte): Kit-Modell der Variante, Import-Closure des BALLON-Typmoduls, Closure von BALLONs Bau-/Back-/Exportcode,
eigener Code (diese Datei, ballon_kit.py, blender/asset_build.py, Closure des Generators), Blender-Version. Ohne --force wird nur
Fehlendes gebaut; ein zweiter Lauf ist reiner Treffer.
"""
from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import tomllib

from . import ballon, ballon_kit, build, generator, variants
from .cache import Artifact, atomic_write, canonical, file_hash, run_artifacts

ROOT = build.ROOT
FORMAT = 1                     # Cache-/Indexformat der Asset-Artefakte (eigene Konstante, versions.py gehört der Pipeline)
BLENDER_SCRIPT = ROOT / "formgen/blender/asset_build.py"
DEFAULTS = {"blender": "/Applications/Blender.app/Contents/MacOS/Blender", "atlas": 4096, "samples": 64}
EVIDENCE = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.3"


def settings(path: Path = ROOT / "config.toml") -> dict:
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream).get("asset", {})
    cfg = {**DEFAULTS, **data}
    cfg["blender"] = os.environ.get("BLENDER", cfg["blender"])
    return cfg


@functools.lru_cache(maxsize=None)
def blender_version(binary: str) -> str:
    out = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()[0].strip()


@functools.lru_cache(maxsize=None)
def code_hash() -> str:
    files = {rel: file_hash(ROOT / rel) for rel in ("formgen/asset.py", "formgen/ballon_kit.py", "formgen/blender/asset_build.py")}
    files.update({str(Path(k).relative_to(ROOT)): v for k, v in build.source_hashes(ROOT / "formgen/generator.py").items()})
    return hashlib.sha256(canonical(files)).hexdigest()


# ------------------------------------------------------------------ Generator → BALLON-Datensatz

def kit_model(data: dict, author: dict, report: dict) -> dict:
    """Generator-Ergebnis zurück in BALLONs Modulvokabular für `kit.build`/`blender_build.write_spec`.

    `generate` lässt Teile-Metadaten weg (en, func, attach, iface → name_en) und passt zwei Dinge für v2s eigenes Netz an
    (Hohlkegel-r_in, leere Baugruppen). Für BALLONs Baukasten gilt BALLONs Datensatz: Metadaten je Teile-ID aus BALLON,
    r_in auf BALLONs Wert, alle Baugruppen wie deklariert, ACTIONS ohne Schlüssel entfernter Teile."""
    original = {p["id"]: p for p in data["PARTS"]}
    # nur die Netzanpassung r_in zurücknehmen; andere Anpassungen (z. B. Material der Akzentgrenze in 0.4) sind Gestaltung der Variante
    restore = {(a["part"], a["field"]): a["ballon"] for a in report.get("adaptations", [])
               if a.get("part") and a.get("field") == "r_in"}
    parts = []
    for q in author["PARTS"]:
        p = {k: copy.deepcopy(v) for k, v in q.items() if k != "name_en"}
        for key in ("en", "func", "attach", "iface"):
            if key in original[p["id"]]:
                p[key] = copy.deepcopy(original[p["id"]][key])
        for (part, field), value in restore.items():
            if part == p["id"]:
                p[field] = value
        parts.append(p)
    ids = {p["id"] for p in parts}
    actions = copy.deepcopy(data.get("ACTIONS") or {})
    for action in actions.values():
        if isinstance(action.get("keys"), dict):
            action["keys"] = {k: v for k, v in action["keys"].items() if k in ids}
    return {"META": copy.deepcopy(data["META"]), "PARTS": parts, "ASSEMBLIES": copy.deepcopy(data["ASSEMBLIES"]),
            "ANCHORS": copy.deepcopy(author["ANCHORS"]), "ACTIONS": actions}


def plan(ids, kit_snap: Path, data_snap: Path, cfg: dict | None = None) -> list[Artifact]:
    cfg = cfg or settings()
    sheets = variants.sheets()
    unknown = [i for i in ids if i not in sheets]
    if unknown:
        raise SystemExit(f"Unbekannte Blatt-ID: {', '.join(unknown)}")
    params = {"code": code_hash(), "blender": blender_version(cfg["blender"])}
    backend = ballon_kit.backend_hash(kit_snap)
    artifacts = []
    for sid in ids:
        entry = sheets[sid]
        num, variant = entry["num"], entry["variant"]
        data, src = ballon.load(data_snap, num), ballon.source(data_snap, num)
        author, report = generator.generate(data, variant, num, src)
        model = kit_model(data, author, report)
        module = ballon_kit.module_name(kit_snap, ballon.module_file(kit_snap, num))
        typ = hashlib.sha256(canonical(ballon.closure(kit_snap, num))).hexdigest()
        source = hashlib.sha256(canonical({"model": model, "type": typ, "backend": backend, "module": module})).hexdigest()
        artifacts.append(Artifact(sid, "asset_glb", source, params, {"ASSET": FORMAT}, f"assets/{sid}.glb",
                                  "formgen.asset:build_glb",
                                  {"snapshot": str(kit_snap), "module": module, "model": model, "ops": report["ops"],
                                   "skin": variant["skin"], "blender": cfg["blender"]}))
    return artifacts


def run_blender(job: dict, blender: str) -> str:
    with tempfile.TemporaryDirectory(prefix=f"formgen-asset-{job['id']}-") as tmp:
        path = Path(tmp) / "job.json"
        path.write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([blender, "-b", "--factory-startup", "-P", str(BLENDER_SCRIPT), "--", str(path)],
                             capture_output=True, text=True)
    log = run.stdout + run.stderr
    if run.returncode or "Traceback" in log or f"[formgen-asset] {job['id']}:" not in log:
        raise RuntimeError(f"Blender-Lauf für {job['id']} fehlgeschlagen:\n" + "\n".join(log.splitlines()[-25:]))
    return log


def build_glb(artifact: Artifact) -> bytes:
    inputs = artifact.inputs
    if blender_version(inputs["blender"]) != artifact.params["blender"]:
        raise RuntimeError("Blender-Version weicht vom Plan ab")
    with tempfile.TemporaryDirectory(prefix=f"formgen-glb-{artifact.model_id}-") as out:
        run_blender({"snapshot": inputs["snapshot"], "module": inputs["module"], "model": inputs["model"],
                     "id": artifact.model_id, "out": out}, inputs["blender"])
        return (Path(out) / f"{artifact.model_id}.glb").read_bytes()


def build_package(artifact: Artifact, folder: Path, cfg: dict, gpu: bool = True) -> Path:
    """Spielpaket (FBX, AAA-Atlas, Manifest) wie BALLONs Unity-Export – nur als Machbarkeitsnachweis, nicht im Cache.

    Gebaut wird in einem temporären Ordner neben dem Ziel; ein vorhandenes Ziel wird nur ersetzt, wenn es ein eigenes Paket ist
    (enthält `<ID>.package.json`), und erst nach erfolgreichem Bau."""
    folder = Path(folder)
    target = folder / artifact.model_id
    if target.exists() and not (target / f"{artifact.model_id}.package.json").is_file():
        raise RuntimeError(f"{target} ist kein Formgen-Paket (ohne {artifact.model_id}.package.json) – nicht überschrieben")
    folder.mkdir(parents=True, exist_ok=True)
    inputs = artifact.inputs
    with tempfile.TemporaryDirectory(prefix=f".{artifact.model_id}-", dir=folder) as tmp:
        work = Path(tmp) / artifact.model_id
        work.mkdir()
        run_blender({"snapshot": inputs["snapshot"], "module": inputs["module"], "model": inputs["model"],
                     "id": artifact.model_id, "out": str(work), "package": True, "skin": inputs["skin"],
                     "atlas": cfg["atlas"], "samples": cfg["samples"], "gpu": gpu}, inputs["blender"])
        shutil.rmtree(work / "_ballon_out", ignore_errors=True)
        if target.exists():
            shutil.rmtree(target)
        os.replace(work, target)
    return target


# ------------------------------------------------------------------ GLB lesen (Index, Abgleich)

def glb_json(path: Path) -> dict:
    data = Path(path).read_bytes()
    if data[:4] != b"glTF":
        raise ValueError(f"{path}: kein GLB")
    n = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + n])


def glb_info(path: Path) -> dict:
    """Mesh-Knoten mit Dreiecken und Materialnamen je Primitiv, Materialien mit PBR-Werten (ohne Bilddaten)."""
    g = glb_json(path)
    meshes = {}
    for node in g.get("nodes", []):
        if "mesh" not in node:
            continue
        prims = []
        for prim in g["meshes"][node["mesh"]]["primitives"]:
            count = g["accessors"][prim["indices"]]["count"] if "indices" in prim else \
                g["accessors"][prim["attributes"]["POSITION"]]["count"]
            prims.append({"triangles": count // 3, "vertices": g["accessors"][prim["attributes"]["POSITION"]]["count"],
                          "material": g["materials"][prim["material"]]["name"] if "material" in prim else None})
        meshes[node["name"]] = prims
    materials = {m["name"]: {k: v for k, v in m.items() if k != "name"} for m in g.get("materials", [])}
    empties = sorted(n["name"] for n in g.get("nodes", []) if "mesh" not in n)
    return {"meshes": meshes, "materials": materials, "empties": empties,
            "triangles": sum(p["triangles"] for prims in meshes.values() for p in prims)}


def write_index(out: Path, artifacts, results) -> Path:
    path = Path(out) / "assets" / "index.json"
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        index = {}
    index = {"format": "formgenv2/asset-index", "format_version": 1, "assets": index.get("assets", {})}
    for artifact, result in zip(artifacts, results):
        glb = Path(out) / result.output
        info = glb_info(glb)
        index["assets"][artifact.model_id] = {"glb": f"{artifact.model_id}.glb", "sha256": file_hash(glb), "key": result.key,
                                              "triangles": info["triangles"], "materials": sorted(info["materials"]),
                                              "skin": artifact.inputs["skin"], "ballon_module": artifact.inputs["module"]}
    index["assets"] = dict(sorted(index["assets"].items()))
    atomic_write(path, json.dumps(index, ensure_ascii=False, indent=1).encode() + b"\n")
    return path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="+", help="Blatt-IDs (BA01 …)")
    p.add_argument("--out", type=Path, default=ROOT / "out")
    p.add_argument("--cache", type=Path, default=build.DEFAULT_CACHE)
    p.add_argument("--force", action="store_true")
    p.add_argument("--package", type=Path, help="zusätzlich Spielpaket (FBX, Atlas) in diesen Ordner backen (GPU-Sperre)")
    p.add_argument("--cpu", action="store_true", help="Paket auf der CPU backen")
    a = p.parse_args(argv)
    cfg = settings()
    artifacts = plan(a.ids, ballon_kit.snapshot(), ballon.snapshot(), cfg)
    results = run_artifacts(artifacts, a.out, a.cache, force=a.force)
    for r in results:
        print(f"{r.output}: {'gebaut' if r.built else 'Cache'} ({r.reason})")
    print(write_index(a.out, artifacts, results))
    if a.package:
        for artifact in artifacts:
            print(build_package(artifact, a.package, cfg, gpu=not a.cpu))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
