"""Fasen der Roboterteile: Kantenfase auf beliebigen geschlossenen Netzen, nach den Fugen, wie BALLONs Blender-Modifier.

BALLON 14bd78d, `basic/kit.add_bevel`: Bevel-Modifier mit Winkelgrenze 30°, zwei Segmenten und Überlappungsschutz, danach gewichtete
Normalen. `geom._bevel` kann das nur für konvexe Teile; die gewölbten Formen `loft` und `wrap` brauchen diesen Weg. Eigenes Modul statt
`geom.py`, weil geom.py in allen Waffenschlüsseln steht.

Aufbau wie Blender: Jede Fläche behält ihre Ecken, an einer Fasenkante rückt die Ecke um die Breite in die Fläche (`Sektor` = alle Flächen
einer Ecke zwischen zwei Fasenkanten), zwischen den Sektoren entsteht ein Kreisprofil, an Ecken mit drei und mehr Fasenkanten ein Deckel.
Endet eine Fasenkante, läuft das Profil in der Ecke spitz aus. Der Überlappungsschutz gilt wie in Blender je Teil: Wird eine Fläche zu
klein, schrumpft die Breite aller Kanten des Teils. Keine Blender-Parität an Ecken; die Abweichung ist gegen die Referenz gemessen
(docs/robot.md).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from .. import geom, model

ANGLE_DEG = 30.0        # Vorgabe: BALLON kit.add_bevel, angle_limit
SEGMENTS = 2            # Vorgabe: BALLON kit.add_bevel, segs
KEEP = 0.05             # Annahme: Fläche darf bis auf 5 % ihrer Normalenlänge schrumpfen, nie kippen
SLIVER_M = 2e-5         # Annahme: Dreiecke unter 0,02 mm Höhe (Reste der Booleans) zählen nicht für den Überlappungsschutz
LOCAL_PASSES = 60       # Annahme: reicht für alle Fugenteile (gemessen: höchstens 28), danach klemmt der Rest gemeinsam
MITER = 1.5             # Annahme: spitze Sektoren rücken höchstens um das 1,5-Fache der Breite (rechter Winkel: 1,41); mehr gibt Spitzen an Fugenenden
SHORT_RUN = 4.0         # Annahme: Fugenteile lassen Kantenzüge unter vierfacher Breite aus; das sind Reste einer flach streifenden Fuge, keine Kanten
CAP_PULL = 1 - 1 / math.sqrt(2)     # Deckelmitte: trifft bei drei rechten Winkeln die Kugel durch die Profile


class BevelError(ValueError):
    pass


@dataclass
class Result:
    vertices: np.ndarray
    faces: np.ndarray
    soft: np.ndarray    # Indizes der Fasenflächen: untereinander immer glatt, wie harden_normals
    width: float        # wirksame Breite nach dem Überlappungsschutz (Median über die Ecken)
    edges: int          # gefaste Kanten


def _unit(v):
    length = np.linalg.norm(v, axis=-1, keepdims=True)
    return np.divide(v, length, out=np.zeros_like(v), where=length > 1e-15)


def _half_edges(f):
    half = {}
    for i, tri in enumerate(f.tolist()):
        for c in range(3):
            key = (tri[c], tri[(c + 1) % 3])
            if key in half:
                raise BevelError('Netz nicht mannigfaltig: Kante doppelt')
            half[key] = i
    if any((b, a) not in half for a, b in half):
        raise BevelError('Netz nicht geschlossen')
    return half


def _selected(v, f, half, angle_deg):
    normals = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    area = np.linalg.norm(normals, axis=1)
    normals = _unit(normals)
    keys = [k for k in half if k[0] < k[1]]
    first = np.array([half[k] for k in keys])
    second = np.array([half[k[::-1]] for k in keys])
    dot = np.einsum('ij,ij->i', normals[first], normals[second])
    flat = (area[first] < 1e-14) | (area[second] < 1e-14)
    picked = (dot < math.cos(math.radians(angle_deg))) & ~flat
    return {k for k, p in zip(keys, picked) if p}, normals


def _without_short_runs(v, selected, shortest):
    """Nur zusammenhängende Kantenzüge ab Länge `shortest` behalten."""
    if not selected:
        return selected
    edges = np.array(sorted(selected))
    graph = coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(v), len(v)))
    labels = connected_components(graph, directed=False)[1][edges[:, 0]]
    lengths = np.bincount(labels, np.linalg.norm(v[edges[:, 0]] - v[edges[:, 1]], axis=1))
    return {tuple(e) for e, label in zip(edges.tolist(), labels) if lengths[label] >= shortest}


def _fans(tris, vertex, faces, half):
    """Flächen um eine Ecke gegen den Uhrzeigersinn, je Fächer eine Liste (Fläche, Nachbarecke der Ausgangskante); mehrere bei Berührung in einem Punkt."""
    todo = set(faces)
    fans = []
    while todo:
        start = face = min(todo)
        fan = []
        while face in todo:
            todo.remove(face)
            tri = tris[face]
            c = tri.index(vertex)
            fan.append((face, tri[(c + 1) % 3]))
            face = half[vertex, tri[c - 1]]
        if face != start:
            raise BevelError('Fächer nicht geschlossen')
        fans.append(fan)
    return fans


def _sector_offset(v, normals, vertex, first, last):
    """Einheitsverschiebung eines Sektors: rückt von beiden Grenzkanten um 1 in die Fläche (Gehrung)."""
    (f0, n0), (f1, n1) = first, last
    d0, d1 = _unit(v[n0] - v[vertex]), _unit(v[n1] - v[vertex])
    m0, m1 = np.cross(normals[f0], d0), np.cross(normals[f1], -d1)
    denominator = 1 + float(m0 @ m1)
    if denominator < 2 / MITER ** 2:
        return _unit(m0 + m1) * MITER
    return (m0 + m1) / denominator


def _flip_widths(v, tris, offsets):
    """Je Dreieck die Breite, ab der es zu klein wird: Normale(w) · Normale(0) = KEEP · |Normale(0)|², quadratisch in w; sonst unendlich."""
    p, d = v[tris], offsets
    e1, e2, g1, g2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0], d[:, 1] - d[:, 0], d[:, 2] - d[:, 0]
    n0 = np.cross(e1, e2)
    longest = np.max([np.linalg.norm(e1, axis=1), np.linalg.norm(e2, axis=1), np.linalg.norm(p[:, 2] - p[:, 1], axis=1)], axis=0)
    ok = (np.abs(d).sum(axis=(1, 2)) > 0) & (np.linalg.norm(n0, axis=1) > SLIVER_M * np.maximum(longest, 1e-12))
    a = np.einsum('ij,ij->i', n0, np.cross(g1, g2))
    b = np.einsum('ij,ij->i', n0, np.cross(e1, g2) + np.cross(g1, e2))
    c = (1 - KEEP) * np.einsum('ij,ij->i', n0, n0)
    disc = b * b - 4 * a * c
    with np.errstate(divide='ignore', invalid='ignore'):        # stabile Form: (−b ± √D)/2a löscht sich aus, wenn a nur Rauschen ist
        q = -(b + np.where(b >= 0, 1.0, -1.0) * np.sqrt(np.maximum(disc, 0))) / 2
        roots = np.stack([q / a, c / q])
    roots[:, disc < 0] = np.inf
    roots[~np.isfinite(roots) | (roots <= 0)] = np.inf
    roots[:, ~ok] = np.inf
    return roots.min(axis=0)


def _local_scale(v, f, index, offset, width):
    """Überlappungsschutz je Ecke: Die Ecken eines zu kleinen Dreiecks rücken weniger, der Rest des Teils behält die volle Breite."""
    scale = np.ones(len(offset))
    moved = index >= 0
    for _ in range(LOCAL_PASSES):
        limit = _flip_widths(v, f, np.where(moved[..., None], offset[index] * scale[index, None], 0.0)) / width
        bad = limit < 1
        if not bad.any():
            return scale
        for c in range(3):
            rows = bad & moved[:, c]
            np.minimum.at(scale, index[rows, c], scale[index[rows, c]] * limit[rows])
    return scale * min(1.0, float(limit.min()))


def apply(vertices, faces, width, segments=SEGMENTS, angle_deg=ANGLE_DEG, local=False) -> Result:
    """Fast alle Kanten über angle_deg um width (Meter, Rücksprung entlang der Fläche, wie Blenders Offset).

    local=True klemmt je Ecke statt je Teil: für Teile mit Fugen, deren Boolean Kleinstkanten hinterlässt; Blender arbeitet dort auf
    N-Ecken und behält die volle Breite (gemessen an der Referenz, docs/robot.md).
    """
    v = np.asarray(vertices, float)
    f = np.asarray(faces, np.int64)
    half = _half_edges(f)
    selected, normals = _selected(v, f, half, angle_deg)
    if local:
        selected = _without_short_runs(v, selected, SHORT_RUN * width)
    if not selected:
        return Result(v, f, np.zeros(0, np.int64), 0.0, 0)
    feature = {i for e in selected for i in e}
    tris = f.tolist()
    around = {}
    for i, tri in enumerate(tris):
        for vertex in tri:
            if vertex in feature:
                around.setdefault(vertex, []).append(i)

    # Sektoren: je Fächer die Flächen zwischen zwei Fasenkanten. corner[(Fläche, Ecke)] = Sektor, Sektor ist (Ecke, Einheitsverschiebung).
    sectors, corner, rings = [], {}, []
    for vertex, faces_here in around.items():
        for fan in _fans(tris, vertex, faces_here, half):
            marks = [i for i, (_, n) in enumerate(fan) if (min(vertex, n), max(vertex, n)) in selected]
            if len(marks) == 1:                   # Kante endet hier: Profil läuft spitz aus
                sectors.append((vertex, np.zeros(3)))
                for face, _ in fan:
                    corner[face, vertex] = len(sectors) - 1
                rings.append((vertex, [(fan[marks[0]][1], len(sectors) - 1, len(sectors) - 1)]))
            elif marks:
                ids = []
                for a, b in zip(marks, marks[1:] + marks[:1]):
                    run = [fan[i % len(fan)] for i in range(a, b + (len(fan) if b <= a else 0))]
                    close = fan[b][1]
                    sectors.append((vertex, _sector_offset(v, normals, vertex, run[0], (run[-1][0], close))))
                    ids.append(len(sectors) - 1)
                    for face, _ in run:
                        corner[face, vertex] = ids[-1]
                # Kante marks[j] liegt zwischen Sektor j−1 (davor) und Sektor j (danach)
                rings.append((vertex, [(fan[m][1], ids[j], ids[j - 1]) for j, m in enumerate(marks)]))

    offset = np.array([s[1] for s in sectors])
    index = np.full(f.shape, -1)
    for (face, vertex), s in corner.items():
        index[face, tris[face].index(vertex)] = s
    if local:
        scale = _local_scale(v, f, index, offset, width)
    else:
        limit = _flip_widths(v, f, np.where(index[..., None] >= 0, offset[index], 0.0))
        scale = np.full(len(offset), min(1.0, float(limit.min()) / width))

    points = list(v)
    sector_vertex = {}
    for s, (vertex, x) in enumerate(sectors):
        if not x.any():
            sector_vertex[s] = vertex
        else:
            sector_vertex[s] = len(points)
            points.append(v[vertex] + width * scale[s] * x)
    out = [[sector_vertex[index[i, c]] if index[i, c] >= 0 else tri[c] for c in range(3)] for i, tri in enumerate(tris)]
    base = len(out)

    profiles = {}

    def profile(vertex, axis, after, before):
        """Punkte von Sektor `after` nach Sektor `before`; bei zwei Fasenkanten teilen sich beide Kanten dasselbe Profil."""
        if after == before:
            return [sector_vertex[after]] * (segments + 1)
        key = (min(after, before), max(after, before))
        if key not in profiles:
            left, right = np.array(points[sector_vertex[key[0]]]), np.array(points[sector_vertex[key[1]]])
            tip = v[vertex] + axis * float(((left + right) / 2 - v[vertex]) @ axis)
            center = left + right - tip
            mids = []
            for i in range(1, segments):
                t = math.pi / 2 * i / segments
                mids.append(len(points))
                points.append(center + (left - center) * math.cos(t) + (right - center) * math.sin(t))
            profiles[key] = [sector_vertex[key[0]], *mids, sector_vertex[key[1]]]
        line = profiles[key]
        return line if after == key[0] else line[::-1]

    ends = {}
    for vertex, ring in rings:
        directions = [_unit(v[n] - v[vertex]) for n, _, _ in ring]
        for (n, after, before), d in zip(ring, directions):
            ends[vertex, n] = profile(vertex, _unit(directions[0] - directions[1]) if len(ring) == 2 else d, after, before)
        if len(ring) >= 3:                        # Deckel: Ring gegen den Uhrzeigersinn, je Kante rückwärts durch das Profil
            loop = []
            for (n, _, _) in ring:
                loop += ends[vertex, n][::-1][:-1]
            ring_points = np.array([points[i] for i in loop])
            mean = ring_points.mean(axis=0)
            center = len(points)
            points.append(mean + (v[vertex] - mean) * CAP_PULL)
            out += [[center, a, b] for a, b in zip(loop, loop[1:] + loop[:1])]

    for a, b in selected:
        at_a, at_b = ends[a, b], ends[b, a][::-1]     # beide vom Sektor der Fläche a→b zum Sektor der Fläche b→a
        for i in range(segments):
            quad = [at_b[i], at_a[i], at_a[i + 1], at_b[i + 1]]
            quad = [p for j, p in enumerate(quad) if p != quad[j - 1]]
            if len(quad) >= 3:
                out.append(quad[:3])
            if len(quad) == 4:
                out.append([quad[0], quad[2], quad[3]])

    used = np.unique(np.array(out))
    lookup = np.full(len(points), -1)
    lookup[used] = np.arange(len(used))
    return Result(np.array(points)[used], lookup[np.array(out)], np.arange(base, len(out)), width * float(np.median(scale)), len(selected))


def evaluate(document):
    """Modelldokument → ausgewertetes Dokument: `geom.evaluate` baut Formen und Fugen, die Fasen folgen hier; jedes Teil meldet `bevel_status`."""
    source = model.normalize(document)
    widths = {p['id']: p['bevel'] for p in source['parts']}
    for part in source['parts']:
        part['bevel'] = 0                 # fehlt das Feld, fast geom.evaluate selbst mit 1 mm
    result = geom.evaluate(source, booleans=True, bevels=False)
    for part in result['parts']:
        part['bevel'] = widths[part['id']]
        if not part['bevel']:
            continue
        mesh = part['mesh']
        try:
            done = apply(mesh['vertices'], mesh['faces'], part['bevel'] / 1000, local=bool(part.get('cuts')))
        except BevelError as e:
            part['bevel_status'] = 'unsupported'
            result['warnings'].append(f"{part['id']}: Fase nicht ausgewertet: {e}")
            continue
        hard = mesh['hard'][0] if mesh['hard'] else 1
        part['mesh'] = dict(vertices=done.vertices.tolist(), faces=done.faces.tolist(), hard=[hard] * len(done.faces), soft=done.soft.tolist())
        part['bevel_status'] = 'mesh_bevel' if done.edges else 'no_feature_edges'
        part['bevel_effective_mm'] = round(done.width * 1000, 4)
        part['bounds_m'] = [done.vertices.min(axis=0).tolist(), done.vertices.max(axis=0).tolist()]
        part['counts'] = dict(vertices=len(done.vertices), faces=len(done.faces), triangles=len(done.faces))
    meshes = [np.asarray(p['mesh']['vertices']) for p in result['parts']]
    every = np.concatenate(meshes)
    result['bounds_m'] = [every.min(axis=0).tolist(), every.max(axis=0).tolist()]
    total = sum(len(p['mesh']['faces']) for p in result['parts'])
    result['counts'].update(vertices=len(every), faces=total, triangles=total)
    return result
