"""Kopfvarianten (0.14 Kitbash): Helmgruppen, Verformung je Gruppe und Aufsatzteile für RA01 (Helm H 80) und RA02 (gemessener Kopf).

Schnittstelle: PARAMS['helmet'] beider Typen ist eine Kopie von NEUTRAL; ra01/ra02 bekommen die fertigen Kopfteile in Weltmaßen (mm, f/u/x)
und geben sie verformt und ergänzt zurück. Mit NEUTRAL kommt dieselbe Liste unverändert zurück (RA01/RA02 bytegleich).

Verformung: Je Gruppe (GROUPS) ein glattes Verschiebungsfeld im Kopfrahmen (x rechte Körperseite, y vorn, z oben, Ursprung Halspunkt).
Das Feld hängt nur vom Ort ab, nicht vom Teil: Wo zwei Teile verschiedener Gruppen aneinanderstoßen, wandern sie gleich, nichts klafft.
Die Gruppen setzen die Anker (Augenlinie, Kopfhöhe, -tiefe und -breite) aus den gemessenen Teilen und bestimmen, welche Felder ein Teil
erfährt: Der Hals (`neck`) bleibt fest, eine abgesetzte Gruppe (ISOLATED, RA02-Kragen auf dem Rumpf) nur ihr eigenes Feld. Alle Felder
sind spiegelgleich zur Mittelebene x = 0; Übergänge sind Smoothsteps, Faktoren und Wege so begrenzt (LIMITS), dass das Feld nicht faltet.

Aufsätze: Kamm, Antennenpaar, Ohrausleger, Stirnlinse, Halsleitungen aus den Bausteinen von body.py/kit.py, an der verformten Haube
eingemessen (Sonden auf den Punkten), Paare aus einer Geometrie der rechten Seite, links gespiegelt (kit.part sx = −1).
Herkunft: Formen und Maße der Aufsätze nach BALLON 14bd78d (basic/robot/studies/body.py `head`, b_paladin, c_mechanik), Lage und
Übergänge Annahme am Entwurf; die Anker sind je Aufruf an den Teilen gemessen.
"""
from __future__ import annotations

import copy

import numpy as np

from . import kit
from .body import light, tube

NEUTRAL: dict = dict(
    dome=dict(height=1.0, width=1.0, depth=1.0),     # Haube: Höhe über der Augenlinie, Breite und Tiefe ab Augenunterkante (Faktoren)
    visor=dict(forward=0.0),                         # Visier: mm nach vorn (Augenband, vordere Hälfte)
    jaw=dict(width=1.0, forward=0.0, drop=0.0),      # Maske/Kiefer: Breite unter den Augen (Faktor), mm nach vorn, mm nach unten
    sides=dict(out=0.0),                             # Seitengehäuse: mm nach außen je Seite
    collar=dict(width=1.0),                          # Kragen: Faktor um die Halsachse
    back=dict(out=0.0),                              # Hinterkopf mit Rückenbox: mm nach hinten
    crest=0.0,        # Kamm über die Haubenmitte: Höhe über der Haube, mm (0 = ohne)
    antennas=0.0,     # Antennenpaar an den Schläfen: Mastlänge, mm (0 = ohne)
    ears=0.0,         # Ohrausleger: Faktor auf BALLONs Maß (0 = ohne)
    lens=0.0,         # Stirn-/Kameralinse über dem Visier: Radius der Linse, mm (0 = ohne)
    cables=0.0,       # Halsleitungen vom Kragen zum Seitengehäuse: Radius, mm (0 = ohne)
)
# Annahme: in diesen Grenzen bleibt das Feld faltenfrei (Test: Jacobi-Determinante) und der Kopf im Kopfbereich ± 150 mm.
LIMITS = dict(factor=(0.8, 1.25), shift=(-20.0, 30.0), crest=(0.0, 60.0), antennas=(0.0, 180.0), ears=(0.0, 1.4), lens=(0.0, 24.0),
              cables=(0.0, 9.0))

