"""Varianten-Katalog Becken (pelvis), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Einzelteilgrenze (catalog.assembly_of): alles aus body.pelvis (Kern, Gürtel, Schließe, Lendenplatte, Beintaschen, Hüftgelenk, Gürtelmodule,
Gesäßplatte). Die Hüftmaße `hip_x`, `hip_z`, `hip_r`, `hip_len` bleiben: sie hängen am Skelett, und bei RA02 sitzt das gemessene Hüftgelenk
am Oberschenkelknochen (Einzelteil thighs). RA02 hat keine gemessenen Beintaschen; dort wirken Kern, Gürtel, Lendenplatte und Gesäßplatte.
Herkunft je Zahl am Eintrag: Vorgabe = einmalig übertragen aus BALLON 14bd78d (Datei genannt), Annahme = hier gesetzt, am Vielfaltsmaß geprüft.
"""
from __future__ import annotations

from . import Variant

PALADIN = 'BALLON 14bd78d basic/robot/studies/b_paladin.py'
MECHANIK = 'BALLON 14bd78d basic/robot/studies/c_mechanik.py'

VARIANTS: list = [
    Variant('pelvis', 'B', 'Long Tasset', '0.14',
            'Lange, schmale Lendenplatte des Paladins bis weit über die Oberschenkel, schlankeres Becken, einlagige Beintaschen',
            dict(kind='Vorgabe', source=f'{PALADIN} lower_body(): pel a/b (auf den z-Stützstellen von RA01, Annahme), belt, front, side; '
                                        'side ohne layer wie dort'),
            params={'pelvis': {'pel': [(-30, 128, 88, -2), (50, 140, 92, -2), (130, 112, 80, -2), (190, 90, 70, -2)],
                               'belt': (126, 152, 116, 84), 'front': {'full': 10, 'tip': -170, 'a': 28},
                               'side': {'rows': [(-100, 204, 108, -4), (-10, 172, 100, -4), (120, 150, 94, -4)], 'span': 26, 'center': 82,
                                        'layer': False}}}),
    Variant('pelvis', 'C', 'Open Hips', '0.14',
            'Schmales, offenes Becken der Mechanik-Studie: kurze Lendenplatte, kleine Beintaschen, ohne Gesäßplatte und Gürtelmodule',
            dict(kind='Vorgabe', source=f'{MECHANIK} lower_body(): pel a/b (auf den z-Stützstellen von RA01, Annahme), belt, front, side; '
                                        'butt, belt_boxes und layer fehlen dort; hip_len nicht übernommen (Gelenk gehört zum Typ)'),
            params={'pelvis': {'pel': [(-30, 112, 78, -2), (50, 122, 84, -2), (130, 96, 72, -2), (190, 76, 62, -2)],
                               'belt': (120, 140, 100, 76), 'front': {'full': 20, 'tip': -60, 'a': 24},
                               'side': {'rows': [(-60, 176, 96, -4), (30, 150, 90, -4), (110, 136, 86, -4)], 'span': 24, 'center': 84,
                                        'layer': False},
                               'butt': False, 'belt_boxes': False}}),
    Variant('pelvis', 'D', 'Skirt Armor', '0.14',
            'Panzerrock: breite, lange Beintaschen weit um die Hüfte und eine breitere, längere Lendenplatte',
            dict(kind='Annahme', source='side.rows gegen RA01: untere Zeilen 40/20 mm tiefer, a +2…+6, b +2…+4; span 44 statt 32; front a 40, tip −120'),
            params={'pelvis': {'side': {'rows': [(-150, 240, 122, -4), (-40, 206, 112, -4), (110, 170, 102, -4)], 'span': 44},
                               'front': {'full': 20, 'tip': -120, 'a': 40}}}),
]
