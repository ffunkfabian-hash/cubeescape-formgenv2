"""Formen des Roboters → kit-Teile in Weltmaßen (mm, f/u/x). Rein numerisch; Parameter bleiben in body.py, arm.py und roboterbasic_01.py."""
from __future__ import annotations

import math

import numpy as np

from . import forms
from .rig import rot_axis

CURVED = {'loft', 'wrap', 'tube', 'cyl'}


def _plate_points(p):
    """Facettenplatte (BALLON tools/ego_build.plate_verts): Punkte der konvexen Hülle."""
    z0, z1 = p['z']
    w0, w1 = p['w']
    r0, r1 = p['r']
    h0, h1 = p['hip']
    t, rg, u = p['t'], p['ridge'], p.get('u', 0.0)

    def r(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    pts = []
    for z, w in ((z0, w0), (z1, w1)):
        for s in (-1, 1):
            pts += [(u + s * w / 2, r(z), z), (u + s * w / 2, r(z) + t, z)]
    if rg > 0:
        for z in (z0 + h0, z1 - h1):
            pts.append((u, r(z) + t + rg, z))
    ph = math.radians(p.get('phi', 0.0))
    c, s_ = math.cos(ph), math.sin(ph)
    return [(x * c - n * s_, x * s_ + n * c, z) for x, n, z in pts]


def _cylinder(p, segs=20):
    t = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    half = p['len'] / 2
    ring = np.c_[np.cos(t) * p['r'], np.sin(t) * p['r']]
    rings = [np.c_[ring, np.full(segs, s * half)] for s in (-1, 1)]
    order = {'x': [2, 1, 0], 'y': [0, 2, 1], 'z': [0, 1, 2]}[p['axis']]
    return [r[:, order] for r in rings]


def _box(p):
    d = np.array(p['d'], float) / 2
    return np.array([(a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)], float) * d


def _cut_points(c):
    """Quader dict(c, d, rz, rx) wie BALLON `_cut_boxes`: um die Mitte gedreht, dann verschoben."""
    R = rot_axis('z', c.get('rz', 0)) @ rot_axis('x', c.get('rx', 0))
    return (R @ _box(dict(d=c['d'])).T).T + np.array(c['c'], float)


def to_fux(R, o, points):
    """Segmentrahmen → Welt-mm → Autorenrahmen (f nach vorn = −Y, u = Z, x = X)."""
    w = (R @ np.asarray(points, float).T).T + o
    return np.round(np.c_[-w[:, 1], w[:, 2], w[:, 0]], 4).tolist()


def part(pid, label, seg, kind, role, p, frame_, sx, assembly, side):
    """Teil-Tupel (BALLON-Form) im Rahmen frame_=(R, o); sx=-1 spiegelt an X. Liefert ein kit-Teil."""
    R, o = frame_
    mirror = np.array((sx, 1, 1), float)
    out = dict(id=pid, assembly=assembly, role=role, label=label, bevel=0, segment=seg, side=side, form=kind)
    if kind in CURVED:
        out['smooth'] = True

    def tilt(points):
        if not p.get('rot'):
            return points
        ax, deg, piv = p['rot']
        piv = np.array(piv, float)
        if sx < 0:
            piv, deg = piv * (-1, 1, 1), (deg if ax == 'x' else -deg)
        return (rot_axis(ax, deg) @ (np.asarray(points, float) - piv).T).T + piv

    if kind in ('loft', 'wrap', 'tube'):
        V, F = {'loft': lambda: forms.loft(p['secs'], p.get('ring', 56), p.get('sub', 6)),
                'wrap': lambda: forms.wrap(p['secs'], p['a0'], p['a1'], p['t'], p.get('steps'), p.get('sub', 6)),
                'tube': lambda: forms.tube(p['path'], p['r'], p.get('segs', 14))}[kind]()
        V = np.array(V, float) * mirror
        F = [list(f) for f in F]
        out.update(shape='surface', vertices=to_fux(R, o, tilt(V)), faces=F)
        if p.get('cuts'):
            out['cuts'] = [dict(shape='hull', points=to_fux(R, o, tilt(_cut_points(c) * mirror))) for c in p['cuts']]
    elif kind == 'cyl':
        c = np.array(p.get('c', (0, 0, 0)), float) * mirror
        out.update(shape='loft', rings=[to_fux(R, o, tilt(r + c)) for r in _cylinder(p)])
    else:
        if kind == 'hull':
            pts = np.array(p['pts'], float) * mirror
        elif kind == 'plate':
            q = dict(p, phi=sx * p.get('phi', 0.0), u=sx * p.get('u', 0.0))
            pts = np.array(_plate_points(q), float)
        elif kind == 'box':
            pts = _box(p) + np.array(p.get('c', (0, 0, 0)), float) * mirror
        else:
            raise ValueError(f'{pid}: unbekannte Form {kind}')
        out.update(shape='hull', points=to_fux(R, o, tilt(pts)))
    return out
