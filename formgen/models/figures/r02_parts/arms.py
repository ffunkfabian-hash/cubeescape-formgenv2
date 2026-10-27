"""R02 Arme: Schulterpanzer, Oberarm, Ellbogen, Unterarmschutz, Hand je Seite.

Front-x gemessen (äußere Läufe, gespiegelt gemittelt). Profil: Rückenkante
gemessen, wo der Arm sie bildet (Schulterpanzer u1460..1680, Oberarm/
Ellbogen u1300..1460, Unterarm u1060..1300); Vorderkanten liegen in der
Rumpfsilhouette und sind nach dem Profil-Farbbild abgelesen (Annahme).
Hängende Pose: Handflächen zum Oberschenkel, Ellbogen hinter, Hand vor der
Körpermitte (Profil: Ellbogenscheibe f−76/u1331, Hand f−44..+93).
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, mirror, plate_span, projected
from formgen.models.figures.r02_parts.arms_regions import REGIONS
from formgen.models.figures.r02_parts.arms_sections import SECTIONS

PROVENANCE = {
    **COMMON,
    'elbow': {'kind': 'gemessen', 'at': [-77, 1329],
              'source': 'Profil Ellbogenscheibe: Codex-Marker visible-disc-center E (SVG 1560/390 → f−77, u1329), im Farbbild bestätigt (Mitte ≈ f−76/u1331), r≈38; Front-Schätzung u1321'},
    'front_edges': {'kind': 'Annahme',
                    'source': 'Profil-Farbbild: Polster vorn ≈+87, Oberarm ≈+35, Unterarm +22..+49, Hand bis +93'},
}
PARTS = []
ANCHORS = {}


def _pair(name, role, source, shape):
    for side, s in (('l', shape), ('r', mirror(shape))):
        PARTS.append(dict(id=f'arms_{name}_{side}', assembly='arms', role=role, bevel=0,
                          provenance={'kind': 'gemessen', 'source': source}, **s))


PAD = [(1470, 372, 421, -150, 20), (1490, 300, 416, -172, 45), (1500, 215, 411, -177, 60),
       (1520, 210, 413, -182, 75), (1560, 206, 408, -186, 85), (1600, 205, 403, -185, 87),
       (1640, 205, 394, -180, 80), (1660, 205, 377, -174, 72), (1680, 204, 358, -151, 60),
       (1700, 205, 339, -142, 50), (1720, 210, 315, -125, 30), (1735, 240, 290, -95, 5)]
UPPER = [(1332, 282, 420, -146, 25), (1360, 264, 403, -128, 32), (1380, 254, 400, -128, 34),
         (1400, 244, 394, -136, 35), (1420, 234, 387, -138, 35), (1440, 224, 380, -149, 35),
         (1460, 218, 373, -158, 35), (1480, 217, 366, -165, 35), (1495, 218, 362, -160, 35)]
ELBOW = [(1255, 310, 480, -132, 20), (1280, 299, 466, -144, 22), (1300, 290, 450, -149, 24),
         (1320, 287, 421, -150, 25), (1335, 282, 418, -147, 25)]
FOREARM = [(1036, 428, 507, -100, 33), (1060, 412, 521, -130, 38), (1080, 406, 516, -136, 42),
           (1100, 393, 515, -137, 45), (1120, 381, 512, -137, 48), (1140, 369, 509, -136, 49),
           (1160, 353, 506, -133, 48), (1180, 336, 503, -140, 45), (1200, 327, 500, -138, 40),
           (1220, 319, 497, -131, 35), (1240, 312, 493, -134, 30), (1258, 307, 482, -132, 22)]
PALM = [(940, 414, 524, -40, 90), (960, 415, 531, -44, 92), (980, 418, 526, -44, 88),
        (1000, 422, 522, -40, 80), (1040, 428, 507, -30, 60)]
FINGERS = [(860, 443, 478, -30, 60), (880, 446, 500, -38, 75), (900, 455, 512, -40, 82),
           (920, 470, 517, -40, 85), (943, 468, 524, -40, 88)]
THUMB = [(905, 418, 440, 40, 80), (920, 415, 440, 35, 90), (943, 414, 446, 30, 92)]

# Projizierte Platten (Pilot): Hüllen aus den gemessenen Zeilen, Plattenumrisse
# aus den Farbregionen der Front, des Rückens und des linken Profils (B).
DRAWING = {'front': REGIONS['front'], 'back': REGIONS['back'], 'outer': REGIONS['profile-b']}
SEGMENTS = [('shoulder_pad', PAD, .2, .3, 'Front Panzer außen u1470..1735; Profil Rückenkante u1480..1700; innen/vorn Annahme'),
            ('upper_arm', UPPER, .22, .22, 'Front u1335..1495 Oberarmschutz; Profil Rückenkante u1360..1460'),
            ('elbow', ELBOW, .22, .22, 'Front u1255..1335 Ellbogenblock; Profil Rückenkante (Flosse) u1280..1340'),
            ('forearm', FOREARM, .22, .22, 'Front u1036..1258 Unterarmschutz; Profil Rückenkante u1060..1260'),
            ('hand_palm', PALM, .22, .22, 'Front Hand u940..1040; Profil Hand −44..+93 (Farbbild)'),
            ('hand_fingers', FINGERS, .22, .22, 'Front Finger u860..940 (Lauf außen); Profil Fingerbreite'),
            ('hand_thumb', THUMB, .22, .22, 'Front Daumenlauf u920..960 x414..446; Profil vorn')]
# Gestapelte Segmente: Platten enden ≥ 0,55 mm vor dem eingesetzten Nachbarn
# (Rastermitte, common.plate_span); die Fuge zeigt den dunklen Kern wie die
# Tuschelinie des Blatts. Nachbarn: (unten, oben) als erste/letzte Zeile.
STACK = {'hand_fingers': (None, PALM[0][0]), 'hand_thumb': (None, PALM[0][0]),
         'hand_palm': (FINGERS[-1][0], FOREARM[0][0]), 'forearm': (PALM[-1][0], ELBOW[0][0]),
         'elbow': (FOREARM[-1][0], UPPER[0][0]), 'upper_arm': (ELBOW[-1][0], PAD[0][0])}
for name, rows, cx, cf, source in SEGMENTS:
    clip = plate_span(rows[0][0], rows[-1][0], *STACK.get(name, (None, None)))
    core, plates = projected(rows, DRAWING, ('front', 'back', 'outer'), cx=cx, cf=cf, sections=SECTIONS[name], clip=clip)
    _pair(name+'_core', 'frost_frame', source+'; Querschnitt gemessen an KI-Referenz (arms_sections.py), eingepasst auf die Blattzeilen; Kern 4 mm unter der Hülle (Annahme), sichtbar in den Fugen', core)
    for role, shape in plates.items():
        _pair(name+'_'+role.removeprefix('frost_'), role,
              'gemessen: Farbregionen Front/Rücken/Profil B (tools/r02_regions.py) auf der 4-mm-Außenschicht von '+name, shape)

for side, sign in (('L', 1), ('R', -1)):
    ANCHORS['Socket_Shoulder_'+side] = dict(at=[-40, 1560, sign*260], part='arms_shoulder_pad_core_'+side.lower(),
                                           source='Annahme: Schulterachse unter Panzerpolster (siehe upper_body)')
    ANCHORS['Socket_Elbow_'+side] = dict(at=[-77, 1329, sign*413], part='arms_elbow_core_'+side.lower(),
                                         source=PROVENANCE['elbow']['source'])
    ANCHORS['Socket_Hand_'+side] = dict(at=[25, 990, sign*470], part='arms_hand_palm_core_'+side.lower(),
                                       source='gemessen: Handmitte Front x≈470, Profil f≈25, u≈990')
