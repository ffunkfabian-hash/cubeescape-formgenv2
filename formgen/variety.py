"""Vielfalt messen: Silhouetten-IoU jeder Linie gegen die Baseline (BAnn) in drei Orthos, wie tools/ballon_compare.py.

  python -m formgen.variety                     # Tabelle aller Linien × Typen
  python -m formgen.variety --json out/variety.json
  python -m formgen.variety --variants J,K,L,M --pairs   # Design-Serien gegen A und untereinander

Masken: gefüllte Dreiecke der ausgewerteten Geometrie (ohne Booleans und Fasen – die Außenkontur ändern sie nicht
merklich, und die Messung bleibt schnell), 0,5 mm je Pixel, gemeinsamer Ursprung Socket_Hand = 0; kein Fit, keine Verschiebung.
Eine Linie weicht sichtbar ab, wenn die kleinere IoU aus Seite und Draufsicht höchstens THRESHOLD ist, eine Design-Serie höchstens
SERIES_THRESHOLD (Begründung docs/generator.md › Vielfalt).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import ballon, generator, geom, model, variants

MM_PX = 0.5
VIEWS = {"side": (1, 2), "top": (1, 0), "front": (0, 2)}   # Achsen im Ausgaberaum (x links, −y vorn, z oben)
THRESHOLD = 0.98   # Annahme, begründet in docs/generator.md › Vielfalt: ≥ 2 % Flächenunterschied ist im Blatt sichtbar
SERIES_THRESHOLD = 0.95   # Annahme (0.8): eine Design-Serie weicht von A mindestens 5 % ab, gut das Doppelte einer Parameterlinie (0.4: 0,98)
PAIR_THRESHOLD = 0.97     # Annahme (0.8): zwei Serien unterscheiden sich schon in der Silhouette, nicht erst in der Farbe


def triangles(author):
    doc = geom.evaluate(model.normalize(author), booleans=False, bevels=False)
    return np.concatenate([np.asarray(p["mesh"]["vertices"], float)[np.asarray(p["mesh"]["faces"])] for p in doc["parts"]])


def _mask(tris, axes, lo, shape):
    im = Image.new("1", shape[::-1], 0); d = ImageDraw.Draw(im)
    pts = (tris[..., list(axes)] * 1000 - lo) / MM_PX
    for t in pts:
        d.polygon([(float(x), float(shape[0] - 1 - y)) for x, y in t], fill=1)
    return np.asarray(im, bool)


def iou(a, b):
    """IoU je Ansicht zweier Dreiecksmengen (n, 3, 3) in Metern."""
    out = {}
    for view, axes in VIEWS.items():
        both = np.concatenate([a.reshape(-1, 3), b.reshape(-1, 3)])[:, list(axes)] * 1000
        lo = both.min(0) - 4
        shape = tuple(int(x) for x in ((both.max(0) + 4 - lo) / MM_PX)[::-1] + 1)
        ma, mb = _mask(a, axes, lo, shape), _mask(b, axes, lo, shape)
        out[view] = round(float((ma & mb).sum() / (ma | mb).sum()), 4)
    return out


def visible(views, threshold=THRESHOLD) -> bool:
    return min(views["side"], views["top"]) <= threshold


def measure(entries=None, snap=None, letters=None, types=ballon.TYPES):
    entries = variants.load() if entries is None else entries
    snap = snap or ballon.snapshot()
    base = next(v for v in entries if v["letter"] == "A")
    result = {}
    for num in types:
        ref = triangles(generator.build(base, num, snap)[0])
        for v in entries:
            if v["letter"] == "A" or (letters and v["letter"] not in letters) or num not in v["types"]:
                continue
            views = iou(ref, triangles(generator.build(v, num, snap)[0]))
            limit = SERIES_THRESHOLD if v["params"].get("series") else THRESHOLD
            result[variants.sheet_id(v["letter"], num)] = {**views, "visible": visible(views, limit)}
    return result


def pairs(entries=None, snap=None, types=ballon.TYPES, letters=None):
    """Serien untereinander: {Typ: {"J-K": IoU …}} je Paar (kleinere IoU aus Seite und Draufsicht); `letters` wie bei `measure`."""
    entries = variants.load() if entries is None else entries
    snap = snap or ballon.snapshot()
    lines = [v for v in entries if v["params"].get("series") and (not letters or v["letter"] in letters)]
    result = {}
    for num in types:
        tris = {v["letter"]: triangles(generator.build(v, num, snap)[0]) for v in lines}
        row = {}
        for i, a in enumerate(lines):
            for b in lines[i + 1:]:
                views = iou(tris[a["letter"]], tris[b["letter"]])
                row[f"{a['letter']}-{b['letter']}"] = min(views["side"], views["top"])
        result[num] = row
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", type=Path)
    p.add_argument("--variants")
    p.add_argument("--pairs", action="store_true", help="zusätzlich die Serien untereinander messen")
    a = p.parse_args(argv)
    res = measure(letters=a.variants and a.variants.split(","))
    for sid, r in res.items():
        print(f"{sid}  Seite {r['side']:.4f}  oben {r['top']:.4f}  vorn {r['front']:.4f}  {'sichtbar' if r['visible'] else 'ZU ÄHNLICH'}")
    near = pairs(letters=a.variants and a.variants.split(",")) if a.pairs else {}
    for num, row in near.items():
        print(f"Serien {num}: " + "  ".join(f"{k} {v:.4f}" for k, v in row.items()))
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps({"threshold": THRESHOLD, "series_threshold": SERIES_THRESHOLD, "pair_threshold": PAIR_THRESHOLD,
                                      "mm_per_px": MM_PX, "sheets": res, "pairs": near}, indent=1) + "\n")
    return 0 if all(r["visible"] for r in res.values()) and all(v <= PAIR_THRESHOLD for row in near.values() for v in row.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
