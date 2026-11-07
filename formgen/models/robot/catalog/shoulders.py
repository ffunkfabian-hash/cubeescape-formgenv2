"""Varianten-Katalog Schulter (shoulders), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Einzelteilgrenze (catalog.assembly_of): Teile `pauldron_*` und `shoulder_*`, gebaut in body.torso (Rumpfrahmen), dazu die Schulterkugel des
Oberarms. Die Varianten setzen nur `torso.pauldron`; Gelenkpunkt (SX, SZ, joint_r) und Skelett bleiben die des Typs.
RA02: `grooves` steht dort aus (gemessene Fugen); geänderte Fugen bauen den gemessenen Panzer neu, darum stehen sie nur unter types[1].
Herkunft je Zahl am Eintrag: Vorgabe = einmalig übertragen aus BALLON 14bd78d (Datei genannt), Annahme = hier gesetzt, am Vielfaltsmaß geprüft.
"""
from __future__ import annotations

from . import Variant

PALADIN = 'BALLON 14bd78d basic/robot/studies/b_paladin.py'
MECHANIK = 'BALLON 14bd78d basic/robot/studies/c_mechanik.py'

VARIANTS: list = [
    Variant('shoulders', 'B', 'Paladin Guard', '0.14',
            'Großer runder Panzer des Paladins, stärker geneigt, mit zwei Lagen über dem Oberarm (RA02 bekommt die Lagen neu)',
            dict(kind='Vorgabe', source=f'{PALADIN} upper_body(): pauldron n, rows, flare, flare2, flare_span, band, med, tilt, ch, grooves'),
            params={'torso': {'pauldron': dict(
                n=2.8, rows=[(224, 102, 120, -6, 44), (274, 118, 132, -6, 32), (329, 116, 128, -6, 12), (374, 104, 116, -6, -2),
                             (400, 66, 80, -6, -14)],
                flare=[(154, 110, 126, -6, 52), (230, 98, 112, -6, 44)], flare2=[(96, 98, 114, -6, 58), (170, 88, 104, -6, 50)],
                flare_span=100, band=250, med=(244, 24), tilt=22, ch=42)}},
            types={1: {'torso': {'pauldron': {'grooves': (294, 308)}}}}),
    Variant('shoulders', 'C', 'Compact Cap', '0.14',
            'Kompakte runde Schulterkappe der Mechanik-Studie ohne Lagen, flacher geneigt; der Oberarm liegt frei',
            dict(kind='Vorgabe', source=f'{MECHANIK} upper_body(): pauldron rows, band, med, tilt, ch, grooves; flare/flare2 fehlen dort'),
            params={'torso': {'pauldron': dict(
                rows=[(258, 84, 98, -6, 30), (298, 96, 108, -6, 20), (348, 90, 102, -6, 4), (378, 66, 80, -6, -8), (392, 34, 44, -6, -16)],
                flare=None, flare2=None, band=284, med=(270, 22), tilt=12, ch=26)}},
            types={1: {'torso': {'pauldron': {'grooves': (314, 328)}}}}),
    Variant('shoulders', 'D', 'Wide Guard', '0.14',
            'Breiter, waagrecht ausladender Panzer: jede Lage bis 12 mm breiter und 8–18 mm weiter außen, kaum geneigt',
            dict(kind='Annahme', source='pauldron.rows gegen RA01: a +12…+2, b +2, Versatz dx +18…+8 mm; tilt 8 statt 16 Grad'),
            params={'torso': {'pauldron': dict(
                rows=[(250, 116, 126, -6, 58), (290, 132, 136, -6, 48), (340, 128, 132, -6, 28), (375, 104, 114, -6, 8), (392, 62, 78, -6, -6)],
                tilt=8)}}),
]
