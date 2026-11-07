"""Varianten-Katalog Oberarm, Unterarm, Hände (upper_arms, forearms, hands), 0.14 Kitbash; Regeln und Schnittstelle in catalog/__init__.py. Die Grundform A steht dort.

Wirkung nur über Parameter: Oberarm über `upper_arm` (body.upper_arm, beide Typen), Unterarm über `forearm` und Hände über `hand`
(arm.FOREARM, arm.HAND). Gelenke, Skelett, Haltung und Armlängen bleiben die des Typs. RA02 setzt alle Varianten im Modus `field` um
(roboterbasic_02_parameters.templates): Profiländerungen als Verschiebungsfeld auf die gemessenen, über ASSOCIATIONS gebundenen Teile,
neue Konstruktorteile (Kolben, Armschild, Stellzylinder, Knöchelpanzer, Krallen) kalibriert am nächsten gemessenen Geschwisterteil
desselben Segments. Die gemessenen Finger von RA02 sind nicht gebunden; Handvarianten wirken dort über Handfläche, Handrücken und
Aufsätze im Segment hand, Fingermaße nur in RA01 (`types`).

Herkunft der Zahlen: BALLON 14bd78d einmalig übertragen, wo genannt (Lesereferenz, keine Laufzeitbindung); sonst Annahme, entworfen
gegen die Grundmaße in arm.py/body.py und am Vielfaltsmaß (formgen.robot.variety.measure_parts) geprüft.
"""
from __future__ import annotations

from formgen.models.robot import arm

from . import Variant

_BALLON = 'BALLON 14bd78d'
_PW, _PT, _KZ = arm.HAND['palm_w'], arm.HAND['palm_t'], arm.HAND['knuckle_z']

