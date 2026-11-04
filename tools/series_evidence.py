"""Beleg 0.8: Design-Serien im AAA-Look (BALLONs Cycles-Materialien, Hintergrund mittelgrau, ohne Bloom) als Kontaktbogen je Serie und
Vergleich A gegen die neuen Serien.

  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python tools/series_evidence.py BJ01 BK01 … [--samples 32] [--res 960] [--out <ordner>]
  .venv/bin/python tools/series_evidence.py --sheets                    # Bögen aus vorhandenen Bildern neu setzen (ohne Rendern)

Rendert je Blatt mit BALLONs unverändertem `tools/blender_build.main(W=…, base=…, argv=['--views', '--aaa', '--skins', …])` die Hauptansicht und die
linke Seite. Skins der Serien hängt der Lauf nur für sich in `kit.SKINS` ein (wie `formgen/blender/asset_build.py`). Ausgabe außerhalb des Repos:
<out>/aaa/<ID>_{hero,side}.png, <out>/kontaktbogen_<Linie>.png, <out>/vergleich_BASIC-01.png.
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
import glob, importlib, json, os, shutil, sys
job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
os.environ['BASIC_OUT'] = job['out']
sys.path.insert(0, job['snapshot'])
from basic import kit
import tools.blender_build as BB
base = importlib.import_module(job['module'])
if job.get('skin_def'):
    kit.SKINS[job['skin']] = job['skin_def']
argv = ['--views', '--aaa', '--skins', job['skin'], '--only', 'none', '--samples', str(job['samples']), '--res', str(job['res']), '--bg', 'mid']
BB.main(W=job['model'], base=base, argv=argv + (['--gpu'] if job['gpu'] else []))
'''
SERIES = "JKLM"


def font(size):
    path = ROOT / "formgen/assets/fonts/Barlow-SemiBold.ttf"
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def render(sid, entry, kit, snap, cfg, a):
    model, _, base = asset.variant_model(entry, snap)
    module = ballon_kit.module_name(kit, ballon.module_file(kit, entry["num"], base))
    skin = entry["variant"]["skin"]
    with tempfile.TemporaryDirectory(prefix=f"formgen-series-{sid}-") as tmp:
        tmp = Path(tmp)
        (tmp / "wrapper.py").write_text(WRAPPER)
        job = {"snapshot": str(kit), "module": module, "model": model, "skin": skin, "skin_def": asset.skin_def(skin), "out": str(tmp / "o"),
               "samples": a.samples, "res": a.res, "gpu": not a.cpu}
        (tmp / "job.json").write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([cfg["blender"], "-b", "--factory-startup", "-P", str(tmp / "wrapper.py"), "--", str(tmp / "job.json")], capture_output=True, text=True)
        log = run.stdout + run.stderr
        if run.returncode or "Traceback" in log:
            raise RuntimeError(f"{sid}: " + "\n".join(log.splitlines()[-20:]))
        found = {p.name: p for p in (tmp / "o").rglob("skin_*.png")}
        (a.out / "aaa").mkdir(parents=True, exist_ok=True)
        for name, path in found.items():
            kind = "side" if "left" in name or "side" in name or "seite" in name.lower() else "hero"
            shutil.copyfile(path, a.out / "aaa" / f"{sid}_{kind}.png")
    print(sid, sorted(found), flush=True)


def bogen(letter, name, out, columns=5, width=460):
    entries = {v["letter"]: v for v in variants.load()}
    v = entries[letter]
    h = round(width * 9 / 16)
    rows = (len(variants.TYPES) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * (width + 8) + 8, 64 + rows * (h + 30)), "#808080")
    d = ImageDraw.Draw(sheet)
    d.text((12, 14), f"{letter} · {v['name']} ({v['skin']})  {v['idea']}", fill="#111317", font=font(22))
    for i, num in enumerate(variants.TYPES):
        x, y = 8 + (i % columns) * (width + 8), 64 + (i // columns) * (h + 30)
        path = out / "aaa" / f"{variants.sheet_id(letter, num)}_hero.png"
        if path.exists():
            sheet.paste(Image.open(path).convert("RGB").resize((width, h), Image.LANCZOS), (x, y))
        d.text((x + 4, y + h + 3), f"{variants.sheet_id(letter, num)} · BASIC-{num}", fill="#111317", font=font(17))
    sheet.save(out / name)
    return sheet.size


def compare(out, num="01", width=800):
    entries = variants.load()
    letters = ["A", *SERIES]
    h = round(width * 9 / 16)
    sheet = Image.new("RGB", (2 * width + 24, 16 + len(letters) * (h + 34)), "#808080")
    d = ImageDraw.Draw(sheet)
    for i, letter in enumerate(letters):
        v = next(e for e in entries if e["letter"] == letter)
        y = 8 + i * (h + 34)
        d.text((12, y + 4), f"{variants.sheet_id(letter, num)} · {v['name']} ({v['skin']})", fill="#111317", font=font(22))
        for j, kind in enumerate(("hero", "side")):
            path = out / "aaa" / f"{variants.sheet_id(letter, num)}_{kind}.png"
            if path.exists():
                sheet.paste(Image.open(path).convert("RGB").resize((width, h), Image.LANCZOS), (8 + j * (width + 8), y + 30))
    sheet.save(out / f"vergleich_BASIC-{num}.png")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("ids", nargs="*")
    p.add_argument("--samples", type=int, default=32); p.add_argument("--res", type=int, default=960); p.add_argument("--cpu", action="store_true")
    p.add_argument("--out", type=Path, default=asset.EVIDENCE / "belege"); p.add_argument("--sheets", action="store_true")
    a = p.parse_args(argv)
    if a.ids:
        cfg, snap, kit, sheets = asset.settings(), ballon.snapshot(), ballon_kit.snapshot(), variants.sheets()
        for sid in a.ids:
            render(sid, sheets[sid], kit, snap, cfg, a)
    if a.sheets:
        for letter in SERIES:
            print(bogen(letter, f"kontaktbogen_{letter}.png", a.out))
        compare(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