# Gruppen der Kopfteile je Typ (RA01: Teile-ID aus helmet_h80.json bzw. body.head; RA02: source_object). Jedes Kopfteil genau einmal.
GROUPS = {
    1: dict(
        dome=('helmet_crown', 'helmet_shell', 'helmet_brim', 'helmet_forehead_plate_r', 'helmet_forehead_plate_l', 'helmet_screws_upper'),
        visor=('helmet_visor_r', 'helmet_visor_l', 'helmet_mask_gap_a', 'helmet_mask_gap_b'),
        jaw=('helmet_mouth_insert', 'helmet_mouth_rail_r', 'helmet_mouth_rail_l', 'helmet_chin', 'helmet_jaw_r', 'helmet_jaw_l',
             'helmet_jaw_insert_r', 'helmet_jaw_insert_l', 'helmet_jaw_insert_slot_r', 'helmet_jaw_insert_slot_l', 'helmet_screws_chin'),
        sides=('helmet_cheek_r', 'helmet_cheek_l', 'helmet_screws_side', *(f'helmet_detail_{i:02d}' for i in range(1, 15)),
               'helmet_collar_slot_floor_r', 'helmet_collar_slot_floor_l', 'helmet_collar_panel_floor_r', 'helmet_collar_panel_floor_l',
               'helmet_collar_socket_floor_r', 'helmet_collar_socket_floor_l'),
        collar=('helmet_collar', 'helmet_neck_ring', 'helmet_core', 'helmet_rear_panel', 'helmet_collar_dip_plate', 'helmet_detail_15'),
        back=('helmet_back_box_mount', 'helmet_back_box', 'helmet_detail_16', 'helmet_detail_17', 'helmet_detail_18',
              'helmet_back_box_connector_a', 'helmet_back_box_connector_b', 'helmet_screws_back_box'),
        neck=('neck', 'neck_ring', 'neck_trim'),          # body.head, kommt nicht durch ra01: Hals und Halsanker bleiben
    ),
    2: dict(
        dome=('Helmet',),
        visor=('Visor', 'VisorFrame', 'R4_VisorCyan'),
        jaw=('Jaw', 'ChinVent', 'R4_ChinInnerSeal'),
        sides=tuple(f'EarDisc_{s}{k}' for s in 'RL' for k in ('Cap', 'Disc', 'Hub', 'HubBolt1', 'HubBolt2', 'HubBolt3', 'HubBolt4',
                                                               'Recess', 'Ring')),
        collar=('Collar', 'CollarBolt_L', 'CollarBolt_R'),
        back=(),                                          # RA02 hat keine Rückenbox; das Feld wirkt auf den Hinterkopf der Haube
        neck=('Neck', 'NeckRing1', 'NeckRing2'),
    ),
}
FIXED = 'neck'
ISOLATED = {1: (), 2: ('collar',)}       # RA02: der Kragen sitzt auf dem Rumpf, 8 mm unter dem Kopf (gemessen), eigenes Feld
EYES = {1: ('helmet_visor_r', 'helmet_visor_l'), 2: ('R4_VisorCyan',)}       # Augenlinie: Anker der Felder
CABLE_ROOT = {1: 'helmet_neck_ring', 2: 'Collar'}                            # Halsleitungen beginnen in diesem Teil
FIELD_GROUPS = ('dome', 'visor', 'jaw', 'sides', 'collar', 'back')
ATTACHMENTS = ('crest', 'antennas', 'ears', 'lens', 'cables')
PROVENANCE = dict(
    field=dict(kind='Annahme', source='Kopfvariante: Verschiebungsfeld je Helmgruppe im Kopfrahmen, formgen/models/robot/helmet.py; '
                                      'Anker an den gemessenen Teilen'),
    crest=dict(kind='Annahme', source='Kamm über die Haubenmitte nach BALLON 14bd78d body.head crest (b_paladin, Q-D2-PARADE); '
                                      'Basisbreite ±8 mm wie dort ±8° am Kopf, Spitze ±4 mm und Kammleiste Annahme; an der Haube eingemessen'),
    antennas=dict(kind='Annahme', source='Antenne nach BALLON 14bd78d body.head antenna (c_mechanik): Mast r 3 mm, Spitze; als Paar, '
                                         'Halter und Lage an der Schläfe Annahme; an der Haube eingemessen'),
    ears=dict(kind='Vorgabe', source='Ohrausleger nach BALLON 14bd78d body.head ear=out (b_paladin): Kasten 34×52×30 mm bei Breite/2 + 12, '
                                     'Kappe 10×44×22 mm bei Breite/2 + 31, Fasen 3/2 mm; Höhe und Lage an der Haube eingemessen (Annahme)'),
    lens=dict(kind='Annahme', source='Kameralinse nach BALLON 14bd78d body.head ear=lens (c_mechanik, Linse r 13 in Medaillon r 26), '
                                     'hier mittig auf der Stirn; Stufen 5/2 mm Annahme; an der Stirn eingemessen'),
    cables=dict(kind='Annahme', source='Halsleitung nach BALLON 14bd78d body.head neck_cables (b_paladin, r 5,5 mm), Bahn vom Kragen '
                                       'außen zum Seitengehäuse Annahme; an den Teilen eingemessen'),
)


