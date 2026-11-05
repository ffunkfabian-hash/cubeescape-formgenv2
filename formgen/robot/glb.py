"""Ausgewertetes Roboterdokument → GLB, rein in Python; Teile als eigene Nodes mit denselben Extras wie die Waffen-GLBs."""
from __future__ import annotations

import json
import struct
import tomllib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SHARP_DEG = 35.0          # wie BALLON set_sharp_from_angle (form_mesh)


def linear(color: str) -> list[float]:
    c = np.array([int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4).round(5).tolist()


def materials(skin: str, roles, path=ROOT / 'skins.toml'):
    data = tomllib.loads(Path(path).read_text())
    style = data['skins'][skin]
    out = []
    for role in roles:
        base = data['roles'][role]
        finish = style.get('finish', {}).get(role, {})
        color = linear(style.get('roles', {}).get(role, base['color']))
        m = dict(name=role, pbrMetallicRoughness=dict(baseColorFactor=color + [1.0], metallicFactor=finish.get('metal', base.get('metal', 0.0)),
                                                      roughnessFactor=finish.get('rough', base.get('rough', .5))),
                 doubleSided=True)
        if base.get('emit'):
            m['emissiveFactor'] = color
        out.append(m)
    return out


def split_normals(vertices, faces, sharp_deg=SHARP_DEG):
    """Glatte Normalen mit harten Kanten ab sharp_deg; Rückgabe: Punkte, Normalen, Dreiecke (Punkte je Normale aufgetrennt)."""
    v = np.asarray(vertices, float)
    f = np.asarray(faces, np.int64)
    cross = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    area = np.linalg.norm(cross, axis=1, keepdims=True)
    unit = np.divide(cross, area, out=np.zeros_like(cross), where=area > 0)
    order = np.argsort(f.ravel(), kind='stable')
    corner_face = (np.arange(f.size) // 3)[order]
    bounds = np.flatnonzero(np.diff(f.ravel()[order])) + 1
    limit = np.cos(np.radians(sharp_deg))
    normals = np.zeros((f.size, 3))
    for corners, incident in zip(np.split(order, bounds), np.split(corner_face, bounds)):
        n = unit[incident]
        mask = (n @ n.T) >= limit
        normals[corners] = mask @ cross[incident]
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, length, out=np.repeat(unit, 3, axis=0), where=length > 1e-20)
    key = np.c_[f.ravel(), np.round(normals * 512).astype(np.int64)]
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return v[f.ravel()[first]], normals[first], inverse.reshape(-1, 3)


def build(document, skin: str) -> bytes:
    roles = sorted({p['role'] for p in document['parts']})
    material = {r: i for i, r in enumerate(roles)}
    blob, views, accessors, meshes, nodes = bytearray(), [], [], [], []

    def add(array, component, kind, target):
        data = array.tobytes()
        while len(blob) % 4:
            blob.append(0)
        views.append(dict(buffer=0, byteOffset=len(blob), byteLength=len(data), target=target))
        blob.extend(data)
        a = dict(bufferView=len(views) - 1, componentType=component, count=len(array) if array.ndim > 1 else array.size, type=kind)
        if kind == 'VEC3' and target == 34962:
            a['min'], a['max'] = array.min(0).tolist(), array.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1

    def to_gltf(points):                       # Formgen x, y, z (Z oben, −Y vorn) → glTF x, z, −y
        p = np.asarray(points, float)
        return np.c_[p[:, 0], p[:, 2], -p[:, 1]]

    groups = {a['id']: [] for a in document['assemblies']}
    for part in document['parts']:
        mesh = part['mesh']
        v, n, t = split_normals(mesh['vertices'], mesh['faces'])
        prim = dict(attributes=dict(POSITION=add(to_gltf(v).astype('<f4'), 5126, 'VEC3', 34962),
                                    NORMAL=add(to_gltf(n).astype('<f4'), 5126, 'VEC3', 34962)),
                    indices=add(t.astype('<u4').ravel(), 5125, 'SCALAR', 34963), material=material[part['role']])
        meshes.append(dict(name=part['id'], primitives=[prim]))
        nodes.append(dict(name=part['id'], mesh=len(meshes) - 1,
                          extras=dict(basic_part=part['id'], basic_assembly=part['assembly'], basic_label=part.get('label', part['id']),
                                      basic_role=part['role'], basic_form=part.get('form', part['shape']), segment=part.get('segment'), side=part.get('side'))))
        groups[part['assembly']].append(len(nodes) - 1)
    children = []
    for assembly in document['assemblies']:
        nodes.append(dict(name=assembly['id'], children=groups[assembly['id']], extras=dict(basic_assembly=assembly['id'], basic_label=assembly['de'])))
        children.append(len(nodes) - 1)
    for name, anchor in document.get('anchors', {}).items():
        nodes.append(dict(name=name, translation=to_gltf([anchor['position_m']])[0].tolist(), extras=dict(socket=name, basic_part=anchor['part'])))
        children.append(len(nodes) - 1)
    nodes.append(dict(name=document['info']['id'], children=children, extras=dict(basic_model=document['info']['id'], units='m', skin=skin)))
    gltf = dict(asset=dict(version='2.0', generator='formgen.robot.glb'), scene=0, scenes=[dict(nodes=[len(nodes) - 1])], nodes=nodes, meshes=meshes,
                materials=materials(skin, roles), accessors=accessors, bufferViews=views, buffers=[dict(byteLength=len(blob))])
    head = json.dumps(gltf, separators=(',', ':'), ensure_ascii=False).encode()
    head += b' ' * (-len(head) % 4)
    while len(blob) % 4:
        blob.append(0)
    total = 12 + 8 + len(head) + 8 + len(blob)
    return struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<I4s', len(head), b'JSON') + head + struct.pack('<I4s', len(blob), b'BIN\0') + bytes(blob)
