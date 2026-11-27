"""Serie DaVinci (0.52 „Atelier“): exklusive Spitzenmodelle der BASIC-Familie mit eigenem Signature-Skin, eigene Serie neben EXTENDED.

Ein DaVinci-Modell ist wie ein EXTENDED-Modell ein eigenes Modul im BALLON-Kit-Vokabular (META, PARTS, ASSEMBLIES, ANCHORS, POINTS,
ACTIONS), liegt aber unter `formgen/models/davinci/` und hat ein eigenes Blattpräfix: D<Linie><NN>, Linie A = Grundform, NN = BALLON-Typ
(DA01 = Automatikgewehr). Jedes Modell bringt seinen Signature-Skin mit (`SKINS`, Farben nur in `skins.toml`).

  load("d01")                → Datensatz (tief kopiert), Snapshot danach wieder aus sys.path/sys.modules
  source("d01")              → Quellhash: eigene Datei + BALLON-Closure der importierten `basic`-Module
  python -m formgen.davinci preview d01 [--out <Ordner>]        Rastervorschau (Clay + Skin), ohne Blender
  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python -m formgen.davinci export d01   GLB, .blend, spec.json im Skin

Export: BALLONs unverändertes `tools/blender_build.main(W=<Datensatz>)` ohne Ansichten (kein Render). Der Wrapper setzt vorher die
Rollenfarben und `finish` (Rauheit/Metall) des Skins in `kit.MATERIALS` und benennt die Materialien danach eindeutig
(`DA01_sfumato_<Rolle>`), speichert .blend und GLB neu. Nur Fehlendes/Veraltetes wird gebaut (Stempel `export.json`), `--force` baut neu.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

from . import ballon, extended

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "formgen/models/davinci"
MODELS = {"d01": "d01_davinci"}          # Kurzname → Modul; IDs ewig (META.id)
SHEETS = {"d01": "DA01"}                  # Blatt-ID (Nutzerentscheid 27.11.2026: eigene Serie), ewig wie BA01/EA01/RA01
SKINS = {"d01": "sfumato"}                # Signature-Skin je Modell (skins.toml)
SHEET_PATTERN = r"D[A-HJ-NP-Z]\d{2}"      # Linienbuchstabe nach der Variantenregel (ohne I/O)
OUT = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.52/davinci"
PREVIEW_VIEWS = ("side_left", "side_right", "front", "back", "top", "iso")


def sheet_id(key: str) -> str:
    return SHEETS[key]


def module_name(key: str) -> str:
    return f"formgen.models.davinci.{MODELS[key]}"


def load(key: str = "d01", snap: Path | None = None) -> dict:
    """Datensatz eines DaVinci-Modells (tief kopiert). Der Snapshot steht nur während des Imports auf sys.path."""
    snap = Path(snap or ballon.snapshot())
    name = module_name(key)
    extended._purge((name,))
    sys.path.insert(0, str(snap))
    try:
        module = importlib.import_module(name)
        data = {k: copy.deepcopy(getattr(module, k)) for k in extended.FIELDS if hasattr(module, k)}
    finally:
        sys.path.remove(str(snap))
        extended._purge((name,))
    return data


def source(key: str = "d01", snap: Path | None = None) -> dict:
    """Quellhash: Modelldatei + statisch importierte `basic`-Module des Snapshots (wie `extended.source`)."""
    return extended.source_of(FOLDER / f"{MODELS[key]}.py", snap)


def skin(name: str, path: Path = ROOT / "skins.toml") -> dict:
    """Rollenfarben und Oberflächen eines Skins: {role: {color, rough, metal}} für alle Rollen (Rolle aus `roles`, Skin darüber)."""
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)
    style = data["skins"][name]
    out = {}
    for role, base in data["roles"].items():
        finish = style.get("finish", {}).get(role, {})
        out[role] = {"color": style.get("roles", {}).get(role, base["color"]), "rough": finish.get("rough", base.get("rough", 0.5)),
                     "metal": finish.get("metal", base.get("metal", 0.0))}
    return out


# ------------------------------------------------------------------ Vorschau (v2-Raster, ohne Blender)

def evaluate(key: str = "d01", snap=None):
    from . import extended_lines, geom, model as mdl
    doc, _ = extended_lines.author(load(key, snap), sheet_id(key))
    return geom.evaluate(mdl.normalize(doc))


def preview(key: str, out: Path, size=(1200, 520), views=PREVIEW_VIEWS, snap=None) -> list[Path]:
    """Rastervorschau je Ansicht in Clay (einfarbig, Form) und im Signature-Skin; gleicher Maßstab für alle Ansichten."""
    from PIL import Image
    from . import raster
    ev = evaluate(key, snap)
    frame = raster.framing(ev, list(views), size[0], size[1])
    palette = raster.palette()
    clay = dict(de="Clay", kind="Farbe", wear=0.0, roles={role: "#B9B6B0" for role in palette["roles"]})
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    original = raster.palette
    raster.palette = lambda: {**palette, "skins": {**palette["skins"], "clay": clay}}
    try:
        for name in ("clay", SKINS[key]):
            for view in views:
                image = raster.render(ev, view, size[0], size[1], skin=name, scale=frame["scale"], center=frame["center"])
                path = out / f"{sheet_id(key)}_{name}_{view}.png"
                image.convert("RGB").save(path)
                paths.append(path)
    finally:
        raster.palette = original
    sheet = Image.new("RGB", (size[0] * 2, size[1] * len(views)), (128, 128, 128))
    for i, path in enumerate(paths):
        sheet.paste(Image.open(path), ((i // len(views)) * size[0], (i % len(views)) * size[1]))
    sheet.save(out / f"{sheet_id(key)}_vorschau.png")
    return paths + [out / f"{sheet_id(key)}_vorschau.png"]


# ------------------------------------------------------------------ Export (Blender headless, ohne Ansichten)

WRAPPER = r'''
import json, os, sys
job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
os.environ['BASIC_OUT'] = job['out']
sys.path.insert(0, job['snapshot'])
from basic import kit
for role, value in job['skin'].items():
    if role in kit.MATERIALS:
        kit.MATERIALS[role] = dict(kit.MATERIALS[role], **value)
import tools.blender_build as BB
from tools.paths import OUT
BB.main(W=job['model'], base=None, argv=[])
import bpy
for m in bpy.data.materials:
    role = m.get('basic_role')
    if role and m.name.startswith('MT_'):
        m.name = f"{job['sid']}_{job['skin_name']}_{role}"
        m['basic_skin'] = job['skin_name']
wid = job['model']['META']['id']
base = os.path.join(OUT, wid, wid)
bpy.ops.wm.save_as_mainfile(filepath=base + '.blend')
bpy.ops.export_scene.gltf(filepath=base + '.glb', export_apply=True, export_extras=True)
'''


def stamp(key: str, data: dict, kit: Path) -> dict:
    """Alles, was die Exportdateien bestimmt."""
    name = SKINS[key]
    return {"key": key, "sid": sheet_id(key), "data_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest(),
            "source_sha256": source(key)["source_sha256"], "kit": Path(kit).name, "skin": name,
            "skin_sha256": hashlib.sha256(json.dumps(skin(name), sort_keys=True).encode()).hexdigest(),
            "wrapper_sha256": hashlib.sha256(WRAPPER.encode()).hexdigest()}


def outputs(key: str, data: dict, target: Path) -> list[Path]:
    wid = data["META"]["id"]
    return [target / f"{wid}.{ext}" for ext in ("glb", "blend", "spec.json")]


def current(target: Path, want: dict, files: list[Path]) -> bool:
    path = target / "export.json"
    return path.exists() and all(f.exists() for f in files) and json.loads(path.read_text()) == want


def export(key: str, out: Path = OUT, force: bool = False) -> Path:
    from . import asset, ballon_kit
    data = load(key)
    kit = ballon_kit.snapshot()
    target = out / sheet_id(key)
    want = stamp(key, data, kit)
    files = outputs(key, data, target)
    if not force and current(target, want, files):
        print(target, "aktuell, kein Export (--force baut neu)", flush=True)
        return target
    target.mkdir(parents=True, exist_ok=True)
    (target / "export.json").unlink(missing_ok=True)   # abgebrochener Lauf hinterlässt keinen gültigen Stempel
    with tempfile.TemporaryDirectory(prefix=f"formgen-davinci-{key}-") as tmp:
        tmp = Path(tmp)
        (tmp / "wrapper.py").write_text(WRAPPER)
        job = {"snapshot": str(kit), "model": data, "out": str(tmp / "o"), "sid": sheet_id(key), "skin_name": SKINS[key],
               "skin": skin(SKINS[key])}
        (tmp / "job.json").write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([asset.settings()["blender"], "-b", "--factory-startup", "-P", str(tmp / "wrapper.py"), "--",
                              str(tmp / "job.json")], capture_output=True, text=True)
        log = run.stdout + run.stderr
        (target / "blender.log").write_text(log)
        if run.returncode or "Traceback" in log:
            raise RuntimeError("\n".join(log.splitlines()[-30:]))
        made = tmp / "o" / data["META"]["id"]
        missing = [f.name for f in files if not (made / f.name).exists()]
        if missing:
            raise RuntimeError(f"Blender lieferte nicht alle Dateien: {missing}")
        for f in files:
            shutil.copyfile(made / f.name, f)
    (target / "export.json").write_text(json.dumps(want, indent=1))
    return target


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("preview", help="Rastervorschau Clay + Skin (ohne Blender)")
    v.add_argument("key", choices=sorted(MODELS)); v.add_argument("--out", type=Path, default=None)
    e = sub.add_parser("export", help="GLB, .blend, spec.json im Signature-Skin (Blender, unter ce lock blender)")
    e.add_argument("key", choices=sorted(MODELS)); e.add_argument("--out", type=Path, default=OUT)
    e.add_argument("--force", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "preview":
        for path in preview(a.key, a.out or OUT / sheet_id(a.key) / "vorschau"):
            print(path)
    else:
        print(export(a.key, a.out, a.force))
    return 0


assert all(re.fullmatch(SHEET_PATTERN, s) for s in SHEETS.values())

if __name__ == "__main__":
    raise SystemExit(main())
