"""Skelett von RoboterBasic-01: Segmentrahmen in Welt-mm (Blender-Achsen: X links, Y hinten, Z oben), Arme in Ruhehaltung.

Übertragen aus BALLON 14bd78d (basic/robot/__init__.py, tools/robot_build.py, tools/ego_build.py); rein numerisch, ohne Blender.
Ein Rahmen ist (R, o): Spalten von R sind die Segmentachsen x, y, z, o der Ursprung. Rechtes Bein und rechter Arm ungespiegelt,
linke Teile im Segmentrahmen an X gespiegelt.
"""
from __future__ import annotations

import math

import numpy as np


def frame_axes(A, B, hint):
    """z von A nach B, y = hint senkrecht dazu, x = y × z; Listen wie in BALLON `_frame`."""
    z = [b - a for a, b in zip(A, B)]
    L = sum(v * v for v in z) ** 0.5
    z = [v / L for v in z]
    d = sum(h * v for h, v in zip(hint, z))
    y = [h - d * v for h, v in zip(hint, z)]
    L = sum(v * v for v in y) ** 0.5
    y = [v / L for v in y]
    x = [y[1] * z[2] - y[2] * z[1], y[2] * z[0] - y[0] * z[2], y[0] * z[1] - y[1] * z[0]]
    return x, y, z


def frame(A, B, hint):
    return np.array(frame_axes(A, B, hint), float).T


def from_direction(z, hint):
    return frame((0, 0, 0), tuple(np.asarray(z, float)), tuple(np.asarray(hint, float)))


def rot_axis(axis, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return np.array({'x': [[1, 0, 0], [0, c, -s], [0, s, c]], 'y': [[c, 0, s], [0, 1, 0], [-s, 0, c]],
                     'z': [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis], float)


def _norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def body_segments(sk):
    """Rumpfsegmente: name → (R, o, Seite, Typ); sk ist das Ergebnis von body.skeleton."""
    S = [('pelvis', sk['PELVIS'], sk['WAIST'], (0, -1, 0), 'C'),
         ('torso', sk['WAIST'], sk['NECK'], sk['TORSO_HINT'], 'C'),
         ('head', sk['NECK'], sk['HEAD_TOP'], sk['HEAD_HINT'], 'C')]
    for side, (hip, knee, ankle, toe) in sk['JOINTS'].items():
        S += [(f'thigh_{side}', hip, knee, (0, -1, 0), side), (f'shin_{side}', knee, ankle, (0, -1, 0), side),
              (f'foot_{side}', ankle, toe, (0, 0, 1), side)]
    return {name: (frame(A, B, hint), np.array(A, float), side, name.split('_')[0]) for name, A, B, hint, side in S}


def shoulders(sk):
    x, y, z = frame_axes(sk['WAIST'], sk['NECK'], sk['TORSO_HINT'])
    out = {}
    for side, sign in (('R', 1), ('L', -1)):
        lx, ly, lz = sk['SHOULDER_LOCAL']
        out[side] = tuple(round(sk['WAIST'][i] + sign * lx * x[i] + ly * y[i] + lz * z[i], 3) for i in range(3))
    return out


def arm_segments(sk, arm, pose):
    """Arme in Haltung `pose` (upper, fore: Richtungen je Glied; fingers: Name aus arm.FINGER_POSES). Rückgabe wie body_segments."""
    a, b = arm.UPPER_MM, arm.FORE_MM
    fp = arm.FINGER_POSES[pose['fingers']]
    out = {}
    for side, S in shoulders(sk).items():
        S = np.array(S, float)
        wx = -1 if side == 'R' else 1                     # Weltseite (rechts −X)
        sx = 1 if side == 'R' else -1                     # Spiegelung im Segmentrahmen
        u, f = pose['upper'], pose['fore']
        ud, fd = _norm((wx * -u[0], u[1], u[2])), _norm((wx * -f[0], f[1], f[2]))
        E = S + ud * a
        Wp = E + fd * b
        Rh = from_direction(fd, (wx, 0, 0))               # Handrücken nach außen, Daumen nach vorn

        def put(seg, R, o):
            out[f'arm_{side}_{seg}'] = (R, np.asarray(o, float), side, seg)
        put('hand', Rh, Wp)
        scale = arm.FINGER_SCALE
        for i, fx in enumerate(arm.FINGER_X):
            R, o = Rh, Wp + Rh @ np.array((sx * fx, 0, arm.KNUCKLE_Z))
            for j, L0 in enumerate(arm.FINGER_LINKS):
                R = R @ rot_axis('x', fp['f'][i][j])
                put(f'f{i}_{j}', R, o)
                o = o + R @ np.array((0, 0, L0 * scale[i]))
        tb = np.array((sx * arm.THUMB_BASE[0], arm.THUMB_BASE[1], arm.THUMB_BASE[2]))
        td = (sx * arm.THUMB_DIR[0], arm.THUMB_DIR[1], arm.THUMB_DIR[2])
        flex, spread, tip = fp['t']
        R = Rh @ from_direction(td, (0, 1, 0)) @ rot_axis('y', -sx * (spread - 30))
        o = Wp + Rh @ tb
        for j, Lk in enumerate(arm.THUMB_LINKS):
            R = R @ rot_axis('x', [flex, tip * 0.6, tip][j])
            put(f't_{j}', R, o)
            o = o + R @ np.array((0, 0, Lk))
        put('upper', from_direction(E - S, (wx, 0, 0)), S)
        put('fore', from_direction(Wp - E, Rh[:, 1]), E)
    return out
