"""R02 Oberkörper: Bauch, Brustpanzer, Rückenplatte, Kragen/Schal, Brustkern.

Frontbreiten gemessen; Profil vorn gemessen (u1300..1710). Der Rumpfrücken ist
im Profil überall von Oberarm/Schulterpanzer verdeckt: Rückentiefe ist
Annahme (−112 Bauch, −122 Brust). Schulterpanzer gehören zu arms.
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror, disc

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


_part('abdomen_core', 'frost_frame', 'Front u1290..1340 ±130..138; Profil vorn 143..146',
      _sym([(1262, 150, -110, 126), (1290, 132, -112, 136), (1300, 130, -112, 143),
            (1320, 131, -112, 145), (1340, 138, -114, 146), (1362, 156, -116, 144)]))
CHEST = [(1358, 158, -118, 144), (1380, 168, -120, 152), (1400, 177, -122, 162),
         (1420, 185, -122, 169), (1440, 193, -122, 173), (1460, 197, -122, 176),
         (1480, 196, -122, 178), (1500, 200, -122, 179), (1540, 200, -122, 176),
         (1580, 200, -122, 168), (1600, 200, -122, 154), (1620, 199, -122, 151),
         (1640, 198, -122, 145), (1660, 196, -122, 139), (1680, 193, -122, 140),
         (1690, 186, -122, 140), (1700, 184, -122, 129), (1710, 169, -120, 107)]
_part('chest_shell', 'frost_shell', 'Front ±158..201 u1360..1500 und 1680..1710; Profil vorn u1360..1710', _sym(CHEST, .2, .18))
_part('collar', 'frost_slate', 'Front Schal ±152 u1600..1720, ±130/118 u1740/1760; Profil hinten u1680..1780 −151..−108, vorn 141..72',
      _sym([(1598, 150, -122, 100), (1660, 152, -140, 110), (1680, 152, -151, 141),
            (1700, 152, -143, 129), (1710, 152, -145, 107), (1720, 152, -144, 83),
            (1730, 149, -140, 70), (1740, 130, -128, 72), (1750, 127, -122, 75),
            (1760, 118, -121, 70), (1772, 92, -118, 60), (1782, 70, -108, 40)], .25, .2))
_part('core_ring', 'frost_joint', PROVENANCE['core']['source'], disc('f', (1543, 0), 160, 177, 49, 32))
_part('core_light', 'frost_core', PROVENANCE['core']['source'], disc('f', (1543, 0), 170, 179, 33, 32))

ANCHORS['Socket_Waist'] = dict(at=[10, 1265, 0], part='upper_body_abdomen_core', source='gemessen: Gürteloberkante/Bauchansatz u≈1265')
ANCHORS['Socket_Neck'] = dict(at=[0, 1760, 0], part='upper_body_collar', source='gemessen: Schaloberkante Front u≈1760; Profil Mitte')
ANCHORS['Socket_Shoulder_L'] = dict(at=[-40, 1560, 260], part='upper_body_chest_shell', source='Annahme: Schulterachse unter Panzerpolster, Front Panzer x205..410 Mitte ≈300, Profil Polster −186..+87')
ANCHORS['Socket_Shoulder_R'] = dict(at=[-40, 1560, -260], part='upper_body_chest_shell', source='gespiegelt')