# ------------------------------------------------------------------ Schnittstelle

def ra01(parts, params, frames):
    """Helmteile von RA01 (aus helmet_h80.json, schon in Weltmaßen) → verformt und ergänzt; frames wie roboterbasic_01.rig_of."""
    if params['helmet'] == NEUTRAL:
        return parts
    R, o, _, _ = frames['head']
    return _build(1, parts, params['helmet'], R, o, key=lambda p: p['id'])


def ra02(parts, params, frames):
    """Alle Teile von RA02 (Weltmaßen); verformt und ergänzt nur die Teile mit assembly == 'head'. frames wie roboterbasic_02._frames."""
    if params['helmet'] == NEUTRAL:
        return parts
    R, o, _, _ = frames['head']
    heads = [p for p in parts if p['assembly'] == 'head']
    built = iter(_build(2, heads, params['helmet'], R, o, key=lambda p: p['source_object']))
    out = [next(built) if p['assembly'] == 'head' else p for p in parts]
    return out + list(built)


# ------------------------------------------------------------------ Gruppen und Anker

def group_of(num, key):
    """Gruppe eines Kopfteils (Schlüssel wie GROUPS); unbekannt ist ein Fehler, nie eine stille Zuordnung."""
    for group, names in GROUPS[num].items():
        if key in names:
            return group
    raise ValueError(f'Kopfteil {key!r} von RA{num:02d} in keiner Helmgruppe (helmet.GROUPS)')


def check(P):
    """Parameter von helmet: gleiche Schlüssel wie NEUTRAL, Werte in LIMITS."""
    if set(P) != set(NEUTRAL) or any(set(P[g]) != set(NEUTRAL[g]) for g in FIELD_GROUPS):
        raise ValueError(f'helmet: Schlüssel {sorted(P)}, erwartet {sorted(NEUTRAL)}')
    for g in FIELD_GROUPS:
        for k, v in P[g].items():
            lo, hi = LIMITS['factor'] if NEUTRAL[g][k] == 1.0 else LIMITS['shift']
            if not lo <= v <= hi:
                raise ValueError(f'helmet.{g}.{k} = {v} außerhalb {lo}–{hi}')
    for k in ATTACHMENTS:
        lo, hi = LIMITS[k]
        if not lo <= P[k] <= hi:
            raise ValueError(f'helmet.{k} = {P[k]} außerhalb {lo}–{hi}')