VARIANTS: list = [
    # ------------------------------------------------------------------ Oberarm (body.upper_arm: rows (z, a, b, y), shell Winkel, Fase)
    # Bizepskolben (body.upper_arm piston, seitlich in +X) und schmale Schale in beiden Typen: seit 0.14 spiegelt RA02 Feld und Aufsätze am
    # linken Arm (roboterbasic_02_parameters._frame_for), vorher saß der Kolben links hinten statt vorn (Bericht 0.14, Unteragent Arme).
    Variant('upper_arms', 'B', 'Piston Arm', '0.14',
            'Schlanker Mechanik-Oberarm; in RA01 mit schmaler Schale und offenem Bizepskolben an der Vorderseite',
            dict(kind='Vorgabe', source=f'{_BALLON} basic/robot/studies/c_mechanik.py arm_extra (rows, shell, ch, piston); '
                                        'Schulterkugel ball 52 nicht übernommen, sie gehört zum Einzelteil Schulter'),
            params=dict(upper_arm=dict(rows=[(10, 50, 48, 0), (150, 54, 52, 0), (290, 44, 42, 0)], ch=16, shell=(-80, 80), piston=True))),
    Variant('upper_arms', 'C', 'Heavy Shell', '0.14',
            'Schwerer Panzerarm: dicker Körper, Schale greift fast ganz um den Oberarm',
            dict(kind='Annahme', source='entworfen: Querschnitt +15–20 % gegen upper_arm.rows der Grundform, Schale ±150° statt ±110°, '
                                        'Fase 24; Prinzip „Panzer umschließt das Glied“ aus arm.py (Q-D2-ARM)'),
            params=dict(upper_arm=dict(rows=[(10, 72, 70, 0), (150, 84, 80, 4), (290, 66, 62, 0)], shell=(-150, 150), ch=24))),
    Variant('upper_arms', 'D', 'Runner Arm', '0.14',
            'Schlanker dunkler Läuferarm ohne Cremeschale, nur Körper und Fuge',
            dict(kind='Annahme', source=f'Prinzip aus {_BALLON} basic/robot/studies/b_paladin.py (ARM_DROP upper_shell: „Oberarm dunkel '
                                        'und schlank“); Querschnitt entworfen, ≈ 0,78 × Grundform, Fase 14'),
            params=dict(upper_arm=dict(rows=[(10, 48, 46, 0), (150, 55, 53, 0), (290, 46, 44, 0)], shell=None, ch=14))),
    # ------------------------------------------------------------------ Unterarm (arm.FOREARM)
    Variant('forearms', 'B', 'Shield Bracer', '0.14',
            'Schwere Armschiene: breite Schildplatte mit Grat über der Unterarmschale',
            dict(kind='Annahme', source=f'entworfen: Platte z 40–236 mm, 136→104 mm breit (Schale 112→68), 9 mm dick, Grat 10; Prinzip '
                                        f'„geschlossene Cremeschale“ aus {_BALLON} basic/arms/studies/b_panzer.py'),
            params=dict(forearm=dict(guard=dict(z=(40, 236), w=(136, 104), lift=3, t=9, ridge=10, hip=(40, 30))))),
    Variant('forearms', 'C', 'Ram Bracer', '0.14',
            'Mechanik-Unterarm: Stellzylinder mit blanker Kolbenstange an der Innenseite bis zur Stulpe',
            dict(kind='Vorgabe', source=f'{_BALLON} basic/arms/studies/c_mechanik.py actuator (z 24–186, r 17) und actuator_rod '
                                        '(z 180–268, r 7,5); Lage y −52 unter dem Körper Annahme'),
            params=dict(forearm=dict(ram=dict(z=(24, 186), r=17, y=-52, rod_z=(180, 268), rod_r=7.5)))),
    Variant('forearms', 'D', 'Stocky Bracer', '0.14',
            'Gedrungener Unterarm: kräftiger Querschnitt, weit aufgeweitete Stulpe greift über die Hand',
            dict(kind='Annahme', source=f'entworfen: Querschnitt × 1,22 (girth); Stulpe bis z 318 aufgeweitet nach {_BALLON} '
                                        'basic/arms/studies/b_panzer.py CUFF (z 236–320, „Stulpe greift über die Hand“), Maße entworfen'),
            params=dict(forearm=dict(girth=1.22, cuff=((76, -34, 38, 17, 250), (98, -45, 49, 22, 318)),
                                     cuff_trim=(79, -35.5, 39.5, 17.5, 248, 252)))),
    # ------------------------------------------------------------------ Hände (arm.HAND)
    Variant('hands', 'B', 'Armored Fist', '0.14',
            'Panzerfaust: großer Knöchelpanzer über Knöcheln und Fingerwurzeln, dicke Rückenschale, Wangen an der Handfläche',
            dict(kind='Annahme', source=f'Prinzip aus {_BALLON} basic/arms/studies/b_panzer.py („dicke Rückenschale und Knöchelschutz“); '
                                        'Maße entworfen: Panzer KNUCKLE_Z −30…+14 mm, PALM_W +16/+12, 11 mm dick; Rückenschale 9 statt 5 mm'),
            params=dict(hand=dict(back=dict(t=9, ridge=12),
                                  armor=dict(z=(-30, 14), w=(16, 12), lift=2, t=11, ridge=8, hip=(8, 8), cheek=(10, 20, 80))))),
    Variant('hands', 'C', 'Claw Hand', '0.14',
            'Klauenhand: drei gebogene Krallen vom Handrücken weit über die Finger hinaus',
            dict(kind='Annahme', source='entworfen: drei Krallen bei x −22/0/22 mm (Fingerteilung ≈ 20 mm), Fuß z 30–70, Spitze '
                                        'KNUCKLE_Z + 110 mm, 40 mm zur Handfläche gebogen'),
            params=dict(hand=dict(claws=dict(x=(-22, 0, 22), base=(30, 70), reach=110, w=12, t=10, drop=40)))),
    Variant('hands', 'D', 'Precision Hand', '0.14',
            'Schlanke Präzisionshand: schmale, flache, lange Handfläche; in RA01 auch schlanke, längere Finger',
            dict(kind='Annahme', source='entworfen: Handfläche 0,8 × breit, 0,8 × dick, +14 mm lang (KNUCKLE_Z mit); RA01 Finger 14 mm '
                                        'breit, Teilung 16 mm, Glieder × 1,15; RA02 behält seine gemessenen Finger'),
            params=dict(hand=dict(palm_w=_PW * 0.8, palm_t=_PT * 0.8, palm_len=arm.HAND['palm_len'] + 14, knuckle_z=_KZ + 14,
                                  back=dict(w0=56))),
            types={1: dict(hand=dict(finger_w=14.0, finger_d=arm.HAND['finger_d'] * 0.85, finger_x=(24, 8, -8, -24),
                                     finger_scale=tuple(round(s * 1.15, 4) for s in arm.HAND['finger_scale'])))}),
]
