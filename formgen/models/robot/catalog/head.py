"""Varianten-Katalog Kopf (head), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Alle Kopfvarianten wirken nur über PARAMS['helmet'] (formgen/models/robot/helmet.py): Gruppenfelder (Haube, Visier, Kiefer, Seiten,
Kragen, Hinterkopf) und Aufsätze. Beide Typen setzen sie gleich um (RA01 Helm H 80, RA02 gemessener Kopf, ra02 = 'field').
Herkunft der Zahlen je Variante in `origin`; „BALLON“ heißt Commit 14bd78d, basic/robot/studies (einmalig übertragen, nur gelesen).
"""
from __future__ import annotations

from . import Variant

VARIANTS: list = [
    Variant(assembly='head', letter='B', name='Crest Guard', since='0.14',
            idea='Hohe Paradehaube mit Kamm und Kammleiste über die Mitte, Hinterkopf länger',
            origin=dict(kind='Annahme', source='Idee BALLON b_paladin (Helm mit Kamm, hz 1,16 → Haubenhöhe 1,16 Vorgabe); Kamm 30 mm, '
                                               'Tiefe 1,06, Breite 0,96, Hinterkopf 10 mm Annahme am Vielfaltsmaß'),
            params={'helmet': dict(dome=dict(height=1.16, width=0.96, depth=1.06), back=dict(out=10.0), crest=30.0)}),
    Variant(assembly='head', letter='C', name='Sensor Pod', since='0.14',
            idea='Flache, breite Sensorhaube mit Kameralinse auf der Stirn, vorgezogenem Visier und zwei Antennen',
            origin=dict(kind='Annahme', source='Idee BALLON c_mechanik (Kameralinse r 13, Antenne r 3 mit rund 140 mm Mast → Vorgabe); '
                                               'Haubenhöhe 0,86, Breite 1,08, Tiefe 1,04, Visier 10 mm vor Annahme am Vielfaltsmaß'),
            params={'helmet': dict(dome=dict(height=0.86, width=1.08, depth=1.04), visor=dict(forward=10.0), lens=13.0, antennas=140.0)}),
    Variant(assembly='head', letter='D', name='Heavy Jaw', since='0.14',
            idea='Breiter, vorgeschobener Kiefer mit Ohrauslegern, kräftigem Kragen und Halsleitungen',
            origin=dict(kind='Annahme', source='Idee BALLON b_paladin (Ohrausleger ear=out Faktor 1, Halsleitungen r 5,5 → Vorgabe); '
                                               'Kiefer 1,16 breit, 14 mm vor, 6 mm tiefer, Seiten 6 mm, Kragen 1,08 Annahme am Vielfaltsmaß'),
            params={'helmet': dict(jaw=dict(width=1.16, forward=14.0, drop=6.0), sides=dict(out=6.0), collar=dict(width=1.08), ears=1.0,
                                   cables=5.5)}),
]
