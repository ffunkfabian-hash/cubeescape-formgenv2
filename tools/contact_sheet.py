"""Kontaktbogen der Waffenblätter aus vorhandenen Ansichten (kein Rendering): Zeilen = BASIC-Typ, Spalten = Variante.

  python tools/contact_sheet.py --view side_left --out ~/Library/Caches/CubeEscapeFormgen2/0.2/belege/kontaktbogen.png
"""
import argparse, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from formgen import variants  # noqa: E402


def font(size):
    path = ROOT / "formgen/assets/fonts/Barlow-SemiBold.ttf"
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=ROOT / "out"); p.add_argument("--view", default="side_left")
    p.add_argument("--types", default=",".join(variants.TYPES)); p.add_argument("--cell", type=int, default=420)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    entries = variants.load(); types = a.types.split(",")
    cw, ch, head, left = a.cell, a.cell // 2, 56, 230
    sheet = Image.new("RGB", (left + cw * len(entries), head + (ch + 26) * len(types)), "#e9e6df")
    d = ImageDraw.Draw(sheet); f, small = font(22), font(16)
    for j, v in enumerate(entries):
        d.text((left + j * cw + 10, 16), f"{v['letter']} · {v['name']} ({v['skin']})", fill="#22252a", font=f)
    for i, num in enumerate(types):
        y = head + i * (ch + 26)
        spec = None
        for j, v in enumerate(entries):
            sid = variants.sheet_id(v["letter"], num)
            img = a.out_dir / "views" / sid / f"{a.view}.png"
            sp = a.out_dir / "specs" / f"{sid}.spec.json"
            if img.exists():
                sheet.paste(Image.open(img).convert("RGB").resize((cw, ch), Image.LANCZOS), (left + j * cw, y))
            if sp.exists():
                spec = json.loads(sp.read_text())
                d.text((left + j * cw + 8, y + ch + 3), f"{sid} · {spec['dimensions_mm']['length']:.0f} mm", fill="#64696f", font=small)
        if spec:
            d.text((12, y + ch // 2 - 24), f"BASIC-{num}", fill="#995021", font=f)
            d.text((12, y + ch // 2 + 4), spec["type"]["type_de"][:24], fill="#22252a", font=small)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
