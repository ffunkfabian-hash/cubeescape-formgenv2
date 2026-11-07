"""Vielfalt der Roboterlinien messen (0.13): Silhouetten-IoU jeder Linie gegen Linie A desselben Typs in drei Orthos, wie formgen.variety bei den Waffen.

  python -m formgen.robot.variety                  # Tabelle aller Blätter, dazu die Paare der Linien untereinander
  python -m formgen.robot.variety --json out/robot-variety.json
  python -m formgen.robot.variety --teile          # 0.14: je Einzelteil, jede Katalogvariante gegen die Grundform und jede Linie gegen A

Masken: gefüllte Dreiecke der Geometrie ohne Booleans und Fasen (die Außenkontur ändern sie nicht merklich), 2 mm je Pixel, feste Weltgrenzen
beider Figuren, keine Verschiebung. Der Skin zählt nicht. Eine Linie weicht sichtbar ab, wenn die kleinste IoU aus Front, Seite und Draufsicht höchstens
THRESHOLD ist; zwei Linien unterscheiden sich, wenn ihre kleinste IoU höchstens PAIR_THRESHOLD ist. Beide Schwellen Annahme, am Bild gesichtet.
"""
from __future__ import annotations

import copy
import itertools
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

from formgen import geom, model
from . import lines

MM_PX = 2.0           # Annahme: Raster der Messung; die Außenkontur ändert sich darunter nicht merklich, 4 mm Rand je Seite ebenso
VIEWS = dict(front=(0, 2), side=(1, 2), top=(0, 1))      # Achsen im Ausgaberaum (x links, −y vorn, z oben)
THRESHOLD = 0.97       # Annahme: ≥ 3 % Flächenunterschied in der kleinsten Ansicht ist am Blatt zu erkennen; Weapons-Linien: 0,98 bei Langwaffen
PAIR_THRESHOLD = 0.985  # Annahme: zwei Linien sind mindestens halb so verschieden wie eine Linie von A
PART_THRESHOLD = 0.97   # Annahme (0.14): eine Variante weicht in der kleinsten Ansicht ihres Einzelteils um ≥ 3 % Fläche von der Grundform ab


def by_assembly(module, params, sid='RA01'):
    """Dreiecke (n, 3, 3) in Metern je Einzelteil; Polygone werden als Fächer zerlegt."""
    document = module.document(params, sheet_id=sid)
    out = {}
    for p in geom.evaluate(model.normalize(document), booleans=False, bevels=False)['parts']:
        v = np.asarray(p['mesh']['vertices'], float)
        tris = out.setdefault(p['assembly'], [])
        for face in p['mesh']['faces']:
            tris += [v[[face[0], face[i], face[i + 1]]] for i in range(1, len(face) - 1)]
    return {a: np.array(t).reshape(-1, 3, 3) for a, t in out.items()}


def triangles(entry, sid='RA01'):
    """Dreiecke (n, 3, 3) in Metern der ganzen Figur."""
    return np.concatenate(list(by_assembly(lines.module_of(entry), lines.params_of(entry), sid).values()))


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


def _part_iou(a, b):
    """IoU je Ansicht zweier Dreieckssätze desselben Einzelteils auf gemeinsamem Raster; ein leerer Satz zählt als leere Maske."""
    cache = {k: t for k, t in (('a', a), ('b', b)) if len(t)}
    if len(cache) < 2:
        return {view: (1.0 if not cache else 0.0) for view in VIEWS}
    m = masks(cache)
    return iou(m['a'], m['b'])


def measure_parts(catalog=None, types=None, register=None):
    """Vielfalt je Einzelteil (0.14). variants: je Typ jede Katalogvariante allein auf der Grundform, IoU ihres Einzelteils gegen die
    Grundform und die größte Nebenwirkung auf ein anderes Einzelteil (kleinste IoU dort); lines: je Blatt außer A die IoU jedes Einzelteils
    gegen A desselben Typs. Masken nur der Teile des Einzelteils, Raster und Ansichten wie measure()."""
    from formgen.models.robot import catalog as kit_module
    kit = kit_module.load() if catalog is None else catalog
    register = lines.load() if register is None else register
    modules = {t['num']: lines.module_of(dict(type=t)) for t in register['types'] if types is None or t['num'] in types}
    result = dict(variants={}, lines={})
    base = {}
    for num, module in modules.items():
        sid = f'RA{num:02d}'
        base[num] = by_assembly(module, module.PARAMS, sid)
        rows = result['variants'][sid] = {}
        for assembly, variants in kit.items():
            for letter, v in variants.items():
                if letter == kit_module.BASE:
                    continue
                params = copy.deepcopy(module.PARAMS)
                params['variants'][assembly] = letter
                with _catalog(kit_module, kit):
                    tris = by_assembly(module, params, sid)
                own = _part_iou(base[num].get(assembly, np.empty((0, 3, 3))), tris.get(assembly, np.empty((0, 3, 3))))
                side = {a: min(_part_iou(base[num].get(a, np.empty((0, 3, 3))), tris.get(a, np.empty((0, 3, 3)))).values())
                        for a in kit if a != assembly}
                worst = min(side, key=side.get)
                rows[v.id] = dict(assembly=assembly, iou=own, least=min(own.values()), side_effect=dict(assembly=worst, least=side[worst]))
    for sid, entry in lines.sheets(register).items():
        num = entry['type']['num']
        if entry['line']['letter'] == 'A' or num not in modules:
            continue
        with _catalog(kit_module, kit):
            tris = by_assembly(modules[num], lines.params_of(entry), sid)
        result['lines'][sid] = {a: min(_part_iou(base[num].get(a, np.empty((0, 3, 3))), tris.get(a, np.empty((0, 3, 3)))).values())
                                for a in kit}
    return result


class _catalog:
    """Katalog für die Dauer einer Messung festhalten (Gegenproben mit eigenem Katalog)."""
    def __init__(self, module, kit):
        self.module, self.kit = module, kit

    def __enter__(self):
        self.load = self.module.load
        self.module.load = lambda: self.kit

    def __exit__(self, *exc):
        self.module.load = self.load


def part_verdict(result):
    """(Variante, Typ-Blatt, Einzelteil, kleinste IoU, abweichend?) je Katalogvariante."""
    return [(vid, sid, row['assembly'], row['least'], row['least'] <= PART_THRESHOLD)
            for sid, rows in result['variants'].items() for vid, row in rows.items()]


def main(argv=None):
    args = list(argv or sys.argv[1:])
    if '--teile' in args:
        result = measure_parts()
        for vid, sid, assembly, least, ok in part_verdict(result):
            row = result['variants'][sid][vid]
            print(f"{sid} {vid}  {assembly:10s} " + ' '.join(f'{v} {row["iou"][v]:.4f}' for v in VIEWS)
                  + f"  min {least:.4f}  {'abweichend' if ok else 'GLEICH'}  Nebenwirkung {row['side_effect']['assembly']} {row['side_effect']['least']:.4f}")
        for sid, parts in result['lines'].items():
            print(f'{sid} gegen A je Einzelteil: ' + ' '.join(f'{a} {v:.3f}' for a, v in parts.items()))
        if '--json' in args:
            with open(args[args.index('--json') + 1], 'w') as fh:
                json.dump(result, fh, indent=1, sort_keys=True)
        return 0
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
