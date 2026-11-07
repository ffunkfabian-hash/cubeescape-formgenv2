"""Bauteilproportionen der Basic-Typen (0.13 Gantry): vier Faktoren, die Querschnitte der Profile eines Typs skalieren.

Die Faktoren stehen in PARAMS[`proportion`] beider Typen (Standard 1,0 = keine Änderung) und werden im Register je Linie gesetzt
(data/robots.toml, `lines.params.<num>.proportion`). `apply` ersetzt nur Zahlen der Profile; Teile, IDs, Höhen z und Gelenke bleiben.
Beide Typen gehen denselben Weg: RoboterBasic-01 baut die Profile direkt, RoboterBasic-02 überträgt die Differenz als Verschiebungsfeld
auf die gemessenen Flächen (roboterbasic_02_parameters.templates). Herkunft: alle Grenzen und Anteile sind Annahme, am Vielfaltsmaß
und am Bild gesichtet (docs/robot.md › Proportionen); die Profilzahlen selbst bleiben Vorgabe aus BALLON 14bd78d.
"""
from __future__ import annotations

import copy

NEUTRAL = dict(shoulders=1.0, torso=1.0, legs=1.0, pack=1.0)
LIMITS = (0.7, 1.4)     # Annahme: außerhalb schneiden sich Schale, Kern und Gelenk sichtbar durch
WHAT = dict(shoulders='Schulterpanzer: Breite und Tiefe aller Lagen', torso='Rumpf: Kern, Kragen, Halsring und Taille',
            legs='Beine: Oberschenkel, Unterschenkel, Kniescheibe und Kniegelenk', pack='Rückenmodul: Breite und Tiefe aller Lagen')


def _grow(rows, f, at=(1, 2)):
    """Zeilen (z, a, b, …) mit Faktor f auf a und b; z und alle anderen Spalten bleiben."""
    return [type(r)(v * f if i in at else v for i, v in enumerate(r)) for r in rows]


def check(proportion):
    if set(proportion) != set(NEUTRAL):
        raise ValueError(f'proportion: Schlüssel {sorted(proportion)}, erwartet {sorted(NEUTRAL)}')
    for key, value in proportion.items():
        if not LIMITS[0] <= value <= LIMITS[1]:
            raise ValueError(f'proportion.{key} = {value}: erlaubt sind {LIMITS[0]}–{LIMITS[1]}')


def apply(params):
    """Kopie von params mit skalierten Profilen; sind alle Faktoren 1,0, kommt params unverändert (gleiches Objekt) zurück."""
    p = params['proportion']
    check(p)
    if all(v == 1.0 for v in p.values()):
        return params
    out = copy.deepcopy(params)
    f = p['shoulders']
    if f != 1.0:
        pd = out['torso']['pauldron']
        for key in ('rows', 'flare', 'flare2'):
            if pd.get(key):
                pd[key] = _grow(pd[key], f)
    f = p['torso']
    if f != 1.0:
        t = out['torso']
        t['core'] = _grow(t['core'], f)
        t['collar'] = _grow(t['collar'], f)
        t['waist'] = tuple(v * f for v in t['waist'])
        if t.get('gorget'):
            t['gorget'] = _grow([t['gorget']], f)[0]
    f = p['legs']
    if f != 1.0:
        lg = out['legs']
        lg['thigh'] = _grow(lg['thigh'], f)
        lg['shin'] = _grow(lg['shin'], f)
        lg['kneecap'] = _grow(lg['kneecap'], f)
        lg['knee_r'] = lg['knee_r'] * f
    f = p['pack']
    if f != 1.0:
        bk = out['torso']['back']
        bk['rows'] = _grow(bk['rows'], f)
    return out