def _local(R, o, fux):
    """Welt f/u/x → Kopfrahmen (x rechts, y vorn, z oben); Umkehrung von kit.to_fux."""
    f = np.asarray(fux, float).reshape(-1, 3)
    return (np.c_[f[:, 2], -f[:, 0], f[:, 1]] - o) @ R


def _points(shape):
    """Alle Punkte einer Form ohne Schnitte (Anker und Sonden messen die sichtbare Außenform)."""
    out = [np.asarray(shape[k], float).reshape(-1, 3) for k in ('points', 'vertices') if k in shape]
    out += [np.asarray(r, float).reshape(-1, 3) for r in shape.get('rings', [])]
    out += [_points(s) for s in shape.get('items', [])]
    return np.concatenate(out) if out else np.empty((0, 3))


def _map(shape, fn):
    """Kopie der Form mit allen Punkten (auch Schnitte und Unterformen) durch fn: (n, 3) f/u/x → Liste f/u/x."""
    out = dict(shape)
    for k in ('points', 'vertices'):
        if k in shape:
            out[k] = fn(np.asarray(shape[k], float))
    if 'rings' in shape:
        out['rings'] = [fn(np.asarray(r, float)) for r in shape['rings']]
    for k in ('items', 'cuts'):
        if k in shape:
            out[k] = [_map(s, fn) for s in shape[k]]
    return out


def landmarks(num, local):
    """Anker der Felder aus den Teilen (lokal, {Schlüssel: Punkte}): Augenband E0/E1, Kopf oben T, unten B, vorn F, hinten K, halbe Breite W."""
    groups = {g: [k for k in GROUPS[num][g] if k in local] for g in GROUPS[num]}
    core = np.concatenate([local[k] for g in ('dome', 'visor', 'jaw', 'sides') for k in groups[g]])
    eyes = np.concatenate([local[k] for k in EYES[num]])
    return dict(E0=float(eyes[:, 2].min()), E1=float(eyes[:, 2].max()), T=float(core[:, 2].max()), B=float(core[:, 2].min()),
                F=float(core[:, 1].max()), K=float(core[:, 1].min()), W=float(np.abs(core[:, 0]).max()))


# ------------------------------------------------------------------ Felder

