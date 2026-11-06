"""Silhouettenvergleich zweier Figuren: gleiche Registrierung, kein Strecken. Abnahmeregel aus docs/robot.md (IoU ≥ 0,90,
Bandbreite 0,92–1,08; Breite = mittlere äußere Spannweite je Zeile, leere Zeilen zählen null). Eingaben sind Dreiecksnetze in glTF-Achsen (Meter).

  python -m formgen.robot.silhouette <referenz.glb> --referenzhaltung [--typ 2 | --ohne-helm]
  python -m formgen.robot.silhouette <referenz.glb> <modell.glb> [--ohne-helm]
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

IOU_MIN, BAND_MIN, BAND_MAX, BANDS = .90, .92, 1.08, 10
VIEWS = {'front': (0, 1, 1), 'back': (0, 1, -1), 'side_right': (2, 1, 1), 'side_left': (2, 1, -1)}   # Achse waagerecht, senkrecht, Vorzeichen


def triangles(path, helmet=True):
    """Alle Dreiecke eines GLB in Weltlage: Array (n, 3, 3). helmet=False lässt Helmteile weg (Referenz: SEG_head ohne Hals, Modell: helmet_*)."""
    data = Path(path).read_bytes()
    size, = struct.unpack_from('<I', data, 12)
    doc = json.loads(data[20:20 + size])
    base = 28 + size

    def accessor(i):
        a = doc['accessors'][i]
        v = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype({5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']])
        width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        stride = v.get('byteStride', width * dtype.itemsize)
        return np.ndarray((a['count'], width), dtype, data, base + v.get('byteOffset', 0) + a.get('byteOffset', 0), (stride, dtype.itemsize)).astype(float)

    def local(n):
        if 'matrix' in n:
            return np.array(n['matrix'], float).reshape(4, 4).T
        x, y, z, w = n.get('rotation', (0, 0, 0, 1))
        m = np.eye(4)
        m[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                              [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get('scale', (1, 1, 1)))
        m[:3, 3] = n.get('translation', (0, 0, 0))
        return m
    out = []

    def walk(i, parent, head=False):
        n = doc['nodes'][i]
        world = parent @ local(n)
        head = head or n.get('name') == 'SEG_head'
        name = n.get('name') or ''
        skip = not helmet and (name.startswith('helmet_') or (head and 'mesh' in n and name not in ('neck', 'neck_ring', 'neck_trim')))
        if 'mesh' in n and not skip:
            for prim in doc['meshes'][n['mesh']]['primitives']:
                v = accessor(prim['attributes']['POSITION'])
                t = (accessor(prim['indices']) if 'indices' in prim else np.arange(len(v))).reshape(-1, 3).astype(int)
                out.append(((world[:3, :3] @ v.T).T + world[:3, 3])[t])
        for c in n.get('children', ()):
            walk(c, world, head)
    for r in doc['scenes'][doc.get('scene', 0)]['nodes']:
        walk(r, np.eye(4))
    return np.concatenate(out)


def mask(tris, view, lo, hi, px_per_m):
    """Binärmaske der Projektion; lo/hi feste Weltgrenzen (h, v) für beide Figuren."""
    ax, ay, sign = VIEWS[view]
    w, h = np.ceil((hi - lo) * px_per_m).astype(int) + 1
    image = Image.new('1', (int(w), int(h)))
    draw = ImageDraw.Draw(image)
    xs = (tris[:, :, ax] * sign - lo[0]) * px_per_m
    ys = (hi[1] - tris[:, :, ay]) * px_per_m
    for a, b in zip(xs.tolist(), ys.tolist()):
        draw.polygon(list(zip(a, b)), fill=1)
    return np.asarray(image, bool)


def spans(m):
    rows = m.any(axis=1)
    first, last = m.argmax(axis=1), m.shape[1] - 1 - m[:, ::-1].argmax(axis=1)
    return np.where(rows, last - first + 1, 0).astype(float)


def compare(a, b, px_per_m=1000):
    """a Referenz, b Modell (Dreiecke). Rückgabe je Ansicht: IoU, Bandverhältnisse Modell/Referenz, bestanden."""
    result = {}
    for view, (ax, ay, sign) in VIEWS.items():
        both = np.concatenate((a.reshape(-1, 3), b.reshape(-1, 3)))
        lo = np.array((min((both[:, ax] * sign).min(), 0), both[:, ay].min()))
        hi = np.array(((both[:, ax] * sign).max(), both[:, ay].max()))
        ma, mb = mask(a, view, lo, hi, px_per_m), mask(b, view, lo, hi, px_per_m)
        iou = float((ma & mb).sum() / (ma | mb).sum())
        ys = np.flatnonzero(ma.any(axis=1))
        edges = np.linspace(ys[0], ys[-1] + 1, BANDS + 1).round().astype(int)
        sa, sb = spans(ma), spans(mb)
        bands = [float(sb[i:j].mean() / sa[i:j].mean()) for i, j in zip(edges[:-1], edges[1:])][::-1]   # 0 = unten
        result[view] = dict(iou=round(iou, 4), bands=[round(v, 4) for v in bands],
                            iou_pass=iou >= IOU_MIN, bands_pass=all(BAND_MIN <= v <= BAND_MAX for v in bands))
    return result


def reference_triangles(helmet=True, kind=1):
    """Basic-Typ aus dem Register in der Haltung des Referenz-GLB; die Grundhaltung A-Position lässt sich gegen die Referenz nicht messen."""
    import importlib
    import tempfile
    from . import bevel, glb, lines
    modules = {t['num']: t['module'] for t in lines.load()['types']}
    if kind not in modules:
        raise SystemExit(f'--typ {kind}: im Register stehen nur {sorted(modules)}')
    basic = importlib.import_module(modules[kind])
    document = bevel.evaluate(basic.document(basic.REFERENCE_PARAMS))
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'referenz.glb'
        path.write_bytes(glb.build(document, 'weiss_graphit'))
        return triangles(path, helmet)


def main(argv=None):
    args = list(argv or sys.argv[1:])
    helmet = '--ohne-helm' not in args
    kind = 1
    if '--typ' in args:
        at = args.index('--typ')
        if at + 1 == len(args) or not args[at + 1].isdigit():
            raise SystemExit('--typ braucht die Nummer eines Basic-Typs')
        if '--referenzhaltung' not in args:
            raise SystemExit('--typ gilt nur mit --referenzhaltung')
        kind = int(args.pop(at + 1))
    if kind != 1 and not helmet:
        raise SystemExit('--ohne-helm gilt nur für Typ 1: nur dessen Referenz hat SEG_head')
    files = [a for a in args if not a.startswith('--')]
    if '--referenzhaltung' in args:
        report = compare(triangles(files[0], helmet), reference_triangles(helmet, kind))
    else:
        report = compare(triangles(files[0], helmet), triangles(files[1], helmet))
    print(json.dumps(report, indent=1))
    return 0 if all(v['iou_pass'] and v['bands_pass'] for v in report.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
