"""Vielfalt der Roboterlinien messen (0.13): Silhouetten-IoU jeder Linie gegen Linie A desselben Typs in drei Orthos, wie formgen.variety bei den Waffen.

  python -m formgen.robot.variety                  # Tabelle aller Blätter, dazu die Paare der Linien untereinander
  python -m formgen.robot.variety --json out/robot-variety.json

Masken: gefüllte Dreiecke der Geometrie ohne Booleans und Fasen (die Außenkontur ändern sie nicht merklich), 2 mm je Pixel, feste Weltgrenzen
beider Figuren, keine Verschiebung. Der Skin zählt nicht. Eine Linie weicht sichtbar ab, wenn die kleinste IoU aus Front, Seite und Draufsicht höchstens
THRESHOLD ist; zwei Linien unterscheiden sich, wenn ihre kleinste IoU höchstens PAIR_THRESHOLD ist. Beide Schwellen Annahme, am Bild gesichtet.
"""
from __future__ import annotations

import itertools
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

from formgen import geom, model
from . import lines

MM_PX = 2.0
VIEWS = dict(front=(0, 2), side=(1, 2), top=(0, 1))      # Achsen im Ausgaberaum (x links, −y vorn, z oben)
THRESHOLD = 0.97       # Annahme: ≥ 3 % Flächenunterschied in der kleinsten Ansicht ist am Blatt zu erkennen; Weapons-Linien: 0,98 bei Langwaffen
PAIR_THRESHOLD = 0.985  # Annahme: zwei Linien sind mindestens halb so verschieden wie eine Linie von A


def triangles(entry, sid='RA01'):
    """Dreiecke (n, 3, 3) in Metern; Polygone werden als Fächer zerlegt."""
    module = lines.module_of(entry)
    document = module.document(lines.merge(module.PARAMS, entry['params']), sheet_id=sid, line=entry['line']['name'].lower(), name=entry['type']['name_de'])
    out = []
    for p in geom.evaluate(model.normalize(document), booleans=False, bevels=False)['parts']:
        v = np.asarray(p['mesh']['vertices'], float)
        for face in p['mesh']['faces']:
            out += [v[[face[0], face[i], face[i + 1]]] for i in range(1, len(face) - 1)]
    return np.array(out)


def _mask(tris, axes, lo, shape):
    image = Image.new('1', shape[::-1], 0)
    draw = ImageDraw.Draw(image)
    points = (tris[..., list(axes)] * 1000 - lo) / MM_PX
    for t in points.tolist():
        draw.polygon([(x, shape[0] - 1 - y) for x, y in t], fill=1)
    return np.asarray(image, bool)


def masks(cache):
    """Masken aller Blätter auf einem gemeinsamen Raster je Ansicht (feste Weltgrenzen aller Figuren)."""
    out = {sid: {} for sid in cache}
    everything = np.concatenate([t.reshape(-1, 3) for t in cache.values()])
    for view, axes in VIEWS.items():
        flat = everything[:, list(axes)] * 1000
        lo = flat.min(0) - 4
        shape = tuple(int(x) for x in ((flat.max(0) + 4 - lo) / MM_PX)[::-1] + 1)
        for sid, tris in cache.items():
            out[sid][view] = _mask(tris, axes, lo, shape)
    return out


def iou(a, b):
    """IoU je Ansicht zweier Maskensätze."""
    return {view: round(float((a[view] & b[view]).sum() / (a[view] | b[view]).sum()), 4) for view in VIEWS}


def measure(register=None):
    """{'against_a': {Blatt: IoU je Ansicht}, 'pairs': {'RB01-RC01': IoU je Ansicht}}; A gegen A ist 1 und wird nicht gelistet."""
    sheets = lines.sheets(register)
    shapes = masks({sid: triangles(entry, sid) for sid, entry in sheets.items()})
    by_type: dict[int, dict[str, str]] = {}
    for sid, entry in sheets.items():
        by_type.setdefault(entry['type']['num'], {})[entry['line']['letter']] = sid
    against, pairs = {}, {}
    for letters in by_type.values():
        for letter, sid in letters.items():
            if letter != 'A' and 'A' in letters:
                against[sid] = iou(shapes[letters['A']], shapes[sid])
        for (_, sa), (_, sb) in itertools.combinations([(k, v) for k, v in letters.items() if k != 'A'], 2):
            pairs[f'{sa}-{sb}'] = iou(shapes[sa], shapes[sb])
    return dict(against_a=against, pairs=pairs)


def verdict(result):
    """Kurztext je Eintrag: kleinste IoU und ob die Schwelle erreicht ist."""
    rows = []
    for key, views in {**result['against_a'], **result['pairs']}.items():
        limit = THRESHOLD if key in result['against_a'] else PAIR_THRESHOLD
        least = min(views.values())
        rows.append((key, views, least, least <= limit))
    return rows


def main(argv=None):
    args = list(argv or sys.argv[1:])
    result = measure()
    for key, views, least, ok in verdict(result):
        print(f"{key:8s} " + ' '.join(f'{v} {views[v]:.4f}' for v in VIEWS) + f"  min {least:.4f}  {'abweichend' if ok else 'GLEICH'}")
    if '--json' in args:
        path = args[args.index('--json') + 1]
        with open(path, 'w') as fh:
            json.dump(result, fh, indent=1, sort_keys=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
