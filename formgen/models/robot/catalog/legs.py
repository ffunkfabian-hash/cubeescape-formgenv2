"""Varianten-Katalog Oberschenkel, Unterschenkel, Füße (thighs, shins, feet), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Einzelteilgrenzen (catalog.assembly_of nach Segment): thighs = Hüftkugel, Kern, Manschette, Schale, Fugen, Kolben und Leitung des
Oberschenkels; shins = Knie (Gelenk, Kappe, Kniekolben), Schienbein, Wade, Knöchelkolben, Stiefelschaft; feet = Knöchelgelenk, Fuß, Kappen,
Sohle. Längen LT/LS/foot_h und die Gelenkmaße knee_r, knee_len, ankle_r, ankle_len bleiben die des Typs: Bei RA02 sitzen gemessene
Kniekolben am Oberschenkel- und das Knöchelgelenk am Schienbeinknochen, eine Änderung dort träfe das Nachbarteil.
RA02 setzt neue Kolben und Leitungen über das Verschiebungsfeld nur grob an (Kniekolben 268 statt 169 mm lang, Oberschenkelkolben über
die ganze Figur, gemessen 0.14); Varianten mit neuen Kolben gehen darum in RA02 den Ersatzmodus (TH-B, SN-B).
Herkunft je Zahl am Eintrag: Vorgabe = einmalig übertragen aus BALLON 14bd78d (Datei genannt), Annahme = hier gesetzt, am Vielfaltsmaß geprüft.
Fußprofil (z, a, b, y): y ist so gesetzt, dass die Unterkante y − b wie bei RA01 bei −110…−112 mm liegt (Sohle auf −foot_h + 6).
"""
from __future__ import annotations

from . import Variant

PALADIN = 'BALLON 14bd78d basic/robot/studies/b_paladin.py'
MECHANIK = 'BALLON 14bd78d basic/robot/studies/c_mechanik.py'

VARIANTS: list = [
    # ------------------------------------------------------------------ Oberschenkel
    Variant('thighs', 'B', 'Piston Thigh', '0.14',
            'Schlanker Oberschenkel der Mechanik-Studie mit Schale nur vorn, Kolben außen hinten und Leitung',
            dict(kind='Vorgabe', source=f'{MECHANIK} legs(): thigh a/b (auf den z-Stützstellen von RA01, Annahme), thigh_shell, '
                                        'thigh_piston, thigh_cable'),
            params={'legs': {'thigh': [(-12, 56, 60, 0), (110, 70, 76, 2), (280, 62, 66, 0), (395, 50, 54, 0)], 'thigh_shell': (-56, 56),
                             'thigh_piston': True, 'thigh_cable': True}},
            ra02='replace'),
    Variant('thighs', 'C', 'Armored Thigh', '0.14',
            'Schale, die fast ganz um den Oberschenkel greift und höher ansetzt, Fuge tiefer zum Knie',
            dict(kind='Annahme', source='thigh_shell (−150, 60) statt (−112, 34) Grad, thigh_top 120 statt 150 mm, thigh_seams (250,) statt (200,)'),
            params={'legs': {'thigh_shell': (-150, 60), 'thigh_top': 120, 'thigh_seams': (250,)}}),
    Variant('thighs', 'D', 'Heavy Thigh', '0.14',
            'Kräftiger, kantiger Oberschenkel mit Wulst über der Mitte, zum Knie hin schlank',
            dict(kind='Annahme', source='thigh a/b gegen RA01 +10/+10, +16/+16, +14/+14, +6/+6 mm; thigh_ch 34 statt 26'),
            params={'legs': {'thigh': [(-12, 86, 92, 0), (110, 110, 116, 2), (280, 98, 102, 0), (395, 72, 76, 0)], 'thigh_ch': 34}}),
    # ------------------------------------------------------------------ Unterschenkel
    Variant('shins', 'B', 'Piston Shin', '0.14',
            'Offene Mechanik am Unterschenkel: zwei Kniekolben in der Kniekehle, Wadenkolben statt Wadenplatte',
            dict(kind='Vorgabe', source=f'{PALADIN} legs(): knee_pistons; {MECHANIK} legs(): calf_piston, ohne calf'),
            params={'legs': {'knee_pistons': True, 'calf': False, 'calf_piston': True}},
            ra02='replace'),
    Variant('shins', 'C', 'Heavy Greave', '0.14',
            'Beinschiene, die rundum greift, dazu eine große Kniekappe',
            dict(kind='Annahme', source='shin_shell (−130, 130) statt (−96, 96) Grad; kneecap gegen RA01 je Zeile a +6…+8, b +6…+10, '
                                        'beide Enden 6 mm weiter'),
            params={'legs': {'shin_shell': (-130, 130), 'kneecap': [(-70, 60, 66), (-24, 72, 80), (36, 74, 82), (86, 66, 72)]}}),
    Variant('shins', 'D', 'Slim Shin', '0.14',
            'Schlankes Schienbein der Mechanik-Studie mit schmaler Schale, kleiner Kniekappe und freier Wade',
            dict(kind='Vorgabe', source=f'{MECHANIK} legs(): shin a/b/y (auf den z-Stützstellen von RA01, Annahme), shin_shell, kneecap, ohne calf'),
            params={'legs': {'shin': [(30, 56, 60, 0), (140, 64, 70, -6), (280, 52, 56, -2), (385, 46, 48, 0)], 'shin_shell': (-70, 70),
                             'kneecap': [(-50, 44, 50), (-14, 52, 58), (30, 54, 60), (64, 48, 54)], 'calf': False}}),
    # ------------------------------------------------------------------ Füße
    Variant('feet', 'B', 'Round Boot', '0.14',
            'Runder, schmaler Stiefel ohne Fasen nach dem Fußprofil der Mechanik-Studie',
            dict(kind='Vorgabe', source=f'{MECHANIK} legs(): foot z/a/b; y Annahme (Unterkante wie RA01); foot_ch 0 Annahme'),
            params={'legs': {'foot_ch': 0, 'foot': [(-90, 54, 36, -76), (-24, 60, 46, -66), (70, 60, 40, -72), (160, 54, 28, -84),
                                                    (216, 44, 18, -94)]}}),
    Variant('feet', 'C', 'Wide Stomper', '0.14',
            'Breiter, langer Stampfer mit kräftiger Fase, Ferse und Zehe weiter draußen',
            dict(kind='Annahme', source='foot gegen RA01: z −20…+28 mm länger, a +8…+12, b +4 mm; y für die Unterkante; foot_ch 22 statt 14'),
            params={'legs': {'foot_ch': 22, 'foot': [(-120, 72, 48, -64), (-40, 80, 60, -52), (80, 84, 52, -60), (180, 78, 38, -74),
                                                     (250, 64, 26, -86)]}}),
    Variant('feet', 'D', 'Talon Boot', '0.14',
            'Langer, spitz zulaufender Stiefel: schmale Zehe weit vorn, hoher Rist',
            dict(kind='Annahme', source='foot gegen RA01: Zehe 40 mm länger, nach vorn auf a 30 / b 14 mm verjüngt (a −4…−24), Ferse 10 mm länger, Rist b +2 mm; y für die Unterkante'),
            params={'legs': {'foot': [(-110, 58, 46, -66), (-30, 66, 58, -54), (80, 64, 46, -66), (190, 50, 28, -84), (262, 30, 14, -98)]}}),
]
