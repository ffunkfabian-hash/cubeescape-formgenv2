"""Waffen-Assets über BALLONs Blender-Baukasten: Pipeline-Stufe `asset` (0.6 „Hangar“; Machbarkeitsnachweis 0.5 „Forge“).

  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.pipeline           # Stufe asset: GLB je Blatt
  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python -m formgen.pipeline --bake BA01,BD01   # + AAA-Bake auf Anforderung
  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.asset BA01 …        # einzeln, ohne übrige Stufen

Weg: Variantenregister → Grundform der Linie (`ballon.resolve_base`, ab 0.6 der neueste Pilot) → `generator.vary` (dieselben
Eingriffe wie für das Blatt, im BALLON-Vokabular) → `kit_model` (BALLONs Datensatz: Baugruppen wie deklariert, r_in-Anpassung
zurückgenommen, Aktionen ohne entfernte Teile) → Blender headless mit BALLONs unverändertem `tools/blender_build.py` aus dem
gepinnten Schnappschuss (`formgen.ballon_kit`). Ergebnis je Blatt-ID `out/assets/<ID>.glb`; Inhalts-Hashes in
`out/assets/index.json`. Der AAA-Bake (FBX, Atlas mit Albedo/Normalen/AO/Spec, Manifest wie BALLONs `export_unity.bake_weapon`,
≈ 4 min GPU je Blatt bei 4096²) läuft nur für angeforderte IDs unter `ce lock gpu` und landet als `out/assets/<ID>.bake.zip`.

Schlüssel (nur Inhalte): Kit-Modell der Variante, Grundmodul und Import-Closure des BALLON-Typmoduls, Closure von BALLONs Bau-/Back-/
Exportcode, eigener Code (diese Datei, ballon_kit.py, blender/asset_build.py, Closure des Generators), Blender-Version; beim Bake
zusätzlich Skin, Atlasgröße, Samples und Gerät. Ohne --force wird nur Fehlendes gebaut; ein zweiter Lauf ist reiner Treffer.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import functools
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import tomllib
import zipfile

from . import ballon, ballon_kit, build, generator, variants
from .cache import Artifact, atomic_write, canonical, file_hash, run_artifacts

ROOT = build.ROOT
FORMAT = 1                     # Cache-/Indexformat der Asset-Artefakte
BAKE = 2                       # Format des Bake-Pakets (ZIP: <ID>.fbx, textures/, <ID>.package.json); 2 = mit Datensatz `model` (0.7)
PACKAGE = "formgenv2/weapon-package"
PACKAGE_VERSIONS = (1, 2)      # lesbar: 1 (0.6, ohne `model`), 2 (0.7, BALLON docs/formgen-schnittstelle.md › 4); geschrieben wird 2
BLENDER_SCRIPT = ROOT / "formgen/blender/asset_build.py"
# atlas/samples: Vorgabe BALLON export_unity (4096², 64); jobs: Annahme – vier Blender-Läufe zugleich (je ≈ 0,5 GB RAM, ≈ 1,2 s)
DEFAULTS = {"blender": "/Applications/Blender.app/Contents/MacOS/Blender", "atlas": 4096, "samples": 64, "jobs": 4}
EVIDENCE = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.7"


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

def kit_model(data: dict, model: dict, run: dict) -> dict:
    """Ergebnis von `generator.vary` als BALLON-Moduldatensatz für `kit.build`/`blender_build.write_spec`.

    `vary` liefert die Teile im BALLON-Vokabular (auch Bausteinteile aus `common.py` mit de/en/func/attach) und passt zwei Dinge
    für v2s eigenes Netz an: Hohlkegel-r_in (zurückgenommen, BALLON baut ihn selbst) und leere Baugruppen (hier wie deklariert).
    Andere Anpassungen (z. B. Material der Akzentgrenze in 0.4) sind Gestaltung der Variante und bleiben. `POINTS` (0.7): Weltpunkte
    der Variante, wie der Generator sie mit den Teilen verschoben hat; BALLON übernimmt sie beim Bauen (`variant.as_module`)."""
    restore = {(a["part"], a["field"]): a["ballon"] for a in run.get("notes", []) if a.get("part") and a.get("field") == "r_in"}
    parts = []
    for q in model["PARTS"]:
        p = copy.deepcopy(q)
        for (part, field), value in restore.items():
            if part == p["id"]:
                p[field] = value
        parts.append(p)
    ids = {p["id"] for p in parts}
    declared = {a["id"] for a in data["ASSEMBLIES"]}
    unknown = sorted({p["asm"] for p in parts} - declared)
    if unknown:
        raise ValueError(f"Baugruppen ohne Deklaration in BALLONs Modul: {unknown}")
    actions = copy.deepcopy(data.get("ACTIONS") or {})
    for action in actions.values():
        if isinstance(action.get("keys"), dict):
            action["keys"] = {k: v for k, v in action["keys"].items() if k in ids}
    return {"META": copy.deepcopy(data["META"]), "PARTS": parts, "ASSEMBLIES": copy.deepcopy(data["ASSEMBLIES"]),
            "ANCHORS": copy.deepcopy(model["ANCHORS"]), "POINTS": copy.deepcopy(model.get("POINTS") or {}), "ACTIONS": actions}


def variant_model(entry: dict, data_snap: Path) -> tuple[dict, dict, str]:
    """Registereintrag {variant, num} → (Kit-Modell, Lauf von `vary`, tatsächliche Grundform)."""
    num, variant = entry["num"], entry["variant"]
    base = ballon.resolve_base(data_snap, num, variant.get("base", "standard"))
    data = ballon.load(data_snap, num, base)
    model, run = generator.vary(data, variant, num, data_snap)
    return kit_model(data, model, run), run, base


def select(ids, entries=None) -> dict:
    """Blatt-IDs → {ID: {variant, num}} aus dem Register."""
    sheets = variants.sheets(entries)
    unknown = [i for i in ids if i not in sheets]
    if unknown:
        raise SystemExit(f"Unbekannte Blatt-ID: {', '.join(unknown)}")
    return {i: sheets[i] for i in ids}


def plan(selection: dict, kit_snap: Path, data_snap: Path, cfg: dict | None = None) -> list[Artifact]:
    """GLB-Artefakte für eine Auswahl {ID: {variant, num}} (wie `pipeline.select`)."""
    cfg = cfg or settings()
    params = {"code": code_hash(), "blender": blender_version(cfg["blender"])}
    backend = ballon_kit.backend_hash(kit_snap)
    artifacts = []
    for sid, entry in selection.items():
        model, run, base = variant_model(entry, data_snap)
        num = entry["num"]
        module = ballon_kit.module_name(kit_snap, ballon.module_file(kit_snap, num, base))
        typ = hashlib.sha256(canonical(ballon.closure(kit_snap, num, base))).hexdigest()
        source = hashlib.sha256(canonical({"model": model, "type": typ, "backend": backend, "module": module})).hexdigest()
        artifacts.append(Artifact(sid, "asset_glb", source, params, {"ASSET": FORMAT}, f"assets/{sid}.glb",
                                  "formgen.asset:build_glb",
                                  {"snapshot": str(kit_snap), "module": module, "model": model, "ops": run["ops"], "base": base,
                                   "skin": entry["variant"]["skin"], "blender": cfg["blender"]}))
    return artifacts


def bake_plan(glb: list[Artifact], cfg: dict | None = None, gpu: bool = True) -> list[Artifact]:
    """AAA-Bake je GLB-Artefakt: gleiche Quelle, dazu Skin, Atlas, Samples, Gerät (GPU und CPU backen nicht bitgleich)."""
    cfg = cfg or settings()
    out = []
    for a in glb:
        params = {**a.params, "skin": a.inputs["skin"], "atlas": cfg["atlas"], "samples": cfg["samples"],
                  "device": "gpu" if gpu else "cpu"}
        out.append(Artifact(a.model_id, "asset_bake", a.source, params, {"ASSET": FORMAT, "BAKE": BAKE},
                            f"assets/{a.model_id}.bake.zip", "formgen.asset:build_bake", {**a.inputs, "gpu": gpu, "glb_key": a.key}))
    return out


def gpu_locked(env=None) -> bool:
    """Läuft dieser Prozess unter `ce lock gpu`? heavy_lock setzt CE_HEAVY_HELD (exklusive GPU-Sperre = "1")."""
    held = set((os.environ if env is None else env).get("CE_HEAVY_HELD", "").split(","))
    return bool({"1", "gpu"} & held)


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


def _bake(artifact: Artifact, work: Path) -> None:
    inputs = artifact.inputs
    run_blender({"snapshot": inputs["snapshot"], "module": inputs["module"], "model": inputs["model"], "id": artifact.model_id,
                 "out": str(work), "package": True, "skin": artifact.params["skin"], "atlas": artifact.params["atlas"],
                 "samples": artifact.params["samples"], "gpu": inputs["gpu"], "package_version": BAKE}, inputs["blender"])
    shutil.rmtree(work / "_ballon_out", ignore_errors=True)


def zip_folder(folder: Path) -> bytes:
    """Deterministische ZIP eines Ordners: sortierte relative Pfade, feste Zeit, feste Rechte, gespeichert (Bilder sind schon
    komprimiert)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        for path in sorted(p for p in Path(folder).rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(path.relative_to(folder).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def build_bake(artifact: Artifact) -> bytes:
    inputs = artifact.inputs
    if blender_version(inputs["blender"]) != artifact.params["blender"]:
        raise RuntimeError("Blender-Version weicht vom Plan ab")
    if inputs["gpu"] and not gpu_locked():
        raise RuntimeError(f"{artifact.model_id}: AAA-Bake auf der GPU nur unter `~/Claude/cubeescape-nexogen/ce lock gpu -- …`")
    with tempfile.TemporaryDirectory(prefix=f"formgen-bake-{artifact.model_id}-") as tmp:
        work = Path(tmp) / artifact.model_id
        work.mkdir()
        _bake(artifact, work)
        return zip_folder(work)


class PackageError(ValueError):
    pass


def read_package(manifest: dict, sid: str | None = None) -> dict:
    """Manifest eines Bake-Pakets prüfen und einheitlich zurückgeben. Lesbar sind Format 1 (0.6, ohne Datensatz: BALLON nimmt es nur
    an, wenn die Teile aller Weltpunkte unverändert sind) und 2 (0.7, `model` = Kit-Modell mit POINTS). Rückgabe: Kopie mit `model`
    (bei 1 None) und `points` (Herkunft der Weltpunkte)."""
    if not isinstance(manifest, dict):
        raise PackageError("Manifest ist kein Objekt")
    if manifest.get("format") != PACKAGE or manifest.get("format_version") not in PACKAGE_VERSIONS:
        raise PackageError(f"Format {manifest.get('format')}/{manifest.get('format_version')} statt {PACKAGE} {PACKAGE_VERSIONS}")
    if sid is not None and manifest.get("id") != sid:
        raise PackageError(f"Manifest-ID {manifest.get('id')} passt nicht zu {sid}")
    if not isinstance(manifest.get("weapon"), dict) or not manifest["weapon"]:
        # BALLONs formgen_import.load lehnt Pakete ohne weapon-Block ab und bricht dann das Einlesen aller Pakete ab
        raise PackageError(f"ohne weapon-Block ({manifest.get('ego_profile_error') or 'kein Ego-Profil'}) – in BALLON nicht spielbar")
    out = copy.deepcopy(manifest)
    if out["format_version"] == 1:
        out["model"], out["points"] = None, "Grundform (Paket 1 ohne Datensatz)"
        return out
    model = out.get("model")
    shapes = {"META": dict, "PARTS": list, "ASSEMBLIES": list, "ANCHORS": dict, "POINTS": dict}
    if not isinstance(model, dict) or not all(isinstance(model.get(k), t) for k, t in shapes.items()):
        raise PackageError("Paket 2 ohne vollständigen Datensatz model (META, PARTS, ASSEMBLIES als Listen, ANCHORS, POINTS)")
    if not model["META"].get("id") or not model["PARTS"] or not model["ASSEMBLIES"] or \
            not all(isinstance(p, dict) and isinstance(p.get("id"), str) and p["id"] for p in model["PARTS"]) or \
            not all(isinstance(a, dict) and isinstance(a.get("id"), str) and a["id"] for a in model["ASSEMBLIES"]):
        raise PackageError("Paket 2: Datensatz model leer (META.id, PARTS und ASSEMBLIES mit id)")
    ids = [p["id"] for p in model["PARTS"]]
    if len(ids) != len(set(ids)):
        raise PackageError(f"Paket 2: Teil-IDs doppelt: {sorted({i for i in ids if ids.count(i) > 1})}")
    unknown = sorted({p.get("asm") for p in model["PARTS"]} - {a["id"] for a in model["ASSEMBLIES"]}, key=str)
    if unknown:
        raise PackageError(f"Paket 2: Teile in undeklarierten Baugruppen {unknown}")
    if "ACTIONS" in model and not isinstance(model["ACTIONS"], dict):
        raise PackageError("Paket 2: ACTIONS ist kein dict")
    for field in ("ANCHORS", "POINTS"):
        bad = sorted(n for n, q in model[field].items() if _located_problem(q, set(ids)))
        if bad:
            raise PackageError(f"Paket 2: {field} ungültig (at = drei endliche Zahlen in mm, part = Teil des Datensatzes): {bad}")
    out["points"] = "Datensatz des Pakets (POINTS)"
    return out


def _located_problem(q, ids: set) -> bool:
    """Anker/Weltpunkt ungültig: kein dict, `part` kein Teil, `at` nicht genau drei endliche Zahlen."""
    if not isinstance(q, dict) or q.get("part") not in ids:
        return True
    at = q.get("at")
    return not (isinstance(at, (list, tuple)) and len(at) == 3 and
                all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in at))


def package_files(manifest: dict) -> list[str]:
    """Dateien, die ein Paket mitbringen muss (wie BALLONs formgen_import.load): FBX, Spec, alle Texturen."""
    T = manifest.get("textures") or {}
    names = {T.get("weapon", {}).get(k) for k in ("albedo", "spec", "normal", "ao")}
    for skin in T.get("skins", []):
        names |= {skin.get("albedo"), skin.get("spec")}
    if None in names or not manifest.get("fbx"):
        raise PackageError("Manifest ohne FBX oder Texturnamen")
    return [manifest["fbx"], f"{manifest['id']}.spec.json"] + [f"textures/{n}" for n in sorted(names)]


def unpack(zip_path: Path, folder: Path) -> Path:
    """Bake-ZIP nach `folder/<ID>` entpacken (z. B. für Unity); ersetzt nur ein eigenes Paket mit `<ID>.package.json`. Das Manifest
    im ZIP muss ein lesbares Paket dieser ID sein (`read_package`), sonst bleibt der Zielordner unberührt."""
    zip_path, folder = Path(zip_path), Path(folder)
    sid = zip_path.name.split(".")[0]
    with zipfile.ZipFile(zip_path) as archive:
        try:
            manifest = json.loads(archive.read(f"{sid}.package.json"))
        except KeyError:
            raise PackageError(f"{zip_path}: ohne {sid}.package.json") from None
        except ValueError:
            raise PackageError(f"{zip_path}: {sid}.package.json ist kein JSON") from None
        if not isinstance(manifest, dict):
            raise PackageError(f"{zip_path}: Manifest ist kein Objekt")
        read_package(manifest, sid)
        missing = sorted(set(package_files(manifest)) - set(archive.namelist()))
        if missing:
            raise PackageError(f"{zip_path}: Dateien fehlen: {missing}")
    target = folder / sid
    if target.exists() and not (target / f"{sid}.package.json").is_file():
        raise RuntimeError(f"{target} ist kein Formgen-Paket (ohne {sid}.package.json) – nicht überschrieben")
    folder.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{sid}-", dir=folder))
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for name in archive.namelist():
                if name.startswith("/") or ".." in Path(name).parts:
                    raise RuntimeError(f"{zip_path}: unsicherer Pfad {name!r}")
            archive.extractall(tmp)
        if target.exists():
            shutil.rmtree(target)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
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


def _matches(path: Path, sha: str | None) -> bool:
    try:
        return path.is_file() and file_hash(path) == sha
    except OSError:
        return False


def reconcile(out: Path, assets: dict) -> dict:
    """Index gegen die Dateien abgleichen: ein Eintrag, dessen GLB fehlt oder andere Bytes hat, entfällt; ein Bake, dessen ZIP
    fehlt, andere Bytes hat oder zu einer anderen GLB gehört, ebenso. So nennt der Index nach einem abgebrochenen Stapel nie eine
    Datei mit falschem Hash (die ersetzten Blätter fehlen dann bis zum nächsten erfolgreichen Lauf)."""
    folder = Path(out) / "assets"
    kept = {}
    for sid, entry in assets.items():
        if not _matches(folder / entry.get("glb", ""), entry.get("sha256")):
            continue
        bake = entry.get("bake")
        if bake and (bake.get("glb_key") != entry.get("key") or not _matches(folder / bake.get("zip", ""), bake.get("sha256"))):
            entry = {k: v for k, v in entry.items() if k != "bake"}
        kept[sid] = entry
    return kept


@contextlib.contextmanager
def reconciled(out: Path):
    """Für Stufen, die Dateien in out/assets ersetzen: bricht der Stapel ab, wird der Index vor dem Weiterreichen abgeglichen."""
    try:
        yield
    except BaseException:
        write_index(out, [], [])
        raise


def write_index(out: Path, artifacts, results) -> Path:
    """Index aller Asset-Artefakte (GLB und Bake) mit Inhalts-Hash und Schlüssel; Einträge anderer Läufe bleiben, sofern ihre
    Dateien noch passen (`reconcile`)."""
    path = Path(out) / "assets" / "index.json"
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        index = {}
    index = {"format": "formgenv2/asset-index", "format_version": 2, "assets": reconcile(out, index.get("assets", {}))}
    for artifact, result in zip(artifacts, results):
        path_out = Path(out) / result.output
        entry = index["assets"].setdefault(artifact.model_id, {})
        if artifact.kind == "asset_glb":
            info = glb_info(path_out)
            entry.update({"glb": path_out.name, "sha256": file_hash(path_out), "key": result.key, "triangles": info["triangles"],
                          "materials": sorted(info["materials"]), "skin": artifact.inputs["skin"], "base": artifact.inputs["base"],
                          "ballon_module": artifact.inputs["module"]})
            bake = entry.get("bake")
            # Bake gilt nur zur GLB dieses Laufs (Schlüssel: Kitmodell, Code, Blender) und zum Skin der Linie; sonst veraltet
            if bake and (bake.get("glb_key") != result.key or bake.get("skin") != artifact.inputs["skin"]):
                entry.pop("bake")
        else:
            entry["bake"] = {"zip": path_out.name, "sha256": file_hash(path_out), "key": result.key,
                             "glb_key": artifact.inputs["glb_key"], **{k: artifact.params[k] for k in ("skin", "atlas", "samples", "device")}}
    index["assets"] = dict(sorted(index["assets"].items()))
    atomic_write(path, json.dumps(index, ensure_ascii=False, indent=1).encode() + b"\n")
    return path


def run(ids, out: Path, cache: Path, bake=(), force=False, jobs=1, gpu=True, log=print, snap=None, kit=None, entries=None):
    """GLB für `ids`, AAA-Bake nur für `bake` (Teilmenge oder weitere IDs); Index danach. Gibt (Artefakte, Ergebnisse) zurück."""
    cfg = settings()
    snap, kit = snap or ballon.snapshot(), kit or ballon_kit.snapshot()
    ids = list(dict.fromkeys([*ids, *bake]))
    glb = plan(select(ids, entries), kit, snap, cfg)
    with reconciled(out):
        results = run_artifacts(glb, out, cache, jobs=jobs, force=force)
    write_index(out, glb, results)                       # sofort: ein später scheiternder Bake lässt keinen alten Index stehen
    artifacts = list(glb)
    if bake:
        baking = bake_plan([a for a in glb if a.model_id in set(bake)], cfg, gpu)
        with reconciled(out):
            res = run_artifacts(baking, out, cache, jobs=1, force=force)   # eine GPU: nacheinander
        artifacts += baking
        results += res
        write_index(out, baking, res)
    return artifacts, results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*", help="Blatt-IDs (BA01 …) für die GLB")
    p.add_argument("--bake", default="", help="Blatt-IDs für den AAA-Bake, kommagetrennt (GPU-Sperre)")
    p.add_argument("--unpack", type=Path, help="Bake-ZIPs der --bake-IDs zusätzlich in diesen Ordner entpacken")
    p.add_argument("--out", type=Path, default=ROOT / "out")
    p.add_argument("--cache", type=Path, default=build.DEFAULT_CACHE)
    p.add_argument("--force", action="store_true")
    p.add_argument("--cpu", action="store_true", help="auf der CPU backen (eigener Cacheschlüssel)")
    a = p.parse_args(argv)
    bake = [b for b in a.bake.split(",") if b]
    if not a.ids and not bake:
        p.error("Blatt-IDs oder --bake angeben")
    artifacts, results = run(a.ids, a.out, a.cache, bake, a.force, gpu=not a.cpu)
    for r in results:
        print(f"{r.output}: {'gebaut' if r.built else 'Cache'} ({r.reason})")
    if a.unpack:
        for artifact in artifacts:
            if artifact.kind == "asset_bake":
                print(unpack(a.out / artifact.output, a.unpack))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
