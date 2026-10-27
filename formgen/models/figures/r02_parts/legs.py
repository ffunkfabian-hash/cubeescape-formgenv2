"""R02 Beine: Sohle, Fuß, Knöchel, Schienbein, Knie, Oberschenkel je Seite.

Zeilen (u, x_innen, x_außen, f_hinten, f_vorn) in mm für das linke Bein
(x>0); rechts gespiegelt. Gemessen mit tools/r02_measure.py (5-mm-Raster,
Front gespiegelt gemittelt, Profil A/B gemittelt, auf 1 mm gerundet).
Jede obere Gruppe beginnt 3 mm unter der Stoßzeile (eingesetzt, Annahme),
damit keine koplanaren Deckel entstehen. Beide Beine decken sich im Profil; jede Beinzeile nutzt den vollen
Profillauf. Oberhalb u980 verschmelzen Beine und Becken in der Front:
Außenkante dort gemessen, Innenkante Annahme (verdeckt hinter Becken).
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror

PROVENANCE = {
    **COMMON,
    'joints': {'kind': 'gemessen',
               'knee_u': 675, 'knee_f': 0,
               'source': 'Kniescheibe Profil A/B Ringschwerpunkt y2602,3 → u675 (Front: Knieblock u600..760, Mitte ≈ 680)'},
    'ankle': {'kind': 'gemessen', 'u': 190,
              'source': 'Profil A1/A2-Scheiben u≈217/163 (Codex-Marker), schmalste Profilzeile u190; Annahme gemeinsame Achse u190'},
    'hidden': {'kind': 'Annahme',
               'source': 'Oberschenkel-Innenkante oberhalb u980 und alle Kerntiefen hinter den Schalen; Sohlenbogen nach Profil u10 (getrennte Läufe)'},
}
PARTS = []
ANCHORS = {}


def _pair(name, role, source, shape):
    for side, s in (('l', shape), ('r', mirror(shape))):
        PARTS.append(dict(id=f'legs_{name}_{side}', assembly='legs', role=role, bevel=0,
                          provenance={'kind': 'gemessen', 'source': source}, **s))


# Sohle: Ferse und Ballen getrennt (Profil u10: Läufe −143..−33 und 33..230).
_pair('sole_heel', 'frost_frame', 'Profil u0..20 Fersenlauf; Front u5..20 Außenkante',
      rows_loft([(0, 248, 345, -140, -36), (12, 222, 358, -144, -30), (22, 200, 360, -145, -24)]))
_pair('sole_ball', 'frost_frame', 'Profil u0..20 Ballenlauf; Front u5..20',
      rows_loft([(0, 248, 345, 36, 226), (12, 222, 358, 30, 236), (22, 200, 360, 22, 238)]))

FOOT = [(20, 200, 360, -145, 238), (30, 194, 360, -145, 239), (40, 151, 359, -144, 238),
        (50, 140, 356, -141, 234), (60, 141, 351, -132, 220), (70, 141, 342, -132, 203),
        (80, 143, 337, -138, 191), (90, 150, 332, -137, 176), (100, 146, 327, -134, 161),
        (110, 147, 324, -131, 145), (120, 148, 323, -128, 129), (130, 150, 320, -125, 117),
        (140, 151, 315, -121, 113), (150, 152, 309, -117, 101)]
_pair('foot_shell', 'frost_shell', 'Front/Profil u22..150 je 10 mm', rows_loft(FOOT))

ANKLE = [(147, 156, 305, -112, 52), (160, 154, 303, -110, 44), (170, 158, 290, -95, 41),
         (180, 164, 291, -90, 40), (190, 164, 290, -86, 38), (200, 166, 288, -91, 33),
         (210, 161, 285, -100, 28), (220, 157, 283, -104, 50), (228, 156, 285, -105, 52)]
_pair('ankle_core', 'frost_frame', 'Front/Profil u150..228; dunkler Knöchelblock', rows_loft(ANKLE))

SHIN = [(225, 156, 285, -105, 52), (250, 159, 283, -101, 49), (270, 160, 281, -90, 52),
        (300, 152, 280, -92, 56), (340, 142, 280, -98, 62), (380, 126, 282, -104, 66),
        (390, 121, 282, -114, 68), (420, 109, 285, -123, 76), (450, 102, 287, -128, 85),
        (480, 97, 286, -129, 92), (510, 99, 279, -125, 91), (530, 100, 274, -115, 81),
        (550, 102, 269, -109, 77), (560, 103, 267, -105, 96), (580, 106, 261, -97, 108),
        (600, 118, 255, -87, 119)]
_pair('shin_shell', 'frost_shell', 'Front/Profil u228..600; Wadenwölbung hinten u390..530', rows_loft(SHIN))

KNEE = [(597, 118, 255, -87, 119), (610, 106, 246, -77, 124), (620, 100, 240, -74, 129),
        (640, 95, 251, -65, 138), (660, 92, 250, -70, 141), (680, 92, 248, -70, 138),
        (700, 98, 244, -65, 134), (710, 99, 240, -60, 132), (720, 93, 231, -61, 129),
        (740, 86, 236, -63, 123), (750, 83, 237, -64, 104), (760, 80, 238, -64, 115)]
_pair('knee_core', 'frost_frame', 'Front/Profil u600..760 Kniegelenk', rows_loft(KNEE))

THIGH = [(757, 80, 238, -64, 115), (770, 78, 238, -74, 119), (800, 70, 240, -79, 125),
         (840, 60, 241, -87, 132), (880, 50, 241, -99, 139), (900, 38, 240, -105, 141),
         (920, 33, 238, -110, 143), (960, 34, 235, -114, 143), (975, 32, 233, -113, 143),
         (1000, 40, 229, -109, 141), (1040, 60, 218, -106, 135)]
_pair('thigh_shell', 'frost_shell', 'Front/Profil u760..975; u1000/1040 Außenkante und Profil gemessen, Innenkante Annahme', rows_loft(THIGH))

ANCHORS['Socket_Knee_L'] = dict(at=[0, 675, 170], part='legs_knee_core_l', source='gemessen: Kniescheibe Profil, Front-Knieblockmitte x≈170')
ANCHORS['Socket_Knee_R'] = dict(at=[0, 675, -170], part='legs_knee_core_r', source='gespiegelt')
ANCHORS['Socket_Hip_L'] = dict(at=[15, 1040, 135], part='legs_thigh_shell_l', source='Annahme: Oberschenkelkopf hinter Becken, Mitte der Oberkante')
ANCHORS['Socket_Hip_R'] = dict(at=[15, 1040, -135], part='legs_thigh_shell_r', source='gespiegelt')
