"""Varianten-Katalog Oberkörper (upper_body), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Einzelteilgrenze (catalog.assembly_of): alles aus body.torso außer `pauldron_*`/`shoulder_*` (Schulter). Bei RA02 liegen Bauchplatten und
Taillenkern am Quellknochen `spine` und zählen dort zum Becken; die Varianten hier lassen `abdomen`, `waist` und die unteren Rumpfzeilen
(z ≤ 230, aus ihnen greifen die Bauchplatten ab) darum unverändert, außer im Ersatzmodus (UB-D).
Herkunft je Zahl am Eintrag: Vorgabe = einmalig übertragen aus BALLON 14bd78d (Datei genannt), Annahme = hier gesetzt, am Vielfaltsmaß
(formgen.robot.variety.measure_parts) geprüft.
"""
from __future__ import annotations

from . import Variant

PALADIN = 'BALLON 14bd78d basic/robot/studies/b_paladin.py'
MECHANIK = 'BALLON 14bd78d basic/robot/studies/c_mechanik.py'

VARIANTS: list = [
    Variant('upper_body', 'B', 'Plate Back', '0.14',
            'Rücken nur mit Platte wie beim Paladin: kein Rückenmodul, keine Düsen und Leitungen, schlanke Seite und Draufsicht',
            dict(kind='Vorgabe', source=f'{PALADIN} upper_body(): back kind plate, z (150, 220, 360)'),
            params={'torso': {'back': {'kind': 'plate', 'z': (150, 220, 360)}}}),
    Variant('upper_body', 'C', 'Barrel Chest', '0.14',
            'Gewölbter Brustkorb: oberer Rumpf breiter und tiefer, Brust- und Rückenplatte wandern mit; Taille und Bauch bleiben',
            dict(kind='Annahme', source='Rumpfzeilen z 280/330/380 je +22/+22/+14 mm Breite, +16/+14/+8 mm Tiefe gegen RA01; z ≤ 230 unverändert'),
            params={'torso': {'core': [(30, 112, 88, -2), (120, 150, 106, 0), (230, 192, 122, -4),       # unverändert (RA01, Vorgabe a_waechter)
                                       (280, 226, 134, -6), (330, 198, 120, -8), (380, 134, 96, -10)]}}),   # Annahme
    # Ersatzmodus: in RA02 setzt das Verschiebungsfeld neue Merkmale (Wirbelsäule, geteilte Brust) nur grob an (Wirbel bis 83 mm außerhalb
    # der Figur, gemessen 0.14); die gemessenen Teile werden hier durch konstruierte ersetzt (roboterbasic_02_parameters, Ersatzmodus).
    Variant('upper_body', 'D', 'Open Frame', '0.14',
            'Offenes Skelett der Mechanik-Studie: zwei Brustplatten mit Linse, offene Wirbelsäule mit Schulterblattplatten, Bauch als Säule',
            dict(kind='Vorgabe', source=f'{MECHANIK} upper_body(): abdomen spine, rings, chest split/full/mid/t, back spine'),
            params={'torso': {'abdomen': 'spine', 'rings': (-30, -2, 26),
                              'chest': {'split': True, 'full': 130, 'mid': (200, 260, 318), 't': 9},
                              'back': {'kind': 'spine'}}},
            ra02='replace'),
]
