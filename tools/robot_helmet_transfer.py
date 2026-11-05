#!/usr/bin/env python3
"""Einmalige Übertragung: Helm H 80 aus RoboterBasic-01.glb → formgen/models/robot/helmet_h80.json (Flächen im Kopfrahmen).

Nur für die Herkunft im Repo; zur Laufzeit und im Build wird das GLB nie gelesen.
  tools/robot_helmet_transfer.py <RoboterBasic-01.glb>
"""
import hashlib, json, re, struct, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
UNITS = 100          # 0,01 mm je Einheit


def glb_parts(path):
    data = Path(path).read_bytes()
    size, = struct.unpack_from('<I', data, 12)
    doc = json.loads(data[20:20 + size]); base = 28 + size

    def accessor(i):
        a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
        dt = np.dtype({5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']]); w = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        st = v.get('byteStride', w * dt.itemsize)
        return np.ndarray((a['count'], w), dtype=dt, buffer=data, offset=base + v.get('byteOffset', 0) + a.get('byteOffset', 0),
                          strides=(st, dt.itemsize)).astype(float)

    def matrix(n):
        if 'matrix' in n:
            return np.array(n['matrix'], float).reshape(4, 4).T
        M = np.eye(4)
        x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        M[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                              [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * np.array(n.get('scale', [1, 1, 1]))
        M[:3, 3] = n.get('translation', [0, 0, 0])
        return M
    out = []

    def walk(i, P, segment):
        n = doc['nodes'][i]; W = P @ matrix(n)
        segment = n.get('name') if (n.get('name') or '').startswith(('SEG_', 'ARM_', 'SHOULDER_')) else segment
        if 'mesh' in n and segment == 'SEG_head':
            prim, = doc['meshes'][n['mesh']]['primitives']
            V = accessor(prim['attributes']['POSITION'])
            T = (accessor(prim['indices']) if 'indices' in prim else np.arange(len(V))).reshape(-1, 3).astype(int)
            out.append((n.get('name'), doc['materials'][prim['material']]['name'].removeprefix('MT_').removesuffix('_color'),
                        (W[:3, :3] @ V.T).T + W[:3, 3], T))
        for c in n.get('children', []):
            walk(c, W, segment)
    for r in doc['scenes'][0]['nodes']:
        walk(r, np.eye(4), None)
    return out, hashlib.sha256(data).hexdigest()


def main(path):
    from formgen.models.robot import body, rig
    from formgen.models.robot.roboterbasic_01 import REFERENCE_PARAMS
    R, o, _, _ = rig.body_segments(body.skeleton(REFERENCE_PARAMS['skeleton']))['head']
    found, sha = glb_parts(path)
    seen, anon, parts = {}, 0, []
    names = [n for n, *_ in found]
    for name, role, V, T in found:
        if name in ('neck', 'neck_ring', 'neck_trim'):
            continue
        if name is None:
            anon += 1
            pid, label = f'helmet_detail_{anon:02d}', f'Helmdetail {anon}'
        else:
            snake = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', name).lower()
            pid, label = f'helmet_{snake}', name
            if names.count(name) > 1:
                seen[name] = seen.get(name, 0) + 1
                pid += '_' + 'ab'[seen[name] - 1]
        world = np.c_[V[:, 0], -V[:, 2], V[:, 1]] * 1000             # glTF → Welt-mm (X, Y, Z)
        local = np.round(((world - o) @ R) * UNITS).astype(int)
        uniq, inverse = np.unique(local, axis=0, return_inverse=True)
        faces = inverse.reshape(-1)[T]
        faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
        # Mehrfach belegte Kanten: betroffene Dreiecke bekommen eigene Punkte (Naht), sonst lehnt geom die Fläche ab.
        edges = np.sort(faces[:, [[0, 1], [1, 2], [2, 0]]].reshape(-1, 2), axis=1)
        _, ids, counts = np.unique(edges, axis=0, return_inverse=True, return_counts=True)
        seams = np.flatnonzero((counts[ids.reshape(-1)].reshape(-1, 3) > 2).any(axis=1))
        points = np.vstack([uniq, uniq[faces[seams].ravel()]])
        faces[seams] = len(uniq) + np.arange(3 * len(seams)).reshape(-1, 3)
        parts.append(dict(id=pid, label=label, role=role, vertices=points.tolist(), faces=faces.tolist()))
    out = dict(format='formgenv2/robot-surface-data', version=1, frame='Kopfsegment (BALLON-Rahmen, mm)', units_per_mm=UNITS,
               source=f'Helm H 80, gemessen aus RoboterBasic-01.glb SHA256 {sha}, Sicherung 05.11.2026; keine Kit-Quelle vorhanden',
               parts=parts)
    target = ROOT / 'formgen/models/robot/helmet_h80.json'
    target.write_text(json.dumps(out, separators=(',', ':')) + '\n')
    print(len(parts), 'Teile', sum(len(p['vertices']) for p in parts), 'Punkte', sum(len(p['faces']) for p in parts), 'Dreiecke', target.stat().st_size // 1024, 'KiB')


if __name__ == '__main__':
    main(sys.argv[1])
