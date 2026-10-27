"""R02 Oberkörper: Bauch, Brustpanzer, Rückenplatte, Kragen/Schal, Brustkern.

Frontbreiten gemessen; Profil vorn gemessen (u1300..1710). Der Rumpfrücken ist
im Profil überall von Oberarm/Schulterpanzer verdeckt: Rückentiefe ist
Annahme (−112 Bauch, −122 Brust). Schulterpanzer gehören zu arms.
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror, disc, face_panel

PROVENANCE = {
    **COMMON,
    'hidden': {'kind': 'Annahme',
               'source': 'Rumpfrücken −112/−122 verdeckt; Brustbreite u1500..1660 hinter Schulterpanzern ±200 (Nachbarzeilen 1500/1680)'},
    'core': {'kind': 'gemessen', 'at': [0, 1543, 0], 'r_outer': 49, 'r_inner': 33,
             'source': 'Front Brustkern Mitte u≈1543, Ring r≈49, blaue Scheibe r≈33 mm (Farbbild, k=2000/3665)'},
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, shape, sides=False):
    items = [('_l', shape), ('_r', mirror(shape))] if sides else [('', shape)]
    for suffix, s in items:
        PARTS.append(dict(id='upper_body_'+name+suffix, assembly='upper_body', role=role, bevel=0,
                          provenance={'kind': 'gemessen', 'source': source}, **s))


def _sym(rows, cx=.22, cf=.22):
    return rows_loft([(u, -w, w, fb, ff) for u, w, fb, ff in rows], cx, cf)


ABDOMEN = [(1262, -150, 150, -110, 126), (1290, -132, 132, -112, 136), (1300, -130, 130, -112, 143),
           (1320, -131, 131, -112, 145), (1340, -138, 138, -114, 146), (1362, -156, 156, -116, 144)]
_part('abdomen_core', 'frost_frame', 'Front u1290..1340 ±130..138; Profil vorn 143..146', rows_loft(ABDOMEN))
CHEST = [(1358, 158, -118, 144), (1380, 168, -120, 152), (1400, 177, -122, 162),
         (1420, 185, -122, 169), (1440, 193, -122, 173), (1460, 197, -122, 176),
         (1480, 196, -122, 178), (1500, 200, -122, 179), (1540, 200, -122, 176),
         (1580, 200, -122, 168), (1600, 200, -122, 154), (1620, 199, -122, 151),
         (1640, 198, -122, 145), (1660, 196, -122, 139), (1680, 193, -122, 140),
         (1690, 186, -122, 140), (1700, 184, -122, 129), (1710, 169, -120, 107)]
_part('chest_shell', 'frost_shell', 'Front ±158..201 u1360..1500 und 1680..1710; Profil vorn u1360..1710; breite Frontfläche (Fase 8 %) für Seitenstreifen', _sym(CHEST, .08, .18))
_part('collar', 'frost_slate', 'Front Schal ±152 u1710..1720 (darunter Brustschale), ±130/118 u1740/1760; Profil hinten u1710..1780 −145..−108 (u1680..1700 bildet das Schulterpolster), vorn 83..40',
      _sym([(1706, 150, -125, 95), (1712, 152, -145, 98), (1720, 152, -144, 83),
            (1730, 149, -140, 70), (1740, 130, -128, 72), (1750, 127, -122, 75),
            (1760, 118, -121, 70), (1772, 92, -118, 60), (1782, 70, -108, 40)], .25, .2))
_part('core_ring', 'frost_joint', PROVENANCE['core']['source'], disc('f', (1543, 0), 165, 180, 49, 32))
_part('core_light', 'frost_core', PROVENANCE['core']['source'], disc('f', (1543, 0), 172, 182, 33, 32))

# Gestaltung Brust (Front) und Rücken (Rückenansicht): Platten auf den Loftflächen.
CHEST_ROWS = [(u, -w, w, fb, ff) for u, w, fb, ff in CHEST]
# Linke Seite (x>0, s gespiegelt) gebaut, rechts exakt per mirror().
s = lambda v: 1-v
_part('chest_crystal', 'frost_crystal', 'Front: Kristallstreifen außen an der Brust u≈1490..1665',
      face_panel(CHEST_ROWS, 'front', [(1490, s(0)), (1500, s(.13)), (1660, s(.15)), (1665, s(.02))], cx=.08, cf=.18), sides=True)
_part('chest_strap', 'frost_slate', 'Front: schiefergraue V-Gurte Schulter→Brustmitte u≈1380..1655',
      face_panel(CHEST_ROWS, 'front', [(1640, s(.18)), (1655, s(.26)), (1395, s(.42)), (1382, s(.34))], off=1.6, cx=.08, cf=.18), sides=True)
_part('shoulder_blade', 'frost_slate', 'Rücken: zwei Schulterblattplatten u≈1480..1640 beidseits der Mittelplatte',
      face_panel(CHEST_ROWS, 'back', [(1480, .58), (1480, .76), (1600, .8), (1640, .74), (1640, .6)], cx=.08, cf=.18), sides=True)
_part('back_band', 'frost_frame', 'Rücken: dunkler unterer Rücken u≈1360..1440 unter weißer Rückenplatte',
      face_panel(CHEST_ROWS, 'back', [(1360, .2), (1360, .8), (1442, .8), (1442, .2)], cx=.08, cf=.18))
for i, (u0, u1) in enumerate([(1366, 1394), (1406, 1434)]):
    _part(f'back_hex_{i+1}', 'frost_shell', 'Rücken: weiße Sechseckplatten der Wirbelreihe',
          face_panel(CHEST_ROWS, 'back', [(u0, .44), (u0, .56), ((u0+u1)/2, .6), (u1, .56), (u1, .44), ((u0+u1)/2, .4)], off=2.6, depth=2, cx=.08, cf=.18))
_part('back_hex_0', 'frost_shell', 'Rücken: unterste Sechseckplatte der Wirbelreihe',
      face_panel(ABDOMEN, 'back', [(1305, .38), (1305, .62), (1320, .68), (1335, .62), (1335, .38), (1320, .32)], off=1.4, depth=2))

ANCHORS['Socket_Waist'] = dict(at=[10, 1265, 0], part='upper_body_abdomen_core', source='gemessen: Gürteloberkante/Bauchansatz u≈1265')
ANCHORS['Socket_Neck'] = dict(at=[0, 1760, 0], part='upper_body_collar', source='gemessen: Schaloberkante Front u≈1760; Profil Mitte')
ANCHORS['Socket_Shoulder_L'] = dict(at=[-40, 1560, 260], part='upper_body_chest_shell', source='Annahme: Schulterachse unter Panzerpolster, Front Panzer x205..410 Mitte ≈300, Profil Polster −186..+87')
ANCHORS['Socket_Shoulder_R'] = dict(at=[-40, 1560, -260], part='upper_body_chest_shell', source='gespiegelt')
