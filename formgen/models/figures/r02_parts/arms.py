"""R02 Arme: Schulterpanzer, Oberarm, Ellbogen, Unterarmschutz, Hand je Seite.

Front-x gemessen (äußere Läufe, gespiegelt gemittelt). Profil: Rückenkante
gemessen, wo der Arm sie bildet (Schulterpanzer u1460..1680, Oberarm/
Ellbogen u1300..1460, Unterarm u1060..1300); Vorderkanten liegen in der
Rumpfsilhouette und sind nach dem Profil-Farbbild abgelesen (Annahme).
Hängende Pose: Handflächen zum Oberschenkel, Ellbogen hinter, Hand vor der
Körpermitte (Profil: Ellbogenscheibe f−76/u1331, Hand f−44..+93).
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror, disc, face_panel

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
_pair('shoulder_pad', 'frost_shell', 'Front Panzer außen u1470..1735; Profil Rückenkante u1480..1700; innen/vorn Annahme', rows_loft(PAD, .2, .3))
UPPER = [(1332, 282, 420, -146, 25), (1360, 264, 403, -128, 32), (1380, 254, 400, -128, 34),
         (1400, 244, 394, -136, 35), (1420, 234, 387, -138, 35), (1440, 224, 380, -149, 35),
         (1460, 218, 373, -158, 35), (1480, 217, 366, -165, 35), (1495, 218, 362, -160, 35)]
_pair('upper_arm', 'frost_shell', 'Front u1335..1495 Oberarmschutz; Profil Rückenkante u1360..1460', rows_loft(UPPER))
ELBOW = [(1255, 310, 480, -132, 20), (1280, 299, 466, -144, 22), (1300, 290, 450, -149, 24),
         (1320, 287, 421, -150, 25), (1335, 282, 418, -147, 25)]
_pair('elbow_core', 'frost_frame', 'Front u1255..1335 Ellbogenblock; Profil Rückenkante (Flosse) u1280..1340', rows_loft(ELBOW))
_pair('elbow_disc', 'frost_joint', PROVENANCE['elbow']['source'], disc('x', (-77, 1329), 405, 421, 38, 24))
FOREARM = [(1036, 428, 507, -100, 33), (1060, 412, 521, -130, 38), (1080, 406, 516, -136, 42),
           (1100, 393, 515, -137, 45), (1120, 381, 512, -137, 48), (1140, 369, 509, -136, 49),
           (1160, 353, 506, -133, 48), (1180, 336, 503, -140, 45), (1200, 327, 500, -138, 40),
           (1220, 319, 497, -131, 35), (1240, 312, 493, -134, 30), (1258, 307, 482, -132, 22)]
_pair('forearm_shell', 'frost_shell', 'Front u1036..1258 Unterarmschutz; Profil Rückenkante u1060..1260', rows_loft(FOREARM))
PALM = [(940, 414, 524, -40, 90), (960, 415, 531, -44, 92), (980, 418, 526, -44, 88),
        (1000, 422, 522, -40, 80), (1040, 428, 507, -30, 60)]
_pair('hand_palm', 'frost_frame', 'Front Hand u940..1040; Profil Hand −44..+93 (Farbbild)', rows_loft(PALM))
FINGERS = [(860, 443, 478, -30, 60), (880, 446, 500, -38, 75), (900, 455, 512, -40, 82),
           (920, 470, 517, -40, 85), (943, 468, 524, -40, 88)]
_pair('hand_fingers', 'frost_shell', 'Front Finger u860..940 (Lauf außen); Profil Fingerbreite', rows_loft(FINGERS))
THUMB = [(905, 418, 440, 40, 80), (920, 415, 440, 35, 90), (943, 414, 446, 30, 92)]
_pair('hand_thumb', 'frost_shell', 'Front Daumenlauf u920..960 x414..446; Profil vorn', rows_loft(THUMB))

for side, sign in (('L', 1), ('R', -1)):
    ANCHORS['Socket_Shoulder_'+side] = dict(at=[-40, 1560, sign*260], part='arms_shoulder_pad_'+side.lower(),
                                           source='Annahme: Schulterachse unter Panzerpolster (siehe upper_body)')
    ANCHORS['Socket_Elbow_'+side] = dict(at=[-77, 1329, sign*413], part='arms_elbow_core_'+side.lower(),
                                         source=PROVENANCE['elbow']['source'])
    ANCHORS['Socket_Hand_'+side] = dict(at=[25, 990, sign*470], part='arms_hand_palm_'+side.lower(),
                                       source='gemessen: Handmitte Front x≈470, Profil f≈25, u≈990')

# Gestaltung: Kristallfelder auf Polster, Oberarm und Unterarm (Front/Profil-Farbbild).
_pair('pad_crystal_side', 'frost_crystal', 'Profil: großes Kristalloval am Schulterpolster u≈1500..1725',
      face_panel(PAD, 'outer', [(1505, .3), (1505, .7), (1600, .95), (1700, .75), (1722, .4), (1640, .05), (1540, .08)]))
_pair('pad_crystal_front', 'frost_crystal', 'Front: Kristallfeld vorn am Polster u≈1520..1700',
      face_panel(PAD, 'front', [(1520, .2), (1520, .9), (1640, .95), (1700, .6), (1690, .25)]))
_pair('upper_crystal', 'frost_crystal', 'Front: Kristallstreifen Oberarm u≈1360..1480',
      face_panel(UPPER, 'front', [(1365, .35), (1365, .8), (1478, .85), (1478, .45)]))
_pair('forearm_crystal_side', 'frost_crystal', 'Profil: Kristallfeld Unterarm u≈1075..1245',
      face_panel(FOREARM, 'outer', [(1080, .25), (1075, .7), (1160, .9), (1245, .75), (1240, .3), (1160, .1)]))
_pair('forearm_crystal_front', 'frost_crystal', 'Front: Kristallfeld Unterarm außen u≈1080..1225',
      face_panel(FOREARM, 'front', [(1085, .5), (1085, .95), (1225, .9), (1210, .55)]))
