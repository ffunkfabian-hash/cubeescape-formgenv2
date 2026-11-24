"""AAA-Renders eines EXTENDED-Modells (0.15): BALLONs unverändertes `tools/blender_build.main(W=<Datensatz>, argv=[…])` im Kit-Snapshot.

  ~/Claude/cubeescape-nexogen/ce lock blender -- .venv/bin/python tools/extended_render.py e01 --tag r1 [--samples 96] [--res 1600]
  ~/Claude/cubeescape-nexogen/ce lock gpu -- .venv/bin/python tools/extended_render.py e01 --tag r1 --gpu
  .venv/bin/python tools/extended_render.py e01 --tag r1 --sheets      # nur Bögen aus vorhandenen Bildern

Cache: Ein Tag rendert nur, wenn Bilder fehlen oder der Stempel `<out>/<tag>/render.json` (Datensatz-Hash, Quellhash, Kit-Snapshot,
Wrapper, Samples, Auflösung, Ansichten) nicht passt; `--force` rendert trotzdem neu (Projektregel: nie ungefragt alles neu).

0.20 (additiv): `--ref <Ordner>` setzt vergleich_ref_<Ordner>.png gegen eine BASIC-Referenz, DETAIL je Modell legt detail_<n>_<Ansicht>.png
an; ohne --out rendern neue Modelle nach <OUT>/<Kurzname>/<tag>, e01 weiter nach <OUT>/<tag>.

Ansichten: hero (eigenes HERO des Modells), hero_p (70 mm Perspektive), side (rechts), side_left, top, front, rear, dazu clay und
exploded aus demselben Lauf. Hintergrund mittelgrau, ohne Bloom (Projektregel). Ausgabe außerhalb des Repos:
<out>/<tag>/<Ansicht>.png, <out>/<tag>/kontaktbogen.png, <out>/<tag>/vergleich_BA01.png, <out>/<tag>/<id>.spec.json.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import asset, ballon, ballon_kit, extended  # noqa: E402

OUT = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.15/belege"
VIEWS = ("hero", "hero_p", "side_left", "side", "top", "front", "rear")
WRAPPER = r'''
import json, os, sys
job = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
os.environ['BASIC_OUT'] = job['out']
sys.path.insert(0, job['snapshot'])
import tools.blender_build as BB
argv = ['--views', '--aaa', '--only', job['only'], '--samples', str(job['samples']), '--res', str(job['res']), '--bg', 'mid']
BB.main(W=job['model'], base=None, argv=argv + (['--gpu'] if job['gpu'] else []))
'''
BA01 = Path.home() / "Library/Caches/CubeEscapeFormgen2/0.8/belege/aaa"
# 0.19 (EXTENDED-10/11): Energiewaffen nutzen BALLONs Leuchtrollen aus `basic.pilot.energy_roles` (z. B. `charge_core`). Das Waffenmodul
# läuft in Blender nicht, also registriert eine Importzeile die Rollen – nur für Datensätze, die sie nutzen (e01: Wrapper und Stempel gleich).
CHARGE_MATS = ("charge_core", "pin_glow", "draw_light")


def wrapper(data):
    if not any(p.get("mat") in CHARGE_MATS for p in data["PARTS"]):
        return WRAPPER
    return WRAPPER.replace("import tools.blender_build as BB", "import basic.pilot.energy_roles\nimport tools.blender_build as BB")


def font(size):
    path = ROOT / "formgen/assets/fonts/Barlow-SemiBold.ttf"
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def views(a):
    return VIEWS + (("clay", "exploded") if a.extra else ())


def stamp(key, a, data, kit):
    """Alles, was die Bilder bestimmt (gpu nicht: gleiche Szene, nur anderes Gerät)."""
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    return {"key": key, "data_sha256": digest, "source_sha256": extended.source(key)["source_sha256"], "kit": Path(kit).name,
            "wrapper_sha256": hashlib.sha256(wrapper(data).encode()).hexdigest(), "samples": a.samples, "res": a.res,
            "views": list(views(a))}


def current(target, want):
    """True, wenn Stempel gleich und alle Ansichten vorhanden sind."""
    path = target / "render.json"
    if not path.exists() or any(not (target / f"{v}.png").exists() for v in want["views"]):
        return False
    return json.loads(path.read_text()) == want


def render(key, a):
    data = extended.load(key)
    kit = ballon_kit.snapshot()
    target = a.out / a.tag
    target.mkdir(parents=True, exist_ok=True)
    want = stamp(key, a, data, kit)
    if not a.force and current(target, want):
        print(target, "aktuell, kein Render (--force rendert neu)", flush=True)
        return False
    (target / "render.json").unlink(missing_ok=True)   # ein abgebrochener Lauf hinterlässt keinen gültigen Stempel
    with tempfile.TemporaryDirectory(prefix=f"formgen-extended-{key}-") as tmp:
        tmp = Path(tmp)
        (tmp / "wrapper.py").write_text(wrapper(data))
        only = ",".join(views(a))
        job = {"snapshot": str(kit), "model": data, "out": str(tmp / "o"), "only": only, "samples": a.samples, "res": a.res,
               "gpu": a.gpu}
        (tmp / "job.json").write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([asset.settings()["blender"], "-b", "--factory-startup", "-P", str(tmp / "wrapper.py"), "--",
                              str(tmp / "job.json")], capture_output=True, text=True)
        log = run.stdout + run.stderr
        (target / "blender.log").write_text(log)
        if run.returncode or "Traceback" in log:
            raise RuntimeError("\n".join(log.splitlines()[-30:]))
        meta = data["META"]
        wid = meta["id"] + (f'-{meta["variant"]}' if meta.get("variant") else "")
        missing = [v for v in views(a) if not (tmp / "o" / wid / "views" / f"{v}.png").exists()]
        if missing:   # vor dem Kopieren: alte Bilder dürften sonst mit neuem Stempel als aktuell gelten
            raise RuntimeError(f"Blender lieferte nicht alle Ansichten: {missing}")
        for png in (tmp / "o" / wid / "views").glob("*.png"):
            shutil.copyfile(png, target / png.name)
        for ext in ("spec.json", "glb", "blend"):
            src = tmp / "o" / wid / f"{wid}.{ext}"
            if src.exists():
                shutil.copyfile(src, target / src.name)
    (target / "render.json").write_text(json.dumps(want, ensure_ascii=False, indent=1))
    print(target, sorted(p.name for p in target.glob("*.png")), flush=True)
    return True


def sheets(key, a):
    target = a.out / a.tag
    data = extended.load(key)
    title = f"{data['META']['id']} {data['META']['name']} · Runde {a.tag}"
    w, h = 800, 450
    names = [v for v in VIEWS if (target / f"{v}.png").exists()]
    cols = 2
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + 8) + 8, 56 + rows * (h + 30)), "#808080")
    d = ImageDraw.Draw(sheet)
    d.text((12, 12), title, fill="#111317", font=font(26))
    for i, v in enumerate(names):
        x, y = 8 + (i % cols) * (w + 8), 56 + (i // cols) * (h + 30)
        sheet.paste(Image.open(target / f"{v}.png").convert("RGB").resize((w, h), Image.LANCZOS), (x, y))
        d.text((x + 4, y + h + 3), v, fill="#111317", font=font(18))
    sheet.save(target / "kontaktbogen.png")
    pairs = [("BA01_hero.png", "hero.png"), ("BA01_side.png", "side_left.png")]
    cmp = Image.new("RGB", (2 * w + 24, 2 * (h + 34) + 16), "#808080")
    d = ImageDraw.Draw(cmp)
    for j, (ref, own) in enumerate(pairs):
        for i, (path, label) in enumerate(((BA01 / ref, "BASIC-01 (BA01, 0.8)"), (target / own, title))):
            y = 8 + j * (h + 34)
            if path.exists():
                cmp.paste(Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS), (8 + i * (w + 8), y + 30))
            d.text((12 + i * (w + 8), y + 4), label, fill="#111317", font=font(20))
    cmp.save(target / "vergleich_BA01.png")
    print(target / "kontaktbogen.png", target / "vergleich_BA01.png")


# 0.20 Riftguard (additiv): Vergleich mit einer beliebigen BASIC-Referenz statt BA01 – Ordner mit hero/side_left/front/top.png
# (Nahkampf: BASIC-16/17 haben keine BA-Bilder in 0.8). Lange, schmale Formen bekommen Ausschnitte der Hero-Ansicht (--detail).
def compare_dir(key, a):
    target = a.out / a.tag
    data = extended.load(key)
    title = f"{data['META']['id']} {data['META']['name']} · Runde {a.tag}"
    w, h = 800, 450
    names = [v for v in ("hero", "side_left", "front", "top") if (a.ref / f"{v}.png").exists() and (target / f"{v}.png").exists()]
    cmp = Image.new("RGB", (2 * w + 24, len(names) * (h + 34) + 16), "#808080")
    d = ImageDraw.Draw(cmp)
    for j, v in enumerate(names):
        for i, (path, label) in enumerate(((a.ref / f"{v}.png", f"{a.ref.name} · {v}"), (target / f"{v}.png", f"{title} · {v}"))):
            y = 8 + j * (h + 34)
            cmp.paste(Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS), (8 + i * (w + 8), y + 30))
            d.text((12 + i * (w + 8), y + 4), label, fill="#111317", font=font(20))
    name = f"vergleich_ref_{a.ref.name}.png"   # eigenes Präfix: ein Ordner „BA16“ träfe sonst vergleich_BA<NN>.png von --basic
    cmp.save(target / name)
    print(target / name)


def details(key, a):
    """Ausschnitte (Bruchteile x0, y0, x1, y1 des Bildes) je Ansicht aus DETAIL des Modells, auf 800 px Breite."""
    target = a.out / a.tag
    for i, (view, box) in enumerate(DETAIL.get(key, ())):
        if not (target / f"{view}.png").exists():   # wie compare_dir: fehlende Ansicht überspringen
            continue
        im = Image.open(target / f"{view}.png").convert("RGB")
        W_, H_ = im.size
        crop = im.crop((int(box[0] * W_), int(box[1] * H_), int(box[2] * W_), int(box[3] * H_)))
        crop.resize((800, int(800 * crop.size[1] / crop.size[0])), Image.LANCZOS).save(target / f"detail_{i + 1}_{view}.png")


DETAIL = {}
DETAIL["e16"] = [("hero", (0.55, 0.12, 0.98, 0.55)), ("side", (0.02, 0.36, 0.40, 0.68))]   # 0.20: Griffbereich Schwert
DETAIL["e17"] = [("hero", (0.0, 0.5, 0.42, 0.95)), ("side_left", (0.0, 0.38, 0.42, 0.62)),   # 0.20: Kopf und
                 ("hero", (0.55, 0.25, 0.85, 0.62))]                                           # Abzugskragen Glefe


# 0.17 „Outrider“ (additiv, `--basic NN`): Vergleich mit dem eigenen BASIC-Typ statt BA01 – der Pilot BASIC-NN läuft durch denselben AAA-Weg
# (Grundmodul = Pilot, damit EJECT/EGO-Felder vollständig sind) nach <out>/BA<NN>/ mit eigenem Stempel; Bogen vergleich_BA<NN>.png.
REF_VIEWS = ("hero", "side_left")
REF_WRAPPER = WRAPPER.replace("base=None", "base=job['base']")


def render_ref(num, a):
    snap = ballon_kit.snapshot()
    base = ballon.resolve_base(snap, num, "pilot")
    module = ".".join(ballon.module_file(snap, num, base).relative_to(snap).with_suffix("").parts)
    data = extended.load_basic(num)
    target = a.out / f"BA{num}"
    target.mkdir(parents=True, exist_ok=True)
    want = {"ref": num, "module": module, "data_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
            default=str).encode()).hexdigest(), "kit": Path(snap).name, "wrapper_sha256": hashlib.sha256(REF_WRAPPER.encode()).hexdigest(),
            "samples": a.samples, "res": a.res, "views": list(REF_VIEWS)}
    if not a.force and current(target, want):
        return False
    (target / "render.json").unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"formgen-extended-BA{num}-") as tmp:
        tmp = Path(tmp)
        (tmp / "wrapper.py").write_text(REF_WRAPPER)
        job = {"snapshot": str(snap), "model": data, "base": module, "out": str(tmp / "o"), "only": ",".join(REF_VIEWS),
               "samples": a.samples, "res": a.res, "gpu": a.gpu}
        (tmp / "job.json").write_text(json.dumps(job, ensure_ascii=False))
        run = subprocess.run([asset.settings()["blender"], "-b", "--factory-startup", "-P", str(tmp / "wrapper.py"), "--",
                              str(tmp / "job.json")], capture_output=True, text=True)
        log = run.stdout + run.stderr
        (target / "blender.log").write_text(log)
        views_dir = next((tmp / "o").glob("*/views"), None)
        if run.returncode or "Traceback" in log or views_dir is None or any(not (views_dir / f"{v}.png").exists() for v in REF_VIEWS):
            raise RuntimeError("\n".join(log.splitlines()[-30:]))
        for v in REF_VIEWS:
            shutil.copyfile(views_dir / f"{v}.png", target / f"{v}.png")
    (target / "render.json").write_text(json.dumps(want, ensure_ascii=False, indent=1))
    return True


def compare_ref(key, a):
    """vergleich_BA<NN>.png: Hero und linke Seite des Modells neben dem gerenderten BASIC-NN."""
    target, ref = a.out / a.tag, a.out / f"BA{a.basic}"
    data = extended.load(key)
    title = f"{data['META']['id']} {data['META']['name']} · Runde {a.tag}"
    w, h = 800, 450
    cmp = Image.new("RGB", (2 * w + 24, 2 * (h + 34) + 16), "#808080")
    d = ImageDraw.Draw(cmp)
    for j, (r, own) in enumerate((("hero.png", "hero.png"), ("side_left.png", "side_left.png"))):
        for i, (path, label) in enumerate(((ref / r, f"BASIC-{a.basic} (Pilot, gleicher AAA-Weg)"), (target / own, title))):
            y = 8 + j * (h + 34)
            if path.exists():
                cmp.paste(Image.open(path).convert("RGB").resize((w, h), Image.LANCZOS), (8 + i * (w + 8), y + 30))
            d.text((12 + i * (w + 8), y + 4), label, fill="#111317", font=font(20))
    cmp.save(target / f"vergleich_BA{a.basic}.png")
    print(target / f"vergleich_BA{a.basic}.png")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("key", choices=sorted(extended.MODELS.keys() | extended.PIPELINE_SHEETS.keys()))
    p.add_argument("--tag", required=True, help="Runde, z. B. r1")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--res", type=int, default=1600)
    p.add_argument("--gpu", action="store_true", help="nur unter `ce lock gpu`")
    p.add_argument("--extra", action="store_true", help="zusätzlich clay und exploded")
    p.add_argument("--sheets", action="store_true", help="nur Bögen setzen")
    p.add_argument("--force", action="store_true", help="auch bei passendem Stempel neu rendern")
    p.add_argument("--out", type=Path, default=None, help="Zielordner (Standard: OUT, neue Modelle OUT/<Kurzname>)")
    p.add_argument("--ref", type=Path, help="Ordner der BASIC-Referenz (hero/side_left/front/top.png) für den Vergleich")
    p.add_argument("--basic", help="0.17: BASIC-Nummer (z. B. 02) als Vergleich im selben AAA-Weg rendern")
    a = p.parse_args(argv)
    if a.out is None:   # 0.20 (Richter): ohne --out neue Modelle je Kurzname getrennt, e01 behält seinen 0.15-Pfad
        a.out = OUT if a.key == "e01" else OUT / a.key
    if not a.sheets:
        render(a.key, a)
    sheets(a.key, a)
    if getattr(a, "basic", None):
        if not a.sheets:
            render_ref(a.basic, a)
        compare_ref(a.key, a)
    if a.ref:
        compare_dir(a.key, a)
    details(a.key, a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
