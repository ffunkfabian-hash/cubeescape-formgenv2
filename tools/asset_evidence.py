"""Beleg 0.3: Varianten im BALLON-Ego-Look neben BALLONs Spielwaffe – BALLONs eigene Ego-Szene (tools/ego_build.py, Arme, AgX,
Hintergrund mittelgrau, ohne Bloom), je Waffe die Haltungen Hüfte und Zielen aus der Ego-Kamera und von außen.

  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python tools/asset_evidence.py BB01 BC01 [--samples 96] [--out <ordner>]

Bezug ist BALLONs unverändertes Modul der Grundform (Formstudie basic/weapons/wNN_*.py, gleich BAnn). Die Varianten laufen mit ihrem Generatormodell und Skin
durch dieselbe Szene (Modul wird nur für den Lauf unter `basic.formgen_<ID>` eingehängt). Ausgabe außerhalb des Repos:
<out>/<ID>/ego/stills/*.png und <out>/ego_contact.png (Kontaktbogen).
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon, ballon_kit, variants  # noqa: E402

WRAPPER = r'''
import importlib, json, os, sys, types
job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
os.environ['BASIC_OUT'] = job['out']
sys.path.insert(0, job['snapshot'])
from basic import kit
name = job['module'].split('basic.', 1)[1]
if job.get('model'):
    base = importlib.import_module(job['module'])
    W = types.ModuleType('basic.formgen_' + job['id'])
    W.__dict__.update({k: v for k, v in vars(base).items() if not k.startswith('__')})
    W.__file__ = base.__file__
    for k, v in job['model'].items():
        setattr(W, k, v)
    sys.modules[W.__name__] = W
    name = W.__name__.split('basic.', 1)[1]
kit.SKIN['name'] = job['skin']
sys.argv = ['ego_build', '--', '--stills', '--poses', 'hip,ads', '--samples', str(job['samples']), '--weapon', name] + \
    (['--gpu'] if job['gpu'] else [])
import tools.ego_build as EB
EB.main()
'''
POSES = (("hip", "ego"), ("hip", "out"), ("ads", "ego"))


def stills(folder: Path) -> Path:
    found = sorted(Path(folder).glob("*/ego/stills"))
    if len(found) != 1:
        raise RuntimeError(f"Genau ein Ego-Ordner erwartet in {folder}, gefunden {len(found)}")
    return found[0]


MARK = ".formgen-evidence"


def render(job: dict, blender: str, work: Path):
    out = Path(job["out"])
    if out.exists():                                        # alte Stände nicht mit in den Bogen nehmen – nur eigene Ordner leeren
        if not (out / MARK).is_file():
            raise RuntimeError(f"{out} ist kein Belegordner dieses Werkzeugs (ohne {MARK}) – nicht gelöscht")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARK).write_text(job["id"] + "\n")
    script = work / "wrapper.py"
    script.write_text(WRAPPER)
    path = work / f"{job['id']}.job.json"
    path.write_text(json.dumps(job, ensure_ascii=False))
    run = subprocess.run([blender, "-b", "--factory-startup", "-P", str(script), "--", str(path)], capture_output=True, text=True)
    log = run.stdout + run.stderr
    if run.returncode or "Traceback" in log:
        raise RuntimeError(f"Ego-Lauf {job['id']} fehlgeschlagen:\n" + "\n".join(log.splitlines()[-25:]))


def contact(rows, path: Path, width=560):
    tiles = [[Image.open(stills(folder) / f"{p}_{c}.png").convert("RGB") for p, c in POSES] for _, folder in rows]
    h = round(width * tiles[0][0].height / tiles[0][0].width)
    sheet = Image.new("RGB", (190 + len(POSES) * (width + 10), 34 + len(rows) * (h + 10)), "#808080")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)   # Umlaute; Standardschrift kann nur ASCII
    except OSError:
        font = ImageFont.load_default()
    for j, (p, c) in enumerate(POSES):
        d.text((190 + j * (width + 10), 10), f"{p} · {c}", fill="#111111", font=font)
    for i, ((label, _), row) in enumerate(zip(rows, tiles)):
        y = 34 + i * (h + 10)
        d.multiline_text((10, y + h // 2 - 24), label, fill="#111111", font=font)
        for j, im in enumerate(row):
            sheet.paste(im.resize((width, h), Image.LANCZOS), (190 + j * (width + 10), y))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="+")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--out", type=Path, default=Path.home() / "Library/Caches/CubeEscapeFormgen2/0.5/belege")
    p.add_argument("--sheet-only", action="store_true", help="nur den Kontaktbogen aus vorhandenen Bildern neu setzen")
    a = p.parse_args(argv)
    cfg = asset.settings()
    snap = ballon_kit.snapshot()
    sheets = variants.sheets()
    selection = {i: sheets[i] for i in a.ids}
    plans = {x.model_id: x for x in asset.plan(a.ids, snap, ballon.snapshot(), cfg)}
    nums = sorted({e["num"] for e in selection.values()})
    rows = []
    if a.sheet_only:
        render_job = lambda job, blender, work: None   # noqa: E731
    else:
        render_job = render
    with tempfile.TemporaryDirectory(prefix="formgen-evidence-") as tmp:
        for num in nums:
            module = ballon_kit.module_name(snap, ballon.module_file(snap, num))
            out = a.out / f"BALLON-{num}"
            render_job(dict(id=f"BALLON-{num}", snapshot=str(snap), module=module, model=None, skin="standard", samples=a.samples,
                        gpu=not a.cpu, out=str(out)), cfg["blender"], Path(tmp))
            rows.append((f"BALLON BASIC-{num}\n{module.rsplit('.', 1)[1]}\n(unverändert)", out))
            for sid, e in selection.items():
                if e["num"] != num:
                    continue
                x = plans[sid]
                out = a.out / sid
                render_job(dict(id=sid, snapshot=str(snap), module=x.inputs["module"], model=x.inputs["model"], skin=x.inputs["skin"],
                            samples=a.samples, gpu=not a.cpu, out=str(out)), cfg["blender"], Path(tmp))
                rows.append((f"{sid} {e['variant']['name']}\nSkin {e['variant']['skin']}\nFormgen v2 0.3", out))
    sheet = a.out / "ego_contact.png"
    contact(rows, sheet)
    print(sheet)


if __name__ == "__main__":
    main()