def _s(v, a, b):
    """Smoothstep von a (0) nach b (1)."""
    t = np.clip((v - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _ramp(v, a, b):
    """Stammfunktion des Smoothsteps: 0 unter a, Steigung 0 → 1 zwischen a und b, darüber v − b + (b − a)/2; monoton."""
    t = np.clip((v - a) / (b - a), 0.0, 1.0)
    return np.where(v > b, v - b + (b - a) / 2, (b - a) * (t ** 3 - t ** 4 / 2))


def _band(v, a, b, c, d):
    return _s(v, a, b) * (1 - _s(v, c, d))


def fields(P, L):
    """Verschiebungsfeld je Gruppe: {Gruppe: f(p) → d}, p und d (n, 3) im Kopfrahmen. Übergangsbreiten als Anteil von Kopfhöhe H,
    -tiefe D und Untergesicht lo (Augenunterkante − Kopfunterkante): Annahme am Entwurf, faltenfrei in LIMITS."""
    H, D, lo = L['T'] - L['B'], L['F'] - L['K'], L['E0'] - L['B']
    yc = (L['F'] + L['K']) / 2

    def dome(p):
        x, y, z = p.T
        w = _s(z, L['E0'], L['E1'] + 0.15 * H)
        g = P['dome']
        return np.c_[(g['width'] - 1) * x * w, (g['depth'] - 1) * (y - yc) * w,
                     (g['height'] - 1) * _ramp(z, L['E1'] - 0.1 * H, L['E1'] + 0.1 * H)]

    def visor(p):
        x, y, z = p.T
        w = _band(z, L['E0'] - 0.12 * H, L['E0'], L['E1'], L['E1'] + 0.12 * H) * _s(y, yc, L['F'] - 0.2 * D)
        return np.c_[0 * x, P['visor']['forward'] * w, 0 * z]

    def jaw(p):
        x, y, z = p.T
        low = 1 - _s(z, L['B'] + 0.45 * lo, L['E0'])
        front = _s(y, yc - 0.25 * D, yc + 0.1 * D)
        g = P['jaw']
        return np.c_[(g['width'] - 1) * x * low, g['forward'] * low * front, -g['drop'] * low * front]

    def sides(p):
        x, y, z = p.T
        w = _s(np.abs(x), 0.6 * L['W'], 0.9 * L['W']) * _band(z, L['B'], L['B'] + 0.15 * H, L['E1'], L['E1'] + 0.15 * H)
        return np.c_[P['sides']['out'] * np.sign(x) * w, 0 * y, 0 * z]

    def collar(p):
        x, y, z = p.T
        w = (P['collar']['width'] - 1) * (1 - _s(z, L['B'] + 0.35 * lo, L['B'] + 0.75 * lo))
        return np.c_[x * w, y * w, 0 * z]

    def back(p):
        x, y, z = p.T
        w = (1 - _s(y, L['K'] + 0.15 * D, L['K'] + 0.4 * D)) * _s(z, L['B'] + 0.25 * H, L['B'] + 0.45 * H)
        return np.c_[0 * x, -P['back']['out'] * w, 0 * z]
    return dict(dome=dome, visor=visor, jaw=jaw, sides=sides, collar=collar, back=back)


def displacement(num, group, P, L):
    """Feld, das ein Teil der Gruppe erfährt: fest (Hals) → None, abgesetzt → nur das eigene, sonst die Summe der gemeinsamen Felder."""
    if group == FIXED:
        return None
    f = fields(P, L)
    used = (group,) if group in ISOLATED[num] else tuple(g for g in FIELD_GROUPS if g not in ISOLATED[num])
    return lambda p: sum(f[g](p) for g in used)


# ------------------------------------------------------------------ Bau

def _build(num, parts, P, R, o, key):
    check(P)
    keys = [key(p) for p in parts]
    groups = [group_of(num, k) for k in keys]
    local = {k: _local(R, o, _points(p)) for k, p in zip(keys, parts)}
    L = landmarks(num, local)

    def world(points):
        w = np.asarray(points, float) @ R.T + o
        return np.round(np.c_[-w[:, 1], w[:, 2], w[:, 0]], 4).tolist()
    out, cloud = [], []
    for p, k, g in zip(parts, keys, groups):
        d = displacement(num, g, P, L)
        if d is None:
            out.append(p)
            continue

        def fn(points, d=d):
            q = _local(R, o, points)
            return world(q + d(q))
        moved = _map(p, fn)
        moved.setdefault('transform_provenance', copy.deepcopy(PROVENANCE['field']))
        out.append(moved)
        q = _local(R, o, _points(p))
        cloud.append((g, k, q + d(q)))
    return out + attachments(num, P, L, cloud, R, o, parent=_parent(num, parts, keys))


def _parent(num, parts, keys):
    """RA02: Aufsätze hängen an der Haube (parent_part wie die gemessenen Kopfteile); RA01 kennt kein parent_part."""
    if num == 1:
        return None
    return parts[keys.index(GROUPS[2]['dome'][0])]['id']


# ------------------------------------------------------------------ Aufsätze

class Probe:
    """Sonden auf der verformten Kopfform (lokal): Höhe der Mittellinie, seitliche Ausdehnung, Stirn- und Rückfläche.
    Das Fenster wächst, bis es Punkte trifft; seitlich zählt |x| beider Seiten, dadurch bleiben Paare spiegelgleich."""

    def __init__(self, points):
        self.p = points

    def _pick(self, mask_of, pick):
        for grow in (1, 2, 4, 8):
            m = mask_of(grow)
            if m.any():
                return float(pick(self.p[m]))
        raise ValueError('Kopfsonde ohne Treffer')

    def top(self, y):
        return self._pick(lambda g: (np.abs(self.p[:, 0]) < 12 * g) & (np.abs(self.p[:, 1] - y) < 5 * g), lambda q: q[:, 2].max())

    def side(self, y, z):
        return self._pick(lambda g: (np.abs(self.p[:, 1] - y) < 12 * g) & (np.abs(self.p[:, 2] - z) < 10 * g),
                          lambda q: np.abs(q[:, 0]).max())

    def front(self, z):
        return self._pick(lambda g: (np.abs(self.p[:, 0]) < 12 * g) & (np.abs(self.p[:, 2] - z) < 6 * g), lambda q: q[:, 1].max())


def attachments(num, P, L, cloud, R, o, parent=None):
    """Aufsatzteile (kit-Teile in Welt f/u/x), Mittelteile einmal, Paare rechts gebaut und links gespiegelt."""
    H, D, lo = L['T'] - L['B'], L['F'] - L['K'], L['E0'] - L['B']
    yc = (L['F'] + L['K']) / 2
    shell = Probe(np.concatenate([q for g, _, q in cloud if g not in ISOLATED[num]]))
    center, pair = [], []
    if P['crest']:                      # Kamm von der Stirn über den Scheitel zum Hinterkopf, oben Kammleiste
        h, us = P['crest'], np.linspace(0, 1, 11)
        ys = L['F'] - 0.22 * D + us * (L['K'] + 0.18 * D - (L['F'] - 0.22 * D))
        tops = [shell.top(y) for y in ys]
        rise = 0.25 + 0.75 * np.sin(np.pi * us) ** 0.7
        fin = [(sx * 8, y, t - 10) for y, t in zip(ys, tops) for sx in (-1, 1)]
        fin += [(sx * 4, y, t + h * r) for y, t, r in zip(ys, tops, rise) for sx in (-1, 1)]
        edge = [(sx * 2, y, t + h * r + dz) for y, t, r in list(zip(ys, tops, rise))[1:-1] for sx in (-1, 1) for dz in (-4, 2.5)]
        center += [('head_crest', 'Helmkamm', 'head', 'hull', 'shell', dict(pts=fin, bevel=2.0), 'crest'),
                   ('head_crest_edge', 'Kammleiste', 'head', 'hull', 'trim', dict(pts=edge, bevel=0.8), 'crest')]
    if P['antennas']:                   # Mast nach oben und leicht nach hinten, Halter in der Haube, Statuslicht an der Spitze
        n = P['antennas']
        y, z = L['K'] + 0.38 * D, L['E1'] + 0.35 * (L['T'] - L['E1'])
        x = shell.side(y, z)
        foot = (x + 4, y, z + 6)
        tip = (foot[0] + 0.12 * n, y - 0.28 * n, foot[2] + 0.95 * n)
        pair += [(f'head_antenna_{{k}}_mount', 'Antennenhalter', 'head', 'box', 'dark_metal', dict(d=(12, 20, 18), c=(x + 2, y, z), bevel=2.0),
                  'antennas'),
                 (*tube('head_antenna_{k}', 'Antenne', 'head', 'dark_metal', [foot, tip], 3.0, segs=10), 'antennas')]
        pair += [(*q, 'antennas') for q in light('head_antenna_{k}_tip', 'head', tip, axis='z', r=4.0)]
    if P['ears']:                       # Ohrausleger knapp unter der Augenlinie, Kappe außen
        e = P['ears']
        y, z = yc - 0.06 * D, L['E0'] - 0.04 * H
        x = shell.side(y, z)
        pair += [('head_ear_{k}', 'Ohrausleger', 'head', 'box', 'dark_metal', dict(d=(34 * e, 52 * e, 30 * e), c=(x + 12 * e, y, z), bevel=3.0),
                  'ears'),
                 ('head_ear_{k}_cap', 'Auslegerkappe', 'head', 'box', 'shell', dict(d=(10 * e, 44 * e, 22 * e), c=(x + 31 * e, y, z), bevel=2.0),
                  'ears')]
    if P['lens']:                       # Kameralinse mittig über dem Visier, drei Stufen nach vorn
        r, z = P['lens'], L['E1'] + 0.1 * H
        y = shell.front(z)
        center += [('head_lens_housing', 'Linsengehäuse', 'head', 'cyl', 'dark_metal', dict(axis='y', r=r + 5, len=10, c=(0, y + 1, z)), 'lens'),
                   ('head_lens_ring', 'Linsenring', 'head', 'cyl', 'trim', dict(axis='y', r=r + 2, len=12, c=(0, y + 2, z)), 'lens'),
                   ('head_lens', 'Kameralinse', 'head', 'cyl', 'anodized', dict(axis='y', r=r, len=14, c=(0, y + 3, z)), 'lens'),
                   ('head_lens_pupil', 'Linsenkern', 'head', 'cyl', 'energy', dict(axis='y', r=0.4 * r, len=15, c=(0, y + 3.5, z)), 'lens')]
    if P['cables']:                     # Leitung aus dem Kragen außen herum ins Seitengehäuse hinter dem Ohr, Tüllen an beiden Enden
        r = P['cables']
        root = next(q for g, k, q in cloud if k == CABLE_ROOT[num])
        y0 = L['K'] + 0.3 * D
        z0 = float(root[:, 2].min() + root[:, 2].max()) / 2
        near = root[(np.abs(root[:, 1] - y0) < 30) & (np.abs(root[:, 2] - z0) < 10)]
        s0 = float(np.abs((near if len(near) else root)[:, 0]).max())
        y2, z2 = y0 + 0.08 * D, L['E0'] - 0.05 * H
        s2 = shell.side(y2, z2)
        z1 = (z0 + z2) / 2
        s1 = max(s0, shell.side((y0 + y2) / 2, z1))
        path = [(s0 - 6, y0, z0), (s0 + r * 0.5, y0, z0 + 0.15 * (z2 - z0)), (s1 + r + 5, (y0 + y2) / 2 - 0.05 * D, z1),
                (s2 + r * 0.5 + 2, y2, z2 - 0.15 * (z2 - z0)), (s2 - 6, y2, z2)]

        def lerp(a, b, t):
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
        pair += [(*tube('head_cable_{k}', 'Halsleitung', 'head', 'rubber', path, r, segs=12), 'cables'),
                 (*tube('head_cable_{k}_plug_a', 'Leitungstülle', 'head', 'dark_metal', [path[0], lerp(path[0], path[1], 0.7)], r * 1.35, segs=12),
                  'cables'),
                 (*tube('head_cable_{k}_plug_b', 'Leitungstülle', 'head', 'dark_metal', [path[-1], lerp(path[-1], path[-2], 0.7)], r * 1.35,
                        segs=12), 'cables')]
    out = []
    for pid, de, seg, form, role, p, what in center:
        out.append(_part(num, pid, de, seg, form, role, p, (R, o), 1, 'C', what, parent))
    for k, sx, side in (('r', 1, 'R'), ('l', -1, 'L')):
        for pid, de, seg, form, role, p, what in pair:
            out.append(_part(num, pid.format(k=k), de, seg, form, role, p, (R, o), sx, side, what, parent))
    return out


def _part(num, pid, de, seg, form, role, p, frame_, sx, side, what, parent):
    out = kit.part(pid, de, seg, form, role, p, frame_, sx, 'head', side)
    out['provenance'] = copy.deepcopy(PROVENANCE[what])
    if num == 2:            # wie die Konstruktorteile von RA02 (roboterbasic_02_parameters.templates): Quelle Parameter, an der Haube
        out.update(source_object=f'Parameter_helmet_{pid}', parent_part=parent)
    return out
