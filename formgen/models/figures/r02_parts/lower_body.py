"""R02 Unterkörper: Becken, Lendenplatte, Gürtel mit zwei Taschen.

Zeilen gemessen (tools/r02_measure.py, Front gespiegelt gemittelt, Profil
A/B gemittelt). Der Rückenrand des Beckens ist im Profil vom Unterarm
verdeckt (u1060..1300): Rückentiefe −108..−118 ist Annahme nach u1040.
"""
from formgen.models.figures.r02_parts.common import PROVENANCE as COMMON, rows_loft, mirror

PROVENANCE = {
    **COMMON,
    'hidden': {'kind': 'Annahme',
               'source': 'Becken-/Gürtelrückseite verdeckt; Lendenplatte nach Frontfarbbild (weiß u1003..1160, x±87→±30)'},
    'waist': {'kind': 'gemessen', 'at': [10, 1265, 0],
              'source': 'Gürteloberkante/Bauchansatz Front u≈1265..1290 (Breitensprung ±188→±130)'},
}
PARTS = []
ANCHORS = {}


def _part(name, role, source, shape, sides=False):
    items = [('_l', shape), ('_r', mirror(shape))] if sides else [('', shape)]
    for suffix, s in items:
        PARTS.append(dict(id='lower_body_'+name+suffix, assembly='lower_body', role=role, bevel=0,
                          provenance={'kind': 'gemessen', 'source': source}, **s))


def _sym(rows, cx=.22, cf=.22):
    """(u, halfwidth, fb, ff) → symmetric loft."""
    return rows_loft([(u, -w, w, fb, ff) for u, w, fb, ff in rows], cx, cf)


# Dunkler Beckenkern zwischen den Oberschenkeln bis unter den Gürtel.
_part('pelvis_core', 'frost_frame', 'Front u975..1150 Silhouette; Profil u1040 −106/+134, Front um 10 mm hinter Lendenplatte',
      _sym([(965, 30, -95, 110), (980, 120, -105, 120), (1000, 205, -108, 124),
            (1040, 212, -108, 124), (1060, 210, -110, 126), (1080, 208, -110, 128),
            (1100, 204, -110, 130), (1120, 198, -112, 130), (1140, 191, -112, 130),
            (1152, 189, -112, 130)]))
# Weiße Lendenplatte (Front u1003..1160), vor dem Kern bis zur gemessenen Profilfront.
_part('loin_plate', 'frost_shell', 'Frontfarbbild Lendenplatte; Profil vorn u1040..1140 = 134..146',
      _sym([(1000, 30, 100, 134), (1040, 62, 100, 135), (1080, 80, 100, 141),
            (1120, 87, 100, 145), (1150, 87, 100, 146)], .3, .1))
# Gürtel mit Rückenband; Taschen setzen Front- und Profilkante.
_part('belt', 'frost_slate', 'Front u1150..1270 Band ±190..196 (Taschen außen); Profil Rückseite Annahme',
      _sym([(1147, 190, -116, 128), (1180, 194, -118, 130), (1230, 194, -118, 130),
            (1268, 188, -116, 128)]))
POUCH = [(1150, 95, 214, 100, 155), (1180, 95, 210, 100, 158), (1200, 95, 206, 100, 151),
         (1220, 95, 206, 100, 157), (1240, 95, 200, 100, 160), (1268, 95, 192, 100, 158),
         (1285, 100, 175, 100, 150)]
_part('pouch', 'frost_slate', 'Front u1160..1260 Außenkante ±214..194; Profil vorn 151..160; Taschenoberkante u≈1287',
      rows_loft(POUCH, .12, .15), sides=True)
_part('abdomen_plate', 'frost_shell', 'Frontfarbbild kleine weiße Platte über Gürtelschnalle u1205..1276, x±60',
      _sym([(1205, 55, 120, 136), (1240, 60, 120, 138), (1276, 52, 120, 140)], .25, .1))

ANCHORS['Socket_Waist'] = dict(at=[10, 1265, 0], part='lower_body_belt', source=PROVENANCE['waist']['source'])
